# 战争影片补研：coordinator 重算计数器

状态：**新增 exact-build 静态分支；尚无本轮实机观察**。属于[重做 W2](war-video-research-rebuild-2026-09-23.md)，不代表全部目标评分已闭合。
EXE 1.19.0.6，SHA-256 `2d00ff3101ef70b566f2fcbae292f09263199c80e9dc8f139b82d7d96f83db86`，本轮实际读取校验。

## 新结论

[army-controller](army-controller.md) 中“三个计数字段尚未逐一映射”的缺口已在下表范围闭合。
字段是**剩余调用次数计数**，此路径逐次减一，并非绝对日期。原版 define 注释把周期描述为日；本次静态提取尚未证明全部上游调度路径恰好每天调用一次。

| coordinator 字段 | 更新函数 / 调用点 | 重置的原版 define / global RVA | 本路径规则 |
| --- | --- | --- | --- |
| `+0x94` | `0x185A270` / `0x18552C6` | `UPDATE_WAR_STANCE_TICK=30` / `0x570DF44` | 每次进入更新减一；结果 `<=0` 才调用并重置。normal/desperate 的更新属于此链。 |
| `+0x98` | `0x1858200` / `0x18552E1` | `UPDATE_SPLIT_MERGE_TICK=14` / `0x570DF60` | 同样先减一、到期才调用并重置。 |
| `+0x9C` | `0x185A780` / `0x1855305` | `UPDATE_TARGETS_TICK=7` / `0x570DF40`；`UPDATE_TARGETS_TICK_LOPSIDED=14` / `0x570DF64` | 有前置门、到期与提前刷新分支；完成此调用后按 `+0xA0` 选择重置值。 |

注册函数分别为 `0x18A9620`、`0x18A9960`、`0x18A9CA0`、`0x18A9FE0`。
每个注册体同时引用原版 define 名字串与对应 global slot；不是仅凭相邻地址或数字猜映射。

### 目标重算并非只能等七天或十四天

入口 `0x18550D0` 内的确切顺序为：

1. `+0x94/+0x98` 减一。
2. 若 `+0xB0>0` 或 `+0xC0>0`，本次不递减 `+0x9C`，且不请求目标重算。两个字段的完整业务语义仍待追补，不能擅自称为战斗/围城冷却。
3. 否则递减 `+0x9C`。到期（`<=0`）立即设置本次目标重算标志。
4. 尚未到期时，`coordinator+0x68` 的 bit 1（mask `2`）也能设置该标志。
5. 若上述均不成立，则遍历 unit stacks，结合目标 validity、raw assignment `8`、`stack+0x74`、`stack+0x6C` 和 `0x18472D0` 谓词，仍有提前设置标志的路径。该谓词包含移动/撤退/同省状态等多层条件，尚不能缩写为单一“敌人移动事件”。
6. 在更新 stance、split/merge 之后，根据先前保存的本次标志调用目标重算，然后重置 `+0x9C`。

`0x1854D30` 在 `0x1854E54` 写入 mask `2`，是已找到的提前刷新生产者之一。
它含参与者/角色状态探测；本轮尚未为全部判据恢复语义名，也未穷尽所有其它写者。不能据此声称每一种死亡、失去可见性或占领变化都立即改令。

### Lopsided 是严格小于 0.33

`0x185A270` 更新路径读取缓存的两侧 power（`+0x1B58/+0x1B60`），在 `0x185A41B..0x185A53E`：

- 任一原始输入为零，直接写 `+0xA0=1`。
- 两者非零时取较小/较大者，以 Q100000 fixed-point 除法求比例。
- `0x185A51A` 与 `LOPSIDED_WAR_RATIO_THRESHOLD` slot `0x570DF20` 比较，`0x185A521` 使用 **`setl`**，即有符号**严格小于**；结果写 `+0xA0`。
- 原版值为 `0.33`，因此正输入的 fixed-point 比例恰为 `33000` 时此分支为 false，`32999` 时为 true。还需区分输入舍入和整数除法，不能拿四舍五入的 UI 数字判断边界。

这修正了旧专题“**不超过** 0.33”的文字：exact-build 实际比较是“**低于** 0.33”。
本次发现也说明：目标计数器到期使用的是已缓存 `+0xA0`，而非每次目标调用都重新计算当前两侧比例。
本轮未证明缓存 power 的全部质量、盟友与补给聚合含义；不能将它直接替换成画面兵数。

### 初始化与观测含义

构造函数 `0x1852400` 中，`0x18524A8` 将 qword `+0x90` 写为 `2`，同时令其高半 dword `+0x94=0`；
`0x18524B3` 将 qword `+0x98` 清零，故 `+0x98/+0x9C` 初值均为零。`+0xA0` 也先清零。
首次进入这条更新链因此不能按“新建后必须先等 30/14/7 天”理解，仍需考虑目标前置门及实际调度。
正常周期重置路径直接装载 define，本路径未见随机 jitter；这不证明其它构造、载入或调度路径没有错峰。

直接 caller `0x18878F1` 已定位；同一父函数还存在经 `0x1888540` 投递的调度分支。尚未遍历全部异步消费边，不能把单一 direct xref 当成唯一调用者。

## 可复现提取与下一步

脚本：[war_film_targets_extract.py](../../ck3_autonomous_player/native_bridge/research/war_film_targets_extract.py)。
使用已验证 worktree `tools/.venv`，Capstone `5.0.9`、pefile `2024.8.26`：

```text
tools\.venv\Scripts\python.exe ck3_autonomous_player/native_bridge/research/war_film_targets_extract.py --exe C:/SteamLibrary/steamapps/common/CRUSAD~1/binaries/ck3.exe --out D:/workspace/ck3_war_film_research_20260923/targets-extract-r1
```

本次结果：14 个指令锚点、5 组 define 注册与原版值全部吻合，七个有界反汇编片段及其 SHA 已保全。
输出 `targets-extract-r1/summary.json`；[入库摘要](research/war-film-target-countdowns-evidence-20260923.json)保留实际解释器、源字节指纹、PDATA 分片和注册映射。
输出目录只允许新建，重跑须另取 attempt 名称。工具不连接或启动 CK3，PASS 仅证明声明的字节与提取条件。
[研究计划](research/war-film-targets-plan-20260923.json)及[决策图](research/war-film-targets-graph-20260923.md)区分静态边与未知上游。

`open_kaishek` 适用判断：本包是 Windows EXE 指令/注册映射的只读提取，未调用 CK3，未执行脚本夹具或 finite runtime；本包不适用。后续真实夹具须重新判断其脚本/确定性子集。

下一步在同一个有效 AI coordinator 上同时观察三组剩余计数、bit 1、`+0xA0`、目标前置门和 assignment：
先确认进入更新的次数，再对照到期和提前刷新，不能继续仅凭“十四日后换目标”归因。观察前补齐 producer 调度、身份/缓存寿命并通过 `check --for-observation`。
目标候选去重、评分算术顺序、路径代价和同分选择仍由 W2 后续包补齐；本包没有生成新旁白或影片。
