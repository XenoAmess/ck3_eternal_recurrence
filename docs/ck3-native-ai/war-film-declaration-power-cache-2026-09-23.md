# 宣战军力缓存：`military+0x308` 的生产者与特殊部队口径

日期：2026-09-23。范围：影片 C01–C02 所用角色军力叶，CK3 `1.19.0.6`，纯离线静态研究。
本包闭合上一包保留的 **`+0x308` 生产链**；不重做准备金和 CB 成本，不启动 CK3，不声称观察到宣战。
EXE 为 95,206,008 bytes，SHA-256
`2d00ff3101ef70b566f2fcbae292f09263199c80e9dc8f139b82d7d96f83db86`。以下均为 RVA。

## 本轮新增结论

`CCharacter+0x1B8 -> +0x308` 是八类部队 **MAX 侧 power** 的已发布缓存，类型为 int64、单位为 Q100000。
它与同对象 `+0x2F0/+0x2F4` 的 int32 当前/最大数量不同；也与 `+0x310` 的 CURRENT 侧 power 不同。
“MAX 侧”是实际槽位及分支名称，不表示所有桶都把兵补满：特殊部队、特定 regiment kind、骑士等有自己的规则。

实际 producer `0x2971090` 使用 `mode=3` 调用 `0x292FC40`，同时计算 CURRENT 和 MAX。
[战分分母包](war-film-battle-score-denominator-2026-09-23.md) 的调用者则传 `mode=2`，只消费每桶的数量槽。
共享一个八桶生产函数不等于共享同一种数值。

## 写入链与缓存边界

`0x2617F80` 接收 Character，`0x2617F86` 取 `+0x1B8`，为空则返回；否则调用 producer 并发布各字段。
producer 的 `0x29710BD` 明确写 `r8b=3`，`0x29710C8` 调用八桶函数。
八桶输出从 `[rsp+0x60]` 开始，步长 `0x20`，下表直接对应其末尾累加和 wrapper 的 copy。

| 含义 | 每桶字段 | producer 汇总及 scratch 写入 | 已发布 military 字段 |
|---|---|---|---|
| CURRENT 数量 | `+04 int32` | `0x29712F7..0x2971310` → `+60` | `0x2617FA4` → `+2F0` |
| MAX 数量 | `+00 int32` | `0x2971314..0x297133D` → `+64` | `0x2617FAD` → `+2F4` |
| MAX 侧 power | `+08 int64` | `0x2971359..0x297137D` → `+78` | `0x2617FD2` → `+308` |
| CURRENT 侧 power | `+10 int64` | `0x2971381..0x29713A5` → `+80` | `0x2617FE0` → `+310` |

另外两条已定位的发布路径：

- `0x264D590` 取得一组选中 Character pointers，`0x264D622` 逐个调用 producer，
  `0x264D631/+63A/+65F/+66D` 发布上述四项；调用点之一为 `0x264D2C4`。
- `0x28AD550` 的末尾在局部 changed 标志非零且 military 存在时，
  `0x28ADE6E` 调 producer，`0x28ADEAB` 发布 `+308`，并发布同组数量和 CURRENT power。
  此条件分支不能代替全部自然调度规则。

`0x26478F0` 在 `0x2647919` 调 producer 后继续其他计算，所检查的此函数并不直接复制到 `+308`。
因此“producer 执行过”“scratch 已变”“宣战读取的缓存已发布”是三个需要分辨的事实。
自然更新频率、跨角色批处理顺序，以及某次宣战读到的缓存年龄仍未闭合。
初始计划中的 `daily-tick` 是待验证调度假设；结果计划明确收窄为 `unknown`，不把计划标签当证据。

## 八桶如何进入宣战 base

桶名和数量字段的 UI 绑定复用[战分分母包](war-film-battle-score-denominator-2026-09-23.md)；本包重新绑定 power 分支与缓存发布。
设 B 为 CRegiment `+128`，D 为其类型对象 `+118` 中 `qword[+290]+qword[+298]`。
以下规则是该简化 power 路径，不是本场战斗的地形、克制、统帅和实际骑士勇武模拟。

| 桶 | 实际来源 | 进入 `+308` 的 MAX 侧 power | 与 CURRENT 侧的区别 |
|---|---|---|---|
| `+00` 征召兵 | `0x290E410` 原生征召贡献选择器 | MAX 数量 × `LEVY_ATTACK + LEVY_TOUGHNESS`；`0x292FDB6..0x292FE4F` | CURRENT 分支另取当前数量，写 `+10`；不是把地图当前军队数量直接当 MAX |
| `+20` 兵士 | military `+108/+2A8` regiment IDs → `0x2930850` | 通常 B × D；`regiment+138==1` 时改用 `0x2394EE0`；`0x29309EF..0x2930A2B` | CURRENT 总是使用 composition 修正数量与 `0x2394EE0` power |
| `+40` 雇佣兵 | military `+138` company IDs，以及首个持有头衔的条件补充分支 | `0x2930A90` 遍历 company regiment IDs，MAX 使用 B × D | CURRENT 使用 composition 修正数量 × D；公司是否纳入由上层原生容器/条件决定 |
| `+60` 骑士团兵力 | military `+150` IDs，以及首个头衔的条件补充分支 | `0x2930D30` 的 MAX 同样使用 B × D | CURRENT 使用 composition 修正数量；仅记录既有战争军力桶，不扩展招募或宗教策略 |
| `+80` 特殊部队 | military `+290`，组步长 `38`，组内 `+20/+2C` regiment IDs | **`0x2394EE0` 当前 composition power**；`0x29301F4` 求值，`0x293021F` 加入 MAX | `0x293020D` 把同一结果加到 CURRENT；两侧相同，不能解释为自动补满 |
| `+A0` 骑士 | `0x28FDD40` 返回向量数量，包含其既有公司/持有人附加分支 | 数量 ×（默认每点伤害 + 韧性）× 假定平均勇武 | `0x2930112/+119` 同写两侧；不读取每名真实骑士的战斗有效勇武 |
| `+C0` 符合条件的持有头衔 regiment | `0x28AB770` → Title `+418` IDs → `0x2930850` | 与 `+20` 相同的 regiment 规则 | 政府/rank/title 资格如前包；不把这一桶冒充全行政领地或全部盟友 |
| `+E0` 游牧换算兵力 | 条件成立且 `+2A8` 为空时，nomadic riders 换算数量 | 换算数量 × 对应类型的两个基础 power 参数 | 两侧相同；`+2A8` 有 regiment 时此桶清零，相关 regiment 已在 `+20` |

`0x2394EE0` 用七行 composition 得到 Q，再计算 Q/B 的 Q100000 比例，乘以 B × D。
它保留原生整数除法、定点舍入和零分母分支；不能用浮点 `Q × D` 声称逐 bit 等价。
七行数量规则仍是前包记录的：row+0 非零时，若 `row+18==3 && row+4==0` 选 row+0，否则选 row+4，
用选中值减 row+0 修正 B。`kind==1` 与 row state 的全部业务生命周期尚未命名。

## 盟友与行政加成在哪一层

八桶 producer 遍历的是上述部队来源，并没有在这里遍历宣战关系网络。
`0x18784D0` 随后读取 `+308` 建立 actor State16，再执行已在
[宣战输入包](war-film-declaration-inputs-2026-09-23.md) 闭合的行政权重追加和特定政府清零分支。
`0x1878A00 -> 0x1879850` 的目标/己方关系网络仍是后续独立追加层，读取纳入角色各自的同一个 `+308` 缓存。

可用于影片的措辞是“先读角色军力估计，再按当前原生规则加入行政与关系网络项”。
不能说“把所有盟友当前兵数相加”“所有列入者都会响应召集”，也不能在缺少逐项 native 输出时自行消除行政/关系来源的潜在重叠。

## 指令勘误：当前默认骑士估计为 600，旧注释为 1100

`0x29300A9/+AF/+B5` 执行 `(int32[570EDFC] + int32[570EDF8]) * int32[570EE00]`，再乘骑士数并转换到 Q100000。
本包用三个注册 thunk 的 R8 literal 与 R9 slot 同时验证名称：

| 注册 RVA | define 与目标 slot | 当前原版源值 |
|---|---|---:|
| `0x2121850` | `KNIGHT_DAMAGE_PER_PROWESS` → `0x570EDF8` | 50 |
| `0x2121B90` | `KNIGHT_TOUGHNESS_PER_PROWESS` → `0x570EDFC` | 10 |
| `0x2121ED0` | `KNIGHT_AVERAGE_PROWESS_FOR_AI_POWER_CALCULATION` → `0x570EE00` | 10 |

故本次未修改原版文件下的静态推导是 **`(50+10)×10 = 600` power/骑士**，即 raw `60,000,000`。
`common/defines/00_defines.txt:621–622` 的旧注释仍写 1100；[military-preparation.md](military-preparation.md) 的相关旧陈述也沿用了该注释。
本包保留旧文件，追加这个与指令、注册名称和当前参数一致的更正。600 不是实际对局 define 读回；mod 或不同 build 应读取自身参数。
原版 defines 目录搜索仅发现这三项在 `00_defines.txt` 中定义；源文件 hash 与原文行已保存在本包证据。

## 下一次最小观察面

本包 8 条 static-confirmed、3 条 unknown、0 条 live-confirmed；计数仅覆盖本图枚举的 11 条边，不是“全 CK3 完成率”。
要支持影片实际案例，最少需要在同一角色、同一更新/宣战 attempt 中保存：

1. 完整 Character generation ID、游戏日/执行阶段、producer 与 publish 调用点、同次采样标识；暂停读取不能冒充刷新。
2. producer 输出八桶 `+00/+04/+08/+10`，以及 scratch `+60/+64/+78/+80` 与 published `+2F0/+2F4/+308/+310`。
   八桶是 producer 栈上临时对象，只能在真实调用有效窗口被动复制；不得保留栈指针跨 callback 或主动调用来制造更新。
3. 对本案例相关的部队组/公司/Title/Regiment 完整 ID，B、kind、七行 composition、类型 D，及实际读取的 define 值。
   对齐至少一个普通受损 regiment 与一个特殊部队案例，才能验证两侧差异。
4. 后续同次 actor State16 base/admin、target base、network 分项及来源 ID；盟友最终回应与同战争参战仍另验。

自然调用频率和发布时间需先定位，结果计划因此明确提示尚不具备 live observation window；本包没有调用新观测或 writer。

## 复现与冻结文件

- [初始计划](research-plans/war-film-power-cache-20260923-r1/war_film_power_cache_plan_20260923.json) 与其 check 保留在 r1；先于字段扫描生成。
- [结果计划](research-plans/war-film-power-cache-20260923-r2/war_film_power_cache_result_plan_20260923.json)、[图](research-plans/war-film-power-cache-20260923-r2/war_film_power_cache_result_graph_20260923.md)、[check](research-plans/war-film-power-cache-20260923-r2/war_film_power_cache_result_check_20260923.json)。
- [原始指令/字段/注册/源行合同](research-plans/war-film-power-cache-20260923-r2/war_film_power_cache_static_20260923.json)：20 个代码窗口，SHA-256 `55286e24d86b9afd9da9b049a9101b743f4e31ede421c8b64b0f9c8e56e3a5a7`。
- [locator](../../ck3_autonomous_player/native_bridge/research/war_film_power_cache_locate.py) 只提供 `.pdata` 对齐的显式 member-write 候选，不能把任意 `+308` store 直接认定为 military。
- [freezer](../../ck3_autonomous_player/native_bridge/research/war_film_power_cache_freeze.py) 从 EXE 重新提取与绑定，输出必须是新目录；不写游戏，不连接进程。

```text
tools\.venv\Scripts\python.exe ck3_autonomous_player/native_bridge/research/war_film_power_cache_freeze.py --output-dir D:/workspace/ck3_war_film_research_20260923/power-cache-reproduce-new
tools\.venv\Scripts\python.exe tools/native_research_plan.py check docs/ck3-native-ai/research-plans/war-film-power-cache-20260923-r2/war_film_power_cache_result_plan_20260923.json
```

第一条适合复验字节提取；freezer 根据输出位置生成对上一 checked-in 合同的引用，Windows 跨盘时保留绝对路径。
仓库内被冻结的结果计划已实际 check/render 一次通过。
check 只证明结构与两个 evidence 文件 hash 一致，明确 `semantic_correctness_verified=false`、`live_execution_performed=false`。

外部原始扫描、反汇编、排除的 stack-local `+308` 假候选、一次 CLI 参数误用和一次 define 名称映射拒绝均保留在
`D:/workspace/ck3_war_film_research_20260923/power-cache-r1/`。define 拒绝发生在输出目录创建前；核对 literal 后才生成 r2 合同，未覆盖失败证据。
