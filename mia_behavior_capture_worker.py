"""Real, paired IBM MIA activation collection for Model Mountain behavior discovery.

Run in the IBM vLLM-Hook environment with CUDA. Requires MIA capture_hs.
No local/mock fallback and no synthetic activations. Captured hidden states can
contain sensitive information: keep outputs private and delete as appropriate.
"""
import argparse
import hashlib
import json
import multiprocessing as mp
import os
from pathlib import Path

os.environ.setdefault('VLLM_WORKER_MULTIPROC_METHOD','spawn')
os.environ.setdefault('MIA_APERTURE_GPU_BYTES',str(512*1024*1024))


def extract_last_token(stats, layer):
    import torch
    key=f'model.layers.{layer}'
    tensor=stats.get('hidden_states',{}).get(key)
    if tensor is None:
        raise RuntimeError(f'MIA capture missing {key}; check model layer naming and capture config')
    if isinstance(tensor,(list,tuple)):
        if len(tensor)!=1:
            raise RuntimeError('Unexpected MIA capture count; need one request at a time')
        tensor=tensor[0]
    if not isinstance(tensor,torch.Tensor):
        raise RuntimeError('MIA output is not a torch Tensor')
    # MIA may return [hidden], [1,hidden], or [batch=1,tokens=1,hidden].
    if tensor.ndim not in (1,2,3) or tensor.numel() != tensor.shape[-1]:
        raise RuntimeError('Expected exactly one captured last-token hidden vector')
    feature=tensor.detach().to(device='cpu',dtype=torch.float32).reshape(-1)
    if feature.numel()<2 or not bool(torch.isfinite(feature).all()):
        raise RuntimeError('Nonfinite or empty MIA hidden state')
    return feature.tolist()


def capture(args):
    from mia import MiaLLM
    from vllm import SamplingParams
    from model_mountain.behaviorlab import validate_pairs
    raw=Path(args.dataset).read_bytes()
    dataset=json.loads(raw)
    report=validate_pairs(dataset)
    if not report['training_ready']:
        raise ValueError('Dataset requires >=2 train, >=1 validation, >=1 test pairs')
    # MIA hidden_states.layers indexes are 1-based, while the resulting keys and
    # steer optimal_layer are zero-based decoder blocks.
    config={'hidden_states':{'layers':[args.layer+1],'mode':'last_token'}}
    out=Path(args.output)
    out.parent.mkdir(parents=True,exist_ok=True)
    config_file=out.with_suffix('.capture_config.json')
    config_file.write_text(json.dumps(config,indent=2))
    llm=MiaLLM(model=args.model,worker_name='capture_hs',analyzer_name='hidden_states',
               config_file=str(config_file),gpu_memory_utilization=args.gpu_memory_utilization,
               max_model_len=args.max_model_len,max_num_seqs=1,enable_prefix_caching=False)
    def capture_one(prompt):
        chat=llm.tokenizer.apply_chat_template([{'role':'user','content':prompt}],
            tokenize=False,add_generation_prompt=True)
        output=llm.generate(chat,SamplingParams(max_tokens=1,temperature=0.0),use_tqdm=False)
        probes=getattr(output[0],'probes',None)
        if probes is None:
            raise RuntimeError('MIA returned no probes; refusing to emit synthetic data')
        stats=llm.analyze(analyzer_spec={'reduce':'none'},probes=probes)
        return extract_last_token(stats,args.layer)
    rows=[]
    for idx,row in enumerate(dataset['pairs']):
        positive=capture_one(row['positive'])
        negative=capture_one(row['negative'])
        if len(positive)!=len(negative):
            raise RuntimeError('Hidden-state dimensionality drift')
        rows.append({'id':row['id'],'task_group':row['task_group'],'split':row['split'],
                     'positive':positive,'negative':negative})
        print(f'Captured real MIA vectors for pair {idx+1}/{len(dataset["pairs"])}',flush=True)
    result={'schema_version':1,'engine':'IBM_MIA_CAPTURE_HS','model':args.model,
            'behavior':dataset['behavior'],'layer_zero_based':args.layer,
            'hidden_dim':len(rows[0]['positive']),'dataset_sha256':hashlib.sha256(raw).hexdigest(),
            'pairs':rows,'validation':'unverified_behavioral_effect'}
    # All-or-nothing write: never accidentally fit an incomplete collection.
    tmp=out.with_suffix('.partial')
    tmp.write_text(json.dumps(result))
    tmp.replace(out)
    print(json.dumps({'status':'REAL_MIA_CAPTURED','output':str(out),
                      'pairs':len(rows),'hidden_dim':result['hidden_dim']},indent=2))


def main():
    p=argparse.ArgumentParser()
    p.add_argument('--model',default='Qwen/Qwen2-1.5B-Instruct')
    p.add_argument('--dataset',required=True)
    p.add_argument('--layer',type=int,default=14,help='0-based decoder layer')
    p.add_argument('--output',required=True)
    p.add_argument('--max-model-len',type=int,default=1536)
    p.add_argument('--gpu-memory-utilization',type=float,default=0.55)
    args=p.parse_args()
    if args.layer<0:raise ValueError('Layer must be >=0')
    capture(args)

if __name__=='__main__':
    mp.set_start_method('spawn',force=True)
    main()
