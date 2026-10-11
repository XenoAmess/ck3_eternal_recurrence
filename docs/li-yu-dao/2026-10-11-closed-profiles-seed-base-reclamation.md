# 三份已闭场 profile 的种子基础 shadercache 回收（2026-10-11）

ROOT 原始 admission、plan、apply、close 命令均实际退出 0；12 批共删除 11,220 个种子基础缓存副本、440,826,201 逻辑字节。范围仅 CASE6/CASE7/CASE8 的 `state/profile/shadercache` 中已声明与保留种子一致的基础文件，每组 3,740 文件、146,942,067 字节。原始结果见 [证据索引](acceptance/2026-10-11-closed-profiles-seed-base-reclamation/INDEX.actual.json)。

CASE6/CASE7 为 `lyd-i4-natural-expiry-20261011-006/007`，CASE8 为 `lyd-i4-natural-event-context-20261011-008`。独有文件与保留 seed 不在删除范围；旧 prepared 如需重验，应先按原索引恢复，状态为 `RESTORE_REQUIRED`。未延长旧输入、缓存或配额 TTL，未新增自动删除。保留 seed manifest SHA-256 为 `a1fab6e0e92e4a8ea394d6e85e365f5c6be619e87d4f2c16b7ed9d2623cebe06`。

apply 实际 UTC 04:23:31.477 至 04:26:48.179；close 为 04:27:24.384 至 04:27:25.099。48 MiB 预约已闭合，future reservation 为 0。唯一事件 `lyd-closed-profiles-seed-base-20261011-001` 只 claim 一次，440,826,201 字节 credit 没有重复扣旧事件；保守 project carry 为 135,138,642,911 字节。

闭账记录新增保留量 17,024,573 字节，加 1 MiB closing upper bound；闭账 fresh free 为 619,688,644,608 字节。上述删除量是逻辑字节，不代表独占物理回收量；并发 free 差额不归因本次动作。原 AD、测量及 12 份详细删除账保留外置精确引用，永久包只收 compact AGG/EVENT/CLAIM/CLOSED 与四份原 ROOT command RESULT，不复制 cache、SAVE、PE 或明细 ledger。

此包只记录实际存储维护，不改变 Source16 冻结、不改变 R57 永久包，不授予 CK3/C3/B4/I4 业务验收。Phase I 仍为 75% 估计、`NOT_GREEN`。

本轮 raw ledger review 为 2026-11-10T04:22:00.227019Z，compact review 为 2027-04-09T04:22:00.227019Z；原缓存期限仍为 2026-10-17T13:06:29.278808Z。review 日期不构成自动续期或自动删除。
