"""Explicit source-only full-episode contract; never grants live-result credit.

This narrow boundary validates JSON-domain types before constructing immutable
objects. File bytes, line excerpts and pointer values are still verified by the
existing FormalInputs source consumer, not by this classification gate.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

ContentClass = Literal['rule', 'preview', 'historical-recall', 'editorial']
ClaimKind = Literal['source-rule', 'rule-example', 'observed-preview',
                    'historical-recall', 'editorial-scope']
MODE = 'source-mechanism-full'


@dataclass(frozen=True)
class MechanismCue:
    id: str
    content_class: ContentClass
    claim_ids: tuple[str, ...]


@dataclass(frozen=True)
class MechanismClaim:
    id: str
    claim_kind: ClaimKind


@dataclass(frozen=True)
class MechanismFullContract:
    cues: tuple[MechanismCue, ...]
    claims: tuple[MechanismClaim, ...]


def _object(value: object, label: str) -> dict[str, object]:
    if not isinstance(value, dict):
        raise ValueError(label + ' must be a JSON object')
    result: dict[str, object] = {}
    for key, child in value.items():
        if not isinstance(key, str):
            raise ValueError(label + ' must have string keys')
        result[key] = child
    return result


def _array(value: object, label: str) -> tuple[object, ...]:
    if not isinstance(value, list):
        raise ValueError(label + ' must be a JSON array')
    return tuple(value)


def _text(value: object, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(label + ' must be nonempty text')
    return value


def _texts(value: object, label: str) -> tuple[str, ...]:
    result = tuple(_text(item, label) for item in _array(value, label))
    if not result or len(set(result)) != len(result):
        raise ValueError(label + ' must be nonempty and unique')
    return result


def _content_class(value: object) -> ContentClass:
    if value == 'rule':
        return 'rule'
    if value == 'preview':
        return 'preview'
    if value == 'historical-recall':
        return 'historical-recall'
    if value == 'editorial':
        return 'editorial'
    raise ValueError('Source mechanism cue has an unknown content_class')


def _claim_kind(value: object) -> ClaimKind:
    if value == 'source-rule':
        return 'source-rule'
    if value == 'rule-example':
        return 'rule-example'
    if value == 'observed-preview':
        return 'observed-preview'
    if value == 'historical-recall':
        return 'historical-recall'
    if value == 'editorial-scope':
        return 'editorial-scope'
    raise ValueError('Source mechanism claim has an unknown claim_kind')


def _positive_integer(value: object, label: str, *, zero_allowed: bool = False) -> int:
    if type(value) is not int or value < (0 if zero_allowed else 1):
        raise ValueError(label + ' must be an exact integer in range')
    return value


def _source_refs(value: object) -> None:
    refs = _array(value, 'source_refs')
    if not refs:
        raise ValueError('Every source mechanism claim needs a narrow source_ref')
    for item in refs:
        ref = _object(item, 'source_ref')
        file = _object(ref.get('file'), 'source_ref.file')
        if set(file) != {'path', 'bytes', 'sha256'}:
            raise ValueError('source_ref.file needs the exact file binding fields')
        _text(file['path'], 'source_ref.file.path')
        _positive_integer(file['bytes'], 'source_ref.file.bytes', zero_allowed=True)
        digest = _text(file['sha256'], 'source_ref.file.sha256')
        if len(digest) != 64 or any(c not in '0123456789abcdefABCDEF' for c in digest):
            raise ValueError('Invalid source_ref.file SHA-256')
        if 'json_pointer' in ref:
            if 'first_line' in ref or 'last_line' in ref:
                raise ValueError('A source_ref cannot mix pointer and line ranges')
            pointer = _text(ref['json_pointer'], 'source_ref.json_pointer')
            if not pointer.startswith('/'):
                raise ValueError('source_ref needs an explicit JSON pointer')
        else:
            first = _positive_integer(ref.get('first_line'), 'source_ref.first_line')
            last = _positive_integer(ref.get('last_line'), 'source_ref.last_line')
            if last < first:
                raise ValueError('source_ref line range is reversed')


def parse_mechanism_full(
    document: object,
    voices: object,
    evidence: object,
) -> MechanismFullContract | None:
    """Opt in explicitly; retain all legacy live-result requirements otherwise.

    An invalid explicit mode raises. Missing or different modes return None and
    cannot create an empty-result exception in the caller.
    """
    doc = _object(document, 'document')
    if doc.get('review_content_kind') != MODE:
        return None
    voice_catalog = _object(voices, 'voices')
    cue_evidence = _object(evidence, 'evidence')
    if doc.get('scope') != 'episode02-formal-review':
        raise ValueError('Source mechanism full mode requires the full episode02 scope')
    for owner, key in ((doc, 'result_voice_batches'),):
        if _array(owner.get(key), key):
            raise ValueError('Source mechanism full mode cannot carry result voices')
    for owner, key in ((doc, 'pending_result_slots'),
                       (voice_catalog, 'new_live_result_voice_slots')):
        if _object(owner.get(key), key):
            raise ValueError('Source mechanism full mode cannot erase or invent live slots')
    raw_cues = _array(doc.get('cues'), 'cues')
    if not raw_cues:
        raise ValueError('Source mechanism full mode requires explicit cues')
    cues: list[MechanismCue] = []
    for value in raw_cues:
        row = _object(value, 'cue')
        if row.get('live_result_asserted') is not False:
            raise ValueError('Every source mechanism cue must explicitly deny live results')
        cues.append(MechanismCue(_text(row.get('id'), 'cue.id'),
                                  _content_class(row.get('content_class')),
                                  _texts(row.get('claim_ids'), 'cue.claim_ids')))
    if len({cue.id for cue in cues}) != len(cues):
        raise ValueError('Duplicate source mechanism cue identity')
    claims: list[MechanismClaim] = []
    for value in _array(cue_evidence.get('claims'), 'claims'):
        row = _object(value, 'claim')
        if row.get('live_result_asserted') is not False:
            raise ValueError('Every source mechanism claim must explicitly deny live results')
        _source_refs(row.get('source_refs'))
        claims.append(MechanismClaim(_text(row.get('id'), 'claim.id'),
                                    _claim_kind(row.get('claim_kind'))))
    claim_ids = {claim.id for claim in claims}
    if not claims or len(claim_ids) != len(claims):
        raise ValueError('Source mechanism claims must be nonempty and unique')
    if any(not set(cue.claim_ids) <= claim_ids for cue in cues):
        raise ValueError('Source mechanism cue references an absent claim')
    return MechanismFullContract(tuple(cues), tuple(claims))
