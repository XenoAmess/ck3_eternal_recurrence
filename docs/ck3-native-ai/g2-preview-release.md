# G2 标准封建可运行预览包（冻结版）

R706 已从这份精确 ZIP 的全新解压目录经正式 `native-auto-run` 完成 5/5 turn 实机冷启动、日期推进、新 checkpoint 和进程回收；R701–R704 已在同一普通 production campaign 证明正式非空动作、后续策略消费、可控停止及另一新轮次 cold restore。用户现在可用下述冻结包和已准备的 state 启动有界自动游玩。预览切片不改变正式 G2 里程碑状态，权威状态仍为 1/8。

## 获取与支持组合

冻结 ZIP：`Z:\ck3_mod_rewrite_process_assets\g2-preview-bundle-d11268f1-eefc88e4\g2-preview-candidate-d11268f1-eefc88e4.zip`，81,958,760 字节，SHA-256 `0e233dcb024d1df3e6eb1a3534f1d160cf27b4609cec078cc2a1364551e44eb2`。同目录外部交付清单 `download-manifest.json` SHA-256 `c4af9c509cd31cd22ff1fff50d1f5f4ff29187181207edf9ba3bb284a8fb395e`（2026-09-16 只读复核），记录 R706 从该 ZIP 验证后的 `GO_BOUNDED_PREVIEW_EXACT_VALIDATED_HOST`、报告与 checkpoint 映射。包内 `candidate-manifest.json` SHA-256 为 `ff352e242a68fdc62268f40f78bb67088f4170b92449f82bbac98489e99bf730`；它封存时仍写 `NO_GO_PENDING_FORMAL_SMOKE_FROM_ZIP_LAYOUT`，通过后的状态在**外部**交付清单，ZIP 未为改状态无故重建。764 个 ZIP entry 的 CRC 与 763 个文件的逐文件 SHA 已通过。ZIP 不包含 CK3 本体。用户在本机可先核对：

```powershell
$zip = 'Z:\ck3_mod_rewrite_process_assets\g2-preview-bundle-d11268f1-eefc88e4\g2-preview-candidate-d11268f1-eefc88e4.zip'
$expectedZipSha = '0e233dcb024d1df3e6eb1a3534f1d160cf27b4609cec078cc2a1364551e44eb2'
if ((Get-FileHash -Algorithm SHA256 -LiteralPath $zip).Hash.ToLowerInvariant() -ne $expectedZipSha) { throw 'preview ZIP hash mismatch' }
```

实机冻结组合是 CK3 `1.19.0.6`，`ck3.exe` SHA-256 `2d00ff3101ef70b566f2fcbae292f09263199c80e9dc8f139b82d7d96f83db86`；正式 Python agent/source commit `d11268f15b829a38d0f6e32cffe9d62b71aad306`；默认 Release native DLL/injector 来源 commit `eefc88e43859c422b562b4c0a9489c347fec3233`，SHA-256 分别为 `5143f1c6d6d25775b9d048d59050c5a465dcbad59d10b4e5837dbeba0bd5fdf5`、`9754f14ffb5079155f0cfd4908ed99a024c04585ef66bac75d38546deefea1b1`。政府范围仅 `feudal_government`。R706 production profile environment SHA-256 为 `c044ff66fc11ba23bf0162e6378b5c16f551a74b4b0820f175f5dc8aecf37554`、rules SHA-256 为 `6cca52869f5bc32de1b509dd63255f8847875134933e936f97125ebc6be092f7`、production mod tree SHA-256 为 `8471f6b4333d2d3d0c4dfb1be1dff11a586953ae7b920089dfc830164fbf0367`；`dlc_load.json` 明确唯一加载顺序 `enabled_mods=["mod/xar_autoplayer.mod"]`、`disabled_dlcs=[]`。R706 解压态 CK3 启动 `debug.log` 第 26–88 行实际列出下述 29 个 DLC descriptor 和 29 个 VFS DLC 内容挂载，另仅一个 `mod/xar_autoplayer.mod|Enabled`；该日志 SHA-256 为 `c4da047b73398fce19beea6c0be6dc89fa4da899166131bd881a32f687f21a32`。这是本次游戏加载内容证据，账号 entitlement 未独立核验。当前包内普通 production 样本已验；任意其他封建存档尚未因此自动取得支持资格。

```text
dlc016_cp2, dlc007_ep2, dlc012_afr, dlc014_ep3, dlc011_ce1, dlc027_cp9,
dlc003_fp1, dlc022_ep4, dlc001_preorder, dlc010_fp3, dlc004_ep1,
dlc002_sp_day1, dlc029_mp1, dlc024_cp6, dlc009_bp2, dlc021_bp4,
dlc026_cp8, dlc005_fp2, dlc008_sp2, dlc025_cp7, dlc013_sp3,
dlc023_cp5, dlc017_cp3, dlc015_bp3, dlc006_bp1, dlc020_ce2,
dlc028_sp5, dlc019_sp4, dlc018_cp4
```

## 本机正式启动

下列路径是从上述**精确 ZIP**全新解压后实际校验的布局；这台已获授权的 Windows 宿主已有该解压目录和从包内样本生成的独立 production state。先取得 CK3 单实例所有权并确认所有受管环境的旧实例已经死亡。正式入口自行核对本机进程库存；其他机器失联不代表旧实例已死。

```powershell
$python = 'Z:\ck3_mod_rewrite\tools\.venv\Scripts\python.exe'
$repo = 'Z:\ck3_mod_rewrite_process_assets\g2-preview-bundle-d11268f1-eefc88e4\extracted-smoke\repo'
$state = 'Z:\ck3_mod_rewrite_process_assets\g2-preview-bundle-d11268f1-eefc88e4\extracted-smoke-state'
$game = 'Z:\ck3_mod_rewrite\Crusader Kings III'
$native = 'Z:\ck3_mod_rewrite_process_assets\g2-preview-bundle-d11268f1-eefc88e4\extracted-smoke\native'
$entry = Join-Path $repo 'ck3_autonomous_player\agent.py'
$pipe = '\\.\pipe\xar_ck3_restore_exact2_7aff1d0'
$common = @('-B', $entry, '--state-dir', $state, '--game-dir', $game, '--bridge-mode', 'native-headless', '--bridge-pipe', $pipe, '--bridge-dll', (Join-Path $native 'xar_ck3_bridge.dll'), '--bridge-injector', (Join-Path $native 'xar_ck3_bridge_injector.exe'))
$save = Join-Path $state 'profile\save games\xar_checkpoint.ck3'
$driverPath = Join-Path $state 'native-session\driver-state.json'
$driver = Get-Content -LiteralPath $driverPath -Raw | ConvertFrom-Json
$saveSha = (Get-FileHash -Algorithm SHA256 -LiteralPath $save).Hash.ToLowerInvariant()
$driverSha = (Get-FileHash -Algorithm SHA256 -LiteralPath $driverPath).Hash.ToLowerInvariant()
& $python @common native-one-generation-preflight --expected-character-id $driver.episode_character_id --expected-episode-run-id $driver.episode_run_id --expected-checkpoint-sha256 $saveSha --expected-driver-state-sha256 $driverSha
if ($LASTEXITCODE -ne 0) { throw 'cold-start preflight blocked; CK3 was not launched' }
$runDir = Join-Path (Split-Path -Parent $state) ('user-preview-' + (Get-Date -Format 'yyyyMMddTHHmmss'))
New-Item -ItemType Directory -Path $runDir -ErrorAction Stop | Out-Null
$formalReport = Join-Path $runDir 'formal-report.txt'
& $python @common native-auto-run --turns 20 --timeout 390 --readiness-timeout 300 --cold-start-checkpoint | Tee-Object -FilePath $formalReport
$cliExitCode = $LASTEXITCODE
```

`native-auto-run` 是 production 策略循环，启动后自行查询、决策、提交 typed 动作、核对独立 paused 后置状态、推进日期并保存 checkpoint；上述 20-turn 窗口内无需人工代点、代选人物/互动 ID 或手动推进日期。`--turns 20` 与 390/300 秒有界参数在同 d112 agent 版本的 R701 实机使用；精确 ZIP 布局的 R706 另以 5 turn 冒烟。stderr 会打印本次 `Operator stop request file: <state 目录的绝对路径>\native-auto-run.stop`，stdout 由 `Tee-Object` 单独保存为完整 JSON，不能用 `2>&1` 混入 PowerShell 的 NativeCommandError。当前解压态 state 已由 R706 继续到 date_raw `53192304`，save/driver 当前 SHA-256 分别是 `6e308a88b01a8ae0e7dc1a108eed7d4be17dab98b4404384366f1aeed65cdbc9`、`432cdef8d5476d8e4d534d25b7518c9c29fa24d578803201f6b4c85468afab09`；预检脚本每次读取实际当前 SHA，下一次运行会继续而非从旧样本重来。

上面的路径是已验宿主的实际值。迁移 ZIP 到另一获授权机器或新目录时，先确认当地 `ck3.exe` 是上述 exact SHA，并把 `$python`、`$repo`、`$game`、`$state`、`$native` 改为当地有权限的真实位置；将 ZIP 全新解压后的 `repo` 和 `native` 配套使用。**新** `$state` 要从解压源码执行正式 `prepare-profile`、`verify-profile`，让 mod descriptor 指向当地生成的 production 投影，再把包内 `sample-resume/xar_checkpoint.ck3` 与 `sample-resume/driver-state.json` 原样复制到 `$state/profile/save games/`、`$state/native-session/` 并用上面的正式预检。包内 `episode-seed.json` 仅作样本身份参考，不能替智能体改存档或动作结果。解压源码、只读查询能在其他授权环境使用，不等于该机器已核验可运行 CK3；ZIP 不含 Steam/个人凭据，账号与本地 CK3 授权由操作者各自取得。命令为：

```powershell
$entry = Join-Path $repo 'ck3_autonomous_player\agent.py'
& $python -B $entry --state-dir $state --game-dir $game prepare-profile
if ($LASTEXITCODE -ne 0) { throw 'production profile preparation failed' }
$sample = Join-Path (Split-Path -Parent $repo) 'sample-resume'
New-Item -ItemType Directory -Path (Join-Path $state 'native-session') -Force | Out-Null
Copy-Item -LiteralPath (Join-Path $sample 'xar_checkpoint.ck3') -Destination (Join-Path $state 'profile\save games\xar_checkpoint.ck3')
Copy-Item -LiteralPath (Join-Path $sample 'driver-state.json') -Destination (Join-Path $state 'native-session\driver-state.json')
& $python -B $entry --state-dir $state --game-dir $game verify-profile
if ($LASTEXITCODE -ne 0) { throw 'production profile verification failed' }
```

## 状态、暂停、停止与恢复

运行中可用本机进程库存看 CK3 是否存活；`native-session\driver-state.json` 只表示已持久化的命令历史与最近 checkpoint，并非独立 live-status CLI。正式结果在 CLI 退出后读本次 `$formalReport`：

```powershell
Get-CimInstance Win32_Process -Filter "Name='ck3.exe'" | Select-Object ProcessId,CreationDate,ExecutablePath
$result = Get-Content -LiteralPath $formalReport -Raw | ConvertFrom-Json
$result | Select-Object status,outcome,ok
$result.auto_run.successful_turns
$result.checkpoints | Select-Object -Last 1 status,date_raw,sha256
$result.cleanup | Select-Object ok,cleanup_proven
$cliExitCode
```

主动“暂停”是在当前 turn 的安全边界请求 checkpoint 后停止进程，随后可冷恢复；Windows 上实测的正式方法是在**另一个 PowerShell**中核对启动 CLI 实际打印的 stop 路径，再执行：

```powershell
$state = 'Z:\ck3_mod_rewrite_process_assets\g2-preview-bundle-d11268f1-eefc88e4\extracted-smoke-state'
$stopFile = Join-Path $state 'native-auto-run.stop'
Set-Content -LiteralPath $stopFile -Value stop
```

成功受控停止的正式结果为 `status=operator_stop_checkpointed`、`outcome=operator_stopped`、CLI 退出码 0、兼容配对 checkpoint、请求文件已消费清除、CK3 进程树已回收；这种提前停止的顶层 `ok=false` 不表示 RED，也不表示原定 turn 上限已完成。`operator_stop_checkpoint_deferred`、RED、超时、未执行、证据不足分别保留；强制 modal 或动作已提交但未确认时，先查 paused 实际结果和 receipt，不盲重试。PowerShell Ctrl+C 在已控台环境没有可靠到达 Python 停止处理器，不用它作为正式方法。

存档是 `$state\profile\save games\xar_checkpoint.ck3`，agent 配对状态是 `$state\native-session\driver-state.json`，同一目录还有 `episode-seed.json`；CK3 日志在 `$state\profile\logs\debug.log`、`error.log`，本次完整正式结果在 `$formalReport`。停止或有界结束且全部 CK3 进程回收后，保留 save/driver/版本关系，再在新轮次用上面的同一 `native-one-generation-preflight` 和 `native-auto-run --cold-start-checkpoint` 命令恢复。预检读取**当前** save/driver SHA，不把旧证据的 driver SHA 悄悄恢复；新进程必须继续同一 episode/高层目标，不重复已生效动作。

## 验收证据与限制

R701 d112 正式 20/20 turn 报告在 `Z:\ck3_mod_rewrite_process_assets\g2-preview-action-stop-d11268f1\action-live-attempt-1\formal-report.txt`，SHA-256 `e64060ab323da1bb24ec34c709d33b4dfdffdc6a8a471390587dc3ea1f9c0865d`：自然 `pay_ransom_interaction` → 正式唯一 typed reject → 独立下一 paused frame pending 消失 → 后续 turn 消费且未重复。R702 同 campaign 受控 stop 报告在 `...\stop-live-attempt-1\formal-report.txt`，SHA-256 `654e96110d8fe311c32cc153a45f0b35dd5b87abad67f19ad878b8ecd5e8cc00`。R703 d112 受控公共 paused 封建资格报告在 `...\eligibility-live-attempt-1\report.json`，SHA-256 `570a31dd4efbb7de2b8311558b3ce2fc023d38e31287da00b79f2c7e0a9cafe1`，只读查询无动作；它发生在 R701 动作与 R702 停止**之后**，不是 R701 同帧政府观测。R701 verifier 用真实 R703 资格报告通过 11/11。R704 新 CK3 进程正式 5/5 turn 冷恢复报告在 `...\cold-restore-after-eligibility-attempt-1\formal-report.txt`，SHA-256 `1097f1bd07a8ac7be52ddb7e09de0f3d794f0358e87a24c9fccf438817379aea`；同 episode、保守战争发现目标、日期前进、旧互动无第二次 reject，物理 checkpoint SHA-256 `5852f45fbd4a0c6cdda2b07d2e910a036dc46b0646699df378de245483c22e7d`。R706 **从冻结 ZIP 全新解压目录**正式 5/5 turn 报告在 `Z:\ck3_mod_rewrite_process_assets\g2-preview-package-smoke-d11268f1\formal-live-attempt-1\formal-report.txt`，SHA-256 `3f5cb8c2852a98bbf6fc2ccfb1f2731d9b0b040e30a92cd0bf98687e286c1822`；cold checkpoint 继续同 episode、日期 `53190696→53192304`、正式 `war-entry-minimal-defer-v1/NO_DECLARE` 保守战争发现目标、全历史旧 reject 仍只一次，新物理 checkpoint SHA-256 `6e308a88b01a8ae0e7dc1a108eed7d4be17dab98b4404384366f1aeed65cdbc9`，退出码 0、CK3 进程 0。该 WAR 策略明确 `semantic_optimal=false`，不广告成熟战争决策。

已验价值局限于此普通 production 标准封建样本的有界自动游玩、自然赎金 pending 回复、保守战争发现与自动日期推进、可控停止及 cold restore。R706 包冒烟本身没有新增语义动作；真实非空动作、独立后置状态与下一 turn 消费直接来自**同 d112 Python/native/mod 冻结组合**的 R701，不能把 R706 的两次日期推进改写成新动作证据。议会四类门、战争终局、自然指定事件、自然继承人接续、和平建设/封臣治理、婚姻外交、整局 1066→1453、双独立种子及其他政府未通过正式主链，不注册或广告为本预览能力；R705 的真实战争 RED 独立保留处理。遇到范围内未知强制状态或缺关键观测时，保留 RED 并停止在 checkpoint/日志现场，不把 no-op 或人工救场称继续可用。
