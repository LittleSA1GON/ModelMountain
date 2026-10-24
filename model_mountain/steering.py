"""Real IBM MIA steering client and paired direction-learning utilities.

This module makes NO claim that a particular steering vector improves safety.
A remote endpoint must be provisioned with MIA_WORKER=steer and a trusted model.
"""
from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
import argparse
import json
import math


@dataclass(frozen=True)
class SteeringProfile:
    model: str
    vector_path: str
    optimal_layer: int | list[int]
    coefficient: float = 1.0
    phase: str = 'both'
    positions: str = 'all_tokens'
    method: str = 'add_vector'

    def __post_init__(self):
        if not self.model or not self.vector_path or self.method not in ('add_vector','adjust_rs'):
            raise ValueError('Model, vector file and a supported MIA method are required')
        if self.phase not in ('both','prefill','decode') or self.positions not in ('all_tokens','last_token'):
            raise ValueError('Unsupported MIA steering mode')
        if not isinstance(self.coefficient,(float,int)) or not math.isfinite(self.coefficient):
            raise ValueError('Steering coefficient must be finite')
        layers = [self.optimal_layer] if isinstance(self.optimal_layer,int) else self.optimal_layer
        if not isinstance(layers,list) or not layers or any(not isinstance(x,int) or x < 0 for x in layers):
            raise ValueError('Explicit zero-based decoder layer(s) required')

    def payload(self) -> dict:
        return {'method':self.method,'coefficient':self.coefficient,
                'optimal_layer':self.optimal_layer,'phase':self.phase,
                'positions':self.positions,'vector_path':self.vector_path}

    @classmethod
    def load(cls, filename: str) -> 'SteeringProfile':
        data=json.loads(Path(filename).read_text())
        if 'steering' in data:
            data={**data['steering'], 'model':data.get('model') or data.get('model_info',{}).get('model_id')}
        return cls(**{k:data[k] for k in ('model','vector_path','optimal_layer','coefficient',
                                        'phase','positions','method') if k in data})


class MIARequestError(RuntimeError):
    pass


class MIASteeringClient:
    """Thin MIA served backend; no automatic fallback when the request fails.

    Server MIA_WORKER provenance cannot be attested through OpenAI-compatible
    completions responses alone: verify server logs/config independently.
    """
    def __init__(self, *, endpoint: str, api_key: str, model: str, client=None):
        if not endpoint.startswith(('http://127.0.0.1:', 'http://localhost:', 'https://')):
            raise ValueError('Use a loopback or HTTPS endpoint; never send API keys over remote HTTP')
        self.model=model
        if client is None:
            try:
                from openai import OpenAI
            except ImportError as exc:
                raise MIARequestError('Install optional dependency: pip install openai') from exc
            client=OpenAI(base_url=endpoint.rstrip('/'), api_key=api_key, timeout=120.0)
        self.client=client

    def generate(self, system: str, question: str, context: str, *,
                 profile: SteeringProfile | None=None, max_tokens: int=160) -> str:
        if profile is not None and profile.model != self.model:
            raise MIARequestError('Model-specific steering profile does not match served model')
        if not 1 <= max_tokens <= 512:
            raise ValueError('Invalid token budget')
        kwargs = dict(model=self.model, max_tokens=max_tokens, temperature=0.0,
                      messages=[{'role':'system','content':system},
                                {'role':'user','content':f'Question: {question}\nUntrusted retrieved data:\n{context}'}])
        if profile is not None:
            kwargs['extra_body']={'vllm_xargs': {'steer':json.dumps(profile.payload())}}
        try:
            result=self.client.chat.completions.create(**kwargs)
            out=result.choices[0].message.content
        except Exception as exc:
            raise MIARequestError('Remote model inference failed; not retrying without steering') from exc
        if not isinstance(out,str):
            raise MIARequestError('Missing model text')
        return out


def derive_direction(positive_file: str, negative_file: str, output: str) -> dict:
    """Learn contrastive mean direction from user-labeled, trusted `.pt` tensors.

    Each input contains a [hidden] or [n,hidden] Tensor; supervision quality
    determines the result. Never evaluate on these same training samples.
    """
    try:
        import torch
    except ImportError as exc:
        raise RuntimeError('PyTorch is required for real activation-vector training') from exc
    def load(path):
        x=torch.load(path, map_location='cpu', weights_only=True)
        if isinstance(x,dict) and 'activations' in x:
            x=x['activations']
        if not isinstance(x,torch.Tensor) or x.ndim not in (1,2) or not x.is_floating_point():
            raise ValueError('Expected 1D/2D floating activations tensor')
        x=x.float().reshape(-1,x.shape[-1])
        if x.shape[0]<2 or not bool(torch.isfinite(x).all()):
            raise ValueError('At least two finite training activation vectors required per class')
        return x
    pos,neg=load(positive_file),load(negative_file)
    if pos.shape[1]!=neg.shape[1]:
        raise ValueError('Activation hidden dimensions do not match')
    raw=pos.mean(0)-neg.mean(0)
    norm=float(torch.linalg.vector_norm(raw))
    if norm<1e-8 or not math.isfinite(norm):
        raise ValueError('No usable direction could be learned')
    direction=raw/norm
    avg=float((pos@direction).mean())
    # This is IBM MIA's expected vector container: dir and avg_proj.
    Path(output).parent.mkdir(parents=True,exist_ok=True)
    torch.save({'dir':direction, 'avg_proj':avg},output)
    return {'output':output, 'hidden_dim':pos.shape[1], 'positive_count':len(pos),
            'negative_count':len(neg), 'method':'contrastive_mean_held_out_validation_required'}


def main():
    p=argparse.ArgumentParser(description='Model Mountain MIA activation vector learner')
    p.add_argument('--positive',required=True,help='Trusted captured activations from grounded/safe examples')
    p.add_argument('--negative',required=True,help='Trusted captured activations from ungrounded/unsafe examples')
    p.add_argument('--output',required=True)
    args=p.parse_args()
    print(json.dumps(derive_direction(args.positive,args.negative,args.output),indent=2))


if __name__=='__main__':main()
