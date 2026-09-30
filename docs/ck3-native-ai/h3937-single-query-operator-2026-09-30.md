# H3937 one paused route-contact query

This candidate reuses the managed `native_session`, paused H3937 subject,
source-frame, one appended history row, persisted history, save and sidecar
guards. It builds the wire from the **fresh published nonretreating hostile
roster**. This roster is not a physical-inventory completeness certificate.
The original inventory check and sibling `physical_army_inventory_diagnostics`
are retained unchanged in `query-report.json`. Date and gameplay actions remain
unauthorized; `six_read_contracts_completed` is always zero.
The admitted single-query path reports RED when the original inventory check
is invalid. The diagnostic sibling cannot upgrade that check.

## Actual entry

Use the explicitly verified interpreter. Both commands default to read-only
admission preflight and leave the live output absent:

```text
D:/workspace/ck3_eternal_recurrence/tools/.venv/Scripts/python.exe -B C:/h3q30/ck3_autonomous_player/h3937_single_query_once.py --config <fresh-absolute-config> --preflight
D:/workspace/ck3_eternal_recurrence/tools/.venv/Scripts/python.exe -B C:/h3q30/ck3_autonomous_player/agent.py native-query-h3937-stationary-route-contact-v1 --config <fresh-absolute-config>
```

Only an explicit `--live` or the profile's single frozen job can run the query.
The job name is `h3937-route-contact-once`; its argv is:

```text
<verified-python> -B <exact-consumer>/ck3_autonomous_player/h3937_single_query_once.py --config <fresh-absolute-config> --live
```

The existing operator provider accepts the frozen profile command directly.
No gameplay MCP server, screen claim or game was started while implementing
or testing this candidate.

## New input and no-launch binding

The config uses `xar.h3937.single-query-run-config.v1` and the complete existing
`h3937_run_config.py` tuple. It also requires these explicit values:

| Field | Input |
| --- | --- |
| `native_source_checkout`, `native_source_head` | Clean native build source and its exact commit. |
| `native_build_receipt`, `native_build_receipt_sha256` | Root's actual build receipt and frozen bytes. |
| `bridge_dll_sha256`, `bridge_injector_sha256` | Actual new binary hashes. |

The new source-matched `preparation.json` must use the original frozen #685
save, raw driver and child sidecar. Prepare a new state using the real
`prepare-profile`, `rebind-ordinary-seed-v1` and `native-one-generation-preflight`
commands. Copy new binaries into that attempt's `source-verified` directory;
`preparation.source` binds their source paths and hashes. The prepared driver
SHA is recomputed after rebind; historical prepared state must not be reused.

After root supplies its genuinely allocated tuple, these create-only actions
bind the new admission and profile. They never allocate an identity or create GO:

```text
<verified-python> -B <exact-consumer>/ck3_autonomous_player/h3937_single_query_once.py --config <fresh-absolute-config> --bind-admission
<verified-python> -B <exact-consumer>/ck3_autonomous_player/h3937_single_query_once.py --config <fresh-absolute-config> --freeze-operator-profile <new-absolute-profile> --operator-state-dir <new-absolute-state-dir>
```

The profile freezes source, interpreter, config, build receipt, admission,
manifest and binaries. It advertises only the one-query job. Source changes
require a fresh production prepare/rebind/preflight and another profile.

## Fresh root GO

Use the existing H3937 challenge, fresh Steam frame, direct review and screen
lease fields with a new actual tuple. The single-query differences are:

| Field | Required value |
| --- | --- |
| `schema` | `xar.war.h3937-single-query-once-go.v1` |
| `decision` | `GO_READ_ONLY_H3937_ROUTE_CONTACT_ONCE` |
| `authorized_scope` | `one_paused_route_contact_query` |
| `maximum_query_actions` | `1` |
| `cold_load_observer_enabled` | `false` |
| `cold_load_observer_dir` | `null` |

The entry reuses the existing challenge/frame/direct-review validator; old GO
and six-query GO are refused. The exact existing `ScreenLeaseKeeper` supplies
both `abort` and `before_process_create` to the managed native session.
The output is a new create-only attempt. The query envelope preserves the raw
diagnostics and the original inventory check without authorizing either.

## Current evidence boundary

The two actual CLI help commands returned RC0. The focused offline suite
`ck3_autonomous_player/tests/unit/test_h3937_single_query_once.py` passed
6/6 with `-B` and 6/6 with `-B -O` using the verified main venv. The suite
includes the actual driver result path and existing operator profile loader
and preflight with a fake process inspector; it opens no pipe or SDK server.
These are source evidence.
The native binary build, actual pair receipt, fresh production preparation,
root-allocated tuple, final profile and live query remain separate receipts.
Absent those inputs, do not label this candidate live READY or claim any of
the six complete read contracts.

The actual new sole-builder manifest is consumed with its existing schema:
Release/H3937 option, source head/tree/fingerprint, actual binary bytes,
author config, same-source focused fixture and independent review are checked.
The primitive route result is saved create-only as `native-query-result.json`
before shape/normalization/frame checks. The returned envelope is separately
saved as `raw-query-envelope.json` before the next snapshot. Both retain the
entire object under `query_result`; completion binds every retained file.
One additional directed fixture exercises inventory RED, driver frame failure,
post-query snapshot failure and final source-hash failure. Earlier six-case
receipts remain historical source evidence and are not rerun for this delta.


## ie 隔离源码交付（2026-09-30）

本次仅在固定 ie 起点 `d5f3c51215439b23f578c8973d5d74ac01f1493c` 上接入冻结的 H3937 producer 与 single consumer 源码。master 冻结点为 `c69260e65b63bf8f8b8ae42e3aee8f2a68561660`；未接收冻结点之后的 master 内容，只交付 ie。

复用的 fixture、pair、no-launch 与实机记录分别绑定其原始执行树。旧 `0d06` pair 不认证本次适配后的原生树；本次没有构建、启动游戏或认证六读，formal 仍为 0。Steam 持续离线。

## Rejected command-result retention candidate

R0125 received a negative decoded `command_result` and raised inside the
primitive before either success-result sink was reachable. Its original full
request/frame was not retained; the timeout text does not establish that the
eight-slot inventory diagnostics were generated or lost.

The next candidate adds an optional route-contact observer immediately after
the primitive's keyed wait returns a decoded frame, before the original reject.
Only the admitted single-query driver installs it. The create-only
`decoded-command-result.json` retains the full request and decoded frame,
including request ID, result, error and any diagnostic siblings. The two
existing raw success layers remain separate. Completion hashes this third
artifact even when the original rejection is raised. Legacy default is None.

The single entry prints ASCII-escaped JSON so a GBK terminal can return the
intended RED/RC1 after the UTF-8 completion artifact is persisted. Artifact
serialization is unchanged. One new offline primitive rejection fixture also
checks scoped callback behavior, immutable retention and strict CP936 output.
This source candidate does not qualify a new native build or live tuple; any
new native receipt must retain exact same-source fixture/review binding.
