"""Read-only Rakaly stdout projection: bounded records, no melted world file.

This is an offline save observation, not a native action or proof of succession.
Unknown tokens/fields are retained as unknown rather than guessed from CK3 lore.
"""
from __future__ import annotations

from collections import Counter
from contextlib import contextmanager
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path
import ctypes
import codecs
import io
import hashlib
import json
import os
import re
import subprocess
import threading

from .campaign_development_score_v1 import D, UNITS, fmt


def utc():
    return datetime.now(timezone.utc).isoformat()


def small_json(path, cap=512 * 1024):
    path = Path(path)
    with path.open("rb") as stream:
        data = stream.read(cap + 1)
    if len(data) > cap:
        raise ValueError("metadata input exceeds bounded cap")
    return json.loads(data), {"path": str(path.resolve()), "bytes": len(data),
                              "sha256": hashlib.sha256(data).hexdigest()}


@contextmanager
def locked_save(path: Path, expected: dict | None):
    """GENERIC_READ, FILE_SHARE_READ only; identity checked under the held handle."""
    if os.name != "nt":
        raise ValueError("actual save custody requires Windows read lock")
    from ctypes import wintypes as W
    import msvcrt

    class Info(ctypes.Structure):
        _fields_ = [("attr", W.DWORD), ("created", W.FILETIME), ("accessed", W.FILETIME),
                    ("modified", W.FILETIME), ("volume32", W.DWORD), ("high", W.DWORD),
                    ("low", W.DWORD), ("links", W.DWORD), ("index_high", W.DWORD), ("index_low", W.DWORD)]

    class FileID(ctypes.Structure):
        _fields_ = [("volume", ctypes.c_ulonglong), ("id", ctypes.c_ubyte * 16)]

    k = ctypes.WinDLL("kernel32", use_last_error=True)
    k.CreateFileW.argtypes = [W.LPCWSTR, W.DWORD, W.DWORD, ctypes.c_void_p, W.DWORD, W.DWORD, W.HANDLE]
    k.CreateFileW.restype = W.HANDLE
    k.GetFileInformationByHandle.argtypes = [W.HANDLE, ctypes.POINTER(Info)]
    k.GetFileInformationByHandle.restype = W.BOOL
    k.GetFileInformationByHandleEx.argtypes = [W.HANDLE, ctypes.c_int, ctypes.c_void_p, W.DWORD]
    k.GetFileInformationByHandleEx.restype = W.BOOL
    k.CloseHandle.argtypes = [W.HANDLE]
    path = path.resolve(strict=True)
    h = k.CreateFileW(str(path), 0x80000000, 1, None, 3, 0, None)
    if h == ctypes.c_void_p(-1).value:
        raise ctypes.WinError(ctypes.get_last_error())

    def identity():
        info, fid = Info(), FileID()
        if not k.GetFileInformationByHandle(h, ctypes.byref(info)):
            raise ctypes.WinError(ctypes.get_last_error())
        if not k.GetFileInformationByHandleEx(h, 18, ctypes.byref(fid), ctypes.sizeof(fid)):
            raise ctypes.WinError(ctypes.get_last_error())
        modified = (info.modified.dwHighDateTime << 32) | info.modified.dwLowDateTime
        return {"volume_serial_number": fid.volume, "file_id_128_hex": bytes(fid.id).hex(),
                "bytes": (info.high << 32) | info.low,
                "mtime_ns": modified * 100 - 11644473600000000000,
                "attributes": info.attr, "number_of_links": info.links}

    stream, fd = None, None
    try:
        before = identity()
        if before["attributes"] & 0x400:
            raise ValueError("source is a reparse point")
        for key in ("bytes", "mtime_ns", "volume_serial_number", "file_id_128_hex"):
            if expected is not None and key in expected and expected[key] != before[key]:
                raise ValueError(f"source differs from prior identity: {key}")
        fd = msvcrt.open_osfhandle(h, os.O_RDONLY | os.O_BINARY)
        stream = os.fdopen(fd, "rb")
        proof = {"path": str(path), "identity_before": before,
                 "desired_access": "GENERIC_READ", "share_mode": "FILE_SHARE_READ",
                 "body_sha_passes": 0, "save_write_calls": 0, "locked_from_utc": utc()}
        yield stream, proof
        after = identity()
        proof.update({"identity_after": after, "unchanged": before == after, "verified_at_utc": utc()})
        if before != after:
            raise ValueError("held save identity changed")
    finally:
        if stream is not None:
            stream.close()
        elif fd is not None:
            os.close(fd)
        else:
            k.CloseHandle(h)


SCALAR = re.compile(r'^([\w.\-]+)\s*=\s*(.*?)\s*$')
NUMBER = re.compile(r"^-?\d+(?:\.\d+)?$")
LEX = re.compile(r'\s+|#[^\r\n]*(?:\r?\n|\r|$)|"(?:[^"\\]|\\.)*"|[{}=]|[^\s{}="#]+')
ROOT_CHARACTER = {"living", "dead_unprunable", "dead_prunable", "dead"}
KEEP = {"key", "holder", "de_facto_liege", "de_jure_liege", "province", "capital",
        "county", "county_title", "county_title_id", "owner", "type", "holding_type",
        "house", "dynasty_house", "dynasty", "dynasty_id", "parent_house", "founder",
        "development", "development_level", "control", "control_level", "county_control",
        "birth", "death", "gold", "value", "current", "balance", "first_name",
        "primary_title", "liege", "player", "character", "version", "meta_date", "date",
        "revolt", "casus_belli", "attacker", "defender", "original_attacker", "original_defender",
        "income", "strength", "current_strength", "strength_without_hires", "power", "max_power", "levy"}


def atom(value: str):
    if value.startswith('"') and value.endswith('"'):
        return value[1:-1]
    return value


def integer(value):
    return int(value) if isinstance(value, str) and re.fullmatch(r"\d+", value) else None


def numeric(value):
    return D(value) if isinstance(value, str) and NUMBER.fullmatch(value) else None


def melt_tokens(stream, stats=None):
    """Bounded lexical carry; quotes/comments/compact blocks may cross reads."""
    decoder = codecs.getincrementaldecoder("utf-8")("strict")
    carry = ""
    while True:
        raw = stream.read(65536)
        if stats is not None:
            stats.text_bytes += len(raw)
            stats.line_count += raw.count(b"\n")
        final = not raw
        carry += decoder.decode(raw, final=final)
        position = 0
        while position < len(carry):
            match = LEX.match(carry, position)
            if match is None:
                if not final and carry[position] in {'"', '#'}:
                    break
                raise ValueError("invalid/incomplete melted lexical token")
            token = match.group(0)
            if not final and match.end() == len(carry) and token not in {"{", "}", "="} and not token.isspace():
                break
            position = match.end()
            if not token.isspace() and not token.startswith("#"):
                yield token
        carry = carry[position:]
        if len(carry) > 2 * 1024 * 1024:
            raise ValueError("melted token exceeds bounded carry")
        if final:
            if carry.strip():
                raise ValueError("unconsumed melted lexical tail")
            return


class SaveProjection:
    """Small scalar maps only, not a complete AST or character/world objects."""
    def __init__(self, wanted_characters):
        self.wanted = set(wanted_characters)
        self.path, self.active = [], None
        self.characters, self.character_houses = {}, {}
        self.character_sources = {}
        self.character_house_unknown, self.wanted_character_unknown = set(), set()
        self.character_duplicate_audit, self.character_duplicate_examples = Counter(), []
        self.war_containers, self.war_layout_unknown = set(), False
        self.titles, self.counties, self.provinces, self.houses, self.dynasties = {}, {}, {}, {}, {}
        self.wars, self.metadata, self.schema_fields = {}, {}, {}
        self.root_counts = Counter()
        self.root_keys = []
        self.line_count, self.text_bytes, self.unknown_key_fields = 0, 0, 0
        self.unsupported_lines = 0
        self.pending, self.assignment = None, None
        self.token_count = 0
        self.selected_scalar_count, self.skipped_scalar_count = 0, 0
        self.stream_complete = False

    def token(self, token):
        self.token_count += 1
        if token == "=":
            if self.pending is None or self.assignment is not None:
                raise ValueError("unexpected assignment token")
            self.assignment, self.pending = self.pending, None
            return
        if self.assignment is not None:
            key, self.assignment = atom(self.assignment), None
            if token == "{":
                if not self.path and key not in self.root_keys:
                    self.root_keys.append(key)
                self.path.append(key)
                if len(self.path) > 128 or len(self.root_keys) > 256:
                    raise ValueError("save nesting/root-container cap exceeded")
                if self.active is None:
                    rec = self.record_kind(self.path)
                    if rec:
                        self.active = (*rec, {})
                if (self.active is not None and self.active[0] == "character" and self.active[1] in self.wanted
                        and self.path[self.active[2]:] == ["landed_data", "wars"]):
                    self.player_wars_presence()
            elif token in {"=", "}"}:
                raise ValueError("missing assigned value")
            else:
                self.scalar(key, token)
            return
        if self.pending is not None:
            self.anonymous(self.pending)
            self.pending = None
        if token == "{":
            self.path.append("[]")
            if len(self.path) > 128:
                raise ValueError("save nesting cap exceeded")
        elif token == "}":
            if not self.path:
                raise ValueError("unbalanced save close")
            if self.active is not None and len(self.path) == self.active[2]:
                self.finish()
            self.path.pop()
        else:
            self.pending = token

    def anonymous(self, token):
        if self.active is None:
            return
        if self.path and self.path[-1] in {"perk", "perks", "legacy_perks", "unlocked_perks", "held_titles", "wars", "succession"}:
            key = ".".join(self.path[self.active[2]:])
            old = self.active[3].get(key, "")
            if len(old) < 16384:
                self.active[3][key] = old + " " + atom(token)
            else:
                self.active[3]["incomplete:" + key] = "true"

    def player_wars_presence(self):
        fields = self.active[3]
        if len(fields) >= 478:
            raise ValueError("selected wars-list presence cap")
        if "present:landed_data.wars" in fields:
            fields["nonunique:landed_data.wars"] = "true"
        fields["present:landed_data.wars"] = "true"

    def complete(self):
        if self.pending is not None:
            self.anonymous(self.pending)
            self.pending = None
        if self.assignment is not None or self.path or self.active is not None:
            raise ValueError("melted stream ended inside a scope/value")
        self.stream_complete = True

    def scalar(self, key, value):
        if not self.path and key not in self.root_keys:
            self.root_keys.append(key)
        if key.startswith("0x"):
            self.unknown_key_fields += 1
        scope = self.path[0] if self.path else "root"
        examples = self.schema_fields.setdefault(scope, set())
        if len(examples) < 192:
            examples.add(".".join(self.path[1:3] + [key]) if len(self.path) < 2 or not self.path[1].isdigit() else ".".join(["<id>"] + self.path[2:4] + [key]))
        if self.active is not None:
            kind, identity, depth, fields = self.active
            relative = self.path[depth:] + [key]
            wanted = key in KEEP or "develop" in key or "control" in key or "legacy" in key
            if kind in {"county", "province", "house", "dynasty", "war"} and len(relative) <= 3:
                wanted = True
            if any(part in {"history", "character_history", "title_history", "chronicle"} for part in relative[:-1]):
                wanted = False
            if kind in {"house", "dynasty"} and len(relative) > 1 and not any("legacy" in part or "perk" in part for part in relative):
                wanted = False
            if kind == "character" and identity not in self.wanted:
                wanted = len(relative) == 1 and key in {"house", "dynasty_house"}
            if wanted:
                if len(value) > 512 or len(fields) >= 480:
                    raise ValueError(f"selected scalar cap: {kind}/{identity}; cannot infer absent fields")
                self.selected_scalar_count += 1
                name = ".".join(relative)
                if name in fields or "nonunique:" + name in fields:
                    fields.pop(name, None)
                    fields["nonunique:" + name] = "true"
                else:
                    fields[name] = atom(value)
            else:
                self.skipped_scalar_count += 1
        elif key in {"date", "version", "meta_date", "meta_player_tier", "meta_number_of_players"} and len(self.path) <= 1:
            self.metadata[".".join(self.path + [key])] = atom(value)

    def record_kind(self, path):
        if path and path[0] in {"wars", "active_wars"}:
            if len(path) == 1 or path == ["wars", "active_wars"]:
                self.war_containers.add(tuple(path))
            elif len(path) == 2 and not path[1].isdigit() and path[1] != "active_wars":
                self.war_layout_unknown = True
        if len(path) == 2 and path[0] in ROOT_CHARACTER and path[1].isdigit():
            return "character", int(path[1]), 2
        if path and path[0] == "landed_titles" and len(path) in {2, 3} and path[-1].isdigit():
            return "title", int(path[-1]), len(path)
        if len(path) in {2, 3} and path[0] in {"counties", "county_manager"} and (path[-1].isdigit() or path[-1].startswith("c_")):
            return "county", path[-1], len(path)
        if len(path) == 2 and path[0] in {"provinces", "province_manager"} and path[-1].isdigit():
            return "province", int(path[-1]), 2
        if path and path[0] in {"dynasties", "dynasty_houses", "houses"} and len(path) in {2, 3} and path[-1].isdigit():
            kind = "house" if "house" in ".".join(path[:-1]) else "dynasty"
            return kind, int(path[-1]), len(path)
        if len(path) in {2, 3} and path[0] in {"active_wars", "wars"} and path[-1].isdigit():
            return "war", int(path[-1]), len(path)
        return None

    def finish(self):
        kind, identity, depth, fields = self.active
        self.root_counts[kind] += 1
        if len(fields) > 512:
            raise ValueError(f"selected {kind}/{identity} scalar cap exceeded: {len(fields)}")
        if kind == "character":
            candidates = {integer(fields[key]) for key in ("dynasty_house", "house") if key in fields}
            ambiguous = len(candidates) > 1 or any("nonunique:" + key in fields for key in ("dynasty_house", "house"))
            house = next(iter(candidates), None)
            duplicate = identity in self.character_sources
            if duplicate:
                self.character_duplicate_audit["duplicate_records"] += 1
                if identity in self.wanted:
                    self.wanted_character_unknown.add(identity)
                    ambiguous = True
                    self.characters.pop(identity, None)
                    decision = "wanted_identity_unknown"
                elif (identity in self.character_house_unknown or ambiguous
                      or house != self.character_houses.get(identity)):
                    ambiguous = True
                    decision = "house_conflict_unknown"
                else:
                    decision = "identical_house_merged"
                self.character_duplicate_audit[decision] += 1
                if len(self.character_duplicate_examples) < 16:
                    self.character_duplicate_examples.append({"id": identity, "first_source": self.character_sources[identity],
                        "later_source": self.path[0], "decision": decision})
            else:
                self.character_sources[identity] = self.path[0]
            if len(self.character_sources) > 300000:
                raise ValueError("character identity count cap")
            if ambiguous or identity in self.character_house_unknown:
                self.character_house_unknown.add(identity)
                self.character_houses.pop(identity, None)
            elif house is not None:
                self.character_houses[identity] = house
            if identity in self.wanted and identity not in self.wanted_character_unknown:
                self.characters[identity] = fields
        else:
            target = {"title": self.titles, "county": self.counties, "province": self.provinces,
                      "house": self.houses, "dynasty": self.dynasties, "war": self.wars}[kind]
            if identity in target:
                raise ValueError(f"duplicate selected {kind} identity")
            target[identity] = fields
        self.active = None
        if len(self.character_houses) > 300000 or len(self.titles) > 100000:
            raise ValueError("world projection count cap")


    def summary(self):
        return {"metadata": self.metadata, "record_counts": dict(self.root_counts),
                "root_keys": self.root_keys, "line_count": self.line_count,
                "melted_bytes_streamed_not_saved": self.text_bytes,
                "unsupported_lines": self.unsupported_lines,
                "unknown_key_fields": self.unknown_key_fields,
                "selected_scalar_count": self.selected_scalar_count,
                "skipped_scalar_count": self.skipped_scalar_count,
                "war_scan_supported": bool(self.war_containers) and not self.war_layout_unknown,
                "character_duplicate_audit": dict(self.character_duplicate_audit),
                "character_duplicate_examples": self.character_duplicate_examples,
                "unknown_character_house_count": len(self.character_house_unknown),
                "unknown_character_house_ids_sample": sorted(self.character_house_unknown)[:16],
                "wanted_character_unknown": sorted(self.wanted_character_unknown),
                "schema_fields": {k: sorted(v) for k, v in self.schema_fields.items()},
                "selected_characters": {str(k): v for k, v in self.characters.items()}}


def melt_projection(decoder: Path, save: Path, expected: dict, wanted_characters: set[int], *, projection=None):
    projection = projection if projection is not None else SaveProjection(wanted_characters)
    stderr, truncated = bytearray(), [False]
    with locked_save(save, expected) as (_, custody):
        argv = [str(decoder), "melt", str(save), "-c", "--format", "ck3", "--unknown-key", "stringify"]
        child = subprocess.Popen(argv, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                 creationflags=0x4000 if os.name == "nt" else 0)
        def drain():
            while True:
                part = child.stderr.read(8192)
                if not part:
                    return
                available = max(0, 65536 - len(stderr))
                stderr.extend(part[:available])
                truncated[0] |= len(part) > available
        thread = threading.Thread(target=drain, daemon=True)
        thread.start()
        try:
            for token in melt_tokens(child.stdout, projection):
                projection.token(token)
            projection.complete()
            code = child.wait(timeout=60)
            thread.join(timeout=10)
            if thread.is_alive():
                raise ValueError("decoder stderr did not close")
            diagnostic = stderr.decode("utf-8", errors="replace")
            if code not in {0, 1} or (code == 1 and not all(re.fullmatch(r"[0-9a-fA-F]{4}", x) for x in diagnostic.splitlines())):
                raise ValueError(f"decoder failed: exit={code}; diagnostic={diagnostic[:1024]}")
            if projection.path or projection.active is not None:
                raise ValueError("melted stream ended inside a scoped record")
            if projection.unsupported_lines:
                raise ValueError("unsupported unbalanced canonical melt lines")
            custody["decoder"] = {"argv": argv, "actual_exit_code": code,
                                  "status": "complete" if code == 0 else "complete_with_unknown_tokens",
                                  "stderr_excerpt": diagnostic, "stderr_truncated": truncated[0],
                                  "unknown_token_count": len(diagnostic.splitlines())}
        finally:
            child.stdout.close()
            if child.poll() is None:
                # Only this owned offline decoder, never CK3 or unrelated workers.
                child.terminate()
                child.wait(timeout=10)
            thread.join(timeout=10)
            child.stderr.close()
    return projection, custody


def observation(name, value, source, locator, *, reason=None):
    scope = ("fixed_founding_house" if name == "house_anchor_id" else
             "fixed_founding_dynasty" if name in {"K_dynasty", "legacy_ranks", "dynasty_county_count",
                                                  "dynasty_anchor_id", "active_family_branches"} else
             "saved_current_player_realm")
    return {"value": None if value is None else str(value), "unit": UNITS[name],
            "availability": "unknown" if value is None else "observed",
            "scope": scope,
            "source_ref": source, "locator": locator, "unavailable_reason": reason}


def _static_context():
    # Recalculation inputs are explicit. Never silently reuse a previous campaign.
    return {}, None


def landed_title_map(paths, *, machine_id):
    """Derive county/barony/province links from explicit same-build source files."""
    class MappingProjection(SaveProjection):
        def __init__(self):
            super().__init__(set())
            self.mapping = {}

        def record_kind(self, path):
            return None

        def scalar(self, key, value):
            if key != "province" or not atom(value).isdigit():
                return
            county = next((x for x in reversed(self.path) if x.startswith("c_")), None)
            barony = next((x for x in reversed(self.path) if x.startswith("b_")), None)
            if county and barony:
                group = self.mapping.setdefault(county, {})
                if barony in group and group[barony] != int(atom(value)):
                    raise ValueError("conflicting static barony province")
                group[barony] = int(atom(value))

    result, pins = {}, []
    for path in paths:
        path = Path(path).resolve(strict=True)
        with path.open("rb") as stream:
            data = stream.read(8 * 1024 * 1024 + 1)
        if len(data) > 8 * 1024 * 1024:
            raise ValueError("static definition file exceeds bounded input cap")
        projection = MappingProjection()
        for token in melt_tokens(io.BytesIO(data.removeprefix(b'\xef\xbb\xbf'))):
            projection.token(token)
        projection.complete()
        for county, baronies in projection.mapping.items():
            for barony, province in baronies.items():
                if barony in result.setdefault(county, {}) and result[county][barony] != province:
                    raise ValueError("conflicting static files; effective mod override must be resolved explicitly")
                result[county][barony] = province
        pins.append({"path": str(path), "bytes": len(data), "sha256": hashlib.sha256(data).hexdigest()})
    now = utc()
    return {"machine_id": machine_id, "observed_at_utc": now, "county_baronies": result,
            "historical_loaded_static_hash_verified": False,
            "source": {"id": "static_titles", "files": pins,
                       "basis": "explicit definition sources read now; historical loading not inferred"}}


def bounded_observation(name, lower, upper, source, locator, reason):
    if lower == upper:
        return observation(name, lower, source, locator)
    row = observation(name, None, source, locator, reason=reason)
    row.update(availability="bounded", lower=fmt(lower), upper=fmt(upper))
    return row


def player_war_defence(character_fields, wars, *, actor):
    """Pure proof over the explicit landed player's current-war list, not alive_data counters."""
    key = "landed_data.wars"
    audit = {"method": "player_landed_war_list", "locator": key, "listed_war_ids": [], "known": False}
    def unknown(reason):
        audit["reason"] = reason
        return None, audit
    if any(prefix + key in character_fields for prefix in ("nonunique:", "incomplete:")):
        return unknown("CONFLICT_OR_TRUNCATED_LIST")
    present = character_fields.get("present:" + key) == "true"
    if key not in character_fields and not present:
        return unknown("MISSING_LIST")
    value = character_fields.get(key, "")
    if not isinstance(value, str):
        return unknown("INVALID_LIST_TYPE")
    values = value.split()
    if not values and not present:
        return unknown("EMPTY_WITHOUT_PRESENCE")
    ids = [integer(value) for value in values]
    if len(ids) > 1024 or None in ids or len(ids) != len(set(ids)):
        return unknown("INVALID_OR_DUPLICATE_WAR_IDS")
    audit["listed_war_ids"] = ids
    own_defence = False
    for identity in ids:
        war = wars.get(identity, wars.get(str(identity)))
        if not isinstance(war, dict) or "nonunique:casus_belli.defender" in war:
            return unknown("MISSING_OR_CONFLICTING_WAR")
        defender = integer(war.get("casus_belli.defender"))
        if defender is None:
            return unknown("MISSING_CB_DEFENDER")
        own_defence |= defender == actor
    audit.update(known=True, own_defence=own_defence, reason="ALL_LISTED_WARS_VERIFIED")
    return own_defence, audit


def audit_saved_county_membership_v1(projection, *, actor, house, dynasty,
                                     county_baronies, source_id):
    """Pure tri-state membership over complete saved records and explicit map.

    Missing/cyclic references are unknown. A complete foreign title record
    omitting its optional de_facto_liege is a foreign root, not a missing node.
    An unmapped c_ key has unknown geography, never an assumed landless status.
    """
    titles, realm_cache, family_cache = projection.titles, {}, {}
    key_counts = Counter(row.get("key") for row in titles.values())
    maps = county_baronies if isinstance(county_baronies, dict) else {}
    valid_maps = {key for key, rows in maps.items()
                  if isinstance(key, str) and key.startswith("c_") and isinstance(rows, dict) and rows
                  and all(isinstance(barony, str) and barony.startswith("b_")
                          and type(province) is int and province > 0 for barony, province in rows.items())
                  and len(set(rows.values())) == len(rows)}
    province_owners, barony_owners = {}, {}
    for key in valid_maps:
        for barony, province in maps[key].items():
            province_owners.setdefault(province, set()).add(key)
            barony_owners.setdefault(barony, set()).add(key)
    conflicted_maps = set().union(*(owners for owners in (*province_owners.values(), *barony_owners.values())
                                    if len(owners) > 1))
    valid_maps -= conflicted_maps

    def realm(identity):
        path, seen = [], set()
        while identity not in realm_cache:
            if identity in seen:
                result = (None, "cyclic_de_facto_liege", identity)
                break
            if identity not in titles:
                result = (None, "missing_de_facto_liege_title", identity)
                break
            seen.add(identity)
            path.append(identity)
            row = titles[identity]
            if "nonunique:holder" in row or integer(row.get("holder")) is None:
                result = (None, "title_holder_unavailable", identity)
                break
            if integer(row["holder"]) == actor:
                result = (True, "held_by_player_on_title_chain", identity)
                break
            if "nonunique:de_facto_liege" in row:
                result = (None, "conflicting_de_facto_liege", identity)
                break
            if "de_facto_liege" not in row:
                result = (False, "complete_foreign_title_root", identity)
                break
            identity = integer(row["de_facto_liege"])
            if identity is None:
                result = (None, "invalid_de_facto_liege", path[-1])
                break
        else:
            result = realm_cache[identity]
        for node in path:
            realm_cache[node] = result
        return result

    def family(holder):
        if (holder is None or holder in projection.character_house_unknown
                or holder not in projection.character_sources or house is None or dynasty is None):
            return None, "holder_house_or_founding_anchor_unavailable"
        start = projection.character_houses.get(holder)
        if start is None:
            return "0", "complete_character_without_house"
        if start in family_cache:
            return family_cache[start]
        identity, path, seen = start, [], set()
        while True:
            if identity in family_cache:
                result = family_cache[identity]
                if path and result[0] == "0":
                    result = (None, "parent_dynasty_disagrees")
                break
            if identity in seen:
                result = (None, "cyclic_parent_house")
                break
            row = projection.houses.get(identity)
            if row is None:
                result = (None, "missing_house_on_ancestry")
                break
            seen.add(identity)
            path.append(identity)
            if any("nonunique:" + key in row for key in ("dynasty", "parent_dynasty_house")):
                result = (None, "conflicting_house_ancestry")
                break
            observed_dynasty = integer(row.get("dynasty"))
            if observed_dynasty is None:
                result = (None, "house_dynasty_unavailable")
                break
            if observed_dynasty != dynasty:
                result = ("0", "different_dynasty") if len(path) == 1 else (None, "parent_dynasty_disagrees")
                break
            if identity == house:
                result = ("1", "founding_house_ancestry")
                break
            if "parent_dynasty_house" not in row:
                result = ("0.5", "complete_other_house_root_in_dynasty")
                break
            identity = integer(row["parent_dynasty_house"])
            if identity is None:
                result = (None, "invalid_parent_house")
                break
        # Cache the start only: a different-dynasty endpoint is not the same
        # proof for an earlier same-dynasty child, and must not poison its row.
        family_cache[start] = result
        return result

    states = {}
    for identity, row in titles.items():
        key = row.get("key")
        if isinstance(key, str) and key.startswith(("b_", "d_", "k_", "e_")):
            continue
        geography = isinstance(key, str) and key.startswith("c_") and key in valid_maps and key_counts[key] == 1
        inside, realm_reason, terminal = realm(identity)
        factor, family_reason = family(integer(row.get("holder")))
        states[identity] = {"key": key, "geographic": True if geography else None,
            "geography_reason": None if geography else "county_geography_or_unique_key_unavailable",
            "in_player_realm": inside, "realm_reason": realm_reason, "realm_terminal_title_id": terminal,
            "family_factor": factor, "family_reason": family_reason}
    realm_known = [i for i, row in states.items() if row["geographic"] is True and row["in_player_realm"] is True]
    realm_unknown = [i for i, row in states.items() if row["in_player_realm"] is not False
                     and (row["geographic"] is not True or row["in_player_realm"] is None)]
    family_known = [i for i, row in states.items() if row["geographic"] is True and row["family_factor"] not in {None, "0"}]
    family_unknown = [i for i, row in states.items() if row["family_factor"] != "0"
                      and (row["geographic"] is not True or row["family_factor"] is None)]
    census_complete = (projection.stream_complete and projection.unknown_key_fields == 0
                       and "landed_titles" in projection.root_keys)
    def scope(known, unknown, ready=True):
        return {"complete": census_complete and ready and not unknown,
                "known_member_title_ids": sorted(known), "unknown_title_ids": sorted(unknown),
                "count_lower": len(known), "count_upper": len(known) + len(unknown) if census_complete and ready else None}
    return {"schema": "xar.ck3.saved-county-membership-audit/v1", "source_ref": source_id,
            "date": projection.metadata.get("date"), "actor_id": actor,
            "founding_house_id": house, "founding_dynasty_id": dynasty,
            "title_census_complete": census_complete,
            "geography_complete": census_complete and all(row["geographic"] is True for row in states.values()),
            "realm": scope(realm_known, realm_unknown),
            "dynasty": scope(family_known, family_unknown, house is not None and dynasty is not None),
            "states": states}


def project_metrics(projection: SaveProjection, *, actor: int, founder: int, source_id: str, static_context=None):
    """Saved state + explicit static map; incomplete occupation/fees stay bounded."""
    from decimal import localcontext
    from .campaign_development_score_v1 import UNITS as current_units
    global UNITS
    UNITS = current_units
    with localcontext() as ctx:
        ctx.prec = 40
        return _project_metrics(projection, actor=actor, founder=founder, source_id=source_id,
                                static_context=static_context)


def _project_metrics(projection, *, actor, founder, source_id, static_context=None):
    metrics = {name: observation(name, None, source_id, None,
               reason="尚缺该字段完整、同帧且语义闭合的观测") for name in UNITS}
    player = projection.characters.get(actor, {})
    if actor in projection.wanted_character_unknown:
        metrics["gold"]["unavailable_reason"] = "玩家角色ID存在重复记录，角色正文保持未知，不能任取一个钱包值"
    for key in ("alive_data.gold.value", "alive_data.gold.current", "alive_data.gold", "gold"):
        value = numeric(player.get(key))
        if value is not None:
            metrics["gold"] = observation("gold", value, source_id, f"living.{actor}.{key}")
            break
    title_by_key = {row.get("key"): identity for identity, row in projection.titles.items() if "key" in row}
    static, static_pin = _static_context() if static_context is None else (static_context, static_context.get("metadata_pin"))
    h0 = static.get("founding_house_id", projection.character_houses.get(founder))
    dynasty = static.get("founding_dynasty_id", integer(projection.houses.get(h0, {}).get("dynasty")))
    actor_house = projection.character_houses.get(actor)
    membership = audit_saved_county_membership_v1(projection, actor=actor, house=h0, dynasty=dynasty,
        county_baronies=static.get("county_baronies"), source_id=source_id)
    states = membership["states"]
    counties = {identity: projection.titles[identity] for identity, row in states.items() if row["geographic"] is True}
    owned = {identity: row for identity, row in counties.items() if states[identity]["in_player_realm"] is True}
    family_factors = {identity: None if states[identity]["family_factor"] is None
                      else D(states[identity]["family_factor"]) for identity in counties}
    family_unknown = membership["dynasty"]["unknown_title_ids"]
    same_dynasty = {identity: row for identity, row in counties.items()
                    if family_factors[identity] is not None and family_factors[identity] > 0}
    maps = static.get("county_baronies", {})
    q_by_id, controls, selected, relevant = {}, {}, [], {**owned, **same_dynasty}
    unresolved = []
    for identity, title in relevant.items():
        key = title["key"]
        county = projection.counties.get(key, projection.counties.get(str(identity), {}))
        development = next((numeric(county.get(k)) for k in ("development", "development_level")
                            if numeric(county.get(k)) is not None), None)
        control = next((numeric(county.get(k)) for k in ("control", "control_level", "county_control")
                        if numeric(county.get(k)) is not None), None)
        completed, holding_rows, holding_known = 0, [], key in maps
        for barony, province in maps.get(key, {}).items():
            raw = projection.provinces.get(province)
            title_id = title_by_key.get(barony)
            barony_title = projection.titles.get(title_id, {})
            kind = raw.get("holding.type") if raw is not None else None
            # An explicit current holding type is positive evidence of an existing holding.
            # Empty type + absent barony holder is known empty; contradictory cases stay unknown.
            if kind is not None and kind != "none":
                completed += 1
            elif raw is None or integer(barony_title.get("holder")) is not None:
                holding_known = False
            holding_rows.append({"barony": barony, "province_id": province, "holding_type": kind,
                                 "holder": integer(barony_title.get("holder"))})
        row = {"title_id": identity, "key": key, "holder": integer(title.get("holder")),
               "in_player_realm": states[identity]["in_player_realm"],
               "realm_membership_complete": membership["realm"]["complete"],
               "same_dynasty": None if family_factors[identity] is None else identity in same_dynasty,
               "family_factor": None if family_factors[identity] is None else fmt(family_factors[identity]),
               "development": fmt(development) if development is not None else None,
               "control": fmt(control) if control is not None else None,
               "completed_holdings": completed if holding_known else None,
               "holding_sources": holding_rows,
               "county_selected_fields": county}
        if development is not None and 0 <= development and holding_known and completed > 0:
            q = 1 + D(".5") * min(development / 20, D(2)) + D(".25") * min(max(completed - 1, 0), 4)
            q_by_id[identity] = q
            row["q_structural"] = fmt(q)
        else:
            unresolved.append(key + ":finished_holdings_or_development")
        if control is not None and 0 <= control <= 100:
            controls[identity] = control / 100
        else:
            unresolved.append(key + ":control")
        selected.append(row)
    realm_values = []
    if membership["realm"]["complete"] and all(identity in q_by_id and identity in controls for identity in owned):
        for identity in owned:
            realm_values.append(q_by_id[identity] * (D(".25") + D(".75") * controls[identity]))
        upper = sum(realm_values, D(0))
        unoccupied = all(raw.get("holding.type") in {None, "none"} or
                         ("occupant" not in raw and "nonunique:occupant" not in raw)
                         for county in selected if county["in_player_realm"]
                         for holding in county["holding_sources"]
                         for raw in [projection.provinces.get(holding["province_id"], {})])
        metrics["Q_realm"] = bounded_observation("Q_realm", upper if unoccupied else upper / 2, upper, source_id,
            "county.development/control + province.holding.type + static county/barony/province mapping",
            "存在occupant但敌对归属未闭合，保留真实不确定范围")
        denominator = sum((q_by_id[identity] for identity in owned), D(0))
        if denominator > 0:
            control_average = sum((q_by_id[i] * controls[i] for i in owned), D(0)) / denominator
            metrics["control_average"] = observation("control_average", control_average,
                                                     source_id, "q_weighted_county_control")
    baseline_lower, baseline_upper, baseline_cap_known = D(0), D(0), True
    for row in static.get("baseline_counties", []):
        dev = numeric(row.get("development"))
        control = numeric(row.get("control"))
        if dev is None or control is None or row.get("realm_membership_complete", True) is not True:
            baseline_cap_known = False
            break
        qmin = 1 + D(".5") * min(dev / 20, D(2))
        multiplier = D(".25") + D(".75") * control / 100
        baseline_lower += qmin * multiplier / 2
        baseline_upper += (qmin + 1) * multiplier
    dynasty_realm_ready = all(states[i]["in_player_realm"] is not None for i in same_dynasty)
    if (membership["dynasty"]["complete"] and dynasty_realm_ready and baseline_cap_known and baseline_lower > 0
            and all(i in q_by_id for i in same_dynasty)):
        inside, outside = D(0), D(0)
        for identity, title in same_dynasty.items():
            contribution = q_by_id[identity] * family_factors[identity]
            if identity in owned:
                inside += contribution
            else:
                outside += contribution / 2
        lower = inside + min(outside, 2 * baseline_lower)
        upper = inside + min(outside, 2 * baseline_upper)
        metrics["K_dynasty"] = bounded_observation("K_dynasty", lower, upper, source_id,
            "deduplicated county holders + house ancestry + structural q",
            "宗族境外上限依开局Q范围保守计算")
    detail = {"actor_id": actor, "founder_character_id": founder,
              "actor_house_id": actor_house, "founder_house_id": h0, "dynasty_anchor_id": dynasty,
              "realm_county_count": len(owned) if membership["realm"]["complete"] else None,
              "known_realm_county_count": len(owned),
              "county_membership_audit": membership,
              "realm_counties": [row for row in selected if row["in_player_realm"]],
              "dynasty_counties": [row for row in selected if row["same_dynasty"]],
              "dynasty_county_count": len(same_dynasty) if membership["dynasty"]["complete"] else None,
              "known_dynasty_county_count": len(same_dynasty), "unresolved_family_county_ids": family_unknown,
              "founding_anchor_source": static.get("founding_anchor_source", source_id),
              "unresolved_county_inputs": unresolved,
              "static_map": static_pin, "occupation_semantics_complete": metrics["Q_realm"]["availability"] == "observed",
              "rebel_war_semantics_complete": False,
              "selected_houses": {str(k): row for k, row in projection.houses.items()
                                  if k == h0 or (dynasty is not None and integer(row.get("dynasty")) == dynasty)}}
    if (dynasty in projection.dynasties and projection.unknown_key_fields == 0
            and "incomplete:perk" not in projection.dynasties[dynasty]):
        perks = projection.dynasties[dynasty].get("perk", "").split()
        metrics["legacy_ranks"] = observation("legacy_ranks", len(set(perks)), source_id,
                                               f"dynasties.dynasties.{dynasty}.perk (unique canonical keys)")
    own_defence, war_audit = player_war_defence(player, projection.wars, actor=actor)
    if (own_defence is None and war_audit["reason"] == "MISSING_LIST" and projection.unknown_key_fields == 0
            and projection.war_containers and not projection.war_layout_unknown
            and all(integer(war.get("casus_belli.defender")) is not None
                    and "nonunique:casus_belli.defender" not in war for war in projection.wars.values())):
        own_defence = any(integer(war["casus_belli.defender"]) == actor for war in projection.wars.values())
        war_audit = {"method": "independent_complete_world_war_roster", "known": True,
                     "own_defence": own_defence, "reason": "ALL_WORLD_CB_DEFENDERS_VERIFIED"}
    detail["player_war_scope"] = {**war_audit, "source_ref": source_id}
    if projection.unknown_key_fields == 0 and own_defence is not None:
        if not own_defence:
            metrics["rebel_share"] = observation("rebel_share", 0, source_id,
                war_audit["method"] + ": player is no CB defender; anti-liege war excluded")
            detail["rebel_war_semantics_complete"] = True
        else:
            metrics["control_average"] = observation("control_average", None, source_id, None,
                reason="存在本方防守战争，需核对CB及战前县集合后才能闭合治理集合G")
    if family_unknown:
        metrics["K_dynasty"]["unavailable_reason"] = "县持有人house存在冲突或固定T0锚未知；未将其当作宗族外0"
        metrics["dynasty_county_count"]["unavailable_reason"] = metrics["K_dynasty"]["unavailable_reason"]
    for name, value in (("realm_county_count", detail["realm_county_count"]), ("dynasty_county_count", detail["dynasty_county_count"]),
                        ("house_anchor_id", h0), ("dynasty_anchor_id", dynasty)):
        if value is not None:
            ref = static.get("founding_anchor_source", source_id) if name in {"house_anchor_id", "dynasty_anchor_id"} else source_id
            metrics[name] = observation(name, value, ref, "fixed T0 anchor" if name in {"house_anchor_id", "dynasty_anchor_id"} else "deduplicated saved title/house identity")
    for scope, name in (("realm", "realm_county_count"), ("dynasty", "dynasty_county_count")):
        audit = membership[scope]
        if not audit["complete"]:
            metrics[name] = (bounded_observation(name, D(audit["count_lower"]), D(audit["count_upper"]),
                source_id, "saved-county-membership-audit/v1:" + scope, "county_membership_incomplete")
                if scope == "realm" and audit["count_upper"] is not None else observation(name, None, source_id,
                    "saved-county-membership-audit/v1:" + scope, reason="county_census_or_founding_scope_unavailable"))
    if not membership["realm"]["complete"]:
        for name in ("Q_realm", "control_average"):
            metrics[name] = observation(name, None, source_id, "saved-county-membership-audit/v1:realm",
                                        reason="realm_county_membership_incomplete")
    if not membership["dynasty"]["complete"] or not dynasty_realm_ready:
        metrics["K_dynasty"] = observation("K_dynasty", None, source_id, "saved-county-membership-audit/v1:dynasty",
                                          reason="dynasty_or_territorial_discount_membership_incomplete")
    saved_date = projection.metadata.get("date", "0.1.1")
    def date_parts(text):
        try:
            return tuple(int(part) for part in text.split("."))
        except ValueError:
            return (9999, 1, 1)
    branches = {identity: row for identity, row in detail["selected_houses"].items()
                if integer(identity) != h0 and integer(row.get("parent_dynasty_house")) is not None
                and date_parts(row.get("found_date", "9999.1.1")) <= date_parts(saved_date)}
    if dynasty is not None:
        metrics["active_family_branches"] = observation("active_family_branches", len(branches),
                                                       source_id, "same dynasty established cadet houses")
    if static_pin:
        additional = [{**static["source"], "machine_id": static["machine_id"],
                       "observed_at_utc": static["observed_at_utc"]},
                      {"id": "static_title_map", **static_pin, "machine_id": static["machine_id"],
                       "observed_at_utc": static["observed_at_utc"],
                       "sha_basis": "bounded_derived_title_map_metadata"}]
        metrics["Q_realm"]["additional_sources"] = additional
    facts = [{"label_zh": "本国实际统治县", "value_text": str(len(owned)), "source_refs": [source_id]},
             {"label_zh": "固定家族／宗族", "value_text": f"house {h0} / dynasty {dynasty}", "source_refs": [source_id]}]
    if not membership["realm"]["complete"]:
        facts[0]["value_text"] = f"已确认{len(owned)}县；成员关系未闭合，不能据此计算失地"
    if metrics["gold"]["availability"] == "observed":
        facts.insert(1, {"label_zh": "保存时金币", "value_text": metrics["gold"]["value"] + " 金",
                         "source_refs": [source_id]})
    return metrics, detail, facts
