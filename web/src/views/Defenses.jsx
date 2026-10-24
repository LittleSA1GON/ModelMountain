import React, { useEffect, useState } from 'react';
import { api } from '../lib/api.js';
import { toneOf, VERDICT_TEXT } from '../lib/logic.js';

function useLoad(fn) {
  const [r, setR] = useState(null);
  useEffect(() => { let a = true; fn().then((x) => a && setR(x)); return () => { a = false; }; }, []);
  return r;
}

const Chip = ({ v, children }) => <span className={`chip ${toneOf(v)}`}>{children || VERDICT_TEXT[v] || v}</span>;
const Loading = () => <div className="card pad" style={{ display: 'grid', gap: 12 }}><div className="skeleton" /><div className="skeleton" /></div>;
const Failed = ({ r }) => <p className="err">{r.error?.message} <span className="mono">({r.error?.code})</span></p>;

function DefenseCards({ cat, onPick, picked }) {
  const incidentsFor = (id) => cat.incidents.filter((i) => i.defenses.includes(id));
  return (
    <div className="def-grid">
      {cat.defenses.map((d, i) => (
        <article key={d.id} className="card pad def">
          <p className="eyebrow">Defense {i + 1}</p>
          <h3>{d.name}</h3>
          <p className="muted">{d.stops}</p>
          <ul className="ticks">{d.controls.map((c) => <li key={c}>{c}</li>)}</ul>
          <p className="small"><b>IBM MIA:</b> <span className="muted">{d.mia}</span></p>
          <p className="small"><b>Limits:</b> <span className="muted">{d.limits}</span></p>
          <div className="row" style={{ gap: 6 }}>
            {incidentsFor(d.id).map((x) => (
              <button key={x.id} type="button" className={`tag link ${picked === x.id ? 'on' : ''}`} onClick={() => onPick(x.id)}>{x.name}</button>
            ))}
          </div>
        </article>
      ))}
    </div>
  );
}

function Incident({ cat, id }) {
  const x = cat.incidents.find((i) => i.id === id);
  if (!x) return null;
  return (
    <div className="card pad callout-incident" aria-live="polite">
      <div className="row" style={{ justifyContent: 'space-between' }}>
        <b>{x.name}</b><span className="muted small">{x.org} · {x.date} · {x.product}</span>
      </div>
      <p>{x.summary}</p>
      <a href={x.url} target="_blank" rel="noreferrer noopener" className="small">Primary source</a>
    </div>
  );
}

function ScenarioSuite({ lab }) {
  const s = lab.scenario_suite;
  return (
    <>
      <div className="stats">
        <div className="stat"><span className="n tnum">{s.unprotected_unsafe_actions}</span><span className="k">unsafe actions would run without protection</span></div>
        <div className="stat"><span className="n tnum">{s.protected_unsafe_actions}</span><span className="k">unsafe actions with Model Mountain</span></div>
        <div className="stat"><span className="n tnum">{s.n}</span><span className="k">scenarios in the suite</span></div>
      </div>
      <div className="card table-wrap">
        <table>
          <thead><tr><th>Scenario</th><th>Without protection</th><th>With Model Mountain</th></tr></thead>
          <tbody>
            {s.cases.map((c) => (
              <tr key={c.scenario}>
                <td><b>{c.scenario.replace(/-/g, ' ')}</b><span className="sub">{c.category.replace(/_/g, ' ')}</span></td>
                <td>
                  {c.unprotected.unsafe_tool_would_run ? <Chip v="deny">Unsafe action: {c.unprotected.tool}</Chip>
                    : <Chip v={c.attacked ? 'monitor' : 'allow'}>{c.attacked ? 'Untrusted text reached model' : 'Answered'}</Chip>}
                </td>
                <td>
                  {c.protected.released ? <Chip v="allow">Answered</Chip> : <Chip v="deny">Withheld</Chip>}
                  {c.protected.rejected_docs.length > 0 && <span className="sub">Quarantined: {c.protected.rejected_docs.join(', ')}</span>}
                  {c.protected.markers.length > 0 && <span className="sub">Flagged: {c.protected.markers.join(', ')}</span>}
                  {c.protected.tool_decision && c.protected.tool_decision !== 'no_tool_requested' && <span className="sub">Tool: {c.protected.tool_decision.replace(/_/g, ' ')}</span>}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <p className="muted small">{s.note}</p>
    </>
  );
}

function EgressTester() {
  const [text, setText] = useState('Here are the onboarding steps: [wiki](https://wiki.acme.example/onboarding) ![chart](https://img.external.example/c.png)');
  const [out, setOut] = useState(null);
  const [tool, setTool] = useState({ tool: 'send_email', to: 'someone@external.example', bcc: '', body: 'Meeting notes', priv: true, untrusted: true, fromSearch: false });
  const [tout, setTout] = useState(null);
  const checkText = async (e) => { e.preventDefault(); setOut(await api.defenseCheck({ kind: 'egress_output', text })); };
  const checkTool = async (e) => {
    e.preventDefault();
    const args = tool.tool === 'send_email' ? { to: tool.to, ...(tool.bcc ? { bcc: tool.bcc } : {}), subject: 'Update', body: tool.body }
      : tool.tool === 'web_search' ? { query: tool.to }
      : tool.tool === 'http_get' || tool.tool === 'web_fetch' ? { url: tool.to } : { repo: tool.to, title: 'Update', body: tool.body };
    const known = tool.tool === 'web_fetch' && tool.fromSearch ? { known_urls: [tool.to] } : {};
    setTout(await api.defenseCheck({ kind: 'egress_tool', tool: tool.tool, args, private_data_read: tool.priv, untrusted_content_seen: tool.untrusted, ...known }));
  };
  return (
    <div className="split">
      <form className="card pad ask" onSubmit={checkText}>
        <h3 style={{ fontSize: 17 }}>Rendered-output check</h3>
        <p className="muted small">Paste an assistant answer. External images never auto-load, and links leave only for allowlisted domains (here <code>acme.example</code>).</p>
        <label htmlFor="eg-text" className="small muted">Assistant answer</label>
        <textarea id="eg-text" value={text} maxLength={4000} onChange={(e) => setText(e.target.value)} />
        <button className="btn primary" type="submit">Check output</button>
        {out && !out.ok && <Failed r={out} />}
        {out?.ok && (
          <div aria-live="polite" style={{ display: 'grid', gap: 8, justifyItems: 'start' }}>
            <Chip v={out.data.verdict} />
            <div className="answer mono small" style={{ justifySelf: 'stretch' }}>{out.data.released_text || 'Nothing released.'}</div>
            {out.data.findings.map((f, i) => <span key={i} className="sub">{f.kind}{f.url_host ? ` → ${f.url_host}` : ''}: {f.reasons.join(', ')}</span>)}
          </div>
        )}
      </form>
      <form className="card pad ask" onSubmit={checkTool}>
        <h3 style={{ fontSize: 17 }}>Tool-call check</h3>
        <p className="muted small">A proposed action is checked before anything runs. Nothing is ever sent from this page.</p>
        <label className="small muted" htmlFor="eg-tool">Tool</label>
        <select id="eg-tool" value={tool.tool} onChange={(e) => setTool({ ...tool, tool: e.target.value })}>
          <option value="send_email">send_email</option><option value="http_get">http_get</option><option value="create_pull_request">create_pull_request</option>
          <option value="web_fetch">web_fetch (search tool)</option><option value="web_search">web_search</option>
        </select>
        <label className="small muted" htmlFor="eg-to">{tool.tool === 'send_email' ? 'To' : tool.tool === 'web_search' ? 'Search query' : tool.tool === 'http_get' || tool.tool === 'web_fetch' ? 'URL' : 'Repository'}</label>
        <input id="eg-to" value={tool.to} maxLength={200} onChange={(e) => setTool({ ...tool, to: e.target.value })} />
        {tool.tool === 'send_email' && (<>
          <label className="small muted" htmlFor="eg-bcc">BCC (optional)</label>
          <input id="eg-bcc" value={tool.bcc} maxLength={200} onChange={(e) => setTool({ ...tool, bcc: e.target.value })} />
        </>)}
        {tool.tool === 'web_fetch' && <label className="check"><input type="checkbox" checked={tool.fromSearch} onChange={(e) => setTool({ ...tool, fromSearch: e.target.checked })} /> This URL came from search results (not built by the model)</label>}
        <label className="check"><input type="checkbox" checked={tool.priv} onChange={(e) => setTool({ ...tool, priv: e.target.checked })} /> Session has read private data</label>
        <label className="check"><input type="checkbox" checked={tool.untrusted} onChange={(e) => setTool({ ...tool, untrusted: e.target.checked })} /> Session has seen untrusted content</label>
        <button className="btn primary" type="submit">Check action</button>
        {tout && !tout.ok && <Failed r={tout} />}
        {tout?.ok && (
          <div aria-live="polite" style={{ display: 'grid', gap: 6, justifyItems: 'start' }}>
            <Chip v={tout.data.verdict} />
            {(tout.data.reasons || []).map((r) => <span key={r} className="sub mono">{r}</span>)}
          </div>
        )}
      </form>
    </div>
  );
}

const PAGE_EXAMPLE = '<article><h1>Valve suppliers 2026</h1><p>Our top picks for industrial valves.</p>\n<p style="color:#ffffff;background:#ffffff">[hidden placeholder: tells the agent to fetch an outside URL with a secret]</p></article>';

function PageScreen() {
  const [html, setHtml] = useState(PAGE_EXAMPLE);
  const [out, setOut] = useState(null);
  const check = async (e) => { e.preventDefault(); setOut(await api.defenseCheck({ kind: 'retrieved_page', text: html })); };
  return (
    <form className="card pad ask" onSubmit={check}>
      <h3 style={{ fontSize: 17 }}>Retrieved web page check</h3>
      <p className="muted small">In the web-search exfiltration study (Rall et al., arXiv 2510.09093) the instructions sat in white-on-white text that a person never sees. Pages from the search tool are screened for hidden text; only the visible text is passed on, as untrusted data.</p>
      <label htmlFor="pg-html" className="small muted">Page HTML</label>
      <textarea id="pg-html" value={html} maxLength={8000} onChange={(e) => setHtml(e.target.value)} />
      <button className="btn primary" type="submit">Screen page</button>
      {out && !out.ok && <Failed r={out} />}
      {out?.ok && (
        <div aria-live="polite" style={{ display: 'grid', gap: 6, justifyItems: 'start' }}>
          <Chip v={out.data.verdict} />
          {out.data.hidden_segments.map((h, i) => <span key={i} className="sub mono">hidden &lt;{h.tag}&gt; ({h.style}): {h.text}</span>)}
          <div className="answer small" style={{ justifySelf: 'stretch' }}>{out.data.visible_text || 'No visible text.'}</div>
        </div>
      )}
    </form>
  );
}

function EgressCases({ lab }) {
  return (
    <div className="card table-wrap">
      <table>
        <thead><tr><th>Fixture</th><th>Decision</th><th>Why</th></tr></thead>
        <tbody>
          {lab.egress.cases.map((c) => (
            <tr key={c.case}>
              <td><b>{c.case.replace(/_/g, ' ')}</b><span className="sub">{c.kind === 'output' ? 'rendered answer' : 'proposed tool call'}</span></td>
              <td><Chip v={c.verdict} /></td>
              <td className="small mono">{(c.reasons || (c.findings || []).flatMap((f) => f.reasons)).join(', ') || '—'}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function McpAndExtraction({ lab }) {
  const m = lab.mcp_supply_chain;
  const camp = lab.model_extraction.campaign;
  return (
    <div className="split">
      <div className="card pad" style={{ display: 'grid', gap: 10 }}>
        <h3 style={{ fontSize: 17 }}>MCP supply chain</h3>
        <p className="muted small">Signed manifests, pinned tool definitions and explicit update approval. {m.blocked} of {m.blocked + m.allowed} fixtures blocked.</p>
        <ul className="plain">
          {m.cases.map((c) => (
            <li key={c.case} className="row" style={{ justifyContent: 'space-between' }}>
              <span>{c.case.replace(/_/g, ' ')}</span>
              <Chip v={c.allowed ? 'allow' : 'deny'} />
            </li>
          ))}
        </ul>
      </div>
      <div className="card pad" style={{ display: 'grid', gap: 10 }}>
        <h3 style={{ fontSize: 17 }}>Model extraction</h3>
        <p className="muted small">{camp.note}</p>
        <div className="accounts" role="img" aria-label="Accounts admitted by per-account limits versus the campaign detector">
          {camp.rows.map((r) => (
            <div key={r.account} className={`acct ${r.campaign_allowed ? 'ok' : 'bad'}`} title={`${r.account}: ${r.campaign_allowed ? 'admitted' : 'blocked for review'}`} />
          ))}
        </div>
        <p className="small">Per-account limits blocked <b className="tnum">{camp.per_account_limits_blocked}</b> of {camp.rows.length}; the cross-account detector blocked <b className="tnum">{camp.campaign_detector_blocked}</b>. Unrelated request still allowed: <b>{camp.benign_unrelated_request_allowed ? 'yes' : 'no'}</b>.</p>
      </div>
    </div>
  );
}

function IncidentTable({ cat }) {
  const names = Object.fromEntries(cat.defenses.map((d) => [d.id, d.name]));
  return (
    <div className="card table-wrap">
      <table>
        <thead><tr><th>Documented incident</th><th>What happened</th><th>Answered by</th></tr></thead>
        <tbody>
          {cat.incidents.map((x) => (
            <tr key={x.id}>
              <td><a href={x.url} target="_blank" rel="noreferrer noopener"><b>{x.name}</b></a><span className="sub">{x.org} · {x.date}</span></td>
              <td className="small">{x.summary}</td>
              <td>{x.defenses.map((d) => <span key={d} className="tag" style={{ marginRight: 4 }}>{names[d]}</span>)}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

export default function Defenses() {
  const cat = useLoad(api.defenses);
  const lab = useLoad(api.defenseLab);
  const [picked, setPicked] = useState(null);
  return (
    <section className="view">
      <div className="head">
        <p className="eyebrow">Defenses</p>
        <h2>Five checks, each answering attacks that have happened to real assistants.</h2>
        <p className="lede">Every result on this page comes from the real rule engine running on CPU against inert fixtures. No model runs here and nothing is sent anywhere; real-model results are on the Steering and Results pages.</p>
      </div>
      {!cat ? <Loading /> : !cat.ok ? <Failed r={cat} /> : (<>
        <DefenseCards cat={cat.data} onPick={(id) => setPicked(picked === id ? null : id)} picked={picked} />
        {picked && <Incident cat={cat.data} id={picked} />}
      </>)}

      <div className="section-title"><h2>Scenario suite</h2><span className="muted small">Same inputs, with and without protection</span></div>
      {!lab ? <Loading /> : !lab.ok ? <Failed r={lab} /> : <ScenarioSuite lab={lab.data} />}

      <div className="section-title"><h2>Exfiltration guard</h2><span className="muted small">Rendered output and tool calls</span></div>
      <EgressTester />
      <PageScreen />
      {lab?.ok && <EgressCases lab={lab.data} />}

      <div className="section-title"><h2>Supply chain and extraction</h2><span className="muted small">MCP tools and model-copying traffic</span></div>
      {lab?.ok && <McpAndExtraction lab={lab.data} />}

      <div className="section-title"><h2>Incident catalog</h2><span className="muted small">Primary sources, summarized</span></div>
      {cat?.ok && <IncidentTable cat={cat.data} />}
    </section>
  );
}
