import React, { useEffect, useMemo, useState } from 'react';
import { api } from '../lib/api.js';
import { snapStrength } from '../lib/logic.js';

const SHIELD = 'injection_shield';
const pctPts = (x) => (typeof x === 'number' ? `${x > 0 ? '+' : ''}${(100 * x).toFixed(1)} pts` : '—');
const pct = (x) => (typeof x === 'number' ? `${Math.round(100 * x)}%` : '—');
const cell = (r) => (r && typeof r.rate === 'number'
  ? <>{pct(r.rate)} <span className="sub">{r.k}/{r.n}{Array.isArray(r.ci95) ? ` · CI ${pct(r.ci95[0])}–${pct(r.ci95[1])}` : ''}</span></>
  : 'not measured');

/** MVP preset: the model's injection shield at the strength chosen on Tensor Trust validation (protection only). */
export function mvpPreset(m) {
  const p = m?.mvp_preset || {};
  return { concept: SHIELD, strength: typeof p.strength === 'number' ? p.strength : 0.1,
    block: p.block != null ? String(p.block) : '', phase: 'both', positions: 'all_tokens', opt_in: true };
}

function ShieldStat({ m }) {
  const t = m.shield?.test;
  if (m.shield?.status !== 'measured' || !t) {
    return <div><span className="k">Injection shield</span><span className="n">Pending</span><span className="sub">GPU run in progress; no effect shown until measured</span></div>;
  }
  return (
    <div><span className="k">Held-out attack success</span>
      <span className="n tnum">{pct(t.bare?.attack_success?.rate)} → {pct(t.shield?.attack_success?.rate)}</span>
      <span className="sub">paired {pctPts(t.shield?.paired_vs_bare?.mean_diff)}{Array.isArray(t.shield?.paired_vs_bare?.ci95) ? `, 95% CI ${pctPts(t.shield.paired_vs_bare.ci95[0])} to ${pctPts(t.shield.paired_vs_bare.ci95[1])}` : ''}</span>
    </div>
  );
}

function ModelCard({ m, n, active, onPick }) {
  const measured = m.shield?.status === 'measured';
  return (
    <button type="button" className={`card pad model-pick ${active ? 'on' : ''}`} onClick={onPick} aria-pressed={active}>
      <div className="row" style={{ justifyContent: 'space-between' }}>
        <b>{n}. {m.model_id.split('/').pop()}</b>
        <span className={`chip ${measured ? 'ok' : 'warn'}`}>{measured ? 'Shield measured on GPU' : 'Shield GPU run pending'}</span>
      </div>
      <span className="sub mono">{m.model_id}{m.revision ? ` @ ${m.revision.slice(0, 7)}` : ''}</span>
      <div className="grid3">
        <ShieldStat m={m} />
        <div><span className="k">Shield block</span><span className="n tnum">{m.shield?.block ?? '—'}</span><span className="sub">decoder layer</span></div>
        <div><span className="k">Injection-detector heads</span><span className="n tnum">{m.heads?.n_important_heads ?? '—'}</span>
          {typeof m.heads?.heldout?.auroc_attack_vs_benign === 'number' && <span className="sub">held-out AUROC {m.heads.heldout.auroc_attack_vs_benign.toFixed(2)}</span>}</div>
      </div>
    </button>
  );
}

function Preview({ p }) {
  if (!p || p.status === 'not_measured') {
    return <p className="muted small">GPU run pending: the injection-shield vector for this model is being fitted and tested on Kaggle. No effect is shown until it has been measured on held-out attacks.</p>;
  }
  const t = p.test || {}, b = t.bare || {}, s = t.shield || {}, tq = p.truthfulqa || {};
  const label = p.status === 'measured' ? `Measured at exactly this setting (strength ${p.chosen_strength}, chosen on validation)`
    : p.status === 'reference_condition_differs' ? `Your setting differs in ${p.differs_in.join(', ')}; numbers below are for the tested setting (strength ${p.chosen_strength}).`
      : `Held-out numbers are for strength ${p.chosen_strength}. Your strength ${p.requested_strength} was only run on the validation split.`;
  return (
    <div style={{ display: 'grid', gap: 8 }}>
      <p className="small">{label} · <span className="tag mia">REAL_IBM_MIA</span></p>
      <div className="card table-wrap">
        <table>
          <thead><tr><th>Held-out Tensor Trust</th><th>No steering</th><th>Shield</th></tr></thead>
          <tbody>
            <tr><td>Attack success (lower is better)</td><td>{cell(b.attack_success)}</td><td>{cell(s.attack_success)}</td></tr>
            <tr><td>Legitimate access kept</td><td>{cell(b.access_code_utility)}</td><td>{cell(s.access_code_utility)}</td></tr>
            <tr><td>TruthfulQA MC1 (capability)</td><td>{cell(tq.bare?.accuracy)}</td><td>{cell(tq.shield?.accuracy)}</td></tr>
          </tbody>
        </table>
      </div>
      {s.paired_vs_bare && <p className="small">Paired change in attack success: <b>{pctPts(s.paired_vs_bare.mean_diff)}</b>{Array.isArray(s.paired_vs_bare.ci95) ? ` (95% CI ${pctPts(s.paired_vs_bare.ci95[0])} to ${pctPts(s.paired_vs_bare.ci95[1])})` : ''}. {Array.isArray(s.paired_vs_bare.ci95) && s.paired_vs_bare.ci95[1] < 0 ? 'The interval is below zero: fewer hijacks.' : 'The interval includes zero or is above it: no reliable protection on this model.'}</p>}
      {p.status === 'validation_only' && p.validation_nearest && <p className="muted small">Validation split at strength {p.validation_nearest.strength}: attack success {pct(p.validation_nearest.attack_success)}, legitimate access {pct(p.validation_nearest.access_granted)} (bare: {pct(p.validation_bare?.attack_success)} / {pct(p.validation_bare?.access_granted)}).</p>}
      {p.utility_constraint_met === false && <p className="muted small">No strength kept legitimate access within 10 points on validation; the most conservative strength was tested.</p>}
    </div>
  );
}

export default function Steering() {
  const [cat, setCat] = useState(null);
  const [modelId, setModelId] = useState(null);
  const [form, setForm] = useState({ concept: SHIELD, strength: 0.1, block: '', phase: 'both', positions: 'all_tokens', opt_in: true });
  const [res, setRes] = useState(null);
  const [busy, setBusy] = useState(false);

  useEffect(() => { let a = true; api.steering().then((r) => { if (!a) return; setCat(r); if (r.ok) setModelId(r.data.models[0]?.model_id); }); return () => { a = false; }; }, []);
  const model = useMemo(() => cat?.ok ? cat.data.models.find((m) => m.model_id === modelId) : null, [cat, modelId]);
  const max = cat?.ok ? cat.data.max_abs_strength : 0.5;

  const runBuild = async (m, f) => {
    if (!m) return;
    setBusy(true);
    const body = { model_id: m.model_id, concept: SHIELD, strength: snapStrength(f.strength, max), phase: f.phase, positions: f.positions, opt_in: f.opt_in };
    if (f.block !== '') body.block = Number(f.block);
    setRes(await api.steeringProfile(body));
    setBusy(false);
  };
  const build = (e) => { e.preventDefault(); runBuild(model, form); };
  // MVP: every model opens with its protection preset already applied and built (profile only; no model runs here).
  useEffect(() => {
    if (!model) return;
    const f = mvpPreset(model);
    setForm(f);
    runBuild(model, f);
  }, [model?.model_id]);  // eslint-disable-line react-hooks/exhaustive-deps
  const download = () => {
    const blob = new Blob([JSON.stringify(res.data, null, 2)], { type: 'application/json' });
    const a = document.createElement('a');
    a.href = URL.createObjectURL(blob); a.download = `shield-${res.data.profile_sha256.slice(0, 12)}.json`; a.click();
    URL.revokeObjectURL(a.href);
  };

  return (
    <section className="view">
      <div className="head">
        <p className="eyebrow">Protection steering</p>
        <h2>Steer each model away from following injected instructions.</h2>
        <p className="lede">For each model we use IBM vLLM-Hook on a Kaggle GPU to find its own "hijack-compliance" direction: the difference between its internal state on Tensor Trust attacks that hijacked it and attacks it resisted. The injection shield steers against that direction. Strength is chosen on validation attacks and the effect is measured on held-out attacks from defenders never seen during fitting. This page never runs the model, and steering never replaces the external checks.</p>
      </div>

      {!cat ? <div className="card pad"><div className="skeleton" /></div> : !cat.ok ? <p className="err">{cat.error?.message}</p> : (
        <div className="model-row">
          {cat.data.models.map((m, i) => <ModelCard key={m.model_id} m={m} n={i + 1} active={m.model_id === modelId} onPick={() => setModelId(m.model_id)} />)}
        </div>
      )}

      {model && (
        <form className="card pad ask steer-form" onSubmit={build}>
          <div className="row" style={{ justifyContent: 'space-between' }}>
            <h3 style={{ fontSize: 17 }}>Shield profile · {model.model_id.split('/').pop()}</h3>
            <button type="button" className="btn ghost" title={cat.data.presets_note} onClick={() => { const f = mvpPreset(model); setForm(f); runBuild(model, f); }}>MVP preset: injection shield</button>
          </div>
          <div className="form-grid">
            <label>Vector<select value={SHIELD} disabled><option value={SHIELD}>Injection shield (protection)</option></select></label>
            <label>Strength <span className="mono tnum">{snapStrength(form.strength, max).toFixed(2)}</span>
              <input type="range" min={0} max={max} step="0.05" value={form.strength} onChange={(e) => setForm({ ...form, strength: Number(e.target.value) })} aria-valuetext={`${form.strength}`} />
            </label>
            <label>Decoder block<input type="number" min="0" max={model.num_layers ? model.num_layers - 1 : undefined} placeholder={model.shield?.block != null ? `default ${model.shield.block}` : ''} value={form.block} onChange={(e) => setForm({ ...form, block: e.target.value })} /></label>
            <label>Phase<select value={form.phase} onChange={(e) => setForm({ ...form, phase: e.target.value })}><option value="both">prefill + decode</option><option value="prefill">prefill</option><option value="decode">decode</option></select></label>
            <label>Positions<select value={form.positions} onChange={(e) => setForm({ ...form, positions: e.target.value })}><option value="all_tokens">all tokens</option><option value="last_token">last token</option></select></label>
          </div>
          <label className="check"><input type="checkbox" checked={form.opt_in} onChange={(e) => setForm({ ...form, opt_in: e.target.checked })} /> Steering is opt-in. Authorization and egress checks still apply.</label>
          <div className="row"><button className="btn primary" type="submit" disabled={busy || !form.opt_in}>{busy ? 'Building…' : 'Build profile'}</button>
            <span className="muted small">Strength unit: {cat.data.units}.</span></div>
        </form>
      )}

      {res && !res.ok && <p className="err">{res.error?.message} <span className="mono">({res.error?.code})</span></p>}
      {res?.ok && (
        <div className="split">
          <div className="card pad" style={{ display: 'grid', gap: 10 }}>
            <div className="row" style={{ justifyContent: 'space-between' }}>
              <h3 style={{ fontSize: 17 }}>Profile</h3>
              <span className={`chip ${res.data.status === 'bound_to_real_vector' ? 'ok' : 'warn'}`}>{res.data.status === 'vector_not_captured_yet' ? 'GPU run pending' : res.data.status.replace(/_/g, ' ')}</span>
            </div>
            {res.data.status === 'vector_not_captured_yet' && <p className="small muted">Preset is set; it binds to the real shield vector as soon as the Kaggle run for this model is ingested.</p>}
            {res.data.payload_kind && <p className="small muted">Bound template: a GPU worker checks the vector's SHA-256, model, revision and block against the Kaggle run's own manifest, then runs it with <code>python -m model_mountain.steering_lab apply profile.json --results &lt;Kaggle mm_results folder&gt; --prompt "..."</code>.</p>}
            {res.data.note && <p className="small muted">{res.data.note}</p>}
            <pre className="pre small">{JSON.stringify(res.data.ibm_steer_payload || res.data.profile, null, 2)}</pre>
            <span className="sub mono">profile sha256 {res.data.profile_sha256.slice(0, 16)}…</span>
            <div className="row"><button type="button" className="btn ghost" onClick={download}>Download profile</button></div>
            <p className="muted small">{res.data.runs_on}</p>
          </div>
          <div className="card pad" style={{ display: 'grid', gap: 10 }}>
            <h3 style={{ fontSize: 17 }}>Measured protection</h3>
            <Preview p={res.data.preview} />
          </div>
        </div>
      )}

      {cat?.ok && (
        <div className="card pad" style={{ display: 'grid', gap: 8 }}>
          <h3 style={{ fontSize: 17 }}>Attention heads: used only to detect prompt injection</h3>
          <p className="muted small">IBM MIA <code>capture_qk</code> records every head's attention; we keep only the heads whose focus on the system instruction drops when a document carries an injected instruction (Attention Tracker, Hung et al., NAACL 2025 Findings). They feed the prompt-injection check as a detector and are never steered. Captured fp16 Q/K are analyzed in FP32 on the T4.</p>
          <ul className="plain">
            {cat.data.models.map((m) => (
              <li key={m.model_id} className="row" style={{ justifyContent: 'space-between' }}>
                <span>{m.model_id.split('/').pop()}</span>
                <span className="small">{m.heads ? `${m.heads.n_important_heads} heads · held-out AUROC ${typeof m.heads.heldout?.auroc_attack_vs_benign === 'number' ? m.heads.heldout.auroc_attack_vs_benign.toFixed(2) : '—'} (${m.heads.heldout?.n_test_attack ?? '?'} attacks vs ${m.heads.heldout?.n_test_benign ?? '?'} benign, exploratory)` : m.heads_review ? 'No heads yet: capture failed on the T4 (mixed attention geometries); patched rerun pending' : 'GPU run pending'}</span>
              </li>
            ))}
          </ul>
        </div>
      )}
    </section>
  );
}
