# 宗教礼仪融合：人工审核续工交接（2026-10-26）

> 后续进展及2026-10-29休假闭场见[最新交接](2026-10-29-religious-ritual-fusion-vacation-handoff.md)。本文保留为历史记录；其中“最后一次游戏”和现场状态不能作为当前状态。

## 当前结论

用户要求收尾全部任务并写交接，因此停止新增施工、检查和实机场次。公开产品仍是 **0.1.0-alpha，Workshop 3826756673**；开发版0.2没有发布，八项人工审核要求仍未全部实机验收。本文接续[上一份交接](2026-10-25-religious-ritual-fusion-review-handoff.md)，历史失败保留。

执行机器为 **`machine_id: 4-8e1c2f1861`**，仓库`C:/workspace/ck3_eternal_recurrence`。本轮实现末提交为 **`0646058deffcb1e3b386786a53269df89d919de6`**，已经普通推送master；本文另作交接提交，不把实现时的测试追认为未来代码验证。

本次闭场观察 **2026-10-25T19:26:16.359978+00:00**：没有CK3、host、screen keeper、Maven或本任务编译进程；没有screen owner，桌面实际1024×768。Steam在 **2026-10-25T19:24:21.757658+00:00** 的后台原生查询为offline=true，没有激活窗口或截图。这是当时状态，不能作为后继启动凭据。`O3/HANDOFF-STATE.final.actual.json`为1360 B，SHA `6306b13965a3998d49b7a48bc63455616204e9eafc07bce4df29344a405009bf`；Steam原件`O3/HANDOFF-STEAM-OFFLINE.final.actual.json`为2436 B，SHA `4fb91d32179eb1bed5d951711d988b971e09535b30da21320241c0aaeb5addf1`。两子线程均已写闭，无待消费测试进程。

## 本轮已交付的实现

| 提交 | 已完成范围 | 验收边界 |
| --- | --- | --- |
| `a30f8e7a01dcf040e7c6170374cd4f78d7e6594e` | 共享启动前恢复：消费原Root wait、原STOP和退出证据，处理合法Popen前开始时间；在保留旧冻结图前提下绑定恢复reader演进；R0013恢复生产者到allocator真实闭环 | 45项回归及修改范围严格检查；不是新的游戏业务 |
| `dbe8a99181982143313a479948f2737325d37a0b` | 共享ExpectedSelection，fixture Request v3、保存请求/报告v2；三项与四项recipe、完整AST集合/双方贡献；已有教义不重复change_rite_doctrine | 完整Maven86、RRF消费者48；有真实R15四scope保存投影回归；未完成原生定制 |
| `4e584e2434d17f1290129a82a524d8b9dc14fa7b` | 采用新结果后对同一结果force_refresh_head_of_rite；真实首领/当前Rite/IsEditing/CanEdit/零报价守卫；无合法编辑资格时保留默认和禁用原因；修正两份测试manifest pin并增加真实CLI→reader回归 | 完整RRF Maven90、DES24、公共三模块61、RRF消费者48；19项生命周期测试的原生选举输入是人工边界，不是游戏结果 |
| `0646058deffcb1e3b386786a53269df89d919de6` | 共享有限原生构建器v2支持严格来源绑定的已回收对象依赖清单；不放宽全局STALE parser、不复制库、不冒充compiled seed | 161项完整对应CI step测试及两个完整模块mypy strict；实际执行在rebase前工作树，同源模块结果保留，不能外推rebase后的登记表消费者 |

实现和失败详见[续工记录](../../mod_religious_ritual_fusion/docs/live-review-resume-2026-10-26.md)。本轮未新增Python生产模块；仅维护一期迁移范围外的既有共享Python构建/恢复工具。后继新开发仍使用Java＋Maven＋Quarkus。

`ExpectedSelection`验证3–100项、唯一、真实TENET和来源可达；当前两来源并集只有4项，5–100不可达时拒绝。fixture规范请求本身进入manifest并被公共prepare消费。保存v2必须显式选择纯检查或融合比较，后者绑定真实fixture manifest与prepared inventory。旧Request v2和旧保存v1不能混用；旧场次原件不热改。

## 八项要求及真实剩余工作

| 用户要求 | 本轮已观察 | 剩余验收 |
| --- | --- | --- |
| 仿礼仪改革美化界面 | 来源选择器可实际显示，后置入口切真正原生礼仪改革窗 | 修复后正常原生草案布局、滚动、长文和尺寸 |
| 创建提示、禁用原因 | 共享校验和可见阻断区已有实现 | 实际悬停、非法组合精确原因 |
| 独立决议组与顺序 | R14确认独立组、同宗教在前，合法状态亮起 | 保存合格实机图并覆盖两种模式 |
| 决议不再总灰 | R14合法状态已亮 | 非法状态灰及原因；完整条件边界 |
| 删除“检查选项” | 代码已删除，选择自动校验 | 最终新界面图和完整操作回读 |
| 四名、图标、颜色、美德罪恶、改信 | R15真实创建Rite153，玩家采用，费用精确500 | 修复后零追加费、同ID原生保存/延期恢复/保留默认、四名和视觉、至亲/封臣实际改信 |
| More Tenets Slots兼容 | 共享3/4集合合同与生产者到消费者测试已完成 | 独立超过3项实机；无MTS三项代表场；不声称百项实测 |
| DES可选及通用改革扩展 | 中立默认与原生动态教义组实现已存在 | 联合新版本实际出现新组，默认非宗族化、可选宗族化及DES维护后态 |

还需独立冷载并核实际after-save结果。任何ACK、窗口消失、Java编译或来源Q均不能代替这些结果。通用兼容只覆盖原生枚举的标准教义组，不自动合并第三方自定义GUI或脚本副作用。

## R0014、R0015的实际终态

R0014／keeper a16进入游戏并确认决议分组及亮起；一次读取缺少与target_rite_id配对的tenet_key，host失败，没有融合。原生与保留OS handle退出0，keeper及allocator0，公共run2；屏幕CAS13892释放。

R0015／keeper a17仍是**最后一次实际游戏**。fixture READY且27项DIAG均YES；玩家31254罗贝尔，1066.9.16暂停。来源Rite150／151／152，同属Faith13／Religion8。实际融合只提交一次，结果 **Rite153**，玩家实际采用，虔诚 **6000→5500**；核心为esotericism、astrology、communal_identity，允许离婚。完整inventory只新增153，没有新增Faith或Religion；三份来源完整token SHA未变。

该场原生定制失败：目标153正确，但head为4294967295，硬编码IsEditing=false，初始化草案复制主礼仪而非153，名称空白、核心错误；报价4257，专用保存正确拒绝，没有提交错误草案。实际一年waiver存在，但未捕获数值modifier聚合，不能解释为正最低价或声称缓存原因已经证实。本轮首领刷新修复尚无新游戏验证；原版合法选举不保证玩家必当选。

R15原生和独立OS handle退出0、host原wait0、keeper和allocator原wait0；公共run原wait2。finish_hold入队只余1.511秒，超时且没有normal-close-result；资源关闭不能改称正常关闭资格或业务PASS。显示恢复1024×768，最后屏幕 **CAS13909于2026-10-25T16:48:14Z释放**。没有后续屏幕epoch。既有previous_session_closure读取可识别previous-shared-managed-session；后继仍须由真实allocator/reducer及原锁重验，不能补造normal-close-result或failure-close。

SDK保存另有`save_binding_mismatch`；原生文件实际产生不抵扣SDK continuation缺口。

## 外置路径和关键证据

所有以下本机事实仅属于`4-8e1c2f1861`。定义：

```text
R = C:/workspace/rrf-development-20261024
S = R/review-fixes-a01/zh-live-a01
W = R/review-fixes-a01/review-resume-a01
V10 = S/metadata/product-validation-a10       # 已关闭，禁止新写
V11 = S/metadata/product-validation-a11       # 本次未执行草稿，关闭后禁止新写
O1 = S/metadata/native-successor-a01
O3 = S/metadata/native-successor-a03
N1 = R/build/native-qualified-a01             # 原d13成功构建，保留
N2 = R/build/native-qualified-a02             # 编译前失败，保留
N3 = R/build/native-qualified-a03             # 本次实际终态见下
```

| 原件 | 内容和身份 |
| --- | --- |
| `W/closure-a02/ALLOCATED-UNRUN.actual.json` | R0013合格共享恢复闭环；保留a01失败及原wait，不改旧冻结输入 |
| `W/EXECUTION.shared-recovery-scoped.actual.json` | 45项及修改范围完整模块静态验证 |
| `V10/rrf.a13.command.actual.json` | 完整90项，160237 B，SHA `ab2d70f533e5e7fc7e9a3655e3712bd9b5e58375fe545aed62556f03e478f4f1` |
| `V10/QUALIFIED-PROOFS.a13.actual.json` | RRF216、DES104、public13、consumers196输入的四份scoped证明；各自保留真实命令/原wait/源码身份 |
| `O1/EXECUTION.shared-producer-ci.a02.actual.json` | 完整五命令161项＋两模块strict，7556 B，SHA `2bd3ae9478bc57ac8b749b159f18ea52abe865caf6e2f17ff1a57553d0925123`；首次strict失败原件仍在 |
| `O1/PYTHON-ONLY.shared-producer-scoped.actual.json` | 仅修改两模块通过，694 B，SHA `41935a3e1f37fefe69a4bb25e19f3251331520a12eff9596be37867aaf462d91`；全仓历史10处/8文件RED没有修复 |
| `S/before-R0015.ck3` | 68681950 B，SHA `54a8175d2aa1d914e7f81ccf140a7f569232544c403cad9659c9e12cea05a4bc` |
| `S/managed-states/review-zh-core-a05/state/profile/save games/xar_checkpoint.ck3` | 实际after，68692199 B，SHA `c903190f35fe8976f3ca4354519fb2a7495a53f91a39f5cdd33388fbd029ee3f` |
| `S/live/4-8e1c2f1861--religious-ritual-fusion--R0015/operator-plans/save-oracle-created/report.json` | 完整AST报告480295 B，SHA `6b3162ca36efa54ad43eabed711178a123a2473dc7bd2202e365500e4199b780`；8/14断言true，6 false，不是通过 |
| `S/root-execution-a17`与上述live、state | 原Popen、MCP、退出、屏幕release、截图、原失败；不要仅凭文件名把诊断图当合格发布图 |
| `S/metadata/native-editor-r15-research-a01/HEAD-REFRESH-FINDINGS.md` | 绑定实际EXE的IsEditing/首领研究与原始字节证据 |

## 新原生构建及尚未执行的验证

远端e9的prisoner mailbox/header是实际编译输入，即使相关private开关OFF也不能标作inactive SOURCE_REVIEW。N2因旧b21对象回收使582项Ninja依赖由VALID变STALE而失败，原child wait1；生产编译尚未开始。原成功捕获893项与当前捕获仅状态不同，依赖顺序/数量/mtime均相同，582输出实际不存在。

v2构建器明确引用N1成功qualification，完整重验qualification→freeze→plan→原VALID捕获、原成功link、保留库、机器/祖先提交/profile，当前捕获仅允许状态变化；复用的是TU选择证据，链接仍来自当前新编译对象和原不可变库。新计划选择57生产单元。新config为`O3/native-configured-a03.json`，4670 B，SHA `cba59913c26ba2e5480495d10a4e66d718af56ee54f191d8648535b5340daa13`；sourceCommit为0646058，预算160MiB，8个显式fixture。

**N3实际成功，原wait0**：2026-10-25T19:10:08.688169Z开始，19:23:39.555323Z结束；57个生产单元、链接和8个显式fixture原wait均0，8个项目EXE的管理员精确排除读回verified。原始外层`O3/BUILD.original-wait.actual.json`为5256 B，SHA `8672b648542b3dfbf8ecffe13f537962147af404c0b68557feeaf31ae236bdef`。

新资格文件`N3/native-a01/PUBLIC-RUNTIME-QUALIFICATION.actual.json`为8204 B，SHA `2e11d63d68ac66f2e9745438aa2e49fcd78bc1aafb328ce2f85444381d0f1afe`。新DLL `N3/build/xar_ck3_bridge.dll`为15711744 B，SHA `1e3d3f02a0235cc8925054b6ea418ae0d9235fd587b3df8a06a88d9903135350`。wire index4989 B，SHA `f1a01be3b281cd1e4ae83198fdbaa83961ca6b2e73e619cb59cac35346c3b1a3`。最终native allocation119615488 B，命令采样峰值118984704 B；两者含义不同，不冒充连续峰值证明。整个构建没有启动游戏；新DLL的SDK wire消费、公共runtime导入和实机业务均未执行。

用户要求收尾时，V11补验**尚未启动**；仅保留`V11/run-affected-ci.once.py`操作草稿，没有execution/proof/原wait。`O3/run-native-wire-consumers.once.py`也是**未执行草稿**。不要将文件存在当测试通过；草稿尚未资格化，后继先读完整命令再用新的准入输出根执行。

rebase带入`6d38eadf8`的DES生产、Java、公共products/case和SDK faith_creation更改后，旧四份scoped证明分别有 **5／22／2／2项输入漂移**；旧90／24／61／48只证明其原执行输入。shared五组中的build_runtime与prelaunch测试也消费products，因此不能因为旧proof仅列11源码不漂移就宣称rebase后完整闭包通过。已经推送的[0646058官方RRF Static](https://github.com/XenoAmess/ck3_eternal_recurrence/actions/runs/40224620632)实际成功；不能用该单workflow抵扣未运行的其他完整命令组。19:25Z读取的[4e584e官方总CI](https://github.com/XenoAmess/ck3_eternal_recurrence/actions/runs/40221657946)已终态FAIL，static job121254323890的step44“Verify Java tools, full reactor and actual HTTP consumer chain”失败；只读了终态与step，未归因或修复，原件为`O3/CI.4e-official-terminal.actual.json`。[0646058总CI](https://github.com/XenoAmess/ck3_eternal_recurrence/actions/runs/40224620609)当时仍in_progress，不能称全仓CI通过。

后继应按真实影响补完整RRF Maven、DES Maven、public三模块、RRF五消费者及compat严格检查、新SDK faith_creation完整模块＋records严格检查、共享native完整五命令step。不要热改构建中的源码，也不要为未变输入无条件重复全部历史检查。默认mvn须逐机核不低于3.10.0；本机曾实际为3.10.0、home C:/apache-maven-3.9.16，目录名不是版本。子进程先设PYTHONPATH与fixture状态根，再导入冻结配置的模块；Maven子进程移除污染管道字节数的JAVA_TOOL_OPTIONS，不放松字节数断言。

新N3若成功，仍需实际新wire→SDK完整step：static-ci.yml的“Test pilgrimage option and native execution wire contract”，3组测试、2组mypy、verify_pilgrimage_execution_wire CLI，使用新14包和新readonly4，不能引用旧wire来代表新DLL；另消费prisoner新stdout并跑两原CTest。公共build_runtime要求seam的actual_execution_wire_packets精确等于新Native Q的wire Pin。原Java source-qualifications继承旧seam字段，不能只换--qualified-native；须选择实际消费新包的seam资格。

## 存储和资源闭场

本机获准工作根在C盘，没有获准其他数据卷；D映射属于另一machine，不可照搬。所有后继仍按统一存储策略和当前机器root map重新核验，不能因历史授权省略准入。

旧R15 shadercache3740文件155353904分配字节，以及三份字节相同保存副本206073856分配字节，已精确回收；before、xar_checkpoint、完整AST和必要失败仍保留。回收加回gross retirement，未退款/重置gross和quota。旧a09场次PNG/meta/wire超额历史RED不追认PASS。

最后活动账本曾为rev163：N3 160MiB＋Root2MiB，V11独立64MiB；这些不是后继可继续使用的准入。N3准入rev162观察owned1476850608 B、gross7366237784 B，physical/quota/owned/gross四项通过；是当时事实。owned cap2GiB、gross cap8GiB、project quota84000000000 B（override到2026-10-26T16Z）、other reservations51177672294 B，不能私自清零。

已实际CAS **163→164**，关闭native、V11、共享回归和scene未来写入，仅留1MiB用于本次docs/Git/任务总线及小型闭场记录。`O3/HANDOFF-STORAGE.closed-tail1MiB.actual.json`为2850 B，SHA `89915280e44a356aaeba7ffe21c343c6d31ced5798421fb1a2749a98fe2cfc25`；实际owned1590406856 B、gross7366237784 B、卷可用124975980544 B，physical/quota/owned/gross检查通过，没有删除。

交接提交和push之后，最后writer关闭将另写 `O3/HANDOFF-STORAGE.final-future0.actual.json` 并将所有future归零；接手必须读该**实际最终文件和当前账本**，本文不预填尚未取得的最终SHA/CAS结论。尾项不是新场次准入，后继不得沿用rev162／163／164启动构建、Maven、保存或游戏。

关键现用保存、构建来源和失败证据用途复核仍为2026-11-01T04:00Z；没有因交接自动永久保护。N1原成功、N2失败、N3实际结果及回收清单继续可读；重建得出的中间副本按引用和用途评估，不按目录名或mtime自动删除。

## 恢复工作的最短顺序

1. 读根AGENTS、统一存储策略、本文与当前账本；重新核machine、时钟、默认mvn、Git与任务总线，登记新task。fetch后只允许rebase、普通push。先确认没有CK3、keeper和其他owner；不复用本文离线凭据作新启动准入。
2. 新准入下补上述实际变更的完整验证，并先消费N3原wait/qualification；未完成原生构建时按其真实失败位置恢复，不能复制旧DLL追认新源码。新文档提交造成HEAD变化时重新进行实际source binding，未变native字节不因此自动要求全量重建。
3. V10的`build/quarkus-app/quarkus-run.jar`已支持v3/v2，可用于读取其历史输入；repo原target可能仍是旧Request版本。新联合场次应使用上述当前完整Maven验证产物，按新clean revision正式构建89文件staging及v3三核心fixture11文件，另保留四核心独立recipe。MTS固定输入旧48文件manifest仍可用；DES旧18文件stage不是新DES源码产物，要验最新DES应新build并更换完整兼容Pin。
4. 新scene准入→case-inputs→source-freeze→Java六链Q（GAP0并逐一真实消费）→新native binding→runtime→public prepare。source-only review仅可覆盖确实未选中的源码/文档，不可掩盖活动C++。原执行COMMAND_SOURCE_EXECUTION的cwd要求repo root；cwd tools的真实命令应使用既有COMMAND_VALIDATION种类，不能伪改cwd。
5. 下次预计keeper a18／R0016，以实际allocator结果为准；previous指R15／keeper a17／CAS13909，交由真实reducer重验。旧purpose/state已消费不可复用；新独立state。若没有新的屏幕epoch，不把相同previous-release再作为latest-screen-release传两次。
6. 后继可参考累计1096MiB方案（cache160、native360、before144、PNG144、wire144、metadata144），**尚未准入、未证明当前容量可行**。a17旧分类器遍历整个S，会把独立V10/V11/O3算进scene metadata；如要分离须精确列出这些已闭根，同时所有bytes仍计owned。不能重置历史累计量。
7. `O3/PRODUCTS.rrf-core-hold3600.proposed.json`只把当前catalog的RRF core hold1800改3600，**PROPOSED_NOT_ADMITTED**；必须重新核源catalog无漂移，所有public阶段用同一--products。没有--hold-seconds开关，不可用case-inputs覆盖固定预算。timeout5400＋hold3600＋120＝watchdog9120，闭场另留600；启动时grant剩余至少9720秒。不要照抄旧2h grant，或在现有会话中延长冻结deadline。
8. keeper ready后才按实际支持模式临时2560×1440，保存原模式。后台Steam probe与public run紧邻顺序执行，30秒TTL内不要插入慢操作。正常测试三核心／DES默认，再独立四核心、无MTS和冷载；任何失败如实保留，不发布未验收0.2。

操作细节：widget_id和query_generation均为十进制字符串，另一根query会使旧generation失效；每次activate后重新query。B读取必须成对给target_rite_id和tenet_key。实际grid顺序不等于child路径顺序。原生root为rite_creation_window，2048控件上限会截断，不可把嵌套路径伪作root。需要桌面输入时取新原始PNG、真实尺寸、预览内容矩形，用desktop_coordinate_map.py＋receipt，两轴独立换算；键盘LANGID0409并确认控件焦点，全文读回。未知游戏事件仍原生采集后选实际第一项，不用OCR或鼠标代替。

正常关闭须提前操作：query→prepare_confirmation→query→continue_preparation→query→disable_exit_autosave→query→confirm_desktop（未知不重放）→observe；确认原native0和保留OS0，再finish_hold并消费host/public原wait，恢复显示、STOP keeper并消费其原wait、最后精确CAS释放。旧Root硬编码90秒保留不足以覆盖这次实际关闭耗时；人工至少提前600秒开始闭场。

本次未发布、未重新下载工坊缓存、未新增合格0.2商店图。续工目标是实际原生定制和同ID保存，随后四核心、联合模式、无MTS与冷载，而不是将更多源码或回执当成业务完成。
