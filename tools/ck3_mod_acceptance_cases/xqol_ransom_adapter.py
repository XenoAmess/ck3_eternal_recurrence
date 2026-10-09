"""Original two actual AI self-payer ransom transactions; no callback replay."""
from . import xqol_followup_common as common

validate_contract=common.validate_contract
prepare_case=common.prepare_case
verify_case=common.verify_case


def run_case(context,client):
    result=common.run_plan(context,client)
    result['coverage_exclusions']=['nonself/shared-wallet','PAM rewards','whole selector/UI matrix']
    return common.preserve_result(context,client,result)
