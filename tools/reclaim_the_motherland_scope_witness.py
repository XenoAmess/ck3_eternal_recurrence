"""Byte-exact, log-only RMTM fixture projections; never prepare or launch a game."""
from __future__ import annotations

import hashlib


FIXTURE_RELATIVE = "common/scripted_effects/rqa_effects.txt"
CALLBACK_RELATIVE = "events/rmtm_loyalty_events.txt"
PREFIX = b"RQA_WITNESS_V1"
SCOPE_PREFIX = b"rqa_wit_v1_"

EXECUTE = '''\t\t\t# RQA_WITNESS_V1 EXECUTE_ONLY_BEGIN
\t\t\tvar:rqa_later_title = {
\t\t\t\tsave_temporary_scope_as = rqa_wit_v1_exec_later
\t\t\t\tif = {
\t\t\t\t\tlimit = { exists = current_heir }
\t\t\t\t\tcurrent_heir = { save_temporary_scope_as = rqa_wit_v1_exec_current_heir }
\t\t\t\t}
\t\t\t}
\t\t\tprimary_title = {
\t\t\t\tif = {
\t\t\t\t\tlimit = { exists = current_heir }
\t\t\t\t\tcurrent_heir = { save_temporary_scope_as = rqa_wit_v1_exec_primary_heir }
\t\t\t\t}
\t\t\t}
\t\t\tdebug_log = "RQA_WITNESS_V1 EXEC_BEGIN"
\t\t\tdebug_log_scopes = yes
\t\t\tdebug_log = "RQA_WITNESS_V1 EXEC_END"
\t\t\t# RQA_WITNESS_V1 EXECUTE_ONLY_END
'''

CALLBACK_ENTRY = '''\t\t# RQA_WITNESS_V1 CALLBACK_ENTRY_ONLY_BEGIN
\t\tif = {
\t\t\tlimit = { has_character_flag = rqa_waiting_for_succession }
\t\t\tif = {
\t\t\t\tlimit = { exists = var:rmtm_succession_title }
\t\t\t\tvar:rmtm_succession_title = {
\t\t\t\t\tsave_temporary_scope_as = rqa_wit_v1_callback_later
\t\t\t\t\tif = {
\t\t\t\t\t\tlimit = { exists = var:rmtm_succession_heir }
\t\t\t\t\t\tvar:rmtm_succession_heir = {
\t\t\t\t\t\t\tsave_temporary_scope_as = rqa_wit_v1_callback_expected_heir
\t\t\t\t\t\t}
\t\t\t\t\t}
\t\t\t\t}
\t\t\t}
\t\t\tdebug_log = "RQA_WITNESS_V1 CALLBACK_ENTRY_BEGIN"
\t\t\tdebug_log_scopes = yes
\t\t\tdebug_log = "RQA_WITNESS_V1 CALLBACK_ENTRY_END"
\t\t}
\t\t# RQA_WITNESS_V1 CALLBACK_ENTRY_ONLY_END
'''

CALLBACK_EXIT = '''\t\t# RQA_WITNESS_V1 CALLBACK_EXIT_ONLY_BEGIN
\t\tif = {
\t\t\tlimit = { has_character_flag = rqa_waiting_for_succession }
\t\t\tif = {
\t\t\t\tlimit = { exists = primary_title }
\t\t\t\tprimary_title = { save_temporary_scope_as = rqa_wit_v1_callback_primary_after }
\t\t\t}
\t\t\tif = {
\t\t\t\tlimit = { exists = scope:rqa_wit_v1_callback_later }
\t\t\t\tscope:rqa_wit_v1_callback_later = {
\t\t\t\t\tif = {
\t\t\t\t\t\tlimit = { exists = holder }
\t\t\t\t\t\tholder = { save_temporary_scope_as = rqa_wit_v1_callback_holder_after }
\t\t\t\t\t}
\t\t\t\t}
\t\t\t}
\t\t\tif = {
\t\t\t\tlimit = { exists = var:rmtm_succession_title }
\t\t\t\tdebug_log = "RQA_WITNESS_V1 CALLBACK_ROOT_REF_PRESENT"
\t\t\t}
\t\t\telse = { debug_log = "RQA_WITNESS_V1 CALLBACK_ROOT_REF_ABSENT" }
\t\t\tdebug_log = "RQA_WITNESS_V1 CALLBACK_EXIT_BEGIN"
\t\t\tdebug_log_scopes = yes
\t\t\tdebug_log = "RQA_WITNESS_V1 CALLBACK_EXIT_END"
\t\t}
\t\t# RQA_WITNESS_V1 CALLBACK_EXIT_ONLY_END
'''

SPECS = {
    "execute": ("\t\t\tset_player_character = scope:rqa_later_heir\n", EXECUTE, "", 1),
    "callback": ("\t\trmtm_complete_restoration_succession_effect = yes\n",
                 CALLBACK_ENTRY, CALLBACK_EXIT, 2),
}


def byte_pin(raw: bytes) -> dict:
    return {"bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest()}


def _parts(raw: bytes, kind: str) -> tuple[bytes, bytes, bytes, int]:
    anchor, before, after, count = SPECS[kind]
    newline = b"\r\n" if b"\r\n" in raw else b"\n"
    return (*(text.encode("ascii").replace(b"\n", newline)
              for text in (anchor, before, after)), count)


def restore(projected: bytes, kind: str) -> bytes:
    """Remove only the exact approved insertions, not arbitrary marked regions."""
    anchor, before, after, _ = _parts(projected, kind)
    decorated = before + anchor + after
    if projected.count(decorated) != 1:
        raise ValueError("Exact scope-witness insertion is missing or changed")
    raw = projected.replace(decorated, anchor, 1)
    if PREFIX in raw or SCOPE_PREFIX in raw:
        raise ValueError("Unremoved scope-witness bytes remain")
    return raw


def project(raw: bytes, kind: str) -> tuple[bytes, dict]:
    """Add three dumps total across the unchanged execute and callback paths."""
    if PREFIX in raw or SCOPE_PREFIX in raw:
        raise ValueError("Use the original, unprojected input")
    anchor, before, after, count = _parts(raw, kind)
    if raw.count(anchor) != 1:
        raise ValueError("Original scope-witness anchor must occur exactly once")
    projected = raw.replace(anchor, before + anchor + after, 1)
    inverse = restore(projected, kind)
    if inverse != raw:
        raise ValueError("Scope-witness inverse did not restore the original bytes")
    return projected, {"kind": kind, "source": byte_pin(raw),
                       "projected": byte_pin(projected), "inverse": byte_pin(inverse),
                       "inverse_byte_exact": True, "scope_dump_count": count,
                       "persistent_writes": False, "business_pass": False,
                       "runtime_status": "NOT_RUN"}
