"""Bind existing writer operations to the original common CaseClient owner.

No host/client construction, sampling enable, debugger start or SDK call at import.
The caller supplies its existing Root DR-window guard; no new authorization schema.
"""
from pathlib import Path
import ctypes
from ctypes import wintypes
import hashlib
import json
import re

CASH_TOOL = "ck3_query_war_cash_current_resources_private_v1"


def need(ok, why):
    if not ok:
        raise ValueError(why)


def read_pin(value, limit=8 * 1024 * 1024):
    path = Path(value["path"])
    raw = path.read_bytes()
    need(len(raw) <= limit and len(raw) == value["bytes"]
         and hashlib.sha256(raw).hexdigest() == value["sha256"], "Pinned common input differs")
    return json.loads(raw.decode("utf-8-sig"))


def write_new(path, value):
    raw = (json.dumps(value, ensure_ascii=False, indent=2) + "\n").encode("utf-8")
    need(len(raw) <= 3 * 1024 * 1024, "Existing writer-admission input bound exceeded")
    with Path(path).open("xb") as stream:
        stream.write(raw)
    return {"path": str(Path(path).resolve()), "bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest()}


def retained_creation_filetime(client):
    """Exact FILETIME from the already retained common handle, never float conversion."""
    need(client._handle is not None and client._process is not None, "Original retained common process required")
    fn = client._kernel.GetProcessTimes
    fn.argtypes = [ctypes.c_void_p] + [ctypes.POINTER(wintypes.FILETIME)] * 4
    fn.restype = wintypes.BOOL
    created, exited, kernel, user = (wintypes.FILETIME() for _ in range(4))
    need(bool(fn(client._handle, ctypes.byref(created), ctypes.byref(exited),
                 ctypes.byref(kernel), ctypes.byref(user))), "Retained process FILETIME read failed")
    return (int(created.dwHighDateTime) << 32) | int(created.dwLowDateTime)


class CommonPackets:
    def __init__(self, context, client, packet_root, *, machine):
        self.context, self.client, self.machine = context, client, machine
        need(type(machine) is str and machine not in ("", "unknown"), "Actual common machine identity required")
        self.root = Path(packet_root)
        need(self.root.resolve().is_relative_to(Path(context["output"]).resolve()),
             "Writer views belong to this same common case output")
        self.root.mkdir(parents=True, exist_ok=True)

    def request(self, identifier, tool, arguments, timeout=20):
        need(re.fullmatch(r"[A-Za-z][A-Za-z0-9_-]{0,100}", identifier) is not None, "Bounded unique common ID required")
        path = self.root / (identifier + ".common-view.json")
        need(not path.exists(), "Original common control view exists; never replay")
        step = {"id": identifier, "tool": tool, "args": arguments, "fresh_revision": False,
                "continue_on_error": True}
        # Same owner, same public queue. Errors remain RED but do not close the
        # shared host before the Root operator can converge the attached watcher.
        rows = self.client.execute_plan([step], identifier, timeout=timeout)
        original = Path(self.client.output) / (identifier + ".actual-results.json")
        raw = original.read_bytes()
        need(len(raw) <= 3 * 1024 * 1024, "Original common row exceeds writer admission bound")
        saved = json.loads(raw.decode("utf-8-sig"))
        need(saved.get("rows") == rows and len(rows) == 1 and rows[0].get("id") == identifier,
             "Original common result row differs or is ambiguous")
        row = rows[0]
        body = row.get("result")
        error = row.get("ok") is not True or bool(row.get("error"))
        envelope = {"machine_id": self.machine,
                    "request": {"request_id": identifier, "tool": tool, "arguments": arguments},
                    "is_error": error, "body": body,
                    "transport_origin": "derived_common_case_control_row_not_original_SDK_transport",
                    "common_original": {"path": str(original.resolve()), "bytes": len(raw),
                                        "sha256": hashlib.sha256(raw).hexdigest(), "pointer": "/rows/0/result"},
                    "common_row_ok": row.get("ok"), "common_row_error": row.get("error")}
        view = write_new(path, envelope)
        need(not error and type(body) is dict, "Common control failed; preserved view " + view["path"] + "; never replay")
        if tool == "ck3_take_snapshot":
            self.client.validate_frame(body, require_event_free=False)
        return body, view


def collect_current_context(context, client, *, machine, prefix, packet_root,
                            _created_reader=retained_creation_filetime,
                            owner_binding_mode="episode_bound_v1"):
    """Root-only readonly pair; no sampling enable or observer admission inferred."""
    client.guard()
    client.retain_process()
    relay = CommonPackets(context, client, packet_root, machine=machine)
    before, before_pin = relay.request(prefix + "-before", "ck3_take_snapshot", {"include_native_command_history": False})
    cash, cash_pin = relay.request(prefix + "-cash", CASH_TOOL,
                                   {"expected_revision": before["revision"], "payment_sampling": "query"})
    journal = cash.get("war_payment_observations_v1") or {}
    session, sampling = journal.get("current_session") or {}, journal.get("sampling") or {}
    actor = before["played_character"]["character_id"]
    episode=before.get("episode_run_id")
    need(owner_binding_mode in ("episode_bound_v1","native_campaign_owned_no_load_v2"),
         "Explicit known writer owner mode required")
    ordinary=owner_binding_mode=="native_campaign_owned_no_load_v2"
    if ordinary:
        need(episode is None and before.get("episode_projection")=="native_campaign",
             "Ordinary owner must preserve the original null episode")
        local_player=before.get("local_player_id")
        mailbox=(before["diagnostics"].get("last_heartbeat") or {}).get("main_thread_query_mailbox_v1") or {}
        game_state=mailbox.get("game_state")
        need(type(local_player) is int and 0<local_player<(1<<32)
             and type(game_state) is int and 0<game_state<=0x7ffffffff000,
             "Actual ordinary snapshot local-player/GameState required")
    else:
        need(type(episode) is str and bool(episode.strip()),"Legacy real nonempty episode required")
    need(before["diagnostics"]["bridge_pid"] == client._process["pid"], "Common OS/native PID differs")
    result = {"status": "COMMON_INPUTS_COLLECTED_NOT_OBSERVER_ADMISSION",
              "before_response": before_pin, "cash_response": cash_pin,
              "common_retained_process": dict(client._process),
              "expected": {"pid": client._process["pid"], "created": _created_reader(client),
                           "generation": before["diagnostics"]["connection_generation"],
                           "window": session.get("controlled_window_id"), "epoch": sampling.get("epoch"),
                           "character_id": actor, "revision": before["revision"],
                           "native_revision": before["native_revision"], "date": before["date_raw"],
                           "episode": episode, "machine": machine},
              "current_raw_context_v1_present": "current_raw_context_v1" in cash,
              "actual_controlled_window_admitted": journal.get("controlled_window_admitted"),
              "actual_payment_capture_enabled": sampling.get("capture_enabled"),
              "sampling_actions": 0, "observer_started": False}
    if ordinary:
        result["owner_binding_mode"]=owner_binding_mode
        result["expected"].update(game_state_identity_witness=game_state,local_player_id=local_player)
    result["receipt"] = write_new(Path(packet_root) / (prefix + "-INPUTS.actual.json"), result)
    return result


def bind_legacy_driver(legacy, context, client, *, machine, root_window_guard=None,
                       _created_reader=retained_creation_filetime):
    """Root passes one already loaded/pinned writer module and its original client.

    The original explicit Root 45s-window guard is supplied later by Root; None
    never permits prepare/observe. We neither construct nor interpret a new cap.
    """
    def config(value):
        cfg = read_pin(value, 65536)
        need(cfg.get("schema") == "xar.e04.common-cd-writer-driver-input.v1", "Common writer input required")
        need(re.fullmatch(r"r207-[a-z0-9-]{1,55}", cfg.get("request_prefix", "")) is not None,
             "Use a new R207 request prefix")
        need(Path(cfg["control_root"]).resolve().is_relative_to(Path(context["output"]).resolve()),
             "Writer control belongs to this common case")
        return cfg

    class BoundRuntime:
        def __init__(self, cfg):
            need(callable(root_window_guard), "Root has not supplied its independent 45s DR-window authorization")
            self.cfg, self.repo = cfg, Path(context["repo_root"]).resolve()
            self.run = Path(context["run_dir"])
            x = cfg["watch"]["expected"]
            self.c = {"expected_start_date_raw": x["date"], "maximum_days": 1}
            self.guard()
            need(client._process is not None and client._handle is not None, "Original retained process required")
            need(type(x["pid"]) is int and x["pid"] == client._process["pid"]
                 and type(x["created"]) is int and x["created"] == _created_reader(client),
                 "Current common PID/exact FILETIME differs")
            need(client._binding is not None and tuple(client._binding) == (x["pid"], x["generation"], x["character_id"]),
                 "Existing common native binding differs")
            need(x["machine"] == machine
                 and Path(cfg["watch"]["repo"]).resolve() == self.repo
                 and Path(cfg["watch"]["python"]).resolve() == Path(client.selection.locations["python"]).resolve(),
                 "Common machine/source locations differ")
            self.packets = CommonPackets(context, client, cfg["common_packet_root"], machine=machine)

        def guard(self):
            client.guard()
            root_window_guard(context, client, self.cfg)

        def request(self, identifier, tool, arguments, timeout=20):
            self.guard()
            return self.packets.request(identifier, tool, arguments, timeout)

    legacy.load_config = config
    legacy.RootRuntime = BoundRuntime
    return legacy
