"""Refresh/check the notebook's inert source payload from the canonical checkout.

Uses AST literal parsing only; never executes notebook cells or imports payloads.
"""
import argparse
import ast
import base64
import hashlib
import json
from pathlib import Path
import re
import zlib

ROOT = Path(__file__).resolve().parents[1]
NOTEBOOK = ROOT / "Model_Mountain_Kaggle.ipynb"
SECRETS = re.compile(rb"KGAT_[0-9a-f]{16,}|hf_[A-Za-z0-9]{30,}|gh[pousr]_[A-Za-z0-9]{30,}|sk-[A-Za-z0-9_-]{32,}|-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----")


def payload_cell(document):
    for cell in document["cells"]:
        if cell["cell_type"] != "code":
            continue
        source = "".join(cell["source"])
        if "PACKED_SOURCES =" not in source:
            continue
        for node in ast.parse(source).body:
            if isinstance(node, ast.Assign) and any(isinstance(t, ast.Name) and t.id == "PACKED_SOURCES" for t in node.targets):
                return cell, source, node, ast.literal_eval(node.value)
    raise ValueError("Notebook payload cell not found")


def refresh(check=False):
    document = json.loads(NOTEBOOK.read_text(encoding="utf-8"))
    cell, source, node, old = payload_cell(document)
    paths = set(old)
    patterns = ("model_mountain/*.py", "tests/*.py", "api/*.py", "api/*.json", "kaggle/*.py", "kaggle/*.json",
                "examples/**/*.json", "docs/build/**/*.md", "docs/build/**/*.json", "scripts/*.py")
    for pattern in patterns:
        paths.update(p.relative_to(ROOT).as_posix() for p in ROOT.glob(pattern) if p.is_file())
    # Test contracts read these canonical files. No local runtime state is bundled.
    paths.update(("agent_workflow/refresh_notebook.py", "vercel.json", "web/package.json"))
    packed, hashes, missing = {}, {}, []
    for relative in sorted(paths):
        path = (ROOT / relative).resolve()
        if not path.is_relative_to(ROOT) or not path.is_file():
            raise ValueError("Payload source is missing or outside the project: " + relative)
        data = path.read_bytes()
        if SECRETS.search(data):
            raise ValueError("Credential-shaped data in payload source: " + relative)
        hashes[relative] = hashlib.sha256(data).hexdigest()
        packed[relative] = base64.b64encode(zlib.compress(data, 9)).decode("ascii")
        previous = old.get(relative)
        if previous is None or zlib.decompress(base64.b64decode(previous)) != data:
            missing.append(relative)
    if check:
        if missing or set(old) != paths:
            raise ValueError("Notebook payload differs from canonical sources: " + ", ".join(missing))
        print(json.dumps({"source_files": len(paths), "byte_parity": True, "notebook_executed": False}))
        return
    lines = source.splitlines(keepends=True)
    updated = "".join(lines[:node.lineno - 1]) + "PACKED_SOURCES = " + repr(packed) + "\n" + "".join(lines[node.end_lineno:])
    ast.parse(updated)
    cell["source"] = updated.splitlines(keepends=True)
    for item in document["cells"]:
        if item["cell_type"] == "code":
            item["outputs"], item["execution_count"] = [], None
    document["cells"][0]["source"] = [
        "# Model Mountain: portable CPU verification snapshot\n\n",
        "This notebook restores the current canonical Python package, tests and configuration. All real-model flags default to false.\n\n",
        "The later opt-in GPU cells preserve the original single-model research workflow. For the current three-model emotion/head study use `kaggle/build_kernel.py` and the setup instructions in `docs/build/remote/REMOTE_MODELS.md` from the repository.\n\n",
        "CPU fixtures verify control logic only. Actual capture, steering and held-out attack outcomes require independently reviewed GPU artifacts.\n"]
    NOTEBOOK.write_text(json.dumps(document, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    manifest = {"project_id": "16f864bfa1303fc9", "source": NOTEBOOK.name,
                "method": "AST literal parse + base64/zlib; no cell execution", "files": hashes}
    (ROOT / "agent_workflow/NOTEBOOK_SOURCE_MANIFEST.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"source_files": len(paths), "refreshed": True, "notebook_executed": False}))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    refresh(parser.parse_args().check)
