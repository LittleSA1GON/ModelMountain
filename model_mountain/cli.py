"""Run a self-contained synthetic smoke test or replay genuine MIA evidence."""
import argparse
import csv
import html
import json
from pathlib import Path
from .core import builtin_scenarios, export_json, suite_report
from .mcp_security import synthetic_mcp_suite
from .extraction import synthetic_extraction_suite
from .risk_catalog import RISKS, RISK_ASSUMPTIONS


def render_html(report):
    rows = []
    for r in report['records']:
        denied = ', '.join(d['id'] for d in r['documents'] if not d['allowed_to_context']) or 'none'
        data = [r['scenario'], r['mode'], r['model_engine'], denied,
                'yes' if r['response_released'] else 'no',
                r['policy']['tool'], 'yes' if r['policy']['would_allow'] else 'no',
                'none' if r['mia_score'] is None else str(round(r['mia_score'], 5))]
        rows.append('<tr>' + ''.join('<td>' + html.escape(str(x)) + '</td>' for x in data) + '</tr>')
    return '''<!doctype html><html lang="en"><meta charset="UTF-8">
<title>Model Mountain security results</title><style>
body{background:#101827;color:#ebeff5;font:15px system-ui;margin:30px auto;max-width:1200px;padding:0 20px}
article{background:#1a2739;border:1px solid #34465f;padding:24px;border-radius:15px}
h1{color:#80c9fa}table{border-collapse:collapse;width:100%;font-size:13px}
th,td{padding:10px;text-align:left;border-bottom:1px solid #435269}
th{color:#94d2f7}.note{color:#bacadc}.scroller{overflow:auto}</style>
<article><h1>Model Mountain Security</h1><p>Prompt injection | Retrieval security | Agent authorization | MCP trust / updates | Model extraction monitoring</p>
<p class="note">Run origin: ''' + html.escape(report['engine']) + '''. 
Simulated model outputs are NOT IBM MIA evidence. Tools never execute outside a simulator.</p>
<p>''' + str(report['totals']['cases']) + ''' scenarios | ''' + str(report['totals']['attacks']) + ''' labeled adversarial cases | ''' + str(report['totals']['protected_unauthorized_actions']) + ''' protected unauthorized simulated actions</p>
<div class="scroller"><table><thead><tr><th>Scenario</th><th>Mode</th><th>Engine</th>
<th>Rejected documents</th><th>Response released</th><th>Tool</th><th>Would allow</th><th>MIA score</th></tr></thead><tbody>''' + '\n'.join(rows) + '''</tbody></table></div></article></html>'''


def main():
    ap = argparse.ArgumentParser(description="Synthetic Model Mountain assessment and MIA evidence replay")
    ap.add_argument('--evidence', help='Path to real MIA worker output JSON (requires status PASS)')
    ap.add_argument('--output', default='model_mountain_results')
    ap.add_argument('--threshold', type=float, help='Optional manually calibrated MIA score threshold; high score=attack assumed. No automatic calibration.')
    args = ap.parse_args()
    external = None
    if args.evidence:
        source = json.loads(Path(args.evidence).read_text())
        if source.get('status') != 'PASS' or source.get('analyzer') != 'attn_tracker' or not isinstance(source.get('results'), dict):
            raise ValueError('Evidence must be a real completed IBM MIA Attention Tracker run with status PASS')
        required = {c.name + ':' + mode for c in builtin_scenarios() for mode in ('unprotected','protected')}
        if not required.issubset(source['results']):
            raise ValueError('Incomplete MIA evidence; missing keys: ' + ', '.join(sorted(required-set(source['results']))))
        for key, obj in source['results'].items():
            if obj.get('engine') != 'REAL_IBM_MIA_vllm' or not isinstance(obj.get('mia_score'), (int, float)):
                raise ValueError('Invalid model evidence for ' + key)
        external = source['results']
    report = suite_report(external, args.threshold)
    folder = Path(args.output)
    folder.mkdir(parents=True, exist_ok=True)
    export_json(str(folder/'report.json'), report)
    mcp_report = synthetic_mcp_suite()
    (folder/'mcp_report.json').write_text(json.dumps(mcp_report, indent=2),encoding='utf-8')
    extraction_report = synthetic_extraction_suite()
    (folder/'extraction_report.json').write_text(json.dumps(extraction_report, indent=2),encoding='utf-8')
    (folder/'risk_priorities.json').write_text(json.dumps({'assumptions': RISK_ASSUMPTIONS, 'risks': RISKS}, indent=2),encoding='utf-8')
    combined_html = render_html(report)
    mcp_table = ''.join('<tr><td>'+html.escape(r['scenario'])+'</td><td>'+('ALLOWED' if r['allowed'] else 'BLOCKED')+'</td><td>'+html.escape(', '.join(r['issues']) or 'no issues')+'</td></tr>' for r in mcp_report['results'])
    mcp_section = '<article><h2>MCP security: certificate, updates, identity and authorization</h2><p class="note">SYNTHETIC FIXTURES ONLY — no live TLS handshake, OAuth login, or MCP server executed.</p><div class="scroller"><table><thead><tr><th>Scenario</th><th>Decision</th><th>Reasons</th></tr></thead><tbody>' + mcp_table + '</tbody></table></div></article>'
    extraction_rows = ''.join('<tr><td>'+html.escape(r['scenario'])+'</td><td>'+html.escape(r['decision'].upper())+'</td><td>'+html.escape(', '.join(r['issues']+r['alerts']) or 'none')+'</td></tr>' for r in extraction_report['results'])
    extraction_section = '<article><h2>Model extraction and distillation-abuse monitoring</h2><p class="note">SYNTHETIC REQUEST-ADMISSION TESTS ONLY. Rate limits and repeated training-pattern monitoring are external security controls, not an IBM MIA detector.</p><div class="scroller"><table><thead><tr><th>Scenario</th><th>Decision</th><th>Reasons / alerts</th></tr></thead><tbody>' + extraction_rows + '</tbody></table></div></article>'
    risk_rows = ''.join('<tr><td>'+str(x['priority'])+'</td><td>'+html.escape(x['risk'])+'</td><td>'+html.escape(x['severity'])+'</td><td>'+html.escape(x['protection'])+'</td><td>'+html.escape(x['mia_role'])+'</td></tr>' for x in RISKS)
    risk_section = '<article><h2>Enterprise threat severity (illustrative)</h2><p class="note">'+html.escape(RISK_ASSUMPTIONS)+'</p><div class="scroller"><table><thead><tr><th>Rank</th><th>Threat</th><th>Severity</th><th>Protection</th><th>MIA role</th></tr></thead><tbody>'+risk_rows+'</tbody></table></div></article>'
    combined_html = combined_html.replace('</body>','').replace('</html>',risk_section+mcp_section+extraction_section+'</html>')
    (folder/'report.html').write_text(combined_html, encoding='utf-8')
    with (folder/'results.csv').open('w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=['scenario','category','mode','model_engine','mia_score',
                                                'response_released','unsafe_tool_proposed','unauthorized_action_would_execute'])
        writer.writeheader()
        writer.writerows({k:r.get(k) for k in writer.fieldnames} for r in report['records'])
    print(json.dumps(report['totals'], indent=2))
    print('Evidence type:', report['engine'])
    print('MCP security simulation:', mcp_report['cases'], 'cases /', mcp_report['blocked'], 'blocked')
    print('Extraction monitoring simulation:', extraction_report['cases'], 'cases /', extraction_report['blocked'], 'blocked')
    print('Wrote:', folder.resolve())

if __name__ == '__main__':
    main()
