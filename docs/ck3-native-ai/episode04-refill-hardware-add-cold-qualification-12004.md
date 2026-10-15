# CK3 1.20.0.4 refill ADD 观察器：synthetic 冷夹具资格

本次补齐外置硬件断点观察器的受控冷夹具、有限退出和 debug-register 恢复资格。它没有观察 CK3；`CK3_actual_ADD_observed=false`，R06 实际业务项仍未验收。真实源码、q 的上游与 cap/clear 顺序继续由[补员应用专题](episode04-refill-application-12004.md)和[硬件 ADD 观察器合同](episode04-refill-hardware-add-observer-12004.md)约束。

## 机器、冻结输入与执行准入

- `machine_id: desktop-3fevhd2-1c74096080`；最终冷夹具实际运行和消费时间见下列 actual 文件；本记录整理时间 `2026-10-15T16:35:38.078057+00:00`。
- 外置根：`C:/ck3-war-episode04-research-20261004-a01/refill-add-cold-a03`。全部构建、原始 NDJSON、源冻结和 Defender 回执在该根；未写主树、未访问 CK3/SDK/桌面、未 attach Root 实机。主树版本 `1463bd9b4b89612d283dd45ac4ec9efbf22f048d`，整合由 Root 独占。
- 最终冻结源：`source-a05/`，`SOURCE-FREEZE.a05.actual.json`；`BUILD-START.a05.actual.json` 保存确切 argv；标准 producer 为仓库 `tools/run_native_msvc.py`，只配置并构建 `refill_cold_target`、`refill_cold_observer`，VC 环境由 producer 的既有 vcvars64 取得。
- 最终 build 为 `build-a05/`。`runs-review-a02/EXECUTION-GATE.actual.json` 在首个项目 EXE 执行前核对实际 `S-1-5-18`、`admin_token=true`、`status=verified`、完整精确路径与各 EXE SHA，重新核对源码 input pins。SYSTEM 回执为 `C:\ck3-war-episode04-research-20261004-a01\refill-add-cold-a03\build-a05\defender-exe-exclusions\20261015T163453Z-26315363\receipt.json`，文件 SHA `ba322e723dfa287eb09cdd89f43a722f46414dd7b7b863cba3c5e87441a28087`。manifest 的标准 canonical JSON digest 与原文件 digest 分别保留，没有混为一种 digest。
- 共享准入为 `C:/ck3-e04-resume-20261015-a01/continuation-a05/CAPACITY-ACCEPTED.actual-a01.json`，24 MiB 增量计入原 512 MiB；复核截止 `2026-10-16T07:45:01.597Z`，不自动延期。源码与关键小型回执拟入库；该外置包到期应按统一存储策略复核，不能无限保留各次派生构建。

| 最终项目 EXE | bytes | 实际 SHA-256 |
| --- | ---: | --- |
| `refill_cold_observer.exe` | 111616 | `b5ccd16b791bc8f3d5a9c1430fa335384573d461bf8c3ccc607be412ab5d4516` |
| `refill_cold_target.exe` | 50688 | `24ad4a34bf9b61604221b9b6a26be1c237f7ed188dec7b95b6ae9808fd8c065f` |

标准构建返回 0，保留两个 C4244 警告（受约束 ASCII machine/event 字符从 wchar 转 char）；没有把带警告构建写成无警告。所有新 EXE 路径均在已准 research 根下；早期门禁 RED 及各版冻结输入仍保留，未用新文件替换旧证据。

## 实际冷夹具设计

独立 `research/refill_add_cold_12004/CMakeLists.txt` 只有两个项目 EXE。target 的 MASM 函数执行一条原生 `add dword ptr [rax-0Ch],edx`，随后为 `mov ecx,[rax-0Ch]; cmp ecx,[rax-10h]`。观察器在这两个真实指令地址设置执行 DR0/DR1，未复制、模拟或跳过 ADD。target 在 ADD 之后原子递增独立执行计数，证明观察器完成 pair、清理并 detach 后，该条 ADD 恰执行一次。q=0 的 case 仍有实际 pre/post 两次 trap 和计数 1，不能把未改变数值当成“没有执行 ADD”。

target 提供只属于受控进程的 Regi、ArRg、Army 完整 ID、七个 0x24-byte 物理槽、两条指向同一槽的 DATA alias、mock registry storage slot 和真实 PID/createTime/TID。ASLR 后的两个指令地址由 target metadata 提供，`owned-site-bytes.actual.json` 在 attach 前有限读取实际 3+6 bytes：`0150f4`、`8b48f43b48f0`，保存地址、bytes、SHA。它们是 synthetic 地址，不能当作 CK3 RVA 或 .4 EXE 字节证据。

fixture 观察器只有 `--fixture-meta` 冷入口，并核目标完整映像 basename 必须为 `refill_cold_target.exe`、与观察器同目录；没有 production `--enable` 入口。`--machine-id` 为显式受字符约束参数，runner 从 `tools/ck3_live_run_id.py machine` 新鲜读取稳定身份后传入。真实 CK3 入口没有增加任意 RVA/函数 offset 参数，也没有关闭 .4 的精确验址。

沿用 war31 的进程 debugger 结构：目标线程实际停在 debug event 时读取 INTEGER/CONTROL/DEBUG，写回只包含 CONTROL/DEBUG；没有目标线程 C++ callback 或目标 XSTATE 写入。只武装指定 TID；默认拒绝已占用 DR/TF。保存原 DR0..3/6/7，退出前设置并读回，检查实际 ContinueDebugEvent 返回，再 DebugActiveProcessStop。超时通过独立 debugger break 取得暂停点进行清理。target 内的 auditor 线程在 attach 前、detach 后分别暂停主线程、GetThreadContext 读 DR0..3/6/7；存活 case 的六项与 TID、ok 读回完全一致。本轮初始 DR 均为空闲，未声称测试了占用 DR 的共存/恢复。

## 八个最终实际场景

最终运行器源码为 `research/refill_add_cold_12004/run_cold_fixture.py`。实际输出 `runs-review-a02/COLD-SUITE.actual.json`，每例目录有原生 stdout/stderr、不可改写 NDJSON、9B 真实读取、target 独立计数与前后 debug-register audit。

| case | retained boundary 数 | 原生 terminal reason | target 主线程 ADD 计数 |
| --- | ---: | --- | ---: |
| `normal` | 2 | `paired` | 1 |
| `zero` | 2 | `paired` | 1 |
| `wrap` | 2 | `paired` | 1 |
| `negative` | 2 | `paired` | 1 |
| `other-thread` | 2 | `paired` | 1 |
| `finite-hit` | 0 | `debug_hit_budget_exhausted` | 16 |
| `timeout` | 0 | `timeout_before_unique_pair` | 1 |
| `exit-before-add` | 0 | `process_exited_during_probe` | 正常退出，未进入 ADD |

全部 case 实际 PASS；此处 PASS 指对应预期终态及清理成立，后三例的原生 `status=red` 继续原样保留，不能解释为零补员或未发生 ADD。

- `normal`: 80 + 10 → 90；q/Regi/slot/完整 ArRg DATA/Army 双端一致。
- `zero`: 80 + 0 → 80；原 ADD 计数仍为 1。
- `wrap`: `0xffffffff + 1 → 0`；单条 DWORD 加法取模成功。这只验证指令和消费者，不声称这种输入会通过 CK3 的实际上游 cap。
- `negative`: q bits `0xffffffff`、signed q = -1，0 → `0xffffffff`。signed 数和原始 DWORD 分开保留。
- `other-thread`: worker 先实际执行一次同函数；只在选定主 TID 留存两次边界，`debug_hits=2`，主/worker 独立计数均 1。
- `finite-hit`: 选择不匹配 Regi，最大允许 4 trap，第 5 trap 以 `debug_hit_budget_exhausted` 终止，留存 0；目标随后实际执行完 16 条 ADD，证明过滤未把游戏语义吞掉。该结果只能是未见目标/预算耗尽。
- `timeout`: target 保持等待，1 秒预算后未见 pair；真实恢复、detach，再放行 target，ADD 仍执行 1 次。
- `exit-before-add`: target 在放行后正常退出，observer 消费实际 EXIT_PROCESS event 并结束；已退出进程的 after-DR 读回明确为不适用，未虚构恢复读回。

每个 native pair 还直接将实际捕获 Hit 的 post 副本分别变更 TID、q bits、物理指针、current，四项均被同一 `PairIsUnique` 拒绝，原始 NDJSON 保留 `fixture_mismatch_guard`。这里是从真实捕获构造的判定反例，不冒充发生过的目标执行失配。

## 严格消费者与已修的真实 blocker

`consume_cold_refill_add.py` 直接读取原始 NDJSON、其实际 SHA、原始 metadata/9B 读回和独立 audit，检查 PID/createTime/TID、完整 IDs、Regi+slot 与 RAX 关系、q DWORD/signed、两条 DATA alias、252B 七槽只允许 current DWORD 改变、DWORD 模和原 ADD 计数 1、真实 clean detach。最终五项原生 synthetic pair 均消费成功：`STRICT-CONSUMED.review-a02.actual.json` 与 `strict-consumed-review-a02/`。wrap 的输出明确是 `source_kind=controlled_synthetic_ADD`、`CK3_actual_ADD_observed=false`、`refill_business_qualification_granted=false`，没有把 raw net 或假 RVA 升格。

消费者另外拒绝实际 finite-hit/timeout/正常退出的无 pair 输入；三个显式派生反例（跨 TID、251B 截断七槽、把 fixture 改称 CK3）均拒绝，记录 `STRICT-CONSUMER-QUALIFICATION.actual.json`。派生 packet 位于单独负例目录，原始 native NDJSON 保持不动。

冷运行抓到候选 production 入口的真实 blocker：旧 OpenProcess 只有 `PROCESS_QUERY_LIMITED_INFORMATION | PROCESS_VM_READ | PROCESS_CREATE_THREAD`，随后调用 CheckRemoteDebuggerPresent，导致本机对受控目标返回 false/error 5，尚未 attach 就退出 2。每个最终 case 的 `debugger-presence-rights.actual.json` 对同一活目标有限对照：旧 rights 0x1012 实际 false/error5；补上 `PROCESS_QUERY_INFORMATION` 的 0x1412 实际 true/未被调试。相对补丁只补这个 query right、保留 presence 保护并补失败 error 诊断；不增加 target VM 写权限。API 返回失败应读取 GetLastError，符合 [Microsoft 的函数说明](https://learn.microsoft.com/en-us/windows/win32/api/debugapi/nf-debugapi-checkremotedebuggerpresent)。

## 可以授予与仍未授予的边界

本轮授予该 frozen synthetic clone 的双点 hardware-breakpoint 观察、CPU 原 ADD 一次、过滤及有限清理冷资格；真实 production 候选仍默认 OFF。不能由此授予 CK3 实机 attach、热循环开销、完整自然 core parent/TLS、同 native clock 因果、整个月结窗口覆盖或 R06 实际业务验收。外部 debugger 不得把 query 线程 TLS 当作 core token；没有复制 token allocator。真实 .4 的 2A98B88/2A98B8B 仍必须由已持完整 449B body 与当前明确 EXE 身份验址，当前 Root 现场不执行此 probe。

后续实施已经具体化：在 Root 另行安排的独立冷窗口，以 production 默认 OFF 源的实际 PID/createTime/TID、预绑定完整 Regi ID/物理槽和选定 DATA cohort 启用；保留既有最大 trap/耗时上限、unrelated 诊断与完整清理判据。先接受最小事实“该物理 ADD 实际发生”，自然父调用仍为 null；仅在真实 core 同线程共享 invocation context 有受一致性保护的 publication 后，才接自然父 token。普通 reinforcement toggle 的 action 仍无已验 MCP 通道，本轮没有操作开关或赋予 ACK/readback 资格。
