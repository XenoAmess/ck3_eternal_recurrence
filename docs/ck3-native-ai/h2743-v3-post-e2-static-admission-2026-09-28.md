# H2743 v3：E2 录制后只读准入复核

复核时间：2026-09-28。**只读静态审计；本轮未领取 `ck3-screen`、未运行 official no-launch、未启动 CK3、未提交投降或其他游戏动作。** 本记录将一个会持续前进的 master 固定在以下精确提交；若正式占屏前 master 或候选 DLL 变化，重新核对这些门。

## 分支与当前 master

- draft PR #448 的已推送 head：`ef8f6299aa2aabde283a574a1cc6d5126d0227e4`；本轮抓取的 `origin/master`：`5d675a35647c687b3e9f5ff43721954742c60729`；共同祖先 `5d2070f502ebc45a47cb034fbe054dd3e402bf14`。
- 对这两个精确提交运行 `git merge-tree --write-tree origin/master HEAD` 返回 0，生成树 `1d9d2a71e5c9fb4aa8401f4aff2f9a2bbe36c510`，没有文本冲突。GitHub 当次把 PR 报为 draft / `MERGEABLE` / `CLEAN`；PR 的 static、签名与 CLA 检查通过。以上是静态合并与 CI 证据，不是该合并树的本机 CK3 实机验收。
- master 在共同祖先后更改了 `bridge.cpp`、native query mailbox、`native_driver.py`、`cli.py`、`strategy.py` 等；#448 也改 native bridge/driver/strategy。合并树虽无文本冲突，H2743 已构建候选 DLL仍是 #448 分支既有产物，**不能据此声称它含有 master 后来的 R0271/R0284/M6 运行时改动**。H2743 只读尝试按当前 #448 分支与该 DLL 配对；若先合并 master 或重建 DLL，作为新候选重新编译、冻结 SHA 并新建 attempt。

## 精确源配对与静态检查

`run_h2743_dejure_readonly_v3.py --check-static` 本轮返回 `static_bytes_verified_no_launch`；它同时探测分支 CLI 顶层、`native-session` 与 MCP 的 `--help`。精确路径和 SHA-256：

| 角色 | 路径 | SHA-256 |
| --- | --- | --- |
| 源 save | `D:/ck3-research-artifacts/war31-h2743-20260928/source-verified-01/xar_checkpoint.ck3` | `A5012030DA500A4352EF79D1EA10269D45DD5D19DAC508E22DD835663A5106E9` |
| 源 driver | 同目录 `driver-state.json` | `F31460BAA126BAED289CBA20A6FEFF59AAF6EF87BA3B29943C892236B6D15069` |
| 源 family sidecar | 同目录 `first-heir-marriage-formal-v1.json` | `12D7B2B006E409DB69F7F442107B01B5D38D8C589A7F494B24519094024B5724` |
| 源 DLL | 同目录 `xar_ck3_bridge.dll` | `8C3A9523D14DEDB6C44AC04F748BFC9D086E983B2A973A956CBADD21F07A8A5C` |
| v1 只读候选 DLL | `D:/ck3-research-artifacts/war31-h2743-20260928/build-read-port-v1/Release/xar_ck3_bridge.dll` | `FD8B5C7873C22BE32ACF2E421D2A9F625AE8FF3FB4D5408DB7F6E6AF15321470` |
| injector | `D:/ck3-research-artifacts/war31-live-20260927/source-verified-01/R0221-original-bridge/native/xar_ck3_bridge_injector.exe` | `C89F1A919514A7E664AEE8FAF165B78C693ABA4EA2105289BDA2DB4BAC6A84FF` |
| CK3 EXE | `C:/SteamLibrary/steamapps/common/Crusader Kings III/binaries/ck3.exe` | `2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86` |

四件源是 OneDrive 精确配对后的 receiver 原件；运行用的是另列的候选 DLL。不得把源 DLL 的 SHA 当候选，也不得把当前资源余额或目标 Title ID 当本次终战 delta。

## E2 录制结束后的最短官方只读路径

1. 等录制者释放 CK3、录制进程和任务总线屏幕资源。本任务取得唯一 `ck3-screen:acquired`，确认没有现存 CK3；在该屏幕租约内选全新 `attempt-N-dejure-baseline-no-launch`，运行仓库脚本 `--prepare-no-launch --attempt-name <新编号> --task-id <本任务ID>`。它依次做 `prepare-profile`、放置精确 save/driver/family sidecar、ordinary seed rebind 和 `native-one-generation-preflight`。只接受新 attempt 的 `no_launch_preflight_ready`；旧 08/09 RED 和旧 04/05 GREEN 都不可复用。
2. 取得**当次** Steam 位移截图及 `steam-frame-freshness.json`，人工审阅新图确见“离线模式”，在新 attempt 下填写 `steam-gate.json`（真实审阅人、UTC、截图路径与 SHA）。脚本验证截图与位移收据绑定、审阅距启动不超过 10 分钟，并实时查任务总线独占。具体 schema 与完整命令在 [H2743 v3 运行单](h2743-dejure-readonly-live-v3-runbook-2026-09-28.md)。
3. 同一租约中运行 `--run --prepared-attempt <新 attempt> --steam-gate <新 gate> --task-id <本任务ID>`。唯一允许的游戏层 query step 是 `query-defender-de-jure-exit-terms-v1-16777231`；读取前后 paused H2743 帧，双次同帧 baseline。只在 supervisor 返回 0、CK3 PID 空、stdout reader 停止、源四件／候选 DLL／injector／已放置 save 与 sidecar 后哈希匹配时写 `read-only-result.json`。失败保存原始 envelope、日志与 RED 收据，换新 attempt；不写成功回执。

时间安排：旧 H2743 attempt-04 的 profile/rebind/preflight 文件集中在 02:51–02:52 本地，约 1 分钟；它的旧 DLL 只读会话从 02:52 到 03:03，约 11 分钟。更近期 R0271 R0004 从启动到首个可执行原生命令用 **23 分 37 秒**，是当前保守冷启动参考。新 v3 有双读、55 MB 级快照落盘、清理验签及新鲜 Steam 取证；**可执行工作的实际估计约 30–40 分钟，建议预留至少 60 分钟独占窗口**。这只是排队估算，不是保证完成时间：脚本就绪门 1800 秒、会话超时 3000 秒、停机等待 180 秒；任何超时即 RED 并保全 attempt。

v1 只读结果仍只含双方当前 **14 行余额** 与 2 行月金币收入。运行时 `scope:target`、F 因子、完整 title/vassal 转移、14 行有符号终战资源 delta、条件效果、停战期限及同帧续战风险未读到前，正式比较保持 `unavailable`、`action_literal=null`。本步骤也不调用已崩溃的广义 effect preview 或任何终战动作。
