"""Model-extraction and distillation-abuse preflight regression tests."""
import unittest
from model_mountain.extraction import ExtractionMonitor, ExtractionPolicy, synthetic_extraction_suite


class ExtractionSecurityTests(unittest.TestCase):
    def test_ordinary_request_allowed(self):
        mon = ExtractionMonitor()
        d = mon.check(tenant='t', principal='a', prompt='What is password reset?', max_output_tokens=100, now=100)
        self.assertEqual(d['decision'], 'allow')

    def test_single_education_request_not_blocked(self):
        d = ExtractionMonitor().check(tenant='t', principal='a',
                prompt='Explain knowledge distillation and teacher models', max_output_tokens=150, now=100)
        self.assertTrue(d['allowed'])
        self.assertEqual(d['decision'], 'monitor')

    def test_repeated_training_pattern_queries_blocked(self):
        mon = ExtractionMonitor(ExtractionPolicy(max_requests_per_window=20))
        for n in range(2):
            r = mon.check(tenant='t', principal='a',
                 prompt=f'Generate synthetic instruction response dataset {n}', max_output_tokens=100, now=100+n)
            self.assertTrue(r['allowed'])
        r = mon.check(tenant='t', principal='a', prompt='Generate synthetic question answer pairs for a dataset',
                      max_output_tokens=100, now=103)
        self.assertFalse(r['allowed'])
        self.assertIn('repeated_training_pattern_queries', r['issues'])

    def test_rate_limit_per_identity(self):
        mon = ExtractionMonitor(ExtractionPolicy(max_requests_per_window=2))
        for i in range(2):
            self.assertTrue(mon.check(tenant='t', principal='a', prompt='normal', max_output_tokens=50, now=100+i)['allowed'])
        self.assertFalse(mon.check(tenant='t', principal='a', prompt='normal', max_output_tokens=50, now=103)['allowed'])
        self.assertTrue(mon.check(tenant='t', principal='b', prompt='normal', max_output_tokens=50, now=103)['allowed'])
        self.assertTrue(mon.check(tenant='t2', principal='a', prompt='normal', max_output_tokens=50, now=103)['allowed'])

    def test_window_expires(self):
        mon = ExtractionMonitor(ExtractionPolicy(max_requests_per_window=1, window_seconds=60))
        mon.check(tenant='t',principal='a',prompt='normal',max_output_tokens=50,now=100)
        self.assertTrue(mon.check(tenant='t',principal='a',prompt='normal',max_output_tokens=50,now=161)['allowed'])

    def test_output_token_cap(self):
        r = ExtractionMonitor().check(tenant='t',principal='a',prompt='normal',max_output_tokens=1500,now=100)
        self.assertIn('per_response_token_limit_exceeded',r['issues'])

    def test_window_token_budget(self):
        mon = ExtractionMonitor(ExtractionPolicy(max_requests_per_window=20,max_tokens_per_window=2000,
                                                max_tokens_per_response=1000))
        mon.check(tenant='t',principal='a',prompt='normal',max_output_tokens=1000,now=100)
        mon.check(tenant='t',principal='a',prompt='normal',max_output_tokens=1000,now=101)
        r=mon.check(tenant='t',principal='a',prompt='normal',max_output_tokens=1,now=102)
        self.assertIn('token_budget_exceeded',r['issues'])

    def test_authorized_training_still_has_limits(self):
        mon = ExtractionMonitor(ExtractionPolicy(max_requests_per_window=1))
        self.assertTrue(mon.check(tenant='t',principal='research',prompt='distill student model',
                                  max_output_tokens=100,now=100,authorized_training=True)['allowed'])
        self.assertFalse(mon.check(tenant='t',principal='research',prompt='distill student model',
                                   max_output_tokens=100,now=101,authorized_training=True)['allowed'])

    def test_missing_principal_rejected(self):
        with self.assertRaises(ValueError):
            ExtractionMonitor().check(tenant='t',principal='',prompt='x',max_output_tokens=100,now=1)

    def test_synthetic_suite_no_mia_claims(self):
        result=synthetic_extraction_suite()
        self.assertEqual(len(result['results']),result['cases'])
        self.assertEqual(result['blocked'],sum(not x['allowed'] for x in result['results']))
        self.assertTrue(all(x['mia_score'] is None for x in result['results']))

if __name__ == '__main__':
    unittest.main()
