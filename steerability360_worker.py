"""Optional real IBM AI Steerability 360 pipeline experiment (GPU required).

AI Steerability 360 fits its own in-memory/portable vectors. These are NOT
silently treated as MIA torch `dir` artifacts. For MIA-compatible .pt exports,
use Model Mountain's real MIA capture + model_mountain.behaviorlab fit instead.

API reference: https://generative-computing.github.io/steerability/home/quickstart/
"""
import argparse
import json
from pathlib import Path
from model_mountain.behaviorlab import validate_pairs


def main():
    p=argparse.ArgumentParser()
    p.add_argument('--dataset',required=True)
    p.add_argument('--model',default='Qwen/Qwen2-1.5B-Instruct')
    p.add_argument('--layer',type=int,default=14)
    p.add_argument('--strength',type=float,default=0.5)
    p.add_argument('--output',required=True)
    p.add_argument('--max-new-tokens',type=int,default=80)
    args=p.parse_args()
    data=json.loads(Path(args.dataset).read_text())
    validity=validate_pairs(data)
    if not validity['training_ready']:
        raise ValueError('Use independent train/validation/test task groups')
    if not (-5<=args.strength<=5) or args.layer<0:
        raise ValueError('Invalid experimental strength or layer')
    from steerability.algorithms.core.internals.data import ContrastivePairs
    from steerability.algorithms.state_control.common.sources import ContrastiveFit
    from steerability.algorithms.state_control.common.transforms import AdditiveTransform
    from steerability.algorithms.state_control.activation_adapter.control import ActivationAdapter
    from steerability.algorithms.core.steering_pipeline import SteeringPipeline
    train=[r for r in data['pairs'] if r['split']=='train']
    heldout=[r for r in data['pairs'] if r['split']=='test']
    pairs=ContrastivePairs(positives=[r['positive'] for r in train],
                           negatives=[r['negative'] for r in train])
    direction=ContrastiveFit(data=pairs,method='mean_diff',accumulate='last_token',prompt_format='raw')
    adapter=ActivationAdapter(transform=AdditiveTransform(direction,strength=args.strength),
                              layer_ids=args.layer,token_scope='all')
    pipeline=SteeringPipeline(model_name_or_path=args.model,controls=[adapter],device_map='auto')
    baseline=SteeringPipeline(model_name_or_path=args.model,controls=[],device_map='auto')
    pipeline.steer()
    baseline.steer()
    results=[]
    for row in heldout:
        # Both generators see the same input; held-out labels are NOT sent to scoring.
        prompt=row['negative']
        normal=baseline.generate(prompt,max_new_tokens=args.max_new_tokens)
        steered=pipeline.generate(prompt,max_new_tokens=args.max_new_tokens)
        results.append({'id':row['id'],'input':prompt,'baseline':normal,'steered':steered,
                        'human_review_required':True})
    output={'status':'REAL_STEERABILITY360_TRIAL_NOT_VALIDATED_DEFENSE',
            'model':args.model,'behavior':data['behavior'],'method':'ContrastiveFit_mean_diff',
            'layer_zero_based':args.layer,'strength':args.strength,
            'results':results,'disclaimer':'Outputs require independently labeled scoring. No automatic safety claim.'}
    Path(args.output).parent.mkdir(parents=True,exist_ok=True)
    Path(args.output).write_text(json.dumps(output,indent=2,default=str))
    print(json.dumps({'status':output['status'],'heldout_cases':len(results)},indent=2))

if __name__=='__main__': main()
