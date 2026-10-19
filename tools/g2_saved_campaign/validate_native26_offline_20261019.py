"""Bounded offline checks of the narrow Native26 successor; no Game loading.

Only independent fixture DLLs are loaded by ordinary child Python processes.
The actual production DLL is never loaded, injected or deployed here.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import subprocess
import sys

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(Path(__file__).resolve().parent))
import build_native26_performance_20261019 as build

NATIVE = "ck3_autonomous_player/native_bridge/"


def git(path):
    return subprocess.check_output(["git", "show", "d761b3ce:" + NATIVE + path], cwd=ROOT)


def write_source(path, text):
    path.write_text(text, encoding="utf-8", newline="\n")
    return build.pin(path)


def main():
    parser = argparse.ArgumentParser(__doc__)
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument("--admission", type=Path, required=True)
    parser.add_argument("--route-only", action="store_true")
    args = parser.parse_args()
    root, admission = args.output_root, build.read(args.admission)
    machine = subprocess.check_output([sys.executable, str(ROOT / "tools/ck3_live_run_id.py"), "machine"], text=True).strip()
    if machine != admission["machine_id"] or build.norm(root) != build.norm(admission["approved_output_root"]):
        raise ValueError("wrong admitted machine or root")
    if datetime.now(timezone.utc) >= datetime.fromisoformat(admission["parent_review_at_utc"]):
        raise ValueError("expired storage admission")
    link_result = build.read(root / "LINK-RESULT.json")
    if link_result["exit_code"] or build.pin(link_result["DLL"]["path"]) != link_result["DLL"]:
        raise ValueError("actual production DLL link proof missing/drifted")
    run = root / ("offline04" if args.route_only else "offline01")
    run.mkdir()
    (run / "temp").mkdir()
    env, tools = build.environment(root)
    env["TEMP"] = env["TMP"] = str(run / "temp")
    compiled = build.read(root / "COMPILE-RESULT.json")["results"]
    plan = build.read(root / "INPUT-PLAN.json")
    report = {"schema": "xar.ck3.native26-offline-closure/v1", "machine_id": machine,
              "started_at_utc": build.now(), "producer": build.pin(Path(__file__)),
              "production_link": build.pin(root / "LINK-RESULT.json"), "production_DLL_loaded": False,
              "Game_calls": 0, "new_EXE_started": 0, "checks": {}}
    build.write(run / "STARTED.json", report)
    def production(name):
        rows = [row for row in compiled if Path(row["source"]["path"]).name == name]
        direct = [row for row in rows if row["origin"] == "direct"]
        return (direct or rows)[0]
    def include_flags(row):
        return [value for value in row["argv"] if value.lower().startswith(("/i", "-i"))]
    def compile_one(source, tag, includes, defines=()):
        obj, deps = run / (tag + ".obj"), run / (tag + "-dependencies.json")
        argv = [tools["cl"], "/nologo", "/std:c++20", "/EHsc", "/O2", "/MD", "/Gy", "/utf-8",
                "/W4", "/WX", "/DNOMINMAX", "/DWIN32_LEAN_AND_MEAN", *includes, *defines,
                "/c", str(source), "/Fo" + str(obj), "/sourceDependencies", str(deps)]
        result = build.execute(argv, run, env, run / (tag + "-compile.log"))
        if result["exit_code"]: raise RuntimeError(tag + " compile failed")
        result["object"] = build.pin(obj)
        result["dependencies"] = build.pin(deps)
        return result
    def fixture(tag, objects, symbol, output=None):
        dll = run / (tag + ".dll")
        argv = [str(Path(tools["cl"]).parent / "link.exe"), "/nologo", "/DLL", "/OPT:REF", "/OPT:ICF",
                *map(str, objects), "/OUT:" + str(dll), "user32.lib", "advapi32.lib", "bcrypt.lib", "psapi.lib"]
        result = {"link": build.execute(argv, run, env, run / (tag + "-link.log"))}
        if result["link"]["exit_code"]: raise RuntimeError(tag + " link failed")
        result["DLL"] = build.pin(dll)
        loader = run / (tag + "-loader.py")
        code = "import ctypes,sys\nf=ctypes.CDLL(sys.argv[1])." + symbol + "\nf.restype=ctypes.c_int\n"
        if output:
            code += "f.argtypes=[ctypes.c_char_p]\nraise SystemExit(f(sys.argv[2].encode('utf-8')))\n"
        else:
            code += "f.argtypes=[]\nraise SystemExit(f())\n"
        result["loader"] = write_source(loader, code)
        command = [sys.executable, "-B", str(loader), str(dll)] + ([str(output)] if output else [])
        result["run"] = build.execute(command, run, env, run / (tag + "-run.log"), 120)
        if result["run"]["exit_code"]: raise RuntimeError(tag + " fixture failed")
        return result
    try:
        if args.route_only:
            previous = build.read(root / "offline01/RESULT.json")
            report["previous_actual_failure"] = build.pin(root / "offline01/RESULT.json")
            report["checks"] = {key: previous["checks"][key] for key in ("json", "cb")}
        else:
            # Existing nine-case harness and original old/new bodies. Compile them
            # against THIS successor's actual JSON producer include paths and DTOs.
            old = Path("D:/codex-ck3-demos/2026-10-19-robert-v20261019-native-json-equivalence01/attempt02")
            prior = build.read(old / "RESULT.json")
            for item in prior["source"]["generated_source"]:
                if build.pin(item["path"]) != item: raise ValueError("retained JSON fixture source drift")
            for name in ("ck3_12004_person_six_stage_capture.cpp", "person_callback_entry_inputs_12004.cpp",
                         "ck3_12004_knight_stat_consumption_serializer.cpp"):
                row = production(name)
                expected = next(item for item in prior["source"]["production_source_pins"]
                                if item["commit"] == build.NEW_JSON and item["path"].endswith("/" + name))
                if build.sha(row["source"]["path"]) != expected["whole_source_utf8_sha256"]:
                    raise ValueError("Native26 JSON body differs from retained exact fixture")
            json_row = production("ck3_12004_knight_stat_consumption_serializer.cpp")
            json_compile = compile_one(old / "source/knight-json-streaming-fixture.cpp", "json",
                                       include_flags(json_row), ["/DXAR_SERIALIZER_FIXTURE_DLL=1"])
            actual_includes = build.read(run / "json-dependencies.json")["Data"]["Includes"]
            allowed = {build.norm(item) for item in build.read(json_row["dependencies"]["path"])["Data"]["Includes"]}
            for item in actual_includes:
                if "xar_bridge" in build.norm(item) and build.norm(item) not in allowed:
                    raise ValueError("JSON fixture used a header outside actual Native26 DTO closure: " + item)
            output = run / "JSON-RESULT.json"
            report["checks"]["json"] = {"compile": json_compile,
                **fixture("json", [json_compile["object"]["path"]], "XarRunKnightJsonStreamingFixture12004", output),
                "result": build.pin(output), "actual_typed_project_headers": [build.pin(item) for item in actual_includes if "xar_bridge" in build.norm(item)]}
            # Retain the original actor callback/order test bodies unchanged.
            test = git("src/ck3_12002_declarations_test.cpp").decode("utf-8-sig")
            test = test.replace("int main(int argc, char **argv) {", "int RunDeclarationsMain(int argc, char **argv) {", 1)
            close = test.rindex("\n}")
            test = test[:close] + "\n  return 0;" + test[close:]
            test += '\nextern "C" __declspec(dllexport) int RunNativeDeclarationFixture() { char n[]="offline"; char *v[]={n,nullptr}; return RunDeclarationsMain(1,v); }\n'
            source = run / "declarations-fixture.cpp"
            test_pin = write_source(source, test)
            decl = production("ck3_12002_declarations.cpp")
            cb_compile = compile_one(source, "cb", include_flags(decl))
            report["checks"]["cb"] = {"fixture_source": test_pin, "compile": cb_compile,
                **fixture("cb", [cb_compile["object"]["path"], decl["object"], root / "build/native26-runtime.lib"], "RunNativeDeclarationFixture"),
                "production_declarations_object": decl["object_pin"]}
        # Use the existing router-spy prefix. Keep every spy body; replace only
        # the adapter descriptor and main with the exact .4 seam assertions.
        test = git("src/ck3_12002_nonwar_router_test.cpp").decode("utf-8-sig")
        test = test[:test.index("int main() {")]
        descriptor = '"ck3-1.20.0.2-msvc-x64", "1.20.0.2", "router-fixture", "fixture", {}'
        replacement = 'xar::ck3_12004::kAdapterId, xar::ck3_12004::kGameVersion, xar::ck3_12004::kExecutableSha256, "fixture", {}'
        if test.count(descriptor) != 1: raise ValueError("router fixture descriptor changed")
        test = '#include "xar_bridge/ck3_12004.hpp"\n' + test.replace(descriptor, replacement)
        test += r'''
extern "C" __declspec(dllexport) int RunNative26TerminationRouteFixture() {
  using namespace xar;
  using namespace xar::ck3_12002;
  RouterAdapter adapter;
  ck3_11906::MainThreadQueryMailboxV1 mailbox{};
  game::Snapshot published{};
  published.date_raw=53175816; published.played_character_id=29829;
  NonwarPrivateState12002 state{}; state.faction_query_sequence=42;
  SwayTerminationRecorder12002 owned{};
  state.sway_termination_recorder=&owned; expected_sway_termination_recorder=&owned;
  const std::string payload="{\"expected_revision\":916,\"actor_id\":29829,\"target_id\":42,\"scheme_id\":81,\"after_sequence\":0}";
  const std::string request="native26-route-only";
  expected={&adapter,&mailbox,&published,&state,916,r5_steps[2],payload,request};
  Check(IsNonwarPrivateStep12004(adapter,r5_steps[2]),"exact .4 termination gate admits constant");
  std::string serialized="stale",failure="stale";
  Check(HandleNonwarPrivate12002(adapter,mailbox,published,916,r5_steps[2],payload,request,state,serialized,failure),"termination dispatch");
  Check(serialized==r5_outputs[2] && failure.empty() && r5_calls[2]==1,"unaltered original R5 spy and args");
  Check(state.faction_query_sequence==42,"unrelated state unchanged");
  Check(!IsNonwarPrivateStep12004(adapter,"query-sway-completion-termination-v1-private-unregistered"),"suffix stays rejected");
  Check(!IsNonwarPrivateStep12004(adapter,"query-sway-completion-execution-v1-private"),"execution gate unchanged");
  Check(!IsNonwarPrivateStep12004(adapter,"query-sway-completion-invalidation-reason-v1-private"),"invalidation gate unchanged");
  state.sway_termination_recorder=nullptr; serialized="stale"; failure="stale";
  Check(!HandleNonwarPrivate12002(adapter,mailbox,published,916,r5_steps[2],payload,request,state,serialized,failure),"missing owned recorder rejects");
  Check(failure=="sway_termination_observer_not_installed" && r5_calls[2]==1,"typed missing observer; spy not called twice");
  std::cout << "native26 exact .4 termination routing checks=" << checks << "\n";
  return 0;
}
'''
        # Keep the actual parser body; other terminal-provider paths are spies
        # that fail if touched. The requested termination route calls its
        # original R5 spy and never reaches this .4 completion provider.
        sdk = Path("D:/codex-ck3-background-spill/ck3-sdk91/ck3_autonomous_player/native_bridge/src")
        parser_source = sdk / "active_scheme_sway_private_transport_v1.cpp"
        parser_text = parser_source.read_text(encoding="utf-8-sig")
        begin = parser_text.index("bool ParseActiveSchemeSwayPrivateQueryStepV1(")
        end = parser_text.index("\n}\n", begin) + 3
        test += '\n#include <charconv>\nnamespace xar::ck3_11906 {\n' + parser_text[begin:end] + "\n}\n"
        test += r"""
namespace xar::ck3_12004 {
bool ExecuteSwayTerminalMailbox12004(void *,
    const ck3_11906::MainThreadExecutionStampV1 &) noexcept {
  Check(false,"unrelated terminal executor must not be reached"); return false;
}
bool HandleSwayTerminal12004(const game::GameAdapter &,
    ck3_11906::MainThreadQueryMailboxV1 &, const game::Snapshot &,
    std::uint64_t, std::string_view, std::string_view, std::string_view,
    std::string &, std::string &) noexcept {
  Check(false,"unrelated terminal provider must not be reached"); return false;
}
}
"""
        source = run / "termination-route-fixture.cpp"
        route_pin = write_source(source, test)
        router = production("ck3_12002_nonwar_router.cpp")
        flags = include_flags(router)
        define = ["/DXAR_CK3_ENABLE_G2_ACTIVE_SCHEME_PRIVATE_CANDIDATE_V1=1"]
        route_compile = compile_one(source, "termination-route-test", flags, define)
        router_compile = compile_one(Path(router["source"]["path"]), "termination-route-production", flags, define)
        abi4 = next(item for item in plan["objects"] if Path(item["source"]).name == "ck3_12004_abi_profile.cpp")
        abi4_compile = compile_one(Path(abi4["source"]), "termination-abi4", flags)
        abi3_source = sdk / "ck3_12003_abi_profile.cpp"
        abi3_compile = compile_one(abi3_source, "termination-abi3", flags)
        report["checks"]["termination_route"] = {"fixture_source": route_pin, "compile": route_compile,
            "exact_production_source_compile": router_compile, "abi4_compile": abi4_compile, "abi3_compile": abi3_compile, "original_parser_source": build.pin(parser_source),
            **fixture("termination-route", [route_compile["object"]["path"], router_compile["object"]["path"], abi4_compile["object"]["path"], abi3_compile["object"]["path"]], "RunNative26TerminationRouteFixture"),
            "scope": "exact .4 gate and real dispatcher, original domain spy only; no native provider/business/terminal occurrence qualification"}
        report["status"] = "PASS_OFFLINE_JSON_CB_EXACT4_TERMINATION_ROUTE"
    except Exception as error:
        report["status"], report["error"] = "RED", repr(error)
    report["closed_at_utc"] = build.now()
    report["whole_child_logical_bytes_before_receipt"] = build.check_space(root, "offline", 768 * build.MIB)
    build.write(run / "RESULT.json", report)
    print(json.dumps({"status": report["status"], "error": report.get("error"), "result": build.pin(run / "RESULT.json")}))
    return 0 if report["status"].startswith("PASS_") else 1


if __name__ == "__main__":
    raise SystemExit(main())
