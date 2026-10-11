# CASE5/R54 种子基础缓存检查：实际零回收（2026-10-11）

本轮实际结果为零回收：真 admission 命令退出 0，plan 退出 1，close 退出 0；没有 apply、删除或新增容量 credit。原 plan 在首个索引目标 `state/profile/shadercache/dx11/ps_5_0/00000000004359E4.bin` 的受保护文件打开处返回 WinError 2。随后 ROOT 有界 metadata presence 原命令退出 0，确认 CASE5 `lyd-i4-natural-expiry-20261011-005` 的 3,740 个种子基础目标全 absent，present=0、cache body reads=0、deletions=0。该结果不解释这些旧文件何时或为何缺失，也不能将预计 146,942,067 字节算作本轮回收。

原始 [AGG、零事件、零 claim、闭账及命令回执](acceptance/2026-10-11-case5-r54-profile-seed-base-reclamation/INDEX.actual.json) 保留：AGG `all4_complete=false`、`actual_results=[]`，失败阶段为 plan。成熟闭账保留了值为 0 的 canonical event 与 claim marker；它们不是新的正容量 credit，本包没有生成第二个事件或 claim。CLOSED 实际 UTC 05:13:03.147887，remaining reservation=0，credit deduction=0，保守 project carry 前后均为 135,302,413,670 字节。48 MiB 预约释放只结束后续写入额度，不代表物理回收，也没有恢复额外 2 GiB 容量。

先前 constructor001 的 `Small original metadata changed` 失败及 admit001 的 `Only exact small source/plan/receipt files under B may be charged` 失败均保存原 RESULT/stderr。constructor003 只修正 line81 的路径分隔符归一化，内容 pins 未变；成功 constructor 原命令为002。workflow003 的 admission 薄修正为接受已声明 `.diff` 文件、移除未定义的冗余 AD 引用（既有 OUT 即 admission root），并把 ROOT command family 改为002；AD/serial/case/executor roots 仍001。原 final002、失败 attempt 与 source-only INDEX 不重写，实际成功由独立原命令证明。

独有文件、保留 seed、SAVE/native 与其他原件不在本次动作范围，未读取缓存正文。旧 prepared 若需原路径验真仍为 `RESTORE_REQUIRED`，不得因零回收续 TTL。原缓存 review 仍为2026-10-17T13:06:29.278808Z；本轮 raw review 为2026-11-10T05:07:32.634069Z，compact review 为2027-04-09T05:07:32.634069Z，均不构成自动续期/自动删除。

原 AD 59,985 字节、metadata measure 与来源 INDEX 仅保存外置精确 ref；永久包不复制身份大账、缓存、SAVE、PE 或输入树。闭账 known retained=81,756 字节，closing upper bound=1 MiB，fresh free=619,493,441,536 字节；free 变化不独占归因本轮。此项只记录维护失败与行政闭场，不授 CK3/C3/B4/I4 业务信用，Phase I 仍为75%估计、`NOT_GREEN`。
