import React, { useEffect, useMemo, useState } from 'react';
import { api } from '../lib/api.js';
import { summarizeRuns, conditionRows, evidenceClass, pct } from '../lib/logic.js';

const short = (id = '') => id.split('/').pop();

function Ci({ ci }) {
  if (!Array.isArray(ci)) return null;
  return <span className="ci tnum">{pct(ci[0])}–{pct(ci[1])}</span>;
}

/** Horizontal bar with a 95% interval whisker. */
function Bar({ value, ci, tone }) {
  if (value == null) return <div className="hbar empty-bar" />;
  return (
    <div className="hbar" role="img" aria-label={`${pct(value)}${ci ? `, 95% interval ${pct(ci[0])} to ${pct(ci[1])}` : ''}`}>
      <span className={`fill ${tone}`} style={{ width: `${Math.max(value * 100, 0.8)}%` }} />
      {Array.isArray(ci) && <span className="whisker" style={{ left: `${ci[0] * 100}%`, width: `${Math.max((ci[1] - ci[0]) * 100, 0.4)}%` }} />}
    </div>
  );
}

function Protection({ m }) {
  const p = m.protect;
  const rows = conditionRows(p).filter((r) => !['C_calm_steer', 'E_spotlight_steer', 'F_all_layers'].includes(r.id));
  return (
    <div className="card">
      <div className="pad prot-head">
        <div>
          <b>{short(m.model_id)}</b>
          <span className="sub">{p.benchmark} · {p.n_test} held-out attacks</span>
        </div>
      </div>
      <div className="table-wrap">
        <table className="prot">
          <thead><tr><th>Condition</th><th>Attacks that succeeded</th><th>Legitimate access code works</th></tr></thead>
          <tbody>
            {rows.map((r) => (
              <tr key={r.id}>
                <td><b>{r.label}</b>{r.mia && <span className="tag mia">MIA</span>}{r.skipped && <span className="sub">{r.reason}</span>}{r.posthoc && <span className="sub">Post-hoc estimate on recorded replies; no gate ran at serving time</span>}</td>
                <td>{!r.skipped && <><Bar value={r.asr} ci={r.asrCi} tone="bad" /><span className="tnum">{pct(r.asr)}</span> <Ci ci={r.asrCi} /></>}</td>
                <td>{!r.skipped && <><Bar value={r.util} ci={r.utilCi} tone="ok" /><span className="tnum">{pct(r.util)}</span></>}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <div className="pad grid3 top-line">
        <div><span className="k">Activation monitor AUROC</span><span className="n tnum">{p.monitor.auroc_deepset_test?.toFixed(2) ?? '—'}</span><span className="sub">deepset test set, injection vs normal</span></div>
        <div><span className="k">Held-out detection</span><span className="n tnum">{pct(p.monitor.tpr?.rate)}</span><span className="sub">training-calibrated threshold · test false positives {pct(p.monitor.fpr?.rate)}</span></div>
        <div><span className="k">Tensor Trust prompts flagged</span><span className="n tnum">{pct(p.monitor.tensor_trust_attack_flag_rate?.rate)}</span><span className="sub">attacks · legitimate prompts flagged {pct(p.monitor.tensor_trust_access_code_false_block_rate?.rate)}</span></div>
      </div>
      <p className="pad small muted">Tensor Trust uses a chat adaptation. TruthfulQA MC1 choices are capped at six including the correct answer; these are not standard leaderboard scores. Monitor-gated rows are post-hoc estimates and must be assessed with their legitimate-request utility.</p>
      {p.conditions?.A_bare?.examples?.length > 0 && (
        <details className="pad top-line">
          <summary>Example attacks and unprotected replies</summary>
          {p.conditions.A_bare.examples.map((e, i) => (
            <div key={i} className="example"><p className="mono small">{e.attack}</p><p className="small">→ {e.reply}</p></div>
          ))}
        </details>
      )}
    </div>
  );
}

function Heads({ m }) {
  const h = m.heads;
  const held = h.heldout || {};
  return (
    <div className="card pad" style={{ display: 'grid', gap: 10 }}>
      <div><b>{short(m.model_id)}</b><span className="sub">IBM MIA capture_qk · Attention Tracker criterion (Hung et al., NAACL 2025 Findings), k = {h.k_used}{h.k_used !== h.k_paper_default ? ` (paper default ${h.k_paper_default})` : ''}{typeof h.head_capture_coverage === 'number' ? ` · finite head coverage ${pct(h.head_capture_coverage)}` : ' · full head coverage not recorded'}</span></div>
      <div className="grid3">
        <div><span className="k">Injection-sensitive heads</span><span className="n tnum">{h.n_important_heads}</span><span className="sub">{h.capped ? 'capped at the strongest 64' : 'all heads passing the criterion'}</span></div>
        <div><span className="k">Held-out AUROC</span><span className="n tnum">{typeof held.auroc_attack_vs_benign === 'number' ? held.auroc_attack_vs_benign.toFixed(2) : '—'}</span><span className="sub">attack vs benign · {held.n_test_attack} vs {held.n_test_benign} · split by {held.split_unit}</span></div>
        <div><span className="k">Config fingerprint</span><span className="n mono small">{String(h.config_sha256 || '').slice(0, 12)}</span><span className="sub">IBM attention_tracker JSON</span></div>
      </div>
      {Array.isArray(h.top) && h.top.length > 0 && <p className="small muted mono">Top heads [layer, head]: {h.top.slice(0, 10).map((x) => `[${x[0]},${x[1]}]`).join(' ')}</p>}
      <p className="small muted">Role: prompt-injection detector only; these heads are never steered.{h.analysis?.precision ? ` Analysis precision: ${h.analysis.precision}.` : ''} The held-out set is small (exploratory).</p>
    </div>
  );
}

function Shield({ m }) {
  const t = m.shield?.test || {}, b = t.bare || {}, s = t.shield || {}, pr = s.paired_vs_bare || {};
  return (
    <div className="card pad" style={{ display: 'grid', gap: 8 }}>
      <div><b>{short(m.model_id)}</b><span className="sub">Injection shield at block {m.shield?.artifact?.block}, strength {s.strength} (chosen on validation) · held-out n = {m.shield?.n_test}</span></div>
      <div className="grid3">
        <div><span className="k">Attack success</span><span className="n tnum">{pct(b.attack_success?.rate)} → {pct(s.attack_success?.rate)}</span>
          <span className="sub">paired {typeof pr.mean_diff === 'number' ? `${(100 * pr.mean_diff).toFixed(1)} pts` : '—'}{Array.isArray(pr.ci95) ? `, 95% CI ${(100 * pr.ci95[0]).toFixed(1)} to ${(100 * pr.ci95[1]).toFixed(1)}` : ''}</span></div>
        <div><span className="k">Legitimate access kept</span><span className="n tnum">{pct(b.access_code_utility?.rate)} → {pct(s.access_code_utility?.rate)}</span></div>
        <div><span className="k">TruthfulQA MC1</span><span className="n tnum">{pct(m.shield?.truthfulqa?.bare?.accuracy?.rate)} → {pct(m.shield?.truthfulqa?.shield?.accuracy?.rate)}</span></div>
      </div>
      <p className="small muted">Direction: {m.shield?.artifact?.direction_source}. {Array.isArray(pr.ci95) && pr.ci95[1] < 0 ? 'The interval is below zero: fewer hijacks on held-out attacks.' : 'The interval includes zero or is above it: no reliable protection on this model.'}</p>
    </div>
  );
}


function Pending({ x }) {
  return (
    <div className="empty">
      <b>{x?.ok ? 'The Kaggle GPU run has not been ingested yet.' : 'Results are unavailable.'}</b>
      <p className="small" style={{ marginTop: 6 }}>
        {x?.ok ? 'One private notebook on 2 × Tesla T4 runs Qwen2.5-1.5B, Granite-3.1-2B and Gemma-4-E4B through IBM vLLM-Hook, then the results appear here.'
          : x?.error?.message}
      </p>
    </div>
  );
}

export default function Results() {
  const [x, setX] = useState(null);
  const [r, setR] = useState(null);
  const [sel, setSel] = useState(0);
  useEffect(() => {
    let a = true;
    api.experiments().then((v) => a && setX(v));
    api.reports().then((v) => a && setR(v));
    return () => { a = false; };
  }, []);
  const models = useMemo(() => (x?.ok ? (x.data.models || []).filter((m) => m.status !== 'blocked' || m.phases) : []), [x]);
  const ingested = x?.ok && x.data.status === 'ingested';
  const hasProtect = ingested && (x.data.models || []).some((mm) => mm.protect);
  const m = models[sel];
  const items = r?.ok ? r.data.items || [] : [];
  const demo = summarizeRuns(items.filter((i) => evidenceClass(i.evidence_type) === 'synthetic'));
  const diag = items.filter((i) => evidenceClass(i.evidence_type) === 'diagnostic');

  return (
    <section className="view">
      <div className="head">
        <p className="eyebrow">Results</p>
        <h2>{hasProtect ? 'Real-model evaluation on GPU.' : 'Real-model evaluation (GPU runs pending).'}</h2>
        <p className="lede">Every GPU number comes from a Kaggle run of IBM vLLM-Hook (MIA) and covers three MIA defenses: the injection shield (hidden-state capture plus steering), the activation monitor (hidden-state probe) and the Attention Tracker detector heads (Q/K capture). Protection is measured on held-out Tensor Trust attacks; the attention heads use our own labeled set. The CPU demo summary at the bottom is not a model measurement.</p>
      </div>

      {x == null ? <div className="card pad"><div className="skeleton" /></div> : !ingested ? <Pending x={x} /> : (
        <>
          <div className="card pad runmeta">
            <span className="tag">{x.data.evidence_type}</span>
            <span className="small">{(x.data.runtime?.gpus || []).length} × {x.data.runtime?.gpus?.[0]?.name || 'GPU'}</span>
            <span className="small mono">IBM MIA {String(x.data.runtime?.ibm_mia_commit || '').slice(0, 7)}</span>
            <span className="small mono">vLLM {x.data.runtime?.vllm}</span>
            {x.data.kernel && <span className="small mono">{x.data.kernel}{x.data.kernel_version ? ` v${x.data.kernel_version}` : ''}</span>}
            <span className="small muted">finished {x.data.finished ? new Date(x.data.finished).toLocaleString() : '—'}</span>
          </div>

          <div className="seg" role="tablist" aria-label="Model">
            {models.map((mm, i) => (
              <button key={mm.model_id} role="tab" aria-selected={i === sel} onClick={() => setSel(i)}>
                {short(mm.model_id)} <span className={`dot ${mm.status === 'measured' ? 'ok' : mm.status === 'partial' ? 'warn' : 'bad'}`} />
              </button>
            ))}
          </div>

          {m && m.status === 'blocked' && (
            <div className="card pad">
              <b>{short(m.model_id)} did not complete on this GPU.</b>
              {Object.entries(m.phases || {}).filter(([, v]) => v.rc).map(([k, v]) => (
                <details key={k}><summary className="small">{k} failed</summary><pre className="mono small pre">{v.error_tail}</pre></details>
              ))}
            </div>
          )}

          {m && !m.shield && (
            <div className="card pad"><b>Injection shield (MIA steering): GPU run pending</b><p className="small muted">The shield kernel fits each model's hijack-compliance direction with MIA hidden-state capture and tests MIA steering on held-out Tensor Trust attacks. No effect is shown until that run is ingested.</p></div>
          )}
          {m?.shield && (
            <div>
              <div className="section-title"><h2>Injection shield (MIA steering)</h2><span className="muted small">MIA capture_hs direction, applied with the MIA steer worker · held-out Tensor Trust</span></div>
              <Shield m={m} />
            </div>
          )}
          {m?.protect && (
            <div>
              <div className="section-title"><h2>MIA activation monitor and prompt baseline</h2><span className="muted small">Tensor Trust hijacking benchmark</span></div>
              <Protection m={m} />
            </div>
          )}
          {m?.heads && (
            <div>
              <div className="section-title"><h2>Attention Tracker detector heads (MIA capture_qk)</h2><span className="muted small">Our labeled behavior tests · selected on training groups, scored on held-out groups</span></div>
              <Heads m={m} />
            </div>
          )}
          {m?.heads_review && <div className="card pad"><b>Attention result withheld</b><p className="small muted">{m.heads_review.reason}</p></div>}
        </>
      )}

      <div>
        <div className="section-title"><h2>Demo runs on this server</h2><span className="tag">CPU_SYNTHETIC</span></div>
        {r?.ok && demo.total > 0 ? (
          <div className="card"><div className="stats">
            <div className="stat"><span className="n tnum">{demo.total}</span><span className="k">Requests</span></div>
            <div className="stat"><span className="n tnum" style={{ color: 'var(--bad)' }}>{demo.deny}</span><span className="k">Blocked</span></div>
            <div className="stat"><span className="n tnum" style={{ color: 'var(--ok)' }}>{demo.allow}</span><span className="k">Answered or declined</span></div>
            <div className="stat"><span className="n tnum">{demo.p50 == null ? '—' : demo.p50.toFixed(1)}</span><span className="k">Median ms</span></div>
          </div><p className="pad muted small top-line">Rule checks on sample policies from the Try it tab. Not a model benchmark.</p></div>
        ) : r?.ok ? <div className="empty">No demo runs yet. Try a question in <b>Try it</b>.</div> : null}
        {diag.length > 0 && <p className="muted small" style={{ marginTop: 8 }}>{diag.length === 1 ? 'One hardware/compatibility diagnostic is' : `${diag.length} hardware/compatibility diagnostics are`} listed in MIA Lab, not here.</p>}
      </div>
    </section>
  );
}
