# CK3 1.20.0.3：损耗人数计算与逐兵团写回

2026-10-04，第4期 P0-LOSS 离线增量。冻结 CK3 **1.20.0.3 / Steam build25652598**，本机 EXE `C:/SteamLibrary/steamapps/common/Crusader Kings III/binaries/ck3.exe` 为 101039736 B，SHA-256 `94B55397ABB687A3DCD436805A5D885E6BE90FA6C693FEB44A9E3BBEEADE02A6`。主解释器显式核验为 `D:/workspace/ck3_eternal_recurrence/tools/.venv/Scripts/python.exe` / Python3.14.7 / capstone5.0.9 / pefile2024.8.26。源码阅读 HEAD `563a55c5393086d3b795e7ac8fa7e0fd488d5f01`，未改共享树。

本包闭合**月度损耗执行入口到 ordinary 兵团数量写回的静态链**，并定位独立行军损耗计数入口；不重复已有补给状态表、容量或界面比例 getter。它没有 SDK、进程读取、CK3启动、游戏函数调用、窗口输入、录制、游戏日、策略或 Git ref 写入。静态规则不能替代本期的实际前后人数录像。

## 为什么不能把界面比例直接乘总人数

原生 `0x24E3430` 并不调用 `GetArmyAttritionPercentage` 的最终 getter `0x24E2E50` 来扣兵。它分别产生补给、劫掠、围城的**整数人数预算**，再分配到实际兵团、persistent chunk，最后重算军团总人数。各分量取整、不同资格集合、特殊角色兵团跳过和执行时点都可能使显示比例与实际净人数不形成简单乘法。

原版 `game_concept_attrition_desc` 将损耗解释为逃兵、疾病或饥饿造成的兵员损失。口播使用“损失兵员”更准确，不能将所有损耗都称为“死亡”。两暂停帧的净人数差还可能包含补员、战斗、集结、分合军或其他事件，必须分别排除或记录。

## 实际月度执行链

| 入口 / 输入 | exact 指令事实 | 可以说明的内容 |
| --- | --- | --- |
| `0x24E3430(CArmy*, date*)` | `0x24E3450` 调用 `0x24E4D10`；成功才在 `0x24E345E` 调用 `0x24E32E0` | 补给状态损耗预算的生产依赖真实供给更新成功；补给更新先发生，再读状态比例。scheduler、日期相位及两个anchor由独立补给时钟工作包负责。 |
| `0x24E32E0(CArmy*) -> EAX` | 调用既有 `0x24E4FA0` 得 signed Q100000 供给分量，遍历 Army+38/44 全部实际兵团，要求有效 ArRg 与 `0x2A956D0`；累加各团 whole current+38；`0x24E33FE…3415` 乘比例、向零除100000、上限为eligible人数 | 非负普通输入下，补给预算为 `min(eligible soldiers, trunc0(eligible soldiers * supply component /100000))`。舰队/grace与状态比例复用既有专题；此函数不重新调用最终总比例 getter。 |
| 当前劫掠 | `0x24E3473` predicate `0x24E8560` true，才以 loaded slot `0x5C69618` 调用 `0x24DD580` | 该分量有独立人数取整，不从当前补给状态推断是否劫掠。 |
| 当前围城 | Army+1E8不等于−1，才以 loaded slot `0x5C69098` 调用 `0x24DD580` | 判断依据是当前围城关联ID；原版 `NSiege.MONTHLY_ATTRITION=0.01` 是数据基线，运行期loaded值未在本包读取。 |
| `0x24DD580(rateRaw, CArmy*) -> EAX` | 累加全部有效实际团 current+38，将rate clamp到0…100000，再乘总量、向零除100000，结果不超过总量 | 劫掠与围城分别按当时整个Army的whole总量算整数预算。两项都在实际扣除补给损失之前计算。 |

实际分配分两轮。第一轮处理补给预算；第二轮处理预先计算的“劫掠预算＋围城预算”。第一轮先选 definition receiver `ArmyRegiment+0x18` 的 integer+2A0≤0、且 `2A956D0=true` 的有效实际团；第二轮先选该+2A0≤0的有效实际团。**+2A0字段的语义名字尚未证明**，本包只说明它是实际筛选条件，不能自行叫它“免损耗”或“无敌”字段。

各轮先求筛选集合剩余whole人数，限制本轮可分配预算，再按Army中的团顺序做 `trunc0(regiment soldiers * remaining budget / remaining eligible soldiers)`；调用 `0x26341B0(regiment, allocated soldiers*100000)` 后，从剩余预算和分母中分别扣去本次整数损失和该团的前态人数。供给轮残余调用 `0x2A95800(Army+38, remaining soldiers, flags=2)`，劫掠/围城轮残余用flags0。flags2只要求 `2A956D0`，flags0不加这个条件；fallback不能误写成再次使用前一轮完全相同的筛选集合。

在非溢出的普通游戏人数域内，上述整数算术不会保存“0.4名士兵”到actual current。算术例：假设199名普通合格兵、供给分量5%、围城1%，两个预算分别为9和1；将界面合计6%统一取整则是11。这只是解释取整差的**假设算术例**，不是本期军队实测，也不能替代带人物/日期的正式画面。

## 兵团、record和chunk的数量写回

`0x26341B0(CArmyRegiment*, lossRawQ100000)` 核对ArRg magic/FullID、跳过 `0x2634880` 判定为合法角色兵团的对象，并跳过current+38=0的团。角色判定解析ArmyRegiment+148的FullCharacterID；这不是所有实际団都会扣损失的统一规则。

该writer从ArmyRegiment+20读取data-record数组，+2C为count，**record stride=0x10**。`0x260DB70(record*)` 用record+8的persistent Regiment FullID做generation回读，再读record+C的chunk index，返回 `persistent +0x18 + index*0x24`。这同时闭合了旧首record专题中尚未证明的stride；本包未修改已有reader，也未宣称全部records已实机读取。

ordinary chunk的current是+4，maximum是+0，state是+18。writer在chunk顺序中限定当前数量和剩余损失，向零除100000后调用 `0x2657EA0(chunk, newCurrent)`；setter的 `0x2657EA3` 实际写 `chunk+4`。普通非负且预算为整数的情况下，record顺序依次消耗剩余损失，不能描述成对每个chunk都统一乘界面比例。

存在明确特殊支路：state=3且current=0时，计算有效数量改取maximum，写回起点仍取原current；writer另有第二轮record访问兜底。该state的游戏语义和全部特殊兵生命周期未在本包证明，不把ordinary规则外推到特殊分支。拒绝合法角色兵团与零record等支路也意味着“整数预算”不必等于最终army净减少值。

writer末尾调用 `0x2633340(CArmyRegiment*)`。refresh按相同16字节records解析persistent/chunk、合计current与maximum，`0x26338C0/38C3`分别写回actual+38/+3C；另有合法角色兵团的特例。新增观察口只需复用现Strength循环已读的FullID/current/max，不必先实现完整补员预测。

## 独立的行军损耗入口

当前stock `NArmy.COUNTY_MOVEMENT_ATTRITION_PERCENTAGE=0.05`、`MINIMUM_COUNTY_MOVEMENT_ATTRITION=100`；英文概念提示限定从敌对county进入另一敌对county且目标不邻接已控制county。**这些数据不是任何移动都扣5%或至少100人的无条件规则。**

exact `0x24E2400` 按来源/目的对象及actor条件调用 `0x24E2250`，通过后调用 `0x24E6670(CArmy, null)`产生行军损失人数，再使用同一 `26341B0` 写回。`24E6670`内部先由 `24E6590`得到当前比例输入，再由 `24DD9C0`得到minimum项的modifier输入，以whole总人数计算并向零取整，选择比例项与minimum项较大值，最后限制到当前whole人数。当前native modifier输入和所有邻接/actor谓词的游戏语义仍有具体缺口；不在本包把两常量写成所有主案的最终值。

该链独立于月度总比例getter。沿路线看见“当前损耗率0”，不能据此排除刚发生的county跨越损失。本期先做驻地实验隔离该分量，再在路线实验逐次记录实际到达和人数。

## 本期最小采样与可说范围

第一段使用驻地、无战斗、无集结、无分合军、无参军离军的有限窗口。Root冻结主案后保存start，读同暂停帧date/native revision、CUnit/CArmy FullID、commander、province、空route、combat ID/state、siege关联和gathering状态，再读stock/capacity/month-change/attrition与全部actual团 `{army_regiment_id,current_soldiers,maximum_soldiers,scale:1}`。连续原生录像跨一次实际损耗执行，保存紧邻前后快照与正常after save；通过补给时钟包定位真正结算日，不假定月首。

如果补员不能完整排除，口播只报告“这个窗口净少了X人”，并说明当前比例与实际净变化的区别。首record的两个permission bool保持独立；首record false、某一chunk false、whole persistent月fraction或UI补员开关都不能单独证明整个Army当日没有补员。三方案结果表可以保留实际净人数，不必等全军未来补员公式闭合。

机制因果的证据等级分别为：本包静态链；新读取的当前原生字段；无混杂的实际转移或独立回放对照。只有最后两者进入本期的具体人名/日期/损失数字。录制窗口出现战斗、分合军、gathering、兵团身份集合变更或其他数量事件时，停止单因果叙述并保留attempt；不因此把原片改写成没有发生该事件。

## 证据与未完成项

本包的小型精确切片、源码文档快照、stock取证、图表和delivery位于 `C:/ck3-war-episode04-research-20261004-a01/loss-cause/`。最早只读输出和失败环境/字符编码回执保留在 `D:/ck3-war-episode04-research-20261004-a01/loss-cause/`，未删除或覆盖旧原始切片。历史Z盘研究根本机不存在；本包重新核验当前同SHA EXE并保存自己的有界切片，不制造同名历史替代文件。

| 精确范围 | 新切片文件 | bytes SHA-256 |
| --- | --- | --- |
| 24E32E0..24E3425 | `supply-loss-count.bin` | 2440ecf4047b3c54c9b8273034b018cc82b93d5296183bc8f5309ea5a7c070af |
| 24E3430..24E3A5C | `army-loss-executor.bin` | 7fda4144c5b8015aad9cac8ff059ee79e4895a9e4d5f1da155efc04f24db5bed |
| 24DD580..24DD64F | `rate-to-loss-count.bin` | 0bce03f6d9c921ba50cf40c1fb94946b4b46e8f7d550df4a404a8b143228ff8a |
| 26341B0..26344AF | `regiment-loss-writer.bin` | c88e413b22c0676821267b730251bacd1910432196ba95d9bd665fe771d4a390 |
| 2657EA0..2657F0E | `chunk-current-setter.bin` | 8101e3c101bb81cb321d1beb721bbddc91b47f863750d3aa4a3881a2256bbcac |
| 2633340..2633AE0 | `regiment-strength-refresh.bin` | 1b25b700b5bb5281b98d2a5f9613c27a873266bebbcbf5341fe76fac8027de1d |

`0x24E3425`是前函数return后的INT3 padding；供给updater的 `0x24E3450` 是call-site，完整执行入口为 `0x24E3430`。旧耗尽专题把3425称“dispatch around”的表述仅是历史locator，不可继续作为精确调度依据；独立补给时钟包给出实际scheduler。

`open_kaishek`本机checkout `D:/workspace/open_kaishek` commit `890b32de49081b7b5510e40c5518dfb59d5c8a6d`。本步骤为 `not-applicable`：研究对象是exact EXE中的Army/chunk原生写回及tick转移，现可读README限定Paradox parser/validator/strict IR/finite白名单runtime，没有此原生二进制执行语义或1.20.0.3 Army模型；没有提供或运行fixture/corpus，不用其成功代替native研究。记录检查命令及不支持项，不重复跑无覆盖目标的预验。

剩余项明确为：Root的主案连续人数观测与排混杂；运行期loaded rate/table、两anchor及真实日期节奏（补给时钟包）；行军上下文谓词和modifier最终返回值；特殊state3/character或零record等全部生命周期。普通驻地因果实验与A/B/C拍摄仍可推进，完整原生AI地点评分和调度不是本包门禁。

可复用依据：[当前补给与比例](army-current-supply-capacity-attrition-12003.md)、[补给状态与更新](army-supply-depletion-update-and-state-12003.md)、[补员及两类Regiment](army-regiment-replenishment-raised-reserve-12003.md)。日/周报告记本包 `exact-build-static-chain`；新增游戏天、动作、SDK、录制与live cases均为0，P0-LOSS静态执行链推进，整项实机验收仍pending。
