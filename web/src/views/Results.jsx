import React, { useEffect, useMemo, useState } from 'react';
import { api } from '../lib/api.js';
import { summarizeRuns, conditionRows, bestCondition, evidenceClass, pct } from '../lib/logic.js';

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
  const rows = conditionRows(p);
  const best = bestCondition(rows);
  const a = rows.find((r) => r.id === 'A_bare');
  return (
    <div className="card">
      <div className="pad prot-head">
        <div>
          <b>{short(m.model_id)}</b>
          <span className="sub">{p.benchmark} · {p.n_test} held-out attacks</span>
        </div>
        {best && a && (
          <div className="callout">
            <span className="big tnum">{pct(a.asr)} → {pct(best.asr)}</span>
            <span className="small muted">attacks that got through, unprotected vs {best.label.toLowerCase()}</span>
          </div>
        )}
      </div>
      <div className="table-wrap">
        <table className="prot">
          <thead><tr><th>Protection</th><th>Attacks that succeeded</th><th>Real password still works</th></tr></thead>
          <tbody>
            {rows.map((r) => (
              <tr key={r.id} className={r.id === best?.id ? 'best' : ''}>
                <td><b>{r.label}</b>{r.mia && <span className="tag mia">MIA</span>}{r.skipped && <span className="sub">{r.reason}</span>}</td>
                <td>{!r.skipped && <><Bar value={r.asr} ci={r.asrCi} tone="bad" /><span className="tnum">{pct(r.asr)}</span> <Ci ci={r.asrCi} /></>}</td>
                <td>{!r.skipped && <><Bar value={r.util} ci={r.utilCi} tone="ok" /><span className="tnum">{pct(r.util)}</span></>}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <div className="pad grid3 top-line">
        <div><span className="k">Activation monitor AUROC</span><span className="n tnum">{p.monitor.auroc_deepset_test?.toFixed(2) ?? '—'}</span><span className="sub">deepset test set, injection vs normal</span></div>
        <div><span className="k">Caught at 5% false alarms</span><span className="n tnum">{pct(p.monitor.tpr?.rate)}</span><span className="sub">wrongly blocked {pct(p.monitor.fpr?.rate)}</span></div>
        <div><span className="k">TruthfulQA, with steering</span><span className="n tnum">{pct(p.truthfulqa?.calm_steer?.accuracy?.rate ?? p.truthfulqa?.baseline?.accuracy?.rate)}</span>
          <span className="sub">without {pct(p.truthfulqa?.baseline?.accuracy?.rate)} · chance {pct(p.truthfulqa?.baseline?.chance)}</span></div>
      </div>
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

function Emotions({ m }) {
  const e = m.emotions;
  const sweep = e.layer_sweep || [];
  const max = Math.max(...sweep.map((s) => s.val_accuracy || 0), 0.01);
  const rw = e.monitor_realworld?.tensor_trust_attack_vs_access_code || {};
  const top = Object.entries(rw).filter(([, v]) => v != null).sort((x, y) => Math.abs(y[1] - 0.5) - Math.abs(x[1] - 0.5))[0];
  return (
    <div className="card pad emo">
      <div><b>{short(m.model_id)}</b><span className="sub">block {e.selected_block} of the residual stream · {Math.round(e.depth * 100)}% depth</span></div>
      <div className="grid3">
        <div><span className="k">Held-out topic accuracy</span><span className="n tnum">{pct(e.test_accuracy)}</span><span className="sub">10 emotions · chance {pct(e.chance)} · n={e.test_n}</span></div>
        <div><span className="k">Unlabeled scenarios</span><span className="n tnum">{pct(e.implicit?.accuracy)}</span><span className="sub">emotion never named · n={e.implicit?.n}</span></div>
        <div><span className="k">Valence alignment</span><span className="n tnum">{e.valence_r?.toFixed(2) ?? '—'}</span><span className="sub">|r| of first PC with positive/negative</span></div>
      </div>
      <div className="sweep" aria-label="Validation accuracy by layer depth">
        {sweep.map((s) => (
          <div key={s.block} className={`scol ${s.block === e.selected_block ? "sel" : ""}`} title={`block ${s.block}: ${pct(s.val_accuracy)}`}>
            <span style={{ height: `${(s.val_accuracy / max) * 100}%` }} />
            <small className="tnum">{Math.round(s.depth * 100)}%</small>
          </div>
        ))}
      </div>
      {top && <p className="small muted">Strongest emotion signal on real attacks: <b>{top[0]}</b> separates Tensor Trust attacks from real passwords at AUROC {top[1].toFixed(2)}.</p>}
    </div>
  );
}

function Steering({ m }) {
  const s = m.steer;
  return (
    <div className="card">
      <div className="pad"><b>{short(m.model_id)}</b><span className="sub">{s.units}</span></div>
      <div className="table-wrap"><table>
        <thead><tr><th>Steer toward</th><th>Strength</th><th>Injection success</th><th>Capability</th><th>Agrees with false claims</th><th>Tone shift</th></tr></thead>
        <tbody>
          <tr className="base"><td>None (baseline)</td><td>0</td><td className="tnum">{pct(s.baseline.attack_success?.rate)}</td><td className="tnum">{pct(s.baseline.capability?.rate)}</td><td className="tnum">{pct(s.baseline.sycophancy?.rate)}</td><td>—</td></tr>
          {s.rows.map((r) => (
            <tr key={r.emotion + r.strength}>
              <td>{r.emotion}</td><td className="tnum">{r.strength > 0 ? '+' : ''}{r.strength}</td>
              <td className="tnum">{pct(r.attack_success?.rate)}</td><td className="tnum">{pct(r.capability?.rate)}</td>
              <td className="tnum">{pct(r.sycophancy?.rate)}</td>
              <td className="tnum">{r.tone_shift == null ? '—' : `${r.tone_shift > 0 ? '+' : ''}${r.tone_shift.toFixed(2)} ${r.tone_label || ''}`}</td>
            </tr>
          ))}
        </tbody>
      </table></div>
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
  const m = models[sel];
  const items = r?.ok ? r.data.items || [] : [];
  const demo = summarizeRuns(items.filter((i) => evidenceClass(i.evidence_type) === 'synthetic'));
  const diag = items.filter((i) => evidenceClass(i.evidence_type) === 'diagnostic');

  return (
    <section className="view">
      <div className="head">
        <p className="eyebrow">Results</p>
        <h2>Measured on real attacks, on real GPUs.</h2>
        <p className="lede">Every number below comes from a Kaggle run of IBM vLLM-Hook on public benchmarks. Attacks are human-written; the model never saw the test split while the defenses were tuned.</p>
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

          {m?.protect && (
            <div>
              <div className="section-title"><h2>Protection against prompt injection</h2><span className="muted small">Tensor Trust hijacking benchmark</span></div>
              <Protection m={m} />
            </div>
          )}
          {m?.emotions && (
            <div>
              <div className="section-title"><h2>Emotion directions</h2><span className="muted small">Method of Anthropic (2026), adapted to small open models</span></div>
              <Emotions m={m} />
            </div>
          )}
          {m?.steer && (
            <div>
              <div className="section-title"><h2>What steering changes</h2><span className="muted small">Same prompts, greedy decoding, vs unsteered</span></div>
              <Steering m={m} />
            </div>
          )}
          {x.data.stories?.samples?.length > 0 && (
            <details className="card pad">
              <summary>Training stories ({x.data.stories.kept} written by {short(x.data.stories.generator?.model_id)})</summary>
              <div className="stories">{x.data.stories.samples.map((s) => <div key={s.emotion}><span className="chip">{s.emotion}</span><p className="small">{s.text}</p></div>)}</div>
            </details>
          )}
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
