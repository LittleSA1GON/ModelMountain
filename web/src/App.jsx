import React, { useEffect, useState } from 'react';
import { api } from './lib/api.js';
import Overview from './views/Overview.jsx';
import Playground from './views/Playground.jsx';
import Defenses from './views/Defenses.jsx';
import Steering from './views/Steering.jsx';
import Lab from './views/Lab.jsx';
import Results from './views/Results.jsx';
import Team from './views/Team.jsx';

const VIEWS = [
  { id: 'overview', label: 'Overview', C: Overview },
  { id: 'try', label: 'Try it', C: Playground },
  { id: 'defenses', label: 'Defenses', C: Defenses },
  { id: 'steering', label: 'Steering', C: Steering },
  { id: 'lab', label: 'MIA Lab', C: Lab },
  { id: 'results', label: 'Results', C: Results },
  { id: 'team', label: 'Build team', C: Team },
];

const fromHash = () => {
  const h = (typeof location !== 'undefined' && location.hash.slice(1)) || '';
  return VIEWS.some((v) => v.id === h) ? h : 'overview';
};

function Logo() {
  return (
    <svg viewBox="0 0 32 32" aria-hidden="true">
      <path d="M2 27 12 9l5 8 4-5 9 15z" fill="var(--accent)" />
      <path d="M12 9l2.6 4.7-2.6 1.8-2.4-1.6z" fill="var(--surface)" opacity=".9" />
    </svg>
  );
}

export default function App() {
  const [view, setView] = useState(fromHash);
  const [health, setHealth] = useState(null);

  useEffect(() => {
    const onHash = () => setView(fromHash());
    addEventListener('hashchange', onHash);
    return () => removeEventListener('hashchange', onHash);
  }, []);
  useEffect(() => {
    let alive = true;
    const load = () => api.health().then((r) => alive && setHealth(r));
    load();
    const t = setInterval(load, 30000);
    return () => { alive = false; clearInterval(t); };
  }, []);

  const go = (id) => {
    setView(id);
    try { history.replaceState(null, '', '#' + id); } catch { /* sandboxed */ }
    scrollTo({ top: 0, behavior: 'smooth' });
  };
  const onKey = (e) => {
    const i = VIEWS.findIndex((v) => v.id === view);
    if (e.key === 'ArrowRight') go(VIEWS[(i + 1) % VIEWS.length].id);
    if (e.key === 'ArrowLeft') go(VIEWS[(i - 1 + VIEWS.length) % VIEWS.length].id);
  };

  const Current = VIEWS.find((v) => v.id === view).C;
  const up = health?.ok;

  return (
    <>
      <header className="bar">
        <div className="bar-inner">
          <a className="brand" href="#overview" onClick={(e) => { e.preventDefault(); go('overview'); }}>
            <Logo /><b>Model Mountain</b>
          </a>
          <nav className="nav" role="tablist" aria-label="Sections" onKeyDown={onKey}>
            {VIEWS.map((v) => (
              <button key={v.id} role="tab" aria-selected={view === v.id} tabIndex={view === v.id ? 0 : -1} onClick={() => go(v.id)}>
                {v.label}
              </button>
            ))}
          </nav>
          <div className="live" title={up ? 'Control API reachable' : 'Control API unreachable'}>
            <span className={`dot ${health == null ? '' : up ? 'ok' : 'bad'}`} />
            <span className="txt">{health == null ? 'Connecting' : up ? 'API online' : 'API offline'}</span>
          </div>
        </div>
      </header>
      <main className="page" key={view}>
        <Current health={health} go={go} />
      </main>
      <footer className="foot">
        <div className="page">
          <span>Model Mountain · SpartHill Hacks 2026 · IBM AI Challenge</span>
          <span className="mono">{health?.data?.project_id ? `project ${health.data.project_id}` : ''}</span>
        </div>
      </footer>
    </>
  );
}
