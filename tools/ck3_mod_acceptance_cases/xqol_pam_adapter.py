"""Original positive/negative natural PAM observations, with common read opt-ins."""
from . import xqol_followup_common as common

TOOLS=['ck3_query_player_religion_context_v1','ck3_query_player_religion_personal_parameters_v1']
verify_case=common.verify_case


def validate_contract(context):
    common.validate_contract(context)
    common.require(context['case_spec'].get('opt_in_read_only_mcp_tools')==TOOLS and
                   all(tool in context['case_spec']['required_mcp_tools'] for tool in TOOLS),
                   'Both original PAM read-only tools must be declared through the one shared host')


def prepare_case(context):
    validate_contract(context)
    return common.prepare_case(context)


def run_case(context,client):
    validate_contract(context)
    result=common.run_plan(context,client)
    result['remaining_resource_causality_gap']='Cross-day public legitimacy totals do not prove the synchronous stock callback delta'
    result['natural_dispatch_callback_and_rewards_unmodified']=True
    result['coverage_exclusions']=['bulk selector50/slider','all reward families','nonself ransom']
    return common.preserve_result(context,client,result)
