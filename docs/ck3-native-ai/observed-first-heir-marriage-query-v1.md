# Observed first-heir marriage final-legality query v1 (M5-OBS-R736)

Status: static-ready candidate only. No public capability, MCP tool, action,
strategy consumer, or production advertisement is registered by this package.
The next gate is a same-build paused live read using the new candidate DLL.

## Exact source and observed boundary

- CK3 1.19.0.6 `ck3.exe` SHA-256 `2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86`.
- `00_marriage_interactions.txt` SHA-256 `681A9B669E5A16642A197B6FE16085193DFBB99A398D0E20E86173F5AC6DE219`: redirected marriage pair roles and actor-list family candidates. Exact source/call chain and dashed unknown branches are in [marriage-and-alliance.md](marriage-and-alliance.md), R720–R736.
- R736 read-only live report SHA-256 `83AE48416AD7B7F0CEC1E3DCE7F3C0322B6DAAA6139DF996B0238BFF798C8E94`; private family result SHA-256 `D58FE7C85CFB03655745188E2D820404E3747AA808F9F65620847C5A060F7B7A`. The public campaign-root observed the primary first heir; native complete Can Send plus recipient final answer yielded 657 distinct legal candidates. R736 used the **old private** step, not this new candidate protocol, so it does not close the new live gate.
- Native human-player AI Strategy rank source was unavailable in R720; `native_rank` stays `null`. Storage order, acceptance raw, and candidate count are **not** a rank or shared opportunity-cost score.

## Candidate bridge and MCP asset

Controlled exact-build bridge step: `query-observed-first-heir-marriage-legality-v1`, compiled only with `XAR_CK3_ENABLE_G2_M5_RANKED_MARRIAGE_PRIVATE_QUERY_V1`. It reuses the same paused snapshot/revision, connection-local public campaign-root first-heir binding, generation-checked character enumeration, redirected five-role context, complete Can Send, and recipient final native answer as the R736 private read. There is no CharacterID input and no marriage submit path. The former `query-observed-heir-marriage-choices-v1-private` step is unchanged for existing controlled callers.

Python candidate API: `NativeHeadlessGameplayDriver.query_observed_first_heir_marriage_legality_v1(expected_native_revision=...)` and the corresponding `GameplayBridgeService` method. Result schema: [`observed-first-heir-marriage-legality-v1.schema.json`](../../ck3_autonomous_player/schemas/observed-first-heir-marriage-legality-v1.schema.json). It returns `available` with all complete-Can-Send rows, a separately filtered `native_legal_candidates` set (final answer raw 0/1), or typed `unavailable`; transport/frame/shape failures remain RED. `native_rank` is always `null`. Faith inputs are consumed only through the opaque native final judgment. No new faith/doctrine query is exposed.

Future generic MCP name (not registered yet): `ck3_query_observed_first_heir_marriage_legality_v1(expected_native_revision)`. It should call this service method and return the same versioned schema on any authorized host connected to a compatible CK3 bridge. A host without CK3 can inspect the schema and source-bound fixture, but cannot truthfully claim live game capability. Do not add the MCP decorator or hello capability before the exact-build paused live test of the new bridge step, same-frame identity and candidate rows, unavailable/RED behavior, and schema response. Action and strategy promotion are separate gates.

Compatibility: this adds an optional unadvertised read-only protocol step and Python method; existing snapshots, hello capabilities, private step, actions, and MCP tool list do not change. `open_kaishek` needs no immediate migration. Before public registration, downstreams can adopt the schema by feature-detecting the future capability; they must not infer support from the presence of this source file or a native DLL with the private CMake switch alone. A versioned candidate DLL is required for the new literal; the frozen R736 DLL does not contain it.
