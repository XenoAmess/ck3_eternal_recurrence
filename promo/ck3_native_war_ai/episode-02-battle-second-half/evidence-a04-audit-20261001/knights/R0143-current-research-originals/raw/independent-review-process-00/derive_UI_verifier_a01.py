from pathlib import Path
source=Path('C:/Users/1/ck3-a04-mechanism-evidence-20261001/R0142-permanent-archive-other-a01/verify_R0142_UI_a01.py')
target=Path(__file__).parent/'verify_R0143_UI_a01.py'
text=source.read_text(encoding='utf-8')
for old,new in [('R0142','R0143'),('root-attempt-06-hidden-modal-ui','root-attempt-07-trace-diagnostic'),('episode02-e2-05-d26-six-gap-ui-live-20261001-a06','episode02-e2-05-d26-six-gap-trace-live-20261001-a07'),('1790851314.6089177','1790857417.4866428'),('984144','2491964'),('4ad477ee33e15a93e412f711c7b05b216a2e6651','419cac1a956c7be356d886256c7bc689cda5327d'),('3461','3490')]:
 if old not in text:raise ValueError('missing exact old token '+old)
 text=text.replace(old,new)
old="    require(day['day_advance_count'] == 1 and day['day_postcondition_verified'] is True and day['one_day_retry_performed'] is False and day['trace_export_status'] == 'RED_MANAGED_DTO_UNAVAILABLE' and day['complete_causal_chain'] is False, 'one real day, truthful daily trace RED without retry')"
new="""    actual_day = receipt_body(day['one_day'])
    require(actual_day == day['one_day_body'] and actual_day['requested_horizon_days'] == 1 and actual_day['elapsed_days'] == 1 and actual_day['paused'] is True and actual_day['starting_date_raw'] == B['before_date_raw'] and actual_day['ending_date_raw'] == B['after_date_raw'], 'one actual requested horizon day and exact paused endpoint')
    require(day['day_postcondition_verified'] is True and day['trace_retry_or_extra_day'] is False and day['trace_finish_body'] is None and day['complete_causal_chain'] is False and day['trace_finish']['result'] == 'RED', 'one real day, truthful trace RED without retry')
    verify_ref(day['trace_finish']['request']); verify_ref(day['trace_finish']['response'])
    stop_original = load(ROOT / 'actual-stopped-run-summary-a01.json')
    verify_ref(stop_original['actual_native_diagnostic'])
    native_diagnostic = load(stop_original['actual_native_diagnostic']['path'])
    d = native_diagnostic['original_parsed_command_result']['trace_publish_diagnostic']
    require(d['failure_gate'] == 'managed_wire_cap' and d['assembled_output_bytes'] == 1217950 and d['managed_cap_bytes'] == 921600 and d['drain_failure_flags'] == d['scoped_failure_flags'] == 0 and d['drain_record_count'] == 7 and d['scoped_record_count'] == 184 and d['detours_uninstalled'] is True, 'actual typed managed cap diagnostic, valid fragments do not equal export')
    day['independent_trace_status'] = 'RED_MANAGED_WIRE_CAP'
"""
if text.count(old)!=1:raise ValueError('exact original day predicate missing')
text=text.replace(old,new)
text=text.replace("'Before terrain tooltip lies above panel; after battle panel has no tooltip occlusion.'", "'Both before and after battle panel have no overlapping tooltip.'")
text=text.replace("Before terrain tooltip lies above panel; after battle panel has no tooltip occlusion.","Both before and after battle panel have no overlapping tooltip.")
text=text.replace("'native_hover_provider': 'RED_STOCK_DERIVED_TEXTBOX_RTTI_REJECTED_NOT_DISPATCHED; actual list pixels obtained through individually bound coordinate-map fallback'", "'native_hover_provider': 'UNCHANGED_SOURCE_BOUND_R0142_DERIVED_RTTI_LIMITATION; no new R0143 hover rejection fabricated; actual list pixels from individually bound coordinate-map fallback'")
text=text.replace("'optional_eligible_military_list': 'RED_DEFAULT_PLAYER_OWNER_UNVERIFIED; never substituted for active combat list'", "'optional_eligible_military_list': 'NOT_NEEDED_FOR_CURRENT_ACTIVE_COMBAT_UI; prior R0142 eligible owner RED never substituted for current combat list'")
text=text.replace("'daily_trace_status': day['trace_export_status']", "'daily_trace_status': day['independent_trace_status'], 'original_typed_trace_diagnostic': stop_original['actual_native_diagnostic'], 'typed_diagnostic_fields': d, 'consumer_finish_delay': 'Wrong requested_days field versus actual requested_horizon_days aborted immediate controller after real +24; unique fresh finish continuation, no second day or retry'")
with target.open('x',encoding='utf-8',newline='\n') as f:f.write(text)
print(target)
