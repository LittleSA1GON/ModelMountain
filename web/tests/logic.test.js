import test from 'node:test';
import assert from 'node:assert/strict';
import { readdirSync, readFileSync, statSync } from 'node:fs';
import { join } from 'node:path';
import { fileURLToPath } from 'node:url';
import { verdictOf, stagesFor, boardColumns, summarizeRuns, capabilityState, cleanTitle, conditionRows, bestCondition, evidenceClass, pct } from '../src/lib/logic.js';

test('verdict mapping, including allow-with-abstention-text', () => {
  assert.equal(verdictOf({ decision: 'allow', answer: 'The limit is $500. [expense-policy]' }), 'allow');
  assert.equal(verdictOf({ decision: 'allow', answer: 'Insufficient verified evidence to answer this question.' }), 'abstain');
  assert.equal(verdictOf({ decision: 'deny' }), 'deny');
  assert.equal(verdictOf({ decision: 'abstain' }), 'abstain');
  assert.equal(verdictOf({ decision: 'unprotected_fixture' }), 'none');
  assert.equal(verdictOf(null), 'none');
});

test('pipeline stops at the stage named by the reason', () => {
  const s = stagesFor({ decision: 'deny', reasons: ['direct_prompt_injection_detected'] });
  assert.deepEqual(s.map((x) => x.state), ['pass', 'stop', 'skip', 'skip', 'skip']);
  assert.equal(s[1].reason, 'direct_prompt_injection_detected');
  const a = stagesFor({ decision: 'allow', answer: 'Insufficient verified evidence', reasons: [] });
  assert.deepEqual(a.map((x) => x.state), ['pass', 'pass', 'pass', 'hold', 'skip']);
  const ok = stagesFor({ decision: 'allow', answer: 'The limit is $500.', reasons: [] });
  assert.ok(ok.every((x) => x.state === 'pass'));
});

test('board hides review jobs and cancelled tasks, strips owner prefixes', () => {
  const cols = boardColumns([
    { id: 'MM-A', title: 'Codex: build api', status: 'completed' },
    { id: 'MM-B', title: 'Claude Code: secure it', status: 'in_progress' },
    { id: 'REV-1', title: 'review', status: 'todo' },
    { id: 'MM-C', title: 'x', status: 'cancelled' },
    { id: 'MM-D', title: 'Antigravity: ui', status: 'blocked' },
  ]);
  assert.equal(cols.done[0].title, 'Build api');
  assert.equal(cols.doing[0].title, 'Secure it');
  assert.equal(cols.todo.length, 1);
  assert.equal(cols.todo[0].blocked, true);
  assert.equal(cleanTitle('Claude: Kaggle runtime'), 'Kaggle runtime');
});

test('run summary and capability states', () => {
  const s = summarizeRuns([{ decision: 'allow', latency_ms: 3 }, { decision: 'deny', latency_ms: 1 }, { decision: 'unprotected_fixture', latency_ms: 2 }]);
  assert.deepEqual([s.total, s.allow, s.deny, s.baseline, s.p50], [3, 1, 1, 1, 2]);
  assert.equal(summarizeRuns([]).p50, null);
  assert.equal(capabilityState('unverified'), 'unverified');
  assert.equal(capabilityState({ available: true }), 'available');
  assert.equal(capabilityState('unsupported'), 'unavailable');
});

test('no hardcoded percentages or metric literals in UI source', () => {
  const walk = (d) => readdirSync(d).flatMap((f) => { const p = join(d, f); return statSync(p).isDirectory() ? walk(p) : [p]; });
  for (const file of walk(fileURLToPath(new URL('../src', import.meta.url)))) {
    if (!/\.(jsx?|css)$/.test(file) || file.endsWith('.css')) continue;
    const src = readFileSync(file, 'utf8');
    assert.doesNotMatch(src, /\b\d{1,3}\.\d+\s*%/, `hardcoded percentage in ${file}`);
    assert.doesNotMatch(src, /\bAUROC\s*[:=]\s*0?\.\d/i, `hardcoded AUROC in ${file}`);
  }
});

test('evidence classes keep diagnostics and fixtures out of real results', () => {
  assert.equal(evidenceClass('REAL_IBM_MIA'), 'real');
  assert.equal(evidenceClass('CPU_SYNTHETIC'), 'synthetic');
  assert.equal(evidenceClass('STATIC_ESTIMATE_ON_ACTUAL_GPU'), 'diagnostic');
  assert.equal(evidenceClass('HARDWARE_PREFLIGHT_ONLY'), 'diagnostic');
  assert.equal(evidenceClass('REAL_LOOKING_BUT_UNKNOWN'), 'other');
});

test('protection rows are ordered and the best condition respects utility', () => {
  const p = { conditions: {
    D_monitor: { label: 'Monitor', attack_success: { rate: 0.1, ci95: [0.05, 0.2] }, utility: { rate: 0.5 } },
    A_bare: { label: 'None', attack_success: { rate: 0.6 }, utility: { rate: 0.9 } },
    B_spotlight: { label: 'Spot', attack_success: { rate: 0.3 }, utility: { rate: 0.88 } },
    C_calm_steer: { status: 'skipped', reason: 'no strength' },
  } };
  const rows = conditionRows(p);
  assert.deepEqual(rows.map((r) => r.id), ['A_bare', 'B_spotlight', 'C_calm_steer', 'D_monitor']);
  assert.equal(rows[2].skipped, true);
  assert.equal(bestCondition(rows).id, 'B_spotlight');   // D blocks too many real users
  assert.equal(pct(0.256), '26%');
  assert.equal(pct(null), '—');
});

test('trace rows map measured gateway stages', async () => {
  const { traceRows } = await import('../src/lib/logic.js');
  assert.equal(traceRows(undefined), null);
  const rows = traceRows([{ stage: 'identity', verdict: 'pass' }, { stage: 'egress_output', verdict: 'sanitized' },
    { stage: 'tool_egress', verdict: 'deny', reasons: ['non_allowlisted_destination:to'] }]);
  assert.deepEqual(rows.map((r) => r.state), ['pass', 'hold', 'stop']);
  assert.equal(rows[2].reason, 'non_allowlisted_destination:to');
});

test('verdict tones, strength snapping and rate formatting', async () => {
  const { toneOf, snapStrength, fmtRate } = await import('../src/lib/logic.js');
  assert.equal(toneOf('deny'), 'bad');
  assert.equal(toneOf('require_human_approval'), 'warn');
  assert.equal(toneOf('allow'), 'ok');
  assert.equal(snapStrength(0.123), 0.1);
  assert.equal(snapStrength(9), 0.5);
  assert.equal(snapStrength(-0.07), -0.05);
  assert.equal(fmtRate(null), 'not measured');
  assert.equal(fmtRate({ rate: 0.25, n: 40, ci95: [0.14, 0.4] }), '25% of 40 (95% CI 14%–40%)');
});
