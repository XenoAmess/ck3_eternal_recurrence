# bookmark.1070 A：事件兵生成字段与当前补员边界（1.20.0.4）

> 2026-10-16 来源增量：当前EXE内置文档确认uses_supply默认yes，且已闭合spawn创建raw138=1→当前CanReplenish直接false的producer链。详见[原生默认专题](bookmark1070-spawn-defaults-native-12004.md)。下文保留2026-10-15 19:09当时的未知边界；constructor初始化byte4F1的具体store与类别正式enum名仍未捕获。

machine_id: `desktop-3fevhd2-1c74096080`；来源复核时间 `2026-10-15T19:09:32.222160+00:00`。
本增量只研究已发生的 A 选项兵员机制，不改变事件选择策略，不重复旧 registry/replay。
游戏路径取 R0173 prepared.json；EXE/build 身份仅复用该机器回执，未重新读取 EXE。

## 已闭合的脚本来源

当前 `events/bookmark_events.txt` SHA-256 `5a5ce08980d8c4fda1dcf40ec26e12d8973c01286f4da42a6d939776cfd50e03` 与通用 registry 已分析来源一致。
A/native0 是 `bookmark.1070.a`。实际三个 `spawn_army` 在 **1259–1275、1277–1293、1295–1311**，
三个块字段和内容相同，每块只写：

```text
levies = 125
men_at_arms = { type = bowmen men = 50 }
men_at_arms = { type = light_horsemen men = 50 }
men_at_arms = { type = conrois men = 25 }
location = root.capital_province
name = norman_highwaymen
```

所以脚本实际定义 **3×250=750** 人。1251–1257 的 `show_as_tooltip` 内 `levies=750` 是显示摘要，
不是第四个真实执行的军队，也不能再加750。1259后的 `hidden_effect` 才是三次实际 spawn。

| 机制 | 本事件显式值 | 当前 .4 默认/原生映射 |
|---|---|---|
| 兵力/兵种 | 每军125 levies、50 bowmen、50 light_horsemen、25 conrois | 脚本定义闭合；不是当前运行每行自动来源标签 |
| 生成位置 | `location=root.capital_province` | 只证明生成时省份表达式；不证明当前所在省或 persistent Regi 的 home/origin 字段 |
| 补员 | 没有 `can_reinforce` | **默认未知**；当前Army93原生谓词false是另一个已观察事实 |
| 使用补给 | 没有 `uses_supply` | **默认未知**；不能以当前供应量或guard推默认 |
| 继承 | 没有 `inheritable` | **默认未知**；没写no不等于本包证明yes |
| 统帅 | 没有 `commander` | **默认/自动分配未知**；没指定不等于永远没有统帅 |
| 驻地/来源地 | 没有 `origin` | **默认未知**；不要把location表达式直接命名为native home字段 |
| 合入目标/战争绑定 | 没有 `army`、`war`、`war_keep_on_attacker_victory` | 本段没有显式绑定目标；全局生命周期/默认仍未由此研究闭合 |
| 维护费用 | 无maintenance_multiplier/scaling_factor | **默认未知**；不能宣传免费 |

限定检索没有取得可绑定当前 **1.20.0.4** 的 effect 默认值文档：prepared 指向安装的
`game/documentation` 不存在，既有具名事件/战争专题也未闭合这些默认值。历史版本/网上样例仅为发现线索，
没有纳入当前默认值证据。到此停止查找，不以反例样例、缺省语法或guard数值替代engine默认。

## 当前Army93/94/95的关联与限界

Root报告当前R0176中的93/94/95是R0174 day15正常选A后事件兵，各250。
本包直接读取了R0176的具名小baseline与specialowner封好的两份小projection；
没有读取39MB raw，也没有再次查询游戏。
**现有来源足以指向A的三军来源分支/250人形状；没有逐spawn execution-node回执，
无法把93/94/95逐一对应到第1/2/3条相同spawn。不得按ArmyID升序猜ordinal。**
R0174选择动作事实由Root提供；本包引用旧通用来源核对，不把旧R0173选择回执冒充R0174动作。

已封小projection显示Army93→CArmy85的四个physical DATA行：
`guard138=1`，native/chunk `CanReplenish=false`，后读`prepared148=0`。
这是**当前消费者/运行状态**；producer分类writer和正式enum名仍NOTHELD。
因此`guard138=1`继续使用字节/偏移名，**不能改名成`can_reinforce=no`、uses_supply、事件兵标志**，
也不能从prepared为0倒推spawn时作者意图。
Root报告的单向split/merge250物理兵守恒，说明当前路径没有凭空增兵；
转移同一批Regi本身不证明补员资格已改变。具体操作验收归R09原包，本增量不新增该实机信用。

视频/agent可复用措辞：**“A选项脚本生成三支各250人的混编事件兵；当前观察到其中Army93的四个Regi补员谓词为false。
脚本没有明示补员开关，原生分类writer与脚本开关的映射尚未闭合。”**

机器可读索引：`evidence/bookmark1070-spawn-policy-12004/index.json`。
小实机来源：`C:/ck3-e04-resume-20261015-a01/high-parallel-special-refill-a02/ACTUAL-QUERY-PROJECTION.json`
及同根 `ACTUAL-CONSUMER-RESULT.json`；小baseline：
`C:/ck3-e04-resume-20261015-a01/live12004-r13-normal-a01/r09-split-merge-relay-a01/r09-selected93-a01/baseline.actual.json`。
这些来源SHA和大小在索引，机器身份只证明上述来源机器，不能外推其他机器运行状态。

本包不读取EXE、不调用SDK/游戏/桌面/Steam、不构建native、不写主树。
外置≤256KiB，计Root原active32/metadata17预算；原截止/复核 `2026-10-16T07:45:01.597Z` 不延长。


## 2026-10-16：uses_supply真正constructor默认写入已闭合

machine_id: `desktop-3fevhd2-1c74096080`；本次观察 `2026-10-15T21:02:52.946091+00:00`；主树来源 `d9322bcfb3e17a3fe78607cea777bbfaf7be0a11`。
exact **1.20.0.4 / Steam25734779**，冻结EXE SHA `98702f88a547cde2eaf29a85f93b85f68ee4cf8148336a4f7afaeb75319dd518`复用，未重hash/运行EXE。
本增量保留旧a03与联盟知识封包，不重做三个spawn枚举/策略测试。

当前真实factory/constructor入口 **2CCF3E0..2CCF52D，333B**，SHA
`9f5f4d1889b83b9c0829b21d03a59a208063e150b83ff5a4ba83f371c9562263`。它从Root获准的当前编译窗口 `[2CCC000,2CD0000)` 一次16KiB定位中取得；
只保留实际命中的窄函数，不保存完整窗口。不是旧RVA平移，也未扫描全部.text。
`2CCF3F5`分配size4F8，`2CCF40F` RIP-LEA计算实际vptr **4839B88**，
`2CCF416`写新对象vptr。已有actual COL4EB9540→TD5A71D20的类型名为
**`.?AVCSpawnArmyEffect@@`**，因此这是真正的该类型创建入口。

关键指令是 **2CCF4FD**：

```text
66 C7 87 F0 04 00 00 01 01
mov word ptr [rdi + 0x4F0], 0x0101
```

小端序明确写入 **effect4F0=1、effect4F1=1**。此前R14已置0，
`2CCF506`另写4F2=0。该默认store之后没有callee或4F0/4F1覆盖，
`2CCF517 mov RAX,RDI`、`RET2CCF52C`返回同一新对象。
所以旧的“uses_supply默认yes只有内置文档、尚未取得constructor store”缺口现已由实际指令关闭。

与已封来源联接：actual intern **32C7=uses_supply**；parser2CCCFA0在32C7分支把
**effect+4F1**交给bool解析器（2CCD0E1/0EF）。省略该属性时保留此构造默认；显式输入可经该分支替换。
两条实际spawn创建路径分别在2CCDB54/5C和2CCE501/508，把4F1复制为persistent **byte141**；
actual供给eligible叶2A956B0对ArRgkind1经首DATA完整generation解析，**2A95703读141!=0**。
这闭合 `constructor默认1 → parser属性绑定 → spawn字段复制 → 当前供给资格消费者`。
没有从字面文档或当前兵量反推默认写入，也没有授当前补给扣减/伤亡已发生信用。

补员属于另一个来源轴：两条spawn路径硬置 **R8D=1**进入2A96C00，
**2A96C28**将该创建分类存persistent **DWORD138**；现有当前permission在
262C6F2/6FF对138==1直接false。**138是创建分类raw值，141是uses_supply字段，不能互相改名。**
当前结论是“spawn创建的该raw类别被当前CanReplenish拒绝，且uses_supply默认true”；
不是虚构一个`can_reinforce=no`布尔默认，也不是保证所有writer之后或所有特殊兵永久不补员。
raw138正式enum名称、其他类别及未来状态改变保持未命名；无新SDK/游戏/录制/业务验收信用。

初始窄读已排除：typed deleting destructor2CCE540→2CCE580；相邻2CCCEF0是另一0x118对象析构，
2CCE710是assign-commander执行。它们不能冒充constructor；真实匹配来自窗口内唯一vptr命中2CCF40F，
并从实际.pdata entry重解码确认指令边界。
完整指令、raw hex、typed provenance、旧链的精确原件SHA及排除项见
[portable窄来源证明](evidence/bookmark1070-constructor-default-12004/source-proof.json)。
外置≤256KiB，原active池与2026-10-16T07:45:01.597Z复核不延；无主树写入、整EXE dump/fullbuild。
