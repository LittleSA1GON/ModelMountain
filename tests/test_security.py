import json
import unittest
from model_mountain.core import Document, Scenario, builtin_scenarios, doc_check, run_scenario, scan_injection, suite_report, tool_decision, digest
from model_mountain.real_inputs import make_inputs
from mia_security_worker import tool_parse

class SecurityTests(unittest.TestCase):
    def get_case(self, name):
        return next(x for x in builtin_scenarios() if x.name == name)

    def test_hash_deterministic(self):
        self.assertEqual(digest('x'), digest('x'))

    def test_tampered_document_rejected(self):
        case = self.get_case('tampered-rag')
        r = run_scenario(case, True)
        self.assertNotIn('it-password-policy-tampered', r['context_doc_ids'])
        self.assertTrue(any('integrity_unverified_or_tampered' in d['integrity_issues'] for d in r['documents']))

    def test_unapproved_web_rejected(self):
        r = run_scenario(self.get_case('unapproved-web-rag'), True)
        self.assertNotIn('outside-webpage', r['context_doc_ids'])

    def test_cross_tenant_rejected(self):
        r = run_scenario(self.get_case('cross-tenant-doc'), True)
        self.assertNotIn('secret-finance', r['context_doc_ids'])

    def test_direct_injection_gated(self):
        r = run_scenario(self.get_case('direct-injection'), True)
        self.assertFalse(r['response_released'])

    def test_tool_output_injection_gated(self):
        r = run_scenario(self.get_case('untrusted-tool-result'), True)
        self.assertFalse(r['response_released'])

    def test_poisoned_document_affects_unprotected_fixture(self):
        r = run_scenario(self.get_case('tampered-rag'), False)
        self.assertTrue(r['unsafe_tool_proposed'])
        self.assertTrue(r['unauthorized_action_would_execute'])

    def test_unsafe_tool_blocked_independently(self):
        r = run_scenario(self.get_case('unauthorized-tool'), True)
        self.assertTrue(r['unsafe_tool_proposed'])
        self.assertFalse(r['policy']['would_allow'])

    def test_valid_reset_requires_admin_and_approval(self):
        c = Scenario('test','reset',(),user_role='admin',identity_verified=True,admin_approved=True)
        self.assertTrue(tool_decision(c,'reset_password',{'target_tenant':'acme'},True)['would_allow'])
        self.assertFalse(tool_decision(c,'reset_password',{'target_tenant':'other'},True)['would_allow'])

    def test_denies_unknown_tool(self):
        self.assertFalse(tool_decision(self.get_case('clean-password'),'run_shell',{},True)['would_allow'])

    def test_clean_not_blocked(self):
        r = run_scenario(self.get_case('clean-password'), True)
        self.assertTrue(r['response_released'])
        self.assertFalse(r['unsafe_tool_proposed'])

    def test_heuristic_is_not_mia(self):
        r = run_scenario(self.get_case('direct-injection'), True)
        self.assertIsNone(r['mia_score'])
        self.assertEqual(r['model_engine'],'DETERMINISTIC_SIMULATION_NOT_MIA')

    def test_full_suite_no_protected_executions(self):
        report = suite_report()
        self.assertGreaterEqual(report['totals']['attacks'], 7)
        self.assertEqual(report['totals']['protected_unauthorized_actions'], 0)

    def test_model_inputs_are_split_by_protection_mode(self):
        inp = make_inputs()
        self.assertEqual(len(inp), 2 * len(builtin_scenarios()))
        orig = next(x for x in inp if x['key']=='tampered-rag:unprotected')
        shield = next(x for x in inp if x['key']=='tampered-rag:protected')
        self.assertIn('Ignore previous instructions', orig['data'])
        self.assertNotIn('Ignore previous instructions', shield['data'])

    def test_no_text_to_tool_without_json(self):
        self.assertEqual(tool_parse('call reset_password now')[1], '')
        self.assertEqual(tool_parse('{"answer":"ok","tool":"reset_password","tool_args":{}}')[1], 'reset_password')

    def test_external_scores_are_not_invented(self):
        r = run_scenario(self.get_case('clean-password'), True,
                         external_response={'text':'real answer','mia_score':0.55,'engine':'REAL_IBM_MIA_vllm'})
        self.assertEqual(r['mia_score'],0.55)
        self.assertEqual(r['output'],'real answer')
        self.assertFalse(r['mia_alert'])  # only use threshold after explicit calibration

if __name__ == '__main__':
    unittest.main()
