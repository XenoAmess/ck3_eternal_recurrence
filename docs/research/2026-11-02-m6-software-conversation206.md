# M6 software endpoint conversation 206

Three Java files belong in `local-service/src/test/java/org/xar/ck3/control/platform/`.
They are test helpers and opt-in tests, not production Sway dispatch or a Root issuer.

The helper starts only a configured `sameworld_live_peer.exe` software executable,
checks its SHA-256, actual owned process executable, PID and exact birth, and retains
only that process's read-only handle. Every endpoint I/O verifies that same live
owned process. One new Job, pipe, session, request IDs and evidence directory are
created for each test. No existing CK3 process, Steam, native DLL, window or ledger
is discovered or accessed.

`NativeGameTransport` receives the actual HELLO and performs the two real typed
fresh reads. Dynamic Sway requests go directly through the same authenticated
`NativePipeEndpoint` with `NativeWire`, and are **DATA only**. They do not acquire a
`ReadPermit`, `SubmissionPermit`, action ACK custody, Core or Root authority.
The old finite test and old two-fresh test are not run.

The new positive conversation uses nine requests: target, Start, original receipt,
post-Start target, selected target, completion, opinion, Stop and post-Stop completion.
Start's expected fields come from its actual target reply; later full instance ID
and generation come from the actual receipt. All request IDs are distinct from
logical action IDs. The peer's own numbered incoming/outgoing raw JSON is compared
byte-for-byte with the original framed packets, including ordering before and after
the fresh reads. The controlled software source creates a row after queue transfer,
changes its opinion input to 73, and exposes the named reader value 12. These are
fixture inputs. Start/Stop native machine execution and natural terminal/cause or
material gain are not claimed. Stop remains pending and the row stays active.

The negative test uses a separate new peer and one stale native-revision query.
It checks the exact error, an unchanged state and a subsequent genuine fresh read,
without Start, receipt, Stop or a source opinion transition.

By default both JUnit methods are disabled before any software process starts.
Explicit opt-in uses `-Dxar.m6.software206.settings=/absolute/private/settings.json`.
The JSON has exactly these fields:

```json
{
  "executable": "/absolute/path/sameworld_live_peer.exe",
  "software_executable_sha256": "64 hex digits from that software executable",
  "work_directory": "/existing/absolute/private/work",
  "evidence_root": "/existing/absolute/private/evidence",
  "environment": {},
  "actor": 50331649,
  "target": 50331650,
  "bridge_version": "0.1.0",
  "hello_executable_sha256": "98702F88A547CDE2EAF29A85F93B85F68EE4CF8148336A4F7AFAEB75319DD518",
  "adapter_id": "ck3-1.20.0.4-msvc-x64",
  "memory_limit_bytes": 67108864,
  "lifetime_ms": 30000,
  "max_requests": 32
}
```

The HELLO SHA and adapter are the explicit software profile, not proof that this
process is CK3. Private paths, executable, wire originals and reports are not source
artifacts to publish. The configured environment augments the current environment.
This source unit does not ship the private prebuilt peer. A different machine must
qualify its own corresponding software producer and executable before opting in;
the three Java files alone do not make that producer available.
The helper closes its own endpoint, observes natural owned-process exit, and closes
its own Job/handle on all paths. A failure remains a failure and is never replayed.

The remaining real public entry is `RootMcpSway.finish` through
`RootApplicationSession.executePublicDecision` and
`SwayRuntimeInstaller.prepareFinish`. It requires the actual installed current Root,
writer session and complete physical frame/source/Game. Planning reads get their
real private permit in `PlanningReadCoordinator`. Closed software Received values
cannot fill those capabilities. M6 useful Sway natural terminal/cause/material and
its full acceptance contract remain open.

Source provenance, model rejection reasons, owner input corrections and actual
checks are recorded separately. Complete model stops are not adoption. This unit
does not authorize DLL deployment, actual Game action or a performance claim.
