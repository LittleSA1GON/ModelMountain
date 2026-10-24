"""Model Mountain Behavioral Vector Lab.

Learn and *measure* candidate model/layer-specific directions using real paired
activations. This module never calls a language model or invents activations.
Artifacts are experimental and never automatically approved for production.

Usage:
 python -m model_mountain.behaviorlab validate --dataset examples/behavior_pairs.json
 python -m model_mountain.behaviorlab fit --captures captures.json --out results/vector_lab
 python -m model_mountain.behaviorlab score --artifact results/vector_lab --activation '[...]' --model ... --layer 14
"""
from __future__ import annotations
import argparse
from collections import Counter
from dataclasses import dataclass
import hashlib
import json
import math
from pathlib import Path
from typing import Any

SPLITS = {'train', 'validation', 'test'}
BEHAVIORS = {'grounding', 'abstention', 'injection_resistance', 'refusal',
             'uncertainty', 'instruction_hierarchy', 'tool_authorization', 'compliance',
             'empathy', 'happiness', 'anger', 'fear'}


def _read(path: str | Path) -> dict:
    obj = json.loads(Path(path).read_text(encoding='utf-8'))
    if not isinstance(obj, dict):
        raise ValueError('Expected a JSON object')
    return obj


def validate_pairs(dataset: dict) -> dict:
    """Require separately labeled matched pairs, separate task groups, no overlap.

    Positive means the *desired observable behavior*, not necessarily refusal.
    These are illustrative seeds, not sufficient to prove a security direction.
    """
    if dataset.get('schema_version') != 1 or not isinstance(dataset.get('pairs'), list):
        raise ValueError('Expected schema_version 1 with pairs list')
    pairs = dataset['pairs']
    if not pairs:
        raise ValueError('No pairs provided')
    ids, prompt_fingerprints, groups = set(), set(), {}
    counts = Counter()
    behavior = dataset.get('behavior')
    if behavior not in BEHAVIORS:
        raise ValueError(f'Unknown behavior: {behavior}')
    for row in pairs:
        if not isinstance(row, dict) or row.get('split') not in SPLITS:
            raise ValueError('Each pair requires a valid split')
        for k in ('id','task_group','positive','negative'):
            if not isinstance(row.get(k), str) or not row[k].strip():
                raise ValueError(f'Each pair requires nonempty {k}')
        if row['id'] in ids:
            raise ValueError('Duplicate pair id')
        ids.add(row['id'])
        if row['positive'] == row['negative']:
            raise ValueError('Contrasts must differ')
        for k in ('positive','negative'):
            digest = hashlib.sha256(row[k].strip().lower().encode()).hexdigest()
            if digest in prompt_fingerprints:
                raise ValueError('A prompt appears in more than one contrast; potential leakage')
            prompt_fingerprints.add(digest)
        group = row['task_group']
        if group in groups and groups[group] != row['split']:
            raise ValueError(f'Task-group leakage across splits: {group}')
        groups[group] = row['split']
        counts[row['split']] += 1
    return {'behavior': behavior, 'pairs': len(pairs), 'split_counts': dict(counts),
            'task_groups': len(groups), 'training_ready':counts['train']>=2 and counts['validation']>=1 and counts['test']>=1}


def validate_captures(data: dict, *, allow_synthetic: bool=False) -> dict:
    """Validate provenance and paired activation vectors, before any fitting."""
    if data.get('schema_version') != 1 or data.get('engine') not in ({'IBM_MIA_CAPTURE_HS', 'SYNTHETIC_TEST_FIXTURE'} if allow_synthetic else {'IBM_MIA_CAPTURE_HS'}):
        raise ValueError('Expected IBM MIA capture schema; synthetic vectors require explicit test opt-in')
    for k in ('model','behavior','dataset_sha256'):
        if not isinstance(data.get(k), str) or not data[k]:
            raise ValueError(f'Missing capture provenance: {k}')
    if data['behavior'] not in BEHAVIORS:
        raise ValueError('Unknown captured behavior')
    layer = data.get('layer_zero_based')
    if type(layer) is not int or layer < 0:
        raise ValueError('Missing valid zero-based layer')
    hidden = data.get('hidden_dim')
    if type(hidden) is not int or hidden < 2:
        raise ValueError('Invalid hidden dimension')
    rows = data.get('pairs')
    if not isinstance(rows,list) or not rows:
        raise ValueError('No captured pairs')
    ids, group_split, counts = set(), {}, Counter()
    for row in rows:
        if not isinstance(row,dict) or row.get('split') not in SPLITS:
            raise ValueError('Invalid capture split')
        ident, group = row.get('id'), row.get('task_group')
        if not isinstance(ident,str) or not ident or ident in ids:
            raise ValueError('Capture ids must be unique')
        ids.add(ident)
        if not isinstance(group,str) or not group:
            raise ValueError('Capture requires task_group')
        if group in group_split and group_split[group] != row['split']:
            raise ValueError('Capture task-group leaked across splits')
        group_split[group] = row['split']
        for k in ('positive','negative'):
            values = row.get(k)
            if not isinstance(values,list) or len(values)!=hidden or any(
                    isinstance(v,bool) or not isinstance(v,(float,int)) or not math.isfinite(v)
                    for v in values):
                raise ValueError(f'Invalid activation {k} for {ident}')
        counts[row['split']]+=1
    if counts['train'] < 2 or counts['validation'] < 1 or counts['test'] < 1:
        raise ValueError('Need >=2 train, >=1 validation, >=1 test independent pairs')
    return {'pairs':len(rows),'split_counts':dict(counts),'model':data['model'],
            'layer_zero_based':layer,'hidden_dim':hidden,'behavior':data['behavior']}


def _metrics(values: list[tuple[float,int]], threshold:float) -> dict:
    tp = sum(v >= threshold for v,y in values if y == 1)
    fn = sum(v < threshold for v,y in values if y == 1)
    fp = sum(v >= threshold for v,y in values if y == 0)
    tn = sum(v < threshold for v,y in values if y == 0)
    return {'n':len(values),'tp':tp,'fn':fn,'fp':fp,'tn':tn,
            'accuracy':(tp+tn)/len(values),
            'recall':tp/(tp+fn) if tp+fn else None,
            'false_positive_rate':fp/(tn+fp) if tn+fp else None,
            'balanced_accuracy':0.5*(tp/(tp+fn)+tn/(tn+fp)) if tp+fn and tn+fp else None}


def _calibrate(scores:list[tuple[float,int]]) -> float:
    vals=sorted(set(float(s) for s,_ in scores))
    candidates=[vals[0]-1.0,vals[-1]+1.0]
    candidates += [(a+b)/2 for a,b in zip(vals,vals[1:])]
    # On validation ONLY; penalize false positives as benign model utility risk.
    def score(t):
        m=_metrics(scores,t)
        return (m['balanced_accuracy']-0.1*m['false_positive_rate'],
                -m['false_positive_rate'], -abs(t))
    return float(max(candidates,key=score))


def fit_captures(captures: str | Path, out: str | Path, method: str='mean_diff', *, allow_synthetic:bool=False) -> dict:
    """Fit paired direction, calibrate on validation, seal held-out test metrics.

    Exports the `{'dir': Tensor,'avg_proj': float}` payload required by IBM MIA,
    and a JSON manifest with hashes, model/layer binding, scores and status.
    """
    if method not in ('mean_diff','pca_pairwise'):
        raise ValueError('Use mean_diff or pca_pairwise')
    import torch
    path=Path(captures)
    raw=path.read_bytes()
    data=json.loads(raw)
    summary=validate_captures(data,allow_synthetic=allow_synthetic)
    rows=data['pairs']
    train=[r for r in rows if r['split']=='train']
    delta=torch.tensor([ [a-b for a,b in zip(r['positive'],r['negative'])] for r in train],dtype=torch.float32)
    mean=delta.mean(dim=0)
    if method=='pca_pairwise':
        # Principal direction of pairwise differences; orient toward positive mean.
        # GPU not needed for fitting a small matrix of captured hidden states.
        u,s,vh=torch.linalg.svd(delta,full_matrices=False)
        direction=vh[0]
        if torch.dot(direction,mean)<0:
            direction=-direction
    else:
        direction=mean
    norm=float(torch.linalg.vector_norm(direction))
    if not math.isfinite(norm) or norm < 1e-8:
        raise ValueError('No learnable activation contrast')
    direction=(direction/norm).contiguous()
    avg_proj=float((torch.tensor([r['positive'] for r in train],dtype=torch.float32) @ direction).mean())
    def score_split(split):
        scores=[]
        for row in rows:
            if row['split'] != split: continue
            scores += [(float(torch.dot(torch.tensor(row['positive']),direction)),1),
                       (float(torch.dot(torch.tensor(row['negative']),direction)),0)]
        return scores
    val=score_split('validation')
    threshold=_calibrate(val)
    out=Path(out)
    out.mkdir(parents=True,exist_ok=True)
    vector_file=out/'vector.pt'
    torch.save({'dir':direction,'avg_proj':avg_proj},vector_file)
    vector_hash=hashlib.sha256(vector_file.read_bytes()).hexdigest()
    manifest={**summary,'schema_version':1,'method':method,
        'engine':data['engine'], 'capture_sha256':hashlib.sha256(raw).hexdigest(),
        'dataset_sha256':data['dataset_sha256'],
        'vector_file':'vector.pt','vector_sha256':vector_hash,
        'calibration_threshold':threshold,
        'validation_metrics':_metrics(val,threshold),
        'heldout_test_metrics':_metrics(score_split('test'),threshold),
        'approval':'SYNTHETIC_TEST_ONLY' if data['engine']=='SYNTHETIC_TEST_FIXTURE' else 'EXPERIMENTAL_UNREVIEWED',
        'interpretation':'Prediction of labeled activation class only; not proof of causal steering or model security.'}
    (out/'manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
    return manifest



def export_mia_profile(artifact_dir:str|Path, output:str|Path, *,
                       coefficient:float=0.5, phase:str='both',
                       positions:str='all_tokens',allow_experimental:bool=False) -> dict:
    """Bind a reviewed experimental vector to a model and exact decoder layer.

    Makes a local profile only; does not install or activate steering on a server.
    Server-side filesystem must contain the vector at this absolute path.
    """
    base=Path(artifact_dir)
    manifest=_read(base/'manifest.json')
    if manifest['approval']=='SYNTHETIC_TEST_ONLY':
        raise ValueError('Synthetic test directions cannot be exported for real MIA steering')
    if not allow_experimental:
        raise ValueError('Explicit --allow-experimental required; no vectors are validated defenses')
    path=(base/manifest['vector_file']).resolve()
    if not path.is_file() or hashlib.sha256(path.read_bytes()).hexdigest()!=manifest['vector_sha256']:
        raise ValueError('Direction integrity check failed')
    from .steering import SteeringProfile
    profile=SteeringProfile(model=manifest['model'],vector_path=str(path),
                            optimal_layer=manifest['layer_zero_based'],
                            coefficient=coefficient,phase=phase,positions=positions)
    output=Path(output)
    output.parent.mkdir(parents=True,exist_ok=True)
    data=profile.__dict__ | {'provenance_manifest':str((base/'manifest.json').resolve()),
                             'approval':'EXPERIMENTAL_UNREVIEWED'}
    output.write_text(json.dumps(data,indent=2))
    return {'profile_path':str(output),'model':profile.model,'layer':profile.optimal_layer,
            'approval':'EXPERIMENTAL_UNREVIEWED','on_server_verified':False}


def score_activation(artifact_dir:str|Path, values:list[float], *, model:str, layer:int) -> dict:
    """Offline candidate probe; NEVER an independent authorization boundary."""
    import torch
    base=Path(artifact_dir)
    manifest=_read(base/'manifest.json')
    if manifest['model']!=model or manifest['layer_zero_based']!=layer:
        raise ValueError('Model/layer mismatch: cross-model directions are not portable')
    vector_path=base/manifest['vector_file']
    if hashlib.sha256(vector_path.read_bytes()).hexdigest()!=manifest['vector_sha256']:
        raise ValueError('Steering artifact integrity check failed')
    vector=torch.load(vector_path,map_location='cpu',weights_only=True)['dir']
    if len(values)!=int(vector.numel()) or not all(isinstance(v,(int,float)) and
                      not isinstance(v,bool) and math.isfinite(v) for v in values):
        raise ValueError('Invalid probe activation')
    proj=float(torch.dot(torch.tensor(values,dtype=torch.float32),vector))
    return {'behavior':manifest['behavior'],'model':model,'layer_zero_based':layer,
            'projection':proj,'threshold':manifest['calibration_threshold'],
            'predicted_desired_behavior':proj >= manifest['calibration_threshold'],
            'approval':manifest['approval'],'for_authorization':False}


@dataclass(frozen=True)
class TrustedRoutingContext:
    """Application-created metadata. Do NOT populate from LLM-generated text."""
    source_class: str
    model: str
    operation: str = 'answer'
    principal_authorized: bool = False


def select_experimental_profile(context:TrustedRoutingContext, profiles:dict, *, explicit_opt_in:bool=False) -> dict:
    """Route experimental profiles only; authorization cannot be bypassed by a vector."""
    if context.source_class not in {'internal_verified','retrieved_document','external_tool','user'}:
        raise ValueError('Unknown source class')
    if context.operation not in {'answer','tool_action'}:
        raise ValueError('Unknown operation')
    if context.operation=='tool_action' and not context.principal_authorized:
        return {'decision':'BLOCK_UNAUTHORIZED_ACTION','profile':None}
    if not explicit_opt_in:
        return {'decision':'NO_STEERING_NOT_OPTED_IN','profile':None}
    behavior=('injection_resistance' if context.source_class in {'retrieved_document','external_tool'}
              else 'grounding' if context.source_class=='internal_verified' else None)
    profile=profiles.get(behavior) if behavior else None
    if profile is None:
        return {'decision':'NO_MATCHING_PROFILE','profile':None}
    from .steering import SteeringProfile
    if not isinstance(profile,SteeringProfile) or profile.model!=context.model:
        raise ValueError('Approved experimental profile must match the exact served model')
    return {'decision':'EXPERIMENTAL_STEERING_SELECTED','behavior':behavior,'profile':profile}


def main():
    parser=argparse.ArgumentParser(description='Model Mountain Behavioral Vector Lab')
    sub=parser.add_subparsers(dest='cmd',required=True)
    p=sub.add_parser('validate'); p.add_argument('--dataset',required=True)
    p=sub.add_parser('fit'); p.add_argument('--captures',required=True);p.add_argument('--out',required=True)
    p.add_argument('--method',choices=['mean_diff','pca_pairwise'],default='mean_diff')
    p.add_argument('--allow-synthetic-test-data',action='store_true')
    p=sub.add_parser('export-profile');p.add_argument('--artifact',required=True)
    p.add_argument('--output',required=True);p.add_argument('--coefficient',type=float,default=.5)
    p.add_argument('--allow-experimental',action='store_true')
    p=sub.add_parser('score');p.add_argument('--artifact',required=True)
    p.add_argument('--activation',required=True,help='JSON list of numeric hidden state values')
    p.add_argument('--model',required=True);p.add_argument('--layer',required=True,type=int)
    a=parser.parse_args()
    if a.cmd=='validate': result=validate_pairs(_read(a.dataset))
    elif a.cmd=='fit': result=fit_captures(a.captures,a.out,a.method,allow_synthetic=a.allow_synthetic_test_data)
    elif a.cmd=='export-profile': result=export_mia_profile(a.artifact,a.output,
                          coefficient=a.coefficient,allow_experimental=a.allow_experimental)
    else: result=score_activation(a.artifact,json.loads(a.activation),model=a.model,layer=a.layer)
    print(json.dumps(result,indent=2))

if __name__=='__main__': main()
