# 普通战斗终局后的败方 effect：战分门、正统性与战争条件

这是 CK3 `1.19.0.6` 的**有界纯静态**审计，接在[战斗终局与战分 writer](battle-terminal-and-reentry.md)已经闭合的局部调用顺序之后。目标是说明 `normal_result` 写入单场战分后，败方 on-action 中一个确切的后续 effect 门如何使用该数字；本页没有实机执行 effect，也没有证明任何特定存档的正统性实际变化。

## 精确输入与复核范围

- `C:/SteamLibrary/steamapps/common/Crusader Kings III/binaries/ck3.exe` SHA-256 `2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86`。
- 原版 `game/common/on_action/combat_on_actions.txt` SHA-256 `B35D696F472E801BB332D7204AA46008349E8AFBFDB38985C781EB099BBFB233`；`game/common/script_values/00_legitimacy_values.txt` SHA-256 `13E43166356B5DD99358F435330B03CB9BE95AB5913280318B01681186E23A2E`。以上两个 SHA 只指该安装的原版文件，不外推其他 build、DLC 组合或 mod 覆盖。
- 只读有界反汇编保存在 `D:/workspace/ck3_native_war_ai_promo_work/normal-result-effect-static-20260927-subagent/`：`normal-finalizer.txt` SHA-256 `C3882E857561D0E1CB2829FBC022DA9661F622A6DE709AB1841137D99D2EA72E`，`war-row-writer.txt` 为 `D0ECD7D7CDA65D70CDF36CC75D731B2178119FACF2D17E869DA82075257A3DB9`，`result-effects-extended.txt` 为 `45C54AE4046F3F59E4D9EAB3313089D21489CB12ED288BA334FF8C34CF4D8AD2`。没有启动 CK3、调用原生 mutator 或读取活内存。

## 已证的局部顺序与脚本条件

在正常分支，RVA `0x230A7C6` 调用 `0x222A5A0(CWar*, CCombat*)`。其 `0x222A693→0x222A697` 将新 battle row `+0x40` 拷贝到 result `+0x40`；RVA `0x230A7DA` 随后构造 UI/reward 数据。直到 RVA `0x230A9A3` 才调用 `0x230AF10`。后者从 `CCombat+0x6E0` 选胜方，先于 `0x230AFF4` 取 loaded effect database `+0x258` 并在 `0x230B035` dispatch 胜方，然后在 `0x230B0AD` 取 `+0x260` 并于 `0x230B0EE` dispatch 败方。这个机器顺序表明败方 effect 发生在 battle row/result 数字写入之后。

`warscore_value` 的现有 exact-build evaluator 已在前述专题闭合：RVA `0x284C7A0` 中 `0x284C7FC` 从 `CCombat+0x708` 取 ResultID，严格解析后 `0x284C830` 直接读 ResultData `+0x40` qword。因此 on-action 字段与刚写入的 row 是同一份 **Q100000 非负单场幅度**，不是 UI 文本或战争进攻方相对增量。脚本文字 `15` 表达 **15 战分**；按字段尺度对应算术原始整数 `1,500,000`，但本轮未逐指令复核脚本编译器将该字面量转换为比较操作数的路径，仍需同场原生 trigger/效果回读确认边界比较。已实机记录的单场 row `5,000,000` Q100000 即显示值 `50`，能说明量级，不能代替该效果的实机触发证据。

原版 `combat_on_actions.txt:519–664` 的 `on_combat_end_loser` 声明了以下一条具体后续 effect 链：

1. `:561–564` 要求 `combat = { warscore_value >= 15 }`。既有 [战分研究](battle-terminal-and-reentry.md#cwar-battle-row-writer-与终局顺序)已证明单场 row/result `+0x40` 是**非负 magnitude**，不是进攻方相对正负数；因此败方脚本门槛要按单场幅度理解，不能把败方的负号带进这个比较。
2. `:566–576` 在败方 `side_primary_participant` 且 `is_valid_for_legitimacy_change=yes` 时，通过 `send_interface_toast` 内声明 `add_legitimacy = minor_legitimacy_loss`。对应 `00_legitimacy_values.txt:172,182–185`：`minor_legitimacy_gain=50`，`minor_legitimacy_loss=0-50=-50`。所以“单场幅度至少 15 且身份合法”是脚本声明的 **-50 正统性写入条件**；没有 live postcondition 时，只能称静态可达条件。
3. 同一外层战分门内，`:579–663` 的 marshal-help 分支还要求败方 landed、在战争中、存在非 peasant war 且本人为该战争主参战方，其 `defender_war_score<=-25` 或 `attacker_war_score<=-25`。后续还检查 marshal、既有 flag、对手身份及随机条件，才可能触发 `ach_yearly_events.1003`。这里的 `-25` 是**战争方当前总分门**，与单场 `15` 幅度门是两个不同数字；本审计没有证明事件在任何实机战斗中实际触发。

因此本条可复用的机制结论是：`normal_result` 的单场 row 写入先于败方 result effect，原版败方 effect 中存在依赖**单场幅度 ≥15** 的 -50 正统性分支，以及在其内部进一步依赖**战争方总分 ≤-25** 的 marshal 事件候选分支。它不能被描述成“终局会直接把战争写成失败”：战争终止、事件后续 effect、脚本字面量的原生比较过程，以及 `add_legitimacy` 的真实执行回执仍是独立待证边界。`no_normal_result` 跳过这段正常 effect dispatcher，不能从它的结果反推上述分支。

## 最小复核命令

以下命令在仓库根目录用已验证的项目 venv 执行；`CRUSAD~1` 是此机器经 `dir /x` 核实的目录别名，只为避免命令行空格转义歧义。[静态 verifier](../../ck3_autonomous_player/native_bridge/research/verify_normal_result_loser_effect_static.py) 先拒绝任何输入 SHA 或 14 个机器锚点不符的 build，再检查脚本声明；它输出 `script_literal_comparator_verified=false`、`live_effect_writeback_verified=false`、`war48_request_verified=false`，不会把静态门误报为实机结论。反汇编程序与 verifier 均只读文件。

```text
D:\workspace\ck3_eternal_recurrence\tools\.venv\Scripts\python.exe tools\file_sha256.py C:\SteamLibrary\steamapps\common\CRUSAD~1\binaries\ck3.exe
D:\workspace\ck3_eternal_recurrence\tools\.venv\Scripts\python.exe ck3_autonomous_player\native_bridge\research\disasm_ck3.py 0x230A590 --size 0x650 --exe C:\SteamLibrary\steamapps\common\CRUSAD~1\binaries\ck3.exe
D:\workspace\ck3_eternal_recurrence\tools\.venv\Scripts\python.exe ck3_autonomous_player\native_bridge\research\disasm_ck3.py 0x222A5A0 --size 0x300 --exe C:\SteamLibrary\steamapps\common\CRUSAD~1\binaries\ck3.exe
D:\workspace\ck3_eternal_recurrence\tools\.venv\Scripts\python.exe ck3_autonomous_player\native_bridge\research\disasm_ck3.py 0x230AF10 --size 0x280 --exe C:\SteamLibrary\steamapps\common\CRUSAD~1\binaries\ck3.exe
D:\workspace\ck3_eternal_recurrence\tools\.venv\Scripts\python.exe ck3_autonomous_player\native_bridge\research\disasm_ck3.py 0x284C7A0 --size 0xA0 --exe C:\SteamLibrary\steamapps\common\CRUSAD~1\binaries\ck3.exe
D:\workspace\ck3_eternal_recurrence\tools\.venv\Scripts\python.exe ck3_autonomous_player\native_bridge\research\verify_normal_result_loser_effect_static.py --exe C:\SteamLibrary\steamapps\common\CRUSAD~1\binaries\ck3.exe --on-action C:\SteamLibrary\steamapps\common\CRUSAD~1\game\common\on_action\combat_on_actions.txt --legitimacy-values C:\SteamLibrary\steamapps\common\CRUSAD~1\game\common\script_values\00_legitimacy_values.txt
```
