# R12 / R13 execution handoff

Historical source machine: `desktop-3fevhd2-1c74096080`. Future manifests explicitly name their own source machine; this tool does not assert a current-machine installation or live acceptance. This tool sends no game commands. It prepares the existing native APIs and a read-only consequence verifier. R12 and R13 are still pending actual gameplay; synthetic qualification is not live completion or film approval.

## Existing entry points

Use `ck3_move_army(army_id, target_province_id, expected_revision)` for both normal initial Move and R13 reroute. The MCP tool delegates to `service.move_army` and `_execute_typed_move_army`; it bypasses the planner's enumerated destination list through its existing typed capability contract and still requires actual native validation. No new tool or gate relaxation is needed. R0172 `018-move-short-sea.json` used this exact tool and received an actual moving route. Preserve `ck3_execute_step("move-army-...")` rejected outside the planner list as a wrong-entry negative control.

Preview uses `ck3_execute_step(step="preview-move-army-U-to-P", expected_revision=R)`. Halt uses `ck3_execute_step(step="halt-army-U", expected_revision=R)`. The existing Halt return explicitly says `halt_submitted`, `postcondition_verified=false`; record an independent later native frame before claiming a consequence.

Read `ck3_take_snapshot` (ordinary default without full transcript), then `ck3_query_army_strengths(army_ids=[U], expected_revision=R, profile="ordinary_core_v1")`. Ordinary core contains the current movement progress, actual loaded cutoff and first-edge remaining duration; retained full-history journals are unnecessary here. Preserve each actual Driver raw result referenced by the query history receipt. Do not feed a compact MCP display summary to the verifier in place of the full raw result. A scoped query reduces exported rows; it is not a destructive drain of all histories.

## Fresh session and seed

Root owns the single CK3 session and its fresh Steam-offline evidence. After reopening the normal campaign checkpoint, capture new PID, process creation FILETIME, connection generation, episode, living owner and selected Army full/native IDs. Never reuse the closed R0173 PID14544 or its episode as a new live binding.

The closed R0173 checkpoint was date53145576, Army18/owner31254 at Province1036, embarked, complete empty route. The null raw target was explicitly unobservable; do not describe it as proven cleared. This is a preparation seed, not a locked-action sample. R11's actual progress9799 was below actual cutoff50000 and cannot qualify R12/R13.

Use this finite candidate sequence only if each new native preview and validator accepts it:

1. **R13 first:** From fresh actual Army18/C1036/empty, preview target1033. Candidate route is `[8653,1034,1033]`; require the actual new complete route to have at least two hops and distinct front/tail. Call typed Move once and preserve its actual later applied route.
2. Advance natural days using the existing daily sentinel below. While still on the same original first edge, wait for `actual_progress.raw > actual_loaded_cutoff.raw`. Read both from the same joined strength frame at Q100000. Equal, missing, malformed or unavailable readings do not admit a locked case.
3. Fresh preview alternate1034. Require alternate distinct from current Province, old front and old tail; require actual preview to keep old front and branch before old tail. If the expected path is `[8653,1034]`, it avoids old tail1033. The preview must be pinned to the current snapshot/revision/connection/episode; read it again if that frame changes before action.
4. Call `ck3_move_army(18,1034,R)` exactly once. Bounded read-only polling may wait for asynchronous application. Require the actual later paused same-date route to equal the new preview, its first edge and progress to remain intact, and its suffix to change. Then naturally advance to an actual frame at old front8653 with a remaining route toward1034, and finally an actual stationary/empty-route frame at1034. Submission or reaching only8653 does not close R13.
5. **Independent R12:** Use the actual R13 final1034/empty frame as a new baseline. Start a separate normal preview and Move toward1036; `[8653,1036]` is only a candidate, never a promised route. Require a new actual multi-hop route. Again observe progress strictly above the actual cutoff while on its first edge. Submit `halt-army-18` once. The actual later paused same-date route must be exactly `[old_front]` and retain the same progress. Naturally reach that original front with an empty route. Do not reuse a single-hop route left by a previous Halt as the next case's normal initial Move.

If the candidates are rejected or the preview is not genuinely multi-hop, retain the attempt and choose another previewed lawful route in the owned campaign. Do not edit saves, teleport, change enemy control, use old tail shortcuts or manufacture lock readings.

## One natural day and finite stopping

For actual date D, use existing `ck3_execute_step` step:

```
research-arm-tactical-daily-sentinel-v1-D-to-DPLUS24-speed-5-mode-terminal-a-1-18
```

Replace D and DPLUS24 with actual integer date values, preserving the exact grammar. Arm while paused, resume once through the existing `resume` step, poll read-only until an actual paused frame, query `research-query-tactical-daily-sentinel-v1`, and join a fresh scoped strength read. Require a new sentinel generation, target/trigger D+24, one completed daily tick, no overshoot/abnormal flag and actual pause. `date_deadline` may coexist with expected `army_position_changed` or `route_target_changed`; do not force a date-only reason on an actual arrival day. Unrelated modal, combat, death, owner/connection change or abnormal stop suspends the card for explicit handling.

Record every natural day from the initial Move to the final endpoint; the verifier rejects gaps. Initial lock search budget: 12 natural days or original first-edge arrival, whichever occurs first. Once admitted, first-edge arrival budget is `ceil(actual_first_edge_remaining_q100000/100000)+2` days. Final alternate arrival gets an explicit finite case budget (suggest 30 natural days; this is an operational limit, not a promised travel ETA). Never unpause indefinitely or retry an uncertain action automatically.

If a daily publication skips the original front and only shows a later Province, final arrival alone does not prove the required intermediate observation. Preserve the attempt without claiming that edge; use a new independent case with a longer observable leg or an already qualified actual transition record. This lane adds no new hook. The current closed R11 whole-route timeline was unavailable, so it cannot provide a trustworthy total ETA.

## Independent evidence and filming windows

For each case retain baseline, actual initial preview, exactly one normal Move request/result, its actual applied frame, all daily sentinel results, the admitted locked frame, exactly one case-action request/result, an independent later applied frame and final actual endpoint. R13 additionally retains the exact alternate preview and actual first-front arrival. Each frame pair includes the snapshot and the full scoped strength raw file, exact bytes and SHA256. The manifest's command counts describe the complete case-owned request log; they are not proof of absence of unlogged outside commands. The operator must preserve exclusive session custody and the no-load window.

Useful film marks are: baseline/normal-Move path; paused locked numeric admission (show actual numerator/cutoff); action submission; independent route/progress consequence; R13 actual old-front observation; final stationary endpoint. Natural-day markers should be tied to actual sentinel date/sequence. Film only after Root's recorder is active; this lane has neither started a recorder nor created raw footage.

[`verify.py`](verify.py) is read-only; its `admit_locked` function is also a pure guard that an agent can consume before deciding whether to issue an action. Fill an independent R12/R13 manifest using the templates, replace every null placeholder with real exact references and current bindings, then run:

```
python -B /PATH/TO/REPO/promo/ck3_native_war_ai/episode-04-march-logistics/tools/review02/locked_routes/verify.py --manifest /PATH/TO/CASE.actual.json --output /PATH/TO/NEW-AUDIT.actual.json
```

The verifier never sends commands, never overwrites an existing audit and does not invent human approval. Its PASS is limited to supplied exact native observations and the operator's session custody; it is not independent detection of every possible intervening load or external command. Game version/preflight comes from Root's managed-session evidence rather than an invented field in the snapshot schema.

## Relative-path and reuse contract

The command accepts an explicitly supplied manifest path. Relative `owned_evidence_roots` and evidence-reference paths resolve against that manifest's directory, independent of the shell's working directory. Absolute paths remain explicit caller inputs. Existing files keep exact bytes/SHA bindings. The source machine is read from the manifest and must agree with its pinned process receipt; historical source IDs never become the current host's installation or live qualification.

The pure `admit_locked(observation)` guard returns the actual front/tail, progress, cutoff and bounded first-edge duration. It grants no gameplay action by itself: an agent must also preserve the joined owned frame, original edge and lawful command/preview preconditions. `r12`/`r13` validate observed consequences. No automatic executor or active agent policy is installed by this package.

The historical [R0173 knowledge entry](../../../../../../docs/ck3-native-ai/episode04-r0173-boarding-halt-12004.md) and its in-repository ZIP retain the actual R11 negative control. No C-drive module or unarchived local source is dynamically imported. Earlier rejected generic-Move experiments are historical diagnostics, not a required production patch.

## 2026-10-16 actual R0174 continuation boundary

Latest source machine: `desktop-3fevhd2-1c74096080`. See the [R0174 archived evidence and replay entry](../../../../../../docs/ck3-native-ai/episode04-r0174-common-t0-control-12004.md) and [current daily report](../../../../../../docs/autonomous-agent-progress/daily/2026-10-16.md). R0174 is closed; never reuse PID17468/create134365505726865638/gen1/episode `native-31254-0d067159706e` for the next session.

The stationary21-day control is an actual `saved_t0_continuation_control` pair PASS, not two newly loaded treatment/control arms. It loaded9ab3 and remained at2624/Army18/1196/1196 with complete empty route across exact raw53145048→53145552. Historical R0173 had saved that T0 and continued without loading9ab3. Original R07 seven-day/no-economic-settlement/stationary-T0-new-Move requirements remain unclosed; research stays3/14, no R12/R13 credit.

R0174 now has a separate45-second Halt raw:56479663B, SHA `6d28162df56f95b7ea85c252dd8d61794c73b87c00c54b6ab7002945f46f1f12`,1350frames,2560×1440/30fps,no audio; strict whole decode PASS. Suggested source candidates are0–4s movement→standby and4–20s standby. Upper-left coastal tooltip persists; continuous-clean review and human signoff remain pending. Wall-to-encoded timestamps are uncalibrated. Do not claim that Halt was present in the older R0173 six-minute raw, or silently update frozen story-a02 to that effect.

The actual final R0174 control checkpoint is date53145552, Army18 at2624/regular/complete_empty. This differs from R0173's sea1036 checkpoint used in the candidate sequence above. The next operator must select and bind an explicit normal checkpoint, obtain a fresh actual position/route and legal preview, then use this existing verifier. Candidate1036/8653/1034/1033 hops are not a promise for a different starting location. Obtain a new initial normal Move for each independent locked case, actual progress strictly greater than same-frame loaded cutoff, one action, independent later route consequence and actual endpoint. No one may promote the current unlockedHalt or45s raw to lockedHalt/reroute acceptance.

Source1463/a05 did not include the new supply-parent-join patch applied after closure. Next nativea06 build/qualification and its exact new PID/episode must be recorded independently. The0/11 new clean packages and3/14 research counters remain unchanged at this cutpoint. All external child packages stay under the existing512MiB shared reservation and original2026-10-16T07:45:01.597Z review deadline; no automatic renewal is implied.

## 2026-10-16 本机R0177闭场、R03原件与story-a05草稿

本段所有现场、素材和稿件事实均属 machine_id: `desktop-3fevhd2-1c74096080`，按Root本次实际回执滚动追加。 原R0173/R0174/R0175/R0176的证据和runtime身份继续按原档读取，不能复用为新场身份。

- R0177已有Root实际CLOSED回执：3219 B，SHA-256 `9a2f12db0d934f8cb01236c7ca8e88a1515b18ef552677ccc13df70841bc9797`。coastal原片45秒/1350帧，完整解码PASS；`clean=false`、`human=false`，不授连续clean或人工签核。
- R03原件在raw53147472、同一callback188中，7条preferred writer实际扣兵11（1+1+3+1+2+1+2），siege11/raid0，原件正消费通过。正式整卡审结仍待Root；本次汇报暂保留整卡5/14＝35.7%、核心业务3/11，不先增加分子。
- [story-a05完整草稿](../../../review02/story-a05/README.md)为69/69＝100%，8351字；`TTS/provider=0`。这是草稿接受率，不等于最终冻结、声音、新成片或人审完成。
- 共享源码解释见[拆合军库存权重/取整顺序](../../../../../../docs/ck3-native-ai/episode04-split-merge-stock-weight-order-12004.md)、[统帅容量与零准备量](../../../../../../docs/ck3-native-ai/episode04-commander-capacity-zero-preparation-12004.md)。新增source的最终提交、a08 DLL、构建及新冷验结果由实际回执另记，本段不预填未来SHA、CI通过或实机资格。

当前交接与后续来源以[本机交接入口](../../../../../../docs/handover/2026-10-15-war-episode04-machine-resume.md)为统一转链。
