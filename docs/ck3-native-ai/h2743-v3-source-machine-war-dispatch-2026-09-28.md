# H2743 v3 来源机并行只读协作派发

2026-09-28 11:36–11:37 UTC，战争机在固定 OneDrive 相对目录 `WAR/H2743-EXIT-READONLY-V3-20260928/` 新增 H2743 只读协作请求。此为**发送端目录与字节事实**，未证明云端完成同步、来源机领取、来源机屏幕可用或实机成功。Git `master` 的 H2743 request/response/verification 仍是状态权威；本记录和 WAR 来件不会把它改为 delivered/passed。

| 新文件 | 字节 | SHA-256 | 作用 |
| --- | ---: | --- | --- |
| `REQUEST.json` | 4,720 | `2E53D0AD878EE59983104ADBC2613E6975E815552B646E7F787E868DBDC13475` | 准确帧、只读步骤、无日期／动作、清理后回执要求 |
| `TRANSFER-MANIFEST.json` | 2,220 | `6B33C63819C8E41365478AAF33490C065D5553FB299B1FB1089665989CEC6895` | 两件候选传输物及来源机四件原件的 SHA/大小 |
| `RECEIVER-ACK-CONTRACT.md` | 1,953 | `77609BE6466BBE1EB41BDF6A89636B9EEA975BF1845BEFA91B8F486FE1DAAE78` | 本机核验、可用／阻塞和 append-only 回复格式 |
| `xar_ck3_bridge.dll` | 3,137,024 | `FD8B5C7873C22BE32ACF2E421D2A9F625AE8FF3FB4D5408DB7F6E6AF15321470` | #448 H2743 V1 只读候选，区别于原件 DLL `8C3A…8A5C` |
| `xar_ck3_bridge_injector.exe` | 39,936 | `C89F1A919514A7E664AEE8FAF165B78C693ABA4EA2105289BDA2DB4BAC6A84FF` | 精确 injector |

目录只有上述五文件；两份 JSON 已解析。仅两件候选二进制从外置本机冻结源以 `xb` 新建并重新哈希。发送端外置回执 `D:/ck3-research-artifacts/war31-h2743-20260928/sender-copy-receipt-readonly-v3.json` SHA-256 `C98D4DA3B470A33328E4D149416E63DD0319D81811BE071F0C2F808E58DF9FAE`。H2743 save、driver、family sidecar 和原件 DLL 没有再次上传；来源机需对其既有原件自行复算大小与 SHA，绝不以本机副本可读代替来源机 ACK。本轮未读取或下载 WAR 下其他请求的二进制内容。

请求将来源机实机定为有条件、低于其现有高优先级占屏任务：先在 `RECEIVER-ACK.json` 报精确资产与可用性；只有来源机自己的 CK3/录制/屏幕锁、Steam 新鲜离线画面、EXE SHA、完整 no-launch 配对全部 GREEN 时，才可做 WarID `16777231` 的双次 `query-defender-de-jure-exit-terms-v1-16777231`。前后必须 paused、date_raw `53217264`、双方/目标/native revision 不漂移；禁止日期推进、投降、白和平和旧崩溃 effect preview。只有 managed supervisor 返回 0、CK3 PID 空、stdout 读取结束且原件／候选／已放置资产后哈希全匹配，才可报只读成功。来源机路径可能不同，#448 wrapper 的本机绝对路径不可未经审阅直接照搬。

战争机 [v3 运行单](h2743-dejure-readonly-live-v3-runbook-2026-09-28.md) 继续作为 E2 录制结束后的备用路线。即使来源机取得 14 行当前余额和两行收入，具体终战 title/vassal 变化、F、14 行有符号资源 delta、休战及续战风险仍未证明；`material_complete=false`、比较 unavailable、终战动作 null。来源机若回复 RED 或暂无屏幕，保留其原始 attempt 和 blocker，本机仍排新独立 attempt。
