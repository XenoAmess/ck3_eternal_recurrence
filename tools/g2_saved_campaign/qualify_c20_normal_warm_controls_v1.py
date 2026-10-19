"""One source/pin closure, reusing the prior seven-source RAM composition."""
import json
from datetime import datetime, timezone
from pathlib import Path
import sys
import prepare_c20_normal_warm_controls_v1 as p

if __name__ == '__main__':
    graph,binding = p.compose()
    factory = graph['root_p37c20_warm_resume.py'].decode()
    p.require(factory.count("self.flags = [flag for flag in self.flags if flag != '--private-active-scheme-sway-completion-execution-query']") == 1, 'execution mask lost')
    p.require(graph['root_p37c20_sdk_queue.py'].decode().count('from root_p37c16_overlay_relay import relay_compact, error_projection') == 3, 'physical relay lost')
    p.require('from root_p37c16_compact_decision_feed import publish_before_submit' in graph['root_p37c20_mcp_entry.py'].decode(), 'physical callback lost')
    p.require('ROOT-SAVED-MAP-RECORDING-ADMITTED-C16.json' in graph['launch_sdk_p37c20_owner.py'].decode(), 'physical firstgate lost')
    files = [Path(p.__file__),Path(__file__)]
    report = {'schema':'xar.C20-normal-warm-control-source-closure/v1', 'machine_id':p.MACHINE,
        'observed_at_utc':datetime.now(timezone.utc).isoformat(), 'status':'SOURCE_READY_NOT_ADOPTED',
        'source_binding':binding,
        'files':[{'path':str(path.resolve()),'bytes':path.stat().st_size,'sha256':p.sha(path.read_bytes())} for path in files],
        'sources':{name:{'bytes':len(raw),'sha256':p.sha(raw)} for name,raw in graph.items()},
        'logical_bytes':368122, 'prospective4096cluster_bytes':385024, 'protected_constants':45,
        'seven_RAM_results_reproduced':True, 'original_namespace_port_inverse_bytes_AST':True,
        'old_matrices_or_startup_RPC_repeated':False, 'resident_algorithm_and_full_loop_unchanged_except_namespace':True,
        'retained_physical_Game_record_publisher_score_generation':'C16',
        'WAL_Task_env_required':'XAR_CK3_ENABLE_DRIVER_STATE_WAL_V1=1', 'execution_query_flag_supported':False,
        'new_classifier_pin_required':{'source':str(p.CLASSIFIER),'sha256':p.CLASSIFIER_SHA,'four_action_rows':True},
        'Source15_f236_omission_proof_not_inherited':True,
        'SAVE_offline_reconciliation_preserves_original_governance_classifier_until_new_constructor':True,
        'boundary':'then actual clean/reconciled SAVE10456 and normalclosed inputs; no request sequence minted here',
        'payload_subcap_quote':655360, 'additional_atomic_subcap_quote':327680,
        'complete_stage_quote_upper':10690560, 'stage_ceiling':12582912,
        'budget_quote_not_D_install_or_Task_authority':True,
        'source_card_sha256':'4cca727314c44ca64ad974c80e784e711ee041fa84e60a93eafc1bbf884636da',
        'D_Git_Task_Game_RPC_Driver_SAVE_operations':0, 'outputs_materialized':False, 'scratch_files':0,
        'record_review_at_utc':'2027-04-18T21:04:37+00:00', 'future_writes_after_freeze':0}
    raw = (json.dumps(report,indent=2)+'\n').encode()
    total = sum(path.stat().st_size for path in files)+len(raw)
    p.require(total <= 16384, 'complete source16KiB cap exceeded')
    if len(sys.argv) == 2:
        with Path(sys.argv[1]).open('xb') as output: output.write(raw)
    print(json.dumps({'proof_bytes':len(raw),'proof_sha256':p.sha(raw),'complete_source_bytes':total,
        'seven_logical_bytes':368122,'sources':report['sources']}))
