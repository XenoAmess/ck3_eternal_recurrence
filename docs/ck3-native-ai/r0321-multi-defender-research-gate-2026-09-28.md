# R0321 two-defender research forecast remains outside contact actions

## Frozen source boundary

- Source notice: `WAR/M5-WAR-CASH-20260928/SOURCE-R0321-WAR-FORECAST-RED-v1.json`, SHA-256 `6CCA6BE7CD31828F662271C9FF0B58E9C7D48081A587C9D5833DA9A7C2D6DD20`.
- Formal report: 388,302 bytes, SHA-256 `7A7774C59DA6099B0A1FFD650AB21A29407BD8B22B1056C7B6F5053251A5CF30`. It records R0321's paused `native:23`, public revision 24, native revision 23, raw date 53219928, WarID 16777231, ArmyID 83886367 and target ProvinceID 2629. Its siege partition is available with ordered target defenders `[50331920, 83886484]` and no observed offsite hostiles. The native route has six hops, so it does not prove immediate target contact.
- Extracted v3 raw row: 2,080,166 bytes, SHA-256 `865EA7B7AC1B4A680E2BE3A1D84012C67CF9550474075E4A917EFE043CCCDD51`. The source identifies the row as `/command_history/3919` in the H3911 driver. Its read-only query was accepted for the same `native:23`/24/23 frame, target 2629, entry 2630, attacker `[83886367]` and ordered defenders `[50331920, 83886484]`; `actual_route_dependency=false`. The raw source driver's 46 MB bytes were not transferred for independent equality comparison. The extracted row omits its original request, before/after state, episode ID and connection generation. The source notice and formal report supply the offline reconstruction's build/profile/frame identity; this is not a live planner replay.

The v3 input reports `input_observation_ready=true`, while `monte_carlo_ready=false`, `transition_fidelity_gate=false` and `planner_usable=false`. Its model still lacks loaded phase-event transition and exact original-trace parity. A syntactically accepted input read is no attack authorization.

## Offline research result

The read-only reproducer at `D:/ck3-research-artifacts/r0321-scope-exact-001/replay_readonly_canary.py` (SHA-256 `44C361DC9F43625D18B9655439A58A58F4A8F76180AC9944DDB0C686D785B2A2`) validates the three transferred files' exact hashes and runs the R0321 v3 payload through the repository's 512-trial research sampler at commit `ca56f7ffe`. Its immutable result is `D:/ck3-research-artifacts/r0321-scope-exact-001/offline-canary-result.json`, SHA-256 `F460927DD38672DEEC3D3EB41F213CAFDEACD5C52F8007CF8109184ED1188EEF`.

| Research output | Observed value |
| --- | ---: |
| Model wins / losses / unresolved | 512 / 0 / 0 |
| Model resolved-win Wilson 95% lower bound | 0.992553 |
| Model p90 hard loss, Q100000 | 26,213,443 |
| Existing provisional hard-loss budget, Q100000 | 46,660,000 |
| Research `contact_admission.admitted` | `true` |
| Patched canary status | `multi_defender_research_only` |
| Patched canary `planner_usable` | `false` |

The 512/512 result is a **phase-events-disabled model outcome**, not a measured or calibrated CK3 battle win rate. Commander or knight death, future reinforcement and participant exit, voluntary retreat, and future daily stat, width and advantage refresh remain unquantified. The result cannot authorize a move, a date advance, or an attack.

## Action-seam correction

The first #502 commit removed the old single-defender guard from the research canary. An independent review found that this could turn a later one-day, two-defender frame into `provisional_admissible`, which the existing siege ingress could consume as a real contact move. The offline result above shows why this was a concrete risk.

Follow-up commit `ca56f7ffe` keeps complete ordered multi-defender v3 inputs available for **research only**. It returns `multi_defender_research_only` with `planner_usable=false`, then separately requires exactly one defender before the formal provisional action branch. The one-day two-defender planner regression returns `selected_step=null` and `active_attack_allowed=false` both with the actual research result and with a deliberately injected stale `provisional_admissible` result. The two relevant local test modules passed 17/17; this is static and offline verification, not live gameplay acceptance.

The qualified production forecast producer and its activation are separate and remain unavailable. R0321 requires qualified same-frame battle probability, expected-utility comparison, complete participant risk and formal action/postcondition evidence before a contact decision. Historical R0271 RED is unchanged.
