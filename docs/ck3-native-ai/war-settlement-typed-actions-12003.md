# Existing typed war settlement actions, CK3 1.20.0.3

Prepared 2026-10-03 15:17 Asia/Shanghai from source e38eb9bd7757275746d0ffed1c630fc1540d087e and saved coordinator artifacts. This file-only lane binds Steam build 25652598 and EXE SHA-256 `94B55397ABB687A3DCD436805A5D885E6BE90FA6C693FEB44A9E3BBEEADE02A6`. It does not operate SDK, game, pipe or window, and does not mutate shared Git.

The existing victory sender is complete and reusable for Robert's actual three defensive wars. No new native command, ABI scan, permit or compile flag is needed. The native score and end-war input tree is recorded in [war-end-conditions](war-end-conditions-1.20.0.3-2026-10-03.md); it precedes this execution recipe.

## Existing native submission

The `.3` factory gates the exact executable SHA and reuses the reviewed `.2` diplomacy and command implementations. The existing exact `.3` core-comparison is GREEN/UNCHANGED for both modules. `SubmitEnforceDemands`, `SubmitSurrenderWar` and `SubmitOfferWhitePeace` share the production submit path in `ck3_12002_diplomacy.cpp`. It resolves the full-generation WarID, rereads paused/alive/current player and side membership, requires current primary leadership, rebuilds the requested context, and reruns final CanSend at `0x307C040`.

For victory the native resolution constructor `0xCF57D0` takes `true` for **player victory on either physical side**. Robert defending therefore selects attacker-defeat. White peace separately rereads the loaded CB permission bit and constructs special index3. `0x2968170` constructs a 0x368 send packet; the existing owning clone is queued at `0x37F06F0`, command manager `image+0x5CC1240`, flags0x0E. Temporary and embedded contexts retain their established destruction lifecycle. Queue success is submission only.

## Current observed boundary

The saved date53236608 options are production-live primitives, not current action authorization: War16777231 is `individual_county_de_jure_cb`, War129 is `minor_religious_war`, and post-refusal War50331736 is `populist_war`. Robert29829 is primary defender in all three. Their observed victory and white-peace final CanSend values were false; surrender was mechanically legal. No termination was submitted by this lane. These saved negative rows are not reused as a future same-frame decision.

| Existing MCP | Current public scope | Readiness boundary |
|---|---|---|
| `ck3_enforce_demands(war_id=W, expected_revision=R)` | Any actual CB, current primary player, player-relative score100 | Default capability; fresh native context/CanSend still decides. |
| `ck3_offer_white_peace(war_id=W, expected_revision=R)` | Existing narrow primary-attacker claim/de-jure policy slices | Current Robert defender cases are not included; `.3` final recipient response is still unavailable. |
| `ck3_surrender_war(war_id=W, expected_revision=R)` | Existing de-jure/Raiktor/terminal attacker slices | Native legality does not implement current defender title-loss policy. |

This table separates mechanical native sender availability from typed policy readiness. It introduces no new combat restriction. Continue the military loop using current observations and use the existing victory action once native legal100score is observed.

## Future single-submission recipe

1. In the retained Root SDK session take a fresh paused snapshot, retaining exact executable identity, actor29829, episode `native-29829-2bc2d599f7f9`, full W, primary leadership and public revisionR. Query `ck3_query_war_termination_options(war_id=W, expected_revision=R)` and retain its same-frame metadata. Choose victory only when the actual player-relative total is100 and the victory context's native validator/available are true. This is the existing action's readiness, not a newly added gate.
2. Record pre-state gold/prestige/piety raw Q100000 from the snapshot and campaign root via `ck3_query_campaign_root_context_v1(expected_revision=R)`. Refresh public revision as required by the retained session. The root context covers the player's held-title partition and realm/vassal scope; it is not a generic arbitrary enemy-title holder query.
3. Call `ck3_enforce_demands(war_id=W, expected_revision=R)` exactly once using the fresh current revision. The production driver already waits for the exact old full W to disappear. A failed/timeout/uncertain receipt is retained; no blind second submission is inferred from it.
4. Independently take a new paused snapshot and `ck3_get_war_state()`. Require absence of exactly W, preserve other actual wars, and compare actor/episode/date with the submission context. War absence following the known victory request establishes the observed terminal transition; ACK alone does not. Retain any active event or succession/invalidation changes that affect attribution.
5. Read the actual material aftermath. Compare raw resources and held titles/realm/vassal scope using fresh snapshot and campaign root. For populist victory additionally use fresh faction alerts and, when its already available query permit is enabled, player prisoner collection to observe the old faction33554465 alert's removal and rebel70766 custody. A targeting-alert row disappearing does not itself expose the global faction object's destruction. These readbacks are observations, not prisoner actions. Save the resulting normal checkpoint once.

## Material outcome limits

All three present defender-victory CB blocks avoid conquest title transfer, but different resource and custody effects apply. De-jure defeat includes attacker reparations; minor religious defeat includes defender piety and attacker payment; populist defeat includes faction cleanup and attacker imprisonment. Reuse the exact installed-stock clauses in the end-conditions topic. Record only actual before/after fields: no guessed payment, prestige/fame, piety, truce, dread, legitimacy or individual custody claim.

Current general observations can verify Robert's gold/prestige/piety, own held-title partition, realm/vassal scope, war lifecycle and optional faction/prisoner changes. They do not expose every nonclaim target holder/liege transition, all attacker participants, exact opponent resources, generic truce set or every ancillary CB effect. In particular target2128 belongs to the wider realm: absence from Robert's own held-title list cannot prove its holder changed. Generic claim-only terms and historical H2743 data are not substitutes. Report an unobserved material field as unobserved without blocking the existing useful victory transition.

Negotiated white peace remains a scoped construction entry if it becomes useful and native legal: close the exact `.3` final recipient evaluator and extend the same options DTO, then implement the actual current-CB defender policy. Current defender surrender additionally needs the chosen dynamic loss scope. Neither gap requires duplicating the existing owned sender or stops current combat.

## Reused verification and report fields

The native diplomacy header, sender and `ck3_12002_diplomacy_test.cpp` hashes match their prior GREEN receipt. That fixture invokes actual production sender functions with native seams and checks both physical-side outcome polarity, CanSend rejection, full IDs, owned clone/queue and context destruction. Retained fixture binary SHA is `74d705ea6a89e82ab45078661437bf0f94c36968ebf3c688f1bf54849cfbbd4a`; it is a test executable, not the CK3 EXE. The reviewed `.3` reuse receipt establishes ABI compatibility, not live termination.

Existing NativeHeadlessGameplayDriver tests check exact old WarID disappearance for enforce and distinguish white-peace/surrender `submitted_pending` from applied. Registered MCP fixture actually calls enforce through a callback driver; it only lists the other two tools. These complementary fixtures are not one native-sender-to-SDK end-to-end run. No concrete production sender defect was found, so no fixture was repeated and no new component was created.

Completed: confirmed reusable mechanical senders and legal100score victory scope; delivered once-submission and independent material-readback recipe. Why: preserve military delivery pace using established primitives. Readiness: native/static-ready actions, existing Robert options production-live primitive; Robert termination remains live-pending, with no victory/OODA credit. Test/artifact: `Z:/ck3_mod_rewrite_process_assets/g2-resume-20261003/war-settlement-typed-action/ROOT-DELIVERY.json` indexes source hashes, retained native/ABI evidence and child reports. RED: no new capability defect; current defender negotiated/surrender observation/policy gaps remain documented. Next: continue combat and later enforce an observed native legal100score, collecting actual postconditions. Commit/push: coordinator-owned adoption pending; this lane changes only isolated external artifacts.

## 2026-10-04: current defender de-jure white-peace proposal

The retained Root query at date53244648, public2/native493, actor29829, ordinary episode `native-29829-2bc2d599f7f9` observes War16777231 (`individual_county_de_jure_cb/index17`): primary defender Robert, opposing primary30097, player score+7. White-peace context construction, final native CanSend and availability are true; raw AI quote163736/Q100000=+1.63736, auto_acceptfalse. CB-specific terms and final recipient response are typed unavailable/null. War50331736 and129 still have unavailable white peace and victory; no result is inferred from those saved negative rows. The real three leaves were consumed once and pinned at `war-settlement-typed-action/next-paused-war-options-r25/actual-three-war-consumed-01/ROOT-DELIVERY.json`.

### Native role/input tree reused before policy expansion

The exact .3 reused reader and sender already resolve full W, paused/living current player, exactly one participant side and primary leadership. White peace reads loaded CB permission bit7, identifies the opposing primary through the actual physical player side, constructs special-index3 context, and runs `0x307C040` CanSend. Raw acceptance from `0x307C460` and observable auto-accept are proposal inputs. The current .3 reader does not publish a final recipient evaluator; its missing response is not an execution restriction. Submission independently rereads these real inputs, reconstructs the context and reruns native CanSend before the owned queue packet. No native ABI, sender, DTO, flag or protocol extension is required for the current defender proposal.

```mermaid
flowchart TD
    S[Exact .3 paused actor/full W/actual side/primary role] --> P[Loaded CB permits white peace]
    P --> C[Native special3 context/opposing primary]
    C --> V[Native CanSend and raw AI quote]
    V --> B[Same-frame options binding/current primary defender de-jure17]
    B --> D[Root chooses one useful positive-quote proposal]
    D --> N[Existing sender rereads current roles/context/native CanSend]
    N --> A[Queue receipt: submission only]
    A --> R[Independent paused actual war/status/title/resource readback]
    R -->|Exact old W absent after known proposal| E[Observed white-peace end-state; retain actual outcome context]
    R -->|W remains| U[Pending/rejected/unresolved as actually observed; continue military work]
    V -. Final reply not projected .-> F[Unknown prediction quality; preserve response null]
```

### Minimal functional extension and honest quality boundary

g54 `_white_peace_readiness` only dispatches two primary-attacker slices, so a legal current defender proposal is omitted from `action_steps`; named MCP and generic execute both reject it before reaching the native sender. This is missing functional coverage, not a remaining nonwar or religion authorization rule. Reading claim-only terms cannot change Robert's role and is unnecessary for this white-peace proposal. The source extension adds the actual current primary-defender de-jure17 branch, using existing same-frame options and positive observable native quote, while reusing the published `ck3_offer_white_peace(war_id, expected_revision)` sender. Unknown CB terms and recipient_response do not become gates. Original attacker behavior and native final predicate remain in force; the quote is never called an accepted answer.

The selected counter-policy is deliberately a chosen current proposal, not a full final-reply predictor. It has not adopted the absent .3 final evaluator or previewed every CB effect. If repeated actual proposals demonstrate that prediction quality is insufficient, the construction entry is that exact .3 final evaluator projected through the existing options MCP; no generic gate or new protocol is introduced now. A still-active W after submission is a real game outcome to record, not proof that ACK meant peace. Current title-holder publication can independently observe target2128 after resolution, and snapshot gold/prestige/piety/campaign scope can measure material changes.

Root-only action recipe: at its next actual pause refresh only War16777231 options, choose the proposal from current legal/positive data, send the existing named action at most once, independently observe exact old W absence or remaining status plus other wars50331736/129, target2128 holder/lieges, resources and any actual event/answer, then save a normal checkpoint once. Prepared call files are in `war-settlement-typed-action/white-peace-current-defender-g54/`. Before actual execution there is no peace/day/victory credit. Fixture readiness and exact source hashes are supplied by that package receipt; genuine native-memory fixtures and in-process registered MCP are not actual CK3 settlement.

## 2026-10-04：当前守方单次白和平提议与三个正常回复日

已封单次offer后一个自然日的独立读回为submitted/pending：offer_attempt_count=1、recipient_answer=null，War16777231仍在实际列表[16777231,50331736,129]，peacecredit0。该旧帧date_raw53246712、累计4266/resumed1113/Oct4新增241保持原阶段；不把提交或pending当作接受、战争结束或胜利，也不重发提议。

Root actual03 **SDK64107 closed/exit0、GREEN** 独立确认date_raw **53246760**／native **860**／public **5**，三个war仍active，各自score为 **16777231:12、50331736:−13、129:−29**；Robert存活、主军regular@2640、event/interaction=null。已完成三个正常replydays、累计 **4268**／resumed **1115**／Oct4新增 **243**，Oct3 frozen **777**；正常 **h6267／93381860B／SHA256 `e5f1e0538a26f0b675dcf5dac3fca6b561b684e44b29cd2423aab50a150c3518`**。这些是Root实际完成的观察/保存；三个正常回复日后仍pending/0accepted，peacecredit与war-win均0。此前两replydays4267/h6265保持旧阶段，未来64日预算及仍在运行的下一轮不提前计。

最新已观测campaign_root_context.capital_province_id为 **2619**（Robert29829、native850/public2/date53246712，capital_ready=true），对应county2142；**2640** 是county2115的capital。今后的current-player-capital标注用2619，历史2640交接与封存事实不重写；此capital缓存不刷新成native860读数。原三authorized查询未发布资源余额，不从monthly income推余额。Root实际hot Python为 **210943a7/g56**，native仍 **g54/PID8898/R25**，没有v50部署声明。

资格仍为 **production-live primitive：单次提议及其后独立观察**，peace settlement未完成。回复scheduler未闭合不阻断ordinary gameplay，本追加不新增门禁或acceptance预测。sealed post-action delivery与CAPITAL-CACHE-FACT只复用原owner缓存，actual03只使用Root sole consumer提供的事实及receipt链接；本doc consumer新增0日/动作，不读取raw或运行下一轮SDK。

封存输入：`Z:/ck3_mod_rewrite_process_assets/g2-resume-20261003/war-settlement-typed-action/white-peace-current-defender-g54/post-action-consumption/ROOT-ACTUAL-CONSUMER-DELIVERY.json`、同根 `raw-query-lane/actual-authorized-after-reply-003-005-007-consumed-01/CAPITAL-CACHE-FACT.json`；Root actual03索引仅链接 `Z:/ck3_mod_rewrite_process_assets/g2-resume-20261003/runtime-preparation/v51/ROOT-ACTUAL-REPLY-DAY-03-RECEIPT.json`，未读取该receipt/raw。


## 2026-10-04：WarID 16777231 独立退出，结束类型仍未观测

同一 ordinary episode `native-29829-2bc2d599f7f9`、Robert 29829、唯一一次白和平提议后，sealed 日账的 exact WarID membership 为最后仍在 `53246784/native874/pub5`、首次不在 `53246808/native877/pub8`：reply03 + march02，共 5 个自然日。DAY55 `53248080/native1089/pub220` 是后来仍保持消失的观察；不能写成 58 天才结束。边界缓存 SHA `dc0e203d2a77e71cd7822267730734c9b2f62168accd60ec57facbed24c50060`。

readiness 为 `production-live primitive`；有限“单次提议 → 自然日 → 独立 exact old WarID 退出”观察循环已闭合。剩余 `50331736/129`，player-relative score `-10/-26`。未观测 settlement type、recipient final answer、truce 或玩家战斗胜利；报价、ACK 和 WarID 消失不能独立证明白和平被接受。已有 A/B 原生输入账本中的 queue/history/final-reply 观测缺口沿已冻结施工入口继续，不阻断当前 battle。

下一真实暂停停点复用现有只读口：`ck3_query_title_holder_v1(title_id=2128, expected_revision=<fresh public integer>)`；`ck3_query_campaign_root_context_v1(expected_revision=<fresh public integer>)` 整组读取已知 5 县 `2102/2111/2115/2142/2173` 与 duchy `2141`，不逐县重复查询。2128 不在本人 held partition，需独立 holder 读回。资源余额复用当停点已有 snapshot cache 的 `played_character_gold/prestige/piety` raw Q100000；必要时 Root 选择现有 `ck3_take_snapshot(include_native_command_history=false)`，收入不当余额，不新增 getter、门禁或 SDK 执行。后续结束类型与 stock effects 只按实际 published readback 陈述。

DAY55 为 paused/map-ready、Robert alive，event/interaction 实际 author cache 为 null，normal checkpoint saved 且 matches final date；该 null 不证明对方接受。累计 `4323 / resume 1170 / 2026-10-04 +298`，本只读报告追加 0 天。仅复用 Root/owner decoded cache 与既有 receipts；不重消费日级 raw。


## 2026-10-04：populist WarID 50331736 实测强制胜利结算

Root 当前实际整战分为 100、玩家为 primary defender、CB4 `populist_war`。SDK43478 原生 termination options 的 player-victory context 为 `attacker_defeat`，context constructed / native validator / available 均 true，auto_accept observable / true；CB-specific terms 与 recipient_response unavailable/null 不构成 force 结算门禁。既有 g57 `ck3_enforce_demands` generic 路径无 CB 过滤，无需扩展白和平 CB17 分支或增加代码/测试。

Root SDK73709 在同一新 action session fresh-query-bind 后只提交一次 `enforce-demands-50331736`，没有重放 closed43478 cache。实际 006 `/packet/structuredContent/war_action` 与 `war_victory` 均为 `{status: victory_enforced, war_id: 50331736}`；顶层 accepted/submitted 仅为 ACK。独立 007 current `active_wars` 仅余 `129`，确认 exact `50331736` 退出；129 为 primary defender、opponent32750、整战分 -24、target2115。两个实际 leaf 的 snapshot 为 `native:10`、public3；直接 date/actor/episode/native_revision 字段未发布，不补填。

该限定分支达到 `production-live primitive`，有限“原生观察 → 选择一次 force → 实际提交 → 独立 exact WarID 退出”循环可 qualified 为 `production-live loop`；不代表全局战争策略或整局游玩 complete。Root normal SAVE 与查询为零日数事务，累计 4359 天；仅一次 force，不重发 167 或 503。旧 167 的结束类型仍 unknown。资源后态、CB terms、70766 实际羁押、33554465 targeting-alert 清理尚未读，不推断财富、囚禁或全局 faction object 销毁；后续只复用已有可用查询口，不作为本次 force 前置门禁。

证据仅复用授权 raw lane 一次消费后的 cache：`actual-enforce-006-007-consumed-01/ROOT-DELIVERY.json` SHA `a643e23bfee8173e0943882d48bc305a1a5120479b4d1ce9c20c46e03c722e55`。006 raw SHA `4f9d70ec375bb9a61502a9bdead7455df0f92758369a3a43c1d635d06ec9a81c`，007 raw SHA `3a35b28ca5fdc74cbc26c713e594319c3d27dba29087f27b443d868ba9a9f12a`；本报告 lane 未读取这些 Root raw。

### 2026-10-04：CB41 防御方白和 typed 入口实拒与最小修复

Root SDK98908 的真实请求在 service 层报 `selected backend does not implement native war step offer-white-peace-129`，未进入 native factory，不是原生 CanSend 拒绝或 AI decline；独立战争状态与正常 SAVE 为 GREEN，过程推进 0 天。该帧 War129 为 Robert29829 primary defender，CB41 `minor_religious_war`，整战分 +40，原生白和 context/CanSend/available 为 true，quote `2670329/100000 = +26.70329`，autoaccept false，recipient response 仍不可见。

生产修复仅 `native_driver.py`：保留 CB17 `individual_county_de_jure_cb` 分支，为真实 CB41 身份新增 `defender_minor_religious_white_peace` variant、readiness dispatch 与 proposal metadata，共享既有同帧 active WarID、primary defender、原生合法和正报价条件，最终 native submission predicate 保留；没有新增 recipient response/CB-specific terms gate、flag、DTO、WAL 或 C++ 改动。Root 已提交推送 `b5add463dd3ff7fc5cbe71c024652af3f4ff750c`。

唯一 registered MCP → actual service/driver 的 `python -O` focused attempt01 首次 GREEN（optimize1，3 phases / 61 explicit checks）：旧版同错误且 native factory callback 0；修复版使用同一真实已发布 CB41 DTO 与生产 query cache，发出一次 `offer-white-peace-129` callback，结果保持 ACK `submitted_pending` 和 null reply；单独 final native predicate false 场景保留拒绝。RESULT SHA-256 `a019a9d263439d45b9efc98c1c711cb8a6b5fd986ea90c8cc36cd6baaa8386dd`，修复 driver SHA-256 `3482c458c4bd08853600aa6e3feb9bf56e12c520be30fec8a1d0063a09dd7c40`；artifact 位于 `Z:/ck3_mod_rewrite_process_assets/g2-resume-20261003/war-settlement-typed-action/war129-score40-wp-r27/actual-service-fix/`。

本增量生产代码状态为 static-ready，等待真实白和请求及独立后态/回答观测；正报价、fixture callback 和 ACK 均不提供 accepted/applied credit。既有 War503 强制要求的有限实机 loop 范围保留，旧 War167 的终止类型仍 unknown。本包基线累计 4444 天 / resume1291 / Oct4+419，query/fix/fixture 额外 0 天。

### R28：CB41 一次提案后的有限实机结算循环

SDK7631 在新 Python `b5add463` 与已有 g59 原生 DLL 上，同一会话 freshquery → 一次 `ck3_offer_white_peace(129)` → 独立读回 GREEN；raw53250984/native3/public2，实际 `submitted_pending`、recipient decision/would-accept=null，War129 仍在、whole+40。此前 SDK98908 pre-native RED 保留；这里补充真实提交后的结果，不改变当时 fixture/static-ready 记录。

三个普通回复日后，最后 present 为 raw53251032/native15/public6，首 absent 与独立 final 均为 raw53251056/native17/public8、`active_wars=[]`；末次正常 SAVE h7044/95001476B/SHA `ee5e3c91755f00294c8b461c2eaf5313dd40df778bb35dd3e9255caff44b7f44`。

状态提升为 **production-live loop，限定一次提案→自然推进→独立精确 WarID 消失→正常保存**；最终 AI 答复、结束类型与 truce 未发布，absence/ACK/正 quote/null 互动均不冒充 direct accepted。

SDK19250 两日48h均实际正常保存；helper 历史 RED 来自 war 消失后仍调用占领查询，service 报 `war occupation query requires one current full WarID participant row`，没有 native structured 结果。`complete_saved_days=1` 与实际 saved calendar2/bounded_success2 并存，不抹去第二日；当时累计4447/resume1294/Oct4+422。

末帧我军83886367 regular@2669；玩家本两日首末 gold655.61127/prestige2832.3818/piety378.26250 相同，未推对手虔诚或物理清理。14个 leaf/day-result 由8线程各once消费，未重读 TOP；有限循环与失败证据见外置 `war-settlement-typed-action/war129-score40-wp-r27/actual-r28-consumption/reply-days02-03/ROOT-DELIVERY.json`（SHA `8528c3d11d766463f9cd7c1574f47f174efbb3efca99814742eb39a31d1ff6e6`）。后续继续既有军队与独立材料读回，不重发白和。


> **历史研究说明（source-only）：** 以下封存复盘截点为 `date_raw 53251656 / 累计 4472 / resume 1319 / Oct4 +447`，当时 War117440524 的玩家为 primary attacker、score 0。当前 Root 已到 R30 正常保存累计 4504 的后续阶段；以下段落不是 R30/4504 的结算、战争结果或实际继任证据。文中的“当前”均指上述历史研究帧。`raiktor_conquest_cb` 是 `bookmark.1071.b` 的 stock 来源 key，不是已独立读取的 actual DB CB 字段；source 回调、继承配置和接口入口不提供新的 live 结果信用。

### 2026-10-04：War117440524的结算与自然继承来源复盘

Root当前摘要为raw53251656、global4472/res1319/Oct4+447，Robert29829年龄近63；War117440524为玩家primary attacker、score0、opponent35991。actual target title IDs为1333、1351、1358，goal province IDs为470、3711、472，两组身份不能互换。冻结CK3 1.20.0.3、EXE SHA-256 `94B55397ABB687A3DCD436805A5D885E6BE90FA6C693FEB44A9E3BBEEADE02A6`，Rootsource标签g61/f3；`bookmark.1071.b`的`raiktor_conquest_cb`是stock来源key，本增量没有独立读取当前CB数据库身份。此前事件选择源与actual六军3k已在33560bf6公开，不重复记功。

| stock回调 | 来源中的角色、条件与结果 | 当前边界 |
| --- | --- | --- |
| on_victory | attacker court中有raiktor variable的random courtier成为vassal_to_be；执行conquest/invasion change，若该scope存在，再转交target titles。claimant去devoted并收100 gold。 | courtier、claimant、继承人是不同角色；不能固定为Robert或旧saved scope，100 gold不自动归玩家。 |
| on_white_peace | white-peace truce；attacker prestige−100及条件stress、payout等helper。 | body无胜利的target transfer或失败的imprisonment；资源、stress与最终接受尚须实际后验。 |
| on_defeat | attacker reparations条件取决于收入/身份/文化，prestige−750；defender监禁attacker并执行其他helper。 | 不预填赔款金额或监禁类型；死亡与其他结算不自动执行失败body。 |

以上是stock callback scope，不是当前结果。配置`transfer_behavior=transfer`、双方`on_primary_*_death=inherit`、双方`*_allies_inherit=yes`（00_event_war2923–2929）支持继承续接；不指定actual heir、不保证未来同一完整WarID，也不使自然死亡自动等于胜、败或白和。`should_invalidate={}`且无custom on_invalidated effect仅关闭脚本层事实，不能推出native永不invalidate。

原生结束入口复用已刊exact .3证据：`ck3_query_war_termination_options(war_id=W, expected_revision=R)`按fresh alive player、完整W、actual side/primary绑定loaded CB和context。enforce literal需玩家primary且player-relative score≥100，最终还要构建context并通过`0x307C040` CanSend；当前score0没有证明当帧最终CanEnforce为true。白和另需loaded CB permission bit7、special3 context与最终validator；stock回调、报价、auto_accept和recipient final answer是不同层，现published final reply evaluator未发布。已有enforce/white-peace/surrender sender重新绑定角色与context后提交；ACK/submitted_pending只证明提交，后续独立readback确认完整W与实际结果。W退出本身不区分胜败、白和或invalidation，其他CB旧回复日数也不能预测当前等待时长。

```mermaid
flowchart TD
    S["stock CB来源配置"] --> O{"on_victory / white_peace / defeat"}
    S --> D["primary death=inherit；双方allies inherit"]
    D --> R["fresh player / 候选 / actual war roles重读"]
    R -.-> H["实际继承者与未来完整WarID尚未观测"]
    Q["fresh W / side / primary / loaded CB"] --> C["termination options / final context + CanSend"]
    C --> A["已有sender提交；ACK只记提交"]
    A --> F["独立snapshot + war-state + occupation后验"]
    F -.-> E["按actual reply/outcome归因退出与物质结果"]
    Q -.-> U["recipient final evaluator未发布"]
```

下一次可直接复用已有读取口：`ck3_query_campaign_root_context_v1(expected_revision=R)`的player_character_id/alive、primary_title、primary_title_succession_character_ids原生有序首项及held_title_partition[].first_heir_character_id；首项只是当前候选，`ck3_plan_turn`的succession_expectation也是预测。自然转换后以`ck3_take_snapshot()`、`ck3_get_war_state()`重读actual player、full active WarIDs、player_side/primary_opponent/player_is_primaryWarLeader；以`ck3_query_war_occupation_targets_v1(war_id=117440524)`确认当前holder/occupation，而不是把父角色旧归属沿用。已有`ck3_query_current_timeline_blocker_context_v1(expected_revision)`及death modal typed continuation可用于实际modal阶段，本包没有调用。

death-time participant/primary/army-owner writer仍是已有逆向账本：War+0x20/+0x80、+0x288/+0x28C及ended+0x358的现代.3读取已刊，写入因果未闭；fresh查询已能读实际归属，只有实际决策需要归因时再沿writer入口补施工，不阻普通推进。本包source research完成，复用published static-ready接口；没有新增bridge/getter/policy、natural继任或war-ending live信用，消费者新增游戏天数、动作均0。

来源只消费两份封存decoded短报告各一次：[stock scope](Z:/ck3_mod_rewrite_process_assets/g2-resume-20261003/war117440524-raiktor-conquest-ending-succession-review/stock-cb/SHORT-STOCK-CB-ENDING-SUCCESSION.md)（SHA873b2327f3f8b659e66f8064480b8d0969658205e5ef3058def35497e1059082），[native ending与继任接口](Z:/ck3_mod_rewrite_process_assets/g2-resume-20261003/war117440524-raiktor-conquest-ending-succession-review/native-ending/NATIVE-ENDING-APPLICABILITY-AND-HEIR-SEAMS.md)（SHA09817c11e6c380012f5fade8bfab8b44bbf94bf5ab6c85582f6679f97f7cb7f9）。本fragment建议追加war-settlement-typed-actions-12003.md，canonical目标由Root最后确认；本消费者未读写shared/canonical/sourceleaf、原eventoptions或raw，未调用SDK/Git/tests/window。

## Provider192 qualified and War117 victory retained at h9390：real raiktor conquest结果（2026-10-06T04:53:09+08:00）

冻结 exact CK3 1.20.0.3／EXE94B55397ABB687A3DCD436805A5D885E6BE90FA6C693FEB44A9E3BBEEADE02A6。R0047原Robert29829、generation1、原ordinary episode；Arta142实际围城日后攻占，3个exact单日后fresh502 War117440524为primaryattacker、actual CB29 `raiktor_conquest_cb`、whole100（occupation90/ticking10/battle0/imprisonment0），victory constructed/validator/available/autoaccept true。CB-specific terms仍unavailable，不能由它预填资源或收件人回答；Root实际503仅一次enforce，war_victory=victory_enforced，随后独立504 active_wars=[]。

独立505/506/507 title1333/1351/1358均holder72315，holder_is_player=false、in_player_realm=true、immediate/topLiege29829。508 native844/public845 domain5/6、health3.05962、direct landed vassals含72315；这是实测目标title转入玩家realm并交vassal持有，不是三county直接进入Robert domain，也不把stock claimant100gold推给玩家。512 native845/public846仅后帧当前2factions non-dangerous。固定h9390/raw53271912/5316（恢复281日）retained save receipt，100939303B／SHA05179d733e35af076d12376a0162dcadc38529187c91252028d4ffa18b07b053；postwar disband不并入。

有限“fresh状态→合法胜利选择→一次执行→独立WarID退出＋三个title/liege material readback→正常保存”达到 **production-live loop**。404无assault事实保留，c4ed Python后续修复仅static-ready；自然继承0、G2 5/8、NW2 2/4，不称完整战争策略／战斗／世纪／complete。[h9390 retained checkpoint](Z:/ck3_mod_rewrite_process_assets/g2-resume-20261006/checkpoints/h9390-war117-victory/checkpoint-receipt.json); [fresh502 victory](Z:/ck3_mod_rewrite_process_assets/g2-resume-20261006/gameplay-responses/502-victory-tick-war-termination.json); [once503 enforce](Z:/ck3_mod_rewrite_process_assets/g2-resume-20261006/gameplay-responses/503-war117-enforce-demands-once.json); [independent504 no wars](Z:/ck3_mod_rewrite_process_assets/g2-resume-20261006/gameplay-responses/504-war117-post-demand-independent-snapshot.json); [title505/506/507](Z:/ck3_mod_rewrite_process_assets/g2-resume-20261006/gameplay-responses/505-dyrrachion-title-after-war.json); [freshroot508](Z:/ck3_mod_rewrite_process_assets/g2-resume-20261006/gameplay-responses/508-campaign-root-after-war.json); [separate512 factions](Z:/ck3_mod_rewrite_process_assets/g2-resume-20261006/gameplay-responses/512-peace-current-faction-alerts.json)。

```mermaid
flowchart LR
    S["Arta142实际围城日攻占"] --> D["3个exact单日：score100"]
    D --> Q["502 fresh CB29 victory available"]
    Q --> A["503 enforce once"]
    A --> W["504 independent active_wars empty"]
    W --> T["505–507 title holders72315 / liege29829"]
    T --> C["508 root domain5/6 + direct vassal72315"]
    C --> H["509 retained h9390 save"]
    Q -.-> U["CB-specific terms / final recipient reply未发布"]
```
