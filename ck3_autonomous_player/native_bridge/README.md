# CK3 native bridge skeleton

This directory contains the first native slice of the dual-backend CK3 player.
It is intentionally small:

- `xar_ck3_bridge.dll` connects to the named pipe supplied in
  `XAR_CK3_BRIDGE_PIPE` and emits length-prefixed UTF-8 JSON frames;
- `xar_ck3_bridge_injector.exe <pid> <dll-path>` injects the x64 bridge into
  an existing x64 process with `VirtualAllocEx` + `WriteProcessMemory` +
  `CreateRemoteThread(LoadLibraryW)`;
- the first frame is a build identity/capability announcement;
- the DLL emits a heartbeat every 250 ms and answers a framed `ping` with
  `pong`;
- `xar_ck3_bridge_host.exe` creates a minimal target with
  `CREATE_SUSPENDED`, runs the PID injector, verifies the complete
  hello/heartbeat/ping/pong exchange from inside that target, and only then
  resumes its original primary thread.

The bridge protocol is deliberately not MCP. The external Python daemon owns
MCP (stdio first, Streamable HTTP if a persistent service is later useful) and
translates typed CK3 tools into these small local frames. Consequently MCP,
planner and schema changes do not require restarting CK3; only native bridge
changes do.

## Build and offline test

Use an x64 Visual Studio developer shell with CMake and Ninja:

```powershell
cmake -S . -B build -G Ninja -DCMAKE_BUILD_TYPE=Release
cmake --build build
ctest --test-dir build --output-on-failure
```

The offline test injects only into the purpose-built
`xar_ck3_bridge_target.exe`; it does not start or touch CK3. A successful run
prints both the injector result and:

```text
PASS: suspended=1 injected=1 protocol=1 hello=1 heartbeat=1 pong=1 resumed=1 target_exit=0 ...
```

For direct use against an x64 process that has inherited
`XAR_CK3_BRIDGE_PIPE`:

```powershell
.\xar_ck3_bridge_injector.exe <pid> .\xar_ck3_bridge.dll
```

The reusable implementation is
`xar::bridge::InjectLibrary(HANDLE, std::filesystem::path)`, exposed by the
`xar_bridge_injector` static library. The supplied process handle must allow
remote allocation, writes, and thread creation.

## Frame contract v1

Each frame is:

```text
uint32 little-endian payload_bytes
payload_bytes of compact UTF-8 JSON
```

The current maximum payload is 1 MiB. Initial frame types are `hello`,
`heartbeat`, `ping`, and `pong`. `hello.capabilities` is authoritative: this
skeleton advertises only bridge identity, heartbeat, and ping.

## Next integration step

`xar_autoplayer.runtime` already creates `ck3.exe` with `CREATE_SUSPENDED`,
assigns it to the tracked Job, verifies its identity, and only then resumes its
main thread. The native MCP mode can now reuse the tested injection sequence in
that existing suspended interval:

1. the external daemon creates the pipe and supplies its name in the child
   environment;
2. runtime creates the suspended CK3 process exactly as it does now;
3. runtime calls `InjectLibrary` (or invokes the PID CLI) for this DLL;
4. runtime resumes CK3 and waits for `hello`;
5. the hybrid gameplay backend routes only advertised native capabilities to
   the bridge and leaves all other observation/action families on OCR and
   keyboard/mouse.

The loader path is now exercised end to end, but it has deliberately not yet
been run against `ck3.exe`, and the DLL still does not hook or read game state.
The next valuable native additions are game phase/date/pause and active event
presence, followed by event option selection and game-speed commands. Those
replace the current repeated OCR event-polling hot path before broader marriage
and war command coverage is attempted.
