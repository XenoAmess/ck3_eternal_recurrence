# SAVE491 的原生提交合同与完成边界

2026-10-31，machine_id `xenoamess-full-tower-eb9d2c1186`。这份只读研究使用 SAVE491 的不可变报文、当前仓库源码及已持历史原生原件。没有操作 Game、DLL、Runtime、账本或再次 SAVE，没有动态执行原生代码。

实际 270B 响应只承诺提交：同一 request_id 的 `ok=true`、`accepted=true`、`status=submitted`，附 `sequence=1`、`requested_save_name=xar_checkpoint`、`date_raw=53144520`。原件 SHA256 为 `6bf8eea83607edaea1fa06ffb9277a145044a2aa130ac8ba0eb4a84276ae859e`，4B 小端长度为 266；147B 请求原件也已核 SHA 和 framing。ACK 于 `16:21:30.088998300Z` 收到。运行岗另外报告文件 mtime `16:21:31.521325100Z`、68,690,729B、saved pair 仍为 0；这里没有重读大文件。这些时间和大小不证明写入者、完成时点、可加载性、持久化或 loaded DLL 对应关系。

当前源码的具体分支是：`CreateCk3_12004Adapter` → actual4 bindings/descriptor → 共享 concrete adapter → `SubmitSaveCheckpoint` → `SubmitCommandCopy` → queue bool。actual4 binder 在非零 image base 和正确 executable SHA 下使用 manager `5CC1240`、queue `37F06D0`、AutoSave 主/次 vptr `44B5158/44B51F0`；默认 12002 头里的 `37F06F0` 不是此分支选择的地址。这个仓库静态分支不等于已加载 DLL 的源码身份。

| 字段或步骤 | 当前源码可证明的合同 | 不增加的信用 |
| --- | --- | --- |
| 保存结构 | 64B 栈对象、flags `0x20`、绑定 vptr、内联 14B `xar_checkpoint`；从 primary+`0x40` 调 native clone | 不证明实际491的内存对象或 ABI |
| queue raw flags `7` | bit3=0，跳过 queue 的 OR20h；bit0=1，绕过本地拒绝块；bit2=1，在 `880340` 两侧选两次间接调用。正常返回的接受路径移走 owned pointer、清 caller holder、AL=1 | 不证明 queue drain、typed Execute、保存完成；不猜 opaque callee 的所有效果 |
| wrapper 返回 | 尝试清理残留 holder，忽略 cleanup bool；queue bool true 映射 `submitted` | 不是文件完成或持久化返回值 |
| `sequence` | WorkerState 本地计数；对象在连接循环前创建，可跨连接复用；在写 ACK 前递增 | 不是完成数、成功 ACK 数或持久历史 |
| `date_raw` | 提交前 CoreSnapshot 的日期 | 不是文件日期或完成后态 |
| 保存名 | ACK 使用 adapter descriptor；命令使用另外的固定内联字符串 | ACK 不独立检查 clone 内存或最终路径 |
| ACK 与 snapshot | 更新本地提交元数据 → 尝试写 ACK → 写成功才调用 PublishSnapshot；后者仍可能无 frame 或写失败 | ACK 不保证后续独立 state frame |
| `last_checkpoint_submission` | 从同一本地提交元数据序列化 `submitted` | 重复发布它不构成引擎完成观察 |

接口没有暴露一个可确定与 ACK 先后关系的保存完成事件。opaque callee 内同步完成、返回后继续工作，以及观察前缀里尚无完成，都与该接口兼容；这里不把其中任一项写成 SAVE491 的实际历史。提交后 ACK 写失败也可能发生，因此缺 ACK 本身不授重放许可。

历史 engine 原件的 12 条证明已封在 `engine-proof/ENGINE-PROOF182.json` 与 `ENGINE-CLAIMS182.md`（13 个完整代码窗，共 5,173B）。正常 writer 的 `384EFE6` 调用 public close 后不检查 EAX；若后继 opaque 调用普通返回，仍可到 `384F113` 写 T.tag0。`384EF19` 是另外的错误结果 cleanup。matched close 中，I+18 正值先清两个 cursor，随后 I+40=0 可保留 node，却不回滚已清的 cursor。只有实际采用所持历史 kind1 模板时，I+40/I+48 才分别对应已证的 FlushFileBuffers gate/CloseHandle destroy；当前491模板和 API 结果未知。历史 receiver `22966B0` 只移动、清理结果字符串，没有直接 R.tag store；dispatcher 的 fresh tag0/1 析构后写2也不是持久化确认。其版本、实例、backend/receiver 与当前命令的接线仍分别保留，不能从旧原件或函数名称补出当前链。

当前具体缺口是自然 queue consumer 与 AutoSave 的 typed Execute 槽、该执行边到具体 SaveWriter/backend/callback 的版本接线、实际491实例的完成观察，以及 loaded DLL 到源码的闭包。已持静态 vtable 的有序候选指针不是 Execute 槽身份。故本研究止于这些边界，没有新 provider、全 PE 扫描或猜测 endpoint。

证据根为 `D:/ck3-state/resume91-m7-native/save491-ack-contract182`：总合同 `SAVE491-NATIVE-CONTRACT182.json`，报文 `actual491/MANIFEST.json`，当前源码与顺序 `wire-proof/DELIVERY182.json`，actual4/queue 证明 `selected-binding/OWNER-PROOF182.json`、factory 补源 `FACTORY-SUPPLEMENT182.json`。各模型原始输入没有被后补源回写。

六个不同证明主题各两轮语义请求，共 12 个逻辑调用、14 次真实 POST：10 stop、2 length、2 半流 reset；本组实际在途峰 3。reported usage 为 144057 prompt + 27297 completion，cached null。没有原样整份证明采用；可核的小部分分析保留，完整错误、截断及半流拒收，owner 的逐指令修正独立记录。尤其完整 79 条队列指令已提供，两轮仍读错位与 JNE 的回答已停止纠正并接管；遗漏 DestroyOwnedCommand 定义和 WorkerState 外层生命周期属于输入覆盖补正，未算模型未获事实的能力失败。没有编译、测试或实机完成信用。
