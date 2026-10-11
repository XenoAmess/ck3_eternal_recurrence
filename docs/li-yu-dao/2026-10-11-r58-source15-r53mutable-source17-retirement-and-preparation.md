# R58、Source15、R53 mutable 回收与 Source17 准备

2026-10-11，ROOT 实际闭合三组清理，共删除 **19,958 个文件、954,105,512 逻辑字节**，各事件仅计入一次回收。Source17 已物化、绑定并闭账；这两类结果不授予 CK3 业务通过。Phase I 仍为 **75% 估计 / NOT_GREEN**。

| 范围 | 实际文件 | 一次逻辑回收字节 | 闭账后保守 carry |
| --- | ---: | ---: | ---: |
| R58 重复输入与 profile-base cache | 7,484 | 660,562,963 | 135,317,010,251 |
| Source15 非 host 输入 | 8,746 | 147,550,914 | 135,174,680,599 |
| R53 mutable cache | 3,728 | 145,991,635 | 135,035,600,228 |

三组原 admit、plan、apply、close 命令均实际 exit0；各 CLOSED 的未来预约均为 0。逻辑字节不能当作物理分配或独占 free 增量；小回执、恢复来源及闭账新增占用另外入账，没有把 gross 回收与恢复成本净量重复扣减。

Source15 的旧 host、O15 metadata/Git objects 与 native 来源保留，8,746 个非 host 输入标为 `RESTORE_REQUIRED`。历史工具需要原路径时，先独立准入恢复峰值，使用保留 Csr16 的同相对路径字节及 SHA 通过原 `restore-batch` 恢复缺项；之后才沿原 Source08–14 恢复配方操作。不得覆盖已有文件，本次没有执行恢复。R53 的 12 个差异文件（950,396 字节）及 unlisted 文件保留。原 review/TTL 未续期。

Source17 mixed source 为 `b12c466f6d308a745275a0d0911aededca3840e4`，继承 Csr16，只采用声明的 host 差异；原生构建来源仍为 `05717072b70d4925f10b3d523b6663d2db89d791`。实际 materialize、bind、cache-draft、cache-review 均 exit0，binding 报 `source_ready=true`，不等于新 native 构建或 live 验收。其 192MiB 预约于 08:03:42 UTC 闭账，已知 retained 160,161,385 字节另加 1MiB closing bound，最终保守 carry 为 **135,196,810,189**；未来预约及新回收 credit 均为 0。

Source17 保留三次真实失败：首次 admission 因旧 R53 credit schema 拒绝；首次 close 缺精确 carry-path 白名单；首次 close recovery 指向两个不存在的旧小目录、在输出前拒绝。后继 admission 与第二次 close recovery 实际 exit0，旧失败原件未改写。恢复源补丁及其原 INDEX 见证据映射。

发布 HEAD `4c12fce400b204361f686dd86ab056c7d4120f3a` 的 Official（38119644177）与 Linear（38119644232）均实际 SUCCESS；它们与 Source17 mixed commit 分列，不外推为 C3 或新 CASE10 实机信用。下一步仍须实际独立 2GiB 准入并沿统一公共入口运行 CASE10；本归档不预填其结果。

历史 R9/R7 大件仅为下一用途退役候选，旧 inventory 数字不是当前可回收量，没有在本轮删除。R10 原0240、R29 B3 诊断、R54 immutable seed、Csr16/17、Cbr3、O15 Git objects 与未闭账准备继续保护；旧 helper 仍 pin 的小源码/metadata 保留。

完整有限映射及原始小回执见 [INDEX.actual.json](acceptance/2026-10-11-r58-source15-r53mutable-source17/INDEX.actual.json)。仅入库 AD/CLOSED/MEASURE、compact 聚合/事件/claim、精确计划、命令 RESULT/小 stdout 与三次失败 stderr；没有复制 SAVE/cache/native/wire/PE/图像正文或大细账。raw 以 `-text` 保字节。raw review 依各原 CLOSED 为 30 天、compact 为 180 天；没有自动 GC 或 TTL 续期。

晚到事实（08:07:03 UTC）：ROOT 已实际完成 CASE10 独立 full 2GiB 准入，原命令 `B/i4-case10-admit-command-20261011-001` exit0，AD 位于 `B/i4-root-storage-admission-20261011-018/ADMISSION.actual.json`；截至该消息，prepare/allocate/public run 均未执行。此处只追加 ROOT 实际事实与路径，不新增 raw 复制或业务信用。
