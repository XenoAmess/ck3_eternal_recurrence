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
