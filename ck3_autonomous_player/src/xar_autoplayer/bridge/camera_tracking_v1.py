"""Optional Native30 one-army action tracking; no gameplay transport or polling."""
import ctypes as C
import re

OFFSET, REGION_BYTES, MAGIC, VERSION, CAPACITY = 0x18400, 8192, 0x54434158, 1, 32


class Province(C.Structure):
    _fields_ = [("id", C.c_int32), ("title_key", C.c_char * 128)]


class Request(C.Structure):
    _fields_ = [("request_sequence", C.c_uint32), ("province_count", C.c_uint32),
                ("owner_epoch", C.c_uint64), ("scope_generation", C.c_uint64),
                ("actor", C.c_int32), ("fullarmy_id", C.c_int32),
                ("start_date_raw", C.c_int32), ("max_date_raw", C.c_int32),
                ("provinces", Province * CAPACITY)]


class Result(C.Structure):
    _fields_ = [("request_sequence", C.c_uint32), ("state", C.c_uint32),
                ("owner_epoch", C.c_uint64), ("scope_generation", C.c_uint64),
                ("observed_uptime_ms", C.c_uint64), ("actor", C.c_int32),
                ("fullarmy_id", C.c_int32), ("date_raw", C.c_int32),
                ("province_id", C.c_int32), ("combat_id", C.c_int32),
                ("target_updates", C.c_uint32), ("pending_slot_capacity", C.c_int32),
                ("pending_slots_visited", C.c_int32), ("reader_elapsed_us", C.c_uint64),
                ("reader_reason", C.c_uint32), ("reserved", C.c_uint32)]


class Shared(C.Structure):
    _fields_ = [("magic", C.c_uint32), ("version", C.c_uint32),
                ("byte_size", C.c_uint32), ("provider_pid", C.c_uint32),
                ("capability_sequence", C.c_int32), ("active", C.c_uint32),
                ("owner_epoch", C.c_uint64), ("result_sequence", C.c_int32),
                ("reserved", C.c_uint32), ("request", Request), ("result", Result)]


if ((C.sizeof(Province), C.sizeof(Request), C.sizeof(Result), C.sizeof(Shared))
        != (132, 4264, 80, 4384)
        or (Shared.request.offset, Shared.result.offset) != (40, 4304)
        or OFFSET < 0x18000 + 168 or OFFSET + REGION_BYTES > 131072):
    raise RuntimeError("camera tracking v1 wire layout is incompatible")


def _int(value, minimum=1, maximum=0x7fffffff):
    return type(value) is int and minimum <= value <= maximum


def tracking_intent_v1(payload, index):
    """Bind an actually armed tactical action's own watched army and finite route.

    No native operation occurs. Missing/oversize route mapping stays unsupported,
    rather than pretending an arbitrary title is a continuously tracked subject.
    """
    scope, frame = payload.get("tracking_scope"), payload.get("source_frame", {})
    if not isinstance(scope, dict) or scope.get("state") != "armed":
        return None
    generation, start, end = (scope.get(k) for k in ("generation", "starting_date_raw", "target_date_raw"))
    actor, watched = frame.get("actor_character_id"), scope.get("watch_army_ids")
    if (not _int(generation, maximum=0xffffffffffffffff) or not _int(actor)
            or not _int(start) or not _int(end) or not 0 < end - start <= 30 * 24
            or frame.get("date_raw") != start or not isinstance(watched, list)
            or not watched or len(watched) > 64 or any(not _int(a) for a in watched)):
        return None
    candidates = {}
    for war in payload.get("active_wars") or []:
        for army in war.get("allied_armies") or []:
            army_id = army.get("army_id")
            if (army_id in watched and army.get("controllable") is True
                    and army.get("retreating") is not True):
                previous = candidates.setdefault(army_id, army)
                if previous != army:  # conflicting duplicate DTOs cannot authorize a subject
                    return None
    if not candidates:
        return None
    army = min(candidates.values(), key=lambda a: (a.get("in_combat") is not True, a["army_id"]))
    route = army.get("route_province_ids")
    if route is None:
        route = []
    if not isinstance(route, list) or len(route) > CAPACITY:
        return None
    provinces = [army.get("current_province_id"), *route]
    target = army.get("move_target_province_id")
    if target is not None:
        provinces.append(target)
    if any(not _int(p) for p in provinces):
        return None
    provinces = sorted(set(provinces))
    if not provinces or len(provinces) > CAPACITY:
        return None
    entries = []
    for province in provinces:
        title = index.barony_by_province.get(province)
        if not isinstance(title, str) or not re.fullmatch(r"b_[a-zA-Z0-9_]{1,124}", title):
            return None
        entries.append((province, title))
    return {"mode": "tracked_hotspot", "reason": "armed_own_watched_army",
            "army_id": army["army_id"], "scope_generation": generation,
            "start_date_raw": start, "max_date_raw": end, "provinces": entries}


def read_capability_v1(view, pid):
    address = view + OFFSET
    sequence = C.c_uint32.from_address(address + Shared.capability_sequence.offset).value
    if sequence & 1:
        return None
    # Only copy the 40-byte capability header, never all province/result storage.
    raw = C.string_at(address, Shared.request.offset)
    header = Shared.from_buffer_copy(raw + bytes(C.sizeof(Shared) - len(raw)))
    if sequence != C.c_uint32.from_address(address + Shared.capability_sequence.offset).value:
        return None
    if ((header.magic, header.version, header.byte_size, header.provider_pid)
            != (MAGIC, VERSION, C.sizeof(Shared), pid)
            or header.active != 1 or header.owner_epoch == 0):
        return None
    return header.owner_epoch


def make_request_v1(intent, frame, sequence, epoch):
    request = Request(request_sequence=sequence, owner_epoch=epoch,
                      scope_generation=intent["scope_generation"], actor=frame["actor_character_id"],
                      fullarmy_id=intent["army_id"], start_date_raw=intent["start_date_raw"],
                      max_date_raw=intent["max_date_raw"])
    entries = intent["provinces"]
    if not 0 < len(entries) <= CAPACITY:
        raise ValueError("tracking province whitelist overflow")
    request.province_count = len(entries)
    for i, (province, title) in enumerate(entries):
        if not _int(province) or not re.fullmatch(r"b_[a-zA-Z0-9_]{1,124}", title):
            raise ValueError("invalid tracking province/title")
        request.provinces[i] = Province(province, title.encode("ascii"))
    return request


def latest_tracking_v1(view, binding):
    if not binding:
        return None
    address = view + OFFSET
    seqaddr = address + Shared.result_sequence.offset
    seq = C.c_uint32.from_address(seqaddr).value
    if not seq or seq & 1:
        return None
    result = Result.from_buffer_copy(C.string_at(address + Shared.result.offset, C.sizeof(Result)))
    if seq != C.c_uint32.from_address(seqaddr).value:
        return None
    if any(getattr(result, key) != binding[key] for key in
           ("request_sequence", "owner_epoch", "scope_generation", "actor", "fullarmy_id")):
        return None
    if result.state > 12:
        return None
    return {"schema": "xar.ck3.camera-tracking-actual/v1", **{
        key: getattr(result, key) for key, _ in Result._fields_},
        "actor_character_id": result.actor,
        "status": "submitted" if result.state in {1, 11} else "cancelled" if result.state in {2, 5, 10} else "unavailable",
        "tracking_active": result.state == 1, "camera_postcondition_verified": False,
        "reader_clock_available": result.reader_elapsed_us != 0xffffffffffffffff,
        "continuous_frame_coverage_verified": False, "same_frame_with_gameplay_claim": False}
