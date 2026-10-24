import React, { useEffect, useState } from 'react';
import { api } from '../lib/api.js';
import { boardColumns } from '../lib/logic.js';

const AGENTS = [
  { id: 'claude', name: 'Claude Opus 5.5', role: 'Lead engineer: security, retrieval, MIA runtime, UI' },
  { id: 'codex', name: 'OpenAI Codex', role: 'Architecture, control API, verifies correctness' },
  { id: 'gemini', name: 'Google Antigravity', role: 'Fast checks and repetitive tasks' },
];
const COLS = [['todo', 'To do'], ['doing', 'In progress'], ['review', 'In review'], ['done', 'Done']];

export default function Team() {
  const [r, setR] = useState(null);
  const load = () => api.orchestration().then(setR);
  useEffect(() => { load(); const t = setInterval(load, 20000); return () => clearInterval(t); }, []);
  const cols = r?.ok ? boardColumns(r.data.items) : null;

  return (
    <section className="view">
      <div className="head">
        <p className="eyebrow">Build team</p>
        <h2>Three AI agents built this, coordinated through one task board.</h2>
        <p className="lede">Every task has an owner, acceptance criteria and an independent reviewer. This board reads the live task list.</p>
      </div>

      <div className="agents">
        {AGENTS.map((a) => (
          <div key={a.id} className="card agent">
            <span className={`av ${a.id}`} style={{ justifySelf: 'start' }}>{a.id}</span>
            <b>{a.name}</b>
            <span className="muted small">{a.role}</span>
          </div>
        ))}
      </div>

      {r == null ? <div className="card pad"><div className="skeleton" /></div>
        : !r.ok ? <p className="err">{r.error?.message}</p>
        : (
          <>
            <div className="board">
              {COLS.map(([k, label]) => (
                <div key={k} className="col">
                  <h3><span>{label}</span><span className="tnum">{cols[k].length}</span></h3>
                  {cols[k].map((t) => (
                    <div key={t.id} className="task">
                      <span className="id"><span>{t.id}</span><span className={`av ${t.assigned_agent || 'none'}`}>{t.assigned_agent || 'open'}</span></span>
                      <span>{t.title}</span>
                      {t.blocked && <span className="chip bad" style={{ justifySelf: 'start' }}>Blocked</span>}
                    </div>
                  ))}
                  {cols[k].length === 0 && <span className="muted small" style={{ padding: '4px 6px' }}>Nothing here</span>}
                </div>
              ))}
            </div>
            <p className="muted small">{r.data.live === false || r.data.scope?.includes('snapshot') ? 'Snapshot of the task list.' : 'Refreshes every 20 seconds.'} Hub {r.data.hub_name}.</p>
          </>
        )}
    </section>
  );
}
