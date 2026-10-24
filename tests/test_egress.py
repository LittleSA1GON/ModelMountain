import unittest

from model_mountain.egress import (EgressPolicy, SessionTaint, check_tool_call, domain_allowed, extract_urls,
                                   sanitize_output, url_carries_data)

P = EgressPolicy(allowed_domains=("acme.example",))
SECRET = "CANARY-DEMO-7Q2X9"


class UrlExtractionTests(unittest.TestCase):
    def test_finds_inline_reference_html_and_bare(self):
        text = ("See ![logo](https://cdn.other.example/a.png) and [docs](https://wiki.acme.example/x).\n"
                "Also ![pic][r1] here.\n\n[r1]: https://img.other.example/p.png\n"
                "<img src=\"https://h.other.example/t.gif\"> and https://bare.other.example/z")
        kinds = {(f["kind"], f.get("reference_style", False)) for f in extract_urls(text)}
        self.assertIn(("image", False), kinds)
        self.assertIn(("link", False), kinds)
        self.assertIn(("image", True), kinds)       # reference-style image is detected, not only inline
        self.assertIn(("html", False), kinds)
        self.assertIn(("bare", False), kinds)

    def test_domain_allowlist_is_exact_or_subdomain(self):
        self.assertTrue(domain_allowed("wiki.acme.example", ("acme.example",)))
        self.assertTrue(domain_allowed("bob@acme.example", ("acme.example",)))
        self.assertFalse(domain_allowed("acme.example.other.example", ("acme.example",)))
        self.assertFalse(domain_allowed("notacme.example", ("acme.example",)))

    def test_url_data_carrier(self):
        self.assertIn("protected_value_in_url", url_carries_data(f"https://x.example/i?d={SECRET}", (SECRET,)))
        self.assertIn("secret_pattern_in_url", url_carries_data(f"https://x.example/{SECRET}"))
        self.assertEqual(url_carries_data("https://wiki.acme.example/onboarding"), [])


class OutputSanitizerTests(unittest.TestCase):
    def test_external_images_removed_internal_links_kept(self):
        out = sanitize_output("Guide: [onboarding](https://wiki.acme.example/start) ![x](https://cdn.other.example/a.png)", P)
        self.assertIn("https://wiki.acme.example/start", out["text"])
        self.assertNotIn("cdn.other.example", out["text"])
        self.assertTrue(out["modified"])

    def test_reference_style_image_removed(self):
        out = sanitize_output("Summary ![s][ref]\n\n[ref]: https://img.other.example/p.png", P)
        self.assertNotIn("img.other.example", out["text"])

    def test_internal_url_with_secret_still_removed_and_text_secret_withheld(self):
        out = sanitize_output(f"[open](https://wiki.acme.example/p?k={SECRET})", P, (SECRET,))
        self.assertNotIn(SECRET, out["text"])
        out2 = sanitize_output(f"The key is {SECRET}.", P, (SECRET,))
        self.assertTrue(out2["withhold"])

    def test_clean_answer_untouched(self):
        out = sanitize_output("Laptop pickup is at IT desk 4 on day 1.", P)
        self.assertFalse(out["modified"])
        self.assertEqual(out["findings"], [])


class ToolEgressTests(unittest.TestCase):
    def test_internal_email_allowed_external_denied(self):
        t = SessionTaint()
        self.assertTrue(check_tool_call("send_email", {"to": "dana@acme.example", "subject": "hi", "body": "ok"}, P, t)["allowed"])
        r = check_tool_call("send_email", {"to": "x@other.example", "subject": "hi", "body": "ok"}, P, t)
        self.assertEqual(r["decision"], "deny")
        self.assertIn("non_allowlisted_destination:to", r["reasons"])

    def test_bcc_to_unapproved_domain_denied(self):
        r = check_tool_call("send_email", {"to": "dana@acme.example", "bcc": "copy@other.example",
                                           "subject": "Invoice", "body": "attached"}, P, SessionTaint())
        self.assertIn("non_allowlisted_destination:bcc", r["reasons"])

    def test_secret_in_any_argument_denied_even_for_non_sink_tool(self):
        t = SessionTaint(protected_values=(SECRET,))
        r = check_tool_call("add", {"a": 2, "b": 5, "note": SECRET}, P, t)
        self.assertFalse(r["allowed"])
        self.assertIn("protected_value_in_tool_arguments", r["reasons"])

    def test_private_data_to_public_sink_denied(self):
        t = SessionTaint(private_data_read=True)
        r = check_tool_call("create_pull_request", {"repo": "public-repo", "title": "t", "body": "b"}, P, t)
        self.assertIn("private_data_to_shared_or_public_sink", r["reasons"])

    def test_lethal_trifecta_requires_human_approval(self):
        t = SessionTaint(private_data_read=True, untrusted_content_seen=True)
        r = check_tool_call("send_email", {"to": "dana@acme.example", "subject": "s", "body": "b"}, P, t)
        self.assertEqual(r["decision"], "require_human_approval")
        self.assertFalse(r["allowed"])


if __name__ == "__main__":
    unittest.main()


class SinkFormTests(unittest.TestCase):
    def test_missing_destination_and_unsafe_url_forms_denied(self):
        t = SessionTaint()
        self.assertIn("missing_destination", check_tool_call("http_post", {}, P, t)["reasons"])
        self.assertIn("unsafe_url_form:url", check_tool_call("http_get", {"url": "ftp://files.acme.example/x"}, P, t)["reasons"])
        self.assertIn("unsafe_url_form:url", check_tool_call("http_get", {"url": "https://u:p@wiki.acme.example/"}, P, t)["reasons"])
        self.assertTrue(check_tool_call("http_get", {"url": "https://wiki.acme.example/page"}, P, t)["allowed"])


class GatewayEgressIntegrationTests(unittest.TestCase):
    def _gw(self, text, tool="", args=None):
        from model_mountain.core import Document
        from model_mountain.gateway import GatewayRequest, ModelMountainGateway, VerifiedIdentity

        def backend(system, data, n):
            return {"text": text, "proposed_tool": tool, "tool_args": args or {}, "engine": "TEST_FIXTURE"}
        gw = ModelMountainGateway(backend, require_mia=False, protected_literals=(SECRET,))
        doc = Document.approved("onboarding", "Laptop pickup is at IT desk 4 on day 1.")
        return gw.evaluate(GatewayRequest("Where do I pick up my laptop?", (doc,),
                                          VerifiedIdentity("acme", "e1", trusted_gateway=True)))

    def test_trace_records_every_stage_on_success(self):
        r = self._gw("Laptop pickup is at IT desk 4 on day 1.")
        self.assertTrue(r["allowed"])
        stages = [t["stage"] for t in r["trace"]]
        for s in ("identity", "extraction_admission", "prompt_injection", "rag_integrity", "model", "egress_output",
                  "tool_authorization"):
            self.assertIn(s, stages)

    def test_external_image_stripped_before_release(self):
        r = self._gw("Desk 4. ![x](https://cdn.other.example/p.png)")
        self.assertTrue(r["allowed"])
        self.assertNotIn("cdn.other.example", r["response"])
        self.assertEqual([t for t in r["trace"] if t["stage"] == "egress_output"][0]["verdict"], "sanitized")

    def test_external_send_tool_denied_by_egress(self):
        r = self._gw("Sending now.", tool="send_email", args={"to": "x@other.example", "subject": "s", "body": "b"})
        self.assertFalse(r["allowed"])
        self.assertIn("tool_egress_denied", r["reasons"])


class CampaignDetectorTests(unittest.TestCase):
    def test_coordinated_accounts_flagged_single_accounts_not(self):
        from model_mountain.extraction import synthetic_campaign_suite, template_fingerprint
        r = synthetic_campaign_suite()
        self.assertEqual(r["per_account_limits_blocked"], 0)
        self.assertGreater(r["campaign_detector_blocked"], 0)
        self.assertTrue(r["benign_unrelated_request_allowed"])
        self.assertEqual(template_fingerprint("Explain topic 101 now"), template_fingerprint("Explain  topic 202 now"))
