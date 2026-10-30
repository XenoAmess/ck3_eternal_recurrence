# M6 NOT mode4 的实际本地合同

machine_id: `xenoamess-full-tower-eb9d2c1186`。Owner `/root/m6_native91`。本次只复用已持 `.4` 原件，两个模型候选实际审阅失败后由 owner 接管，并由 `effect91` 独立复核 Env/支持函数部分。没有新增 PE、provider、编解码、测试或 Game 操作；不授自然终态、原因、收益或游戏日。

原件根为 `D:/ck3-state/resume90-m6-native/event-domain/alternative-terminal-source/current4-callers01/valid-member01`。完整 caller 是 `DECODE-not-evaluator-3785990/stdout.txt`，完整1181B body是 `DECODE-not-mode4-378D810/stdout.txt`，完整111B helper是 `DECODE-not-mode4-helper-3785B10/stdout.txt`；`MODE4-SUPPORT-BATCH01.json` 索引734B支持函数及各段 stdout。详细最终合同为 `D:/ck3-state/resume91-m6-native/mode4/SOURCE-RESULT01.md`，独立复核为 `effect/MODE4-SUPPORT-REVIEW01.md`。

令 T 为 caller 原 RCX，A 为原 RDX，P=T+0x40，Q=T+0x88。`37859C4/37859C9` 分别把 P/Q 存到两个不同 stack holder；`37859DF` 的真三参为 RCX=A、RDX=&holder(P)、R8=&holder(Q)，对应 `37859D7/37859DA/37859D2`。这两个 holder 地址不能与 vector header 或 element storage 混为一层。callee 保存为 RDI/RBX/R15。

caller 的 mode BYTE[A+0x20] 与 TLS DWORD 是不同输入。后者由 `QWORD[GS:0x58]` 取 TLS array，再取其第一 QWORD 指向的 base，读 DWORD[base+0x144]（`378D84C..85E`）。当前加载值、正式 enum 名称与线程角色均未观测。

`3785B10` 先从 holder 取得 vector header，再读 data/count，按8B child遍历并调用 `372E000(child,A,0)`。首个 child AL 非零立即返回 AL0；空或全部 AL0 返回 AL1（`3785B40..B7E`）。这是短路 NOR。该 fold 不保证 child 无副作用或正常返回。

| TLS DWORD 入口 | 实际正常返回行为 |
| --- | --- |
| 1 | `378DC5C..DC67` 对 P-helper 求值并转发 AL，无快照/恢复。 |
| 2 | `378DC6E..DC79` 对 Q-helper 求值并转发 AL，无快照/恢复。 |
| 其它非零 | `378DC7B` 只清 AL，不是完整 EAX 清零。 |
| 0 | 首次 P 的 AL 保存在 R13B；最后 `378DC51` MOVZX EAX,R13B，Q与重算结果均不替换它。 |

TLS0 的顺序为：取当时 E=QWORD[A+0x18] 保存 S0；设 TLS1并对P求值；再次取E保存第一次求值后的 S1；再次取E，把 S0 的第一vector、第二vector和+3D0 tail赋给当前E；设TLS2并对Q求值；再次取E保存第二次求值后的 S2；清TLS0；计量、写全局计数并比较两次保存的AL。

两次AL相等时，`378DA7F` 直接进入快照清理，**没有最终S0恢复**。不等时可走诊断，再在 `378DADD..DB05` 重新读取E并赋S0的同三部分，保持TLS0重算Q（`378DB1B`）；该次AL被丢弃，之后也没有再恢复。S1/S2仅用于后续清理，不比较其内容，也不作恢复源。最终返回的始终是第一次P的保存字节。

父函数没有把入口E指针写回 A+0x18；每次复制/恢复都重新加载它。如果委托调用更换该指针，恢复针对重新加载到的E。静态原件不声称这种更换实际发生。即使指针稳定，相等结果路径也留下post-Q Env，不等路径留下post-recomputed-Q Env，不能称作统一回滚。

支持函数的可见边界是：`3735AE0` 采集32B cell vector、80B cell secondary vector与+3D0 QWORD；`1D877C0` 处理首vector自赋值、count/capacity、可能allocator分配/释放及32B cell复制；`3735DF0` 处理第二vector自赋值、构造/销毁/赋值及每cell byte+0x48显式复制。未展开的复制构造、赋值和allocator子调用，不授深拷贝全部可达对象、恢复原buffer/capacity位表示或回滚外部状态。清理调用不等于普遍成功释放或异常安全。父体另有真实INC/LOCK XADD全局写入（`378DA23/DA2C/DA4B/DA5D/DA6F`），不应被“观察比较”措辞抹去。

共同child core `372E000` 的1070B完整原件已由M4/M2持有：`D:/ck3-state/ck3-java-g2-rea-eval-resume62/tools01/cases/resume63-m2-classifier372e000-01/raw/new-0372E000-0372E42E.bin`。复用M4 `compiled-effect/condition-entry/SOURCE-RESULT01.json` 与 `chain-execution/MODE4-CALLER-SCOPE30.json` 即可连接 descriptor/scope gates、virtual+C8、`372E353` 保存AL及 `372E404` MOVZX最终返回；不另扫PE。实际loaded receiver/children、scope值、子谓词外部效果以及 Sway 的自然 terminal/cause/material 仍是不同输入。

模型原件位于 `D:/ck3-state/model-dispatch91/m6-mode4-support` 和 `m6-mode4-support-correct02`。首轮HTTP200/stop，TTFT23.879s/总122.795s，23372+2723tokens；第二轮同11-source前缀加精确纠错，HTTP200/stop，TTFT2.031s/总64.149s，23456+2202tokens。首轮错ABI且遗漏完整body/support，第二轮仍反写NOR/空true，并把Env支持函数误称TLS修改。两轮均拒绝，详细 `mode4/REVIEW01.json`、`REVIEW02.json`。cached tokens未报告，不由延迟变化推缓存命中；这两次具体任务失败不是模型通用能力上限。
