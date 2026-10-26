# HolyHire 可选 command observer 的直接调用边界（1.20.0.4）

本轮审阅机器为 `xenoamess-full-tower-eb9d2c1186`；来源是既有迁移 cache，原 capture 机器身份为 `unknown`。目标 EXE SHA-256 为 `98702f88a547cde2eaf29a85f93b85f68ee4cf8148336a4f7afaeb75319dd518`。本笔记仅解释静态原件，未新增 EXE 读取、游戏调用或 loaded runtime 资格。观察时间及 exact refs 见 `D:/codex-ck3-background/ck3-java-g2-resume-r4-20261025/resume61/effect_observers/hire_timing10/OBSERVER-SOURCE-CONTRACT11.json`（2605 B，SHA-256 `7e3ae579492aaeacde789aca5c0a5685bcfebc7bc9532d0afd4a1f871106b20b`）。

## 已持原件

复用 `function-match-core/new-03808E00-03808F82.bin` 的完整 386 B（SHA-256 `260c1c6a0a725e0c1f444a146774be17e664aed114cd2ff9c3cb3a1860da4535`）及 103 条指令原件（25235 B，SHA-256 `3c2b27f098dff27e01395d47bf8f986087fa78555ad42b8237d87c476ba2ac74`）。根目录为 `Z:/ck3_mod_rewrite_process_assets/g2-background-20261007/upstream-build-migration/`。

调用方 QueueOwnedCommand 的 250 B / 79 条指令已经由 NativeRefund 的 `CANCEL-CALLER02.json` 闭合，本轮只复用其结果：可选 receiver 在队列接受判断之前被调用，随后 owned primary 通过 append 加入 manager 容器。本次不重新给该 ABI 记完成，也不把 HolyHire 已持 caller flags 转移给取消 GUI。

## 386 B 直接控制流

| RVA | 直接可见操作 |
| --- | --- |
| `03808E1E` | receiver 首字节为零时退出。 |
| `03808E30` | 对 receiver `+8` 进入间接 lock-like 调用；`03808F60` 有对应退出。 |
| `03808E3E` 起 | 比较 `+24` 的数量和 `+20` 的容量；满时通过 `+28` 对象的 virtual `+8` 取得按指针大小分配的空间并移动旧槽。 |
| `03808E98` / `03808EF5` | 两条路径都调用 concrete primary vtable `+40`，目标槽作为参数。HolyHire 已持 72 B 表将该槽绑定到 clone `2995640`。 |
| `03808F01` | 调用 concrete primary `+48`，把返回的 EAX 交给 `3F4F8E0`。此槽的目标尚未从实际数据原件取得。 |
| `03808F14..03808F58` | 阈值判断后可能调用 `3F5F970` / `8807D0`，然后退出 lock-like 区域。 |

这段直接 body 没有 secondary Execute 调用。其 virtual callbacks、分配/移动辅助函数和尾部 helper 的全部副作用仍未闭合，因此不能从“body 未直接 Execute”推出所有后代都无业务副作用，更不能把 AL=false 解释为绝无副作用。

## 对效果观察的约束

HolyHire 的实际 primary base 是 `476D9D8`。此前 72 B 表范围为 `[476D9D8,476DA20)`，仅覆盖到 `+40`；它没有覆盖 `+48`。本轮只提出 `[476DA20,476DA28)` 的 8 B DATA 请求，待 b64 唯一执行窗口批准批次后实际读取。请求路径是同目录 `SOURCE-REQUEST12-HOLY-PRIMARY48.json`（3010 B，SHA-256 `29f9adcf6e463c4ccd85058e8f7d4a17dec63c12804c46ece6323ca060f1e9a5`）；不得据地址相邻猜目标，或自动扩读未知 target body。

当前仍没有 owning queue consumer/drain 相对查询 mailbox 的实际调度证明。`pump_epoch` 只能说明已持查询路径的 pump 事实，不能授予 manager `2A88610` 已执行、付款、到场或雇佣完整生效的信用。普通 HolyHire 已有 after-read 路径也不补齐 reconciliation 的 origin/read-contract/caller 三个缺口。保持 UNKNOWN 原请求不重放。

结构化研究计划和自动图分别为同目录 `research-plan11.json` 与本文件同 stem 的 `.graph.md`。工具检查只证明计划结构、文件引用和 hash 一致，语义与实机验证均未完成。
