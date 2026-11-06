# Saved 已加载进程的显式准入与被动观察

Main250 以前仅调用 retained 路线，要求目标 writer 已有 SavedEntry。本次新 Game 在冷读准入前失败，目标 writer 仍为 preentry，因而需要调用已有的严格 preentry API。请求继续使用原七个字段，通过不同 schema 显式选择路线；不根据 marker 是否存在猜测模式。

| schema | 路线 |
| --- | --- |
| `xar.java-loaded-saved-resume-request/v1` | 原 retained prepare/open，保留原 SavedEntry 要求 |
| `xar.java-loaded-saved-preentry-request/v1` | 既有 prepareLoadedSaved/openLoadedSaved，保留双 fresh READ、actor/date 与实际 Core 准入 |
| `xar.java-loaded-saved-passive-observer-request/v1` | 真 source、preentry Core、只读 attach 与 LoadedCustody 校验后，仅接收自动通知 |

三个请求的字段均严格为 `schema`、`machineId`、`sourceRuntimeConfiguration`、`newRuntimeConfiguration`、`sourceConfirmation`、`checkpointPair`、`ownerDirectory`。原 owner descriptor、Game PID/birth、配置、Native plan/session、文件原件与 source/pair 验证保持。附着使用独立 READ 预算，原 launch deadline 不被刷新；附着的清理只关闭观察端点与只读进程句柄。

被动模式不进入 Saved open/adopt、业务循环或双 fresh READ。它只调用 `NativeGameTransport.observe(Instant)`：HELLO 后最多接收一个包，接收期限十秒，无私有动作权限。带 maximumAge 的二参 overload 可能发 fresh 查询，未用于此路线。只有 heartbeat 的情况下，一参接收器会因 snapshot 帧预算耗尽而抛出 IOException；该细节照实记录，再读取同接收器的 diagnostics。没有 heartbeat 时返回 2，不能把异常解释成 Ready 或自动重试。

输入保持既有 NativeWire 单帧 64 MiB 加四字节前缀上限。独立的归档上限是最后实际收到的 heartbeat、error、snapshot diagnostic 各 64 KiB，总计不超过 196608 字节；超额拒绝归档，不截断原包，也不把这个输出限制说成较小的接收硬上限。原 packet、SHA、长度和接收时间用于诊断，不产生 Driver frame、SavedEntry 或动作许可。

软件验证为最终 CLI 单 TU、两类首编通过；两个必要 DATA 方法在同一轮取得 2P。请求测试覆盖三条 schema、原字段拒绝、文件原包/哈希/不覆盖/帧与字节边界。内存 FIFO 测试调用真实一参接收器：HELLO 加一个 heartbeat 共两次读取，第三包保留、发送计数为零，并保留原 IO cause 身份；没有伪造实际 Owner 或 LoadedCustody。

18:52:35 UTC 的一次真实被动观察已取得 Game102152 的原 heartbeat，随后端点正常释放，keeper35300 与 Game 保留。该包报告当前 mailbox ready、paused、stamp read 成功，date_raw 为53168040；这只说明该时刻的字段，不倒推18:26通用负 ACK 的具体拒绝分支，也不代替严格 Saved 准入或性能验收。后继准入、游戏进展和保存继续按各自真实回执记录。

机器导航：`D:/ck3-state/resume91-java-delivery/ordinary-p0-20261105/loaded-saved-passive-observer96/`；实际原包与 custody：`D:/ck3-state/resume91-runtime/resume-after-user-play-20261105/m7-passive-observer96/frozen-heartbeat96/`。正式 Main250 与 qualified 源仅有 CRLF/LF 差别，原 formal 前像亦与实际前像一致；两测试源码逐字节复用，未另跑旧绿或引入支持编译。
