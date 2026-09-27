# CK3 1.19.0.6：职业兵士有效伤害与坚韧的静态来源入口

本页只对应原版 `ck3.exe` SHA-256 `2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86`。结论级别是 **exact-build 静态确认**：找到了有效属性计算中读取哪些原生 modifier 的入口；尚未回读梅西纳战斗中各项 modifier 的运行时值，也不能解释第 11、21 日合计 18 个职业兵士条目为什么在 schedule 入口与先前暂停快照不同。

## 可追踪的调用链

`0x23D2CE0` 把 side entry 的完整兵团 ID 解析为 `CRegiment*`，于 `0x23D2D2F` 调 `0x239CAE0(regiment, Stats38* out, target Province*)`，随后把 `Stats38 +0x18/+0x20` 写入 side entry 的有效伤害 `+0x40`、坚韧 `+0x48`。非骑士的职业兵士路径在 `0x239CCE2` 调 `0x2C8F1A0`；后者从 `CRegiment+0x118` 取 `CMenAtArmsType*`，在 `0x2C8F78D` 调 `0x2C8D6A0` 构造按兵种类别的属性修正，并在 `0x2C8F7B9` 调 `0x23C2DF0` 参与聚合。`0x2C8D6B7` 从 type `+0x270` 读取 class index，以全局 class count `+0xF14` 校界后选出 `0x58` 字节的 class 行。这个 class 是原生数值类别，不等于片中展示名称或 `maa_type_key` 字符串。

`0x2C8D6A0` 通过原生 modifier 读取器 `0x2940E80` 访问以下 enum；名称来自同一 EXE 的 modifier 元数据，且每个读取操作数与名称均由[有界校验脚本](../../ck3_autonomous_player/tools/project_native_maa_effective_stat_sources.py)核对：

| 进入的有效属性 | enum | 原生名称 | 静态证据 |
| --- | --- | --- | --- |
| 伤害 | `0x1AA` | `MOD_MAA_DAMAGE_ADD` | `0x2C8D801` 读取，累计到中间属性 `+0x10` |
| 伤害 | `0x1AB` | `MOD_MAA_DAMAGE_MULT` | `0x2C8D823` 读取，累计到中间属性 `+0x40` |
| 伤害 | `0x1A6` | `MOD_ARMY_DAMAGE_MULT` | `0x2C8D84C` 读取，参加同一中间属性的乘法修正累计 |
| 坚韧 | `0x1AC` | `MOD_MAA_TOUGHNESS_ADD` | `0x2C8D8E0` 读取，累计到中间属性 `+0x18` |
| 坚韧 | `0x1AD` | `MOD_MAA_TOUGHNESS_MULT` | `0x2C8D902` 读取，累计到中间属性 `+0x48` |
| 坚韧 | `0x1A7` | `MOD_ARMY_TOUGHNESS_MULT` | `0x2C8D92B` 读取，参加同一中间属性的乘法修正累计 |

同一 class 行还可以分别在 `+0x2C/+0x38`、`+0x2E/+0x3A` 提供**额外的伤害、坚韧 modifier enum**；值为 `0xFFFF` 时跳过。这些位置由 `0x2C8D86E..0x2C8D8BE` 和 `0x2C8D94D..0x2C8D99D` 的有界指令确认，但特定战斗的 class 行及这些 enum 值未回读，所以不能把它们省略为零。`0x2C8EA90` 还从兵种 type 的 `+0x280..+0x2A8` 取基础六维数值，并接收兵团上下文字段；`0x2C8F1A0` 后段还使用 target Province 指针及其子对象继续叠加属性。上述两段的每项字段语义、先后算式和截断规则没有在本次闭合，不能仅凭 enum 名称给出完整有效属性公式。

## 与两次实机差异的边界

[第 11 日](../../ck3_autonomous_player/src/xar_autoplayer/simulation/data/ck3_1_19_0_6_episode01_messina_daily_stat_source_day11_v1.json)有 8 个职业兵士条目变化，[第 21 日](../../ck3_autonomous_player/src/xar_autoplayer/simulation/data/ck3_1_19_0_6_episode01_messina_daily_stat_source_day21_v1.json)有 10 个。两份回执证明的是“暂停缓存值不同于随后 schedule 入口的有效值”，没有上述 enum、class 行、type 六维与目标省份各项的同帧数值。因此不能说这 18 项已被某个具体 trait、地形、将领或驻扎效果解释。

下一次实机只读探针应在同一来源日冻结 `CRegimentID`、target Province ID、type/class、六个固定 enum 的实际 `0x2940E80` 返回、四个 class 动态 enum 及其返回、`0x2C8EA90` 的基础六维、中间聚合结果、最终 `0x239CAE0` 的 `Stats38`；暂停控制帧和 schedule 入口各记录一次，并与既有 raw entry 对拍。若有任何 identity、class、target 或序列不一致，就不能跨帧归因。

[RegimentID 87 的有界来源审计](maa-regiment-87-refresh-source-boundary-2026-09-27.md)补充了第 11/21 日同一职业兵团的冻结数值、标准入口额外 `r9=0` 的跳过边界，以及目标省份输入路径；具体 modifier 来源仍待同帧采值。

有界复核（不启动游戏、不扫描完整 EXE；校验脚本只读指定指令和最多 400 个 `0x38` 字节的 metadata 行）：

```text
<python-with-pefile> ck3_autonomous_player/tools/project_native_maa_effective_stat_sources.py --exe <exact-1.19.0.6-ck3.exe>
```
