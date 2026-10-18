"""Offline actual CK3 writer JSONL projection. Never attaches, queries or writes game memory."""
from pathlib import Path
import argparse
import datetime as dt
import hashlib
import importlib.util
import json
import sys

import importlib.util as _owner_import
_owner_spec = _owner_import.spec_from_file_location('_writer_owner_binding_v2', Path(__file__).with_name('owner_binding.py'))
owner = _owner_import.module_from_spec(_owner_spec)
_owner_spec.loader.exec_module(owner)

OFFSETS = None
integer = None
require = None
REGISTERS = {"rax","rbx","rcx","rdx","r8","r9","r10","r11","rsi","rdi","rbp","rsp"}
LIMIT = 8 * 1024**2


COPY_SOURCE_SHA = "ffebf7d960edb76b71d2456b7f8722cc09092952b41c565f648410b42a47dede"
COPY_PROLOGUE_HEX = "48895c2410488974241848897c2420554154415541564157488d6c24b04881ec50010000"

def project_known_copy_caller(row, start, thread_generation):
    """Optional raw stack observation. It grants no caller business semantics."""
    leaf = row.get("known_copy_caller_v1")
    if leaf is None:
        return None
    def need(ok, message):
        if not ok:
            raise ValueError(message)
    def u64(value):
        return type(value) is int and 0 <= value < (1 << 64)
    need(type(leaf) is dict, "Known-copy caller leaf shape")
    need((row["slot"], row["RIP_after_rva"]) in ((0, 0x28A645B), (1, 0x28A6466)),
         "Caller capture is not at a source-qualified store post-PC")
    need(leaf["source_entry_rva"] == "28A63E0" and leaf["source_raw_sha256"] == COPY_SOURCE_SHA,
         "Caller capture source differs")
    need(type(leaf["capture_ordinal"]) is int and 1 <= leaf["capture_ordinal"] <= 8,
         "Caller capture ordinal")
    need(type(leaf["admission_generation"]) is int
         and leaf["admission_generation"] == start["admission_generation"], "Caller admission generation differs")
    for key in ("prologue_matches", "frame_relation_matches", "register_context_matches",
                "identity_after", "read_before_complete", "read_after_complete", "return_stable"):
        need(type(leaf[key]) is bool, "Caller read flag: " + key)
    regs = row["registers"]
    frame = regs["rsp"] <= (1 << 64)-1-0x178 and regs["rbp"] <= (1 << 64)-1-0x78 and regs["rsp"]+0x178 == regs["rbp"]+0x78
    obj = regs["r9"] == row["context"] and regs["rsi"] == row["character"]
    need(leaf["frame_relation_matches"] is frame and leaf["register_context_matches"] is obj,
         "Caller source frame/object proof differs")
    need(leaf["return_slot_address"] == (regs["rsp"]+0x178 if frame else None), "Caller return slot differs")
    for complete, value in (("read_before_complete", "return_before"), ("read_after_complete", "return_after")):
        need(u64(leaf[value]) if leaf[complete] else leaf[value] is None, "Caller raw read availability differs")
    stable = leaf["prologue_matches"] and frame and obj and leaf["identity_after"] and leaf["read_before_complete"] and leaf["read_after_complete"] and leaf["return_before"] == leaf["return_after"] and leaf["return_before"] != 0
    need(leaf["return_stable"] is stable, "Caller return stability differs")
    address = leaf["return_before"] if stable else None
    base, size = start["module_base"], start["module_size"]
    rva = address-base if address is not None and base <= address < base+size else None
    need(leaf["candidate_return_absolute"] == address and leaf["candidate_return_rva"] == rva,
         "Caller raw/RVA mapping differs")
    return dict(source_entry_rva="28A63E0", source_raw_sha256=COPY_SOURCE_SHA,
                caller_return_absolute=address, caller_return_rva=rva,
                source_status="source_qualified_return_slot" if stable else "unavailable_return_slot",
                return_slot_address=leaf["return_slot_address"], raw_read_before=leaf["return_before"],
                raw_read_after=leaf["return_after"], return_stable=stable,
                prologue_matches=leaf["prologue_matches"], identity_after=leaf["identity_after"],
                thread_generation=thread_generation, admission_generation=start["admission_generation"],
                capture_ordinal=leaf["capture_ordinal"], instruction_start=None,
                known_c_d_producer=False, maintenance_attribution="unclosed")

def configure(repo):
    global OFFSETS, integer, require
    repo = Path(repo).resolve()
    sys.dont_write_bytecode = True
    sys.path[:0] = [str(repo), str(repo/"ck3_autonomous_player/src")]
    path = repo/"ck3_autonomous_player/native_bridge/research/maintenance_writer_cold_12004/consume_writer_cold.py"
    spec = importlib.util.spec_from_file_location("_writer_existing_cold_defs", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    OFFSETS, integer, require = module.OFFSETS, module.integer, module.require

def bounded(path):
    path = Path(path)
    if path.stat().st_size > LIMIT:
        raise ValueError("Explicit input exceeds 8 MiB")
    return path.read_bytes()

def digest(data):
    return hashlib.sha256(data).hexdigest()

def packet(data):
    value = json.loads(data.decode("utf-8-sig"))
    require(type(value) is dict and value["is_error"] is False and type(value["body"]) is dict,
            "Original completed packet body/error missing")
    structured = value.get("sdk_result",{}).get("structured_content")
    require(structured is None or structured == value["body"], "Original SDK/body differs")
    return value

def bind_inputs(admission, cash_bytes, before_bytes):
    from xar_autoplayer.bridge.war_cash_current_raw_context_v1 import validate_current_raw_context_v1
    from xar_autoplayer.bridge import war_payment_observations_v1 as payment
    from xar_autoplayer.bridge.nonwar_private_build import private_native_build_identity
    from xar_autoplayer.bridge.version_identity import CK3_12004
    require(admission["schema"] in ("xar.maintenance.writer_pc.future-admission.v1","xar.maintenance.writer_pc.future-admission.v2"),
            "Existing Root admission schema required")
    require(admission["known_producer"] is False and admission["maintenance_attribution"] == "unclosed",
            "Admission business attribution elevated")
    cash_packet, before_packet = packet(cash_bytes), packet(before_bytes)
    machine = admission["machine_id"]
    require(cash_packet["machine_id"] == before_packet["machine_id"] == machine, "Evidence machine differs")
    require(before_packet["request"]["tool"] == "ck3_take_snapshot"
            and cash_packet["request"]["tool"] == "ck3_query_war_cash_current_resources_private_v1",
            "Original independent before/cash tools differ")
    require(cash_packet["request"]["arguments"]["payment_sampling"] == "query",
            "Existing query mode required")
    snapshot, cash = before_packet["body"], cash_packet["body"]
    require(cash_packet["request"]["arguments"]["expected_revision"] == snapshot["revision"],
            "Original cash request is not bound to independent before")
    require(private_native_build_identity(snapshot) == CK3_12004, "Exact actual4 frame absent")
    validate_current_raw_context_v1(cash, snapshot=snapshot)
    require("current_raw_context_v1" in cash, "Fresh optional current raw leaf absent")
    leaf = cash["current_raw_context_v1"]
    require(leaf == admission["raw_leaf"] and leaf["admission_ready"] is True
            and leaf["actor_identity_stable"] is True and leaf["same_frame_ready"] is True,
            "Root admission/current raw cache differs or is not ready")
    expected = admission["expected_root_identity"]
    journal = payment.normalize_journal(cash[payment.JOURNAL_KEY],snapshot=snapshot,machine_id=machine)
    session, sampling = journal["current_session"], journal["sampling"]
    for name, value in expected.items():
        integer(value, "Root "+name, 1)
        require(session[name] == value, "Root journal binding differs: "+name)
    require(snapshot["diagnostics"]["bridge_pid"] == expected["pid"]
            and snapshot["diagnostics"]["connection_generation"] == expected["connection_generation"]
            and snapshot.get("episode_run_id") == admission["expected_episode"],
            "Root snapshot process/generation/episode differs")
    require(sampling["epoch"] == admission["expected_payment_epoch"]
            and journal["controlled_window_admitted"] is True
            and session["same_owned_process_no_load_window"] is True,
            "Root original payment window/epoch absent")
    require(journal["installed"] is True and journal["install_failure_flags"] == 0
            and journal["read_complete"] is True and sampling["available"] is True
            and sampling["capture_enabled"] is True and sampling["busy"] is False
            and sampling["active_captures"] == 0, "Original admission journal is not ready")
    pins = {x["sha256"] for x in admission["source_packet_pins"]}
    require(digest(cash_bytes) in pins and digest(before_bytes) in pins,
            "Original packet bytes differ from Root admission")
    ordinary=admission["schema"] == "xar.maintenance.writer_pc.future-admission.v2"
    bound=admission.get("owner_binding")
    if ordinary:
        owner.validate(bound)
        require(bound == owner.qualify(owner.ORDINARY,admission["expected_episode"],snapshot,journal,leaf,
                expected_game_state=bound["game_state_identity_witness"],expected_local_player_id=bound["local_player_id"]),
                "Actual ordinary owner binding differs")
    else:
        owner.qualify(owner.EPISODE_BOUND,admission["expected_episode"],snapshot,journal,leaf)
        require(bound is None,"Legacy admission cannot carry a v2 owner binding")
    result=dict(machine_id=machine, pid=expected["pid"], created=expected["process_create_time_100ns"],
                full_id=expected["player_character_full_id"], character=leaf["character"],
                context=leaf["values"]["context_identity_before"],
                admission_window_id=expected["controlled_window_id"],
                admission_payment_epoch=admission["expected_payment_epoch"],
                admission_generation=expected["connection_generation"],
                admission_native_revision=leaf["snapshot_revision"],admission_date_raw=leaf["date_raw"],
                admission_episode=admission["expected_episode"],admission_cash_packet_sha256=digest(cash_bytes),
                current_raw_cache=leaf)
    if ordinary:result["admission_owner_binding"]=bound
    return result

def project(rows, binding):
    require(type(rows) is list and rows, "Raw rows absent")
    start = rows[0]
    ordinary="admission_owner_binding" in binding
    require(start["kind"] == "start" and start["schema"] == ("xar.maintenance.writer_pc.cold.v2" if ordinary else "xar.maintenance.writer_pc.cold.v1"),
            "Existing native raw format required")
    require(start["synthetic"] is False and start["CK3_observed"] is True,
            "Synthetic/cold fixture cannot receive actual CK3 credit")
    require(start["maintenance_attribution"] == "unclosed", "Raw attribution elevated")
    for key in ["machine_id","pid","created","full_id","character","context","admission_window_id",
                "admission_payment_epoch","admission_generation","admission_native_revision",
                "admission_date_raw","admission_episode","admission_cash_packet_sha256"]:
        require(type(start[key]) is type(binding[key]) and start[key] == binding[key],
                "Raw/Root binding differs: "+key)
    if ordinary:
        require(start.get("owner_binding") == binding["admission_owner_binding"]
                and start.get("native_owner_memory_verified") is True,
                "Native ordinary owner readback or v2 source binding differs")
    else:
        require(start.get("owner_binding") is None,"Legacy raw cannot inject ordinary ownership")
    require(start["field_offsets"] == list(OFFSETS)
            and start["DR7_write_len8_mask"] == 0x99990055, "Actual four write/LEN8 declaration differs")
    context = integer(start["context"], "context", 1, 0x7ffffffff000)
    require(context % 8 == 0, "Current context not aligned")
    base = integer(start["module_base"], "actual module base", 1)
    size = integer(start["module_size"], "actual module size", 1)
    require(start["actual_writer_game_date"] is None, "Admission date relabelled as actual write date")
    last = list(start["initial_values"])
    require(len(last) == 4, "Native initial values missing")
    for value in last:
        integer(value, "initial signed64", -(1<<63), (1<<63)-1)
    terminal = rows[-1] if rows[-1].get("kind") == "terminal" else None
    body = rows[1:-1] if terminal is not None else rows[1:]
    active, generations, restored = {}, {}, {}
    hits, unknown, events, masks, issues, retired = [], [], {}, {}, [], []
    hit_count, qpc = 0, 0
    for index, row in enumerate(body, 2):
        kind = row["kind"]
        if kind == "arm":
            tid = integer(row["thread_id"], "arm thread", 1)
            require(tid not in active, "Thread lifecycle armed twice without actual exit")
            require(type(row["success"]) is bool, "Arm result missing")
            saved, armed = row["saved_debug"], row["armed_debug"]
            require(type(saved) is list and type(armed) is list and len(armed) == 6
                    and len(saved) in (0,6), "Actual arm debug vector shape differs")
            for value in saved+armed:
                integer(value, "debug register")
            generation = generations.get(tid, 0)+1
            generations[tid] = generation
            qualified = row["success"] is True and len(saved) == 6
            qualified = qualified and armed[:4] == [context+x for x in OFFSETS]
            qualified = qualified and armed[5]&0xffff00ff == 0x99990055
            if len(saved) == 6:
                qualified = qualified and saved[:4] == [0]*4 and saved[5]&0xffff00ff == 0
            active[tid] = dict(generation=generation,saved=saved,qualified=qualified)
            if not qualified:
                issues.append("arm_unqualified:"+str(tid)+":"+str(generation))
        elif kind == "thread_exited":
            tid = integer(row["thread_id"], "exited thread", 1)
            owned = active.pop(tid, None)
            retired.append(dict(thread_id=tid,thread_generation=owned["generation"] if owned else None))
        elif kind == "restore":
            tid = integer(row["thread_id"], "restore thread", 1)
            owned = active.get(tid)
            require(owned is not None, "Restore not paired to live arm lifecycle")
            require(type(row["readback"]) is bool and type(row["debug"]) is list
                    and len(row["debug"]) == 6, "Actual restore vector shape differs")
            for value in row["debug"]:
                integer(value, "restored debug register")
            restored[(tid,owned["generation"])] = row["readback"] is True and row["debug"] == owned["saved"]
        elif kind == "raw_field_write_trap":
            tid = integer(row["thread_id"], "writer thread", 1)
            require(tid in active, "Actual writer not paired to live arm")
            slot = integer(row["slot"], "slot", 0, 3)
            require(row["offset"] == OFFSETS[slot] and row["address"] == context+OFFSETS[slot],
                    "Trap field/address differs")
            for key in ["full_id","character","context"]:
                require(type(row[key]) is int and row[key] == start[key], "Trap object differs: "+key)
            ordinal = integer(row["event_ordinal"], "event ordinal", 1)
            hit_count += 1
            require(integer(row["slot_hit_ordinal"], "hit ordinal", 1) == hit_count,
                    "Slot-hit order differs")
            require(ordinal >= max(events,default=0) and slot not in events.setdefault(ordinal,set()),
                    "Repeated or reversed event slot")
            events[ordinal].add(slot)
            now = integer(row["qpc"], "QPC", 1)
            require(now >= qpc, "Raw QPC reverses")
            qpc = now
            pc = integer(row["RIP_after"], "postinstruction PC", 1)
            if base <= pc < base+size:
                require(type(row["RIP_after_rva"]) is int and row["RIP_after_rva"] == pc-base,
                        "Actual module post-PC mapping differs")
            else:
                require(row["RIP_after_rva"] is None, "Foreign PC mapped into CK3")
            require(row["writer_instruction_start"] is None
                    and row["before_basis"] == "last_observed_sample_not_atomic_preinstruction",
                    "Post-PC or before value given invented qualification")
            require(row["synthetic"] is False and row["known_producer"] is False
                    and row["military_attribution"] == "unclosed", "Trap source/business credit elevated")
            require(type(row["registers"]) is dict and set(row["registers"]) == REGISTERS,
                    "Raw source registers missing")
            for value in row["registers"].values():
                integer(value, "source register")
            before = integer(row["before_raw"], "before", -(1<<63), (1<<63)-1)
            after = integer(row["after_raw"], "after", -(1<<63), (1<<63)-1)
            mask = integer(row["DR6"], "DR6")&15
            require(mask&(1<<slot) and (ordinal not in masks or masks[ordinal] == mask),
                    "Actual slot DR6 evidence differs")
            masks[ordinal] = mask
            require(type(row["after_read_complete"]) is bool
                    and type(row["context_identity_stable"]) is bool
                    and type(row["same_value_write"]) is bool, "Actual read flags malformed")
            reasons = []
            if not active[tid]["qualified"]: reasons.append("arm_readback_unqualified")
            if before != last[slot]: reasons.append("last_observed_chain_unclosed")
            if not row["after_read_complete"]: reasons.append("after_read_unknown")
            if not row["context_identity_stable"]: reasons.append("context_changed")
            if row["same_value_write"] is not (before == after): reasons.append("same_value_flag_differs")
            item = dict(raw_line=index,thread_id=tid,thread_generation=active[tid]["generation"],
                        event_ordinal=ordinal,slot_hit_ordinal=hit_count,slot=slot,offset=row["offset"],
                        address=row["address"],character=row["character"],context=row["context"],
                        full_id=row["full_id"],qpc=now,DR6=row["DR6"],RIP_after=pc,
                        RIP_after_rva=row["RIP_after_rva"],writer_instruction_start=None,
                        source_status="unknown",actual_writer_game_date=None,trigger_phase="unknown",
                        before_raw=before,before_basis=row["before_basis"],
                        after_raw=after if row["after_read_complete"] else None,
                        same_value_write=row["same_value_write"],registers=row["registers"],
                        physical_write_qualified=not reasons,unavailable_reasons=reasons,
                        known_producer=False,maintenance_attribution="unclosed")
            item["known_copy_caller_v1"] = project_known_copy_caller(row, start, active[tid]["generation"])
            (unknown if reasons else hits).append(item)
            if row["after_read_complete"] and row["context_identity_stable"]:
                last[slot] = after
        else:
            raise ValueError("Unexpected actual raw row kind: "+str(kind))
    for ordinal, slots in events.items():
        if sum(1<<slot for slot in slots) != masks[ordinal]:
            issues.append("incomplete_multi_slot_event:"+str(ordinal))
    missing_restore = [dict(thread_id=t,thread_generation=v["generation"])
                       for t,v in active.items() if not restored.get((t,v["generation"]),False)]
    cleanup = False
    if terminal is None:
        issues.append("terminal_missing")
    else:
        require(terminal["CK3_observed"] is True and terminal["known_producer"] is False
                and terminal["military_attribution"] == "unclosed"
                and terminal["full_window_all_writes_covered"] is False,
                "Actual terminal source/business credit elevated")
        if terminal["hit_count"] != hit_count: issues.append("terminal_slot_count_differs")
        if terminal["data_event_count"] < max(len(events),max(events,default=0)):
            issues.append("terminal_data_event_count_differs")
        cleanup = (terminal["cleanup_complete"] is True and terminal["restored"] is True
                   and terminal["detached"] is True and terminal["pending_event"] is False
                   and terminal["process_exited"] is False and not missing_restore)
        if not cleanup: issues.append("cleanup_not_proved")
        if terminal["observation_thread_admission_complete"] is not True:
            issues.append("observation_thread_admission_incomplete")
    status = ("ACTUAL_WRITERS_SOURCE_UNKNOWN" if hits else "NO_QUALIFIED_WRITER_IN_FINITE_WINDOW")
    if issues or unknown:
        status = "PARTIAL_" + status
    cache = binding["current_raw_cache"]["values"]
    admission_values = [cache[k] for k in ["value_2c0","value_2c8","value_28","value_30"]]
    return dict(status=status,origin="original_files_bound_to_Root_admission",
                evidence_machine_id=binding["machine_id"],Root_binding=binding,
                qualified_writers=hits,unknown_traps=unknown,
                slot_trap_count=hit_count,qualified_slot_count=len(hits),unknown_slot_count=len(unknown),
                recorded_data_event_count=len(events),same_value_write_count=sum(x["same_value_write"] for x in hits),
                native_initial_values=start["initial_values"],current_cache_values_at_admission=admission_values,
                initial_values_equal_admission_values=start["initial_values"] == admission_values,
                initial_value_difference_is_not_rejection=True,
                terminal=terminal,cleanup_proved=cleanup,missing_or_unproved_live_restores=missing_restore,
                issues=issues,retired_thread_lifecycles=retired,
                finite_window_reason=terminal["reason"] if terminal else "unknown",
                actual_writer_game_date=None,full_window_all_writes_covered=False,
                zero_hit_meaning="No qualified trap retained in this finite interval; no fee/producer absence inferred.",
                known_producer=False,maintenance_attribution="unclosed")

def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ["repo","raw","admission","cash-response","before-response","output"]:
        parser.add_argument("--"+name,type=Path,required=True)
    args = parser.parse_args(argv)
    configure(args.repo)
    require(not args.output.exists(), "Append-only projection output exists")
    sources = {"raw":args.raw,"admission":args.admission,"cash":args.cash_response,"before":args.before_response}
    data = {k:bounded(v) for k,v in sources.items()}
    admission = json.loads(data["admission"].decode("utf-8-sig"))
    binding = bind_inputs(admission,data["cash"],data["before"])
    rows = [json.loads(line) for line in data["raw"].decode("utf-8-sig").splitlines() if line.strip()]
    result = project(rows,binding)
    result.update(recorded_utc=dt.datetime.now(dt.timezone.utc).isoformat(),read_only=True,
                  input_pins={k:dict(path=str(sources[k]),bytes=len(v),sha256=digest(v)) for k,v in data.items()},
                  existing_format="xar.maintenance.writer_pc.cold.v2 ordinary mode" if "admission_owner_binding" in binding else "xar.maintenance.writer_pc.cold.v1 actual mode",
                  runtime_actions_performed=0)
    with args.output.open("x",encoding="utf-8",newline="\n") as f:
        json.dump(result,f,ensure_ascii=False,indent=2)
        f.write("\n")
    print(json.dumps(dict(status=result["status"],qualified_slot_count=result["qualified_slot_count"],
                          unknown_slot_count=result["unknown_slot_count"],cleanup_proved=result["cleanup_proved"],
                          military_attribution="unclosed"),ensure_ascii=True))
    return 0

if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (ValueError,KeyError,TypeError,OSError) as exc:
        print(json.dumps(dict(status="UNUSABLE_INPUT",error=str(exc),runtime_actions_performed=0,
                              known_producer=False,military_attribution="unclosed")),file=sys.stderr)
        raise SystemExit(2)
