"""Optional real IBM MIA CoRe reranking on pre-authorized retrieval candidates.

One GPU model process, two Q/K capture passes per question, genuine disk
artifacts. This is independent of the CPU lexical fallback in model_mountain.rag.
"""
import argparse
import json
import multiprocessing as mp
import os
from pathlib import Path
import uuid

os.environ.setdefault('VLLM_WORKER_MULTIPROC_METHOD','spawn')
os.environ.setdefault('MIA_APERTURE_GPU_BYTES',str(512*1024*1024))


def text_and_spans(tokenizer, query:str, docs:list[str]):
    beginning='Here are some paragraphs:\n\n'
    instruction='Find paragraphs relevant to the question.\n\nQuestion: '
    content=beginning
    locations=[]
    for i,doc in enumerate(docs):
        content+=f'[document {i+1}] '
        a=len(content)
        content+=doc
        b=len(content)
        locations.append((a,b))
        content+='\n\n'
    content+=instruction
    start=len(content)
    content+=query
    end=len(content)
    prompt=tokenizer.apply_chat_template([{'role':'user','content':content}],
                                         tokenize=False,add_generation_prompt=True)
    offset=prompt.index(content)
    def tok(n):
        return len(tokenizer(prompt[:offset+n],add_special_tokens=False).input_ids)
    return prompt,(list((tok(a),tok(b)) for a,b in locations),tok(start),tok(start),tok(end))


def main():
    from mia import MiaLLM
    from vllm import SamplingParams
    from model_mountain.evaluation import docs_from_case, example_cases
    from model_mountain.rag import SourceRegistry,SecureRetriever
    ap=argparse.ArgumentParser()
    ap.add_argument('--config',required=True,help='IBM MIA core_reranker JSON config for model')
    ap.add_argument('--model',default='Qwen/Qwen2-1.5B-Instruct')
    ap.add_argument('--cases',help='JSON cases file')
    ap.add_argument('--output',required=True)
    ap.add_argument('--gpu-memory-utilization',type=float,default=.55)
    a=ap.parse_args()
    cases=example_cases() if not a.cases else json.loads(Path(a.cases).read_text())
    llm=MiaLLM(model=a.model,worker_name='capture_qk',analyzer_name='core_reranker',
               config_file=a.config, gpu_memory_utilization=a.gpu_memory_utilization,
               max_model_len=1536, enable_prefix_caching=False)
    records=[]
    for case in cases:
        docs=docs_from_case(case)
        checked=SecureRetriever(SourceRegistry.trusted_fixture(docs),top_k=20).retrieve(
            case['question'],docs,tenant='acme',role='employee')
        if not checked.hits:
            records.append({'id':case['id'],'status':'no_approved_candidates'})
            continue
        candidate_ids=[h.document.doc_id for h in checked.hits]
        passages=[h.document.text for h in checked.hits]
        prompt,spec=text_and_spans(llm.tokenizer,case['question'],passages)
        prompt_na,spec_na=text_and_spans(llm.tokenizer,'N/A',passages)
        run_a=f'model_mountain-q-{uuid.uuid4().hex[:12]}'
        run_b=f'model_mountain-na-{uuid.uuid4().hex[:12]}'
        llm.generate(prompt,SamplingParams(max_tokens=1,temperature=0.0),
                     save_to_disk=True,run_id=run_a,use_tqdm=False)
        llm.generate(prompt_na,SamplingParams(max_tokens=1,temperature=0.0),
                     save_to_disk=True,run_id=run_b,use_tqdm=False)
        score=llm.analyze(run_ids=[run_a,run_b],analyzer_spec={'query_spec':spec,'na_spec':spec_na})
        if not isinstance(score,dict) or 'ranking' not in score:
            raise RuntimeError('CoRe returned no ranking; do not substitute lexical evidence')
        records.append({'id':case['id'],'candidate_doc_ids':candidate_ids,
                        'core_ranking_raw':score['ranking'], 'core_scores_raw':score.get('scores'),
                        'provenance':'REAL_IBM_MIA_CoRe'})
    result={'status':'REAL_MIA_CORE_RERANKING_ONLY','model':a.model,
            'cases':records,'note':'Only approved source candidates passed to CoRe. '
                                    'Relevance is not evidence truth or factual entailment.'}
    Path(a.output).parent.mkdir(parents=True,exist_ok=True)
    Path(a.output).write_text(json.dumps(result,indent=2,default=str))
    print(json.dumps({'status':result['status'],'cases':len(records)},indent=2))

if __name__=='__main__':
    mp.set_start_method('spawn',force=True)
    main()
