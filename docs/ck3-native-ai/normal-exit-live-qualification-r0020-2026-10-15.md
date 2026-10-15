# Native normal-exit qualification from R0020

Runtime007's GUI source verifier, exit-autosave control and official desktop
Quit callback now have live evidence for the recorded MTS profile. This adds
evidence to the immutable runtime; it does not rewrite its original offline
READY, mapping, manifest or request receipts. The compact machine pins are in
[the qualification summary](qualification/native-normal-exit-r0020-12004.json).

`machine_id`: `bf-202609141645-5434332d4d`, independently read with the public
machine command and joined to the original public-run record. The run is
`bf-202609141645-5434332d4d--more-tenets-slots--R0020`, from
2026-10-15 08:53:15.896529 UTC to public parent wait 0 at 10:50:01.818485 UTC.
It used CK3 1.20.0.4/build 25734779, `simp_chinese`, frozen framework
`82e71018739ba112660d1784867ce5948521fb34`, and DLL SHA-256
`bfdfb1fe7f02321e7f7d1117e13953131d93c8f1eab6716b9572838e6f3eb612`.
The same process was PID 15228, creation FILETIME
`134365280174723258`, actor 33339 and connection generation 1.

The native source-verifier fix described in
[the offline parity report](normal-exit-native-gui-source-parity-2026-10-15.md)
is now observed in a real loaded profile: at 09:09:26 UTC the query returned
`context_observed`, with `stock_files_verified`,
`loaded_source_binding_verified` and `frame_verified` all true. Its source
inventory SHA-256 was
`eef3902681166c1fdbf88cf943c48ad50f96bdf8d67122131a09fd980b503d68`.
The profile contained the recorded 48-file product and two unrelated religion
GUI files. This does not admit every mod or an unknown replacement exit GUI.

## Actual requests and later observations

| Request, UTC | Original result | Independent later observation |
| --- | --- | --- |
| `prepare_confirmation`, 10:40:32 | `dispatch_unknown_claimed`; dispatch 0 invoked/handled | Fresh query at 10:40:44 admitted the visible pause-menu target 1. |
| `continue_preparation`, 10:40:54 | `dispatch_unknown_claimed`; dispatch 1 invoked/handled | Fresh query at 10:41:04 saw the confirmation window and `should_save=true`. |
| `disable_exit_autosave`, 10:41:22 | `autosave_disabled`; toggle invoked; postcondition observed | Fresh query at 10:41:40 read available `should_save=false`; the final 10:49:10 query still read false. Root directly reviewed the original unchecked-box image. |
| `confirm_desktop`, 10:49:27 | `dispatch_unknown_claimed`; dispatch 2 invoked/handled | The separately retained OS handle and managed session later observed exit 0 at 10:49:55. |

Each action was submitted once with a consumed claim, no retry authorization,
and a verified fresh context signature. All four request receipts recorded
`uses_desktop_input=false` and `uses_ocr=false`. There were six actual
`ck3_query_normal_exit_context_v1` requests and four
`ck3_request_normal_exit_v1` requests. `ck3_observe_normal_exit_v1` was not called
and receives no live tool qualification from this run. The already-false
idempotent action branch also remains an offline qualification.

The final request's own five-second process observation timed out with
`process_exit_observed=false`, `typed_normal_exit_observed=false` and Windows
`STILL_ACTIVE` 259. These original fields and the three unknown dispatch statuses
remain unchanged. Exit credit comes from the later join: CaseClient's retained
handle was signaled with code 0 for the same process; the original managed
session recorded `exit_reason=process_exit`, code 0, completed thread, cleanup
and an absent process tree. The original host and public Popen waits were 0,
the keeper's actual wait was 0, and CAS 6110 released its resources at
10:58:04.915976 UTC. The close receipt's `normal_close_qualified=true` and
`business_pass=false` retain their separate meanings.

The observed true-to-false checkbox transition qualifies the native exit-save
policy control. The request field `autosave_verified=false` is preserved: this
is not proof of an autosave artifact's integrity or a request to save on exit.

## Evidence ownership and scope

The additive local receipt is
`20261015-native-religion-007/LIVE-QUALIFICATION-R0020.actual.json` below the
machine's common-runtime root. It pins the original READY, selected runtime/DLL,
actual request and fresh-query results, Root image review, retained OS and
managed cleanup, original process waits and resource release. It includes the
machine identity and observation time. No old receipt is upgraded in place;
the Defender registration RED from the build remains recorded.

Product business evidence and its limited verdict remain in the independent
[R0020 product report](https://github.com/XenoAmess/ck3_mod_more_tenant_slots/blob/master/docs/native-legacy-r20-2026-10-15.md).
That case used a prepublication v10 candidate save with the current candidate
product. This shared supplement grants no fresh-campaign, independent cold-load,
published-v10-save, direct owned-Rite-edit, Workshop-release or all-mod credit.
The separately added [rite creation notice knowledge](rite-creation-notice-12004.md)
was not deployed into immutable runtime007 by this documentation package.

This package only reads and summarizes completed evidence. It performs no new
game actions or repeat tests. Reusable source/exit qualification belongs in this
framework; the campaign, product source, saves and business fixtures remain in
the product project.
