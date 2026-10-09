"""Original five-step prison payment boundary/matrix cell only."""
from . import xqol_followup_common as common

validate_contract=common.validate_contract
prepare_case=common.prepare_case
verify_case=common.verify_case


def run_case(context,client):
    return common.preserve_result(context,client,common.run_plan(context,client))
