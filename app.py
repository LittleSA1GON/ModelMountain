"""Streamlit security workbench. All MCP examples are offline signed fixtures.
No external company tools or live servers are called. Real MIA evidence optional.
"""
import json
import streamlit as st
from model_mountain.core import builtin_scenarios, suite_report
from model_mountain.mcp_security import synthetic_mcp_suite
from model_mountain.extraction import ExtractionMonitor, synthetic_extraction_suite
from model_mountain.risk_catalog import RISKS, RISK_ASSUMPTIONS
from model_mountain.integrated_demo import generate as integrated_gateway_demo

st.set_page_config(page_title='Model Mountain Security & Reliability', page_icon='🛡️', layout='wide')
st.title('Model Mountain | Enterprise AI Security & Reliability')
st.caption('Model vulnerabilities | Secure RAG | Evidence-grounded responses | IBM MIA experiments | Agent/MCP security')

with st.expander('Why Model Mountain exists and what IBM MIA contributes', expanded=True):
    st.markdown("""
    Business AI applications can read sensitive documents, call internal APIs, and consume
    third-party MCP tools. A malicious document or tool response can contain instructions
    that the language model mistakenly treats as authoritative, and an unprotected agent
    might then propose an unauthorized action.

    | Protection area | Business security risk | Model Mountain defense |
    | --- | --- | --- |
    | **Prompt injection** | Untrusted prompts or documents can hijack model behavior | Heuristic context checks; optional IBM MIA Attention Tracker telemetry |
    | **RAG retrieval security** | Poisoned or cross-tenant documents may corrupt answers | SHA-256 integrity, tenant/role checks, source quarantine |
    | **Agent action authorization** | Compromised agents may invoke privileged business tools | Deny-by-default permission and approval rules |
    | **MCP integration security** | Server identities, certificates, metadata and updates may change | TLS trust utility, Ed25519 signed manifests, tool pins, OAuth context |
    | **Model extraction monitoring** | Systematic query campaigns may imitate proprietary models | Per-identity rate and token budgets; repeated training-pattern review |

    **IBM MIA:** For compatible self-hosted vLLM models, Q/K and hidden-state capture
    can support security investigation, and activation steering can be evaluated as an
    experimental inference-time intervention. An attention score is not proof of compromise.
    MIA does not verify certificates, authenticate updates, enforce tool permissions,
    or replace source ACLs. The included CPU data is synthetic; real Kaggle GPU MIA
    output must be separately verified and labeled.
    """)
st.warning('Security research prototype: built-in text responses and MCP TLS/OAuth evidence are SYNTHETIC. No real MCP or company action is executed.')

risk_tab, llm_tab, mcp_tab, extraction_tab, gateway_tab, reliability_tab, vectors_tab = st.tabs(['Risk severity', 'Prompt / retrieval / agent', 'MCP identity and updates', 'Model extraction monitoring', 'Integrated security gateway', 'RAG reliability & steering', 'Behavioral vector lab'])
with risk_tab:
    st.caption(RISK_ASSUMPTIONS)
    st.dataframe(list(RISKS),use_container_width=True,hide_index=True)
with llm_tab:
    st.info('The local model is a deterministic fixture. Optional real MIA evidence is separately labeled.')
    file = st.file_uploader('Optional completed Kaggle IBM MIA evidence JSON',type=['json'])
    threshold = st.number_input('Calibrated MIA threshold (optional)',value=0.0,step=0.05)
    use_gate = st.checkbox('Enable MIA score gate (requires externally validated calibration)',value=False)
    evidence = None
    if file:
        obj = json.load(file)
        if obj.get('status') == 'PASS' and obj.get('analyzer') == 'attn_tracker' and len(obj.get('results',{})) == len(builtin_scenarios()) * 2:
            evidence=obj['results']
            if any(item.get('engine')!='REAL_IBM_MIA_vllm' for item in evidence.values()):
                evidence=None
                st.error('Incomplete or unverified MIA evidence.')
        else:
            st.error('Invalid/incomplete MIA evidence. No real MIA results loaded.')
    report=suite_report(evidence,threshold if evidence is not None and use_gate else None)
    st.caption('Engine: '+report['engine'])
    a,b,c,d=st.columns(4)
    a.metric('LLM cases',report['totals']['cases'])
    b.metric('Adversarial cases',report['totals']['attacks'])
    c.metric('Documents rejected',report['totals']['rejected_documents'])
    d.metric('Protected unsafe simulated actions',report['totals']['protected_unauthorized_actions'])
    selected=st.selectbox('LLM security scenario',[c.name for c in builtin_scenarios()])
    cols=st.columns(2)
    for col,mode in zip(cols,('unprotected','protected')):
        r=next(x for x in report['records'] if x['scenario']==selected and x['mode']==mode)
        with col:
            st.subheader(mode.title())
            st.write('**Output:**',r['output'])
            st.write('**Engine:**',r['model_engine'])
            st.write('**MIA score:**',r['mia_score'] if r['mia_score'] is not None else 'Not measured')
            st.write('**Injection markers:**',r['all_input_markers'])
            st.write('**Response released:**',r['response_released'])
            st.write('**Tool proposal and simulated decision:**',r['policy'])
            st.dataframe(r['documents'],use_container_width=True)
    st.download_button('Download LLM assessment JSON',json.dumps(report,indent=2),file_name='model_mountain_report.json',mime='application/json')

with mcp_tab:
    mcp=synthetic_mcp_suite()
    a,b,c=st.columns(3)
    a.metric('MCP test cases',mcp['cases'])
    b.metric('Blocked synthetic violations',mcp['blocked'])
    c.metric('Allowed synthetic cases',mcp['allowed'])
    st.caption('All transport certificates and OAuth contexts in these cases are simulated. Ed25519 signatures are genuinely generated and verified with ephemeral test keys.')
    selected_mcp=st.selectbox('MCP scenario',[r['scenario'] for r in mcp['results']])
    item=next(r for r in mcp['results'] if r['scenario']==selected_mcp)
    st.subheader('Gateway decision: '+ ('ALLOW' if item['allowed'] else 'BLOCK'))
    st.write('**Reasons:**',item['issues'] or ['Approved tool and server unchanged'])
    st.write('**Publisher signature verified:**',item.get('manifest_signature_valid','not evaluated'))
    st.write('**Pinned tool definitions match:**',item.get('tool_pins_match','not evaluated'))
    st.write('**TLS evidence source:**',item['tls_source'])
    st.dataframe([{'scenario':r['scenario'],'decision':'ALLOW' if r['allowed'] else 'BLOCK','issues':', '.join(r['issues'])} for r in mcp['results']],use_container_width=True)
    st.download_button('Download MCP security audit JSON',json.dumps(mcp,indent=2),file_name='mcp_security_results.json',mime='application/json')
    st.markdown('**Deployment limitation:** A real enterprise gateway must invoke TLS CA/hostname verification and validated OAuth middleware, persist pins in protected storage, enforce these decisions before network calls, and connect to an actual MCP client.')

st.caption('Security prototype, not a production gateway. Internal-model analysis cannot substitute for independent TLS, OAuth, authorization or inference rate limits.')

with extraction_tab:
    st.markdown('### Model extraction and distillation-abuse monitoring')
    st.caption('External API controls. Training-related wording alone is not evidence of theft. IBM MIA is not a validated extraction detector.')
    extraction = synthetic_extraction_suite()
    x1,x2,x3 = st.columns(3)
    x1.metric('Synthetic requests', extraction['cases'])
    x2.metric('Blocked admissions', extraction['blocked'])
    x3.metric('Allowed/monitored', extraction['allowed'])
    st.dataframe([{'Scenario': r['scenario'], 'Decision': r['decision'],
                   'Signals': ', '.join(r['issues'] + r['alerts']) or 'none'}
                  for r in extraction['results']],use_container_width=True,hide_index=True)
    st.download_button('Download model extraction test JSON',json.dumps(extraction,indent=2),
                       file_name='model_extraction_report.json',mime='application/json')
    st.markdown('#### Interactive request-admission simulation')
    if 'extraction_monitor' not in st.session_state:
        st.session_state['extraction_monitor'] = ExtractionMonitor()
    principal = st.text_input('Synthetic authenticated principal', 'demo-employee')
    prompt = st.text_area('Prompt to assess', 'How do I find the company PTO policy?')
    output_limit = st.number_input('Requested maximum output tokens',min_value=1,max_value=10000,value=200)
    if st.button('Evaluate synthetic API request'):
        try:
            decision=st.session_state['extraction_monitor'].check(tenant='synthetic-company',
                principal=principal,prompt=prompt,max_output_tokens=int(output_limit))
            st.json(decision)
        except ValueError as exc:
            st.error(str(exc))
    if st.button('Reset simulated request history'):
        st.session_state['extraction_monitor'] = ExtractionMonitor()
        st.success('Synthetic request counters reset.')
    st.warning('Demonstration only: counters are in memory. A production gateway needs authenticated tenant/account IDs, shared atomic limits, enforcement before inference, privacy-safe telemetry and review for legitimate high-volume users.')

with gateway_tab:
    st.subheader('Unified five-area security decision gateway')
    st.caption('CPU SYNTHETIC INTEGRATION, not actual IBM MIA inference. The true MIA gateway is a separate Kaggle GPU subprocess.')
    integrated = integrated_gateway_demo()
    st.dataframe([{'Test':x['name'],'Decision':'ALLOW' if x['allowed'] else 'DENY',
                   'Reasons':', '.join(x['reasons']), 'MIA score':'Not measured'}
                  for x in integrated['test_cases']],use_container_width=True,hide_index=True)
    st.info('With genuine IBM MIA configured, the gateway requires nonempty attention scores and can apply a per-model calibrated threshold before releasing generated answers. MCP identities, permissions, document ACLs and rate limits remain independent checks.')
    st.download_button('Download integrated gateway tests',json.dumps(integrated,indent=2),
                      file_name='model_mountain_integrated_gateway.json',mime='application/json')


with reliability_tab:
    from model_mountain.rag import ModelMountainRAG, RAGRequest, SourceRegistry
    from model_mountain.core import Document
    from model_mountain.evaluation import run_fixture
    st.subheader('Secure retrieval and hallucination-risk gates')
    st.info('CPU implementation: access-controlled lexical retrieval, poisoned-source quarantine, exact-citation verification and abstention. This is NOT a tested hallucination reduction model.')
    st.markdown('#### Live CPU extractive fixture')
    demo_text=st.text_area('Local approved demonstration document (not real trust onboarding)',
                          'The reimbursement limit is $500 per request.\nThe refund deadline is 30 days after purchase.',height=96)
    demo_q=st.text_input('Ask about the document','What is the reimbursement limit?')
    if st.button('Evaluate RAG answer',key='model_mountain_rag_run'):
        doc=Document.approved('demo-policy',demo_text)
        service=ModelMountainRAG([doc],SourceRegistry.trusted_fixture([doc]))
        st.json(service.answer(RAGRequest(demo_q)))
    st.markdown('#### Reproducible security + reliability fixtures')
    fixtures=run_fixture()
    st.dataframe([{'Case':r['id'],'Expected':r['expected'],'Answer':r['output'],
                   'Grounding':r['status'],'Test passed':r['passed_fixture_expectation']}
                  for r in fixtures['cases']],use_container_width=True,hide_index=True)
    st.download_button('Download CPU reliability evidence',json.dumps(fixtures,indent=2),
                       file_name='model_mountain_reliability_simulation.json',mime='application/json')
    st.markdown('#### IBM MIA experiment status')
    st.write('Real steering **requires** a compatible GPU server, a trained vector, and held-out before/after testing. The included scripts support capture, vector derivation, CoRe reranking, and paired real inference; they are not executed by this dashboard.')
    st.code('python -m model_mountain.evaluation --output model_mountain_results/reliability.json\npython -m model_mountain.steering --positive pos.pt --negative neg.pt --output vector.pt',language='bash')
    st.warning('Exact-citation checks do not establish document truth; paraphrases are not automatically approved. The CPU output is a fixture, NOT an LLM.')


with vectors_tab:
    from pathlib import Path
    from model_mountain.behaviorlab import validate_pairs
    st.subheader('Behavioral activation-vector discovery')
    st.info('Contrastive prompts -> REAL IBM MIA hidden-state capture -> paired direction learning -> validation/test probe -> experimental steering. No GPU result is bundled.')
    behavior = st.selectbox('Candidate behavior', ['grounding','injection_resistance','abstention'])
    example_path=Path(__file__).resolve().parent/'examples'/f'behavior_{behavior}.json'
    data=json.loads(example_path.read_text())
    report=validate_pairs(data)
    st.json(report)
    st.dataframe([{'Pair':r['id'],'Split':r['split'],'Task':r['task_group']} for r in data['pairs']],
                 hide_index=True,use_container_width=True)
    st.download_button('Download contrastive dataset',json.dumps(data,indent=2),
                       file_name=f'model_mountain_{behavior}_pairs.json',mime='application/json')
    uploaded=st.file_uploader('Optional externally generated vector manifest (JSON)',type=['json'],key='vector_manifest')
    if uploaded:
        manifest=json.load(uploaded)
        if manifest.get('schema_version')==1 and manifest.get('behavior') in ('grounding','injection_resistance','abstention'):
            st.write('**Probe metrics from supplied manifest (not externally verified)**')
            st.json({'model':manifest.get('model'),'layer':manifest.get('layer_zero_based'),
                     'status':manifest.get('approval'),
                     'validation':manifest.get('validation_metrics'),
                     'heldout':manifest.get('heldout_test_metrics')})
        else:
            st.error('Manifest format or behavior not recognized.')
    st.code('python mia_behavior_capture_worker.py --dataset examples/behavior_grounding.json --layer 14 --output results/captures.json\n'
            'python -m model_mountain.behaviorlab fit --captures results/captures.json --out results/grounding\n'
            'python -m model_mountain.behaviorlab export-profile --artifact results/grounding --output results/profile.json --allow-experimental',
            language='bash')
    st.warning('Small prompt seeds are examples only. Behavioral vectors, thresholds and safety benefits are not universal. Raw activations may be confidential. External authorization is mandatory.')
