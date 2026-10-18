"""Portable source-valued V5 planning corrections; no game/file lookup at runtime."""
from __future__ import annotations
from copy import deepcopy

from .holy_site_v5_adoption_knowledge import CROSS_RELIGION_ADOPTION
from .holy_site_v5_relic_knowledge import RELIC_AI_AND_CB, LAST_FAITH_RETURN, OPINION_ROLES
from .holy_site_v5_building_knowledge import SPECIAL_BUILDINGS

V5_SOURCE_PAYLOADS = {'adoption': {'artifact_relative_name': 'adoption/cross-religion-adoption.knowledge-portable-a01.json',
              'sha256': 'd0ba1e5b51c8587e461d33199c2d96bfd5ca5e7f79bee72edc398eda65f9a950',
              'repository_document': 'docs/ck3-native-ai/holy-site-cross-religion-adoption-12004.md'},
 'relic_ai': {'artifact_relative_name': 'relic-ai/planning-clarification.relic-ai-v5.json',
              'sha256': '0063f8b4ead670b02bf1b17dd5d8683bdb6a7d43bb3cf67d1d7ce467644f2d7b',
              'repository_document': 'docs/ck3-native-ai/holy-site-relic-ai-cleanup-conditions12004-v5.md'},
 'return': {'artifact_relative_name': 'return/return-condition-contract-a01.json',
            'sha256': '534ef365d27af31e50c67fc4625130119a93f065dbaf61863edbabec9b941598',
            'repository_document': 'docs/ck3-native-ai/holy-site-abandon-relic-recipient12004-v5.md'},
 'buildings': {'artifact_relative_name': 'buildings/portable-knowledge.json',
               'sha256': '3ad92c08ecaf06a205d38f5aa801b2d79191182eec28b59b6722ba757ba9927b',
               'repository_document': 'docs/ck3-native-ai/special-building-religion-holy-site-gates12004.md'},
 'opinion': {'artifact_relative_name': 'opinion/opinion-branches-v5.md',
             'sha256': '809fdc27b5b60f5c1e4d140dd19189e2a2cd79279dd203231ac884d7bbfd641a',
             'repository_document': 'docs/ck3-native-ai/holy-site-relic-opinion-conditions12004-v5.md'}}

REFORM_MCP_SCOPE = {
    "source_inventory_build":"1.20.0.4",
    "existing_readers":["player_religion_context","player_religion_doctrines and boolean_parameters",
        "player_religion_tenets current/main/personal/effective", "player_religion_hostility four directions",
        "already-open reform draft, complete choices, price and final native Can"],
    "current_published_write_gap":"At source baseline fa0d46eec95064a2a25fb2af74abc9bcc5f4bd36, public MCP has no reform draft open/select/name/create-write route. A dedicated exact4 candidate is being prepared; not built or live-qualified by this knowledge.",
    "paid_conversion_write":"Existing paid conversion action frame accepts CK3_12003 only; it is not an exact4 creation substitute.",
    "adoption_after_reform":"Existing exact4 typed adoption open/detail/confirm and independent site/Faith/owner/resource reads are reusable only after actual normal Can and fresh identity are observed.",
    "both_directions_new_live_examples":False,
    "source_and_runtime_distinct":True,
    "retained_build_configuration": {
        "observation_kind":"retained CMake cache metadata, not current running capability observation",
        "machine_id":"4-8e1c2f1861",
        "observed_at_utc":"2026-10-18T06:20:55.850653+00:00",
        "source_artifact_relative_name":"root/runtime-plan/ACTUAL-READINESS-a01.json",
        "cache_sha256":"5d938a51e735bc9db879d113054fa4f6d3869abc22e1899858425321175e78d2",
        "readiness_receipt_sha256":"3f7190116c9a92b9e0e301921464e278a5c1fc378266599f89f63239cd85d36d",
        "off":["REFORM_CONTEXT_PRIVATE_QUERY_V1", "DRAFT_GROUPS_PRIVATE_QUERY_V1",
            "DRAFT_TENET_CHOICES_PRIVATE_QUERY_V1", "DRAFT_DOCTRINE_CHOICES_PRIVATE_QUERY_V1",
            "DRAFT_RESOURCE_COSTS_PRIVATE_QUERY_V1", "AI_REFORM_INPUTS", "DOCTRINE_CATALOGUE",
            "DOCTRINE_KNOWLEDGE", "HOSTILITY", "RELIGION_CONVERSION"],
        "qualification":"old a07 binary qualification is source-bound to e23; no current fa0d/new-writer build or live credit",
    },
}


def holy_site_v5_clarifications(action: str) -> dict[str, object]:
    result = {"schema":"xar.ck3.holy-site-v5-clarifications.v1","ck3_build":"1.20.0.4",
        "qualification":"source_reviewed_static","state_observed":False,
        "native_legality":None,"action_ready":False,"runtime_file_access_required":False,
        "source_payloads":deepcopy(V5_SOURCE_PAYLOADS)}
    if action == "adopt":
        result.update(cross_religion_adoption=deepcopy(CROSS_RELIGION_ADOPTION),
            reform_mcp_scope=deepcopy(REFORM_MCP_SCOPE),special_buildings=deepcopy(SPECIAL_BUILDINGS))
    if action == "create":
        result["special_buildings"] = deepcopy(SPECIAL_BUILDINGS)
    if action in ("enshrine_relic","remove_relic"):
        result.update(relic_ai_and_cb=deepcopy(RELIC_AI_AND_CB),opinion_roles=deepcopy(OPINION_ROLES))
    if action == "abandon":
        result["last_faith_return"] = deepcopy(LAST_FAITH_RETURN)
    return result
