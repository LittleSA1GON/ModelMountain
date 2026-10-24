import React, { useEffect, useState } from 'react';
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

const DEFENSE_OF = {
  direct_injection: 'Prompt-injection firewall', role_spoofing: 'Prompt-injection firewall',
  rag_poisoning: 'RAG integrity', data_authorization: 'RAG integrity',
  exfiltration_attempt: 'Exfiltration guard', agent_authorization: 'Exfiltration guard (tool authorization)',
  tool_output_injection: 'Prompt-injection firewall (tool output)',
  mcp_tool_metadata_injection: 'MCP supply-chain guard', mcp_tool_output_injection: 'MCP supply-chain guard',
};

function GpuRecorded() {
  const [x, setX] = useState(null);
  useEffect(() => { let a = true; api.experiments().then((r) => a && setX(r)); return () => { a = false; }; }, []);
  const t = x?.ok ? x.data.tryit : null;
  if (!x) return null;
  if (!t) {
    return <div className="card pad"><b>Recorded on GPU: run pending</b><p className="small muted">A Kaggle kernel runs every gateway scenario on Qwen2.5-1.5B with IBM MIA; real replies appear here once it is ingested.</p></div>;
  }
  const byName = {};
  for (const r of t.records || []) (byName[r.scenario] ||= {})[r.mode] = r;
  const rows = Object.entries(byName).filter(([, v]) => v.unprotected?.attacked);
  const fs = (v) => (typeof v === 'number' ? v.toFixed(3) : '—');
  return (
    <div style={{ display: 'grid', gap: 10 }}>
      <div className="section-title"><h2>Recorded on GPU</h2><span className="tag mia">REAL_IBM_MIA</span></div>
      <p className="muted small">{t.model_id.split('/').pop()} on a Kaggle T4. Each attack scenario was sent to the real model twice: as an unguarded assistant would see it, and through Model Mountain. Tools are never executed. "MIA focus" is the Attention Tracker score from IBM vLLM-Hook capture_qk (lower means attention was pulled away from the instruction). Unguarded unsafe tool proposals: <b className="tnum">{t.totals?.unprotected_unsafe_tool_proposals ?? '—'}</b>; unsafe actions allowed with Model Mountain: <b className="tnum">{t.totals?.protected_unsafe_would_execute ?? '—'}</b>.</p>
      <div className="card table-wrap">
        <table>
          <thead><tr><th>Attack (defense)</th><th>Real model, unguarded</th><th>With Model Mountain</th><th>MIA focus</th></tr></thead>
          <tbody>
            {rows.map(([name, v]) => {
              const u = v.unprotected, pr = v.protected || {};
              return (
                <tr key={name}>
                  <td><b>{name.replace(/-/g, ' ')}</b><span className="sub">{DEFENSE_OF[u.category] || u.category}</span></td>
                  <td className="small">{u.output || '—'}{u.policy?.tool && <span className="sub mono">proposed tool: {u.policy.tool}{u.unauthorized_action_would_execute ? ' (would run unguarded)' : ''}</span>}</td>
                  <td className="small">
                    <span className={`chip ${pr.response_released && !pr.unauthorized_action_would_execute ? 'ok' : 'bad'}`}>{pr.response_released ? 'Released' : 'Withheld'}</span>
                    {pr.rejected_docs?.length > 0 && <span className="sub">documents rejected: {pr.rejected_docs.join(', ')}</span>}
                    {pr.policy?.tool && <span className="sub mono">tool {pr.policy.tool}: {pr.policy.would_allow ? 'allowed' : 'denied'} ({pr.policy.reason})</span>}
                    {pr.prompt_markers?.length > 0 && <span className="sub mono">markers: {pr.prompt_markers.join(', ')}</span>}
                  </td>
                  <td className="tnum mono small">{fs(u.mia_score)} → {fs(pr.mia_score)}</td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
      <p className="muted small">Model extraction (the fifth defense) acts before any model call: see the cross-account campaign on the Defenses page.</p>
    </div>
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
        <p className="lede">The interactive box runs the real rule engine on CPU with sample company policies. Below it, "Recorded on GPU" shows the same gateway on a real model (Qwen2.5-1.5B on a Kaggle T4 with IBM MIA).</p>
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

      <GpuRecorded />
    </section>
  );
}
