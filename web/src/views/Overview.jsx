import React from 'react';
import { STAGES } from '../lib/logic.js';

function StatusRow({ label, value, tone }) {
  return (
    <div className="item">
      <span className="label">{label}</span>
      <span className={`chip ${tone}`}>{value}</span>
    </div>
  );
}

export default function Overview({ health, go }) {
  const h = health?.ok ? health.data : null;
  return (
    <section className="view">
      <div className="hero">
        <div>
          <p className="eyebrow">SpartHill Hacks 2026 · IBM AI Challenge</p>
          <h1 style={{ marginTop: 12 }}>A security gateway for company AI assistants.</h1>
          <p className="lede">
            Assistants that read internal documents and call tools can be steered by a poisoned file or a crafted prompt.
            Model Mountain checks every request before and after the model runs, and studies the model's own activations with IBM's vLLM-Hook.
          </p>
          <div className="row">
            <button className="btn primary" onClick={() => go('try')}>Try the gateway</button>
            <button className="btn ghost" onClick={() => go('defenses')}>See the five defenses</button>
            <button className="btn ghost" onClick={() => go('steering')}>Steer a model</button>
          </div>
          <svg className="ridge" viewBox="0 0 600 56" preserveAspectRatio="none" aria-hidden="true">
            <path d="M0 52 L70 30 L110 40 L190 8 L250 34 L300 22 L380 46 L450 16 L520 38 L600 26" fill="none" stroke="currentColor" strokeWidth="1.5" />
            <path d="M0 56 L80 40 L140 48 L210 26 L270 44 L340 34 L410 52 L480 32 L600 44" fill="none" stroke="currentColor" strokeWidth="1" opacity=".6" />
          </svg>
        </div>

        <div className="card status" aria-live="polite">
          <h3>System status</h3>
          {health == null ? (
            <div className="pad" style={{ display: 'grid', gap: 12 }}><div className="skeleton" /><div className="skeleton" /><div className="skeleton" /></div>
          ) : !h ? (
            <div className="pad"><p className="err">{health.error?.message} Start it with <code>python scripts/serve_web.py</code>.</p></div>
          ) : (
            <>
              <StatusRow label="Control API" value="Online" tone="ok" />
              <StatusRow label="Demo mode" value={h.simulation_available ? 'CPU simulation' : 'Off'} tone="info" />
              <StatusRow label="Remote GPU worker" value={h.remote_configured ? 'Connected' : 'Not connected'} tone={h.remote_configured ? 'ok' : ''} />
              <StatusRow label="MIA capture report" value={h.capture_smoke_available ? 'Recorded' : 'Pending'} tone={h.capture_smoke_available ? 'ok' : 'warn'} />
              <StatusRow label="Batch model evaluations" value={h.batch_results_available ? 'Available' : 'Pending'} tone={h.batch_results_available ? 'info' : 'warn'} />
            </>
          )}
        </div>
      </div>

      <div>
        <div className="section-title"><h2>How a request is checked</h2><span className="muted small">Each step can stop the request</span></div>
        <ol className="card flow">
          {STAGES.map((s) => (<li key={s.id}><b>{s.name}</b><span>{s.hint}</span></li>))}
        </ol>
      </div>

      <div className="split">
        <div className="card pad" style={{ display: 'grid', gap: 8 }}>
          <h3 style={{ fontSize: 17 }}>Who it protects</h3>
          <p className="muted">Teams running internal assistants over HR, finance and IT knowledge bases, where a wrong answer or an unauthorized action has real cost.</p>
        </div>
        <div className="card pad" style={{ display: 'grid', gap: 8 }}>
          <h3 style={{ fontSize: 17 }}>What is measured so far</h3>
          <p className="muted">{h?.batch_results_available
            ? 'Saved GPU evaluations and CPU rule fixtures are reported separately. Steering can worsen outcomes; see each model’s results and uncertainty.'
            : h?.capture_smoke_available
              ? 'A real Qwen activation capture is recorded. Full model evaluations are pending; the interactive gateway uses labeled CPU fixtures.'
              : 'CPU rule fixtures are available. Real-model and activation-steering results appear after GPU runs finish and their artifacts are reviewed.'}</p>
        </div>
      </div>
      <details className="card pad disclose">
        <summary><b>How this was built</b><span className="muted small">AI tools and existing components</span></summary>
        <div className="disclose-grid">
          <div>
            <p className="eyebrow">AI tools</p>
            <ul>
              <li><b>Claude Opus 5.5</b> (Claude Cowork): lead engineer. Kaggle MIA runtime, steering-vector datasets, this web app, security reviews.</li>
              <li><b>OpenAI Codex</b>: interface contracts, control API, metrics, independent verification, Kaggle and Vercel runs.</li>
              <li><b>Google Antigravity</b>: mechanical checks only. Its earlier UI and evaluation set were withdrawn.</li>
            </ul>
          </div>
          <div>
            <p className="eyebrow">Existing components</p>
            <ul>
              <li>Model Mountain v4 security gateway, RAG and MCP checks (pre-existing project code).</li>
              <li>IBM vLLM-Hook (MIA), vLLM, PyTorch, Hugging Face models (Qwen, IBM Granite).</li>
              <li>React, Vite, Python cryptography, IBM Plex typefaces.</li>
            </ul>
          </div>
        </div>
      </details>
    </section>
  );
}
