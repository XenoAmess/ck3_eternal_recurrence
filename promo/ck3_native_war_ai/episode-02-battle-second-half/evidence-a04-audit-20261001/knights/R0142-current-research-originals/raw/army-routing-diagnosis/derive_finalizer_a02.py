from pathlib import Path
p=Path(__file__).parent
raw=(p/'finalize_routing_review_a01.py').read_text('utf-8')
raw=raw.replace("'exact/current-routing-query'", "'exact/current-routing-query-a02'").replace("'exact/native-routing-query-return'", "'exact/native-routing-query-return-a02'")
raw=raw.replace("cutoff = route_envelope['at']", "target_raw_sha = body['native_ui_raw_return_receipt']['sha256']\nmatched_target_query = False")
raw=raw.replace("        if timestamp and timestamp > cutoff:\n            break\n", "")
needle="                          'body_fields': {k: result_body[k] for k in fields if isinstance(result_body, dict) and k in result_body}})"
assert needle in raw
raw=raw.replace(needle, needle+"\n        current_body = value.get('body') or {}\n        if isinstance(current_body, dict) and current_body.get('native_ui_raw_return_receipt', {}).get('sha256') == target_raw_sha:\n            matched_target_query = True\n            break")
raw=raw.replace("prefix_path = OUT / 'mcp-calls-bounded-prefix-through-routing-query-a01.jsonl'", "assert matched_target_query, 'Exact original native query return must identify MCP cutoff'\nprefix_path = OUT / 'mcp-calls-bounded-prefix-through-routing-query-a02.jsonl'")
raw=raw.replace("report_path = OUT / 'routing-review-final-a01.json'", "result['prior_finalizer_failure_preserved'] = {'script': identity(OUT/'finalize_routing_review_a01.py'), 'reason': 'Incorrect envelope-at cutoff excluded original MCP query; a01 assertion failed before report. a02 cuts exact raw-return SHA instead.', 'old_prefix': identity(OUT/'mcp-calls-bounded-prefix-through-routing-query-a01.jsonl')}\nreport_path = OUT / 'routing-review-final-a02.json'")
raw=raw.replace("receipt_path = OUT / 'routing-review-final-receipt-a01.json'", "receipt_path = OUT / 'routing-review-final-receipt-a02.json'")
with (p/'finalize_routing_review_a02.py').open('x',encoding='utf-8',newline='\n') as f:f.write(raw)
