import json
import os
from pathlib import Path
import tempfile
import unittest
import threading
from http.server import ThreadingHTTPServer
from urllib.request import Request, urlopen
from urllib.error import HTTPError
from unittest.mock import patch
from model_mountain.control_api import APIError, ControlAPI, RunStore, Settings, sanitize


class FakeRemote:
    def __init__(self):
        self.calls = []
        self.result = {"run_id": "remote-1", "evidence_type": "REAL_MODEL", "answer": "Policy answer", "model_id": "Qwen/Qwen2-1.5B-Instruct",
                       "steering_verified": True, "access_token": "must-not-leak"}

    def request(self, method, path, payload=None):
        self.calls.append((method, path, payload))
        return dict(self.result)


class ControlAPITests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.remote = FakeRemote()
        self.store = RunStore(Path(self.temp.name) / "runs.db")
        self.api = ControlAPI(Settings(remote_url="https://worker.example", remote_token="worker-secret", operator_token="operator-secret"), remote=self.remote, store=self.store)
        self.request = {"model_id": "Qwen/Qwen2-1.5B-Instruct", "question": "What is the reimbursement limit?", "mode": "simulation"}
        self.auth = {"Authorization": "Bearer operator-secret"}

    def test_public_inference_is_explicitly_synthetic_and_inert(self):
        result = self.api.handle("POST", "/api/v1/inference", self.request)
        self.assertEqual(result["evidence_type"], "CPU_SYNTHETIC")
        self.assertFalse(result["model_executed"])
        self.assertFalse(result["steering_verified"])
        self.assertEqual(self.remote.calls, [])

    def test_remote_requires_operator_before_any_worker_call(self):
        with self.assertRaises(APIError) as error:
            self.api.handle("POST", "/api/v1/inference", {**self.request, "mode": "remote"})
        self.assertEqual(error.exception.status, 401)
        self.assertEqual(self.remote.calls, [])

    def test_released_abstention_preserves_abstain_verdict(self):
        result = self.api.handle("POST", "/api/v1/inference", {
            **self.request, "question": "What is the vacation policy?"})
        self.assertEqual(result["decision"], "abstain")
        self.assertTrue(result["answer"].startswith("Insufficient verified evidence"))
        self.assertEqual(result["reasons"], ["insufficient_verified_evidence"])

    def test_public_defense_lab_is_inert_and_cached(self):
        result = self.api.handle("GET", "/api/v1/defenses")
        self.assertEqual(len(result["defenses"]), 5)
        lab = self.api.handle("GET", "/api/v1/defenses/lab")
        self.assertEqual(lab["evidence_type"], "CPU_SYNTHETIC")
        self.assertIs(lab, self.api.handle("GET", "/api/v1/defenses/lab"))
        checked = self.api.handle("POST", "/api/v1/defenses/check", {
            "kind": "egress_tool", "tool": "send_email", "args": {"to": "sink@collector.invalid"}})
        self.assertEqual(checked["verdict"], "deny")
        self.assertEqual(self.remote.calls, [])

    def test_public_lab_rejects_malformed_and_privileged_fields(self):
        for body in ({"kind": "egress_tool", "args": []}, {"kind": "prompt_injection", "text": {}},
                     {"kind": "egress_tool", "private_data_read": "false"},
                     {"kind": "egress_tool", "admin_approved": True}, {"kind": "unknown"}):
            with self.assertRaises(APIError) as error:
                self.api.handle("POST", "/api/v1/defenses/check", body)
            self.assertEqual(error.exception.status, 400)
        for body in ({"opt_in": True, "model_id": []}, {"opt_in": False}):
            with self.assertRaises(APIError) as error:
                self.api.handle("POST", "/api/v1/steering/profile", body)
            self.assertEqual(error.exception.status, 400)
        self.assertEqual(self.remote.calls, [])

    def test_steering_editor_never_executes_a_model(self):
        catalog = self.api.handle("GET", "/api/v1/steering")
        self.assertEqual(len(catalog["models"]), 3)
        result = self.api.handle("POST", "/api/v1/steering/profile", {
            "model_id": "Qwen/Qwen2.5-1.5B-Instruct", "concept": "calm", "strength": 0.1,
            "block": 14, "opt_in": True})
        self.assertFalse(result["model_executed"])
        self.assertFalse(result["steering_applied"])
        self.assertEqual(result["status"], "vector_not_captured_yet")
        self.assertEqual(self.remote.calls, [])

    def test_browser_cannot_grant_privilege_or_redirect_worker(self):
        for field, value in (("identity_verified", True), ("tenant", "admin"), ("endpoint", "http://169.254.169.254"), ("vector_path", "/etc/passwd")):
            with self.assertRaises(APIError):
                self.api.handle("POST", "/api/v1/inference", {**self.request, field: value})
        self.assertEqual(self.remote.calls, [])

    def test_remote_report_is_not_independent_hook_verification(self):
        result = self.api.handle("POST", "/api/v1/inference", {**self.request, "mode": "remote"}, self.auth)
        self.assertFalse(result["steering_verified"])
        self.assertTrue(result["worker_claims_steering_verified"])
        self.assertNotIn("access_token", result)

    def test_remote_failure_never_becomes_fixture(self):
        self.remote.result = {"evidence_type": "CPU_SYNTHETIC"}
        with self.assertRaises(APIError) as error:
            self.api.handle("POST", "/api/v1/inference", {**self.request, "mode": "remote"}, self.auth)
        self.assertEqual(error.exception.code, "invalid_worker_evidence")
        self.assertEqual(self.store.list(), [])

    def test_prompt_and_generated_text_not_in_public_reports(self):
        self.api.handle("POST", "/api/v1/inference", self.request)
        report = json.dumps(self.api.handle("GET", "/api/v1/reports"))
        self.assertNotIn(self.request["question"], report)
        self.assertNotIn("$500", report)
        self.assertNotIn("operator-secret", report)

    def test_unconfigured_worker_fails_closed(self):
        api = ControlAPI(Settings(operator_token="operator-secret"), store=self.store)
        with self.assertRaises(APIError) as error:
            api.handle("POST", "/api/v1/inference", {**self.request, "mode": "remote"}, self.auth)
        self.assertEqual(error.exception.status, 503)

    def test_unsafe_or_credential_embedded_endpoints_refused(self):
        for url in ("http://remote.example", "https://user:pass@worker.example", "https://worker.example?key=secret", "file:///etc/passwd"):
            with self.assertRaises(APIError):
                Settings(remote_url=url, remote_token="test").checked_remote()
        self.assertEqual(Settings(remote_url="http://127.0.0.1:9000", remote_token="test").checked_remote(), "http://127.0.0.1:9000")

    def test_registration_requires_immutable_revision_and_auth(self):
        request = {"model_id": "Qwen/Qwen2-1.5B-Instruct", "revision": "main"}
        with self.assertRaises(APIError):
            self.api.handle("POST", "/api/v1/models/register", request, self.auth)
        self.assertEqual(self.remote.calls, [])
        request["revision"] = "a" * 40
        self.api.handle("POST", "/api/v1/models/register", request, self.auth)
        self.assertEqual(self.remote.calls[0][1], "/models/register")

    def test_invalid_modes_limits_and_profile_paths_refused(self):
        for patch in ({"condition": ""}, {"condition": []}, {"max_output_tokens": True}, {"max_output_tokens": 100000}, {"question": " "}, {"profile_id": "../../x"}):
            with self.assertRaises(APIError):
                self.api.handle("POST", "/api/v1/inference", {**self.request, **patch})

    def test_demo_limit_and_store_restart(self):
        for _ in range(60):
            self.api.public_limit()
        with self.assertRaises(APIError) as error:
            self.api.public_limit()
        self.assertEqual(error.exception.status, 429)
        self.store.put({"run_id": "persisted", "evidence_type": "CPU_SYNTHETIC"})
        self.assertEqual(RunStore(self.store.path).list()[0]["run_id"], "persisted")

    def test_sanitization_preserves_usage_counts(self):
        self.assertEqual(sanitize({"usage": {"input_tokens": 5}, "lease_token": "private"}), {"usage": {"input_tokens": 5}})

    def test_health_has_no_false_gpu_verification(self):
        result = self.api.handle("GET", "/api/v1/health")
        self.assertTrue(result["remote_configured"])
        self.assertFalse(result["real_mia_verified"])

    def test_hub_export_is_model_mountain_scoped_and_sanitized(self):
        root = Path(self.temp.name)
        (root / ".ai").mkdir()
        (root / ".ai/TASKS.json").write_text(json.dumps({"revision": 1, "tasks": [{"id": "MM-1", "title": "Model Mountain task", "status": "todo", "lease_token": "private", "result": {"secret": "private"}}]}))
        with patch("model_mountain.control_api.ROOT", root):
            result = self.api.handle("GET", "/api/v1/orchestration")
        self.assertEqual(result["project_name"], "Model Mountain")
        self.assertEqual(result["items"][0]["id"], "MM-1")
        self.assertNotIn("private", json.dumps(result))

    def test_remote_result_must_match_model_and_not_expose_credentials(self):
        self.remote.result["model_id"] = "other/model"
        with self.assertRaises(APIError) as error:
            self.api.handle("POST", "/api/v1/inference", {**self.request, "mode": "remote"}, self.auth)
        self.assertEqual(error.exception.code, "invalid_worker_result")
        self.remote.result["model_id"] = self.request["model_id"]
        self.remote.result["answer"] = "Leaked operator-secret"
        with self.assertRaises(APIError) as error:
            self.api.handle("POST", "/api/v1/inference", {**self.request, "mode": "remote"}, self.auth)
        self.assertEqual(error.exception.code, "sensitive_output_withheld")
        self.assertEqual(self.store.list(), [])

    def test_reviewed_hook_attestation_is_bound_to_exact_model_and_profile(self):
        registry = Path(self.temp.name) / "attestations.json"
        attestation = {"id": "att-1", "model_id": self.request["model_id"], "model_revision": "a"*40,
                       "ibm_revision": "b"*40, "profile_sha256": "c"*64, "capture_artifact_sha256": "d"*64,
                       "run_id": "remote-1", "hook_artifact_sha256": "f"*64,
                       "request_id": "server-request-1",
                       "reviewers": ["codex", "claude"], "hook_executed": True, "evidence_type": "REAL_IBM_MIA"}
        registry.write_text(json.dumps({"project_id": "16f864bfa1303fc9", "items": [attestation]}))
        api = ControlAPI(Settings(remote_url="https://worker.example", remote_token="worker-secret", operator_token="operator-secret", attestation_file=str(registry)), store=self.store, remote=self.remote)
        self.remote.result.update(attestation_ref="att-1", model_revision="a"*40, profile_sha256="c"*64,
                                  ibm_revision="b"*40, capture_artifact_sha256="d"*64, hook_artifact_sha256="f"*64, request_id="server-request-1")
        with patch("model_mountain.control_api.uuid.uuid4", return_value="server-request-1"):
            result = api.handle("POST", "/api/v1/inference", {**self.request, "mode": "remote"}, self.auth)
        self.assertTrue(result["steering_verified"])
        result = api.handle("POST", "/api/v1/inference", {**self.request, "mode": "remote", "question": "A different question"}, self.auth)
        self.assertFalse(result["steering_verified"])
        self.remote.result["run_id"] = "unreviewed-new-run"
        result = api.handle("POST", "/api/v1/inference", {**self.request, "mode": "remote"}, self.auth)
        self.assertFalse(result["steering_verified"])
        self.remote.result["run_id"] = "remote-1"
        self.remote.result["profile_sha256"] = "e"*64
        result = api.handle("POST", "/api/v1/inference", {**self.request, "mode": "remote"}, self.auth)
        self.assertFalse(result["steering_verified"])

    def test_untyped_worker_metadata_never_poison_public_reports(self):
        for field, value in (("decision", {"debug": "confidential"}), ("latency_ms", float("nan")), ("latency_ms", float("inf")), ("reasons", ["worker-secret"])):
            original = dict(self.remote.result)
            self.remote.result[field] = value
            with self.assertRaises(APIError):
                self.api.handle("POST", "/api/v1/inference", {**self.request, "mode": "remote"}, self.auth)
            self.remote.result = original
        self.assertEqual(self.store.list(), [])
        json.dumps(self.api.handle("GET", "/api/v1/reports"), allow_nan=False)

    def test_unknown_worker_fields_dropped_and_header_case_ignored(self):
        self.remote.result.update(debug="worker-secret", hf_token="private", kaggle_key="private")
        result = self.api.handle("POST", "/api/v1/inference", {**self.request, "mode": "remote"}, {"AUTHORIZATION": "Bearer operator-secret"})
        self.assertNotIn("debug", result)
        self.assertNotIn("hf_token", result)
        self.assertNotIn("kaggle_key", result)
        self.assertNotIn("worker-secret", json.dumps(result))

    def test_all_worker_metadata_routes_drop_extras_and_hold_credentials(self):
        for path in ("/models", "/vectors", "/jobs"):
            self.remote.result = {"items": [{"id": "item-1", "debug": "worker-secret", "hf_token": "private"}], "debug": "worker-secret"}
            result = self.api.handle("GET", "/api/v1" + path, headers=self.auth)
            self.assertNotIn("worker-secret", json.dumps(result))
            self.assertNotIn("hf_token", json.dumps(result))
            self.remote.result = {"items": [{"id": "worker-secret"}]}
            with self.assertRaises(APIError):
                self.api.handle("GET", "/api/v1" + path, headers=self.auth)
            self.remote.result = {"items": [{"id": {"debug": "confidential prompt"}}]}
            with self.assertRaises(APIError):
                self.api.handle("GET", "/api/v1" + path, headers=self.auth)


class HTTPBoundaryTests(unittest.TestCase):
    def test_http_routes_enforce_json_body_limits_and_public_remote_boundary(self):
        from api.index import handler
        with tempfile.TemporaryDirectory() as folder:
            api = ControlAPI(Settings(data_dir=folder, operator_token="operator-secret"))
            with patch("api.index._control", api):
                server = ThreadingHTTPServer(("127.0.0.1", 0), handler)
                thread = threading.Thread(target=server.serve_forever, daemon=True)
                thread.start()
                base = f"http://127.0.0.1:{server.server_port}"
                try:
                    with urlopen(base + "/api/v1/health", timeout=5) as response:
                        self.assertEqual(json.load(response)["project_name"], "Model Mountain")
                        self.assertEqual(response.headers["Cache-Control"], "no-store")
                    requests = [
                        (Request(base + "/api/v1/inference", data=b"{}", headers={"Content-Type": "text/plain"}), 415),
                        (Request(base + "/api/v1/inference", data=b"x" * 32769, headers={"Content-Type": "application/json"}), 413),
                        (Request(base + "/api/v1/inference", data=b"{invalid", headers={"Content-Type": "application/json"}), 400),
                        (Request(base + "/api/v1/inference", data=json.dumps({"question":"test", "model_id":"Qwen/Qwen2-1.5B-Instruct", "mode":"remote"}).encode(), headers={"Content-Type": "application/json"}), 401)]
                    for request, expected_status in requests:
                        with self.assertRaises(HTTPError) as error:
                            urlopen(request, timeout=5)
                        self.assertEqual(error.exception.code, expected_status)
                        result = json.loads(error.exception.read())
                        self.assertEqual(result["project_name"], "Model Mountain")
                        self.assertIn("error", result)
                finally:
                    server.shutdown()
                    server.server_close()
                    thread.join(timeout=5)


class KaggleBatchBoundaryTests(unittest.TestCase):
    def setUp(self):
        from api.kaggle_jobs import KaggleBatch
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        (self.root / "api").mkdir()
        (self.root / "api/model_catalog.json").write_text(json.dumps({"items": [{"model_id": "Qwen/test", "revision": "a"*40}]}))
        self.calls = []
        self.batch = KaggleBatch(self.root, self.root / "jobs", "testowner", runner=self.run_cli, pause=lambda _: None)
        self.batch.cli = lambda: "test-kaggle-cli"

    def run_cli(self, argv, timeout=60):
        self.calls.append(argv)
        if "build_kernel.py" in " ".join(argv):
            bundle = self.root / "model_mountain_results/kaggle_bundle/test"
            bundle.mkdir(parents=True)
            (bundle / "kernel-metadata.json").write_text('{}')
            return str(bundle)
        if "push" in argv:
            return "Kernel version 1 successfully pushed."
        if "status" in argv:
            return 'has status "KernelWorkerStatus.COMPLETE"'
        if "output" in argv:
            destination = Path(argv[argv.index("-p") + 1]) / "mm_results"
            destination.mkdir(parents=True)
            (destination / "summary.json").write_text(json.dumps({"config": {"models": ["Qwen/test"]}, "preflight_usable": False, "phases": []}))
            return ""
        raise AssertionError(argv)

    def test_invalid_inputs_never_reach_cli_or_create_fence(self):
        from api.kaggle_jobs import BatchError
        for body in ({"model_ids": ["other/model"]}, {"model_ids": ["Qwen/test"], "owner": "attacker"}, {"model_ids": ["Qwen/test"], "phase": "shell"}):
            with self.assertRaises(BatchError):
                self.batch.prepare(body)
        self.assertEqual(self.calls, [])
        self.assertFalse((self.root / "jobs/active.lock").exists())
        with self.assertRaises(BatchError):
            self.batch.get("../../private")

    def test_complete_kernel_with_failed_preflight_is_blocked_not_model_success(self):
        job = self.batch.prepare({"model_ids": ["Qwen/test"], "phase": "preflight"})
        self.batch.execute(job["id"])
        record = self.batch.get(job["id"])
        self.assertEqual(record["status"], "blocked")
        self.assertFalse(record["model_executed"])
        self.assertFalse(record["independently_verified"])
        self.assertFalse((self.root / "jobs/active.lock").exists())
        output_call = next(c for c in self.calls if "output" in c)
        self.assertIn("--file-pattern", output_call)

    def test_uncertain_push_is_fenced_and_never_automatically_retried(self):
        from api.kaggle_jobs import BatchError
        original = self.batch.runner
        def interrupted(argv, timeout=60):
            if "push" in argv:
                raise TimeoutError("Unknown submission outcome")
            return original(argv, timeout)
        self.batch.runner = interrupted
        job = self.batch.prepare({"model_ids": ["Qwen/test"], "phase": "preflight"})
        self.batch.execute(job["id"])
        self.assertEqual(self.batch.get(job["id"])["status"], "submission_unknown")
        with self.assertRaises(BatchError):
            self.batch.prepare({"model_ids": ["Qwen/test"], "phase": "preflight"})

    def test_cloud_disabled_and_submission_requires_operator(self):
        from api.kaggle_jobs import KaggleBatch
        with patch.dict(os.environ, {"MODEL_MOUNTAIN_KAGGLE_ENABLED": "1", "MODEL_MOUNTAIN_KAGGLE_OWNER": "testowner"}):
            self.assertIsNone(KaggleBatch.from_environment(self.root, vercel=True))
        api = ControlAPI(Settings(operator_token="test-operator", data_dir=str(self.root / "control")), batch=self.batch)
        with self.assertRaises(APIError) as error:
            api.handle("POST", "/api/v1/jobs", {"model_ids": ["Qwen/test"]})
        self.assertEqual(error.exception.status, 401)
        self.assertEqual(self.batch.list(), [])


class ExperimentsRouteTests(unittest.TestCase):
    def test_pending_then_ingested(self):
        import model_mountain.control_api as C
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            (root / "api").mkdir()
            with patch.object(C, "ROOT", root):
                api = ControlAPI(Settings(), store=RunStore(root / "r.db"), batch=False or None)
                self.assertEqual(api.handle("GET", "/api/v1/experiments")["status"], "pending")
                (root / "api/experiments.json").write_text(json.dumps({"schema": "mm-experiments-v1", "project_id": "wrong"}))
                with self.assertRaises(APIError):
                    api.handle("GET", "/api/v1/experiments")
                (root / "api/experiments.json").write_text(json.dumps({"schema": "mm-experiments-v1", "project_id": "16f864bfa1303fc9", "models": []}))
                self.assertEqual(api.handle("GET", "/api/v1/experiments")["status"], "ingested")
