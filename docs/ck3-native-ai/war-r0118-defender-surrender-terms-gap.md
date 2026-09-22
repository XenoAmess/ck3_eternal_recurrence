# R0118 普通 `claim_cb` 守方投降：物质条款只读缺口

本包只核对 CK3 `1.19.0.6`，`ck3.exe` SHA-256 `2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86`。研究记录和同源图见 [plan](research/war-r0118-defender-surrender-terms-plan.json) 与 [graph](research/war-r0118-defender-surrender-terms-graph.md)。计划是 `offline-only`：未启动或查询 CK3，未提交投降。图中的静态边不是实机物质结果。

## 已闭合的原版路径与当前可读边界

- [static-confirmed] 冻结原版 `game/common/character_interactions/00_war.txt` SHA-256 `5C99B8F14893929A9BC2DBB5B258CDD2D4233D5805091952209413DE876EE09F`：`end_war_attacker_victory_interaction` 在第 458–459 行定义，`on_accept` 第 644 行 `end_war = attacker`。玩家为 primary defender 时投降的绝对结果因此是 `attacker_victory`，不是 `attacker_defeat`。
- [static-confirmed] `game/common/casus_belli_types/00_claim.txt` SHA-256 `D9AA37BDC45F81B4F6185B2697A3EBD09404084EA0D3CF77BBE3C1D2C962E8B1`：`claim_cb.on_victory` 第 375–594 行执行 `create_title_and_vassal_change(type=conquest_claim,add_claim_on_loss=yes) → setup_claim_cb → resolve_title_and_vassal_change`。其后有 `claimant != attacker` 的条件性改领主/额外结算、favor hook、参战者 fame、进攻方胜利休战；前段还有正统性等条件效果。这是脚本分支，不是特定 WarID 的实际变更列表。
- [static-confirmed] 生产 `ReadWarTerminationTerms` 可在玩家为守方时读取 full-generation WarID、CB、claimant、目标 title 与当前 claim，并为 `claim_cb.attacker_victory` 写出静态方向 `transfer_to_claimant_via_conquest_claim` / `resolve_with_add_claim_on_loss`。它没有列出结算后的 title holder、liege/vassal 改变或本帧资源 delta。
- [live-confirmed in existing evidence, not re-run here] 旧 broad loaded-effect preview 两次在 `RVA 0x334C668` 崩溃；详见 [战争终止专题](war-termination.md)。当前公开 `ReadWarTerminationExitTerms` 在任何 effect 读取前硬返回 `loaded_effect_preview_disabled_after_live_crash_rva_0x334C668`。旧离线 RE fixture 只接受 primary attacker，且仅建模 `white_peace` / `attacker_defeat`；不得扩出守方胜负条款，更不能重新打开崩溃路径。
- [static-confirmed, 2026-09-22] [exact-build ABI 提取器](../../ck3_autonomous_player/native_bridge/research/extract_defender_surrender_title_preview_abi.py) 与 [冻结输出](../../ck3_autonomous_player/native_bridge/research/defender_surrender_title_preview_1_19_0_6_abi.json)（Git 内 LF 字节 SHA-256 `639757E2950E6995566645E79B26475B5F0C5C01CC9CD25582CF89892DBE4B0A`）核对 RTTI/vtable：`CResolveTitleAndVassalChangeEffect` execute slot `+0xB0 → 0x2EC43F0`，preview slot `+0xB8 → 0x7E9220`，后者字节 `B0 01 C3`，即 `mov al,1; ret`，不会遍历实际 title/vassal 操作。`CSetupClaimCBEffect<0>` 的 preview slot `0x2EA7E90` 则不是此 stub。`WarOverview` victory root 从 `CB+0x968` 进入 `0xF5BFD0`，在 `0xF5C038` 构建 `CTitleAndVassalTransferVisitor`，`0xF5C09F` 调用 `0x3380170`。该 UI 路径只证明存在 visitor 调度，不证明能生成完整最终条款；本包未调用它。

因此，R0118 的原生合法/接受读口即使报告守方投降可发，也只证明可提交，不证明损失可接受。当前守方 `attacker_victory` 的物质效用是 **unknown**；`claim_cb_exit_terms_v2` 未注册/未广告，不能据此自动选择投降。

## 下一项最小可施工观测

只建立私有、只读、同一 paused frame 的 `claim_cb` 守方 `attacker_victory` 观测，不接动作或公共广告：

1. 从已发布 WarID、玩家 primary-defender 身份、原生 surrender context 的 `attacker_victory`，绑定同一 war/CB pointer、primary leaders、claimant、所有 target-title full IDs 与 paused date/revision。任一身份漂移整项 unavailable；不把 `unknown`/空行写为零。
2. 在**不执行** `end_war` / `resolve_title_and_vassal_change` 的条件下，从已定位的 `WarOverview` `CB+0x968 → 0xF5BFD0 → CTitleAndVassalTransferVisitor` 继续追 visitor payload、callback 类型和 scope 生命周期；另找 `CTitleAndVassalChange` 实际 move 列表的只读生产者。`resolve_title_and_vassal_change` 的 preview slot 已证实是 no-op，不能再把它当动态操作采集点。尤其要避开旧崩溃的 `0x3371050 → 0x334DBE0 → 0x334C668`。只有闭合非变更调用链，才采集动态 target、旧/新 holder、liege/vassal 和 title 操作；对额外条件分支逐项声明命中或未命中。不能把 tooltip 文本、静态 `transfer_to_claimant` 字串或当前 holder 当结果。
3. 同一条件下采集 primary 当前资源与结算 delta、F/fame、legitimacy、truce evaluated days/expiry、PoW release pairs。已有 Raiktor **attacker-defeat** 的 visible-root/pointer-only 观察器只可作 ABI 线索；CB 类型、绝对 outcome、root offset 与 actor side 不同，不能直接复用结论。无法安全读取的域保留 typed unavailable；不可把 partial 打包成完整投降效用。
4. 新读口先做精确构建 source fixture 与 Debug/Release、Python normal/`-O` 聚焦验证；再由单实例负责人在获授权的 paused snapshot 中双读同帧并在 cold restore 后核对身份。只有 material terms、独立游戏后置与下一 turn 消费齐全，才允许将守方投降纳入正式选择。单 ACK 只说明命令提交。

本次闭合了 `resolve_title_and_vassal_change` preview 的否定边界和 UI title visitor 入口，但尚未闭合实际 move 的只读生产者、visitor payload/teardown 或资源 delta；因此没有可用的完整投降条款 ABI。按已发生的崩溃证据停止在这里，不添加会调用旧 preview 的代码，也不运行 CK3。下一开发包先追 `0xF5BFD0`、visitor slot `0x2F0DE20` 与 `CTitleAndVassalChange` actual-move 生产者，证明非变更读取与生命周期后再做精确 fixture；之后才排队一条有界实机只读验收。守方投降仍不得作为自动动作。
