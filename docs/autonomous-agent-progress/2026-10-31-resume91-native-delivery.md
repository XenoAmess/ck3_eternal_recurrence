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
