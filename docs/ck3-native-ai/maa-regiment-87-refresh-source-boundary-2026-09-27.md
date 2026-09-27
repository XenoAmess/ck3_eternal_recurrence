# CK3 1.19.0.6：职业兵团 87 坚韧刷新差额的来源边界

本页只研究梅西纳战斗 `CombatID 16777218` 的 side 0 `RegimentID 87`，不把单团结果外推到另外 17 项职业兵士变化。原版 `ck3.exe` SHA-256 为 `2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86`。本次没有启动游戏或读取新的实机值。

## 已有同场数值

| 源日 | date_raw | 旧控制缓存伤害/坚韧 | 暂停帧原生直接求值伤害/坚韧 | 下一次 schedule 入口伤害/坚韧 |
| --- | ---: | ---: | ---: | ---: |
| 11 | 53146488 | 4,500,000 / 2,500,000 | 4,500,000 / 2,625,000 | 4,500,000 / 2,625,000 |
| 21 | 53146728 | 4,500,000 / 2,500,000 | 4,500,000 / 2,625,000 | 4,500,000 / 2,625,000 |

这两组 Q100000 值来自[日更对照](../../ck3_autonomous_player/src/xar_autoplayer/simulation/data/ck3_1_19_0_6_episode01_messina_daily_stat_refresh_day11_v1.json)及[暂停帧逐团求值](../../ck3_autonomous_player/src/xar_autoplayer/simulation/data/ck3_1_19_0_6_episode01_messina_paused_stat_eval_day11_v1.json)（第 21 日同名 `day21` 文件）。逐团报告将 87 分类为 `men_at_arms`。坚韧差额为原始整数 `125,000`，即 Q100000 的 `1.25`、相对于旧值 `5%`。`2,500,000×105,000÷100,000=2,625,000` 与 `2,500,000+125,000=2,625,000` 都成立；这是两种**算术见证**，不能据此断言引擎采用单项 `+5%`、单项 `+1.25`，或发生了一个同日 modifier 事件。旧缓存采集时间早于暂停帧重算，本次未采到它当时的每项输入。

## 本次收窄的 exact-build 输入路径

[已有属性源专题](maa-effective-stat-sources.md)确认六个固定 modifier enum、四个可能的 class 动态 enum，以及从 side entry 到 `0x239CAE0 → 0x2C8F1A0` 的调用。本次核对了其传参：

| 来源层 | 精确指令 / 数据路径 | 对 87 的已证边界 |
| --- | --- | --- |
| 兵种基础值 | `0x2C8F1D6` 取 `CRegiment+0x118` 的 type；`0x2C8F36C` 调 `0x2C8EA90`，后者读取 type `+0x280..+0x2A8` 六维基础值 | 路径存在；回执没有 87 的 type key、class index 或当帧基础值。不能把 `2,500,000` 直接叫基础坚韧。 |
| 兵团及所属上下文 | `0x2C8F1F0..0x2C8F340` 通过 `CRegiment+0x12C/+0x130` 选对象，`0x2C8F35E` 将 `CRegiment+0x120` 传入基础 helper；`0x2C8F371` 还调用 `0x2396490` 收集后续属性源 | 这些是兵团上下文输入。其具体 owner / army / station 语义和 87 的实际对象身份未在本次静态闭合，不给字段贴“领主加成”标签。 |
| type/class 与 modifier | `0x2C8F78D → 0x2C8D6A0`，class 行来自 type `+0x270`；六个固定 enum 与至多四个 class enum 通过 `0x2940E80` 进入中间属性，`0x2C8F7B9 → 0x23C2DF0` 应用 Q100000 修正 | 哪些 enum 对 87 的 class 有效、读数、相加和乘法中间值均未在旧回执出现；伤害不变也不能排除互相抵消的修正。 |
| 目标省份 | `0x239CCDC` 把保存的原调用 `r8`（target Province）传给 `0x2C8F1A0`；后者 `0x2C8F8E2..0x2C8F8FF` 从原 `r8` 经 `+0x20 → +0xB8` 到 `0x2C88B10` 取得并累加六维向量；`0x2C8FA78..0x2C8FA7F` 还有目标 `+0x628` 的可选子对象 | 目标上下文确实在该计算路径内，不能凭这条静态入口断定第 11/21 日差额来自地形、驻扎或某一省份效果。 |
| 额外 r9 上下文 | 标准入口 `0x239CCD4` 明确 `xor r9d,r9d`；`0x2C8F1CD` 将它保存到 `r12`，`0x2C8F792..0x2C8F795` 检零并跳过 `0x2C91060` 可选合并 | **这条标准调用的额外 r9 分支为零并被跳过**。这不排除上述兵团、type、modifier 和 target 输入，也不描述其他调用入口。 |

上述 `rbp+0x7D0` 是 `0x2C8F1A0` 入参保存槽中的原 `r8`；`rbp+0x7D8` 才是原 `r9`。两者若混淆，会误将目标省份路径认作已跳过的额外上下文路径。

下一次同场被动采样须先以 exact EXE、单一 RegimentID 87、CombatID、side、source date 和同一线程绑定两侧；在旧控制缓存形成时、暂停帧直接求值时、下一 schedule 入口分别留存 type/class、`CRegiment+0x120/+0x12C/+0x130` 解析身份、target Province ID、所有实际启用 enum 的 `0x2940E80` 返回、基础六维、中间修正向量、`0x23C2DF0` 前后和最终 `Stats38`。任何 identity、target 或采样时点不匹配即拒绝“变化来源”归因。只允许有界被动记录，不能为取数调用会更改游戏状态的原生函数。其他 17 个职业兵团需要各自的同类证据。

有界复核（只读 EXE 和四份已冻结 JSON，不启动 CK3）：

```text
<python-with-pefile> ck3_autonomous_player/tools/project_native_maa_regiment87_refresh_boundary.py --exe <exact-1.19.0.6-ck3.exe>
```
