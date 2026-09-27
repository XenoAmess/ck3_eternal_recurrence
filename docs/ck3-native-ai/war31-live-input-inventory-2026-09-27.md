# WAR31 独立双点实机尝试：输入盘点（2026-09-27）

本盘点是对 [R0221 请求](../autonomous-agent-progress/coordination/war-requests/requests/WAR-INPUT-R0221-WAR31-20260927.json)、
[R0197 冻结清单](../autonomous-agent-progress/coordination/war-requests/evidence/WAR-INPUT-R0221-WAR31-20260927.r0197-raw-freeze.json)
与 [R0221 只读回执](../autonomous-agent-progress/coordination/war-requests/evidence/WAR-INPUT-R0221-WAR31-20260927.r0221-raw-freeze.json)
的离线复核。只读取磁盘文件；没有访问桌面或 CK3 进程，没有发起投降。
新采样器及门禁见 [双点实验方案](war31-two-point-hardware-probe-2026-09-27.md)。

| 输入 | 原始冻结身份 / 本机实测 | 状态 |
| --- | --- | --- |
| CK3 1.19.0.6 `ck3.exe` | 本机 95,206,008 B；SHA-256 `2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86`，与 R0221 一致 | 可用的静态文件；新 attempt 仍需重新核进程实例 |
| 生产硬件采样器 | 本机 83,456 B；SHA-256 `5045765D3671D067C18A21F1F03EE0D72EC6EC8481D9882F9DCDB964FE8A04EB` | 离线可用；没有用于 CK3 |
| R0197 checkpoint，history index 2134/date_raw 53215920 | 冻结 77,478,199 B；期望 SHA-256 `1AF4055F978AF60267FB3A0D8658224047CD6BFDA884C66886A13B74EE34A90A` | **本机无原始字节，不能复算** |
| R0197 `driver-state.json` | 冻结 16,681,512 B；期望 SHA-256 `1DE61CF0AC47EDD1D63FE1F3D77668D5F499EA6CA06B90BC83B068CF35F16336` | **本机无原始字节，不能复算** |
| R0221 bridge DLL | 请求记录期望 SHA-256 `C36ECCEB67A0DCA7C8C1C6C855A5036771B46617E9F1BF5F4185D965C1951BCE` | **本机未找到匹配原 DLL**；现存 3 个旧构建候选的 SHA 分别为 `10E4B41DBB4ABB59F8B624F90A1A083FF9B4750FF9FE87065BB15FD39CD7A011`、`2EB6E3265459CA3B2773D1A80E377A10F159592DAAEC77AC97C6E0CDB02807DC`、`973B9EB1A4BAA926811CD06237A8B8173CC4459C7F9140221AFD45242E537095`，均不同 |
| R0197 环境/重绑 sidecars | 冻结清单另列 `xar-autoplayer-environment.json` SHA `061F7190B65AD145711FAB7EA476090F1CB6B61A6519793AC33E074BCA6103CC`、`ordinary-seed-rebind-v1.json` SHA `4D8264C47AB8C749C85BDABE75DA996104FC85E2200B3B420DEA3257E464A057` | **本机无原始字节**；这些历史身份不证明两份文件已涵盖全部 replay sidecars |
| R0221 Git 只读回执 | 本机 `r0221-raw-freeze.json` 8,383 B；SHA `BE7CCFF4DED6305744D3C2EE0ADD7FFD8D9163E0B662F02C3986090271DC30C5`，与请求一致 | 仅身份/查询证据，不能替代存档、driver 或动作回执 |
| 新 attempt 单次动作授权回执 | R0221 回执明确 `typed_termination_authorized=false`，请求范围明确“不授权投降” | **缺失**；先前广义研究/游玩指令不能改写这个具体禁令，不能自行制造 `authorized` 回执 |
| 新 attempt PID/创建时间、帧/effect 调用、动作前后状态 | 只能由未来独立受管执行生成 | **尚不存在**；不能复用已完成 104/106 的身份 |

原始 `Z:\ck3_mod_rewrite_process_assets\...` 是另一台机器的历史来源路径；
本机没有 `Z:` 盘。离线扫描了本机 `D:/ar/artifacts`、主工作区
`artifacts`/`research`、用户 Downloads、上传目录、Temp、Saved Games
及 `D:/Users`：没有找到同名 `xar_checkpoint.ck3`、`driver-state.json`、
`sidecar.json`，也没有找到文件名指向 R0197/R0221/WAR31 的候选资产。
扫描索引保存在外置
`D:/ck3-research-artifacts/war31-hwprobe-20260927/saved-input-inventory.json`；
哈希回执保存在同目录 `saved-input-candidate-hashes.json`。这只是列出的
本机目录范围，不声称遍历所有盘和云端文件。根据项目 OneDrive 下载
限制，本次没有访问 OneDrive 同步目录或触发任何云端下载。

因此目前**不能组装合法 live manifest，更不能附加 CK3**。下一次
独立尝试至少需要：经单独传输并按冻结 SHA 重验的 checkpoint、driver、
运行所需全部 sidecars 与对应 DLL；新 attempt 中的真实 PID/创建时间
和帧/effect 身份；对 `surrender-war-16777231` 的真实、独立单次授权
来源和回执；以及动作前后原生状态、清理和恢复证据。当前驱动只绑定
一份显式 `sidecar` 文件；完整 replay 所需的其他 sidecars 必须由受管
执行者另行列清并 hash 绑定，不能因该单字段通过就宣称输入完备。
