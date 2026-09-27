# WAR31：防守方投降的原版停战脚本链（静态）

**范围。** R0221 的 WarID `16777231` 是 CK3 `1.19.0.6` 的
`individual_county_de_jure_cb`；Robert（CharacterID `29829`）为 primary defender，
其 primary opponent（`30097`）为 primary attacker。原生同帧查询确认防守方投降可合法接受、
对应绝对 `attacker_victory`；**本页原始静态提取阶段没有执行投降**。本页只确定该结果将走的原版脚本链，
不把脚本意图当成已落地的停战或到期日。

后续单次获授权的[WAR31 实机投降](war31-r0197-one-shot-live-result-2026-09-28.md)已执行，战后保存的精确人物对新增原始 `truce_1` 槽、到期 `1079.11.17`、result `victory`。**脚本方向 `30097 → 29829` 与存档槽位方向的对应仍未由原生读取证明**；不要用本页的静态意图直接给 `truce_1` 定向。以下“未执行／待执行”均指本页冻结时的历史边界。

## 可静态确定的部分

精确版本绑定的[只读提取器](../../ck3_autonomous_player/native_bridge/research/extract_dejure_war31_truce_script.py)
校验本机 `ck3.exe` SHA-256
`2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86`
及三份原版脚本的整文件 SHA-256，再读取 Git 冻结的
[R0221 请求](../autonomous-agent-progress/coordination/war-requests/requests/WAR-INPUT-R0221-WAR31-20260927.json)。
结果固化为[静态回执](../../ck3_autonomous_player/native_bridge/research/dejure_war31_truce_script_1_19_0_6.json)
（SHA-256 `1D6BF5595F1E8083C4909302E180889381E84F2D30AB6D809F9FDB844D958168`）。

| 连线 | 原版位置 | 确定内容 |
| --- | --- | --- |
| CB 的进攻方胜利 | `game/common/casus_belli_types/00_dejure_war.txt:435–497` | `on_victory` 调用 `add_truce_attacker_victory_effect = yes`（第 487 行）。 |
| 通用胜利停战效果 | `game/common/scripted_effects/00_war_effects.txt:1814–1915` | 在 `scope:attacker` 内执行唯一 `add_truce_one_way`：`character=scope:defender`、`days=standard_truce_duration_days`、`war=root.war`、`result=victory`（第 1895–1902 行）。脚本没有在这里给 defender 添加反向停战。 |
| 停战天数脚本值 | `game/common/script_values/00_war_values.txt:7–66` | 基数、条件修正、下限以及边境劫掠战乘数如下。 |

结合 R0221 的角色身份，**如果**该投降后来实际执行并走到这条效果，脚本所指定的方向是
`30097 → 29829`，即进攻方对防守方的单向停战；`result` 参数是 `victory`。
这里的 CharacterID 是同帧人物身份，不是已观察到的停战存储行。

原版的天数顺序可写为

`D = (2 if B else 1) × max(730, 1825 − 450F − 900S + 900L − 730N)`。

其中 `F` 是进攻方具有 `flexible_truces_perk`；`S` / `L` 分别是进攻方
`any_character_struggle` 中与防守方满足较短 / 较长停战参数；`N` 是双方都具备
`government_is_nomadic`；`B` 是进攻方的 `any_character_war` 中存在同一 primary
attacker/defender 的 `fp2_border_raid`。每个符号在条件满足时为 `1`，否则为 `0`。
原版先执行 `min=730`，再在 `B` 成立时 `multiply=2`；因此不能把边境劫掠乘数移到
下限之前，也不能仅凭本次 CB 不是边境劫掠就把 `B` 置零。R0221 没有冻结这些动态条件。

## 严格边界

本次只读提取没有执行 `on_victory`、`add_truce_one_way` 或停战天数 evaluator，
也没有启动 CK3。实际 `evaluated_days`、最终持久化的 `expiry_date_raw` 均为 `null`，
不能由 `paused_date_raw + 1825` 或上式猜出。其它 title/holder/liege/vassal 变化、
资源签名增减、条件效果及终局后覆盖仍未观测。production
`ReadWarTerminationTerms` 对此 CB 的结构化条款仍为 unavailable；本回执只供确定
**脚本意图和人物方向**，不授权提交防守方投降，也不提高 formal War31 出口的完成度。

要补齐实际到期日，需先在同一暂停帧用安全的原生 evaluator 取得这条具体效果的动态天数，
再在独立、获策略许可的终局动作后读取已存储的单向停战记录和 end-date；两次身份、
WarID、版本与帧配对必须独立验证。现有 Raiktor 专用 evaluator 和 post-application
expiry reader 有不同 CB / 角色合同，不能直接冒称覆盖本次 de-jure 战争。

校验：`test_dejure_war31_truce_script.py` 对精确原版文件与冻结请求重放回执，
并测试改版脚本和错误玩家角色 fail-closed；普通 Python 与 `-O` 均为 `3 passed`。
