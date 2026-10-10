"""Frozen pre-diagnostic pure guard for regression comparison only.

Source: shared host05717072b, inherited byte-exact by Csr13.
Host SHA256: d0e2c7a1d9d0febd7c8d9e1a2c111c2dc2d37cca274c63228d113d1b5867156e.
This is a test fixture, not a runtime import or current live evidence.
"""

def campaign_pause_frame_binding(snapshot: object, *, allow_running: bool = False,
                                 allowed_event_instance: int | None = None,
                                 allow_pause_transition: bool = False) -> dict[str, object]:
    """Bind a complete campaign frame; heartbeat is only an owner guard."""
    if not isinstance(snapshot, dict):
        raise RuntimeError("campaign pause readback lacks a complete snapshot")
    diagnostics = snapshot.get("diagnostics")
    played = snapshot.get("played_character")
    if not isinstance(diagnostics, dict) or not isinstance(played, dict):
        raise RuntimeError("campaign pause readback lacks native identity")
    hello = diagnostics.get("hello")
    heartbeat = diagnostics.get("last_heartbeat")
    mailbox = heartbeat.get("main_thread_query_mailbox_v1") if isinstance(heartbeat, dict) else None
    if not isinstance(hello, dict) or not isinstance(mailbox, dict):
        raise RuntimeError("campaign pause readback lacks the actual owner")
    expected = {"expected_ck3_version": "1.20.0.4",
                "expected_ck3_sha256": "98702F88A547CDE2EAF29A85F93B85F68EE4CF8148336A4F7AFAEB75319DD518",
                "game_adapter_id": "ck3-1.20.0.4-msvc-x64", "ck3_build_match": True}
    if any(type(hello.get(k)) is not type(v) or hello[k] != v for k, v in expected.items()):
        raise RuntimeError("campaign pause readback crossed exact native build identity")
    pid, generation, actor = diagnostics.get("bridge_pid"), diagnostics.get("connection_generation"), played.get("character_id")
    numbers = {"pid": (pid, 1, 2**32 - 1), "generation": (generation, 1, 2**64 - 1),
               "actor": (actor, 1, 2**31 - 1), "date": (snapshot.get("date_raw"), 1, 2**31 - 1),
               "revision": (snapshot.get("revision"), 1, 2**64 - 1), "native_revision": (snapshot.get("native_revision"), 1, 2**64 - 1),
               "local_player": (snapshot.get("local_player_id"), 0, 2**31 - 1), "speed": (snapshot.get("speed"), 1, 5),
               "owner": (mailbox.get("owner_tid"), 1, 2**32 - 1), "pump": (mailbox.get("owner_verified_pump_epochs"), 1, 2**64 - 1),
               "rejections": (diagnostics.get("rejected_state_snapshot_count"), 0, 2**64 - 1)}
    if any(type(v) is not int or not lo <= v <= hi for v, lo, hi in numbers.values()):
        raise RuntimeError("campaign pause readback has malformed identity or clock")
    if allowed_event_instance is not None:
        event = snapshot.get("active_event")
        if (type(allowed_event_instance) is not int or allowed_event_instance <= 0
                or not isinstance(event, dict) or type(event.get("instance_id")) is not int
                or event["instance_id"] != allowed_event_instance):
            raise RuntimeError("campaign pause readback lost the explicitly admitted event instance")
    running = (allow_running is True and snapshot.get("paused") is False
               and mailbox.get("ready") is False)
    pause_transition = (allow_pause_transition is True and running and mailbox.get("paused") is True
                        and mailbox.get("paused_main_thread_observed") is False
                        and type(mailbox.get("consecutive_verified")) is int
                        and mailbox["consecutive_verified"] == 0)
    if running and (snapshot["speed"] != 1
            or type(hello.get("connection_generation")) is not int or hello["connection_generation"] != generation
            or mailbox.get("application_main_observed") is not True
            or (mailbox.get("paused") is not False and not pause_transition)
            or mailbox.get("paused_main_thread_observed") is not False or type(mailbox.get("ready")) is not bool
            or type(mailbox.get("consecutive_verified")) is not int or mailbox["consecutive_verified"] < 0):
        raise RuntimeError("campaign pause readback lacks the complete running owner stamp")
    if (snapshot.get("episode_projection") != "native_campaign" or snapshot.get("backend_id") != "native-headless"
            or snapshot.get("source") != "injected-dll-named-pipe" or snapshot.get("map_ready") is not True
            or type(snapshot.get("format_version")) is not int or snapshot["format_version"] != 1
            or snapshot.get("complete_snapshot") is False
            or type(snapshot.get("paused")) is not bool or played.get("alive") is not True
            or (snapshot.get("active_event") is not None and allowed_event_instance is None)
            or snapshot.get("one_life_terminal_reason") is not None
            or snapshot.get("snapshot_id") != "native:" + str(snapshot["native_revision"])
            or diagnostics.get("connected") is not True or diagnostics.get("semantic_state_available") is not True
            or diagnostics.get("last_error") is not None or diagnostics.get("transport_fatal_error") is not None
            or type(hello.get("pid")) is not int or hello["pid"] != pid
            or type(heartbeat.get("pid")) is not int or heartbeat["pid"] != pid
            or not isinstance(diagnostics.get("pipe_name"), str) or not diagnostics["pipe_name"]
            or mailbox.get("installed") is not True or (mailbox.get("ready") is not True and not running)
            or mailbox.get("stop") is not False or type(mailbox.get("failure")) is not int or mailbox["failure"] != 0
            or type(mailbox.get("current_tid")) is not int or mailbox["current_tid"] != mailbox["owner_tid"]
            or mailbox.get("stamp_read_success") is not True or type(mailbox.get("date_raw")) is not int
            or mailbox["date_raw"] != snapshot["date_raw"]):
        raise RuntimeError("campaign pause readback lost the complete same-owner frame")
    return {"identity": (pid, generation, actor, snapshot["local_player_id"], snapshot["speed"],
                         diagnostics["pipe_name"], mailbox["owner_tid"], snapshot.get("pending_character_interaction")),
            "date": snapshot["date_raw"], "revision": snapshot["revision"], "native_revision": snapshot["native_revision"],
            "pump": mailbox["owner_verified_pump_epochs"], "rejections": diagnostics["rejected_state_snapshot_count"],
            "pause_transition": pause_transition}
