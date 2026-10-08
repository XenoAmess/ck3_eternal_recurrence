"""Original product scope and D0 evidence parsers, independent of runtime selection."""
import hashlib, re

def require(value,message):
    if not value:raise ValueError(message)
def digest(raw):return hashlib.sha256(raw).hexdigest()

def parse_song_scope(raw: bytes, policy: dict[str, object]) -> dict[str, object] | None:
    """Parse one framed dump; Root may still be Robert and is never an actor source."""
    import re
    if len(raw) > 64 * 1024 * 1024:
        raise ValueError("QOL scope log exceeds the bounded 64 MiB read")
    markers = {key: value.encode("ascii") for key, value in policy["markers"].items()}
    counts = {key: raw.count(value) for key, value in markers.items()}
    if counts["fail"]:
        raise ValueError("actual QOL post-switch qualification emitted failure")
    if any(counts[key] > 1 for key in ("begin", "pass", "end")):
        raise ValueError("QOL scope qualification was observed more than once")
    if not all(counts[key] == 1 for key in ("begin", "pass", "end")):
        return None
    lines = raw.splitlines(keepends=True)
    locations = {key: next(i for i, line in enumerate(lines) if marker in line)
                 for key, marker in markers.items() if key != "fail"}
    if not locations["begin"] < locations["pass"] < locations["end"]:
        raise ValueError("QOL scope begin/pass/end ordering is invalid")
    prefix = b"".join(lines[locations["begin"] + 1:locations["pass"]])
    saved_header = list(re.finditer(rb"(?m)^Saved event targets:\r?$", prefix))
    alias = re.escape(policy["scope_name"].encode("ascii"))
    identity = rb"\(Internal ID: (?P<actor>[1-9][0-9]*) - Historical ID han_8052\)"
    saved = list(re.finditer(rb"(?m)^" + alias + rb": [^\r\n]*?" + identity + rb"[^\r\n]*\r?$", prefix))
    current = list(re.finditer(rb"(?m)^\[\d{2}:\d{2}:\d{2}\]\[D\]\[effectimpl\.cpp:\d+\]: [^\r\n]*?" + identity + rb"[^\r\n]*\r?$", prefix))
    all_saved_labels = re.findall(rb"(?m)^" + alias + rb":", prefix)
    if len(saved_header) != 1 or len(saved) != 1 or len(all_saved_labels) != 1 or len(current) != 1:
        raise ValueError("QOL scope dump does not match the reviewed current/saved actor format")
    if not current[0].end() < saved_header[0].start() < saved[0].start():
        raise ValueError("QOL saved actor is outside the current dump section")
    actor = int(saved[0].group("actor"))
    if not 1 <= actor <= 2**31 - 1 or int(current[0].group("actor")) != actor:
        raise ValueError("QOL current and uniquely saved actor identities disagree")
    block = b"".join(lines[locations["begin"]:locations["end"] + 1])
    start = sum(len(line) for line in lines[:locations["begin"]])
    return {"schema": "ck3-xqol-current-actor-scope-proof-v1", "runtime_character_id": actor,
            "historical_character_id": "han_8052", "scope_name": policy["scope_name"],
            "begin_line": locations["begin"] + 1, "pass_line": locations["pass"] + 1, "end_line": locations["end"] + 1,
            "byte_start": start, "byte_end": start + len(block), "log_bytes": len(raw),
            "log_sha256": hashlib.sha256(raw).hexdigest(), "raw_scope_block_sha256": hashlib.sha256(block).hexdigest(),
            "raw_scope_block_hex": block.hex(), "root_scope_used": False,
            "format_boundary": "Historical .2 format is a parser fixture only; actual .4 mismatch fails closed"}

def parse_steppe_scope(raw: bytes, policy: dict[str, object]) -> dict[str, object] | None:
    """Parse one framed dump; Root may still be Robert and is never an actor source."""
    import re
    if len(raw) > 64 * 1024 * 1024:
        raise ValueError("QOL scope log exceeds the bounded 64 MiB read")
    markers = {key: value.encode("ascii") for key, value in policy["markers"].items()}
    counts = {key: raw.count(value) for key, value in markers.items()}
    if counts["fail"]:
        raise ValueError("actual QOL post-switch qualification emitted failure")
    if any(counts[key] > 1 for key in ("begin", "pass", "end")):
        raise ValueError("QOL scope qualification was observed more than once")
    if not all(counts[key] == 1 for key in ("begin", "pass", "end")):
        return None
    lines = raw.splitlines(keepends=True)
    locations = {key: next(i for i, line in enumerate(lines) if marker in line)
                 for key, marker in markers.items() if key != "fail"}
    if not locations["begin"] < locations["pass"] < locations["end"]:
        raise ValueError("QOL scope begin/pass/end ordering is invalid")
    prefix = b"".join(lines[locations["begin"] + 1:locations["pass"]])
    saved_header = list(re.finditer(rb"(?m)^Saved event targets:\r?$", prefix))
    alias = re.escape(policy["scope_name"].encode("ascii"))
    identity = rb"\(Internal ID: (?P<actor>[1-9][0-9]*) - Historical ID 194333\)"
    saved = list(re.finditer(rb"(?m)^" + alias + rb": [^\r\n]*?" + identity + rb"[^\r\n]*\r?$", prefix))
    current = list(re.finditer(rb"(?m)^\[\d{2}:\d{2}:\d{2}\]\[D\]\[effectimpl\.cpp:\d+\]: [^\r\n]*?" + identity + rb"[^\r\n]*\r?$", prefix))
    all_saved_labels = re.findall(rb"(?m)^" + alias + rb":", prefix)
    if len(saved_header) != 1 or len(saved) != 1 or len(all_saved_labels) != 1 or len(current) != 1:
        raise ValueError("QOL scope dump does not match the reviewed current/saved actor format")
    if not current[0].end() < saved_header[0].start() < saved[0].start():
        raise ValueError("QOL saved actor is outside the current dump section")
    actor = int(saved[0].group("actor"))
    if not 1 <= actor <= 2**31 - 1 or int(current[0].group("actor")) != actor:
        raise ValueError("QOL current and uniquely saved actor identities disagree")
    block = b"".join(lines[locations["begin"]:locations["end"] + 1])
    start = sum(len(line) for line in lines[:locations["begin"]])
    return {"schema": "ck3-xqol-current-actor-scope-proof-v1", "runtime_character_id": actor,
            "historical_character_id": "194333", "scope_name": policy["scope_name"],
            "begin_line": locations["begin"] + 1, "pass_line": locations["pass"] + 1, "end_line": locations["end"] + 1,
            "byte_start": start, "byte_end": start + len(block), "log_bytes": len(raw),
            "log_sha256": hashlib.sha256(raw).hexdigest(), "raw_scope_block_sha256": hashlib.sha256(block).hexdigest(),
            "raw_scope_block_hex": block.hex(), "root_scope_used": False,
            "format_boundary": "Historical .2 format is a parser fixture only; actual .4 mismatch fails closed"}

def parse_d0_frames(raw, actor):
    require(len(raw) <= 64 * 1024 * 1024, 'Diagnostic log exceeded 64 MiB')
    lines = raw.splitlines(keepends=True)
    frames = {}
    previous_end = -1
    current_pattern = re.compile(rb'^\[\d{2}:\d{2}:\d{2}\]\[D\]\[effectimpl\.cpp:\d+\]: '
                                 rb'[^\r\n]*?\(Internal ID: ([1-9][0-9]*)(?: - Historical ID [^)]*)?\)')
    root_pattern = re.compile(rb'^Root: [^\r\n]*?\(Internal ID: ([1-9][0-9]*)(?: - Historical ID [^)]*)?\)')
    for name in ('ROOT', 'SAMPLE1', 'SAMPLE2'):
        begin, end = ('ZQD09DIAG: ' + name + ' BEGIN').encode(), ('ZQD09DIAG: ' + name + ' END').encode()
        starts = [i for i, line in enumerate(lines) if begin in line]
        ends = [i for i, line in enumerate(lines) if end in line]
        require(len(starts) == len(ends) == 1 and previous_end < starts[0] < ends[0],
                'Missing, duplicate or unordered diagnostic frame: ' + name)
        previous_end = ends[0]
        block_lines = lines[starts[0] + 1:ends[0]]
        values = {}
        for field, choices in {'is_tributary': ('yes', 'no'), 'suzerain_exists': ('yes', 'no'),
                               'suzerain_self': ('yes', 'no', 'no_accessor')}.items():
            pattern = re.compile(rb'ZQD09DIAG: FACT ' + field.encode() + rb' (yes|no|no_accessor)\s*$')
            found = [match.group(1).decode() for line in block_lines if (match := pattern.search(line))]
            require(len(found) == 1 and found[0] in choices, 'Invalid diagnostic fact: ' + name + '/' + field)
            values[field] = found[0]
        require((values['suzerain_exists'] == 'no') == (values['suzerain_self'] == 'no_accessor'),
                'Diagnostic accessor facts disagree')
        current = [int(match.group(1)) for line in block_lines if (match := current_pattern.search(line))]
        roots = [int(match.group(1)) for line in block_lines if (match := root_pattern.search(line))]
        require(len(current) == len(roots) == 1 and roots[0] == actor,
                'Diagnostic current/ROOT format or identity changed')
        require(1 <= current[0] <= 2**31 - 1, 'Invalid diagnostic runtime character')
        if name == 'ROOT':
            require(current[0] == actor, 'Diagnostic ROOT differs from the actual native actor')
        else:
            number = name[-1]
            alias_pattern = re.compile(rb'^zqd09_diagnostic_sample' + number.encode() +
                                       rb': [^\r\n]*?\(Internal ID: ([1-9][0-9]*)(?: - Historical ID [^)]*)?\)')
            aliases = [int(match.group(1)) for line in block_lines if (match := alias_pattern.search(line))]
            labels = [line for line in block_lines if line.startswith(b'zqd09_diagnostic_sample' + number.encode() + b':')]
            require(len(aliases) == len(labels) == 1 and aliases[0] == current[0] and current[0] != actor,
                    'Sample alias is missing, duplicated or differs from CURRENT')
            require(values == {'is_tributary': 'no', 'suzerain_exists': 'yes', 'suzerain_self': 'yes'},
                    'Actual sample does not prove the strict self fallback')
        block = b''.join(lines[starts[0]:ends[0] + 1])
        frames[name] = {'runtime_character_id': current[0], 'root_runtime_character_id': roots[0],
                        'facts': values, 'sha256': digest(block), 'bytes': len(block),
                        'begin_line': starts[0] + 1, 'end_line': ends[0] + 1}
    require(frames['SAMPLE1']['runtime_character_id'] != frames['SAMPLE2']['runtime_character_id'],
            'Diagnostic samples are the same character')
    expected = {'ZQD09DIAG: ORIGINAL eligible none': 1, 'ZQD09DIAG: ORIGINAL eligible exists': 0,
                'ZQD09DIAG: DIAGNOSTIC pool at_least_two': 1,
                'ZQD09DIAG: DIAGNOSTIC pool exactly_one': 0, 'ZQD09DIAG: DIAGNOSTIC pool zero': 0,
                'ZQD09DIAG: GUARD rejected': 0, 'ZQD10GATE: D0 strict_eligible yes': 1,
                'ZQD10GATE: D0 strict_eligible no': 0}
    for marker, wanted in expected.items():
        require(sum(marker.encode() in line for line in lines) == wanted, 'Actual D0 marker rejected: ' + marker)
    require(not any(b'ZQD10GATE: D1 route ' in line for line in lines), 'D1 route already executed')
    return frames
