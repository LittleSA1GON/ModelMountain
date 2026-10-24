"""Small CPU-only control plane for Vercel and local review.

Remote endpoints and credentials come only from deployment configuration. Public
access is limited to inert CPU demonstrations and sanitized aggregate reports.
"""
from __future__ import annotations

from dataclasses import dataclass
from contextlib import closing
from hashlib import sha256
import hmac
import json
import math
import os
from pathlib import Path
import re
import sqlite3
import time
import threading
from urllib.error import HTTPError, URLError
from urllib.parse import urlsplit
from urllib.request import HTTPRedirectHandler, Request, build_opener
import uuid

ROOT = Path(__file__).resolve().parents[1]
MODEL_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,95}/[A-Za-z0-9][A-Za-z0-9_.-]{0,95}$")
SAFE_ID = re.compile(r"^[A-Za-z0-9_.-]{1,100}$")
MAX_BODY = 32768
PROJECT_NAME = "Model Mountain"
PROJECT_ID = "16f864bfa1303fc9"
CAPABILITIES = ["inference", "hidden_states", "attention_tracker", "steering", "core_reranker", "hnode", "science_hallucination", "attnlink"]


class APIError(Exception):
    def __init__(self, status, code, message):
        self.status, self.code, self.message = status, code, message
        super().__init__(message)


@dataclass(frozen=True)
class Settings:
    remote_url: str = ""
    remote_token: str = ""
    operator_token: str = ""
    data_dir: str = ""
    vercel: bool = False
    attestation_file: str = ""

    @classmethod
    def from_env(cls):
        return cls(os.getenv("MODEL_MOUNTAIN_REMOTE_URL", ""), os.getenv("MODEL_MOUNTAIN_REMOTE_TOKEN", ""),
                   os.getenv("MODEL_MOUNTAIN_OPERATOR_TOKEN", ""), os.getenv("MODEL_MOUNTAIN_DATA_DIR", ""), bool(os.getenv("VERCEL")), os.getenv("MODEL_MOUNTAIN_ATTESTATION_FILE", ""))

    def checked_remote(self):
        p = urlsplit(self.remote_url)
        if (p.scheme != "https" and not (p.scheme == "http" and p.hostname in ("127.0.0.1", "localhost", "::1"))) or not p.hostname or p.username or p.password or p.query or p.fragment:
            raise APIError(503, "remote_configuration_invalid", "Configure a fixed HTTPS worker URL without embedded credentials.")
        if not self.remote_token:
            raise APIError(503, "remote_credentials_missing", "A server-side worker credential is required.")
        return self.remote_url.rstrip("/")


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


class RemoteClient:
    def __init__(self, settings):
        self.settings = settings

    def request(self, method, path, payload=None):
        base = self.settings.checked_remote()
        body = json.dumps(payload).encode() if payload is not None else None
        req = Request(base + "/api/v1" + path, data=body, method=method,
                      headers={"Authorization": "Bearer " + self.settings.remote_token, "Content-Type": "application/json"})
        try:
            with build_opener(NoRedirect()).open(req, timeout=20) as response:
                raw = response.read(1048577)
                if len(raw) > 1048576:
                    raise APIError(502, "worker_response_too_large", "Worker response exceeded the limit.")
                result = json.loads(raw)
                if not isinstance(result, dict):
                    raise ValueError("Expected object")
                return result
        except APIError:
            raise
        except HTTPError as exc:
            raise APIError(502, "worker_request_failed", f"Worker returned HTTP {exc.code}; no fallback was performed.") from None
        except (URLError, TimeoutError, OSError, ValueError):
            raise APIError(503, "worker_unavailable", "Remote worker is unavailable; no synthetic fallback was performed.") from None


def sanitize(value):
    """Remove credential-shaped fields from structured transport responses."""
    if isinstance(value, dict):
        secret_fields = {"token", "access_token", "api_key", "remote_token", "operator_token", "lease_token", "authorization", "password", "secret", "credentials"}
        return {k: sanitize(v) for k, v in value.items() if k.lower() not in secret_fields}
    if isinstance(value, list):
        return [sanitize(v) for v in value]
    return value


class RunStore:
    def __init__(self, path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with closing(sqlite3.connect(self.path)) as db, db:
            db.execute("CREATE TABLE IF NOT EXISTS reports (id TEXT PRIMARY KEY, created REAL, report TEXT NOT NULL)")

    def put(self, report):
        with closing(sqlite3.connect(self.path)) as db, db:
            db.execute("INSERT INTO reports VALUES (?, ?, ?) ON CONFLICT(id) DO UPDATE SET created=excluded.created, report=excluded.report", (report["run_id"], time.time(), json.dumps(report)))
            db.execute("DELETE FROM reports WHERE id NOT IN (SELECT id FROM reports ORDER BY created DESC LIMIT 200)")

    def list(self):
        with closing(sqlite3.connect(self.path)) as db, db:
            return [json.loads(row[0]) for row in db.execute("SELECT report FROM reports ORDER BY created DESC LIMIT 100")]


class ControlAPI:
    def __init__(self, settings=None, *, remote=None, store=None, batch=None):
        self.settings = settings or Settings.from_env()
        self.remote = remote or RemoteClient(self.settings)
        folder = self.settings.data_dir or ("/tmp/model-mountain" if self.settings.vercel else str(ROOT / "model_mountain_results/control"))
        self.store = store or RunStore(Path(folder) / "reports.sqlite3")
        self._public_requests = []
        self._limit_lock = threading.Lock()
        from api.kaggle_jobs import KaggleBatch
        self.batch = batch or KaggleBatch.from_environment(ROOT, vercel=self.settings.vercel)

    def attestations(self):
        path = Path(self.settings.attestation_file) if self.settings.attestation_file else ROOT / "api/verified_attestations.json"
        if not path.exists():
            return []
        try:
            document = json.loads(path.read_text(encoding="utf-8"))
            if document.get("project_id") != PROJECT_ID:
                raise ValueError("Wrong project")
            accepted = []
            for item in document.get("items", []):
                reviewers = item.get("reviewers", [])
                hashes = [item.get(field, "") for field in ("profile_sha256", "capture_artifact_sha256")]
                if item.get("evidence_type") != "REAL_IBM_MIA" or item.get("hook_executed") is not True or len(set(reviewers)) < 2 or not {"codex", "claude"} <= set(reviewers):
                    continue
                if not isinstance(item.get("id"), str) or not SAFE_ID.fullmatch(item["id"]) or not MODEL_ID.fullmatch(item.get("model_id", "")) or not re.fullmatch(r"[a-fA-F0-9]{40}", item.get("model_revision", "")) or not re.fullmatch(r"[a-fA-F0-9]{40}", item.get("ibm_revision", "")) or not all(re.fullmatch(r"[a-fA-F0-9]{64}", h) for h in hashes):
                    continue
                accepted.append(item)
            return accepted
        except (OSError, ValueError, TypeError):
            raise APIError(503, "attestation_registry_invalid", "The trusted runtime attestation registry is invalid.") from None

    def authorized(self, headers):
        expected = self.settings.operator_token
        value = {str(k).lower(): v for k, v in headers.items()}.get("authorization", "")
        return bool(expected) and hmac.compare_digest(value, "Bearer " + expected)

    def validated_result(self, result, body):
        """A worker cannot add fields to browser responses or public report rows."""
        allowed = {"run_id", "evidence_type", "answer", "model_id", "model_revision", "decision",
                   "latency_ms", "reasons", "citations", "steering_verified", "profile_sha256",
                   "attestation_ref", "ibm_revision", "capture_artifact_sha256", "hook_artifact_sha256", "request_id"}
        result = {k: v for k, v in result.items() if k in allowed}
        if result.get("evidence_type") not in ("REAL_MODEL", "REAL_IBM_MIA", "LIVE_REAL_MODEL"):
            raise APIError(502, "invalid_worker_evidence", "Worker evidence must explicitly identify real model execution.")
        if not isinstance(result.get("run_id"), str) or not SAFE_ID.fullmatch(result["run_id"]) or result.get("model_id") != body["model_id"] or not isinstance(result.get("answer"), str) or len(result["answer"]) > 32768:
            raise APIError(502, "invalid_worker_result", "Worker result does not match the request schema.")
        decision = result.get("decision", "unknown")
        latency = result.get("latency_ms")
        if not isinstance(decision, str) or decision not in ("allow", "deny", "abstain", "hold", "unknown"):
            raise APIError(502, "invalid_worker_result", "Invalid worker decision.")
        if latency is not None and (type(latency) not in (int, float) or not math.isfinite(latency) or not 0 <= latency <= 86400000):
            raise APIError(502, "invalid_worker_result", "Invalid worker latency measurement.")
        result["decision"] = decision
        if "steering_verified" in result and type(result["steering_verified"]) is not bool:
            raise APIError(502, "invalid_worker_result", "Invalid worker steering status.")
        for key in ("reasons", "citations"):
            values = result.get(key, [])
            if not isinstance(values, list) or len(values) > 50 or any(not isinstance(v, str) or len(v) > 500 for v in values):
                raise APIError(502, "invalid_worker_result", "Invalid worker annotation list.")
        for key in allowed - {"reasons", "citations", "latency_ms", "steering_verified"}:
            if result.get(key) is not None and not isinstance(result[key], str):
                raise APIError(502, "invalid_worker_result", "Invalid worker metadata.")
            if key != "answer" and isinstance(result.get(key), str) and len(result[key]) > 500:
                raise APIError(502, "invalid_worker_result", "Worker metadata exceeded the field limit.")
        from .gateway import SECRET_PATTERNS
        sensitive = [*SECRET_PATTERNS, re.compile(r"\bKGAT_[A-Za-z0-9_-]{16,}\b"), re.compile(r"\bhf_[A-Za-z0-9]{16,}\b")]
        serialized = json.dumps(result, allow_nan=False)
        if any(p.search(serialized) for p in sensitive) or any(secret and secret in serialized for secret in (self.settings.remote_token, self.settings.operator_token)):
            raise APIError(502, "sensitive_output_withheld", "Worker output contained protected credential material.")
        return result

    def worker_response(self, method, route, body=None):
        """Keep non-inference worker endpoints inside a bounded public schema too."""
        raw = self.remote.request(method, route, body)
        row_fields = {
            "/models": {"id", "model_id", "name", "revision", "status", "downloaded", "model_executed", "compatible", "evidence_type", "note", "capabilities"},
            "/vectors": {"id", "name", "concept", "status", "evidence_type", "model_id", "model_revision", "profile_sha256", "block", "hidden_size", "test_auroc", "val_auroc", "trained", "verified"},
            "/jobs": {"id", "job_id", "run_id", "model_id", "model_ids", "status", "evidence_type", "created_at", "updated_at", "version"},
        }
        key = "/jobs" if route.startswith("/jobs/") else route
        fields = row_fields.get(key)
        if fields is not None:
            rows = raw.get("items", [])
            if not isinstance(rows, list) or len(rows) > 200 or any(not isinstance(r, dict) for r in rows):
                raise APIError(502, "invalid_worker_result", "Invalid worker catalog response.")
            result = {"items": [{k: v for k, v in r.items() if k in fields} for r in rows]}
        else:
            allowed = {"job_id", "run_id", "model_id", "revision", "status", "evidence_type", "created_at"}
            result = {k: v for k, v in raw.items() if k in allowed}
        rows_to_check = result.get("items", [result])
        for row in rows_to_check:
            for field, value in row.items():
                if field == "capabilities":
                    continue
                if field == "model_ids" and isinstance(value, list) and all(isinstance(v, str) for v in value):
                    continue
                if isinstance(value, (dict, list)):
                    raise APIError(502, "invalid_worker_result", "Worker metadata field must be scalar.")
        def checked(value, key=None):
            if key == "capabilities":
                if not isinstance(value, dict):
                    raise ValueError("Invalid capabilities")
                return {k: {f: checked(v[f]) for f in ("available", "reason", "config_source") if f in v and not isinstance(v[f], (dict, list))}
                        for k, v in value.items() if k in set(CAPABILITIES) | {"capture_hs", "steer", "hnode_hallucination", "tool_call_risk"} and isinstance(v, dict)}
            if isinstance(value, dict):
                return {k: checked(v, k) for k, v in value.items()}
            if isinstance(value, list):
                if len(value) > 200:
                    raise ValueError("Oversized list")
                return [checked(v) for v in value]
            if value is None or type(value) is bool:
                return value
            if type(value) in (int, float) and math.isfinite(value):
                return value
            if isinstance(value, str) and len(value) <= 2000:
                return value
            raise ValueError("Invalid metadata")
        try:
            result = checked(result)
            serialized = json.dumps(result, allow_nan=False)
        except (ValueError, TypeError):
            raise APIError(502, "invalid_worker_result", "Worker metadata failed schema validation.") from None
        from .gateway import SECRET_PATTERNS
        if any(p.search(serialized) for p in SECRET_PATTERNS) or re.search(r"\b(?:KGAT_|hf_)[A-Za-z0-9_-]{16,}\b", serialized) or any(s and s in serialized for s in (self.settings.remote_token, self.settings.operator_token)):
            raise APIError(502, "sensitive_output_withheld", "Worker metadata contained protected credentials.")
        return result

    def require_operator(self, headers):
        if not self.authorized(headers):
            raise APIError(401, "operator_required", "This operation requires the configured operator credential.")

    def public_limit(self):
        with self._limit_lock:
            now = time.monotonic()
            self._public_requests = [t for t in self._public_requests if now - t < 60]
            if len(self._public_requests) >= 60:
                raise APIError(429, "demo_rate_limit", "Demo request limit reached; retry in a minute.")
            self._public_requests.append(now)

    @staticmethod
    def validate_input(body):
        if not isinstance(body, dict):
            raise APIError(400, "invalid_json", "Request must be a JSON object.")
        if set(body) - {"model_id", "question", "mode", "profile_id", "max_output_tokens", "condition"}:
            raise APIError(400, "unexpected_fields", "Request contains unsupported fields.")
        if not isinstance(body.get("question"), str) or not 1 <= len(body["question"].strip()) <= 8000:
            raise APIError(400, "invalid_question", "Question must contain 1 to 8000 characters.")
        if not isinstance(body.get("model_id"), str) or not MODEL_ID.fullmatch(body["model_id"]):
            raise APIError(400, "invalid_model_id", "Select a repository-style model ID.")
        if body.get("mode", "simulation") not in ("simulation", "remote") or body.get("condition", "D") not in ("A", "B", "C", "D"):
            raise APIError(400, "invalid_mode", "Select a supported mode and condition.")
        tokens = body.get("max_output_tokens", 128)
        if type(tokens) is not int or not 1 <= tokens <= 512:
            raise APIError(400, "invalid_token_limit", "Output limit must be between 1 and 512.")
        if body.get("profile_id") is not None and (not isinstance(body["profile_id"], str) or not SAFE_ID.fullmatch(body["profile_id"])):
            raise APIError(400, "invalid_profile", "Profile must be a registered artifact ID.")

    def simulation(self, body):
        from .core import Document, scan_injection
        from .gateway import ModelMountainGateway, GatewayRequest, VerifiedIdentity, simulation_backend
        from .rag import ModelMountainRAG, RAGRequest, SourceRegistry
        start = time.perf_counter()
        docs = (Document.approved("password-policy", "All password resets require identity verification and admin approval."),
                Document.approved("expense-policy", "The reimbursement limit is $500 per request."))
        condition = body.get("condition", "D")
        question = body["question"]
        reasons, citations = [], []
        if condition == "A":
            # Deterministic unprotected fixture, never a real-model observation.
            answer = simulation_backend("", "Question: " + question + "\n" + "\n".join(d.text for d in docs), body.get("max_output_tokens", 128)).get("text", "")
            decision = "unprotected_fixture"
        else:
            gate = ModelMountainGateway(simulation_backend, require_mia=False)
            result = gate.evaluate(GatewayRequest(question, docs, VerifiedIdentity("acme", "public-demo", trusted_gateway=True)))
            if not result["allowed"]:
                answer, decision, reasons = "Request withheld by deterministic controls.", "deny", result["reasons"]
            else:
                rag = ModelMountainRAG(docs, SourceRegistry.trusted_fixture(docs))
                result = rag.answer(RAGRequest(question))
                answer, decision = result.get("answer", ""), "allow" if result.get("released") else "abstain"
                citations = re.findall(r"\[([A-Za-z0-9_.:-]+)\]", answer)
                reasons = [] if decision == "allow" else ["insufficient_verified_evidence"]
        return {"project_name": PROJECT_NAME, "project_id": PROJECT_ID, "run_id": str(uuid.uuid4()), "evidence_type": "CPU_SYNTHETIC", "mode": "simulation",
                "model_id": body["model_id"], "model_revision": None, "model_executed": False,
                "condition": condition, "decision": decision, "answer": answer, "reasons": reasons,
                "citations": citations, "latency_ms": (time.perf_counter() - start) * 1000,
                "steering_requested": bool(body.get("profile_id")), "steering_verified": False,
                "profile_sha256": None, "attestation_ref": None, "error": None,
                "limitations": ["Deterministic CPU fixture; no selected model, MIA hook or steering vector was executed.",
                                "B/C/D share controls in this UI smoke demo; this is not the A/B/C/D effectiveness benchmark."]}

    def handle(self, method, path, body=None, headers=None):
        headers = headers or {}
        if not path.startswith("/api/v1/"):
            raise APIError(404, "not_found", "Unknown API route.")
        route = path[len("/api/v1"):].split("?", 1)[0]
        if method == "GET" and route == "/health":
            configured = bool(self.settings.remote_url and self.settings.remote_token)
            return {"status": "ok", "api_version": "v1", "remote_configured": configured,
                    "local_batch_available": self.batch is not None, "operator_configured": bool(self.settings.operator_token),
                    "project_name": PROJECT_NAME, "project_id": PROJECT_ID,
                    "real_mia_verified": bool(self.attestations()), "verified_model_count": len({a["model_id"] for a in self.attestations()}), "simulation_available": True,
                    "storage": "ephemeral_per_instance" if self.settings.vercel and not self.settings.data_dir else "local_sqlite",
                    "rate_limit_scope": "per_instance_demo_only", "runtime": "CPU_CONTROL_PLANE"}
        if method == "GET" and route == "/models":
            if self.settings.remote_url and self.authorized(headers):
                return self.worker_response("GET", "/models")
            catalog = ROOT / "api/model_catalog.json"
            if catalog.is_file():
                data = json.loads(catalog.read_text(encoding="utf-8"))
                for row in data["items"]:
                    row.update(id=row["model_id"], name=row["model_id"].split("/")[-1], status="unverified", downloaded=False, model_executed=False)
                return data
            return {"items": [{"id": "Qwen/Qwen2-1.5B-Instruct", "model_id": "Qwen/Qwen2-1.5B-Instruct",
                               "name": "Qwen2 1.5B Instruct", "status": "unverified", "downloaded": False,
                               "capabilities": {c: "unverified" for c in CAPABILITIES},
                               "note": "Candidate from baseline documentation; no GPU compatibility claim."}]}
        if method == "GET" and route == "/vectors":
            if self.settings.remote_url and self.authorized(headers):
                return self.worker_response("GET", "/vectors")
            catalog = ROOT / "api/vector_catalog.json"
            if catalog.is_file():
                return json.loads(catalog.read_text(encoding="utf-8"))
            return {"items": [{"id": name, "name": name.replace("_", " "), "status": "candidate",
                               "evidence_type": "NOT_CAPTURED", "model_id": None, "projection": None,
                               "trained": False, "verified": False}
                              for name in ("grounding", "abstention", "injection_resistance", "empathy", "happiness", "anger", "fear", "calmness")]}
        if method == "GET" and route == "/reports":
            items = self.store.list()
            diagnostic = ROOT / "api/preflight_diagnostic.json"
            if diagnostic.is_file():
                items.append(json.loads(diagnostic.read_text(encoding="utf-8")))
            preflight = ROOT / "api/runtime_preflight.json"
            if preflight.is_file():
                items.append(json.loads(preflight.read_text(encoding="utf-8")))
            return {"items": items, "scope": "sanitized_summaries_and_diagnostic_report"}
        if method == "GET" and route == "/experiments":
            # Curated Kaggle IBM MIA results (scripts/ingest_kaggle_results.py). Read-only, no prompts from users.
            path = ROOT / "api/experiments.json"
            if not path.is_file():
                return {"status": "pending", "evidence_type": "NOT_CAPTURED", "models": [],
                        "note": "No Kaggle run has been ingested yet."}
            data = json.loads(path.read_text(encoding="utf-8"))
            if data.get("project_id") != PROJECT_ID or data.get("schema") != "mm-experiments-v1":
                raise APIError(503, "experiments_invalid", "The experiment results file is invalid.")
            return {**data, "status": "ingested"}
        if method == "GET" and route == "/orchestration":
            return self.orchestration()
        if method == "GET" and (route == "/jobs" or re.fullmatch(r"/jobs/[A-Za-z0-9_.-]{1,100}", route)):
            if self.batch:
                from api.kaggle_jobs import BatchError
                try:
                    items = self.batch.list() if route == "/jobs" else [self.batch.get(route.rsplit("/", 1)[-1])]
                except BatchError:
                    raise APIError(404, "job_not_found", "Unknown Model Mountain batch job.") from None
                return {"items": items, "mode": "KAGGLE_BATCH", "live": False,
                        "note": "Local operator job records; updated by the batch controller. Inspect each updated_at timestamp."}
            snapshot = ROOT / "api/batch_snapshot.json"
            if snapshot.is_file() and not self.settings.remote_url:
                data = json.loads(snapshot.read_text(encoding="utf-8"))
                if route != "/jobs":
                    items = [item for item in data.get("items", []) if item.get("id") == route.rsplit("/", 1)[-1]]
                    if not items:
                        raise APIError(404, "job_not_found", "Unknown Model Mountain batch job.")
                    return {**data, "items": items}
                return data
            self.require_operator(headers)
            if not self.settings.remote_url:
                return {"items": [], "status": "worker_not_configured"} if route == "/jobs" else self.not_configured()
            return self.worker_response("GET", route)
        if method == "POST" and route == "/jobs":
            self.require_operator(headers)
            if not self.batch:
                raise APIError(503, "batch_not_configured", "Kaggle submission requires the opt-in local operator bridge; cloud submission is disabled.")
            from api.kaggle_jobs import BatchError
            try:
                return self.batch.submit(body)
            except BatchError as exc:
                raise APIError(400, "batch_request_refused", str(exc)) from None
        if method == "POST" and route == "/inference":
            self.validate_input(body)
            if body.get("mode", "simulation") == "remote":
                self.require_operator(headers)
                if not self.settings.remote_url:
                    self.not_configured()
                request_id = str(uuid.uuid4())
                result = self.validated_result(self.remote.request("POST", route, {**body, "request_id": request_id}), body)
                if result.get("evidence_type") not in ("REAL_MODEL", "REAL_IBM_MIA", "LIVE_REAL_MODEL"):
                    raise APIError(502, "invalid_worker_evidence", "Remote result is missing an explicit real-model evidence type.")
                if not isinstance(result.get("run_id"), str) or not SAFE_ID.fullmatch(result["run_id"]) or result.get("model_id") != body["model_id"] or not isinstance(result.get("answer"), str) or len(result["answer"]) > 32768:
                    raise APIError(502, "invalid_worker_result", "Worker result is incomplete or does not match the requested model.")
                from .gateway import SECRET_PATTERNS
                sensitive = [*SECRET_PATTERNS, re.compile(r"\bKGAT_[A-Za-z0-9_-]{16,}\b"), re.compile(r"\bhf_[A-Za-z0-9]{16,}\b")]
                if any(pattern.search(result["answer"]) for pattern in sensitive) or any(secret and secret in result["answer"] for secret in (self.settings.remote_token, self.settings.operator_token)):
                    raise APIError(502, "sensitive_output_withheld", "Worker output matched a protected credential pattern and was withheld.")
                result["mode"] = "remote"
                result["worker_claims_steering_verified"] = result.pop("steering_verified", False)
                result["steering_verified"] = any(
                    att["id"] == result.get("attestation_ref") and att["model_id"] == result.get("model_id") and
                    att["model_revision"] == result.get("model_revision") and att["profile_sha256"] == result.get("profile_sha256")
                    and att.get("run_id") == result.get("run_id") and att.get("ibm_revision") == result.get("ibm_revision")
                    and att.get("capture_artifact_sha256") == result.get("capture_artifact_sha256")
                    and isinstance(att.get("hook_artifact_sha256"), str) and re.fullmatch(r"[a-fA-F0-9]{64}", att["hook_artifact_sha256"])
                    and att["hook_artifact_sha256"] == result.get("hook_artifact_sha256")
                    and att.get("request_id") == request_id and result.get("request_id") == request_id
                    for att in self.attestations()) and result["worker_claims_steering_verified"] is True
                result["verification_note"] = "Matched trusted independent artifact review." if result["steering_verified"] else "Worker telemetry requires independent artifact review."
            else:
                self.public_limit()
                result = self.simulation(body)
            # Public summaries contain neither prompt text nor generated/private text.
            summary = {k: result.get(k) for k in ("run_id", "mode", "model_id", "evidence_type", "decision", "latency_ms", "steering_verified")}
            summary.update(project_name=PROJECT_NAME, project_id=PROJECT_ID)
            self.store.put(summary)
            return result
        if method == "POST" and route == "/models/register":
            self.require_operator(headers)
            if not isinstance(body, dict) or set(body) != {"model_id", "revision"} or not isinstance(body.get("model_id"), str) or not MODEL_ID.fullmatch(body["model_id"]) or not isinstance(body.get("revision"), str) or not re.fullmatch(r"[a-fA-F0-9]{40}", body["revision"]):
                raise APIError(400, "invalid_model_registration", "Registration requires model_id and immutable 40-character revision.")
            if not self.settings.remote_url:
                self.not_configured()
            return self.worker_response("POST", route, body)
        if method == "POST" and route == "/evaluations":
            self.require_operator(headers)
            if not isinstance(body, dict) or set(body) - {"mode", "model_id", "conditions"} or body.get("mode") != "remote" or not isinstance(body.get("model_id"), str) or not MODEL_ID.fullmatch(body["model_id"]) or body.get("conditions") != list("ABCD"):
                raise APIError(400, "invalid_evaluation", "Remote evaluation requires a model_id and all A/B/C/D conditions.")
            if not self.settings.remote_url:
                self.not_configured()
            return self.worker_response("POST", route, body)
        raise APIError(404, "not_found", "Unknown API route.")

    @staticmethod
    def not_configured():
        raise APIError(503, "remote_unavailable", "A remote worker is not configured; no GPU operation was performed.")

    @staticmethod
    def orchestration():
        path = ROOT / ".ai/TASKS.json"
        if not path.exists():
            snapshot = ROOT / "api/orchestration_snapshot.json"
            if snapshot.is_file():
                data = json.loads(snapshot.read_text(encoding="utf-8"))
                data.update(project_name=PROJECT_NAME, project_id=PROJECT_ID, live=False)
                return data
            return {"project_name": PROJECT_NAME, "project_id": PROJECT_ID, "items": [], "live": False, "note": "Live Model Mountain local hub is not exposed by this deployment."}
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            tasks = data.get("tasks", data) if isinstance(data, dict) else data
            tasks = tasks.values() if isinstance(tasks, dict) else tasks
            if not isinstance(tasks, (list, type({}.values()))):
                raise ValueError("Invalid task snapshot")
            items = [{k: t.get(k) for k in ("id", "title", "status", "assigned_agent", "depends_on")} for t in tasks if isinstance(t, dict)]
            return {"project_name": PROJECT_NAME, "project_id": PROJECT_ID, "hub_name": "swarm_modelmountain_16f864bf", "items": items, "live": True, "scope": "sanitized_local_task_status", "hub_url": "http://127.0.0.1:8776"}
        except (OSError, ValueError, TypeError):
            raise APIError(503, "hub_unavailable", "The local task snapshot could not be read.") from None
