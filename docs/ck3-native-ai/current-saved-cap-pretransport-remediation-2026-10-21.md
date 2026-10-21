# CurrentSaved CAP 与后台窗口门禁整改（2026-10-21）

`machine_id: xenoamess-full-tower-eb9d2c1186`。证据截至 UTC `2026-10-21T13:52:50.450482Z`；闭场观察为 `13:46:29.382952Z`，basis 资格观察为 `13:47:25.462208Z`。来源为本轮真实 A28 请求、闭场及 Driver/SAVE 小型取证回执。

## 实际失败与闭场

A28 的 SEM `11375` 实际返回，postcheck 通过。CAP `11376` 随后在本地门禁中，把原 Queue 写出的 flat 六字段 `INFLIGHT` 误按嵌套 `request` 读取，因而在 transport 前 HALT。CAP 未进入原生调用，没有 FULL、新游戏天数、普通周期或 checkpoint；原请求未重放。

实际闭场为 SDK 退出码 `[1, 0]`、Game forced exit `1`、Game Job 活跃数 `0`、录制 worker `0`；supervisor/display Tasks 已不存在，screen126 于游标8023释放。R0016 为 completed-red，不能作为业务验收通过。累计仍为5143周期、5622天，Driver history5896，下一序号11377。

## 整改与验收

`current_saved_campaign_preflight_v1.py` 采用原 Queue 的单一 flat 六字段 DTO；入口校验必填字段、类型、来源和实际请求文件，再构造内部类型。持久化读取及消费者采用同一合同，无嵌套格式兼容别名。未知结果不得重发的守卫保留。

回归通过真实原 Queue 的 `call`、atomic 写入和 session 路径执行 SEM→CAP→BOUND。完整16项通过、0 skip，其中24个错字段、错类型、错路径及重放条件负例没有新增 transport 调用。basis 15项、cold consumer 9项也通过，合计40项、0 skip。离线消费者修复已经通过，下一场原生 CAP 仍须实机读回。

`current_saved_basis_v1.py` 为本次失败增加独立 v2 epoch；原 v1 业务 basis、失败回执与原始字节保留。实际18个 ref 的消费者校验通过，绑定闭场后的 Driver、原 checkpoint 和 business seed。多个 restore bookkeeping 行按实际 lineage 校验，不把失败记为业务进度。

Root 对实际 Driver 完整读取2次，共85540610字节，包含第一次错误比较后失败的读取。SAVE 正文读取及完整哈希次数均为0：复用旧 canonical 来源 SHA，核对当前 SAVE 的 FileID、大小及 mtime 未变。本轮未重新执行 canonical API，未声称重新校验 SAVE 正文。

八个 Python 文件联合检查 `--strict --strict-equality --explicit-package-bases --follow-imports=silent --no-incremental --cache-dir=NUL` 实际通过，输入前后稳定。扩大到11叶的检查失败，52条诊断位于未修改的 `tools/ck3_live_run_id.py` 和 `root_saved_campaign_preflight.py`；失败回执保留，未压掉诊断。八叶通过不代表全仓库严格类型通过。

修改范围为 basis/testbasis、owner、core/testcore、testcold 六个源码叶；producer、feeder 参加联合类型检查但源码未改。现有 CI 已运行相同八叶类型检查和整个 preflight 测试模块，新测试随本次源码进入。新提交远程 CI 按精确 SHA 另行记录，不预写成功。

G2 仍为6/8，30年仍为5622/10950天；A20 实测活动 FULL 为2.62388555秒/日，含 HOLD 连续墙钟为4.632秒/日，1秒/日目标未完成。Source32 scoped clock 优化已离线资格化，实际吞吐须由后续完整批次验证。A29 使用新 v2 basis 从11377开始，保持同一30年目标和原墙钟起点；本记录不预记 A29 启动或推进成功。

## 证据

下列回执均属于上述机器。根目录 R：

```text
D:/codex-ck3-demos/2026-10-14-robert-30year/continuation42-cold-prep/p51-fresh1066-v20261019-prepare01/c23-source23-native30-cold100/current-saved-cap-pretransport-fix01
```

| R 内文件 | 字节 | SHA-256 |
| --- | ---: | --- |
| ROOT-A28-ACTUAL-CLOSED-NO-BUSINESS-INDEX01.json | 9870 | ff6a1ca415a7e007baa6b5986be8800e3245f61febd958b60bb91d2883a73764 |
| ROOT-A28-CLOSED-DRIVER-SAVE-REVIEW01.json | 4113 | 8a1710900331aabb748db34de074edb0ee08177f33da8a208e364cd298bd3f58 |
| ROOT-A28-CANONICAL-SAVE-IDENTITY-REUSE01.json | 3127 | f6939cdb862af4600dbceb608046ebf18abdaf9a61df60d0cf5e28f088b4465a |
| CURRENT-SAVED-CAP-PRETRANSPORT-FAILURE-EPOCH01.json | 6397 | 716ef3ed10d62380dd458608bc2f1511f8b98fc27505fcb9f7e3aba16cf3f574 |
| CANONICAL-SAVED-BASIS-QUALIFICATION01.json | 2944 | da10ddaee3dcbb97aac9305b6f56bd1b2cfdc6dc8844bb355a875e4fc5e623a5 |
| ROOT-CAPFIX-FINAL-STRICT8-QUALIFICATION01.json | 2771 | 36658cb549e41342715687884804f20d6a8fca75c311ff153fb3fe9c87bf3d2c |
| ROOT-CAPFIX-FINAL-STRICT11-QUALIFICATION01.json | 11243 | bffd8102e446fe0604f2948c4c27847859648e4c2a09980b92d91028d22ee022 |

回归结果来源为本轮实际执行 stdout；上述回执继续绑定原生请求、失败 traceback、原 frozen guard、闭场与 basis 原件。

## 14:48 UTC 补充：后台任务与用户窗口共存

以下仍属于 `machine_id: xenoamess-full-tower-eb9d2c1186`。

A29（R0017）于14:07:48实际启动 Game，原监护器因启动前后 HWND 不同而关闭，桌面 ID 未变；SDK 未启动，Game forced1、Job0、Task 已移除，screen127按8029释放。14:09:12对仍存在的 after HWND 做只读查询，观察到非 Game PID6292；这不是启动瞬时的 PID 证明。旧门禁只比较 HWND，缺少归属采样，不能据其拒绝回执断言游戏抢了焦点。

A30（R0018）在 Task 注册前，因临时追加的20秒窗口静止诊断被拒绝，Game/SDK/录制/请求均为0。screen128按8031释放，编号记为 voided、allocated unrun，永不复用。20秒静止是本轮执行者追加的诊断，不是用户要求的后台任务前提；后续准入不要求用户停止正常切窗。

整改使用独立共享 `background_foreground_contract_v1.py`。入口严格接收七字段，持久化输出九字段；JSON auxiliary PID list 与内存 tuple 由唯一编码/解析往返。精确整数、未知归属、Game/owned OBS 归属、桌面变化及伪造派生分类均有校验。用户切到明确的非 Game/非 owned OBS 窗口可以继续，未知归属或桌面变化拒绝。采样采用 HWND→PID→HWND，并复查桌面；不能以 HWND 相等掩盖未知身份或采样竞态。

迁移覆盖实际启动监护器、窗口放置、显示入口、active PNG worker 与 OBS placement 回调。窗口放置从当前源码冻结到新运行树，监护器、子进程加载器与哈希共同指向该副本；只修改 Z 工作树而仍加载旧 H 模块不能算完成。原 H、旧运行树和旧失败回执保留。

OBS 内部保留已有的有限自身窗口最小化清理：只有已保留身份的自身 HWND/PID 才可进入一次原生最小化，观察仍记录 `OWNED_AUXILIARY_FOREGROUND`、`permitted=False`；这不是准入。最终 probe 必须无例外通过才能 GREEN。观察回执描述采样端点，不能声称整个区间从未瞬时改变前台；不恢复或激活其他用户窗口。

14:41的最终十一叶联合类型检查真实拦下两条 focused test 类型错误，失败回执 `R/ROOT-FOREGROUND-FINAL-STRICT11-QUALIFICATION01.json`（4131B，`d7da33e95f33e79412a9608da3182978bc3cc6fc721ae42dc6eef3f63b995b32`）保留。已修正 JSON list 类型上下文及未显式导出的 ctypes 测试访问，后续最终检查另记新回执。placement 单独扩大检查仍有26条历史诊断，不把聚焦新模块通过写成该整文件严格通过。

CAP 修复提交 `2f07ef209da59f08ccf90bcacc94a9bb125a41b7` 的 [Official CI](https://github.com/XenoAmess/ck3_eternal_recurrence/actions/runs/39613515160) 与 [Linear history](https://github.com/XenoAmess/ck3_eternal_recurrence/actions/runs/39613515141) 已终态 SUCCESS。观察来自 GitHub Actions API；CI runner 的机器 ID 未知，本机仅作观察者。小型回执 `R/ROOT-CAPFIX-2F07-CI-TERMINAL01.json` 为1840B，SHA-256 `fd460b7887fae219a5dfd0c4e1d49732c996429134c680a63dda61549f13ea9e`。它不代表尚未提交的后台窗口修复或实机 CAP 已验收。

14:51 UTC 最终软件验收：十一叶联合 `--strict --strict-equality --explicit-package-bases --follow-imports=silent` 实际0诊断，输入前后稳定；新回执 `R/ROOT-FOREGROUND-FINAL-STRICT11-QUALIFICATION02.json` 为3646B，SHA-256 `bb6bbfae70aea30b4a018f1125af7ff7087995ef2411cbf9c42879e47d47e25e`，旧失败01不覆盖。最终生成启动代码4项、8个原生采样模拟分支通过；最终录制流水线14项、0 skip通过，包含实际写入调用→JSON序列化→机器/UTC/嵌套九字段解析。独立只读审查于14:51:37 UTC通过，无剩余P0/P1；它是源码与生成接线审查，不代表新运行树已物理加载或 Game 已通过。

最终十一叶类型范围包含原八叶及新共享合同、renderer、focused test；placement 本体的26条历史诊断继续保留。CI 已接入同一十一叶参数、新 launch 测试类及整个 focused 测试模块。六个修改源码的精确摘要与各执行者结果收于 `R/ROOT-FOREGROUND-FINAL-SOFTWARE-QUALIFICATION01.json`。下一步仍需新运行树的完整实际前置链、子进程来源、原生 SEM/CAP 和首批 FULL 验收；当前业务进度没有增加。

## 停止启动后的系统性复盘（2026-10-21）

本节属于 `machine_id: xenoamess-full-tower-eb9d2c1186`。观察日为2026-10-21，机器身份已再次通过 `tools/ck3_live_run_id.py machine` 读取；来源为原交接、各场小型闭场索引、真实错误栈及本次离线回归。用户最新指令为“先别启动CK3，先梳理为什么一直起不来”。该暂停继续有效；本轮不创建新游戏、SDK、录制或N32运行树，不注册或运行新的启动Task。

### 当前事实

当前工程的主要失败集中在启动、恢复和验收适配层。A20确实完成13个FULL、390个普通周期，并保存193日；累计仍为5622/10950日、5143周期，日期1082-02-09，余5328日。G2的M0–M5原定切片完成，M6、M7未完成，仍为6/8；不能将切片验收外推为全面战略能力。

从源码到推进，实际链路是：源码组合与冻结 → 离线消费者检查 → 监督器/窗口放置/录制 → MCP与Native → 普通规划器/feeder → 保存与闭场。工作树、冻结H、SDK Source32和每次N运行树有不同职责；某个源码或单模块通过，不能代替实际运行树的组合验收。

A31（R0019）已安全闭场：原Task的child退出1、Job活跃数0；原Scheduler实际确认Task不存在，screen129按CAS8034释放至8035，编号记completed-red。未形成ADMITTED、Game launch、SDK或新FULL。原失败树不修改，闭场索引记录Root本次操作错误。

### 逐次失败发生在哪一层

| 场次 | 已证实到达与停止原因 | 对应判断 |
| --- | --- | --- |
| A03–04 | Game已经启动；先后暴露base Python -S跳过pywin32路径、录制目录/固定provider处理错误、SDK custody接收超时及闭场validator漏导入 | 多个启动/录制接缝错误；custody超时先后次序未完全确定 |
| A17 | 已进入实际AUTO；时间推进等待或暂停后验失败 | 有真实原生推进问题，不能归因于其后的零RPC故障 |
| A18 | Game、Native注入、SDK进程创建；生成entry导入不存在的xar_autoplayer.mcp_server | 正确模块为xar_autoplayer.bridge.mcp_server，0RPC |
| A19 | SEM/CAP实际通过，journal也返回；Queue后验引用未定义MACHINE | 原生返回不等于完整后验成功，0FULL |
| A20 | 13FULL、390周期、193日保存成功 | 运行和保存已有实证；Game最终forced1，正常关闭仍未通过 |
| A21 | 完整前缀、尚无Game | 文件哈希digest(path)被同名SHA文本解析器覆盖 |
| A22 | Task已运行、尚无Game | 错把新运行树N/state当作共享STATE路径，环境文件不存在 |
| A23 | Game、SDK和SEM原生返回 | 续存档错误进入“1066创始anchor”分支，后验拒绝当前帧 |
| A24–27 | 离线整改/准备；A24按用户要求停启，后续资格明确无Game | 不能把每个准备编号都计作一次引擎启动失败 |
| A28 | Game、SDK、SEM11375均成功 | CAP11376在transport前把flat六字段INFLIGHT误读为nested request |
| A29–30 | A29创建Game后因HWND变化关闭；A30在Task注册前拒绝 | 缺少即时归属证据，不能认定游戏抢焦点；20秒窗口静止是执行者额外要求 |
| A31 | 完整前缀失败；原Task也在pre-ADMITTED同错退出，0Game | placement污染包搜索路径，另有Root忽略前缀非零结果仍提交Task的操作错误 |

历史入口：[A03–04交接](../handover/2026-10-20-robert-source26-a05-vacation-handoff.md)、[A17真实推进失败](../handover/2026-10-21-robert-source29-a17-clock-failure.md)、[A20保存闭场](robert-a20-saved-progress-2026-10-21.md)。A28–30原始证据见本文前述章节；A31原件见下表。

### 共性根因与验收为什么漏过

1. **跨模块合同与生成代码反复漂移。** 错误涉及模块名、共享状态路径、字段形状、同名函数与未定义常量。强类型能拦下一部分错字段和错类型；包搜索顺序、真实文件布局、运行分支语义仍必须在运行时验证。当前并未达到全仓库严格类型通过，placement此前整叶检查的26条历史诊断尚未逐项清理。

2. **验收组合不完整。** 旧Prepared准确标记为OFFLINE_CONTRACT_PREPARED，fresh_native_qualification和full_loop_permitted均为false。它执行若干独立消费者；OuterCtor验来源却未调用canonical.tools，boot.api先于placement导入，后续只投影部分原AST。因此它没有测试“placement产生导入副作用以后，再解析原生creator包”。录制child-import测的是另一个入口，Win32模拟主要测试提取后的判断逻辑，也不执行该顶层副作用。将这些局部绿色理解为完整启动通过，是执行者对证据范围的错误外推。

3. **A31确定性包冲突。** N31/creator-tools/g2_saved_campaign没有__init__.py，是namespace package；N31/tools/g2_saved_campaign有44字节__init__.py，是regular package。placement把N31/tools永久加入sys.path；Python会选中regular包，即使creator-tools后来移到首位也不改变结果。canonical文件存在、来源SHA已通过，随后仍找不到子模块。真实错误链为supervisor:441 → canonical.tools():91；它早于ADMITTED:463、keeper.start:473和Game创建:502。多路fresh interpreter与PathFinder复核一致，不需要假定缓存残留。

4. **执行链没有传播失败。** Root的嵌套exec_command返回exit_code=1，外围functions.exec只打印结果，仍继续调用Task注册和Run。这是我自己的操作控制错误。Task的来源/身份检查不消费完整前缀结果；原监督器内部守卫最终再次拒绝，所以本次没有创建Game。更多绿色标签不能弥补这个连接缺口。

5. **额外门槛造成误拒和冷重启成本。** 用户正常切换到其他应用，不应被旧HWND相等或20秒窗口静止条件阻止。预算核对和Steam新鲜度仍是必要约束；执行者将已授权链条拆成过多人工步骤，会消耗有效期和恢复时间。当前A28–31停止点没有容量不足的证据。原feeder具备同进程续批能力，反复冷重建不应成为普通游玩的常态。

以上共性是对多次错误的归纳；不能据此宣称旧Native停滞已经找到唯一根因。低CPU、遮挡和分辨率均不是现有证据证明的根因。

### 本轮已经落地、仍不启动的改正

- placement只加入运行树根N，统一使用from tools import ck3_live_run_id，移除N/tools全局暴露；不加模块别名、不修改旧N31、不放松来源SHA。
- 公开startup consumer probe在boot.api前执行原监督器的placement → keeper → canonical.tools/custody导入段；该段失败，公开prepare不能发布Prepared。原六消费者operation合同不变。
- Root现有操作helper增加单一顺序执行函数：完整prefix → register → inspect → run，各步subprocess.run(check=True)，并检查prefix实际布尔成功事实。非零、超时、缺字段、错误类型均停止；用户暂停期间该函数只经fake runner测试，没有调用真实Task。
- Root实际执行20项窗口/生成代码/接线回归及原有9项cold合同回归，合计29项、0skip通过。另以两个fresh BASE -I -B -S进程验证：N31原字节导入链必失败，仅最小placement变更的RAM读取覆层通过；没有别名、缓存清理或运行树写入。该资格仅涵盖原导入段，**不是完整pre-ADMITTED或新冻结运行树通过**。
- 新Root helper的7个离线分支与函数strict/equality通过。最终十一叶strict/equality检查通过；首次检查发现sys._base_executable无公开类型声明，已用运行时object校验收紧后另记成功回执，原失败保留。未用Any、cast或ignore压错。

### 未完成与下一步边界

修复后的真实CAP仍未验证：A29–31没有再到SDK，旧CI通过不能代替它。Source32新clock配置尚无新FULL吞吐实测；旧10565原生停滞、M6自然terminal到后续消费、M7广度和正常Game退出仍未闭合。灰色面板富化已有早前实机展示，本轮导入修复没有新增决策能力验收信用。

1秒/日目标未完成。A20有完整墙钟的12批为488.0427秒/186日＝2.62388555秒/日；13批总推进193日，但最后一批缺完整FULL墙钟，不能混用分母。原整场墙钟起点2026-10-19T03:26:49.420926Z不重置；截至本次复盘已超过59小时，本场整体1秒/日已不可能，后续只能另外报告局部实测优化。

当前只完成离线诊断、必要窄修和可审查记录。后续首先整合这些修复并审清完整启动入口，停止逐场追加临时例外；用户明确改变停启指令前，不进行下一次CK3启动。恢复后也须从实际新运行树重做完整前置链，再分别读回SEM/CAP、首FULL与后续推进，不能预记成功。

### 本轮精确小型证据

下列均属上述机器；Q31为O/current-saved-a31-runtime-prep01，O完整路径与本文R相同父目录。

| Q31内文件 | 字节 | SHA-256 |
| --- | ---: | --- |
| ROOT-A31-PRE-ADMITTED-FAILED-CLOSED-INDEX01.json | 2523 | f15a959ec71584b05b157f5957de80bea76ba1df144aede5203922ed612ec4f2 |
| ROOT-CHECKED-CHAIN-OFFLINE-QUALIFICATION01.json | 1925 | 760c078d5fa3b2bc6528109345bfcca89b7bf199ab087bb11470973b1652dc0a |
| ROOT-NAMESPACE-FINAL-SOFTWARE-QUALIFICATION01.json | 5601 | 1ecd5be9abc38b5ad790c75a93503e212686c0940f916e1627d32430219ed3f6 |
| ROOT-NAMESPACE-TYPED-COLD-REGRESSION01.json | 2675 | ba72962dc380ef9b6963b3fa2c73eac2ba3c478f85d9ce84366bf730db89d79d |
| ROOT-NAMESPACE-FINAL-STRICT11-QUALIFICATION01.json（原FAIL） | 3791 | 30d42ed796ccc807bfa331ffe0d2c26f2dc782381c91764f19a871aec982fb95 |
| ROOT-NAMESPACE-FINAL-STRICT11-QUALIFICATION02.json | 3646 | 539a895f17903217601e611be30fb263b9e22d0fb9c3e4f00bd83a10e5e0fb97 |

该索引绑定原stderr、CLOSED、Task Run ACK、screen释放和R0019终态。小型回归回执绑定实际源码摘要、测试输出和RAM覆层边界。未读取或重新散列SAVE/Driver正文，未新增影片或截图；失败原件按通用存储策略和当前问题用途复核，不因复盘无限延期。
