import React, { useEffect, useMemo, useState } from 'react';
import { api } from '../lib/api.js';
import { fmtRate, snapStrength } from '../lib/logic.js';

const EMOTIONS = ['afraid', 'angry', 'calm', 'desperate', 'disgusted', 'happy', 'hostile', 'loving', 'sad', 'surprised'];

function ModelCard({ m, active, onPick }) {
  const measured = m.evidence_type === 'REAL_IBM_MIA';
  return (
    <button type="button" className={`card pad model-pick ${active ? 'on' : ''}`} onClick={onPick} aria-pressed={active}>
      <div className="row" style={{ justifyContent: 'space-between' }}>
        <b>{m.model_id.split('/').pop()}</b>
        <span className={`chip ${measured ? 'ok' : 'warn'}`}>{measured ? 'Measured on GPU' : 'GPU run pending'}</span>
      </div>
      <span className="sub mono">{m.model_id}{m.revision ? ` @ ${m.revision.slice(0, 7)}` : ''}</span>
      <div className="grid3">
        <div><span className="k">Emotion vectors</span><span className="n tnum">{m.vectors.length || '—'}</span></div>
        <div><span className="k">Held-out accuracy</span><span className="n tnum">{typeof m.test_accuracy === 'number' ? `${Math.round(m.test_accuracy * 100)}%` : '—'}</span>
          {typeof m.chance === 'number' && <span className="sub">chance {Math.round(m.chance * 100)}%</span>}</div>
        <div><span className="k">Injection heads</span><span className="n tnum">{m.heads?.n_important_heads ?? '—'}</span>
          {typeof m.heads?.heldout?.auroc_attack_vs_benign === 'number' && <span className="sub">held-out AUROC {m.heads.heldout.auroc_attack_vs_benign.toFixed(2)}</span>}</div>
      </div>
    </button>
  );
}

function Preview({ p }) {
  if (!p || p.status === 'not_measured') return <p className="muted small">No GPU measurement for this vector and model yet, so no effect is shown.</p>;
  const r = p.result || {}, b = p.baseline || {};
  return (
    <div style={{ display: 'grid', gap: 8 }}>
      <p className="small">{p.status === 'measured' ? 'Measured at exactly this setting' : p.status === 'reference_condition_differs'
        ? `Measured at the reference setting (block ${p.reference_condition?.block}, prefill + decode, all tokens, strength ${p.measured_strength}). Your setting differs in ${p.differs_in.join(', ')}, so its effect is not measured.`
        : `Nearest measured strength: ${p.measured_strength}`} · <span className="tag mia">REAL_IBM_MIA</span></p>
      <div className="card table-wrap">
        <table>
          <thead><tr><th>Outcome (held-out)</th><th>Unsteered</th><th>Steered</th></tr></thead>
          <tbody>
            <tr><td>Prompt-injection success</td><td>{fmtRate(b.attack_success)}</td><td>{fmtRate(r.attack_success)}</td></tr>
            <tr><td>Capability (exact answers)</td><td>{fmtRate(b.capability)}</td><td>{fmtRate(r.capability)}</td></tr>
            <tr><td>Agrees with false claims</td><td>{fmtRate(b.sycophancy)}</td><td>{fmtRate(r.sycophancy)}</td></tr>
          </tbody>
        </table>
      </div>
      {r.hook_evidence && <p className="muted small">Output comparison: {r.hook_evidence.injection_outputs_differ} of {r.hook_evidence.n_injection} injection replies and {r.hook_evidence.tone_outputs_differ} of {r.hook_evidence.n_tone} tone replies differ from the unsteered run (corroborates that steering took effect; not an independent hook attestation).</p>}
      {r.example && <blockquote className="example small">{r.example}</blockquote>}
    </div>
  );
}

export default function Steering() {
  const [cat, setCat] = useState(null);
  const [modelId, setModelId] = useState(null);
  const [form, setForm] = useState({ concept: 'calm', strength: 0.1, block: '', phase: 'both', positions: 'all_tokens', opt_in: false });
  const [res, setRes] = useState(null);
  const [busy, setBusy] = useState(false);

  useEffect(() => { let a = true; api.steering().then((r) => { if (!a) return; setCat(r); if (r.ok) setModelId(r.data.models[0]?.model_id); }); return () => { a = false; }; }, []);
  const model = useMemo(() => cat?.ok ? cat.data.models.find((m) => m.model_id === modelId) : null, [cat, modelId]);
  const concepts = model?.vectors?.length ? model.vectors.map((v) => v.concept) : EMOTIONS;
  const max = cat?.ok ? cat.data.max_abs_strength : 0.5;

  const build = async (e) => {
    e.preventDefault();
    if (!model) return;
    setBusy(true);
    const body = { model_id: model.model_id, concept: form.concept, strength: snapStrength(form.strength, max), phase: form.phase, positions: form.positions, opt_in: form.opt_in };
    if (form.block !== '') body.block = Number(form.block);
    setRes(await api.steeringProfile(body));
    setBusy(false);
  };
  const preset = (concept, strength) => setForm({ ...form, concept, strength });
  const download = () => {
    const blob = new Blob([JSON.stringify(res.data, null, 2)], { type: 'application/json' });
    const a = document.createElement('a');
    a.href = URL.createObjectURL(blob); a.download = `steering-${res.data.profile_sha256.slice(0, 12)}.json`; a.click();
    URL.revokeObjectURL(a.href);
  };

  return (
    <section className="view">
      <div className="head">
        <p className="eyebrow">Steering</p>
        <h2>Adjust the model's internal state, with the evidence beside every setting.</h2>
        <p className="lede">For each model we capture activations with IBM vLLM-Hook on a Kaggle GPU, fit one direction per emotion, and find the attention heads that lose focus on the instruction during prompt injection. Pick a vector and a strength to build a steering profile. This page never runs the model: profiles run on a GPU worker, and the measured effect shown is the closest setting that actually ran.</p>
      </div>

      {!cat ? <div className="card pad"><div className="skeleton" /></div> : !cat.ok ? <p className="err">{cat.error?.message}</p> : (
        <div className="model-row">
          {cat.data.models.map((m) => <ModelCard key={m.model_id} m={m} active={m.model_id === modelId} onPick={() => { setModelId(m.model_id); setRes(null); }} />)}
        </div>
      )}

      {model && (
        <form className="card pad ask steer-form" onSubmit={build}>
          <div className="row" style={{ justifyContent: 'space-between' }}>
            <h3 style={{ fontSize: 17 }}>Steering profile · {model.model_id.split('/').pop()}</h3>
            <div className="row" style={{ gap: 6 }}>
              <button type="button" className="btn ghost" title={cat.data.presets_note} onClick={() => preset('calm', 0.1)}>Preset: calm +0.10</button>
              <button type="button" className="btn ghost" title={cat.data.presets_note} onClick={() => preset('desperate', -0.1)}>Preset: desperate −0.10</button>
            </div>
          </div>
          <div className="form-grid">
            <label>Vector<select value={form.concept} onChange={(e) => setForm({ ...form, concept: e.target.value })}>{concepts.map((c) => <option key={c}>{c}</option>)}</select></label>
            <label>Strength <span className="mono tnum">{snapStrength(form.strength, max).toFixed(2)}</span>
              <input type="range" min={-max} max={max} step="0.05" value={form.strength} onChange={(e) => setForm({ ...form, strength: Number(e.target.value) })} aria-valuetext={`${form.strength}`} />
            </label>
            <label>Decoder block<input type="number" min="0" max={model.num_layers ? model.num_layers - 1 : undefined} placeholder={model.selected_block != null ? `default ${model.selected_block}` : model.num_layers ? `default ${Math.round(model.num_layers * 2 / 3)}` : ''} value={form.block} onChange={(e) => setForm({ ...form, block: e.target.value })} /></label>
            <label>Phase<select value={form.phase} onChange={(e) => setForm({ ...form, phase: e.target.value })}><option value="both">prefill + decode</option><option value="prefill">prefill</option><option value="decode">decode</option></select></label>
            <label>Positions<select value={form.positions} onChange={(e) => setForm({ ...form, positions: e.target.value })}><option value="all_tokens">all tokens</option><option value="last_token">last token</option></select></label>
          </div>
          <label className="check"><input type="checkbox" checked={form.opt_in} onChange={(e) => setForm({ ...form, opt_in: e.target.checked })} /> I understand steering changes model behavior and is opt-in. Authorization and egress checks still apply.</label>
          {cat.data.presets_note && <p className="muted small">Presets: {cat.data.presets_note}</p>}
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
              <span className={`chip ${res.data.status === 'bound_to_real_vector' ? 'ok' : 'warn'}`}>{res.data.status.replace(/_/g, ' ')}</span>
            </div>
            {res.data.status === 'vector_not_captured_yet' && <p className="small muted">Pending template: it binds to a real vector once the GPU run captures one for this model.</p>}
            {res.data.payload_kind && <p className="small muted">Bound template: a GPU worker resolves the vector by its SHA-256, verifies it, and runs it with <code>python -m model_mountain.steering_lab apply profile.json --vectors &lt;kaggle vectors folder&gt; --prompt "..."</code>.</p>}
            {res.data.note && <p className="small muted">{res.data.note}</p>}
            <pre className="pre small">{JSON.stringify(res.data.ibm_steer_payload || res.data.profile, null, 2)}</pre>
            <span className="sub mono">profile sha256 {res.data.profile_sha256.slice(0, 16)}…</span>
            <div className="row"><button type="button" className="btn ghost" onClick={download}>Download profile</button></div>
            <p className="muted small">{res.data.runs_on}</p>
          </div>
          <div className="card pad" style={{ display: 'grid', gap: 10 }}>
            <h3 style={{ fontSize: 17 }}>Measured effect</h3>
            <Preview p={res.data.preview} />
          </div>
        </div>
      )}
    </section>
  );
}
