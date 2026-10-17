# Battle and committed-route modal consumer source fixture

This package extracts a narrowly scoped consumer from the frozen P35 candidate.
It accepts existing Native sentinel `player_decision` receipts for active battles
and one-day committed routes, while retaining the original clock, generation,
cancel, actor, episode, war, complete hostile scope and 1.5 margin checks. It
does not issue actions or select options. The result records measured elapsed
time and a typed nonmaterial observation; it never credits UI or business
success, or authorizes replay of the original action.

`tools/root_battle_route_modal_classifier_v1.py` depends on the formal
`xar_autoplayer` SDK. It imports the original war-contract parsers and Native
sentinel normalizer/validators. It is a pure consumer with SDK dependencies,
not a self-contained queue implementation. Call `classify(body, initial_frame,
game_pid, start_binding, scope)` with the existing gameplay start-binding
validator. `None` means that the original nonmodal classifier remains
responsible. A rejected matching modal raises; callers must not turn that
failure into permission to replay or act on unknown UI.

The public helper changes only three Army-ID range checks from the frozen
16,268-byte helper (`7968a6327bef980a49c34f5caf290fbdca09cb00e12603a4d56a5648a06fa69f`):
public CUnit IDs accept the native signed-int32 range `0..2147483647`.
War IDs, provinces and PID retain their separate positive-ID contracts.
The frozen runtime helper and the private 262,062-byte classifier are not
changed or copied into this public package. Public source delivery alone
does not install this consumer into an active queue.

Run the portable test from a checkout:

```text
python -B -X utf8 ck3_autonomous_player/tests/unit/test_battle_route_modal_classifier_v1.py -v
```

For an external source package, pass `--source-root <checkout>` and
`--helper-file <helper.py>`. The test configures the formal SDK source path and
verifies the resolved NativeDriver import. Optional `--receipt <new-file.json>`
writes a create-only result. There are no fixed drive, scene, queue or SDK-generation
paths in the public code or synthetic fixture.

The fixture reuses the six existing Native-I/O fixture definitions from
`test_native_bridge_driver.py`, then actually calls `NativeHeadlessGameplayDriver.execute_step`.
The four main cases cover each consumer with an active event plus generation
cancel/idle, and a pending interaction plus triggered sentinel. Forty-eight
mutations must be rejected. A separate actual producer case covers CUnit 0.
Startup has six fields and predates the current planning frame; public and
Native revisions remain distinct, and the first command uses the Native
revision. The ordinary plan/Service envelope and the start-binding callback
are fixture inputs. `Service.auto_turn` and the private formal queue are not
executed by this portable test.

On 2026-10-17 the two test methods passed against the then-current public
worktree source: four main producer cases, 48 rejected mutations and one
CUnit-0 producer case. The first portable run rejected a test assertion that
had incorrectly fixed the old public revision at 2; current source produced
public 3 / Native 11. The test now checks the real startup-to-current public
increment and retains the independently fixed Native wire revision. That RED
and the necessary corrected rerun are preserved separately. These are source
fixture results with fake Native I/O, zero Game/MCP calls, and no live
acceptance or date-progress credit.

The stronger private formal-queue loading, persistence and original-response
reconsume evidence remains in the separately frozen P35 delivery. This public
test makes no claim to reproduce those private queue boundaries.
