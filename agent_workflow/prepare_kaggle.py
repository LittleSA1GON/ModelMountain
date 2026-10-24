"""Stage a private Kaggle notebook bundle locally; never upload or execute it."""
import argparse
import hashlib
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]


def prepare(owner, output, gpu=False):
    if not re.fullmatch(r"[a-zA-Z0-9_-]+", owner):
        raise ValueError("Supply your Kaggle username slug")
    notebook = ROOT / "Model_Mountain_Kaggle.ipynb"
    data = json.loads(notebook.read_text(encoding="utf-8"))
    # Public notebook exports must contain no old cell outputs or execution state.
    for cell in data["cells"]:
        if cell.get("cell_type") == "code":
            cell["outputs"] = []
            cell["execution_count"] = None
    encoded = json.dumps(data, indent=1, ensure_ascii=False) + "\n"
    if "KGAT_" in encoded:
        raise ValueError("Notebook contains a Kaggle access-token marker; inspect before export")
    output = Path(output)
    output.mkdir(parents=True, exist_ok=False)
    (output / notebook.name).write_text(encoded, encoding="utf-8")
    metadata = {"id": f"{owner}/model-mountain", "title": "Model Mountain",
                "code_file": notebook.name, "language": "python", "kernel_type": "notebook",
                "is_private": True, "enable_gpu": gpu, "enable_internet": gpu,
                "dataset_sources": [], "competition_sources": [], "kernel_sources": [], "model_sources": []}
    (output / "kernel-metadata.json").write_text(json.dumps(metadata, indent=2) + "\n", encoding="utf-8")
    report = {"staged": True, "uploaded": False, "executed": False, "private": True,
              "gpu_requested": gpu, "real_mia_enabled": False,
              "notebook_sha256": hashlib.sha256(encoded.encode("utf-8")).hexdigest(),
              "credential_present": (Path.home() / ".kaggle/access_token").is_file()}
    print(json.dumps(report, indent=2))
    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--owner", required=True)
    parser.add_argument("--output", type=Path, default=ROOT / "model_mountain_results/kaggle_bundle")
    parser.add_argument("--gpu", action="store_true", help="Request GPU/internet; real-MIA switches remain off")
    args = parser.parse_args()
    prepare(args.owner, args.output, args.gpu)
