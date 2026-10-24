"""Experimental IBM MIA GPU workbench: capture hidden states for contrastive learning.

Run with IBM's dedicated vLLM-Hook environment, from the IBM repository root.
Captures real activations; labels belong to user-curated training examples.
No claim that these vectors are security-/hallucination-reducing until held-out evaluation.
"""
import argparse
import json
import multiprocessing as mp
import os
from pathlib import Path

os.environ.setdefault('VLLM_WORKER_MULTIPROC_METHOD','spawn')
os.environ.setdefault('MIA_APERTURE_GPU_BYTES',str(512*1024*1024))


def capture(args):
    import torch
    from mia import MiaLLM
    from vllm import SamplingParams
    examples=json.loads(Path(args.examples).read_text())
    if not isinstance(examples,list) or len(examples)<4:
        raise ValueError('At least four labeled examples required')
    if any(item.get('label') not in ('positive','negative') or not item.get('prompt')
           for item in examples):
        raise ValueError('Each row needs a nonempty prompt and positive/negative label')
    llm=MiaLLM(model=args.model,worker_name='capture_hs',analyzer_name='hidden_states',
               config_file=args.config, gpu_memory_utilization=args.gpu_memory_utilization,
               max_model_len=args.max_model_len,max_num_seqs=1,
               enable_prefix_caching=False)
    layers={}
    for number,item in enumerate(examples):
        prompt=llm.tokenizer.apply_chat_template([{'role':'user','content':item['prompt']}],
                                                 tokenize=False,add_generation_prompt=True)
        output=llm.generate(prompt, SamplingParams(max_tokens=1,temperature=0.0),use_tqdm=False)
        probes=getattr(output[0],'probes',None)
        if probes is None:
            raise RuntimeError('IBM MIA did not capture any activation probes')
        stats=llm.analyze(analyzer_spec={'reduce':'none'},probes=probes)
        key=f'model.layers.{args.layer}'
        if key not in stats.get('hidden_states',{}):
            raise RuntimeError(f'No MIA hidden-state tensor at {key}; available: {list(stats.get("hidden_states",{}))}')
        activation=stats['hidden_states'][key][0]
        if not isinstance(activation,torch.Tensor) or activation.numel()<16:
            raise RuntimeError('Unexpected empty activation capture')
        flat=activation.detach().to('cpu',dtype=torch.float32).reshape(-1,activation.shape[-1])
        # capture_hs default last_token; all_tokens mode must be handled explicitly
        if flat.shape[0]!=1:
            raise RuntimeError('Set config hidden_states.mode=last_token; expected one feature vector')
        layers.setdefault(item['label'],[]).append(flat[0])
        print(f'CAPTURED {number+1}/{len(examples)}: label={item["label"]} shape={list(flat.shape)}',flush=True)
    if not all(len(layers.get(label,[]))>=2 for label in ('positive','negative')):
        raise ValueError('At least two captures per class required')
    out=Path(args.output)
    out.mkdir(parents=True,exist_ok=True)
    for label in ('positive','negative'):
        torch.save({'activations':torch.stack(layers[label])},out/f'{label}.pt')
    report={'status':'REAL_MIA_HIDDEN_STATE_CAPTURE_ONLY','model':args.model,
            'layer_zero_based':args.layer,'positive':len(layers['positive']),
            'negative':len(layers['negative']),
            'note':'Labels reflect curated training examples; intervention effectiveness is NOT validated.'}
    (out/'capture_report.json').write_text(json.dumps(report,indent=2))
    print(json.dumps(report,indent=2))


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--model',default='Qwen/Qwen2-1.5B-Instruct')
    ap.add_argument('--config',required=True,help='IBM MIA capture_hs config with last_token mode')
    ap.add_argument('--examples',required=True,help='JSON list of {label,prompt}')
    ap.add_argument('--layer',type=int,default=14,help='ZERO-BASED layer key model.layers.N')
    ap.add_argument('--output',required=True)
    ap.add_argument('--gpu-memory-utilization',type=float,default=0.55)
    ap.add_argument('--max-model-len',type=int,default=1024)
    capture(ap.parse_args())


if __name__=='__main__':
    mp.set_start_method('spawn',force=True)
    main()
