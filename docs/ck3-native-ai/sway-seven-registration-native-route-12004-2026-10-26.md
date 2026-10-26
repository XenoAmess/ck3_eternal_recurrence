# 七项 Sway 注册属性与 .4 原生路由的真实缺口

`machine_id: xenoamess-full-tower-eb9d2c1186`；源读截至 2026-10-25 21:54 UTC。
本轮检查 Root79 实际 Java 枚举、被冻结的 `native10/source60`、native profile03/04。
没有修改冻结源或 profile，没有编译、启动游戏或把注册成功当成业务通过。

三项现有编译旗已经覆盖七类源码的编入，但 .4 路由漏了 execution 与 invalidation 两项。
本轮已交四行窄补丁给唯一 router writer M6；invalidation 的 handler/source 迁移仍未闭合。

## 七项映射

Root79 原件为 `sources/runtime_package/saved_native75/RootSelectedRegistrationConfiguration.java`，
41401 B / SHA `8f6cba33519f76a0bac7c9be548b446589e0503ba6656218c08ec03739fc7a16`。
其 `RegistrationFlag` 在 59–65 行枚举下表属性。这里只证明字段合同，未把尚未供应的 first-live DATA 布尔值猜为 true。

下表的 `CORE`、`ACTION`、`OPINION` 分别指现有
`XAR_CK3_ENABLE_G2_ACTIVE_SCHEME_PRIVATE_CANDIDATE_V1`、
`XAR_CK3_ENABLE_G2_ACTIVE_SCHEME_SWAY_FORMAL_PRIVATE_ACTION_V1`、
`XAR_CK3_ENABLE_G2_ACTIVE_SCHEME_SWAY_OUTCOME_OPINION_PRIVATE_QUERY_V1`。
profile03-PILGRIMAGE 与 profile04-FEAST 的 85–95 行均将这三旗设为 ON。

| Java `allow_private_active_scheme_sway_` 后缀 | 现有 native flag | source60 的真实 .4 路由 |
| --- | --- | --- |
| `action` | CORE + ACTION | router 371–375/530–534：formal submit/receipt；selected Stop 使用独立现有 callback |
| `completion_execution_query` | CORE | 源已编入；原 .4 whitelist 与 callback 均遗漏；本轮四行补丁覆盖该路由 |
| `completion_invalidation_reason_query` | CORE | 源已编入；原 .4 whitelist 与 callback 均遗漏；补丁后仍受旧 SHA handler 拒绝，实际 .4 能力未完成 |
| `completion_query` | CORE | router 368/525：实际 .4 `ExecuteSwayTerminalMailbox12004` / `HandleSwayTerminal12004` |
| `completion_termination_query` | CORE | router 369/526：现有 termination recorder/query；真实 recorder 安装与采样另验 |
| `outcome_opinion_query` | OPINION | router 377–378/537–538：现有 opinion query；编入不授当前材料变化 |
| `query` | CORE | router 370/527–529：现有 target query；`.2` 文件/函数名不代替当前 binding 资格 |

具体 token 保持既有合同：target query 前缀为 `query-active-scheme-sway-target-v1-private-`；
formal 前缀为 `submit-active-scheme-sway-v1-private-` / `receipt-active-scheme-sway-v1-private-`；
本轮遗漏项为 `query-sway-completion-execution-v1-private` 与
`query-sway-completion-invalidation-reason-v1-private`。

## 缺口为何出现在实际调用链

source60 `CMakeLists.txt` 1111–1116 编入 completion；1135–1147 编入 execution 和已有 .4 observer；
1187–1192 编入 termination；1201–1206 编入 invalidation；1238–1241 编入 opinion。
1501–1502/1549/1559–1560 转发现有宏，1844–1867 编入现有 state/action transport。
因此问题不是缺第四个 build flag。

实际 .4 mailbox environment 在 `bridge.cpp:12510` 调用 `PopulateNonwarRouterExecutors12004`，
不会因旧 `PopulateNonwarRouterExecutors12002` 的两项赋值已经存在而自动获得相同 callback。
`HandleNonwarPrivate12002:727–728` 在 .4 descriptor 下首先调用 `.4` allowlist；
原 `IsNonwarPrivateStep12004:524–538` 没列这两个步骤，故后方 802–808/850–856 的 handler 分派不可达。

四行补丁只在现有 CORE 宏内补两个 callback 和两个 exact token。M6 保持唯一最终 router 原件，
同时保留其 DIAG 两处增量；本 owner 不另封整叶 router 选择。

## 路由修复后仍存在的 invalidation 来源差距

`ck3_12002_sway_completion_execution_handler.cpp:46–51` 已识别真实 .4 version/SHA，
84–87 行向既有 serializer 传实际版本与 SHA。
相对地，`ck3_12002_sway_completion_invalidation_reason_handler.cpp:47–51` 仍只接受历史 `kExecutableSha256`，
并在 82–83 行调用历史 serializer。

`bridge.cpp:30547–30576` 的实际 .4 Startup 安装 execution、common-end 和 termination；
旧 invalidation sink 的 bind/secondary-sink install/attached=true 位于后续旧 adapter 分支 30583–30601。
所以补路由之后，invalidaton 不会凭四行修改就产生当前 .4 record。
现阶段保留真实 `sway_invalidation_reason_frame_or_request_invalid`，不能把该项重标为 ready、
放宽 SHA 或用版本替换制造一个“已捕获”的来源。

## 本轮源码与待执行回归

外置包为 `resume61/native_schemes_events/sway_route68/`：

- `ROUTER-FOUR-LINES68.patch`，1290 B，SHA `0867a51b8fc188254ce852d81c1ca95468f044bf2a42bec0924b74c31014d2e6`；对冻结 source60 的只读 `git apply --check` exit 0。
- `ck3_12002_nonwar_router_test.cpp`，96321 B，SHA `281a1aa06e554ca4c9113c01584716e87bf16d03d86c8e34d1a35800ebd4447e`；独占测试候选，原件 93484 B / SHA `935740e044eec9bbc5778b1f80a5d0e21fcbb4749e176dc1c2c1e1d74f7037fe`。
- `SOURCE-DELTA68.json` 只选择测试叶；M6 的正式 combined map 才选择 router 叶。

M6 `diag_slot02/SOURCE-MAP02.json` 已正式封；combined router 为 55942 B /
SHA `00514547ebb6df352424de08ad3e25f7218374c299be710d4e802b0371e75b1d`。
本 owner 实际读回匹配：372–373 行是两个 callback，534–535 行是两个 exact whitelist token；
独立 `COMPANION-READBACK68.json` 绑定原 map68 与 M6 正式 map，不修改已封原件。

回归扩展既有 RouterAdapter 的可选 exact .4 descriptor；在现有 default/selected main 中核对两 callback、
canonical allowlist、default-OFF、旧 descriptor 与非法 suffix 拒绝，以及中央分派的两条 missing-recorder 真实诊断。
新用例不安装 recorder，不进入 provider，不产生假 data 成功；它验证实际路由与诊断边界。
NativeExecution 确认复用 `xar_ck3_12002_nonwar_router_default_test` 与
`xar_ck3_12002_nonwar_router_selected_test`，不新增 runner。

当前仅源核对/patch applicability；Native 编译、上述两个 target、handler/serializer 回归及真实 .4 查询均 NOT_RUN。
没有新游戏日，G2 完整实机验收仍 0/8。材料复核期限为 2026-10-26 08:00 UTC。

## 当前 reason-child 的可施工源入口

旧 reason reader 的 92–111 行依赖 Tooltip `4931918/4931850`、description `4931D10`，
随后读原始 child command 与 `child+50` literal key。它要求恰好一个 direct child、child 无下级，
分别识别 dead/war/range；并不递归搜索整个 conditional tree。
这些旧类型未在当前 .4 five-primary 映射中资格化，不能靠偏移加十六追认。
[既有当前执行输入专题](sway-invalidation-executing-input-12004.md)明确只捕获共有标题与 full tokens。
当前源仍需证明具体 reason child，之后才能连接同一 recorder；共有标题本身不能填出某个原因。

`invalidation69/research-plan.json` 及其 check/render 已用既有工具核对 4 个文件引用；
没有执行任何新的 EXE read。
该包从 held OLD/NEW `.pdata` 的真实同序号记录提取两个候选：

| 旧 locator 与元数据 ordinal | 当前 .4 named candidate | 精确跨度 |
| --- | --- | ---: |
| custom_tooltip factory `3770570`，188767 | `[3770550,37705F8)` | 168 B |
| custom_description_no_bullet factory `37707E0`，188770 | `[37707C0,37708CC)` | 268 B |

`BOUNDARIES69.json`，1947 B / SHA `c9384e4af148f6a99e1acd23bba410d77ad6b73e39b4a26df9e836f393a2d42d`，
仅提出 436 B current4 source 候选。b64 唯一 executor 将它排入独立 batch03；
没有热改其已封 batch02，也没有要求旧 .3 body、相邻 callee 或完整映像扫描。
当前函数边界仍是 locator，需实际 factory 指令、primary producer 和独立 typed COL/name 证据才能成为类型闭合。
M6 并行核查 handler→mailbox→serializer→消费者的版本兼容，不先扩大 SHA 接受范围。

2026-10-25 22:05 UTC 另行读回本机实际安装的原版 `sway_scheme.txt`：13634 B /
SHA `7d73696a96c28ff7daddc6b6fa08c3c4365d53a2b69a9aa70def0f00d18720b3`，
stat 前后稳定。当前 `on_invalidated` 位于 526–577 行；dead Toast 为 538–542、
war 为 552–556、range 为 567–574，三个 reason key 与上述 source locator 相同。
dead/war 是 if/else_if，range 是独立 if，因此仍须保留同 SchemeID 的多条输入，不能只留最后一个原因。
当前块不含 `end_scheme`。这次直接 source 读不证明任何自然触发或终态。

`invalidation69/STOCK-SOURCE69.json` 保存实际文件身份、SHA、完整该块与机器/观察时间，
4982 B / SHA `8a0b929c5a226eeeabe5b8905ba7e9ca7150d57199e0148d668f4f3d388d3f11`。
旧专题的整文件 `b2b1a4ba...` 与当前整文件不相等；其历史记录保留，本轮未读取对应历史全文，
不宣称只改行号、整 AST 相等或旧源码哈希可代表当前来源。

## 22:36 UTC：工厂实际指令与后继类型入口

`b64_execution/BATCH03-RESULT01.json` 已实际交付两个候选，32698 B /
SHA `460cb1a0294518eccb7c0ba5d22da7b93d51976f98d13e2c7c3b73dc8303acbb`。
本岗核对 raw 字节及完整区域解码，分别为 168 B 和 268 B，均到实际 `RET`。
这次把同序号候选推进成具体构造指令来源，尚未闭合其脚本命令名或原因 parser。

| 实际构造区域 | 当前指令直接生产的 primary | 已见初始写入 |
| --- | --- | --- |
| `3770550..37705F8` | `3770581` 的 RIP LEA：`3770588+11C13A0=4931928`，随后写入新 object | 分配请求 `100`；调用 `3764150`；`+50=0`、`+60=0`、`+68=15`、`+50` 首字节为零 |
| `37707C0..37708CC` | `37707F1` 的 RIP LEA：`37707F8+11C1528=4931D20`，随后写入新 object | 分配请求 `220`；调用 `3764150`；同样的 `+50/+60/+68` 初始写入，另初始化 `+100/+190` 子对象 |

两者把 factory 输入 `+10` 的 dword 复制到新 object `+8`，令 `+C=0`，返回 object。
这里只看到空字符串形态的初始化，**没有看到 authored parser 把原因值写入 `+50`**。
不能因为旧版相应字段用作原因 key，就把空初始字段追认为当前原因来源。
实际 `custom_tooltip` / `custom_description_no_bullet` 注册键、RTTI/type、parser property
与字串复制、base constructor 的 child count 布局和执行时直接子树仍须独立闭合。

下一次仅申请两个已见 primary 的前缀：`[4931920,4931940)` 与 `[4931D18,4931D38)`，
各 32 B，覆盖 `vptr-8` 的 COL 指针和前三个 slot，以取得实际当前类型/parser 定位。
它们来自本次真实 RIP 指令，不是全局偏移假设；未自动申请 COL 正文、type name 或 parser/callee。
已交唯一 executor 后继候选，见 `invalidation69/DECLARED-SCOPE72.json`。

人工源审 `SOURCE-ANALYSIS72.json` 为 3579 B /
SHA `72b4b4b81a7a0addc0e33922c2b4bb2787454504d31b1c6aef76c2a8b4086946`；
两份 decode 原件留在同目录。`research-plan72.json` 为 10369 B /
SHA `fba18263bb00843e20b7171e75be1d0eac6a5ddb4cf737a5751a78cda77e9cca`。
现有工具 check/render 均 exit 0，仍只验证记录结构与引用字节，不自动授语义或实机资格。

M6 的[typed 版本合同](sway-invalidation-typed-version-contract-12004-resume61.md)把需要的字段另行列清：
具体 reason/key、command/title、直接子树及 scope join 均不能由工厂单独证明；
frame/cursor 来源在录制链，五项 outcome 仍为 false。当前 `.4` 原因查询继续如实拒绝，未放宽旧 SHA。

路由测试的现行选择是 `registration70/SOURCE-DELTA70.json`，4313 B /
SHA `c215ab117a97cabccaa2bdf1d37f07a3399ee29f637705cf38a8e310c1b414ef`，只替换旧测试68。
70 保留 Sway 回调/路由诊断，并核实际 `Populate12004` 与历史 `Populate12002` 的 DIAG/Open
exact callback；selected ON/default OFF 通过 M6 CMake03 配置，spy 计数要求零调用。
M6 已独立源审 MATCH，实际编译/CTest 仍待 NativeExecution，未新增 runner 或 native 成功数据。

另一个独立前沿来自两个真实 factory call `377057C/37707EC -> 3764150`。
held current4 RF row 188577 为 `[58081616,58081967,87374888]`，即
`[3764150,37642AF)`，351 B。`DECLARED-SCOPE73-BASE.json` 只请求该实际基类构造函数，
用于核 direct-child vector/count 的当前初始化与布局；它不能预先证明实际执行实例的子树数量。
窄查迁移缓存文件名未命中，已请唯一 executor 优先复用其已有同窗；未宣称全局缓存不存在。
`research-plan73.json` 单独列这条 unknown 边，SHA
`8420b22bf833871bcfbc0fcd63a65906a361452408b0eb80c3b8ce218426430b`，
check/render 均 exit 0。它与上述 64 B primary 前缀分开声明，不自动扩展 callee。

## 23:06 UTC：实际类型表前缀与基类初态

统一 batch04 已实际取得前缀与 base 三窗，原件只由 b64 采集，本岗读回字节/哈希再源审。
`BATCH04-RESULT01.json` 为 34087 B / SHA
`2617d3449748633be7850aefe175da7efe37e1ff05e93e45308d8974c890e13a`。
两个 32 B 前缀直接给出以下 RVA；原始绝对值按明确的 preferred base `140000000` 转换，
不据此推断其他地址的偏移：

| 已见 primary | COL 指针 | slot 0 / 1 / 2 |
| --- | --- | --- |
| `4931928` | `501D2F8` | `3771B10 / 3779C90 / 3779C50` |
| `4931D20` | `501D348` | `3771BA0 / 3764400 / 3779930` |

这些是实际指针前沿，仍未解析 COL/type name 或把 slot 语义追认为 parser。
`3779C50/3779C90` 没有被当前 RF record 覆盖；后继只声明 64/32 B 有界区域，
不会把最近 RF 的相邻 382 B 函数当作它们的完整 body。
`3779930..3779ACC` 则有实际当前 RF row 188857 支持，412 B。
两个 COL 后继各只申请 24 B，未申请 type-name/callee 扫描。

base `3764150..37642AF` 的实际 351 B 完整解码显示：
`3764199` 将 object `+30` qword 清零，`376419D` 将 `+38` qword 清零，
覆盖旧 reader 的 capacity `+38` 与 count `+3C` 初态。
它还读写 global `5C6A4D0` 指向的 registry：必要时初始化，持有 `+70` 锁，
把 registry index 写到 object `+48`，追加 object 指针、递增 count，再释放锁。
因此该构造函数有状态修改，不能调用它来制造“只读”查询。
这些零写只支持当前初始布局，不证明执行时 direct count=1、nested count=0 或实际选中分支。

人工源审共用 `BATCH04-SOURCE74.json`，4481 B / SHA
`4aba837aca0957502010b67a32a540e032438f8f28152a7df98765d3abee721b`；
`invalidation69/research-plan74.json` SHA
`8f185e2980d456cd6664a623c68592f660d20bd42a17f7e854f8288d19db57bd`。
check/render 均 exit 0。M6 已独立读回该源审并更新字段矩阵，未重复采集或扩大 `.4` 资格。
后继有限窗口另封 `DECLARED-SCOPE74.json`；字面原因来源、type 和执行实例 join 仍未闭合。

## 23:31 UTC：实际 property 分派与 COL 字段

batch05 实际提供两个 slot 前缀、description slot 的 412 B 以及两个 24 B COL；
原件见统一 `BATCH05-RESULT01.json`，34761 B / SHA
`e678f109c76662d7ca1b94429d3b84319b293debda0a601cc682714b97b89bdc`。
实际参数位置为 `RCX=effect`、`RDX=valueNode`、`R8D=property`，不能把它写成旧猜测的 EDX 属性号。

- `3779C50` 的有限前缀中，property `8F` 分支把原 valueNode 放入 `RCX`，
  effect `+50` 作为 `RDX`，`R8D=0`，于 `3779C7F` 尾调用 `3F83BC0`。
  property `912` 转向 `+70` 的另一助手，其余转基类；未扩展这些支路。
- `3779C90` 的有限前缀中，只有 valueNode `+1C8 != 3` 时，才规范化为 property `8F`
  并虚调 slot `+10`；kind 3 走 `3764400`，其语义仍 unknown。
- 完整 description slot `3779930..3779ACC` 同样把 property `8F` 送到 effect `+50`，
  在 `3779A37` 尾调用同一 `3F83BC0`。其他 property 各有独立分支，不能都当作字面原因。

两个实际 COL 分别为 `(1,0,0,5BB1860,501CF50,501D2F8)` 与
`(1,0,0,5BB1898,501CFC8,501D348)`。当前记录的 primary offset 和 self RVA 已核，
TypeDescriptor 名称尚未读取，仍不能据旧名追认当前 class。
helper 的第三参数零也不能代替独立的 capture mode/child `+0C` 条件。

下一范围仅为共同实际 helper `[3F83BC0,3F83C7D)` 的 189 B，
以及上述两个实际 TypeDescriptor 各 16 B header 与 96 B bounded name 的重叠并集
`[5BB1860,5BB1908)`，168 B，共 357 B；见独立 `DECLARED-SCOPE76.json`。
若名称无 NUL 或 helper 仍有未闭依赖，保持 unknown，不自动扩大到类层次、其他 property 或辅助函数。

`BATCH05-SOURCE76.json` 为 6726 B / SHA
`d4cd81ca108f6edd8fdbc00969b88db7d3aff6dae145099000c4b6d12efdf526`；
`invalidation69/research-plan76.json` SHA
`e4d8377b458306f6fcf7b853516ae47ef399e803947b50bf4fdb9855e1748c1d`，check/render 均 exit 0。
这些实际分派参数尚不足以证明 authored key 未本地化；实际子树数量、选中分支和 source join 也仍独立。
M6 字段矩阵同步保留这些缺口，没有扩大 `.4` 原因查询守卫。

## 23:48 UTC：类型名称与值助手的条件改写

batch06 的 357 B 实际原件已回读核对。两个请求的 TypeDescriptor 均在限定前缀内遇到 NUL，
实际名称为 `.?AV?$CCustomTooltipEffect@$00@@` 与
`.?AV?$CCustomDescriptionEffect@$0A@@@`。
这里只采用这两个被实际 COL 指向的名称，不采用同窗偶然覆盖的邻接第三类型。
模板的业务参数仍由实际命令/构造/分派合同解释，不从编码外观猜名称含义。

共同助手 `3F83BC0..3F83C7D` 不是对所有值无条件直拷：
valueNode `+1DC` 非零时从 `+1D0` 取 C 字符串，否则用 RIP fallback，扫描 NUL 算长度，
以 `(effect+50, source, length)` 调用 `855DB0`。
第三参数为零时，它另用 `(stored_data, 0A, stored_length)` 调用 `4227190`，
将非空返回值减 data、空值转为 -1；若低 32 位不等于 -1，调用节点诊断后用固定 17 B 文本覆盖。
这里没有独立授予搜索 callee 的名字/语义，也没有把第三参数零当作 capture mode。
因此实际捕获仍必须读取**最终存入对象**的值并与三个来源 key 精确匹配。

复用 Core held `new-00855DB0-00855E0B.bin` 时又排除了一个错误结论：
91 B 是完整解码的一个 RF record，不是完整逻辑函数。
容量内分支写 size、调用 `4226860`、补 NUL，再跳 `855E9A`；越容分支仍继续到 `855E0B`，
并可跳 `855EB0`。三个实际 ASCII key 长度为 21、20、37 B，均超过工厂初始容量 15，
所以容量内片段不能授予任何一个新对象 reason key 的完整赋值路径。
后继只申缺失 `[855E0B,855EBC)`，177 B，覆盖三个连续 RF 区域；已有 91 B 不重采。

`BATCH06-SOURCE77.json` 为 4648 B / SHA
`4a435e42cd4b70a420146a9a137824f26a8346fffcabbe7c43474b8fa1a4466e`，
`DECLARED-SCOPE77.json` 单独声明该 177 B，不自动扩展 allocator、搜索、诊断或 type hierarchy。
`invalidation69/research-plan77.json` SHA
`d58b371bd31edc183caae97ec6545bc5a08ac81d215b094803c686e64227bdcc`，check/render 均 exit 0。
类型身份已推进，完整赋值、执行实例的实际子树/scope join 与 `.4` sink/消费者接管仍未完成。

## 00:23 UTC：真实长字符串赋值与当前版本只读候选

batch07 实际补齐 `[855E0B,855EBC)` 的 177 B，原件 SHA
`392a783602241944efea15417f5fa08d45cff51d45041b04acc3c34dbd8e1abe`。
它与原持有 91 B 连起来，显示超出内联容量时的容量计算、分配调用、实际长度及容量写回、
字节复制调用、NUL、旧缓冲释放及对象指针更新，最后返回目的对象。
这补上三条 21/20/37 B key 所需的当前赋值路径；未重新资格化分配器、复制库的全部 CPU 分支或诊断函数。
`BATCH07-SOURCE78.json` 为 3540 B / SHA
`9c57a3261347183a374e0076e4898db4490a24bdef3c569639dd7637ebfea2bf`。

据此形成 `invalidation79/SOURCE-DELTA79.json`（6318 B / SHA
`f85ce8e278f598c1f3ae93b2d0c9c940649a624fb7d355fa214111fe4a96c0f2`）的两叶生产候选。
新增 `CaptureSwayInvalidationReason12004`，复用现有 current4 Toast 标题、原生命名 scope 与 Core 前后帧检查；
在最后一次 Core 检查前读取实际 child，要求 direct count=1、nested count=0、mode=0，
当前 primary 为 `4931928` 或 `4931D20`，命令和最终 `child+50` key 均精确匹配。
因此 helper 的条件 17 B 重写或其他 key 不会被当成那三条 authored reason。
它不调用旧版本 reason binder，也不因 factory 初态推定实际执行数量。

只有完整读取和稳定帧检查通过后才写出 source；四个 token 从 execution 的 `type` 显式转换到 reason 的 `kind`，
保留 subtype、reserved 与完整 64 位 payload。两种 capture enum 的值序不同，结果采用显式 switch 对应。
原 `CaptureSwayInvalidationBranch12004` 仍独立读取标题，不因多 child 或未知 reason 改变原行为。

现有 `sway_complete_branch_12004_test.cpp` 扩展后调用实际 reader，再进入原 recorder 的 Append/Query，
覆盖三条 key 和相关 class、命令、数量、mode、精确字串、同帧失败；没有手填 source。
`invalidation80/SOURCE-DELTA80.json`（4440 B / SHA
`42073a4229838aa95533a136e826349f2d62c40f39b0fa02623435f4d61ad183`）只接续替换该 fixture：
使用 M6 `invalidation_join07/SOURCE-DELTA07-SERIALIZER.json` 的现有完整外层 serializer，
显式传 current4 version/SHA，并可向同一输出目录写三份 producer 原始字节。
计划路径不是原件引用，实际文件及其 SHA 须由 NativeExecution 编译运行后取得，再交 Java 真消费者。

79 三份源 patch、79/80 的单一 CMake 集成 proposal 与 80 fixture patch 均已只读 apply-check，exit 0。
原 fixture 原先未列入 CMake；proposal 只在现有 BUILD_TESTING、WIN32 和 ACTIVE_SCHEME 旗下，
把该既有 fixture 链接到现有 `xar_ck3_12002_runtime`，拟 target 为
`xar_ck3_12004_sway_branch_source_test`。M6/NativeLead 唯一合入 CMake，未另建 runner。
生产两叶、测试与 serializer 当前仍是未编译候选，不能据此宣称 target 已生成或测试已通过。

`.4` secondary sink/install、精确 handler、外层版本与 Java 消费者仍须同图接线后采用。
未提前放宽版本/SHA，未宣称已经取得执行实例或 Game 后态；五项既有 outcome 仍为 false。
本机 ID 仍为 `xenoamess-full-tower-eb9d2c1186`；没有新 Game 调用、推进日或 G2 实机验收。

## 00:56 UTC：实际路由增量编译与链接缺口

NativeExecution 的 `routerbuild02` 实际完成六个 router CXX 单元，协议 obj/lib 复用，
随后 default target 链接报 25 个 LNK2019；selected target 尚未链接。
真实诊断是 `D:/ck3-state/ck3-java-g2-r5-native61/controls/dev/ROUTER-LINK-DIAGNOSTIC02.json`，
2347 B / SHA `64de4d21b606aabc3d187937c4fb4798ff1175c177149e515622d994a83f66b4`。
这说明编译走到了真实链接阶段，不能算作测试通过。

独占测试叶候选 `router_link81/SOURCE-DELTA81.json`（3712 B / SHA
`9f3133a8f5c35d6ec1e79d525e3a6fa6ca6fc1199ba90184b17106e166ca1714`）
保留70所有断言，为24个实际缺少的域符号补齐既有隔离测试的强类型替身。
新增未测 provider/handler 一旦被调用会直接使测试失败，不返回伪造的原生成功。
另一个缺口 `IsCk3_12004Descriptor` 采用真实 `ck3_12004_abi_profile.cpp`，
由 M6 在原 router foreach 中追加这一最小依赖；不链接整个 runtime，不修改生产路由。
M6 `router_abi10/SOURCE-DELTA10.json` 为 4064 B / SHA
`45d821934c7b645592b90a2533c02ca6ce12cb25be72b699e944d3d21962a910`，保留当前 M5 include 与03宏。
81源 patch 和该 CMake hunk 均只读 apply-check exit 0；修复后的实际编译、链接、测试结果仍待 NativeExecution。
79/80的 reason 业务候选是独立后继，不混进这一轮实际编译修错。

## 01:13 UTC：实际默认与选定路由夹具结果

增量 build03 已闭合先前25项中的15项，剩余10项来自 router 源文件的 SOURCE 级宏没有传给独立测试单元，
使81中的相应测试替身未生成。82只移除这些测试替身及声明头的条件编译，未修改生产宏或路由。
其 default 原EXE随后实际通过289项检查、current4注册14项；对应 terminal 为
`native10/build61/dev/native_execution/routerdefaulttest01/terminal.json`，727151 B / SHA
`2628f93550a4da48c4247279b0829bf366cfa0cb26f9847e14c20f115bd7c80d`。

首次 selected 链接另暴露11项真实缺口。83在同一测试叶补9个 actual4 Prisoner/Sway terminal/stop
强类型隔离替身，以及2个保持原解析合同的 selector fixture；后两者不代表验证了生产 parser。
83 map 为 `router_link83/SOURCE-DELTA83.json`，2709 B / SHA
`81425d41b8a8d86b92cb069e45691bdb0f4be5e2d66a153eefaa53ebae31a407`；
测试叶106828 B / SHA `40d2c291ed94697972a5ac8512450f6a4158fc136ffc62fc821ed11e20f6558d`。

83 selected 原EXE实际通过632项检查、current4注册17项。
对应 terminal 为 `native10/build61/dev/native_execution/routerselectedtest01/terminal.json`，
727962 B / SHA `10de0fe724dcd84bdb03380850bc06dfbf99f47215f7460f4406b52dd83c909e`；
stdout 437 B / SHA `9bfe7022211a8ba53c9440fa9dfb2d3cdafb5bd83617340cc8eebae8be4a8331`。
本岗独立读回匹配：child退出0、Job active_processes=0、前/后输入与runtime三项MATCH，
`game_rpc_calls=0`，`live_verified=false`，`ck3_touched=false`。

83 default也已实际重新编译、链接并完成独立 no-work 验证；复测 producer 因 standing 于
01:15:53 UTC 到期而真实拒绝，未启动child，因此仍为 NOT_RUN，待下一新窗口补其原EXE运行。
不能把82 default的289项通过投影成83 default通过，更不能把两种隔离路由夹具投影为实际provider或Game通过。
这些局部修复一直复用同一开发源码和编译缓存，没有每轮复制全图或全量重建。

01:40 UTC 后继：NativeExecution 在 fresh S25 窗口实际运行同 source83 的 default 原EXE，
通过289项、current4注册14项，child耗时0.3962219秒，未重新编译。
新 terminal 为 `D:/ck3-state/ck3-java-g2-r5-native61/controls/continuation01/native_execution/default83test01/terminal.json`，
27393 B / SHA `680a5540c765218ea6191b31ecfacce939257abbf511c9c33fd07a293794bb6d`。
本岗独立读回PASS、child退出0、Job active_processes=0、三项MATCH、Game RPC为0；
stdout仍为437 B / SHA `ca42f47bd8cd74a20d0f56b65f17cfed5f43f9c08f84e28da2c3378e647543b2`。
因此83同源的 default289与selected632两variant现在均实际软件通过；此前到期拒绝仍保留其 NOT_RUN 历史。
Runtime Bridge 的另一处 C1128 由 M6 单独追加 `/bigobj`，没有据此改变这两个router target的源码或定义。
两个隔离测试不授予生产 parser/provider、reason业务链或 CK3 实机资格。
