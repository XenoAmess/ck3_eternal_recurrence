"""Narrow, explicit comparison of narration and SentenceBoundary metadata.

The provider's original text is never rewritten. A recognized formatting
difference is reported as such, rather than labeled an exact text match.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Literal, TypedDict

MatchStatus = Literal['EXACT', 'LEADING_OPEN_QUOTE_OMITTED']


class SentenceMatchJSON(TypedDict):
    sequence: int
    source_text: str
    reported_text: str
    status: MatchStatus


@dataclass(frozen=True)
class SentenceMatch:
    sequence: int
    source_text: str
    reported_text: str
    status: MatchStatus


def _compare(sequence: int, source: str, reported: str) -> SentenceMatch:
    if not source or not reported:
        raise ValueError('Empty source or reported sentence')
    if source == reported:
        return SentenceMatch(sequence, source, reported, 'EXACT')
    if source.startswith('\u201c') and reported == source[1:]:
        return SentenceMatch(sequence, source, reported, 'LEADING_OPEN_QUOTE_OMITTED')
    raise ValueError('Unrecognized SentenceBoundary text difference at sentence ' + str(sequence))


def reconcile_sentence_texts(source: tuple[str, ...], reported: tuple[str, ...]) -> tuple[SentenceMatch, ...]:
    """Match complete sentences or one omitted U+201C at source index zero.

    No whitespace normalization, punctuation stripping, interior edit, word
    replacement, numeric change, or sentence-count change is permitted.
    """
    if not isinstance(source, tuple) or not isinstance(reported, tuple):
        raise ValueError('Internal sentence collections must be tuples')
    if not 1 <= len(source) <= 1024 or len(source) != len(reported):
        raise ValueError('Source and reported sentence counts must match')
    if any(not isinstance(item, str) for item in (*source, *reported)):
        raise ValueError('Sentence entries must be strings')
    return tuple(_compare(i, expected, actual) for i, (expected, actual) in enumerate(zip(source, reported), 1))


def encode_sentence_matches(matches: tuple[SentenceMatch, ...]) -> list[SentenceMatchJSON]:
    """Convert the internal tuple to the explicit JSON array representation."""
    result: list[SentenceMatchJSON] = []
    for expected_sequence, item in enumerate(matches, 1):
        if type(item.sequence) is not int or item.sequence != expected_sequence:
            raise ValueError('Sentence match sequence must be exact consecutive integers')
        validated = _compare(item.sequence, item.source_text, item.reported_text)
        if item.status != validated.status:
            raise ValueError('Declared text-match status does not describe the actual texts')
        result.append({'sequence': item.sequence, 'source_text': item.source_text,
            'reported_text': item.reported_text, 'status': item.status})
    return result


def decode_sentence_matches(value: object) -> tuple[SentenceMatch, ...]:
    """Validate a persisted JSON array before constructing internal matches."""
    if not isinstance(value, list) or not 1 <= len(value) <= 1024:
        raise ValueError('Expected nonempty bounded JSON sentence-match array')
    result: list[SentenceMatch] = []
    for expected_sequence, raw in enumerate(value, 1):
        if not isinstance(raw, dict) or set(raw) != {'sequence', 'source_text', 'reported_text', 'status'}:
            raise ValueError('Missing, extra, or wrong sentence-match fields')
        sequence: object = raw['sequence']
        source: object = raw['source_text']
        reported: object = raw['reported_text']
        status: object = raw['status']
        if type(sequence) is not int or sequence != expected_sequence:
            raise ValueError('Sequence must be an exact consecutive integer')
        if not isinstance(source, str) or not isinstance(reported, str):
            raise ValueError('Source and reported text must be strings')
        match = _compare(sequence, source, reported)
        if status != match.status:
            raise ValueError('Persisted status does not describe actual text difference')
        result.append(match)
    return tuple(result)
