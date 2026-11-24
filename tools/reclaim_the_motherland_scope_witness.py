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


# Pure DATA consumer. The projector above is byte-preserved. No entrypoint,
# CK3 call, legacy Native packet, current-world claim or caller authority.
import re as _scope_re


class ScopeWitnessParseError(ValueError):
    """Missing, ambiguous or malformed original witness DATA."""


_SCOPE_PHASES = (
    ("execute", b"EXEC_BEGIN", b"EXEC_END", (
        ("rqa_wit_v1_exec_later", "title"),
        ("rqa_wit_v1_exec_current_heir", "character"),
        ("rqa_wit_v1_exec_primary_heir", "character"),
    )),
    ("callback_entry", b"CALLBACK_ENTRY_BEGIN", b"CALLBACK_ENTRY_END", (
        ("rqa_wit_v1_callback_later", "title"),
        ("rqa_wit_v1_callback_expected_heir", "character"),
    )),
    ("callback_exit", b"CALLBACK_EXIT_BEGIN", b"CALLBACK_EXIT_END", (
        ("rqa_wit_v1_callback_later", "title"),
        ("rqa_wit_v1_callback_primary_after", "title"),
        ("rqa_wit_v1_callback_holder_after", "character"),
    )),
)

# Exact stock SCOPE_DEBUG_FORMAT lines, current859 core_l_*:78. These are
# pre-logger formatter DATA. Actual logger decoration/type labels remain UNBOUND.
_SCOPE_DEBUG_FORMATS = {
    "english": "$NAME$ #weak ($TYPE|U$ - $ID$)#!",
    "simp_chinese": "$NAME$#weak （$TYPE|U$-$ID$）#!",
    "spanish": "$NAME$ #weak ($TYPE|U$ - $ID$)#!",
    "french": "$NAME$ #weak ($TYPE|U$ – $ID$)#!",
    "german": "$NAME$ #weak ($TYPE|U$ – $ID$)#!",
    "korean": "$NAME$ #weak ($TYPE|U$ - $ID$)#!",
    "japanese": "$NAME$ #weak （$TYPE|U$ - $ID$）#!",
    "russian": "$NAME$ #weak ($TYPE|U$\u00a0— $ID$)#!",
    "polish": "$NAME$ #weak ($TYPE|U$ – $ID$)#!",
}
_SCOPE_LOG_LIMIT = 16 * 1024 * 1024


def _scope_need(condition: bool, reason: str) -> None:
    if not condition:
        raise ScopeWitnessParseError(reason)


def _scope_file_pin(raw: bytes, source: dict) -> dict:
    _scope_need(type(raw) is bytes and len(raw) <= _SCOPE_LOG_LIMIT,
                "A complete bounded byte buffer is required")
    _scope_need(type(source) is dict and set(source) == {"path", "bytes", "sha256"},
                "Exact three-field raw FilePin required")
    _scope_need(type(source["path"]) is str and bool(source["path"])
                and "\x00" not in source["path"], "FilePin path invalid")
    _scope_need(type(source["bytes"]) is int and source["bytes"] == len(raw),
                "Raw FilePin byte count differs")
    _scope_need(type(source["sha256"]) is str
                and _scope_re.fullmatch(r"[0-9a-f]{64}", source["sha256"]) is not None
                and hashlib.sha256(raw).hexdigest() == source["sha256"],
                "Raw FilePin SHA-256 differs")
    return dict(source)


def _scope_lines(raw: bytes) -> list[tuple[int, int, bytes]]:
    rows = []
    start = 0
    for value in raw.splitlines(keepends=True):
        end = start + len(value)
        rows.append((start, end, value.rstrip(b"\r\n")))
        start = end
    return rows


def extract_original_scope_dump_containers(raw: bytes, source: dict) -> dict:
    """Index the six unique original markers without guessing logger prefixes.

    Ranges are zero-based, end-exclusive original bytes. The untouched payload
    may still include actual logger prefixes; this function never strips them.
    FilePin checks identify the supplied buffer, not its Runtime provenance.
    """
    actual = _scope_file_pin(raw, source)
    lines = _scope_lines(raw)
    containers = []
    previous_end = 0
    for phase, begin, end, _ in _SCOPE_PHASES:
        markers = []
        for token in (begin, end):
            literal = PREFIX + b" " + token
            _scope_need(raw.count(literal) == 1,
                        "Missing or repeated exact original marker: " + literal.decode())
            matching = [(a, z, line) for a, z, line in lines if literal in line]
            _scope_need(len(matching) == 1, "Marker is not on exactly one raw line")
            a, z, line = matching[0]
            _scope_need(line.count(literal) == 1, "Repeated marker in raw line")
            _scope_need(line.endswith(literal), "Exact marker has an unsupported raw suffix")
            at = a + line.index(literal)
            markers.append({"literal": literal.decode(), "line_byte_range": [a, z],
                            "literal_byte_range": [at, at + len(literal)]})
        first, last = markers
        payload_begin = first["line_byte_range"][1]
        payload_end = last["line_byte_range"][0]
        _scope_need(previous_end <= first["line_byte_range"][0]
                    and payload_begin < payload_end,
                    "Original witness order, overlap or truncation differs")
        containers.append({"phase": phase, "begin": first, "end": last,
                           "payload_byte_range": [payload_begin, payload_end]})
        previous_end = last["line_byte_range"][1]
    return {"schema": "rmtm-original-scope-dump-containers-unbound-v1",
            "status": "UNBOUND_LOG_TRANSPORT_AND_TYPE_LABELS", "source": actual,
            "containers": containers, "byte_ranges": "zero-based, end-exclusive",
            "world_binding": "NOT_CHECKED", "business_pass": False,
            "execute_time_identity_qualified": False}


def _scope_type_labels(kind_labels: dict) -> dict:
    _scope_need(type(kind_labels) is dict and set(kind_labels) == {"character", "title"},
                "Both explicit DATA kind labels required")
    for label in kind_labels.values():
        _scope_need(type(label) is str and bool(label) and len(label.encode("utf-8")) <= 128
                    and not any(c in label for c in "\r\n\x00#$"),
                    "Kind label DATA malformed")
    _scope_need(kind_labels["character"] != kind_labels["title"],
                "Kind labels are ambiguous")
    return dict(kind_labels)


def parse_scope_dump_payload(payload: bytes, phase: str, *, language: str,
                             kind_labels: dict, origin_byte: int = 0,
                             richtext_encoding: str = "LITERAL_HASH") -> dict:
    """Parse an unframed formatter payload only; never assert Runtime binding.

    kind_labels are display DATA, not caller permission or proof of engine kind.
    A real consumer must attest the effective localization and raw-log transport
    separately before using these values alongside actual Native/Core receipts.
    """
    _scope_need(type(payload) is bytes and len(payload) <= _SCOPE_LOG_LIMIT,
                "Bounded formatter payload bytes required")
    _scope_need(type(origin_byte) is int and origin_byte >= 0, "Byte origin invalid")
    phases = [p for p in _SCOPE_PHASES if p[0] == phase]
    _scope_need(len(phases) == 1, "Unknown original phase")
    _scope_need(type(language) is str and language in _SCOPE_DEBUG_FORMATS,
                "Effective stock formatter language unbound")
    labels = _scope_type_labels(kind_labels)
    try:
        payload.decode("utf-8", errors="strict")
    except UnicodeDecodeError as error:
        raise ScopeWitnessParseError("Payload is not complete UTF-8") from error
    _scope_need(b"\x00" not in payload, "NUL or truncated logger payload unsupported")
    lines = _scope_lines(payload)
    roots = [i for i, (_, _, line) in enumerate(lines) if line.startswith(b"Root: ")]
    headers = [i for i, (_, _, line) in enumerate(lines) if line == b"Saved event targets:"]
    _scope_need(len(roots) == 1 and len(headers) == 1 and roots[0] < headers[0],
                "Unframed Root/singular target container missing or ambiguous")
    lists = [i for i, (_, _, line) in enumerate(lines) if line == b"Saved list targets:"]
    _scope_need(len(lists) <= 1 and (not lists or lists[0] > headers[0]),
                "Saved list target container ambiguous")
    stop = lists[0] if lists else len(lines)
    section = lines[headers[0] + 1:stop]
    parsed = []
    for name, kind in phases[0][3]:
        prefix = name.encode("ascii") + b": "
        matches = [(a, z, line) for a, z, line in section
                   if line.startswith(name.encode("ascii") + b":")]
        _scope_need(len(matches) == 1, "Required singular target missing/repeated: " + name)
        a, z, line = matches[0]
        _scope_need(line.startswith(prefix), "Malformed singular target separator: " + name)
        value = line[len(prefix):].decode("utf-8")
        _scope_need(richtext_encoding in {"LITERAL_HASH", "CONTROL15"},
                    "Explicit known formatter encoding required; no auto normalization")
        formatter = _SCOPE_DEBUG_FORMATS[language]
        if richtext_encoding == "CONTROL15":
            formatter = formatter.replace("#weak", "\x15weak").replace("#!", "\x15!")
        pattern = _scope_re.escape(formatter)
        pattern = pattern.replace(_scope_re.escape("$NAME$"), r"(?P<name>[^\r\n]*)")
        pattern = pattern.replace(_scope_re.escape("$TYPE|U$"), _scope_re.escape(labels[kind]))
        pattern = pattern.replace(_scope_re.escape("$ID$"), r"(?P<id>0|[1-9][0-9]*)")
        found = _scope_re.fullmatch(pattern, value)
        _scope_need(found is not None, "Wrong kind or incomplete final ID format: " + name)
        _scope_need(len(found.group("id")) <= 10, "Packed32 decimal field is too wide")
        number = int(found.group("id"))
        _scope_need(0 <= number < 0xFFFFFFFF, "Invalid complete packed32 ID: " + name)
        parsed.append({"scope_name": name, "expected_kind": kind,
                       "display_kind_label": labels[kind], "full_packed_id": number,
                       "raw_row": line.decode("utf-8"),
                       "row_byte_range": [origin_byte + a, origin_byte + a + len(line)],
                       "line_byte_range": [origin_byte + a, origin_byte + z]})
    return {"schema": "rmtm-original-scope-formatter-data-v1", "phase": phase,
            "status": "PARSED_DATA_UNBOUND_RUNTIME", "language": language,
            "kind_labels": labels, "targets": parsed,
            "world_binding": "NOT_CHECKED", "business_pass": False,
            "execute_time_identity_qualified": False}


def parse_first_line_prefixed_scope_payload(payload: bytes, phase: str, *, language: str,
                                           kind_labels: dict, origin_byte: int = 0) -> dict:
    """Observed current267 transport shape only; no genuine-log/type/world authority.

    Keep the first logger line and every continuation byte intact. The actual
    D3-window sample has only ordinary Character targets, so it cannot satisfy
    any original execute/callback fixed-name phase. Title labels supplied to
    this DATA parser remain unobserved for genuine original witness containers.
    """
    _scope_need(type(payload) is bytes and len(payload) <= 24 * 1024,
                "Bounded original logger payload required")
    lines = _scope_lines(payload)
    header = rb"\[(?:[01][0-9]|2[0-3]):[0-5][0-9]:[0-5][0-9]\]\[D\]\[effectimpl\.cpp:656\]: [^\r\n]*"
    _scope_need(len(lines) >= 4 and _scope_re.fullmatch(header, lines[0][2]) is not None,
                "Observed first-line logger prefix differs")
    _scope_need(lines[1][2].startswith(b"Root: "),
                "Unprefixed Root continuation required")
    for _, _, line in lines[1:]:
        _scope_need(_scope_re.match(rb"\[[0-9]{2}:[0-9]{2}:[0-9]{2}\]\[[A-Z]\]\[", line) is None,
                    "Prefixed/interleaved continuation is not the observed transport")
    result = parse_scope_dump_payload(payload, phase, language=language,
        kind_labels=kind_labels, origin_byte=origin_byte, richtext_encoding="CONTROL15")
    result.update(status="PARSED_PREFIXED_FORMAT_DATA_ONLY", richtext_encoding="CONTROL15",
                  transport="CURRENT267_FIRST_LINE_PREFIX_CONTINUATIONS_UNPREFIXED",
                  provenance="CALLER_SUPPLIED_BYTES_NOT_ATTESTED",
                  original_phase_type_binding="NOT_OBSERVED",
                  business_pass=False, execute_time_identity_qualified=False)
    return result


def parse_original_scope_witness_log(raw: bytes, source: dict, *, layout: str = "UNBOUND",
                                    language: str | None = None,
                                    kind_labels: dict | None = None) -> dict:
    """Retain actual raw ranges, with an explicit UNBOUND real-log default.

    The sole stitched layout below is expressly a SOFTWARE FIXTURE. Current859
    genuine logging prefixes, rich-text retention and effective TYPE labels must
    be observed before a new narrow transport profile can be adopted. No fake
    log can acquire Native/world/revision/D5 qualification through this parser.
    """
    result = extract_original_scope_dump_containers(raw, source)
    _scope_need(layout in {"UNBOUND", "UNPREFIXED_SOFTWARE_FIXTURE_V1"},
                "Actual log transport profile is not implemented or qualified")
    if layout == "UNBOUND":
        result["required_actual_sample"] = [
            "One complete genuine original three-container debug.log FilePin and full read EOF",
            "Actual prefix treatment on message and continuation lines, newline and rich-text retention",
            "Effective loaded SCOPE_DEBUG_FORMAT and observed Character/Title display TYPE labels",
        ]
        return result
    _scope_need(language is not None and kind_labels is not None,
                "Explicit software fixture display DATA required")
    for phase, (_, begin, end, _) in zip(result["containers"], _SCOPE_PHASES, strict=True):
        # The fixture transport has literal-only marker lines. Never silently
        # strip an unobserved real logger prefix, timestamp or formatting code.
        for which, token in (("begin", begin), ("end", end)):
            a, z = phase[which]["line_byte_range"]
            _scope_need(raw[a:z].rstrip(b"\r\n") == PREFIX + b" " + token,
                        "Software fixture marker line has unbound transport decoration")
        a, z = phase["payload_byte_range"]
        phase["parsed_data"] = parse_scope_dump_payload(raw[a:z], phase["phase"],
            language=language, kind_labels=kind_labels, origin_byte=a)
    result["status"] = "PARSED_SOFTWARE_FIXTURE_ONLY"
    result["layout"] = layout
    return result


def _current267_scope_profile_ranges(containers: list) -> list:
    return [{"phase": item["phase"],
             "begin_line_byte_range": list(item["begin"]["line_byte_range"]),
             "begin_literal_byte_range": list(item["begin"]["literal_byte_range"]),
             "payload_byte_range": list(item["payload_byte_range"]),
             "end_line_byte_range": list(item["end"]["line_byte_range"]),
             "end_literal_byte_range": list(item["end"]["literal_byte_range"])}
            for item in containers]


def _current267_scope_profile_range(value: list, size: int) -> list:
    _scope_need(type(value) is list and len(value) == 2
                and all(type(number) is int for number in value)
                and 0 <= value[0] < value[1] <= size,
                "Actual original byte range is not a bounded integer pair")
    return list(value)


def parse_current267_original_scope_full_log(raw: bytes, source: dict, *,
                                           profile: dict | None = None) -> dict:
    """Join original extractor and observed-format parser, never business authority.

    Default remains UNBOUND. The explicit profile is DATA bound to the exact
    complete log, actual three containers, six message prefixes and observed
    Character/Title label rows. No caller actor/title/epoch/revision is accepted.
    Missing original D5 containers must not be supplied by an ordinary D3 dump.
    This function does not promote typed epoch/ACK or parsed IDs to D5/26 PASS.
    """
    result = extract_original_scope_dump_containers(raw, source)
    if profile is None:
        result["required_actual_binding"] = [
            "Exact full-log FilePin plus three original container byte ranges",
            "Six actual original debug_log message prefixes",
            "Effective language and actual Character/Title label rows",
        ]
        return result
    keys = {"schema", "source", "language", "kind_labels", "container_ranges",
            "marker_prefixes", "kind_label_evidence"}
    _scope_need(type(profile) is dict and set(profile) == keys,
                "Exact current267 original full-log profile required")
    _scope_need(profile["schema"] == "rmtm-current267-original-control15-profile-data-v1",
                "Unknown original full-log DATA profile")
    bound_source = _scope_file_pin(raw, profile["source"])
    _scope_need(bound_source == result["source"],
                "Profile refers to another original full log")
    language = profile["language"]
    _scope_need(type(language) is str and language in _SCOPE_DEBUG_FORMATS,
                "Effective actual language remains UNBOUND")
    labels = _scope_type_labels(profile["kind_labels"])
    actual_ranges = _current267_scope_profile_ranges(result["containers"])
    ranges = profile["container_ranges"]
    _scope_need(type(ranges) is list and len(ranges) == len(_SCOPE_PHASES),
                "All three actual original containers must be bound")
    range_keys = set(actual_ranges[0])
    for item, actual in zip(ranges, actual_ranges, strict=True):
        _scope_need(type(item) is dict and set(item) == range_keys
                    and item["phase"] == actual["phase"],
                    "Original container phase/range shape differs")
        for key in range_keys - {"phase"}:
            _current267_scope_profile_range(item[key], len(raw))
        _scope_need(item == actual,
                    "Profile byte ranges differ from complete original extractor")
    prefixes = profile["marker_prefixes"]
    _scope_need(type(prefixes) is list and len(prefixes) == 6,
                "Six actual original marker prefixes remain UNBOUND")
    index = 0
    for container in result["containers"]:
        phase = container["phase"]
        script = (b"common/scripted_effects/rqa_effects.txt" if phase == "execute"
                  else b"events/rmtm_loyalty_events.txt")
        for edge in ("begin", "end"):
            item = prefixes[index]
            index += 1
            _scope_need(type(item) is dict and set(item) == {"phase", "edge", "prefix"}
                        and item["phase"] == phase and item["edge"] == edge
                        and type(item["prefix"]) is str,
                        "Original marker prefix phase/order differs")
            first = container[edge]["line_byte_range"][0]
            at = container[edge]["literal_byte_range"][0]
            actual_prefix = raw[first:at]
            _scope_need(item["prefix"].encode("utf-8") == actual_prefix,
                        "Profile must retain the complete actual logger prefix")
            envelope = (rb"\[(?:[01][0-9]|2[0-3]):[0-5][0-9]:[0-5][0-9]\]"
                        rb"\[D\]\[jomini_effect_impl\.cpp:444\]: file: "
                        + _scope_re.escape(script)
                        + rb" line: [1-9][0-9]* \([^\r\n\x00]+\): ")
            _scope_need(_scope_re.fullmatch(envelope, actual_prefix) is not None,
                        "Original marker transport/callsite layout is UNBOUND")
        a, z = container["payload_byte_range"]
        # Do not strip first prefix/blank lines or rewrite richtext. Existing
        # observed-format parser preserves all original UTF8/control offsets.
        container["parsed_data"] = parse_first_line_prefixed_scope_payload(
            raw[a:z], phase, language=language, kind_labels=labels, origin_byte=a)
    evidence = profile["kind_label_evidence"]
    _scope_need(type(evidence) is list and len(evidence) == 2,
                "Both actual label rows must be bound, no guessed Title label")
    seen = set()
    for item in evidence:
        _scope_need(type(item) is dict
                    and set(item) == {"kind", "phase", "scope_name", "row_byte_range"}
                    and item["kind"] in {"character", "title"}
                    and item["kind"] not in seen,
                    "Observed type-label evidence shape differs")
        seen.add(item["kind"])
        rows = [row for container in result["containers"]
                if container["phase"] == item["phase"]
                for row in container["parsed_data"]["targets"]
                if row["scope_name"] == item["scope_name"]
                and row["expected_kind"] == item["kind"]]
        _scope_need(len(rows) == 1, "Evidence is not an original fixed-name/kind row")
        _current267_scope_profile_range(item["row_byte_range"], len(raw))
        _scope_need(item["row_byte_range"] == rows[0]["row_byte_range"]
                    and rows[0]["display_kind_label"] == labels[item["kind"]],
                    "Actual label row/range differs from full-log DATA")
    _scope_need(seen == {"character", "title"}, "Original kind-label binding incomplete")
    result.update(schema="rmtm-current267-original-full-log-profile-data-v1",
                  status="PARSED_ORIGINAL_CONTAINERS_DATA_BUSINESS_UNBOUND",
                  layout="CURRENT267_FIRST_LINE_PREFIX_CONTROL15_DATA_ONLY",
                  profile=profile, container_ranges=actual_ranges,
                  world_binding="NOT_CHECKED", business_pass=False,
                  execute_time_identity_qualified=False,
                  independent_original_AND=[
                      "Actual execution-time full Later/current-heir/primary-heir identity",
                      "Actual callback-entry/exit and private Native/Core/world binding",
                      "Original three physical phases and original26 business consumer",
                  ])
    return result


def read_current267_original_scope_full_log(source: dict, *,
                                          profile: dict | None = None) -> dict:
    """Read only an explicitly pinned complete log; no Game/SDK or execution.

    Missing/truncated/duplicate original markers or unsupported layout raise
    ScopeWitnessParseError. The caller must retain UNBOUND/PARTIAL, never fill
    identities from the ordinary292B D3 fragment or another source/frame.
    """
    from pathlib import Path
    _scope_need(type(source) is dict and set(source) == {"path", "bytes", "sha256"},
                "Explicit original full-log reference required")
    _scope_need(type(source["path"]) is str and bool(source["path"])
                and "\x00" not in source["path"], "Original full-log path invalid")
    _scope_need(type(source["bytes"]) is int and 0 <= source["bytes"] <= _SCOPE_LOG_LIMIT,
                "Original full-log bound invalid")
    path = Path(source["path"])
    _scope_need(path.is_file(), "Original pinned log is unavailable")
    before = path.stat()
    raw = path.read_bytes()
    after = path.stat()
    _scope_need(before.st_size == after.st_size == len(raw)
                and before.st_mtime_ns == after.st_mtime_ns,
                "Original log changed during complete read")
    _scope_file_pin(raw, source)
    return parse_current267_original_scope_full_log(raw, source, profile=profile)
