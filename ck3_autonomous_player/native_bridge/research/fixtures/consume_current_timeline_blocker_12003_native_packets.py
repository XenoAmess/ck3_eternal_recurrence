"""Consume actual .3 production fixture packets through existing transports.

This uses a memory-only endpoint and sends no SDK, pipe or CK3 commands.
"""
from pathlib import Path
from copy import deepcopy
from types import SimpleNamespace
import argparse
import ast
import hashlib
import importlib.util
import json
import sys


def require(condition, message):
    if not condition:
        raise RuntimeError(message)


def verify_cli_loader_registration(mcp_producer, mcp_source, driver, packet_folder):
    """Execute the producer's real parser -> main load expression -> loader.

    Only the native driver constructor is replaced: no endpoint is opened.
    The current main call is compiled from its actual AST instead of repeating
    its keyword arguments in this fixture.
    """
    flag = "--private-death-succession-modal-continue"
    require(mcp_producer.parser().parse_args([]).private_death_succession_modal_continue
            is False, "Existing private flag default changed")
    args = mcp_producer.parser().parse_args([
        "--driver", "native-headless", "--transport", "stdio",
        "--state-dir", str(packet_folder / "never-opened-state"),
        "--pipe-name", r"\\.\pipe\fixture-never-opened-succession-12003", flag,
        "--succession-lifecycle", "ordinary_campaign_succession",
        "--ordinary-campaign-no-pact",
    ])
    require(args.private_death_succession_modal_continue is True,
            "Actual CLI parser did not enable the existing flag")
    source = mcp_source.read_text(encoding="utf-8-sig")
    main_nodes = [node for node in ast.parse(source).body
                  if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
                  and node.name == "main"]
    require(len(main_nodes) == 1, "Cannot select actual producer main")
    calls = [node for node in ast.walk(main_nodes[0])
             if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
             and node.func.id == "load_driver"]
    require(len(calls) == 1, "Cannot select actual main load_driver call")
    captured = []
    driver.allow_private_death_succession_modal_continue = False
    previous = mcp_producer.NativeHeadlessGameplayDriver

    def capture_native_constructor(*positional, **kwargs):
        captured.append({"positional": positional, "kwargs": kwargs})
        driver.allow_private_death_succession_modal_continue = kwargs.get(
            "allow_private_death_succession_modal_continue", False)
        return driver

    binding = {"lifecycle_mode": "ordinary_campaign_succession",
               "ordinary_campaign_no_pact": True}
    namespace = dict(vars(mcp_producer))
    namespace.update(args=args, selected_state_dir=Path(args.state_dir),
                     war31_gate=None, succession_lifecycle_binding=binding)
    try:
        mcp_producer.NativeHeadlessGameplayDriver = capture_native_constructor
        expression = ast.Expression(body=deepcopy(calls[0]))
        loaded = eval(compile(ast.fix_missing_locations(expression), str(mcp_source), "eval"),
                      namespace)
    finally:
        mcp_producer.NativeHeadlessGameplayDriver = previous
    require(loaded is driver and len(captured) == 1,
            "Actual main expression did not select the native loader")
    kwargs = captured[0]["kwargs"]
    require(kwargs.get("allow_private_death_succession_modal_continue") is True,
            "Actual main/loader lost the parsed private flag")
    require(kwargs.get("succession_lifecycle_binding") == binding,
            "Actual loader lost the ordinary lifecycle binding")
    require(driver.allow_private_death_succession_modal_continue is True,
            "Captured native constructor did not receive the enabled existing mode")
    server = mcp_producer.create_server(loaded)
    registry = server._tool_manager._tools
    names = ["ck3_query_current_timeline_blocker_context_v1",
             "ck3_continue_death_succession_modal_v1"]
    require(all(name in registry for name in names),
            "Actual CLI/loader-selected producer did not register both facades")
    query_tool = registry[names[0]]
    annotations = query_tool.annotations
    require(getattr(annotations, "read_only_hint",
                    getattr(annotations, "readOnlyHint", None)) is True,
            "Actual CLI/loader-registered query lost the read-only annotation")
    return server, {
        "cli_flag": flag, "parsed_enabled": True,
        "main_load_driver_call_line": calls[0].lineno,
        "actual_main_call_evaluated": True, "actual_load_driver_invoked": True,
        "captured_native_constructor": True,
        "captured_allow_private_death_succession_modal_continue": True,
        "registered_facades": names,
        "constructor_seam": "Memory-only capture; actual NativeHeadless constructor, endpoint and main transport loop are not executed",
    }


def run(source_tree, packet_folder, mcp_source, *, registration_only=False, receipt_path=None):
    sys.path.insert(0, str(source_tree / "ck3_autonomous_player/src"))
    from xar_autoplayer.bridge.timeline_blocker_private_transport import (
        query_current_timeline_blocker_context_private_v1,
    )
    from xar_autoplayer.bridge.death_succession_modal_private_transport import (
        continue_death_succession_modal_private_v1,
    )
    spec = importlib.util.spec_from_file_location(
        "xar_autoplayer.bridge.mcp_server", mcp_source)
    require(spec is not None and spec.loader is not None, "Cannot load exact MCP producer")
    mcp_producer = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mcp_producer
    spec.loader.exec_module(mcp_producer)

    def read(name):
        path = packet_folder / name
        return json.loads(path.read_text(encoding="utf-8"))

    modal = read("modal-native-command-result.json")
    clear = read("clear-native-command-result.json")
    ack = read("close-native-command-result.json")
    native_revision = modal["result"]["snapshot_revision"]
    date_raw = modal["result"]["current_timeline_blocker_context"]["date_raw"]
    actor_id = ack["result"]["played_character_id"]
    episode = "fixture-native-" + str(actor_id) + "-succession12003"

    class Driver:
        allow_private_current_timeline_blocker_query = True
        allow_private_death_succession_modal_continue = True

        def __init__(self):
            self.closed = False
            self.advanced = False
            self.calls = []
            self.query_count = 0
            self.close_count = 0
            self.life_count = 0
            self.endpoint = SimpleNamespace(send=self.send)
            self.state = SimpleNamespace(wait_for_command_result=self.wait)

        def take_snapshot(self):
            return {
                "snapshot_id": "fixture-frame-" + str(1 + int(self.advanced)),
                "revision": 77 + int(self.advanced),
                "native_revision": native_revision + int(self.advanced),
                "date_raw": date_raw + 24 * int(self.advanced),
                "paused": True, "map_ready": True,
                "episode_character_id": actor_id,
                "episode_run_id": episode,
                "played_character": {"character_id": actor_id, "alive": True},
                "active_event": None, "pending_character_interaction": None,
                "one_life_terminal_reason": None,
            }

        def send(self, request):
            self.calls.append(deepcopy(request))

        def wait(self, request_id, timeout_seconds):
            require(timeout_seconds > 0, "existing transport timeout must be positive")
            request = self.calls[-1]
            require(request["request_id"] == request_id, "transport request binding changed")
            require(request["expected_revision"] == native_revision, "native revision changed")
            if request["step"] == "query-current-timeline-blocker-context-v1":
                self.query_count += 1
                result = deepcopy(clear if self.closed else modal)
                if self.closed:
                    require(result["result"]["observation_revision"]
                            > ack["result"]["action_observation_revision"],
                            "production-emitted independent clear must follow the ACK")
            elif request["step"] == "continue-death-succession-modal-v1":
                require(not self.closed, "Close must be submitted only once")
                require(request["expected_date_raw"] == date_raw,
                        "existing Close request lost the native fixture date")
                require(request["expected_played_character_id"] == actor_id,
                        "existing Close request lost the successor ID")
                self.close_count += 1
                self.closed = True
                result = deepcopy(ack)
            else:
                raise RuntimeError("Unexpected transport step " + str(request["step"]))
            # Dynamic UUID correlation is endpoint scaffolding, not producer data.
            result["request_id"] = request_id
            return result

        def execute_step(self, step, *, expected_revision):
            require(step == "life-advance" and expected_revision == 77,
                    "existing transport must use its formal advance entry")
            require(self.closed, "No date advance before the independently cleared Close")
            self.life_count += 1
            self.advanced = True
            return {"step": step, "accepted": True, "elapsed_days": 1,
                    "starting_date_raw": date_raw, "ending_date_raw": date_raw + 24}

        def query_current_timeline_blocker_context_v1(self, *, expected_revision):
            return query_current_timeline_blocker_context_private_v1(
                self, expected_revision=expected_revision)

        def continue_death_succession_modal_private_v1(
            self, *, expected_revision, expected_played_character_id, expected_episode_run_id,
        ):
            return continue_death_succession_modal_private_v1(
                self, expected_revision=expected_revision,
                expected_played_character_id=expected_played_character_id,
                expected_episode_run_id=expected_episode_run_id)

    driver = Driver()
    server, cli_loader = verify_cli_loader_registration(
        mcp_producer, mcp_source, driver, packet_folder)
    if registration_only:
        require(driver.query_count == driver.close_count == driver.life_count == 0
                and driver.calls == [], "Registration supplement replayed producer actions")
        prior = packet_folder / "python-consumer-result.json"
        require(prior.is_file(), "Registration supplement requires the completed consumer receipt")
        require(json.loads(prior.read_text(encoding="utf-8"))["status"] == "GREEN",
                "Cannot reuse a non-GREEN completed consumer receipt")
        result = {
            "schema": "xar.succession-modal-12003-cli-loader-supplement/v1",
            "status": "GREEN", "python_optimized": not __debug__,
            "scope": "Changed CLI/parser/main load expression/actual loader/registered facades only; completed producer/normalizer result reused",
            "mcp_producer": str(mcp_source),
            "mcp_producer_sha256": hashlib.sha256(mcp_source.read_bytes()).hexdigest(),
            "cli_loader": cli_loader,
            "prior_consumer_receipt": {"path": str(prior),
                "sha256": hashlib.sha256(prior.read_bytes()).hexdigest()},
            "facade_action_invocations": 0, "native_reruns": 0,
            "sdk_calls": 0, "game_commands": 0, "window_inputs": 0,
            "natural_succession_credit": 0, "new_saved_days": 0,
        }
        require(receipt_path is not None, "Registration supplement needs a distinct receipt path")
        receipt_path.parent.mkdir(parents=True, exist_ok=True)
        require(not receipt_path.exists(), "Do not overwrite a completed supplement receipt")
        receipt_path.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
        print(json.dumps({"status": "GREEN", "optimized": result["python_optimized"],
                          "result": str(receipt_path)}, ensure_ascii=False))
        return
    # Actual producer registration and facade functions, without an SDK Client,
    # session, pipe, transport connection, application-main hook or live CK3.
    registry = server._tool_manager._tools
    query_name = "ck3_query_current_timeline_blocker_context_v1"
    close_name = "ck3_continue_death_succession_modal_v1"
    require(query_name in registry and close_name in registry,
            "Existing facades were not actually registered by the new producer")
    query_tool = registry[query_name]
    close_tool = registry[close_name]
    annotations = query_tool.annotations
    require(getattr(annotations, "read_only_hint",
                    getattr(annotations, "readOnlyHint", None)) is True,
            "Actual registered query must retain its read-only annotation")
    initial = query_tool.fn(expected_revision=77)
    require(initial["current_timeline_blocker_context"]["identity"]
            == "death_succession_modal", "Actual production query packet not normalized")
    outcome = close_tool.fn(expected_revision=77, expected_played_character_id=actor_id,
        expected_episode_run_id=episode)
    require(outcome["status"] == "materially_verified", "Existing Close consumer did not close")
    require(outcome["submission_ack"]["material_result_verified"] is False,
            "ACK must remain separate from the independent result")
    require(outcome["postcondition_query"]["current_timeline_blocker_context"]["identity"] == "none",
            "Existing consumer did not read actual production clear packet")
    require(outcome["ending_date_raw"] == date_raw + 24,
            "Existing production consumer did not verify later date")
    require(driver.close_count == 1 and driver.life_count == 1,
            "Existing production continuation repeated an action")
    result = {
        "status": "GREEN", "python_optimized": not __debug__,
        "scope": "New .3 production reader/executor serializer packets through existing Python normalizer and both private transports",
        "registered_facade_invocations": [query_name, close_name],
        "cli_loader": cli_loader,
        "mcp_producer": str(mcp_source),
        "mcp_producer_sha256": hashlib.sha256(mcp_source.read_bytes()).hexdigest(),
        "query_count": driver.query_count, "close_count": driver.close_count,
        "life_count": driver.life_count,
        "sdk_calls": 0, "game_commands": 0, "natural_succession_credit": 0,
        "outcome": outcome,
        "packets": [{"path": str(packet_folder / name),
                     "sha256": hashlib.sha256((packet_folder / name).read_bytes()).hexdigest()}
                    for name in ("modal-native-command-result.json", "clear-native-command-result.json",
                                 "close-native-command-result.json")],
    }
    (packet_folder / "python-consumer-result.json").write_text(
        json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": result["status"], "optimized": result["python_optimized"],
                      "result": str(packet_folder / "python-consumer-result.json")}, ensure_ascii=False))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("source_tree", type=Path)
    parser.add_argument("packet_folder", type=Path)
    parser.add_argument("mcp_source", type=Path, nargs="?")
    parser.add_argument("--stdio-registration-only", action="store_true")
    parser.add_argument("--receipt", type=Path)
    args = parser.parse_args()
    mcp_source = (args.mcp_source or args.source_tree /
                  "ck3_autonomous_player/src/xar_autoplayer/bridge/mcp_server.py")
    run(args.source_tree, args.packet_folder, mcp_source,
        registration_only=args.stdio_registration_only, receipt_path=args.receipt)
