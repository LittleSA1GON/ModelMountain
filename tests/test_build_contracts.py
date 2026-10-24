"""Public contract examples preserve evidence and authorization boundaries."""
import json
from pathlib import Path
import unittest


class BuildContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.examples = json.loads((Path(__file__).resolve().parents[1] / "docs/build/contracts/examples.json").read_text())

    def test_unavailable_remote_is_not_verified(self):
        self.assertFalse(self.examples["health"]["remote_configured"])
        self.assertFalse(self.examples["health"]["real_mia_verified"])

    def test_cpu_response_cannot_attest_hook_or_measurements(self):
        result = self.examples["inference_response"]
        self.assertEqual(result["evidence_type"], "CPU_SYNTHETIC")
        self.assertFalse(result["steering_verified"])
        self.assertIsNone(result["attestation_ref"])
        self.assertIsNone(result["latency_ms"])

    def test_browser_request_does_not_supply_authority(self):
        request = self.examples["inference_request"]
        self.assertFalse({"tenant", "identity_verified", "trusted_gateway", "endpoint", "vector_path", "api_key"} & request.keys())
        self.assertIn(request["mode"], ("simulation", "remote"))
        self.assertLessEqual(request["max_output_tokens"], 512)

    def test_abstention_withholds_unsupported_claim(self):
        result = self.examples["inference_response"]
        self.assertEqual(result["decision"], "abstain")
        self.assertEqual(result["citations"], [])
        self.assertIn("no_authorized_evidence", result["reasons"])


if __name__ == "__main__":
    unittest.main()
