# 劫掠任务清理中的战中返程候选：精确静态边界

日期：2026-09-27。目标为 CK3 1.19.0.6 的 `ck3.exe`，SHA-256
`2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86`。
只读分析磁盘 EXE；没有启动或附加 CK3。本包接续[撤退 caller 归属](war-film-retreat-callers-2026-09-23.md)，
只把其中 raid **主任务失败后的清理支路**继续追到建路和提交门，不把它称为普通战争 AI 的败势撤退策略。

## 静态上能确认的门

| RVA | 确认的分支或动作 | 不能由此推出的事 |
| --- | --- | --- |
| `0x18CF047/05B/05D` | raid 主任务 `0x18CEC60` 返回 false 才进入清理循环；true 跳到 `0x18CF15A`。 | false 的自然发生条件、频率。 |
| `0x18CF11B/122/127` | 对解析出的 `CArmy+0x1D4` 比较零；非零才调用返程 helper `0x18793B0`。 | `+0x1D4` 的正式字段语义。旧研究把它与 raid 任务及 `on_defeat_raid_army` 关联，但本包没有证明它是某种“撤退意愿”或“败势”字段。 |
| `0x1879429/454/457` | 取得 owner Character 所在省，与该 CUnit 当前省 ID 比较；同省直接返回。 | 目标省必然是首都，或战中一定不同省。 |
| `0x1879475/47C` | `0x2248860` 通用移动验证失败直接返回。它的战中分支可落到已研究的 `0x2308250` 资格检查。 | 当日战斗已达到撤退时机，或该 army 一定合法。 |
| `0x187948D/492/497` | `0x186B190` builder 返回的栈上状态非零时返回。 | builder 已提交命令。 |
| `0x1879509/510` 与 `0x1879542/549` | 两次 `0x23C33D0` 建路尝试；任一次 true 转入 `0x187964D` 命令分支。两次均 false 落入 `0x18795A8 → 0x26B5710` 的另一支。 | 另一支的完整业务语义；不能将其自动算作撤退成功。 |
| `0x187965A/65F` | 成功建路支路以参数 `2` 调 `0x26B5080`，后面组建 kind `2` 的移动对象。 | 命令已进入队列或次帧生效。 |
| `0x18796C2/6C9/71B` | 全局字节的 `&0xFD` 非零时走 `0x1879727`，绕过当前可见的 `0x187971B → 0x973E00` 提交调用。 | 该字节的业务名称、运行时值或替代分支等价提交。 |

raid **主任务**在 `0x18CEEEB → 0x2248A80` 会排除 active combat，清理分支的上述窗口没有对应主动排除。
这只形成“战中也可能走到通用资格检查”的**静态候选**。它仍须满足 raid 任务失败、army 字节门、
异省、移动验证、路线与派令门；因此不能套用到普通战争 AI 根据战损/时机主动撤退。

## 最小实机复核门

未来由唯一受管游戏 owner，在自然 raid 主任务失败而清理循环运行的一次独立 attempt 中，
先冻结 EXE/DLL SHA、原始存档、WarID/CombatID、Character/CUnit/Army 的 full ID 和 paused date。
仅用被动、容量受限的定向观测记录 `0x18CF05D` 主任务结果、`0x18CF11B` 字节原值、
`0x18CF127` 实际调用，及 `0x1879475` validator 返回、两次建路返回、`0x187965F` 校验返回、
`0x18796C2` 全局字节和真实提交点。再在同一 combat 的后续暂停帧核对 route、battle membership、
撤退/追击实际写回。任何一处身份、时间或提交对应不上，保持 RED；不凭路线在 UI 出现推断是此调用新派令。
本包没有做这次实机复核，故 `live_active_combat_order_proven=false`。

## 复核入口和下一步

只读 [exact-build verifier](../../ck3_autonomous_player/native_bridge/research/verify_raid_cleanup_retreat_candidate_static.py)
核对整份 EXE SHA 与 24 个指令锚点：

```text
<verified-python> ck3_autonomous_player/native_bridge/research/verify_raid_cleanup_retreat_candidate_static.py --exe <exact-ck3.exe>
```

本机使用 `D:/workspace/ck3_eternal_recurrence/tools/.venv/Scripts/python.exe` 执行通过。
有界反汇编原文保存在仓库外
`D:/workspace/ck3_native_war_ai_promo_work/ai-voluntary-retreat-static-20260927-subagent/`：
`raid-cleanup-parent.txt` SHA-256 `74bd134541070f735d9be60848a36662dedd8491f036b6e1ad83eebb6c897e65`；
`mission-return-builder-extended.txt` SHA-256 `c7b98d72a9a1d6b50427b0ede8e8f630c6dc9b905b7cb92390e317f11bd04d73`。
这些是静态指令，不是运行日志。

普通战争 AI 的下一最小静态包应回到[既有 coordinator 评分/调度证据](war-film-retreat-callers-2026-09-23.md)：
从自然普通战争军队的 coordinator tick 入口向下，找**同一分支**读取当前 Combat/伤亡或战力、
比较阈值或计时，再把同一 CUnit 引向 kind-2 移动或 owner-subset 撤退的调用。先固定该分支的
入参身份和 `score` 符号，再设计自然实机采样；仅看到通用 builder、raid 清理或战败结算不算闭合。
