"""Pure reversible splice for canonical and frozen Source15 Service bytes."""
from __future__ import annotations

import ast
import hashlib


SOURCE15_SERVICE_SHA256 = "5b49eaf311269230aeb046e9f61ccb829aa4392c627b23f0878e14f42c3883f8"
CANONICAL_BASE_SHA256 = "9c293647d45273ef725cbb6657de1c935ce04a5985efc10b9d5248cd1211b14f"
IMPORT_OLD = b"from .campaign_root_context_contract import ("
IMPORT_NEW = (b"from .campaign_root_terminal_retry_v1 import claim_campaign_root_terminal_retry_v1\n"
              + IMPORT_OLD)
PLANNING_OLD = b'''                if getattr(error, "native_error", None) not in {
                    "campaign-root snapshot changed or is not ready",
                    "application-main typed query failed or its snapshot changed",
                }:
'''
PLANNING_NEW = b'''                if (getattr(error, "native_error", None) not in {
                    "campaign-root snapshot changed or is not ready",
                    "application-main typed query failed or its snapshot changed",
                } and not claim_campaign_root_terminal_retry_v1(error, snapshot)):
'''
SELECTED_OLD = b'''                or getattr(error, "native_error", None)
                not in {
                    "campaign-root snapshot changed or is not ready",
                    "application-main typed query failed or its snapshot changed",
                }
'''
SELECTED_NEW = b'''                or (getattr(error, "native_error", None)
                not in {
                    "campaign-root snapshot changed or is not ready",
                    "application-main typed query failed or its snapshot changed",
                } and not claim_campaign_root_terminal_retry_v1(error, root_query_start))
'''


def _retry_method(raw: bytes) -> str:
    source = raw.decode("utf-8-sig")
    nodes = [node for node in ast.walk(ast.parse(source))
             if isinstance(node, ast.FunctionDef) and node.name == "_retry_rejected_campaign_root_read"]
    if len(nodes) != 1:
        raise ValueError("expected one unchanged retry method")
    return ast.get_source_segment(source, nodes[0])


def transform_service_source(payload: bytes, *, reverse: bool = False) -> bytes:
    """No disk write; caller owns the new immutable output and its manifest."""
    old_retry = _retry_method(payload)
    if not reverse and hashlib.sha256(payload).hexdigest() not in {
            SOURCE15_SERVICE_SHA256, CANONICAL_BASE_SHA256}:
        raise ValueError("unqualified Service baseline")
    changes = ((IMPORT_OLD, IMPORT_NEW, 1), (PLANNING_OLD, PLANNING_NEW, 2),
               (SELECTED_OLD, SELECTED_NEW, 1))
    result = payload
    for before, after, count in changes:
        old, new = (after, before) if reverse else (before, after)
        if result.count(old) != count:
            raise ValueError("Service retry hunk count differs")
        result = result.replace(old, new)
    if _retry_method(result) != old_retry:
        raise ValueError("existing retry method changed")
    if reverse and hashlib.sha256(result).hexdigest() not in {
            SOURCE15_SERVICE_SHA256, CANONICAL_BASE_SHA256}:
        raise ValueError("reverse did not restore exact qualified baseline")
    return result


RETRY_BASE_SHA256 = "69ff7e9dc23dc6d06c2703e8c0f4a7475589cb91475b12f4e11e569234194414"
RETRY_MARKER = b"def retry_readonly_planning_once_v1(plan_once):"
CLAIM_API = b'''def claim_guarded_campaign_root_retry_v1():
    """Share the outer planner's one remaining retry with a guarded inner read.

    A directly selected readonly ROOT has no planning ContextVar; its existing
    caller still owns its single try. Inside planning, even a later fresh-frame
    decline consumes the budget so outer replanning cannot bypass that guard.
    """
    budget = _RETRY_BUDGET.get()
    if budget is None:
        return True
    if (not isinstance(budget, dict) or type(budget.get("remaining")) is not int
            or budget["remaining"] != 1 or not isinstance(budget.get("rejections"), list)):
        return False
    budget["remaining"] = 0
    return True


'''
RETRY_DOC_OLD = b'A failed read whose application-main executor never entered Game code.'
RETRY_DOC_NEW = b'A read rejected before its typed campaign reader; admission may read Game state.'


def transform_retry_source(payload: bytes, *, reverse: bool = False) -> bytes:
    """Add one claim API to the exact loaded helper; preserve its existing loop."""
    if not reverse and hashlib.sha256(payload).hexdigest() != RETRY_BASE_SHA256:
        raise ValueError("unqualified outer readonly retry baseline")
    old, new = ((CLAIM_API + RETRY_MARKER, RETRY_MARKER) if reverse else
                (RETRY_MARKER, CLAIM_API + RETRY_MARKER))
    if payload.count(old) != 1:
        raise ValueError("outer retry claim hunk count differs")
    result = payload.replace(old, new)
    doc_old, doc_new = (RETRY_DOC_NEW, RETRY_DOC_OLD) if reverse else (RETRY_DOC_OLD, RETRY_DOC_NEW)
    if result.count(doc_old) != 1:
        raise ValueError("outer retry admission documentation hunk differs")
    result = result.replace(doc_old, doc_new)
    if reverse and hashlib.sha256(result).hexdigest() != RETRY_BASE_SHA256:
        raise ValueError("outer retry inverse differs")
    return result
