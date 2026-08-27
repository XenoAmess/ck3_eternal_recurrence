# 一代人 20-turn production canary 交接

状态：`static-ready / normal-desktop live pending`。本入口只验证一代人严格运行器的 G1 启动、20 回合 OODA、
持久化 checkpoint/blocker 与 cleanup；它不把 20 回合存活误称为完成一代，也不替代后续全寿命长跑。

## 固定 production6b 输入

- source state：`%TEMP%\xar-war-entry-production6b-state`；只读，不原地 prepare 或运行；
- checkpoint：`67118175` bytes，SHA-256
  `12FD30A079982E3B01FAD6442574D7938E795A84A59B4EBDD53023135B04F37D`；
- driver state：SHA-256
  `3C3BBFECDC6941B17B1CC946CEDA1011ABF3DD673AD511B1BFB764FC20E955A9`，pipe
  `\\.\pipe\xar_ck3_restore_exact2_7aff1d0`，Character `29829`，run
  `native-29829-ee172aa720db`，date `53177976`，history anchor `402`；

checkpoint、driver、pipe、Character、run、date 和 history anchor 对两个 profile 完全相同。代码与 native 产物身份按
profile 独立冻结：

- `legacy`（默认）：clean runtime commit
  `480f287489eb91efd65f94ec07bc39f681960bd0`；DLL SHA-256
  `A2B78F371A16A87B2A911E1E832C07A5701E2E7B3C42FA046006A41C233702DF`；injector SHA-256
  `1618840EC108F688B3EBECC6D7F8963038BA64C8D4A3E10DDE2E29E3F443B4DF`；
- `claim-cb-white-peace`：clean runtime commit
  `51fe8cf6cb55de5ca01db4ed215e0abff52213a6`；DLL SHA-256
  `F52203F2395819CCB7A37153DBD36AB9CC6F6E168F4B44D179D3979ABF939D7B`；injector SHA-256
  `8A46DE3BFBF567E34BA99E61AEFA7F59DA248C4AE89791BB74E12820B4380B99`。

入口是 [run_one_generation_canary.ps1](../../tools/run_one_generation_canary.ps1)。`-Profile` 只接受 `legacy` 或
`claim-cb-white-peace`，省略时仍是 `legacy`。脚本默认只生成 dry-run JSON，
不创建 target；只有显式 `-Execute` 才运行。执行路径还要求当前 token 为 `xenoa`、当前 desktop 为
`WinSta0\Default`、没有现存 `ck3.exe`，并拒绝任何已存在 target。target 限定为当前 `%TEMP%` 的新后代；
复制使用非 mirror、非 purge 的 `robocopy /E`。失败后保留新 target 供诊断，绝不删除或回写 source。

## claim_cb 白和平正常桌面命令

本机已经准备好完全 clean、detached 的 canonical runtime worktree：
`C:\Users\xenoa\AppData\Local\Temp\xar-claim-white-peace-runtime-51fe8cf`。只有该目录不存在、确需重建时，
才从认识 `51fe8cf` commit 的隔离 clone 创建；不要对尚不认识该 commit 的 `Z:\ck3_mod_rewrite` 运行此命令：

```powershell
git -C "C:\Users\xenoa\AppData\Local\Temp\xar-one-generation-milestone-20260827-113758" `
  worktree add --detach `
  "C:\Users\xenoa\AppData\Local\Temp\xar-claim-white-peace-runtime-51fe8cf" `
  51fe8cf6cb55de5ca01db4ed215e0abff52213a6
```

然后在普通 `xenoa / WinSta0\Default` PowerShell 先运行 dry-run：

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File `
  "C:\Users\xenoa\AppData\Local\Temp\xar-agent-mainline-worktree-20260827-1254\tools\run_one_generation_canary.ps1" `
  -Profile claim-cb-white-peace `
  -RepoRoot "C:\Users\xenoa\AppData\Local\Temp\xar-claim-white-peace-runtime-51fe8cf" `
  -GameDir "Z:\ck3_mod_rewrite\Crusader Kings III" `
  -PythonPath "Z:\ck3_mod_rewrite\tools\.venv\Scripts\python.exe" `
  -BridgeDll "Z:\ck3_mod_rewrite\ck3_autonomous_player\native_bridge\build-claim-white-peace-51fe8cf-msvc\xar_ck3_bridge.dll" `
  -BridgeInjector "Z:\ck3_mod_rewrite\ck3_autonomous_player\native_bridge\build-claim-white-peace-51fe8cf-msvc\xar_ck3_bridge_injector.exe"
```

claim profile 的默认产物路径是相对 `RepoRoot` 的
`ck3_autonomous_player/native_bridge/build-claim-white-peace-51fe8cf-msvc/`。因为 clean worktree 通常不包含 ignored
build 目录，上面的正常桌面命令显式指向主仓库里的冻结产物，但脚本本身没有硬编码盘符。确认 JSON 的
`profile=claim-cb-white-peace`、`git_revision`、四项 SHA、pipe、`host_observed` 和 `execute_host_required` 一致后，
在同一窗口给同一命令追加 `-Execute`。

## legacy 正常桌面命令与隔离边界

先在普通 `xenoa / WinSta0\Default` PowerShell 运行 dry-run：

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File `
  "C:\Users\xenoa\AppData\Local\Temp\xar-agent-mainline-worktree-20260827-1254\tools\run_one_generation_canary.ps1" `
  -RepoRoot "C:\Users\xenoa\AppData\Local\Temp\xar-one-generation-milestone-20260827-113758" `
  -GameDir "Z:\ck3_mod_rewrite\Crusader Kings III" `
  -PythonPath "Z:\ck3_mod_rewrite\tools\.venv\Scripts\python.exe" `
  -BridgeDll "Z:\ck3_mod_rewrite\ck3_autonomous_player\native_bridge\.build-event-scopes-a860702-msvc\xar_ck3_bridge.dll" `
  -BridgeInjector "Z:\ck3_mod_rewrite\ck3_autonomous_player\native_bridge\.build-event-window-cea30a0-msvc2\xar_ck3_bridge_injector.exe"
```

这条旧命令省略 `-Profile`，因此保持 `legacy`。它只对应 `480f287 + 旧 DLL + 旧 injector` 的冻结组合；不得把
`51fe8cf` source、新 DLL 或新 injector 混入 legacy，也不得用 claim profile 搭配旧产物。dry-run 可显式覆盖
`Expected*` 以验证夹具；`-Execute` 会在复制 target 前要求所有 Expected* 严格等于所选 profile 的 canonical
identity，不能用 override 绕过。

这里两条即时命令都引用隔离 mainline 中已经具备双 profile 的 helper。`Z:\ck3_mod_rewrite\tools` 在本变更合入前仍是
历史单 profile helper；它可以继续承担原 legacy handoff，但不能据此运行 claim profile。合入后脚本位置可以切回主仓库，
所选 profile 的 canonical identity 不变。

确认 JSON 的 `profile=legacy`、`git_revision`、四项 SHA、pipe、`host_observed` 和 `execute_host_required` 一致后，在同一窗口给同一命令
追加 `-Execute`。必须使用上面的显式 `powershell.exe ... -ExecutionPolicy Bypass -File` 形式；本机默认 execution policy
会阻止直接 `& script.ps1`。脚本会：

1. 原子占用一个从未存在的新 target，再完整复制 production6b state；
2. 核对 target checkpoint 与 driver-state 逐字节等于 source；
3. 从 clean clone 显式以 `--bridge-mode disabled`、显式 `--game-dir` 运行 `prepare-profile`，随后同样运行
   `verify-profile`；不会拿仍含旧绝对路径的复制 manifest 做 pre-prepare verify；
4. 再次证明 prepare/verify 没有改变 checkpoint 或 driver-state；
5. 以 exact pipe/DLL/injector 运行 `native-one-generation --max-turns 20`；
   wall timeout 固定为 `21600` 秒，readiness timeout 固定为 `300` 秒，checkpoint cadence 固定为 `3`；
6. 核对 source 仍未改变，并核对 CLI 返回报告逐字段等于 target 中最新、`finalized=true` 的 one-generation report；
7. 独立核验最新 run 的 `report.json` 路径/identity。bounded 分支必须验证 `first-blocker.json` 的相对路径、大小、
   SHA-256 和完整 JSON 均与 report 绑定；qualified 分支同样验证 `terminal-settlement.json`，并要求全部
   `qualification_gates=true`；
8. runner 返回后立即重新枚举 `ck3.exe`；只有进程数为 `0` 才接受上述两种结果，PID 列表写入 helper JSON。

## 结果判定

- 20 回合内自然完成该角色死亡结算：native exit `0`、`outcome=qualified`，helper exit `0`；这是罕见但合法的
  canary GREEN。
- 角色在回合上限仍存活：native exit `1`、`outcome=bounded_incomplete`、`status=turn_limit`、
  `cleanup.ok=true`、`first_blocker.kind=run_bound_exhausted`，且持久化报告为最新 finalized run。脚本保留 native
  exit `1` 于 JSON，但只有 first-blocker sidecar 绑定且 post-run CK3 inventory 为空时才自身 exit `0`。这是
  **预期 canary 结果，但不是 G1 一代人完成 GREEN**。
- 其余 exit `1`、报告不匹配、cleanup RED、planner blocker 或 harness error：helper exit `1`，必须读取
  `report_path` 和 `first-blocker.json` 后再决定下一项施工。

## 已知、刻意不处理的 G2 债务

production6b 的 `native-session/episode-seed.json` 仍指向另一 state，且本 state 没有
`profile/save games/xar_episode_seed.ck3`。它只影响死亡后 `start-next-episode` 的 G2 路径，不影响本次固定
checkpoint 的单寿命 G1 canary。此次只记录，不修改 source、不伪造 episode seed；长跑须使用另一个 fresh target，
不得复用本 canary state。
