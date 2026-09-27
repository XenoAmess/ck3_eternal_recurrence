# 墨西拿正常战果：败方正统性尚无战前后配对

日期：2026-09-27。接续[普通终局败方 effect 的静态条件](normal-result-loser-effect-war-score-gate-2026-09-27.md)，本轮只读审计原版 CK3 1.19.0.6 的墨西拿五次既有回放 `004/021/024/072/074`；没有启动游戏或修改 NativeBridge。目的是核实：能否由已冻结存档、正式快照和人物回执证明败方 `combat = { warscore_value >= 15 }` 内的 `add_legitimacy = minor_legitimacy_loss` 实际写回。

## 同一人物的已证前值

[机器 sidecar](../../ck3_autonomous_player/src/xar_autoplayer/simulation/data/ck3_1_19_0_6_episode01_messina_loser_legitimacy_gap_v2.json)冻结 11 份原生存档、对应 Rakaly 0.8.19 解码文本、五次回放的完整 profile `.ck3` SHA 清单及 14 份正式响应的逐文件 SHA。用完全相同的 Rakaly EXE（SHA-256 `E154AF99…56A6F1633D`）重解 11 份 raw save，文本 SHA 全部一致；[只读投影器](../../ck3_autonomous_player/tools/project_native_loser_legitimacy_pair_gap.py)还能拒绝新增或不同内容的 profile save。原始档与解码文本保留在 `D:/workspace/ck3_native_war_ai_promo_work/`，未回填旧回执。

| 来源 | 原生存档日期 | 败方主参战者 CharacterID `29829` | 胜方 CharacterID `31549` |
| --- | --- | --- | --- |
| `004` 不可变 `trace-d25/d26/d27` | `1066.12.28/29/30` | Robert，`playable_data.legitimacy=321`，类型 `duke_legitimacy`，三日相同 | Ali，`legitimacy=100`，类型 `count_legitimacy` |
| `004/021/024/072/074` 各自最后自动存档 | 均为 `1067.1.1` | 同一 CharacterID，均为 `321` | 同一 CharacterID，均为 `100` |

`004` 第 27 日正式快照的 raw 日期是 `53146896`，存档日历日期为 `1066.12.30`；正常终局回执及 `004/021/024/072/074` 的终局日正式快照是 `53146992`，相差四个 `24 raw` 的游戏日，即 `1067.1.4`。所以最后自动存档 `1067.1.1` **在终局前三日**。五次会话的 `last_save.ck3` 与各自 `autosave.ck3` SHA 相同；其余 profile 存档均由 sidecar 归入更早的冻结 source SHA，找不到终局后的原生存档。`004/021/024` 的原始终局在回放第 32 日；`072/074` 的 day26 是从不同起点编号的同一 raw 日期，不能把两个 day 编号当日历日期直接相减。

身份也影响现有读口的可用性：`004/021/024` 第 32 日正式快照的 played CharacterID 是败方 `29829`，`072/074` 第 26 日及 `074` 次日快照的 played CharacterID 则是胜方 `31549`，其中败方只出现在 WarID `4` 的 primary opponent 字段。两组回放不能把“玩家正统性”不经身份检查地拼成同一人物的前后值。审计的 14 份正式响应，包括 `074` 终局次日 raw `53147016` 的快照，在 body 中都没有 legitimacy 字段；终局 journal/战分回执也不是人物资源回执。因此已证的 `321` 只是**终局前值**，不存在同一 CharacterID 的冻结后值，更没有 `321→271` 的实机观测。

## 归因边界和下一次最小读口

原版脚本声明的 `minor_legitimacy_loss=-50` 仍只是有条件 effect。现有材料没有同场 `is_valid_for_legitimacy_change` 判定、败方 loaded `warscore_value >= 15` 节点身份、实际 `add_legitimacy` 执行或排除同日其他正统性 effect 的写集；即使未来只见 `-50` 净差，也不能仅凭数值吻合归因。本页不更改既有正常战分或终局结论。

下一次受管**自然**正常终局，最省读口的是在败方可控的回放中使用既有 `query-campaign-root-context-v1.player_legitimacy_v1`，在终局前后各读一次并核对 played CharacterID `29829`、CombatID/WarID、日期和 Q100000 原始值；这只能证明期间净变化。要把变化归到本条脚本，需在同一次败方 `0x230B0EE` on-action dispatch 的入口/返回处，对严格解析的 CharacterID `29829` 被动读取正统性 raw，并记录该 loaded 条件节点的唯一父链、`+0x50` 操作码、RHS、合法性分支和实际写回；同一时间窗若有其他写者也须逐一记录或保留未知。此前[loaded-node 身份审计](loser-loaded-effect-tree-source-identity-static-2026-09-27.md)仍未闭合，不得仅凭 trigger 类型 key、注册表偏移或相近时间安装“已归因”探针。容量溢出、身份或 VFS 不符时保留 RED，不调用原生 effect/mutator。

复核命令使用本机已验证的项目 Python；`--check-sidecar` 只读，`--verify-melt` 另在临时目录重解 raw save 并逐 SHA 比较，不启动 CK3：

```text
<verified-python> ck3_autonomous_player/tools/project_native_loser_legitimacy_pair_gap.py --evidence-root D:/workspace/ck3_native_war_ai_promo_work --melt-root D:/workspace/ck3_native_war_ai_promo_work/normal-result-legitimacy-pair-offline-20260927 --rakaly-exe D:/workspace/ck3_native_war_ai_promo_work/episode01-effect-save-attempt-008/rakaly-0.8.19-x86_64-pc-windows-msvc/rakaly.exe --exe C:/SteamLibrary/steamapps/common/CRUSAD~1/binaries/ck3.exe --verify-melt --check-sidecar ck3_autonomous_player/src/xar_autoplayer/simulation/data/ck3_1_19_0_6_episode01_messina_loser_legitimacy_gap_v2.json
```
