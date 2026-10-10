# 2026-10-10 闭场 profile 可再生缓存回收续记

本记录接续 R42–R48 的原回收记录，只记本轮 R49/R50/R51 和八个更早已闭场 profile 的实际操作，不重复计入已回收的 R42–R48。所有操作均在外置 `C:/workspace/disk-cleanup-20261010/resume-05/`，MAIN、运行时、native 二进制与准备输入未修改。

删除目标逐一从原 `launch.json` 的实际 `--state-dir` 定位并锁定为该 profile 的绝对 `shadercache` 路径。新场要求原 `POST-RUN-CLOSE-05.json` 为 `CLOSED`、三项 closure 均为 true、keeper/allocator actual exit 0、原 CAS `done/resources=[]`；八个旧场分别核对原 CAS 与 keeper actual exit 0，并证明原 harness 已退出、没有活进程引用目标 profile/state。每场都证明缓存不在原 frozen preparation 文件清单与 before-launch profile snapshot 中。

仅删除原实际 launch 至 closed 时间窗口内、`dx11/ps_5_0` 或 `dx11/vs_5_0` 下十六位十六进制同名 `.bin` / `.scache` 对。每文件用独占原生 HANDLE 核单链接、长度、实际 `FILE_STANDARD_INFO.AllocationSize`，读取一次 SHA-256，写入 append-only journal，再删除同一 HANDLE 指向的文件并确认缺失。原 frozen preparation、launch、keeper、CAS，以及新场 prepared-case 的精确原 pin 在操作后保持；原始日志、截图、失败 attempt、存档、配置、fixture、staging、源码与构建输入全部保留。

| 范围 | 文件数 | 删除逻辑字节 | 删除实际 AllocationSize 字节 | 卷 free 前 → 后（字节） | 该窗口 free 净差 |
| --- | ---: | ---: | ---: | --- | ---: |
| R49 / a149 | 3,780 | 149,499,275 | 157,999,920 | 2,268,213,248 → 2,429,386,752 | 161,173,504 |
| R50 / a150 | 3,824 | 152,606,529 | 161,198,896 | 1,800,658,944 → 1,955,725,312 | 155,066,368 |
| R51 / a151 | 3,812 | 151,692,924 | 160,282,832 | 1,304,088,576 → 1,462,607,872 | 158,519,296 |
| 旧 R33/34/36/37/38/39/40/41 | 30,300 | 1,200,636,644 | 1,268,730,240 | 1,446,846,464 → 2,707,333,120 | 1,260,486,656 |

本轮合计删除 **41,716** 个可再生缓存文件，逻辑长度合计 **1,654,435,372 B**，实际文件分配合计 **1,748,211,888 B**。所有删除失败为 0，11 个目标缓存目录全部不存在。逻辑长度不作为空间回收量；各操作窗口的卷 free 净差独立保留，不把并发写入、journal 或目录元数据变化归因于缓存回收，也不把这些非连续窗口拼成一次净增。最后八目录操作结束时卷 free 为 **2,707,333,120 B**。

以下正式回执回链原资格证明和逐文件 journal；字符为完整 SHA-256：

- R49 / a149：[正式删除回执](C:/workspace/disk-cleanup-20261010/resume-05/a149-shadercache-deleted-03.json)，1680 B，`3ee52251f55efa5f5b0226f62a03a872adf7e00e26486ce2a7203cccfa019f1b`。
- R50 / a150：[正式删除回执](C:/workspace/disk-cleanup-20261010/resume-05/a150-shadercache-deleted-03.json)，1713 B，`7ed4660c3ccd287c771c08014713d56ece4767541fe0d287bd22fd73b5976ed7`。
- R51 / a151：[正式删除回执](C:/workspace/disk-cleanup-20261010/resume-05/a151-shadercache-deleted-03.json)，1755 B，`19c27570fe20e75e62bc9d30a0d7301f28b7444a033bd82f9927231e52abe87a`。
- 旧 R33/34/36/37/38/39/40/41：[正式删除回执](C:/workspace/disk-cleanup-20261010/resume-05/old-eight-shadercache-deleted-09.json)，6813 B，`f3408c450f3f1e8ce99aa9dc8902505de4699fc721dbf37d5cdd1de85e31db53`。

**R35 未清理**：本轮已知路径缺少原 CAS 回执，因此保留其全部约 157,999,920 B 实际分配的 shadercache；没有用邻场或 keeper exit 代替该场 CAS。

另对已闭 R47/R48/R49/R50/R51 的大 `.raw/.json/.jsonl/.log/.txt` 输出执行一次有界无损 NTFS 压缩：10 个文件、逻辑长度 10,499,210 B，逐文件同一独占 HANDLE 前后验证 bytes/SHA-256/mtime 不变，实际 AllocationSize 节省 **7,614,464 B**，失败 0；36 个已带 `FILE_ATTRIBUTE_COMPRESSED` 的大输出直接跳过，没有重复 hash 或压缩。该节省量与上表缓存删除量分列，未删除任何证据。

- a147：[压缩回执](C:/workspace/disk-cleanup-20261010/resume-05/a147-closed-text-compression-05.json)，1394 B，`4b1ed6de53a44f00673c59bd4691767c114b6d7d78fa8dddaf9974de63bd8a42`；实际分配节省 1,470,464 B。
- a148：[压缩回执](C:/workspace/disk-cleanup-20261010/resume-05/a148-closed-text-compression-05.json)，1395 B，`0a32c541c5befa52631ff652a3c2786dadbca97eb817449a8fedaf044170b3f2`；实际分配节省 2,023,424 B。
- a149：[压缩回执](C:/workspace/disk-cleanup-20261010/resume-05/a149-closed-text-compression-05.json)，1394 B，`a83b0cc8f2d425eaea35c5722e82b4b6d3ee9456f576ecf3b52e61548d4a8184`；实际分配节省 1,429,504 B。
- a150：[压缩回执](C:/workspace/disk-cleanup-20261010/resume-05/a150-closed-text-compression-05.json)，1395 B，`1f104e13ed50bc401e9c3300b4d1b1a2ec61b0786c6911ec05373606766bd9cf`；实际分配节省 1,282,048 B。
- a151：[压缩回执](C:/workspace/disk-cleanup-20261010/resume-05/a151-closed-text-compression-05.json)，1394 B，`8f1e84b3a91cdc8825e4cbad7f0a86ab2a968876c2de0d0e46500e18b4a4143e`；实际分配节省 1,409,024 B。

分页文件仅做文件逻辑元数据只读采样：仍为 5,736,935,424 B，mtime 仍为 `2026-10-09T18:15:23.952797+00:00`，与原采样一致；没有取得或声称其 actual AllocationSize、没有读取或修改系统分页设置。[采样回执](C:/workspace/disk-cleanup-20261010/resume-05/PAGEFILE-LOGICAL-SIZE-MTIME-READONLY-06.json)，1194 B，`f8da632c03ca7769bdacb91f4cbb9b6760b041d77532dd65b25b99cb74043438`。

后台操作只降低自身 CPU/IO 优先级。新场 active profile 始终明确排除；Root 接回 MAIN 的空场窗口才处理八个旧目录。后续仍须逐场满足真实闭场、原输入排除与生成来源证明，不能把本次资格自动外推到新目录。
