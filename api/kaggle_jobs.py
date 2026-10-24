"""Opt-in local batch bridge. Kaggle credentials never leave the owner's CLI.

The public Vercel app reads exported snapshots; it cannot launch this bridge.
No browser input becomes a shell command, destination path, owner or credential.
"""
from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import threading
import time
import traceback
import uuid

PROJECT = {"project_name": "Model Mountain", "project_id": "16f864bfa1303fc9"}
JOB_ID = re.compile(r"^mm-[a-f0-9]{24}$")
TERMINAL = {"complete", "blocked", "error", "cancelled"}


def now():
    return datetime.now(timezone.utc).isoformat()


def save_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(".tmp")
    temporary.write_text(json.dumps(value, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    temporary.replace(path)


class BatchError(Exception):
    pass


class KaggleBatch:
    def __init__(self, root, folder, owner, *, runner=None, pause=None):
        self.root, self.folder = Path(root).resolve(), Path(folder).resolve()
        if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_-]{2,49}", owner):
            raise BatchError("Configure the operator's Kaggle username.")
        self.owner = owner
        self.runner = runner or self._run
        self.pause = pause or time.sleep
        self.folder.mkdir(parents=True, exist_ok=True)
        self._lock = threading.Lock()

    @classmethod
    def from_environment(cls, root, *, vercel=False):
        if vercel or os.getenv("MODEL_MOUNTAIN_KAGGLE_ENABLED") != "1":
            return None
        return cls(root, Path(root) / "model_mountain_results/batch_jobs", os.getenv("MODEL_MOUNTAIN_KAGGLE_OWNER", ""))

    def _run(self, argv, timeout=60):
        result = subprocess.run(argv, cwd=self.root, capture_output=True, text=True,
                                timeout=timeout, shell=False)
        # Remains in ignored operator storage; never copied into a public job record.
        with (self.folder / "cli.log").open("a", encoding="utf-8") as log:
            log.write(f"{now()} exit={result.returncode}\n{result.stdout}\n{result.stderr}\n")
        if result.returncode:
            # CLI output can include local paths or upstream messages; retain privately.
            raise BatchError("The local Kaggle command failed; inspect operator logs.")
        return result.stdout

    def cli(self):
        path = self.root / (".venv/Scripts/kaggle.exe" if os.name == "nt" else ".venv/bin/kaggle")
        if not path.is_file():
            raise BatchError("Install the Kaggle CLI in this project's .venv.")
        return str(path)

    def path(self, job_id):
        if not isinstance(job_id, str) or not JOB_ID.fullmatch(job_id):
            raise BatchError("Invalid Model Mountain job ID.")
        return self.folder / job_id / "job.json"

    def get(self, job_id):
        path = self.path(job_id)
        if not path.is_file():
            raise BatchError("Unknown Model Mountain job.")
        return json.loads(path.read_text(encoding="utf-8"))

    def list(self):
        rows = []
        for path in sorted(self.folder.glob("mm-*/job.json"), reverse=True)[:100]:
            if JOB_ID.fullmatch(path.parent.name):
                rows.append(json.loads(path.read_text(encoding="utf-8")))
        return rows

    def prepare(self, body):
        if not isinstance(body, dict) or set(body) - {"model_ids", "phase"}:
            raise BatchError("Use only model_ids and phase.")
        models = body.get("model_ids")
        phase = body.get("phase", "full")
        if not isinstance(models, list) or len(models) != 1 or any(not isinstance(m, str) for m in models) or phase not in ("full", "preflight", "stories"):
            raise BatchError("Choose one allowlisted model and a full/preflight/stories phase; models run in separate jobs.")
        catalog = json.loads((self.root / "api/model_catalog.json").read_text(encoding="utf-8"))
        allowed = {m["model_id"]: m["revision"] for m in catalog["items"]}
        if any(m not in allowed for m in models):
            raise BatchError("Model is not in the operator-reviewed pinned catalog.")
        if phase == "full" and not any(r.get("phase") == "stories" and r.get("status") == "complete" and r.get("runtime", {}).get("stories_sha256") for r in self.list()):
            raise BatchError("Complete a managed stories job before requesting a model experiment.")
        with self._lock:
            # A filesystem fence also prevents duplicate submission by another local process.
            try:
                descriptor = os.open(self.folder / "active.lock", os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
            except FileExistsError:
                raise BatchError("A batch is active or its outcome needs operator reconciliation.") from None
            job_id = "mm-" + uuid.uuid4().hex[:24]
            os.write(descriptor, job_id.encode("ascii"))
            os.close(descriptor)
            row = {**PROJECT, "id": job_id, "model_ids": models, "model_revisions": {m: allowed[m] for m in models},
                   "phase": phase, "status": "queued", "created_at": now(), "updated_at": now(),
                   "evidence_type": "NOT_CAPTURED", "model_executed": False, "mia_hook_executed": False,
                   "independently_verified": False}
            save_json(self.path(job_id), row)
        return row

    def submit(self, body):
        row = self.prepare(body)
        threading.Thread(target=self.execute, args=(row["id"],), daemon=True).start()
        return row

    def execute(self, job_id):
        row = self.get(job_id)
        submitted = False
        reconciled = False
        try:
            row["controller_step"] = "build"
            slug = "model-mountain-job-" + job_id[3:]
            command = [sys.executable, str(self.root / "kaggle/build_kernel.py"), "--owner", self.owner]
            if row["phase"] == "preflight":
                command.append("--preflight-only")
            elif row["phase"] == "stories":
                command.extend(["--stories", "--generator", row["model_ids"][0]])
                slug = "model-mountain-stories"
            else:
                command.extend(["--model", row["model_ids"][0]])
            built = self.runner(command).strip().splitlines()[-1]
            bundle = Path(built).resolve()
            if not bundle.is_relative_to(self.root / "model_mountain_results/kaggle_bundle"):
                raise BatchError("Builder returned a destination outside its allowlisted directory.")
            metadata_path = bundle / "kernel-metadata.json"
            metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
            metadata.update(id=f"{self.owner}/{slug}", title=slug.replace("-", " "), is_private=True)
            save_json(metadata_path, metadata)
            row.update(status="submitting", kernel_ref=metadata["id"], updated_at=now())
            save_json(self.path(job_id), row)
            # An interrupted push is uncertain; never automatically retry it.
            submitted = True
            row["controller_step"] = "submit"
            output = self.runner([self.cli(), "kernels", "push", "-p", str(bundle), "--accelerator", "NvidiaTeslaT4", "--timeout", "10800"], timeout=90)
            refs = re.findall(r"https://www\.kaggle\.com/code/([A-Za-z0-9_-]+/[A-Za-z0-9_-]+)", output)
            if refs and any(ref != metadata["id"] for ref in refs):
                raise BatchError("Kaggle returned an unexpected job identity; reconcile before retrying.")
            version = re.search(r"Kernel version (\d+)", output)
            row.update(status="running", version=int(version.group(1)) if version else None, updated_at=now())
            save_json(self.path(job_id), row)
            deadline = time.monotonic() + 14400
            row["controller_step"] = "poll"
            while time.monotonic() < deadline:
                status = self.runner([self.cli(), "kernels", "status", row["kernel_ref"]])
                match = re.search(r"KernelWorkerStatus\.([A-Z_]+)", status)
                if not match:
                    raise BatchError("Kaggle status could not be interpreted; reconcile before retrying.")
                state = match.group(1).lower()
                if state in TERMINAL:
                    reconciled = True
                    row.update(status=state, updated_at=now())
                    if state == "complete":
                        row["controller_step"] = "download"
                        destination = self.path(job_id).parent / "outputs"
                        self.runner([self.cli(), "kernels", "output", row["kernel_ref"], "-p", str(destination),
                                     "--file-pattern", r"^mm_results/(?:.*\.(?:json|pt|npz|npy))$", "--quiet"], timeout=300)
                        row["runtime"] = self.inspect_output(destination, row)
                        row["controller_step"] = "inspect"
                        if not row["runtime"]["preflight_usable"] or row["runtime"]["failed_phases"]:
                            row["status"] = "blocked"
                            row["reason"] = "Runtime preflight or experiment phase failed; inspect operator artifacts."
                        row["model_executed"] = True if row["runtime"]["model_execution_reported"] else (False if not row["runtime"]["preflight_usable"] else None)
                        row["mia_hook_executed"] = None if row["runtime"]["capture_reported"] else False
                    break
                row.update(status=state, updated_at=now())
                save_json(self.path(job_id), row)
                self.pause(30)
            else:
                raise BatchError("Operator polling deadline reached; job outcome needs reconciliation.")
        except Exception as exc:
            (self.path(job_id).parent / "controller-error.log").write_text(traceback.format_exc(), encoding="utf-8")
            row.update(status="submission_unknown" if submitted and not reconciled else "blocked",
                       error_code=type(exc).__name__,
                       reason=str(exc) if isinstance(exc, BatchError) else "Local batch failed; inspect operator artifacts.", updated_at=now())
        finally:
            save_json(self.path(job_id), row)
            if not submitted or reconciled:
                (self.folder / "active.lock").unlink(missing_ok=True)

    @staticmethod
    def inspect_output(destination, row):
        path = destination / "mm_results/summary.json"
        if not path.is_file() or path.stat().st_size > 1048576:
            raise BatchError("Completed job lacks a bounded runtime summary.")
        raw = path.read_bytes()
        summary = json.loads(raw)
        config = summary.get("config", {})
        models = config.get("models") or [config.get("model") or config.get("generator_model")]
        if models != row["model_ids"]:
            raise BatchError("Runtime summary does not match requested models.")
        phases = summary.get("phases", [])
        if not isinstance(phases, list) or any(not isinstance(p, dict) for p in phases):
            raise BatchError("Malformed phase evidence.")
        captured = summary.get("preflight_usable") is True and any(p.get("phase") in ("vectors", "emotions") and p.get("rc") == 0 for p in phases)
        generated = summary.get("preflight_usable") is True and any(p.get("phase") == "stories" and p.get("rc") == 0 for p in phases)
        story_sha = None
        if generated:
            story_path = destination / "mm_results/stories.json"
            if not story_path.is_file() or story_path.stat().st_size > 16777216:
                raise BatchError("Story-generation phase lacks a bounded corpus artifact.")
            story_sha = hashlib.sha256(story_path.read_bytes()).hexdigest()
        return {"preflight_usable": summary.get("preflight_usable") is True,
                "model_execution_reported": captured or generated, "capture_reported": captured,
                "stories_sha256": story_sha,
                "failed_phases": [p.get("phase") for p in phases if p.get("rc") != 0],
                "phases": [{"phase": p.get("phase"), "exit_code": p.get("rc")} for p in phases],
                "summary_sha256": hashlib.sha256(raw).hexdigest(), "independently_verified": False,
                "note": "Worker phase telemetry; success requires separate artifact review. Raw outputs remain local."}
