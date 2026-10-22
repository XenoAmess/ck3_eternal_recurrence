# R07：1162 人为什么实际支付 3 金币登船费

> 2026-10-22 来源整理：下列原文件名对应 [embark-fee 来源包及逐成员映射](evidence/episode04-mechanism-rules-20261022/source-index.json)。原作者正文作为独立历史原件保留在来源包，本文仅调整导航与发表时效措辞。

机器 `desktop-3fevhd2-1c74096080`，本轮只读研究时间 2026-10-22 UTC。目标为保留的 CK3 1.20.0.4 / build 25734779，EXE SHA-256 `98702f88a547cde2eaf29a85f93b85f68ee4cf8148336a4f7afaeb75319dd518`，不是当前安装/运行状态声明。普通规划器不会自动加载 Markdown。

## 计算规则与影片算例

通常的非负、整数不溢出范围内，当前版本的普通计费路径等价于：

```text
登船费 = 四舍五入到整金币(
    max(0, 当前该军队计费人数 / 100 × 每百人基础费率
           × max(1 + 角色已聚合登船费修正, 最低倍率))
)
```

原版基础费率为**每 100 人 1 金币**；最低倍率为 **0.1**。先按实际人数计算，最终才取整，没有“每开始一百人先向上凑成一百人”的步骤。0.1 是倍率下限，不是最低收取 1 金币。

R196 原存档中，角色 31254（Robert）的文化 ID 是 73，模板 `norman`，`innovation_longboats` 进度为 100。原版长船革新的角色修正明确为 `embarkation_cost_mult = -0.75`。当日 Army 18 原生人数为 1162，与计费器使用同一 ArRg.current38 累加口径。代入：

```text
1162 / 100 × 1 × max(1 − 0.75, 0.1)
= 11.62 × 0.25
= 2.905 金币
最后四舍五入 = 3 金币
```

实际付款请求为 300000（Q100000），个人钱包 **26010399 → 25710399**，即 **260.10399 → 257.10399，实扣 3 金币**。原付款入口/返回绑定 payer 31254、Army 18、转换省份 1032。画面的全局计数 1163 是另一个计数，不能换入本支军队的 1162。

准确定点步骤为：人数因子 1162000；费率 100000；倍率 25000；取整前 290500；加半金币后 340500；整金币 3；请求 300000。这里没有用浮点近似证明取整。相同人数若没有折扣，11.62 最终为 12 金币；其他实际修正和人数会改变结果。

这个算例结合了原版计算代码、历史存档长船输入和已记录的实际扣款。原付款回调没有同时转储完整 0x11B 缓存和每个 ArRg；不能把几个采样伪装成一条原子记录。已保存的长船输入给出与实付一致的结果；单凭取整后的 3 金币，不能排他反推全部修正来源只有长船。

## 原生代码如何证明

`FUNCTION-024E86D0.actual.json` 保留完整 1448 B 计费函数 `24E86D0..24E8C78`，raw SHA-256 `90828eda96da9edc6f3d6e691076b4bc5db0bb95b2425f6914b608c1f3e2761b`。

- `24E8707..24E8779` 从军队所属 CUnit 解析角色；`24E877C` 调 `28C3AC0` 取角色修正缓存。这里不是直接按任命将领的特质计价。
- `24E879A` 搜索缓存键 **0x11B**，缺项按 0，再加 100000。当前 EXE 注册链已直接证明该键是 `MOD_EMBARKATION_COST_MULT`。
- `24E8801/08` 与运行时 `5C68F68` 取较大值。注册代码把该地址绑定 `NModifier.STANDARD_MINIMUM_VALUE`。R196 同场原生查询实际读到 10000（0.1），不是从文件零填充猜运行值。
- `24E8813..24E8884` 按有效 ArRg 引用逐项累加 current38。此循环没有按兵种另设价格权重，也没有按航线距离计价；不能由此泛化所有特殊军队都一定进入此分支。
- `24E8884..24E8A86` 按人数、每百人费率、角色倍率做 Q100000 定点运算。费率地址 `5C698A0` 已由注册函数直接绑定 `NFleet.EMBARK_GOLD_COST_PER_HUNDRED`。
- 结果先不低于 0；`24E8C3B` 给非负值加 50000，随后 `24E8C42..24E8C5D` 除以 100000、转整金币再乘回 100000。正常数值域即四舍五入。极端溢出/32 位截断仍按原机器指令，不能套无限精度公式。

### 修正编号的注册闭环

`MODIFIER-REGISTRATION-CLOSED.actual-a02.json` 保存当前 EXE 构造函数和 parser 原字节：`2C4DAE0` 将表 `480C2A0`、数量 0x261 传给 `25F7270`；后者按 0x38 步长读取，在 `25F737E` 取 **row+0x28 的 u16**，乘 0xC8 索引运行时描述符。登船修正真实表项起点 `4810718`，首指针指向 `MOD_EMBARKATION_COST_MULT`，row+0x28 是 0x11B。没有套旧版 enum 或按地址邻近命名。

独立校准同时闭合 0x1A9=SUPPLY_DURATION、0x1D3=SUPPLY_CAPACITY_ADD、0x1D4=SUPPLY_CAPACITY_MULT。早期 `MODIFIER-METADATA-ROWS.actual-a01.json` 曾将表项起点错前移 16 B，误读前项尾部；原件保留，a02 以真实 constructor/parser 纠正。不要消费 a01 的错误 ID 注解，也不要假设物理表项按 ID 排序。

## 扣费时点与容易混淆的数字

`FUNCTION-024E8DB0.actual.json` 保存 `24E8DB0..24E8F46` 的 406 B 转换路径。已保留的调用链为：离岸/船队状态处理 → `2A98990` 登记 ArmyFullID 与省份 → `2A9A570` 消费队列 → `24E8DB0` 转换处理。在 Army+0x1D4 为 0 的本分支，`24E8E99` 调计费器，`24E8F3B` 进付款网关 `28B9950`。R196 实际选择个人钱包种类 0。

所以这里证明实际登船转换中的付款，不把 Move ACK、预览报价或某帧 PTS 当作扣款回调。原片只给相邻帧时间夹界，未把 CPU 回调精确映射到 PTS。

| 来源 | 数值 | 实际含义 |
|---|---:|---|
| NFleet.EMBARK_GOLD_COST_PER_HUNDRED | 1 | 每百人登船基础费率 |
| 长船 embarkation_cost_mult | −0.75 | 角色登船费修正 |
| guiscard_modifier 的 army_maintenance_mult | −0.25 | 军队维护费修正，不能代入登船费 |
| NFleet.GOLD_COST_MAINTENANCE_MULT | +0.25 | 海上军队维护费增加，不能代入一次登船费 |
| NPathFinding.EMBARK_COST | 30 | 寻路权重，不是 30 金币 |
| NModifier.STANDARD_MINIMUM_VALUE | 0.1 | 本计费器采用的倍率下限，不是最低金币收费 |

足够小的正费用仍可取整为 0。特殊军队入口、跳过分支和可负担检查仍以原生条件为准；不能据本例把每次登船都预定为 3 金币。

## 精确来源和后继消费

本目录 `OFFICIAL-FEE-INPUTS.actual-a01.json` 含原版文件完整 SHA 和行号摘录：

- `common/defines/00_defines.txt`：701 基础费率、702 维护费、1438 最低倍率、1189 寻路权重。
- `common/culture/innovations/00_tribal_innovations.txt`：393–403，长船角色修正。
- `common/modifiers/00_bookmark_modifiers.txt`：24–30，Guiscard 的维护费项。
- `history/cultures/norman.txt`：12，诺曼历史发现长船；实际是否掌握以 R196 存档为准。

`R196-SAVED-DISCOUNT-SOURCE.actual-a01.json` 绑定原 Save 既有 SHA、角色/文化的原偏移与片段 SHA，以及 Rakaly 0.8.19 原 PID 16012、FILETIME 134371140597090777、实际 wait0。只用 47221 B 原元数据和两段角色/文化字节解码，没有导出全世界或修改 Save。省略元数据的早期 wait2 方法失败也保留，未改写成成功。

`R196-LOADED-MINIMUM.actual-a01.json` 仅从 11.16 MB 历史结果前 100000 B 提取原生小对象，并绑定历史 reader 源码到 `5C68F68`，没有复制大结果。`R196-DAY31-ARMY-QUERY.original.json` 原样保存当日 1162 人读回；`R196-ROOT-SHOT-ACCEPTANCE.original.json` 原样保存镜头/付款签。`R196-FEE-ARITHMETIC.derived-a01.json` 是明确标注的离线算术，不冒充 native 执行。

已发表的跨机器原证据入口：`docs/ck3-native-ai/episode04-r196-r07-boarding-pair-12004.md`；其 evidence 同名目录下 `PRODUCTION-PAIR-REPLAY.actual-a01.json` 与 `CLOSED-PAIR-ASSESSMENT.actual-a01.json`；`docs/ck3-native-ai/war-payment-passive-12004.md`。原研究按 source-only 封件；本文的便携来源映射见同批来源索引。

智能体可据此估计登船费，但必须代入当次真实军队人数和所属角色当前有效修正，并保留实际报价/钱包后验。资金决策仍应预留军费和雇佣应急资金；未知动作不重投。本轮没有 Game、SDK、新 native build 或新实机资格。
