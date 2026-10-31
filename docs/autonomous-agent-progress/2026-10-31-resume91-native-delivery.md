# resume91 Native 交付执行记录

machine_id: `xenoamess-full-tower-eb9d2c1186`。owner：`/root/native_integrate91`。用户于本轮明确恢复执行，优先推进同一原版 Game 的普通自动游玩，同时推进八 M 和本地模型能力探索。本岗不部署 DLL，不操作 Game；运行现场由 runtime91 独占。

## GUI19 已正常发表

接手时 `D:/ck3-state/resume90-native-integration/delivery90` 保留 GUI19 精确暂存，未混入共享 Z 的 Locator/refund 工作稿。复用 Native66 已构建目标，于 `2026-10-30T18:49:18.288627Z`–`18:49:19.068648Z` 首次执行原休假取消的 `xar_ck3_12004_event_window_gui_dispatch_v2` 正式 CTest：1/1 通过，测试 0.35 秒，外层 0.780 秒，exit0。没有重编旧 7TU 或重跑九场 reader 绿例。

原件：`D:/ck3-state/resume90-native-integration/gui-dispatch-formal-ctest91.{actual.txt,stdout,stderr}`。最初默认 `ctest` 实为 Cygwin，拒绝 Windows 绝对路径；随后明确使用缓存记录的 Visual Studio CTest，正式执行通过。首次绝对路径 shell quoting 失败同样不是测试执行结果。

精确 19 叶先本地提交 `04608c4462`，正常 fetch/rebase 后为 **`b87c3ad78316982d7b7329d42826d751526aeea2`**，普通 FF push master 已 exit0；19 files、1506 additions、21 deletions。未 merge/force、未全树 stage/reset/stash。Java owner 随后正常重基发表其 GUI、Root fixture、status 三本地祖先，报告 master `c627799172`。GUI 明确请求 v2 与 legacy v1 仍分开；软件发表不代表当前 Game 已加载新 Native，Game 仍由运行岗掌握。

## 模型持久测试正取真实诊断

旧 Native 候选 `D:/ck3-state/model-dispatch90/native-json-fixture/ATTEMPT1-CONTENT.txt` 已原样物化到 `D:/ck3-state/resume91-native-integration/json-fixture-attempt1`。当前 Bridge 两函数只在 D 生成 include，候选未进入 shared 或发布树。`2026-10-30T18:52:35.236900600Z`–`18:52:52.049119700Z` 实际 CL exit2/16.813 秒，确认第60/61行有不存在的 `std::filesystem::read_binary_file`（C2039/C3861）及两个 `const char*` 相加（C2110）。原件为旧 integration 根 `json-model-native-attempt1-compile91.{actual.txt,stdout,stderr}`；编译器本机消息为 CP936，外层 UTF-8 显示坏字，错误代码和 API 仍可读。原源码/任务/候选/实际诊断已交唯一 HTTP owner models91 纠错，并要求补上 CMake 独特签名拒重。传输成功与编译/行为/采用分开记录。旧 Java 候选由 java_delivery91 独占处理，两边消费原留存两份 golden，不重新生成。

续行已完成软件闭合：`native-json-fixture-correct/ATTEMPT2-CONTENT.txt` 的 C++ fixture 原样 strict1TU/link exit0/8.275秒；其在旧实际函数下首次运行 exit5/0.720秒，明确 `golden mismatch for nonwar`，这是必要 RED。CMake 后续 `native-json-cmake-only03` 仍返回原2881字符、没有独特签名检查；实查 REQUEST 最后任务要求完整传达，拒绝该轮无修改输出，不归因封包遗漏、不据一次失误断言能力上限。owner 仅加12行独特签名检查，其余模型 CMake base 保留。

只采用原留存生产单hunk将 request_id/step/status 交给既有 `AppendJsonString` 后，复用 Native66 缓存构建新正式 `xar_ck3_command_result_json_v1_test`：CMake配置9.0秒、生成6.2秒，实际只编一个 fixture TU+link，外层 exit0/25.9405882秒。正式 `xar_ck3_command_result_json_v1` CTest于 `2026-10-30T19:16:52.537415500Z`–`19:16:53.263642200Z` exit0，1/1通过、测试0.42秒。原件绝对根 `D:/ck3-state/resume90-native-integration/` 下 `json-model-native-attempt2-{build91,old-red91}.*`、`json-native-formal-{build91,ctest91}.*`。

正式生产/测试/CI精确5叶已普通 FF 发表 **`34c3d0ad9e`**。Java owner先发表 `eb406589f0` 的普通两JUnit与两canonical资源；Native和Java消费同一份258B/218B payload，不重生成、不改换行。未编完整Bridge、未link DLL、未跑hosted CI，不授Game新动作/日。首次stage因非cone sparse未纳入两新叶，只在本地补精确sparse与fixup/autosquash自身未push提交，完整5叶才发远端，没有把缺叶中间状态推送。

## M1 Character 与三组持久入口已发表

Java 两个 public Context 正数门已先发表 `cebf0e9e0a`，大部分 Character 消费者此前已用 `NativeCharacterId`。本岗随后只按顺序应用 Character14 三生产叶26 grouped hunks、County134、Character135、Surrender136 四份精确补丁。9叶与 `D:/ck3-state/resume91-m1-native/M1-NATIVE-NINE-LEAVES91.json` 最终来源逐字相同（归一 EOL，不做全树来源审计）。本地 `3e3e74553c` 正常重基后 **`e2818cf865`** 已 FF push master exit0，9 files、714 additions、32 deletions，继承 Family `8611e0f227`。

三生产叶只将 Character 角色域统一为 signed int32 except -1、full32 lookup、Character member 唯一与排序；Faction 和 title/war 正域分别保持。持久入口复用原同一 faction-fullid target、原 Whole serializer、unused legacy Parse abort seam。沿用已有 Character 六baseline RED→14GREEN、County134十三入口绿、Character135十四入口绿；本轮 Surrender136 只实际增编两fixture TU/link缓存后跑三条新增selector，全exit0。25个 source 成员不是本轮重编数量。未重跑旧绿、未声称完整 shared target/hosted CI、Character allocator 或 Game 通过。

M0 queued GUI seam 仍未采用；后继 getter17、special 等候选保持独立。Native 当前没有部署 DLL。各线只执行新的必要小组合，不从旧交接复活整个取消队列。

## 优先运行的临时编译安排

Root 因真实 D 随机 I/O 与 worker104 类加载压力，先暂停研究新 CL/link/大复制；104自然exit1后撤销旧等待条件，曾恢复全局至多一个有限研究编译。最后已结束项目为 M0 trait 新组合、M1 新 Surrender Java三参数、M3 succession142新两场、M7 special纯Java36断言。M2 random准备器真实javac失败，未进 CL；JavaDelivery JSON 短javac曾未等明确授窗自行开始，可能与M2短重叠，已如实告Root，后继均须明确grant才start。

运行岗随后 MB105 必要 P0 增编 exit0/23.361秒，启动 worker105 同 Game 安装；研究新编译再次 HOLD，到运行岗明确阶段通过/终态再调度。模型 HTTP、源码审阅、已验源码发表继续；不是取消八 M 或让模型变为实际游玩前置。本岗当前无 CL/link 在途。

105于 `19:05:50.0109348Z` 真正 LOOP_START/next16后解除该安装hold，继续全局唯一小研究编译槽，各READY必须明确grant才start，失败保留已绿object，只修必要阶段。每次实际END才转下个岗，不依靠旧估时标签推定资源仍占用。

## MSVC 调用环境

M0实证第三方 `VsDevCmd.bat` 默认路径可能在 `VSCMD_SKIP_SENDTELEMETRY` 空时启动 PowerShell 遥测。已向八 M 传达今后在bootstrap前进程环境明确设为1，不修改SDK或全局环境、不为此重跑旧绿，不将未观测旧spawn写成“已证明没有”。本岗D中两编译cmd原已设1；正式现存 `tools/run_native_msvc.py` 的 `child_environment` 缺此字段，本岗只新增同一键值，独立正常 FF 发表 **`c31f3735fb`**。Java宿主同类缺口交JavaDelivery消费模型窄候选。

## 后续有限队列与真实失败（20:23Z）

Java宿主同类环境修复已以模型原样单行采用、单源严格编译exit0/10.209秒，发表 `67b4a9d984`。M1 getter17只重编断言修正夹具并跑此前未通过的局部roundtrip拒绝例，实际exit0；M2 GUI HELLO协商已发表 `147e648b3c`，没有Native能力广告，缺token仍走v1。M6新sameworld producer和Java fresh receiver已真实闭合：PID303040的新HELLO/fullSnapshot及54链进入receiver/assembler/context，两peer CLEAR；Java单方法1P，资源与生产未改。这些是软件离线组合，不是Game新动作。

运行岗后继106/107均实际终态，108于 `19:59:29.254Z` 真正LOOP_START后恢复唯一短研究槽。P0 obligations实际BEGIN时再次暂停研究新START；在途自然收，不以候选审阅或旧loop标签代替实际占槽。随后Storage与canonical必要短验证完成，MB109七源exit0/10.784秒，109于 `20:27:05.237Z` 真正LOOP_START、安装9.980秒后再次恢复单槽。最新Game动作/日期结论由运行岗给出，本岗无部署/业务操作。

M0 queued-v2原baseline的6个必要新TU现全部严格CL exit0，复用7旧对象；不是13TU重编。TU03..06各6.430120/5.915744/7.632873/8.265346秒，四个CL耗时之和28.244083秒，含消息边界的真实跨段wall为100.404374秒。LINK01首执行exit1120/2.533338秒，完整三个factory TU引入7个未执行reader/wrapper依赖；尚未产生EXE或执行唯一case，不能称行为RED或队列通过。原件 `D:/ck3-state/resume91-m0-native/bridge-queue/queue-actual/{COMPILE-TU01..06-01,LINK01}.json/.stdout`。保持原对象、只收敛真实链接闭包；未采用原seam。当前Z另有Locator与14表，和正式旧D无Locator/13表的兼容候选严格分开，不混对象或信用。

M6 actual4 Sway signed target router候选1TU与新formal test1TU分别CL exit0/8.602/9.120秒；两个真实legacy parser TU增编exit0/11.633秒，另4个common对象按必要源/头和编译档比对后只读复用。BASELINE-LINK首执行exit1120/2.547秒，完整legacy transport引入12个未执行binder/receipt依赖，当时没有行为RED/GREEN。真实dumpbin确认router/test不引用legacy executor，后继按唯一双签名从当前源提取两原parser函数，完整声明/body逐字保持；实际Router/Handler不替换，未增加链接桩。原失败与全部后继原件保留于 `D:/ck3-state/resume91-m6-native/router/build/*/ACTUAL.json`。

## M1 CI137 与 M6 signed Sway 正式采用

M1 CI137将既验原118B liege getter与实际County16消费者保留到现有fullid目标：只新增一个entry TU、三个同目标selector，持有local World/getter头与118B原件。模型新entry/CMake/dispatcher原样，owner只做旧夹具local include包装；新两TU /MP1+原cached link exit0/16.874736秒，三个新holder-zero/top-min/roundtrip-refusal各exit0，新argc90/unknown91符合合同，不重getter8或旧矩阵。正式D精确6叶采用（619+/2-）；共享Z旧未采用CI前像和缺席dispatcher没有被整树覆盖。原件 `D:/ck3-state/resume91-m1-native/liege-ci137/DELIVERY137.json`；未称完整shared CMake target或CTest已运行。

M6 exact-parser生成TU严格编译exit0/6.379秒，复用4common和已绿router/test后，两小link均0，旧baseline真正运行exit1、237检查/30失败；formal修复真正运行exit0、237检查/0失败。后继query/default各只新router+test两TU（14.692/14.299秒），link和run均0，各237检查/0失败。生成器保完整唯一双签名、依赖更新和原函数正文，不用镜像parser；模型extract05拒绝，extract06由owner仅修CMake FIND API/转义，原helper03/core04模型方法保留。最终三source叶按 `D:/ck3-state/resume91-m6-native/router/DELIVERY.patch` 采用，并在原CI目标清单与CTest正则各加三variant。只改actual4三条Sway target分类为canonical signed int32 except -1；旧.2/.3、legacy parser、Event/invalidation范围控制保持，三feature配置分别验收。完整CMake configure/CTest和hosted CI尚未执行，未编完整Bridge或部署DLL，无Game新动作/日信用。

## queued GUI 真实队列与持久入口（21:52Z）

M0旧 LINK01 的7个未解析符号由真实生产者补齐后，LINK02另暴露 BindCoreImage 和 Phase2 两接口；两次链接失败均保留，没有记成行为RED。仅新增必要生产TU及一个专用queued support，再从当前Core源动态提取原659B binder（含wrapper754B，逐字相同），最终原6个新TU+后继9个新TU全部strict CL exit0。24个实际链接对象中15个为本轮新编译、9个为必要旧缓存，不能写成24TU重编。

EXTRA09实际CL exit0/6.703041秒；LINK03以24obj/0archive实际exit0/4.431737秒；唯一首次RUN01于21:25:38.4340603Z真实exit0/0.281971秒，22检查通过。它执行真实submit、queued回调身份、owner pump、Wait和Reclaim，production callback完成Enter/read/Finish，image0结果是typed unavailable。没有available GUI、完整Bridge执行或Game调用信用。原件根为 D:/ck3-state/resume91-m0-native/bridge-queue/queue-actual/，保留LINK01/02/03及RUN01全部原件。

持久目标新增24-source CMake、动态Core原函数生成器、单个既验case及独立两guard support；原GUI dispatch的五guard support保持不动。两轮模型portable target/helper分别暴露漏Phase2、错误shared support、伪造root context、CMake FIND offset API等实际缺陷；纠正05保留模型24-source/MD/LF/dependency接线，owner仅修真实root锚与SUBSTRING-tail+FIND。最终Native CMake -P exit0/0.082秒，生成754B与已执行源逐字一致。独立源码复核为 D:/ck3-state/resume91-native-integration/QUEUED-PORTABLE-REVIEW91.json；驱动脚本只留D，不作为生产新叶。

正式采用冻结无Locator/13表前像的header、callback与Bridge五hunk，同原index11/physical slot20指向同一callback，view存活至原Wait/Reclaim；注册原CI目标清单和CTest正则。当前共享Z另有14表与Locator工作稿，本次没有用旧baseline覆盖它。新portable target未作完整CMake configure/build/CTest，完整Bridge TU、DLL链接和hosted CI未执行；本次不重15个已绿TU或22检查，不部署DLL、不重启Game、不新增能力广告。

M0 Title另一个独立源码比较也已结束：只动态提取当前production Read/Component/ResolveObjectiveTitle三原函数共1030B，新1TU/link/首次run分别exit0/8.4231705、2.287808、0.1226066秒；生产API返回Title*与原生返回VariableContext*的预期差异确实成立。旧whole-province/Army对象保留、12TU候选未编，新增native语义case0，不外推完整province生产链接。证据 D:/ck3-state/resume91-m0-native/getter-compare/exact-source/RESULT05.json。

## 首次已发表 queued target 构建验收（23:06Z）

上述精确10叶已普通FF发表为 **`18f906052a7e12e25c7cb822e9c1a25f69058a17`**。本岗后续仅正常快进到Java正式提交 `132db9161d58ea9d8d940fe7db71da91c57d8bbe`，二者之间Native路径无变更。此前手工24对象链接和22检查并未验证持久CMake入口，Root因此另行要求首次构建已发表target。

M0未新增Java物化平台、未POST该工具任务；仅以固定18f906的普通Git逐叶取得26个seed及实际include闭包，共388文件、2,321,787B。独占根 `D:/ck3-state/resume91-m0-native/bridge-queue/portable-formal-build/` 保留source/build缓存。四行最小CMake入口含CTest，直接include已发表queued模块；模块和helper原字节保持。它验证独立target，未配置整个Native根项目。

Native Windows CMake/Ninja Release、`BUILD_TESTING=ON`、`--parallel 1` 首次配置exit0/4.532秒（23:04:17.311–21.844Z）；首次实际24个TU编译加link共25步exit0/79.590秒（23:04:39.642–23:05:59.232Z）。没有借用旧手工24obj或EXE。原模块的`/UNDEBUG`覆盖Release默认`/DNDEBUG`产生D9025提示，构建真实成功，未为此更改旗标。生成Core754B与此前实际执行原件相同。

随后只在同build执行精确CTest注册名 `xar_ck3_12004_event_window_gui_queued_v2`：23:06:43.180–43.501Z，exit0/0.319秒，1/1通过，测试0.16秒。该次证明首次CMake构建及CTest接线可用；它仍是原22检查、image0/typed-unavailable案例，新增语义覆盖0。完整Native根、Bridge/DLL、GUI available、Game和hosted CI均无新增通过信用。配置/构建/CTest原始命令、stdout和终态保留于同根 `{CONFIGURE01,BUILD01,CTEST01}.{json,stdout,stderr}`，最终入口为 `HANDOFF.md` 与 `RESULT.json`。

当前资源安排依Root最新实际规则：具名只读source查询最多2路、最多8显式源的小javac最多2路，与Native重编1槽分开；有限自持小JVM执行也不占Native重编槽。115于22:55:03.4073879Z真实LOOP_START后已解除安装等待，不能沿旧HOLD阻挡后继。实际Maven/安装新BEGIN时停新编译，在途自然END；HTTP和源码准备不算编译占用。本岗仍未部署DLL或操作Game，实际游玩结论只由运行岗回执给出。

## fullid hosted CI 链接缺口的两叶修复（23:41Z）

对18f906的GitHub Actions run `41134827977` 于22:51:59Z实际失败：keyed-query步骤构建 `xar_ck3_12004_faction_fullid_whole_test.exe` 时，当前 `holy_site_relic_navigation12004.cpp` 引用的 `ReadIngameUiGuiOwnerBindingV1` 未定义（LNK2019/1120）。该步未进入CTest，后续Java全reactor也未执行；它与已独立通过的queued target分开。完整失败日志为 `D:/ck3-state/resume91-native-integration/CI41134827977-keyed-query-failed.log`。

当前正式CMake只在Bridge源集合登记完整 `ingame_ui_navigation_v1.cpp`，fullid所链接的runtime集合没有它。修复只新增一个测试生成器，从当前原文件按两对完整唯一签名提取240B `Actual4UiBoundV1` 与687B `ReadIngameUiGuiOwnerBindingV1`，加wrapper共1109B；Native CMake -P与逐字比较通过，保留LF和原源依赖。fullid target增加该generated TU，并在现有三query别名同一PRIVATE作用域为Read函数指定fixture私有符号；生产Bridge、runtime、实际executor与原函数body不改，没有新增实现桩。

本地先遇formal sparse缺头C1083（0.815秒），补当前精确144头闭包后，原名字版本的generated TU与当前caller分别严格编译0/3.951、4.064秒。首次缓存链接随后LNK2005/1169、0.450秒：旧native63缓存runtime已含完整ingame对象，与本次新Read重复；该205,472,424B旧库和正式当前runtime装配不同，不能盲借旧link信用。最终target私有别名避开此差异，原两绿对象与失败均保留，没有复制、修改旧库或使用FORCE。

别名改变实际符号profile后，仅必要两TU重新严格编译：COMPILE-ALIAS01 exit0/3.955秒，COMPILE-ALIAS02当前caller exit0/4.012秒；原精确缓存闭包LINK02于23:41:31.700Z实际exit0/0.635秒，产物1,292,288B。未运行旧fullid矩阵或queued案例。此为当前原body与当前caller的必要局部链接通过，完整正式CMake target与修复后的hosted CI尚无通过结论。

三次模型输出分别提出整137KB executor TU、错误首右括号/硬长度截取、截断的递归wrapper，均未采用为实现；owner复用已验CMake切片方式并接管target私有别名单行，按实际来源记录。最终集成输入为 `D:/ck3-state/resume91-m0-native/fullid-owner-ci/candidate-alias/cmake/` 两叶及 `FULLID-CMAKE-ALIAS.diff`，原件、精确命令、缓存差异与结果见同根 `HANDOFF.md`、`RESULT.json`、`ALIAS-PLAN.json`。本岗独立复核后只采用两CMake叶与本页，不部署DLL或操作Game。

117于23:39:17.0609316Z真实LOOP_START、安装9.095秒后已解除安装等待；下一实际Maven/安装BEGIN再暂停新编测，不沿旧117标签空等。

## M7 公开组件与正式 CI 接线（01:29Z）

已验原179B dispatcher与480B constructor的软件合同现有正式公开接口 `m7_idler_components_v1.hpp`、共享core及独立两源测试target。Memory、Symbols与typed callbacks由调用者提供；dispatcher保留callback后fresh cursor/end/list读取、signed32 wrap与typed null终态，constructor保留三次分配、fresh O20、descriptor无条件源读取和query前保存O50。两个生产函数采用本地模型原样方法，未由owner改算法；CMake两轮漏runtime登记后owner补上无条件 `target_sources(xar_ck3_12002_runtime PRIVATE ...)`。测试两轮后由owner修正实际API装配，复用6+8场景，不把接线验证算新增原码语义覆盖。

本岗独立读完公开header/core/test/module及Root/CI上下文，仅采用精确六叶。旧补丁的CRLF context以ignore-space-change匹配，清除新空白行尾空格，未改变算法。Root CMake引入模块；既有static CI目标清单增加专用target，并新增精确CTest步骤。未触及bridge.cpp、DLL部署或实际Game。

首次正式模块验收根为 `D:/ck3-state/resume91-native-integration/m7-formal-ci/`：仅从已采用formal复制四必要叶35,589B，7行最小入口提供CTest和runtime登记目标，直接include原模块。Windows Native CMake/Ninja Release首次配置于01:28:30.577–34.445Z exit0/3.867秒；只构建专用target的两个TU及link，于01:28:43.837–46.288Z exit0/2.451秒。D9025只是原 `/UNDEBUG` 覆盖Release `/DNDEBUG` 的提示，没有为此改旗标。runtime SOURCES属性实际包含新core；完整runtime和Native根没有构建。

同build精确 `xar_ck3_12004_m7_idler_components_v1` CTest于01:28:53.136–53.396Z exit0/0.259秒、1/1通过，测试0.12秒。实际stdout为14场景（dispatch6/construction8）和781检查。原始 `{CONFIGURE01,BUILD01,CTEST01}.{json,stdout,stderr}`、PLAN及LastTest均保留。M7另行把同一public API接入Java facade与7个JUnit方法，Java owner独立发表；本页不以它代替Native行为或实机证据。

上述验证仅证明公开组件、runtime源码登记与专用CTest接线；自然live H/P、真实callee、完整Bridge链接、hosted CI、M7跨继承Goal和Game动作/SAVE均未因此完成。125实际MB/安装BEGIN到达时本组编测已全部END，本岗仅继续小型源码发表；下一真实LOOP后才恢复新的编测。

## Fresh owner 读取与关联快照生产路径（02:25Z）

采用 M6 独占候选的四个生产文件、14 处局部修改。WorkerAdapter 增加经现有注册 executor 和 MainThreadQueryMailbox 执行的 fresh snapshot 读取；执行前后核实际 slot、sequence、owner、executor/context 与主线程 stamp，失败读不返回旧快照。Bridge 增加 `query-fresh-full-state-v1`，要求 expected_revision 为零，将实际 owner 观测以 read_request_id 关联的 state_snapshot 先写出，再写同 request_id、snapshot_id、revision 的闭合 ACK。unchanged fresh 观测仍发布，成功写出后才提交 fresh revision/previous/checkpoint 状态。普通发布分支保留原行为，新增 `.4` capability；没有部署 DLL。

本岗独立审阅完整四叶差分，并仅以每个旧块唯一匹配应用 14 处修改。`D:/ck3-state/resume91-native-integration/fresh-formal-apply/APPLY-RESULT.json` 记录全部匹配次数为一，四个正式文件在仅规范 EOL/BOM 后均与实际编译通过的 M6 候选 body 相等，没有集成时算法修改。M6 原候选 semantic TU 严格编译 0/9.620 秒，含 capability 的 `.4` adapter TU 已在必要三 TU 组严格通过；整个 Bridge TU 首次严格通过发生于 01:52:28.790–48.842Z，0/19.940 秒、peak 869040128B、Job active0。此前 C1083 输入闭包失败及 PowerShell roots 数组误算写入预算的 owner 准备错误均保留，没有归作模型语义错误。

三份离线行为证据各自首次通过，均为本次当前源码对象，不借旧 runtime 库。publication unit 为实际 Win32 pipe、原 StateSnapshotFrame/PublishSnapshot 函数，0/0.468 秒；owner executor unit 使用当前 semantic/mailbox 实现，0/0.409 秒，stdout 为 `ok=1 pair_ms=16 raw_reads=4 wrong_owner=0`，覆盖同 clock 连续观测、wrong caller、读失败恢复及 Uninstall 后拒绝；Handler ACK unit 于 02:07:39.823–40.344Z 0/0.405 秒，stdout 为 `fresh-ack: ok=1 raw=5 wrong=0`，覆盖 stale、实际成功、unchanged、失败、恢复、首 snapshot 写失败及卸载后的七条路径。普通非 fresh 扩展的六个 link seam 仅 typed abort，误调用立即失败，不提供成功替身。

M6 的 `production-fresh/{DELIVERY,BRIDGE-RESULT,EXECUTOR-RESULT,PUBLICATION-RESULT,ACK-HANDLER-RESULT,MODEL-REVIEW04}.json` 保存原件与采用范围。生产 primitive/发布/ACK 主体在多次实际源码拒绝后由 owner 接管；模型原样 worker 小方法、serializer 插入及 capability 修改与 owner 补充边界分别记录。三个 unit 目前保留在 D 候选，没有据此宣称已接入正式 CI；ACK 在 snapshot 已成功写出后自身第二次写失败、完整 DLL 链接、公开 dispatcher 运行和 Game 读取仍未验收。本次没有重跑上述已绿 unit，没有 Game 查询、动作、进程重启或 SAVE。

## Hosted CI 新失败与 Native63 路由事实（02:25Z）

实际 hosted run 41146299012 的 step31 共 70 个测试，其中 43 个 faction_fullid 测试通过，证明已发表 5a48 链接修复在该组件的 hosted 构建和行为通过；整组仍有四个失败，不能称 CI 绿。失败是 player_claims_internal_wait_v1 及三个 gift raw identity controls。HTTP/2 CANCEL 是日志下载传输失败；M0 使用任务子进程环境 `GODEBUG=http2client=0` 重取同一日志，exit0/5.333 秒、265012B。Gift 修正过时 source-zero 负例为实际拒绝的 FFFFFFFF sentinel，保留 19 个负例，单 fixture TU 已严格编译 0/7.353 秒，尚未据此授行为通过；Claims 只增加有界真实 site/thread/tick 诊断，原 qualified 条件、计时器及 final checks 保留，尚无根因修复结论。

Runtime126 的实际 Native63 ACK 明确拒绝 `query-family-marriage-send-outgoing-v1-private` 为 unsupported。本岗仅查已持 Native63 frozen source/声明：已有 specific observed-first-heir-marriage-result 路由和冷 pending scanner，需要不同字段与特定观察身份，不能改名冒充 generic prepared outgoing。映射原件为 `D:/ck3-state/resume91-native-integration/NATIVE63-FAMILY-OUTGOING-MAP01.json`。M2 后继 generic endpoint 的三个新 TU 已严格通过，但现有原件缺完整 storage 双拷贝及 finalized actor-shadow 五角色 context provider，当前软件合同只明确 completed_unavailable，不授 Family 读取支持或 G2 完成。128 于 02:19:56.903Z 实际 LOOP 后已解除安装暂停；后继资源只按新的 actual BEGIN/END 管理。

## Family typed unavailable 端点正式接线（02:54Z）

M2 的新 ABI header、三个小生产 TU、Bridge 五处局部接线及 CMake 三源登记已采用到正式 D 候选。新入口保持真实 Java 字面 `query-family-marriage-send-outgoing-v1-private`；按五种原 action route、ACTION_PREPARATION/POST_SUBMISSION 两个 scope 和实际角色字段解析，只在实际 before/after snapshot frame 一致时返回明确 unavailable。preparation 使用原 materialized-context unavailable 合同，post 的 prepared_context 为 null；没有把旧 specific first-heir 结果改名，也没有编造 occupied IDs、候选 rows、canSend、local shadow context 或 storage 双读通过。

四个新文件在仅规范 EOL/BOM 和行尾空白后与实际已验候选 body 相等，M6 Fresh 的全部 14 处已采用新块仍保留，见 `D:/ck3-state/resume91-native-integration/FAMILY-MERGE-CHECK01.json`。集成 Bridge 首次编译因 source 从 M6 candidate/src 迁到 formal/src 而丢失原隐式 quoted include 根，真实 C1083 保留；只显式补入原已闭 candidate/src 根后，同正式 Bridge TU 在原 Sway 三旗标及无条件新增 Family 分支下严格编译 0/18.920 秒，peak869842944B/Job active0，未重建头图或 DLL。

第一份直接 typed 合同验收为三个生产 TU strict0/5.229 秒；新 fixture 一 TU 0/4.833 秒、缓存 link0/3.062 秒、首运行0/0.092 秒，51 场景/145 断言、11 wire；当前 Java 生产解码首次通过11正例及490负例/1236检查。独立审阅发现该链绕过新增 native 字段解析，因此另补真实请求链：Java nativeFields/NativeWire.execute 首次产10原 payload 与 packet（52检查），不重新编码 payload；新 fixture 单 TU0/3.779秒、缓存四对象 link0/2.092秒、首运行0/0.071秒，10实际输入和10变异负例/131检查，经实际 ParseFields→typed reader→serializer 生成10新wire。最后仅消费这10新wire，同一 Java producer 单源 strict0/1.350秒、consume0/0.572秒/269检查，未重产输入或重跑前51/490。

原件为 `D:/ck3-state/resume91-m2-native/family-outgoing127/` 的 DELIVERY127.diff/md、MODEL-REVIEW127.json、RESULT127.json、`bridge-integrated130/RESULT130.json` 和 `field-roundtrip130/` 各 ACTUAL。serializer/dispatch 模型纠正 core 部分采用，owner 类型/schema 补充、字段 parser 多次失败后的窄接管与测试 before-images 修正分开记录。当前 source 路由和 unavailable 软件合同通过，不授 generic storage/context provider、完整原 family feature 矩阵、hosted CI、已载 Native63、DLL部署或 Game 读取成功。131 新实际 Maven/安装 BEGIN 时本组全部编测已 END，只继续小源码发表。

## DATE 与 CROWN 的冻结 Native63 源映射（02:54Z）

只读对照当前 Java OriginalPlanRouting/AdvanceClock 与已持 Native63，`life-advance` 为 Java composite；其实际 set-speed-1..5、terminal-a-0 Sentinel Arm、Status、uint64-generation Cancel、resume-map、pause-map 在63均有真实 handler，三 sentinel capability 与 Java 常量逐字相同，`.4` descriptor 明确登记。`.4` serializer 与 Java SentinelCodec 对应20字段和 numeric uint64 generation。初始 idle/reset 的 native speed0 不符合 Java speed1..5，但当前 ordinary AdvanceClock 先 Arm 再 Status、取消保留已 arm speed，所需路径匹配；未外推所有 pre-arm idle 消费。源映射为 `D:/ck3-state/resume91-native-integration/NATIVE63-DATE-ROUTES01.json`，没有新 query、PE读取、启动重验或 alias 修改。

运行岗另请求已结算 CROWN 后 final-terms 读取映射。M1 在 frozen63 与当前正式源确认：`.4` 实际提交 ExecuteRealmLawPausedPrivateQueryWithTurnTick12004，PopulateNonwarRouterExecutors12004 却登记旧 ExecuteRealmLawPausedPrivateQuery12002；MainThreadQueryMailbox 的逐指针白名单会拒绝该组合，产生 submit_unavailable。route 本身存在，不能因 Bridge 字面搜索未命中就称 endpoint 缺席。证据 `D:/ck3-state/resume91-m1-native/crown-finalterms130/MAPPING130.json` 分开记录 source 缺口与未知 loaded binary；隔离登记修复及实际注册回归正在准备，尚未正式采用或部署。runtime129 已实际 CROWN APPLIED 的事实由运行岗保存，不因后续消费失败重发动作。

## CROWN final-terms executor 登记修复（03:07Z）

采用 M1 三叶原样候选：在相同 REALM_LAW_PAUSED_PRIVATE_QUERY feature guard 内加入真实 TurnTick 声明，并仅把 PopulateNonwarRouterExecutors12004 的 law_final_terms 改为其实际提交的 WithTurnTick12004 callback。Populate12002 继续登记旧 callback。既有 realm_law_wire_test 增加 `--registration-check`，直接执行两个版本的实际 Populate→Register，核各自 mailbox permitted slot；既有 TurnTick whole fixture 模块新增独立 CTest 选择器，未重跑旧 wire 矩阵。

没有可直接授等价的 current whole fixture 对象缓存，因此只验证此次实际登记行为：从当前生产源码精确抽取完整 Populate12002、Populate12004、Register 三个函数 body，引用四个真实结构/声明 header，运行新 selector 原断言。未执行的 callback 仅 typed abort 测试符号，实际未触发；`/OPT:NOICF` 和 old/new 指针不同断言防止地址合并遮蔽缺陷。baseline generated TU 编译链接0/3.194秒，唯一 selector 预期 exit1/0.004秒，精确 `.4 registration mismatch`；candidate generated TU 编译链接0/2.910秒，同 selector exit0/0.011秒、`.2/.4 isolation` 通过，03:04:59Z 全部END/资源释放。没有把这两个 generated TU 写成完整 router/whole fixture 编译。

两轮真实模型返回后 impl02/test02 的精确修改原样采用，第一轮缺 include、模糊 span、无关 guard 与测试缺 `.2` 隔离的源码拒绝保留。正式三叶 patch check0/application0，本岗仅增加交付记录。原件 `D:/ck3-state/resume91-m1-native/crown-finalterms130/{DELIVERY130,MODEL-REVIEW130,MAPPING130}.json` 和 `unit/ACTUAL130.json`。该结果闭合源码的登记指针错配；未授 actual query 执行、完整 Bridge ABI、hosted CTest、DLL部署或129 loaded binary根因，未重新提交 CROWN。
