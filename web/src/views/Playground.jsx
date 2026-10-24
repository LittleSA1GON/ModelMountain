import React, { useState } from 'react';
import { api } from '../lib/api.js';
import { EXAMPLES, VERDICT_LABEL, stagesFor, traceRows, verdictOf } from '../lib/logic.js';

const MODEL = 'Qwen/Qwen2-1.5B-Instruct';
const MARK = { pass: '✓', stop: '✕', hold: '!', skip: '' };

function Pane({ title, note, result, protectedPane, busy }) {
  const v = result?.ok ? verdictOf(result.data) : 'none';
  const d = result?.ok ? result.data : null;
  return (
    <article className="card pane">
      <header>
        <div>
          <h3>{title}</h3>
          <p className="muted small">{note}</p>
        </div>
        <span className={`verdict ${v}`}>{busy ? 'Running…' : d ? VERDICT_LABEL[v] : 'Waiting'}</span>
      </header>

      {result && !result.ok && <p className="err">{result.error?.message} <span className="mono">({result.error?.code})</span></p>}

      <div className="answer" aria-live="polite">
        {busy ? <div className="skeleton" style={{ width: '70%' }} /> : d ? d.answer || <span className="muted">No text released.</span> : <span className="muted">Run a question to see the answer.</span>}
      </div>

      {protectedPane && d && (
        <ol className="steps" aria-label={traceRows(d.trace) ? 'Checks (measured trace)' : 'Checks (inferred from reasons)'}>
          {(traceRows(d.trace) || stagesFor(d)).map((s, i) => (
            <li key={s.id} className={`reveal ${s.state}`} style={{ animationDelay: `${i * 110}ms` }}>
              <span className="mark">{MARK[s.state]}</span>
              <span>{s.name}</span>
              <span className="muted small mono">{s.state === 'skip' ? 'not reached' : s.reason || 'passed'}</span>
            </li>
          ))}
        </ol>
      )}

      {d && (
        <div className="meta">
          {d.citations?.length > 0 && <span>Sources: {d.citations.map((c) => <span key={c} className="tag" style={{ marginLeft: 4 }}>{c}</span>)}</span>}
          {typeof d.latency_ms === 'number' && <span className="tnum">{d.latency_ms.toFixed(1)} ms</span>}
          <span className="tag">{d.evidence_type}</span>
        </div>
      )}
    </article>
  );
}

export default function Playground() {
  const [q, setQ] = useState(EXAMPLES[1].text);
  const [busy, setBusy] = useState(false);
  const [a, setA] = useState(null);
  const [d, setD] = useState(null);

  const run = async (e) => {
    e?.preventDefault();
    const text = q.trim();
    if (!text || busy) return;
    setBusy(true); setA(null); setD(null);
    const [ra, rd] = await Promise.all([api.infer(text, 'A', MODEL), api.infer(text, 'D', MODEL)]);
    setA(ra); setD(rd); setBusy(false);
  };

  return (
    <section className="view">
      <div className="head">
        <p className="eyebrow">Try it</p>
        <h2>Send the same question with and without protection.</h2>
        <p className="lede">This demo runs the real rule engine on CPU with sample company policies. No language model runs here, and the page says so on every result.</p>
      </div>

      <form className="ask" onSubmit={run}>
        <label htmlFor="q" className="small muted">Question</label>
        <textarea id="q" value={q} maxLength={2000} onChange={(e) => setQ(e.target.value)} />
        <div className="row" style={{ justifyContent: 'space-between' }}>
          <div className="examples">
            {EXAMPLES.map((x) => (
              <button type="button" key={x.text} onClick={() => setQ(x.text)}><i>{x.kind}</i>{x.text.length > 46 ? x.text.slice(0, 44) + '…' : x.text}</button>
            ))}
          </div>
          <button className="btn primary" type="submit" disabled={busy || !q.trim()}>{busy ? 'Checking…' : 'Run both'}</button>
        </div>
      </form>

      <div className="versus">
        <Pane title="Without protection" note="Baseline fixture. Shows what an unguarded assistant would pass through." result={a} busy={busy} />
        <Pane title="With Model Mountain" note="Every request goes through the five defenses; each stage below is what the gateway actually recorded." result={d} busy={busy} protectedPane />
      </div>
    </section>
  );
}
