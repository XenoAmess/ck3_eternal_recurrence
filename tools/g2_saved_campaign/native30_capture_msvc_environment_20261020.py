"""Run the frozen MSVC initializer in an owned phase; persist only its delta."""
import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path

def require(value, message):
    if not value: raise RuntimeError(message)

def environment_delta(before, environment):
    previous = {key.upper(): value for key, value in before.items()}
    current = {key.upper(): value for key, value in environment.items()}
    delta = {key:value for key,value in current.items() if previous.get(key) != value}
    require(len(delta) <= 256, "MSVC environment delta key cap")
    require(not any(any(word in key for word in ("PASSWORD", "SECRET", "TOKEN", "API_KEY")) for key in delta),
            "MSVC initializer changed a sensitive environment value")
    require(not any(current.get(key) for key in ("CL", "_CL_", "LINK", "CMAKE_BUILD_PARALLEL_LEVEL")),
            "MSVC initializer introduced unadmitted build flags")
    return delta

def main():
    parser = argparse.ArgumentParser(__doc__)
    parser.add_argument("--frozen-tool", type=Path, required=True)
    parser.add_argument("--tool-sha", required=True)
    parser.add_argument("--installation", type=Path, required=True)
    parser.add_argument("--work", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    require(not args.output.exists(), "create-only MSVC delta output")
    require(hashlib.sha256(args.frozen_tool.read_bytes()).hexdigest() == args.tool_sha, "frozen MSVC initializer SHA")
    spec = importlib.util.spec_from_file_location("native30_frozen_msvc_initializer", args.frozen_tool)
    tool = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(tool)
    before = {key.upper(): value for key, value in os.environ.items()}
    initial = tool.child_environment(args.work)
    environment, tools = tool.initialize_msvc(args.installation, args.work, initial)
    delta = environment_delta(before, environment)
    raw = (json.dumps({"tools": tools, "environment_delta": delta}, indent=2)+"\n").encode()
    require(len(raw) <= 512*1024, "MSVC environment output byte cap")
    with args.output.open("xb") as stream: stream.write(raw)
    print(json.dumps({"tools": tools, "delta_keys": sorted(delta), "output_bytes": len(raw)}))

if __name__ == "__main__": main()
