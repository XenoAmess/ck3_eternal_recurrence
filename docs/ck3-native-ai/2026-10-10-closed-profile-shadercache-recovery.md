## R42–R48 闭场 profile 增长定位与可再生缓存回收（2026-10-10）

本轮针对已闭场 R42–R48 的原 launch 指向的 profile、原 keeper 输出及 C04live 目录做有界只读统计，没有全盘扫描。七场的原 CAS 分别为 7968、7978、8000、8043、8055、8064、8072，均实际 `done/resources=[]`，原 keeper actual exit 均为 0。每场独立 profile 都在实际启动后生成约 150 MB 的 DX11 shader cache；使用原生只读 HANDLE 的 `FILE_STANDARD_INFO.AllocationSize` 核得每场约 158 MB，七场合计 1,107,281,488 B。这解释了 headline `native-report.json` 之外的一项持续增长来源。完整 native/MCP sidecar、UI 原始截图及 keeper 输出也占空间，清理后保留的已知文件分配合计 780,122,136 B。

缓存回收前逐场证明：`shadercache` 不在原 frozen profile-preparation / preparation 的 files 清单，也不存在于原 before-launch `input-snapshots/profile`；26,480 个文件全部为 `dx11/ps_5_0` 或 `dx11/vs_5_0` 下的十六位十六进制同名 `.bin` / `.scache` 对，mtime 均处于对应实际 launch 与 closed 窗口之间。只对这七个绝对目录白名单内的缓存执行删除，逐文件持独占原生 HANDLE，保存 SHA-256、逻辑长度、实际 AllocationSize、mtime 和生成来源后删除；没有删除存档、原片、截图、原始日志、失败 evidence、配置、输入、fixture、staging、源码或 native 构建文件。原 frozen preparation、launch、keeper/CAS 的精确指纹在回收后保持，删除失败为 0。

动作窗口磁盘可用从 1,653,170,176 B 增至 2,753,011,712 B，实际净增 1,099,841,536 B；删除逻辑量为 1,047,746,214 B，逐文件实际 AllocationSize 合计为 1,107,281,488 B。这三个量分别保留，没有把日志写入、目录元数据或并发变化归因于缓存回收。[正式删除回执](C:/workspace/disk-cleanup-20261010/closed-r42-r48-generated-shadercache-deletion-09.json)为 6192 B、SHA-256 `6a4f2248e8900c78c1df8befb9770de0eb87ef48fa5cc77d1f094e7be983cfcf`，回链逐文件 journal 与原输入排除证据。[有界增长与回收汇总](C:/workspace/disk-cleanup-20261010/ROOT-CLOSED-PROFILE-GROWTH-AND-RECOVERY-10.json)为 36160 B、SHA-256 `a4234e995da99ba9e2fca06383d867f17b0823a340ff1368f4fb4273a346fb75`。

分页文件 logical size 仍为 5,736,935,424 B，mtime 仍为 2026-10-09 18:15:23.952797 UTC，与早先采样一致；两种原生只读 metadata HANDLE 打开方式均被系统以 WinError32 拒绝，因此没有伪称取得分页文件实际 AllocationSize，也没有变更分页设置。当前有界统计重建七场已知文件分配约 1.887 GB，每场约 250–287 MB；不能据此把任意两个磁盘可用采样之间的全部 0.4–0.5 GB 降幅都归因于这些目录，授权范围外的并发变化仍未归因。

后续统一闭场可以接入相同的可再生缓存回收步骤：必须先满足当场实际进程与 native cleanup 完成、keeper actual exit 0、CAS `done/resources=[]`，然后逐场证明目标不在 frozen inputs / before-launch snapshots，保存缓存清单及来源再清除。该步骤只限制已闭场 shader cache 的累计占用，不减少业务验收，也不改写原失败 attempt。当前仅建议接入，未声称公共入口已实现此自动步骤。
