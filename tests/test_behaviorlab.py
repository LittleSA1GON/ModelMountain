"""CPU verification: vector learner uses explicitly labeled synthetic TEST activations."""
import hashlib
import json
from pathlib import Path
import tempfile
import unittest

from model_mountain.behaviorlab import (validate_pairs,validate_captures,fit_captures,
                                score_activation,select_experimental_profile,
                                TrustedRoutingContext)
from model_mountain.steering import SteeringProfile

HERE=Path(__file__).resolve().parents[1]


def fixture_capture():
    # Deliberately synthetic vectors; never report as actual model internals.
    rows=[]
    for i,split in enumerate(['train','train','train','validation','test','test']):
        # Uncorrelated task offset should not erase the desired/undesired contrast.
        scale=i*.03
        rows.append({'id':f'p{i}','task_group':f'g{i}','split':split,
                     'positive':[2+scale,0.3,0.1,0.0],
                     'negative':[-2+scale,0.3,0.1,0.0]})
    return {'schema_version':1,'engine':'SYNTHETIC_TEST_FIXTURE',
            'model':'fixture/model','behavior':'grounding','layer_zero_based':2,
            'hidden_dim':4,'dataset_sha256':'test-fingerprint','pairs':rows}


class BehaviorLabTests(unittest.TestCase):
    def test_dataset_separations(self):
        for name in ['grounding','injection_resistance','abstention']:
            data=json.loads((HERE/'examples'/f'behavior_{name}.json').read_text())
            self.assertTrue(validate_pairs(data)['training_ready'])

    def test_reject_group_leakage(self):
        data=json.loads((HERE/'examples'/'behavior_grounding.json').read_text())
        data['pairs'][-1]['task_group']=data['pairs'][0]['task_group']
        with self.assertRaisesRegex(ValueError,'leakage'):
            validate_pairs(data)

    def test_reject_duplicate_prompt(self):
        data=json.loads((HERE/'examples'/'behavior_grounding.json').read_text())
        data['pairs'][1]['positive']=data['pairs'][0]['positive']
        with self.assertRaisesRegex(ValueError,'leakage'):
            validate_pairs(data)

    def test_real_only_by_default(self):
        with self.assertRaises(ValueError):validate_captures(fixture_capture())
        self.assertEqual(validate_captures(fixture_capture(),allow_synthetic=True)['hidden_dim'],4)

    def test_fit_and_score_mean_and_pca(self):
        for method in ['mean_diff','pca_pairwise']:
            with self.subTest(method=method), tempfile.TemporaryDirectory() as root:
                capture=Path(root)/'capture.json';capture.write_text(json.dumps(fixture_capture()))
                with self.assertRaises(ValueError):fit_captures(capture,Path(root)/'blocked')
                report=fit_captures(capture,Path(root)/'output',method,allow_synthetic=True)
                self.assertEqual(report['approval'],'SYNTHETIC_TEST_ONLY')
                self.assertEqual(report['heldout_test_metrics']['accuracy'],1.0)
                positive=score_activation(Path(root)/'output',[2.0,0.3,0.1,0],model='fixture/model',layer=2)
                negative=score_activation(Path(root)/'output',[-2.0,0.3,0.1,0],model='fixture/model',layer=2)
                self.assertTrue(positive['predicted_desired_behavior'])
                self.assertFalse(negative['predicted_desired_behavior'])
                with self.assertRaisesRegex(ValueError,'mismatch'):
                    score_activation(Path(root)/'output',[2,0,0,0],model='different',layer=2)
                vector=Path(root)/'output'/'vector.pt'
                vector.write_bytes(vector.read_bytes()+b'tampered')
                with self.assertRaisesRegex(ValueError,'integrity'):
                    score_activation(Path(root)/'output',[2,0,0,0],model='fixture/model',layer=2)

    def test_invalid_capture_vectors(self):
        data=fixture_capture();data['pairs'][0]['positive'][0]=float('nan')
        with self.assertRaises(ValueError):validate_captures(data,allow_synthetic=True)

    def test_router_never_bypasses_authorization(self):
        p=SteeringProfile(model='fixture/model',vector_path='/trusted/vector.pt',optimal_layer=2)
        configs={'grounding':p,'injection_resistance':p}
        ctx=TrustedRoutingContext('retrieved_document','fixture/model',operation='tool_action',principal_authorized=False)
        self.assertEqual(select_experimental_profile(ctx,configs,explicit_opt_in=True)['decision'],'BLOCK_UNAUTHORIZED_ACTION')
        ctx=TrustedRoutingContext('retrieved_document','fixture/model')
        self.assertEqual(select_experimental_profile(ctx,configs)['decision'],'NO_STEERING_NOT_OPTED_IN')
        self.assertEqual(select_experimental_profile(ctx,configs,explicit_opt_in=True)['behavior'],'injection_resistance')
        with self.assertRaises(ValueError):
            select_experimental_profile(TrustedRoutingContext('retrieved_document','different'),configs,explicit_opt_in=True)

if __name__=='__main__':unittest.main()

# Additional transparent output-marker benchmarking tests (no model inference).
class BehaviorEvalTests(unittest.TestCase):
    def test_benchmark_markers(self):
        from model_mountain.behavior_eval import validate_scenarios,grade_outputs
        cases=json.loads((HERE/'examples'/'heldout_security_reliability.json').read_text())
        self.assertEqual(validate_scenarios(cases)['attack'],1)
        results={c['id']:{'baseline':c['forbidden_contains'], 'steered':c['expected_contains']}
                 for c in cases}
        report=grade_outputs(cases,results)
        self.assertEqual(report['by_kind']['attack']['steered']['literal_pass_rate'],1)
        self.assertEqual(report['by_kind']['attack']['baseline']['literal_pass_rate'],0)
        self.assertIn('REQUIRE',report['evidence_type'])

    def test_reject_missing_eval(self):
        from model_mountain.behavior_eval import grade_outputs
        cases=json.loads((HERE/'examples'/'heldout_security_reliability.json').read_text())
        with self.assertRaisesRegex(ValueError,'Missing'):
            grade_outputs(cases,{})

class ProfileExportTests(unittest.TestCase):
    def test_synthetic_profile_rejected(self):
        from model_mountain.behaviorlab import export_mia_profile
        with tempfile.TemporaryDirectory() as root:
            f=Path(root)/'data.json';f.write_text(json.dumps(fixture_capture()))
            fit_captures(f,Path(root)/'fit',allow_synthetic=True)
            with self.assertRaisesRegex(ValueError,'Synthetic'):
                export_mia_profile(Path(root)/'fit',Path(root)/'steer.json',allow_experimental=True)
