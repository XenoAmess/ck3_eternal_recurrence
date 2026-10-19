# C12 quiet-to-realm camera source audit

machine_id: `xenoamess-full-tower-eb9d2c1186`; observed_at_utc: `2026-10-19T12:19:23.868313+00:00`.
Identity: fresh `tools/ck3_live_run_id.py machine`.
Read-only source/closed-small-evidence audit. No Game/MCP/screen, live Driver/SAVE, build or matrix run; no shared source edits. Previously accepted siege work is not repeated.

**Software path exists:** after 30 observed quiet game days, C12 can send Native mode=realm; Native29 enumerates a subrealm county vector, unions native title bounds, chooses a viewport-padded native zoom bucket and writes the camera target. **This audit does not establish that the current recorded view has shown every realm county.** The policy clock, actual request/settled result and visual coverage are distinct facts.

## Exact adopted inputs and persistent object

- C12 canonical business source: `d35b59325f48b981ddeca6db294f253e45cc9d48`; actual frozen source root S=`D:/codex-ck3-demos/2026-10-14-robert-30year/continuation42-cold-prep/sdk-v20261019-candidate/src11/xar_autoplayer/bridge`.
- Root-named `_runtime/c12-actual-composition86.json` (2,071 B/pin below) was independently read. Its named admission `runtime/ROOT-P37C12-SOURCE-RESUME-ADMISSION.json` was checked: 4,275 B, SHA256 `95557b119a5838fe101441b220647e7816150e392e5ba58c3d725cca6545fe19`.
- Actual entry `runtime/root_p37c12_mcp_entry.py`: 12,630 B, SHA256 `dd9ed8d5c606425488009ea7af39af1258ddcaa23f5a6273e6bca8d104999b8b`. It reads the admitted source root, wraps original_create once, retains exactly one actual Service (L89-L102), then closes tools over that instance. I read only the first4,096 characters of the larger SDK freeze to locate source_root, not its full body.
- Frozen S/mcp_server.py L1660 constructs one GameplayBridgeService; AUTO closures L2888-L2890 reuse it. S/service.py L678 constructs PeaceRealmCameraPolicy, L683 constructs one LatestCameraFollowWorker.
- Runtime owner confirms normal FULL batches do not reconstruct Service. App recreation or a new source connection resets the clock, as designed; batch sequence/FULL size is not an identity/reset input. Root/runtime report retained Game15512, SDK212016/App248160. Those process facts are owner/composition context, not a new process inspection by this audit.
- Runtime reports first FULL4896 advanced only28 game days. That interval alone is shorter than the30-day quiet threshold; activity/mandatory interruptions can restart it again. This is not a measured current quiet_since value or proof that a later realm request was applied.
- Native source root N=`D:/codex-ck3-demos/2026-10-19-robert-v20261019-native29-camera01/source`. Exact source/header/geometry pins below were verified against retained qualification. Native29 DLL identity remains the owner-qualified 18,443,776 B/SHA256 `7e8534e03ec9cad039c99094aa6cb74b21cc6b8002d26d97e3a126e885a589c1`; no DLL body/load was inspected.

## Quiet anchor, reset and dispatch

`PeaceRealmCameraPolicy.observe` S/realm_overview_camera.py L69-L108 uses **source_frame.date_raw**, with24 raw units/day. It is neither wall time nor a batch/campaign-start counter.

| Condition observed by policy | Clock/action |
| --- | --- |
| First eligible payload without an active hotspot | quiet_since=current raw date |
| Date-quiet_since <30*24 | hold; reports quiet_days_observed |
| >=30*24, no recent overview | realm intent; last_realm_date=current date |
| <30*24 since last realm intent | hold existing overview |
| Identity changes: actor/episode/GamePID/connection_generation | reset quiet_since/last_realm_date/hotspot/mode |
| Date falls below quiet_since | reset identity-owned policy state |
| Non-map, mandatory choice, active event or pending interaction | clear quiet clock; cancel when a previous mode was active |
| battle/siege/objective_siege/moving_player_army/army_destination | clear quiet clock; follow changed hotspot or hold same key |
| Native/publish failure | retry_after_failure clears last realm/hotspot/mode, but retains quiet_since; Service applies30-day presentation retry cooldown |

A quiet period is based on payloads the asynchronous worker actually processes. The latest-only worker may coalesce intermediate payloads; source code alone cannot prove there was no short activity between two processed samples.

**War/idle distinction:** merely having active_wars does not block realm. Static war_objective and stationary player_army are deliberately excluded from activity-reset reasons. The payload's has_player_armies field is not used as a blanket policy blocker. Conversely, any selected active battle/siege/movement reason above resets the clock even in a long-running war. No claim here that missing activity data proves there was none.

S/service.py L4868-L4870 schedules only after the business action. It uses S/auto_camera_current_payload_v1.py to read one existing local semantic publication and rebuild both identity/date and army/objective fields together. It checks owner (actor/episode/PID/connection), map/alive, no date/public/native regression, and date >= known action ending_date_raw. It does not attach an end date to old positions or add a Game pipe query.

The background worker delays the first pending job by0.25 wall seconds. Superseding a waiting job keeps its original eligible_at, so rapid new AUTO calls do not perpetually postpone dispatch. It retains only the latest pending payload. After policy chooses realm, NativeCameraPresentationClient.submit writes shared mapping mode1, current source actor/date, padding0.32 and10s wall expiry; it does not use the gameplay command pipe. A hold sends no new camera request.

## Movement/idle producer chain and residual uncertainty

C12 S/service.py::_auto_camera_hotspot_input copies current active-war allied army fields: current province, controllable/in_combat, army_state, siege_days_left, retreating and move_target_province_id. It copies objective states and source identity from that same post-business publication. It does not splice a prior command-history movement result into a new frame.

S/war_hotspot_camera.py::select_war_hotspot:
- prioritizes actual battle, siege and objective_siege;
- for a controllable non-retreating army with a positive move target, emits moving_player_army at its current land province (destination fallback if needed);
- otherwise emits player_army, which does not reset quiet;
- static objective reasons also do not reset quiet.

**The movement gate does not additionally require army_state='moving'.** A fresh DTO with army_state='regular' but a remaining positive route target can therefore still be classified as an active hotspot. The camera payload omits route_read_status/move_target_observable, so the selector cannot independently disambiguate a residual target from queued movement. This is a concrete predicate/information limitation, not proof that the current game has such a residual.

Repository producer `native_bridge/src/ck3_12002_army.cpp::Route` L171-L207 clears route and sets target=-1/observable=false before reading each row, returns empty for count0, and sets target only after complete nonempty route resolution. The rows are freshly constructed at L1332; state is read at L1344 and Route called at L1349. Repository bridge serializer emits target=null when unobservable, and C12 war_contract normalizes the provided current values. Thus the reviewed source does not intentionally retain a previous row's target when the new route is empty.

However, the exact retained Native29 army producer TU source pin was not independently established in this audit; nor is there a closed natural “regular + residual positive route” sample here. Do not claim that the actual Native29 route buffer is always empty immediately on arrival, or patch the activity predicate based on a guessed native timing. Tightening it to state=='moving' without source/actual evidence could also suppress genuinely queued movement. No such patch is proposed now.

## Native29 bounds, zoom and coverage boundary

Native29 camera TU L197-L240 obtains a current native snapshot on the owner pump. It rejects non-map/dead/mismatched actor, request date in the future, or age>7*24 raw units; active event/interaction preempts it. It requires the unique owned CK3 HWND and its actual nonzero client rectangle. Minimized windows are permitted under the revised owned-window test.

For realm mode it calls existing `ck3_12002::ReadSubrealmCountyIdsV1`, rejects failure/empty/>16,384 IDs, resolves each title and calls native ComputeTitleBounds, then unions all returned county rectangles. Any bounds/resolve failure aborts this camera TU; query-only mode returns bounds_available without moving the camera.

**Vassal completeness:** the intended shared reader scope is actor plus recursive vassals, rather than directly-held domain only. But performance_native owner explicitly has no independently pinned single source leaf proving the old inherited reader implementation in Native29. Native29 qualification states M1_ABI_adopted=false; the newer M1 holder/parent/cycle/completeness enhancements are not adopted into its355 retained objects. The frozen camera call alone does not certify full county-set completeness. It is therefore inappropriate to infer “full realm=direct2” or to promote a count/vector into complete coverage without the old-reader source closure/actual county evidence. This audit leaves that adoption proof unknown and does not scan the large historical closure.

Geometry N/include/xar_bridge/realm_camera_geometry_v1.hpp:
- validates bounds and client width>=320/height>=240; padding finite and <0.45;
- computes a conservative square extent from X/Z bounds and real client aspect, divided by(1-2*padding);
- consumes descending native thresholds, now allowing the original terminal -1 while rejecting <-1, nonmonotone tables, invalid extent or >4,096 entries;
- Native TU maps the selected bucket to a native zoom index and checks it against zoom_count; reads zoom/angle tables, finite canonical target, and requires canonicalization to preserve X/Z center;
- checks superseding sequence/expiry before writing actual native zoom index and camera target. It then observes target unchanged and current==target within5s before reporting settled. This is an actual Native camera-target postcondition path, not merely a queued ACK.

**coverage_verified:** Result field defaults to0; this frozen camera TU never sets it to1. That is absent coverage telemetry, not evidence that the geometry was clipped or zoom failed. S/NativeCameraPresentationClient.latest separately reports camera_postcondition_verified only for settled+valid index. camera_receipt_outcome treats that as completed regardless of coverage flag. Setting coverage_verified=true merely because a target settled would falsely upgrade a fit model to viewport proof and is not a fix.

The padding/bucket model is not a screen-space projection/occlusion proof. A matching natural realm request + settled result with county vector/bounds/index/current==target establishes software application; original recorded viewport pixels are still needed to establish that the desired complete realm is visible. Hotspot/siege success cannot substitute for that realm-specific evidence. This audit does not add a pixel requirement or rerun siege; it states the existing acceptance boundary.

## One definite clock weakness / minimal future correction

In C12 S/service.py::_select_auto_camera_hotspot, the retry-cooldown early return precedes policy.observe. During those30 game days the selector computes hotspot but the quiet clock does not consume blocked/activity samples. retry_after_failure preserves quiet_since.

Counterexample from the actual branches: quiet_since=day0; day30 realm attempt fails, cooldown ends day60; a battle or mandatory window is seen at day45 but returned early; day60 is idle. Current policy can immediately emit realm using quiet_since day0, although30 uninterrupted quiet days since the observed interruption have not elapsed. This is a conditional source defect, not a claim it explains the user's current view.

Smallest conservative correction for the next reviewed source update: during cooldown, invalidate **only the quiet anchor** on observed blocked/active-hotspot input, without recording a followed hotspot/mode or submitting a request. Reuse a single policy activity predicate; keep the existing failure backoff and post-business source guard. A day30-failure/day45-activity/day60-idle focused check should then withhold realm until a new quiet interval. No shared source was modified and no test was run here. Do not loosen Native date/target guards, force coverage=true, or alter movement semantics without evidence.

## Pins / closure

S and N are the exact roots defined above; other paths are repository-relative.

| Leaf | Bytes | SHA256 |
| --- | ---: | --- |
| `S/service.py` | 871839 | `b6e078c2397b355aac9bed24834ad4921c7083b477234d2d66438fd32933a3af` |
| `S/mcp_server.py` | 263022 | `1980c01abb14b2cb579bf3dba3bc1a58f9d4b89d7b8181db356a4b216b37e2b7` |
| `S/realm_overview_camera.py` | 13511 | `5878650d997058411b6d73b2ad531147a8441632339c18957890b28b5d4cd037` |
| `S/auto_camera_follow.py` | 9245 | `8b1a2ef99f73ccd5a31696173cc9e9544530f8bdd83507559fcc882ebec3b9b1` |
| `S/auto_camera_current_payload_v1.py` | 2846 | `e2a6cc9ae1a061a0676c3162838b61eb4b42ebaf025934bc27e42a5a2a57a52f` |
| `S/war_hotspot_camera.py` | 13650 | `b00487eb816a450531955199d2d85b344a3aac30197132c1a685f235b2fabe96` |
| `S/war_contract.py` | 226160 | `c2e500e5bf923a6618004d8cdd027c5826a119d33c9bbc58846030b63917eb6a` |
| `N/src/camera_presentation_v1.cpp` | 15775 | `656055437114c216f8703197cc010f4443025969d16cece5fd63333bce3c6abf` |
| `N/include/xar_bridge/camera_presentation_v1.hpp` | 3124 | `976491c0821a651fd6d38ff05427a5a6ed0810ae06776ecede16241348cbfc10` |
| `N/include/xar_bridge/realm_camera_geometry_v1.hpp` | 2180 | `bf38c223793d44d2904a62fe2903078f37079c9c5562abf9d8bc679536ecc80a` |
| `_runtime/c12-actual-composition86.json` | 2071 | `05a457bb822dd72d45baa17f95c288e9c4b239ffa687b23cef0cf73439875c9f` |
| `docs/ck3-native-ai/evidence/native29-camera-build-qualification-2026-10-19.json` | 12034 | `ed50db122c0c7a403ee7755ad8c4393b829ad9b258a715928f6870ff6f992b47` |
| `docs/ck3-native-ai/evidence/c11-native29-actual-cold-adoption-2026-10-19.json` | 4450 | `53d39c582e7dfddf4e591cc583973c929e873478bafba873962e9746e5661f2a` |

Entry metadata caveat sent to Root: its mode-record producer contains literal machine_id suffix eb9d2c1286, unlike actual stable eb9d2c1186 and the independently read composition/admission. That typo was not used as target-machine identity proof and was not changed.

Single new repo audit MD <=16KiB, original other128/review unchanged. No external write or existing M1 artifact edit.
producer_closed: true; future_write_bytes: 0; allocated_bytes: null; physical_release_credit_bytes: 0.
