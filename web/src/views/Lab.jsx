import React, { useEffect, useState } from 'react';
import { api } from '../lib/api.js';
import { capabilityState, evidenceClass } from '../lib/logic.js';

const CAP_LABEL = { inference: 'Inference', hidden_states: 'Hidden states', capture_hs: 'Hidden states', steering: 'Steering', steer: 'Steering',
  attention_tracker: 'Attention tracker', core_reranker: 'CoRe reranker', hnode: 'H-Node', hnode_hallucination: 'H-Node',
  science_hallucination: 'Science hallucination', attnlink: 'AttnLink', tool_call_risk: 'Tool-call risk' };

function useLoad(fn) {
  const [r, setR] = useState(null);
  useEffect(() => { let a = true; fn().then((x) => a && setR(x)); return () => { a = false; }; }, []);
  return r;
}

function Models({ r }) {
  if (!r) return <div className="card pad" style={{ display: 'grid', gap: 12 }}><div className="skeleton" /><div className="skeleton" /></div>;
  if (!r.ok) return <p className="err">{r.error?.message}</p>;
  const items = r.data.items || [];
  if (!items.length) return <div className="empty">No models registered yet.</div>;
  return (
    <div className="card table-wrap">
      <table>
        <thead><tr><th>Model</th><th>Status</th><th>MIA features</th></tr></thead>
        <tbody>
          {items.map((m) => {
            const caps = Object.entries(m.capabilities || {});
            const avail = caps.filter(([, v]) => capabilityState(v) === 'available').length;
            const status = m.compatible === false ? 'Estimated not to fit' : m.status === 'verified' ? 'Verified on GPU' : m.compatible ? 'Estimated fit (T4)' : 'Not run yet';
            const tone = m.compatible === false ? 'bad' : m.status === 'verified' ? 'ok' : m.compatible ? 'info' : 'warn';
            return (
              <tr key={m.model_id || m.id}>
                <td><b>{m.name || m.model_id}</b><span className="sub">{m.model_id}{m.revision ? ` @ ${String(m.revision).slice(0, 7)}` : ''}</span></td>
                <td><span className={`chip ${tone}`} title={(m.blockers || []).join('; ')}>{status}</span></td>
                <td>
                  <div className="row" style={{ gap: 6 }}>
                    {caps.slice(0, 4).map(([k, v]) => <span key={k} className={`chip ${capabilityState(v) === 'available' ? 'ok' : ''}`}>{CAP_LABEL[k] || k}</span>)}
                    {caps.length > 4 && <span className="muted small">+{caps.length - 4} more</span>}
                  </div>
                  <span className="sub">{avail} of {caps.length} config-supported (not runtime-verified)</span>
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}


function Runs({ jobs, reports }) {
  if (!jobs || !reports) return <div className="card pad"><div className="skeleton" /></div>;
  const all = reports.ok ? reports.data.items || [] : [];
  const real = all.filter((x) => evidenceClass(x.evidence_type) === 'real');
  const diag = all.filter((x) => evidenceClass(x.evidence_type) === 'diagnostic');
  const jobItems = jobs.ok ? jobs.data.items || [] : [];
  const rows = [...jobItems.map((j) => ({ id: j.id || j.job_id, what: j.kernel || j.model_id || 'Kaggle job', status: j.status, when: j.updated_at || j.created_at })),
    ...real.map((r) => ({ id: r.run_id, what: r.model_id, status: r.evidence_type, when: r.created_at })),
    ...diag.map((r, i) => ({ id: r.run_id || r.id || `diagnostic-${i}`, what: `${r.title || r.kind || 'Hardware / compatibility check'} (no model output)`, status: r.evidence_type, when: r.created_at || r.generated_at }))];
  if (!rows.length) {
    return (
      <div className="empty">
        <b>No GPU runs published yet.</b>
        <p className="small" style={{ marginTop: 6 }}>
          {jobs.status === 401 ? 'Live job status is visible to the operator only. ' : ''}
          Results appear here once a Kaggle run finishes and its report is uploaded.
        </p>
      </div>
    );
  }
  return (
    <div className="card table-wrap"><table>
      <thead><tr><th>Run</th><th>Model or job</th><th>Status</th><th>Updated</th></tr></thead>
      <tbody>{rows.map((r) => (
        <tr key={r.id}><td className="mono">{String(r.id).slice(0, 12)}</td><td>{r.what}</td>
          <td><span className={`chip ${/complete|succeeded|^REAL/i.test(r.status) ? 'ok' : /STATIC|PREFLIGHT|DIAGNOSTIC/i.test(r.status) ? '' : /fail|error|blocked/i.test(r.status) ? 'bad' : 'warn'}`}>{r.status}</span></td>
          <td className="muted small">{r.when ? new Date(r.when).toLocaleString() : '—'}</td></tr>
      ))}</tbody>
    </table></div>
  );
}

function CaptureSmoke({ r }) {
  if (!r) return <div className="card pad"><div className="skeleton" /></div>;
  if (!r.ok || r.data?.kind !== 'capture_integration_smoke' || r.data?.evidence_type !== 'REAL_IBM_MIA') return <div className="empty"><b>No integration capture published.</b></div>;
  const d = r.data;
  const pick = (...keys) => keys.map((k) => d[k]).find((v) => v != null);
  return (
    <div className="card pad" style={{ display: 'grid', gap: 8 }}>
      <div className="row" style={{ justifyContent: 'space-between' }}>
        <b>Real IBM MIA capture on Kaggle (integration check)</b>
        <span className="chip ok">{d.evidence_type || 'REAL_IBM_MIA'}</span>
      </div>
      <span className="muted small">{pick('model_id', 'model')}{pick('model_revision', 'revision') ? ` @ ${String(pick('model_revision', 'revision')).slice(0, 7)}` : ''}{pick('gpu', 'device') ? ` · ${pick('gpu', 'device')}` : ''}</span>
      <p className="small">This proves the hook ran and returned real hidden states. It is plumbing evidence only: it says nothing about security or steering effects.</p>
      <pre className="pre small">{JSON.stringify(d, (k, v) => (k === 'project_name' || k === 'project_id' ? undefined : v), 2).slice(0, 1200)}</pre>
    </div>
  );
}

export default function Lab({ health }) {
  const models = useLoad(api.models);
  const jobs = useLoad(api.jobs);
  const reports = useLoad(api.reports);
  const smoke = useLoad(api.captureSmoke);
  const gpu = health?.ok && health.data.remote_configured;
  return (
    <section className="view">
      <div className="head">
        <p className="eyebrow">MIA Lab</p>
        <h2>Look inside the model, not just at its text.</h2>
        <p className="lede">IBM vLLM-Hook (MIA) reads a model's internal state while it runs. Model Mountain uses it only for defenses against attacks: detecting prompt injection from attention, monitoring hidden states, and steering the model away from complying with injected instructions.</p>
      </div>

      <div className="card table-wrap">
        <table>
          <thead><tr><th>MIA defense</th><th>IBM MIA worker</th><th>What it does</th></tr></thead>
          <tbody>
            <tr><td><b>Injection shield</b></td><td className="mono small">capture_hs → steer (add_vector)</td><td className="small">Finds the direction separating attacks that hijacked the model from attacks it resisted, then steers against it. Strength chosen on validation; tested on held-out Tensor Trust attacks.</td></tr>
            <tr><td><b>Attention Tracker detector</b></td><td className="mono small">capture_qk + attention analyzer</td><td className="small">Heads whose attention to the system instruction drops under injection; their focus score flags injected inputs (Hung et al., NAACL 2025 Findings).</td></tr>
            <tr><td><b>Activation monitor</b></td><td className="mono small">capture_hs (last token)</td><td className="small">Linear probe on hidden states trained on deepset prompt injections; reported with its false-positive rate under distribution shift.</td></tr>
          </tbody>
        </table>
      </div>

      <div className="card pad row" style={{ justifyContent: 'space-between' }}>
        <div style={{ display: 'grid', gap: 2 }}>
          <b>GPU runs happen on Kaggle</b>
          <span className="muted small">Private Kaggle kernels run IBM MIA on the three models and report held-out results back here.</span>
        </div>
        <span className={`chip ${gpu ? 'ok' : ''}`}>{gpu ? 'Live worker connected' : 'Batch workflow · no live worker'}</span>
      </div>

      <div>
        <div className="section-title"><h2>GPU runs</h2><span className="muted small">Private Kaggle notebooks, 2 × Tesla T4</span></div>
        <Runs jobs={jobs} reports={reports} />
      </div>

      <div>
        <div className="section-title"><h2>Hook integration</h2><span className="muted small">Capture check, not an effect measurement</span></div>
        <CaptureSmoke r={smoke} />
      </div>

      <div>
        <div className="section-title"><h2>Models</h2><span className="muted small">Pinned Hugging Face revisions</span></div>
        <Models r={models} />
      </div>

    </section>
  );
}
