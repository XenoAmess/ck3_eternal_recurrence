"""Pure shared selected-decision wire contracts; no driver, game or file I/O."""
from __future__ import annotations

from collections.abc import Mapping
from typing import Literal, NotRequired, TypeGuard, TypedDict


class StockDefaultParameterV1(TypedDict):
    token_source: Literal["stock_detail_default_token_slot_0x5D4C0D8"]
    canonical_token: int
    key: int
    scope_kind: Literal[4]
    scope_flags: Literal[0]
    scope_payload: Literal[0xFFFFFFFF]
    no_custom_controller: Literal[True]


class EmptyParameterContextV1(TypedDict):
    context_adapter: Literal["actual_empty_named_parameters_only"]
    named_parameter_count: Literal[0]
    stock_default_parameter: NotRequired[None]


class StockParameterContextV1(TypedDict):
    context_adapter: Literal["actual_create_hof_stock_default_parameter_only"]
    named_parameter_count: Literal[1]
    stock_default_parameter: StockDefaultParameterV1


class SelectedResourceQuoteV1(TypedDict):
    raw_scale: Literal[100000]
    resource_vector_raw: list[int]
    native_affordable: bool


class _HofTermsFieldsV1(TypedDict):
    schema: Literal["ck3-selected-decision-terms-v1"]
    available: Literal[True]
    decision_key: Literal["create_hof_decision"]
    played_character_id: int
    date_raw: int
    read_only: Literal[True]
    action_ready: Literal[False]
    decision_confirm_invoked: Literal[False]
    context_verified: Literal[True]
    requirements_bypass_observed: Literal[True]
    requirements_bypass_raw: Literal[0]
    ordinary_legality_observed: Literal[True]
    ordinary_can_confirm: Literal[True]
    can_confirm: Literal[True]
    requirements_description_available: Literal[True]
    cost_description_available: Literal[True]
    requirements_description: str
    cost_description: str
    resource_quote_available: Literal[True]
    resource_quote: SelectedResourceQuoteV1


class EmptyHofQuoteTermsV1(_HofTermsFieldsV1, EmptyParameterContextV1):
    pass


class StockHofQuoteTermsV1(_HofTermsFieldsV1, StockParameterContextV1):
    pass


HofQuoteTermsV1 = EmptyHofQuoteTermsV1 | StockHofQuoteTermsV1


class FilePinV1(TypedDict):
    path: str
    bytes: int
    sha256: str


class HofQuoteClaimV1(TypedDict):
    schema: Literal["faith-e02-R19-hof-once-claim-v1"]
    decision_key: Literal["create_hof_decision"]
    actor: int
    date_raw: int
    quote_receipts: list[FilePinV1]


def require(value: object, message: str) -> None:
    if not value:
        raise ValueError(message)


def is_json_object(value: object) -> TypeGuard[dict[str, object]]:
    return isinstance(value, dict) and all(isinstance(key, str) for key in value)


def json_object(value: object, message: str) -> dict[str, object]:
    if not is_json_object(value):
        raise ValueError(message)
    return value


def is_json_array(value: object) -> TypeGuard[list[object]]:
    return isinstance(value, list)


def json_array(value: object, message: str) -> list[object]:
    if not is_json_array(value):
        raise ValueError(message)
    return value


def strict_integer(value: object, message: str) -> int:
    if type(value) is not int:
        raise ValueError(message)
    return value


def _same_integer(value: object, expected: int) -> bool:
    return type(value) is int and value == expected


def _stock_parameter(value: object) -> TypeGuard[StockDefaultParameterV1]:
    if not is_json_object(value) or set(value) != {
        "token_source", "canonical_token", "key", "scope_kind", "scope_flags",
        "scope_payload", "no_custom_controller",
    }:
        return False
    token = value["canonical_token"]
    return (value["token_source"] == "stock_detail_default_token_slot_0x5D4C0D8"
        and type(token) is int and 0 <= token <= 0xFFFFFFFF
        and _same_integer(value["key"], token)
        and _same_integer(value["scope_kind"], 4)
        and _same_integer(value["scope_flags"], 0)
        and _same_integer(value["scope_payload"], 0xFFFFFFFF)
        and value["no_custom_controller"] is True)


def selected_parameter_context_verified_v1(
    value: Mapping[str, object], requested_key: str,
) -> bool:
    """Wire identity only; preserve empty missing/null and native fixed scope."""
    count = value.get("named_parameter_count")
    if type(count) is not int:
        return False
    parameter = value.get("stock_default_parameter")
    if value.get("context_adapter") == "actual_empty_named_parameters_only":
        return count == 0 and parameter is None
    return (value.get("context_adapter") == "actual_create_hof_stock_default_parameter_only"
        and requested_key == "create_hof_decision" and count == 1
        and _stock_parameter(parameter))


def is_selected_resource_quote_v1(value: object) -> TypeGuard[SelectedResourceQuoteV1]:
    if not is_json_object(value) or set(value) != {
        "raw_scale", "resource_vector_raw", "native_affordable",
    }:
        return False
    vector = value["resource_vector_raw"]
    return (_same_integer(value["raw_scale"], 100000)
        and type(value["native_affordable"]) is bool and is_json_array(vector)
        and len(vector) == 10
        and all(type(n) is int and -(1 << 63) <= n < (1 << 63) for n in vector))


def _qualified_hof_terms(
    value: object, actor: int, date_raw: int,
) -> TypeGuard[HofQuoteTermsV1]:
    terms = json_object(value, "HoF actual selected qualified parameter terms unavailable")
    require(terms.get("available") is True
        and terms.get("schema") == "ck3-selected-decision-terms-v1"
        and terms.get("decision_key") == "create_hof_decision"
        and _same_integer(terms.get("played_character_id"), actor)
        and _same_integer(terms.get("date_raw"), date_raw)
        and terms.get("read_only") is True and terms.get("action_ready") is False
        and terms.get("decision_confirm_invoked") is False
        and terms.get("context_verified") is True
        and selected_parameter_context_verified_v1(terms, "create_hof_decision"),
        "HoF actual selected qualified parameter terms unavailable")
    require(terms.get("requirements_bypass_observed") is True
        and _same_integer(terms.get("requirements_bypass_raw"), 0)
        and terms.get("ordinary_legality_observed") is True
        and terms.get("ordinary_can_confirm") is True and terms.get("can_confirm") is True,
        "HoF original ordinary legality rejected; do not add resources or bypass")
    require(terms.get("requirements_description_available") is True
        and terms.get("cost_description_available") is True
        and isinstance(terms.get("requirements_description"), str)
        and isinstance(terms.get("cost_description"), str)
        and terms.get("resource_quote_available") is True,
        "HoF complete real terms or quote missing")
    quote = terms.get("resource_quote")
    if not is_selected_resource_quote_v1(quote) or quote["native_affordable"] is not True:
        raise ValueError("HoF actual full10 quote is unavailable or unaffordable")
    return True


def hof_quote_terms_v1(row: object, actor: int, date_raw: int) -> HofQuoteTermsV1:
    strict_integer(actor, "HoF actor must be an actual integer, not bool")
    strict_integer(date_raw, "HoF date must be an actual integer, not bool")
    packet = json_object(row, "HoF actual quote query failed")
    require(packet.get("ok") is True and not packet.get("error"), "HoF actual quote query failed")
    value = json_object(packet.get("result"), "HoF actual keyed decision is absent or ambiguous")
    require(value.get("available") is True and value.get("decision_key") == "create_hof_decision"
        and _same_integer(value.get("matching_row_count"), 1),
        "HoF actual keyed decision is absent or ambiguous")
    for key in ("detail_definition_matches_target", "detail_tree_complete",
                "detail_root_visible", "detail_actor_binding_verified"):
        require(value.get(key) is True, "HoF selected detail proof unavailable: " + key)
    require(_same_integer(value.get("detail_actor_reference_key"), actor)
        and _same_integer(value.get("played_character_id"), actor)
        and _same_integer(value.get("date_raw"), date_raw), "HoF selected detail actor/date changed")
    terms = value.get("selected_terms")
    if not _qualified_hof_terms(terms, actor, date_raw):
        raise ValueError("HoF actual selected qualified parameter terms unavailable")
    # A TypeGuard validates the required wire subset without dropping unknown
    # fields or filling the historical missing stock_default_parameter key.
    return terms


def _file_pin(value: object) -> TypeGuard[FilePinV1]:
    if not is_json_object(value) or set(value) != {"path", "bytes", "sha256"}:
        return False
    size, sha = value["bytes"], value["sha256"]
    return (isinstance(value["path"], str) and type(size) is int and size >= 0
        and isinstance(sha, str) and len(sha) == 64
        and all(c in "0123456789abcdef" for c in sha))


def file_pin_v1(value: object) -> FilePinV1:
    if not _file_pin(value):
        raise ValueError("HoF requires an exact original receipt pin")
    return value


def _hof_claim(value: object) -> TypeGuard[HofQuoteClaimV1]:
    claim = json_object(value, "HoF finite once claim differs")
    require(claim.get("schema") == "faith-e02-R19-hof-once-claim-v1"
        and claim.get("decision_key") == "create_hof_decision", "HoF finite once claim differs")
    strict_integer(claim.get("actor"), "HoF claim actor must be an actual integer")
    strict_integer(claim.get("date_raw"), "HoF claim date must be an actual integer")
    refs = json_array(claim.get("quote_receipts"), "HoF requires two independent original quote receipts")
    require(len(refs) == 2, "HoF requires two independent original quote receipts")
    pins = [file_pin_v1(ref) for ref in refs]
    require(pins[0]["path"] != pins[1]["path"], "HoF requires two independent original quote receipts")
    return True


def hof_quote_claim_v1(value: object) -> HofQuoteClaimV1:
    if not _hof_claim(value):
        raise ValueError("HoF finite once claim differs")
    return value
