# G2 标准封建可运行预览包（ordinary R802 冻结版）

截至 2026-09-17，本页所列 ZIP 已完成全新解压资格、正式 production 非空动作、独立后置结果、下一 turn 消费、受控停止 checkpoint 和新进程 cold restore，并由外部资格收据绑定为 `GO_RUNNABLE_PREVIEW`。它取代旧 R783 包作为当前交付；正式 G2 仍为 `1/8`，只完成 G2-M1。

## 获取与冻结组合

- ZIP：`D:\ck3_mod_rewrite_process_assets\g2-preview-ordinary-r802-9bacc5af-stage-20260917\g2-preview-ordinary-9bacc5af-r802.zip`
- ZIP SHA-256：`E32D2057B28641CE78C76F11C478704AA2EEBA549D8C30F7228C88F28DAA1273`
- 大小：79,662,600 字节；2,158 个条目；ZIP CRC GREEN。
- 包内 `candidate-manifest.json` SHA-256：`D11EC38F791E4607CF33A7F7FBEE25B10D5D104A57D7950D86C7531A85D417EF`。
- 外部 GO 清单：同 stage 的 `download-manifest.json`，SHA-256 `CAA552E05117A80C696C1BBBF46EA257E936F0C977E706310926E49DA9EBD4E5`。
- 外部实机资格收据：`D:\ck3_mod_rewrite_process_assets\g2-preview-ordinary-9bacc5af-r802-qualification\g2-preview-ordinary-9bacc5af-r802-live-qualification.json`，SHA-256 `9F7DA87BDEDA3C3C41D50831C5D6EAB724F8DE669586090ED10B8D60B10C1AA3`。

包内 candidate manifest 保留封包时的 pending 状态；外部 GO 收据绑定精确 ZIP 哈希，晋升未重写 ZIP。包中不含 CK3 本体、个人凭据、Python 虚拟环境、Workshop cache、可变运行状态或历史日志。

| 项目 | 冻结值 |
| --- | --- |
| CK3 | `1.19.0.6` |
| `ck3.exe` SHA-256 | `2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86` |
| Python agent/source | `9bacc5af2980cbd70767e8350f1262db60019e23` |
| Native source | `881e1ba5467f3304d930faaa958cdafd24962370` |
| Native DLL SHA-256 | `DA7CA9922FDDD006E66B4D36B051CE48E8A34858E1578E4C6C7F53064227D3B7` |
| Injector SHA-256 | `46D4326761E30C954CCD7E40AE160A0907CD582ABB6AB6ABD696333E5B6AC75F` |
| 初始 paired state | history 293、date `53150976`、actor `31853`、无 war/army/event/pending |
| 政体/生命周期 | `feudal_government` / `ordinary_campaign_succession` |
| 游戏规则 | `xar_enabled=xar_off`，`ordinary_campaign_no_pact=true` |
| Mod 加载顺序 | 只有 `mod/xar_autoplayer.mod` |
| DLC | `disabled_dlcs=[]`；冻结配置见包内 `config/dlc_load.json` |
| Production mod tree | `8471F6B4333D2D3D0C4DFB1BE1DFF11A586953AE7B920089DFC830164FBF0367`，86 个文件 |

## 一次性准备

把 ZIP 解压到新目录，在该目录打开 PowerShell。资格主机使用 CPython 3.13.2；按包内声明安装运行依赖：

```powershell
py -3.13 -m venv .xar-preview-venv
$Python = (Resolve-Path .\.xar-preview-venv\Scripts\python.exe).Path
& $Python -m pip install --disable-pip-version-check .\repo\ck3_autonomous_player
if ($LASTEXITCODE -ne 0) { throw "runtime dependency installation failed" }
```

复制 `operator-manifest.template.json` 为 `operator-manifest.json`，替换四类占位符：`<ABSOLUTE_PYTHON_EXE>`、`<ABSOLUTE_EXTRACTED_PACKAGE_ROOT>`、包含 `binaries\ck3.exe` 的 `<ABSOLUTE_CK3_INSTALL_ROOT>`，以及全新空目录 `<ABSOLUTE_NEW_EMPTY_STATE_DIRECTORY>`。取得 CK3 单实例所有权并确认所有受管主机无存活 CK3 后运行：

```powershell
$Manifest = (Resolve-Path .\operator-manifest.json).Path
$Python = (Get-Content -LiteralPath $Manifest -Raw | ConvertFrom-Json).python
& $Python .\repo\tools\g2_preview_operator.py prepare-state --manifest $Manifest --sample-dir .\sample-resume
if ($LASTEXITCODE -ne 0) { throw "prepare-state failed" }
$Operator = Get-Content -LiteralPath $Manifest -Raw | ConvertFrom-Json
$Rebind = Get-Content -LiteralPath (Join-Path $Operator.state_dir 'ordinary-seed-rebind-v1.json') -Raw | ConvertFrom-Json
$Operator.environment_sha256 = $Rebind.environment.target_sha256
$Operator.driver_state_sha256 = $Rebind.driver_state.target_sha256
$Operator | ConvertTo-Json -Depth 12 | Set-Content -LiteralPath $Manifest -Encoding utf8
```

`prepare-state` 复制成对 checkpoint/driver state、把环境绑定迁移到本机并执行零启动预检；它拒绝覆盖已有 state。不要猜哈希、手改存档或 driver state。

## 启动自动游玩

先登记新的单调 CK3 轮次，再做两个 paused frame 的只读资格验收：

```powershell
$Stamp = Get-Date -Format 'yyyyMMddTHHmmss'
$Eligibility = Join-Path $PWD "runs\eligibility-$Stamp"
& $Python .\repo\tools\g2_preview_eligibility.py --manifest $Manifest --output $Eligibility
if ($LASTEXITCODE -ne 0) { throw "eligibility failed" }
```

资格 GREEN 且旧进程完全回收后，从正式 production 入口启动：

```powershell
$Stamp = Get-Date -Format 'yyyyMMddTHHmmss'
$Formal = Join-Path $PWD "runs\formal-$Stamp"
& $Python .\repo\tools\g2_preview_operator.py run --manifest $Manifest --output $Formal --turns 20 --timeout 810 --readiness-timeout 720
```

包内样本从 WarID 5 终局后的和平 checkpoint 开始。R805 实际运行经公共查询选择新的合法战争、typed 宣战、独立观察 WarID 25、下一 turn 消费、征兵、行军和战斗；旧 `offer-white-peace-5` 没有重放。

## 状态、受控停止与恢复

从另一终端请求在安全 turn 边界保存 checkpoint 并停止：

```powershell
& $Python .\repo\tools\g2_preview_operator.py request-stop --manifest $Manifest
```

查询报告：

```powershell
& $Python .\repo\tools\g2_preview_operator.py status --report (Join-Path $Formal 'formal-report.txt')
```

确认进程树完全回收后，分配新轮次并使用新的输出目录冷恢复：

```powershell
$Stamp = Get-Date -Format 'yyyyMMddTHHmmss'
$ColdRestore = Join-Path $PWD "runs\cold-restore-$Stamp"
& $Python .\repo\tools\g2_preview_operator.py run --manifest $Manifest --output $ColdRestore --turns 5 --timeout 810 --readiness-timeout 720
```

- checkpoint：`<state_dir>\profile\save games\xar_checkpoint.ck3`
- Agent state：`<state_dir>\native-session\driver-state.json`
- CK3 日志：`<state_dir>\profile\logs\debug.log`、`error.log`
- 停止请求：`<state_dir>\native-auto-run.stop`
- 每次完整报告：命令指定的 `<output>\formal-report.txt`

操作者主动停止时，formal report 的 `operator_stop_checkpointed/operator_stopped` 与 operator receipt 的 `completed / exit 0` 共同表示成功；顶层 `ok=false` 只表示未跑满原 turn 上限。真正 RED、超时、未执行和证据不足仍分别记账。

## 实机资格证据

| 轮次 | 结果 | 关键证据 |
| --- | --- | --- |
| R804 | 全新解压 eligibility GREEN | 9/9 检查；actor 31853、date 53150976、标准封建、`xar_off`、空活动上下文；PID 205880 完全回收。报告 SHA `31B13D0FB8D0F29031D6C6C9796A2FA96D427ADDA7DEEC52C0E5889236F76D30`。 |
| R805 | 正式非空动作与受控停止 GREEN | 13/13，6 个 gameplay turn；typed 宣战后独立出现 WarID 25，下一 turn 查询消费，随后征兵/移动/战斗；history 316 checkpoint `96058952...FAE6`，driver `348FF39E...C047`；旧白和平重放 0；PID 167232 回收。报告 SHA `EE0CBC020E2EEA887D471A94A9D5296E70A917BB9D8E4D8B85C3379EBCF719AF`。 |
| R806 | 新进程 cold restore GREEN | PID 52284 从 R805 精确 pair 恢复 actor/episode/WarID 25/ArmyID 304；5/5，2 个 gameplay turn，date 53151912→53152848；重复宣战 0、旧白和平重放 0；最终 checkpoint `E2044A6B...CD7B`、driver `A34BEBBF...B4FF`；进程回收。报告 SHA `3F09893FD9B0CB839EDC0FCA005918015EC9FBF7084BBEA6824E4B8306AED1F2`。 |

## 支持边界

当前只支持上述 exact build、标准封建、`xar_off`、冻结 DLC/mod/load order 和包内普通 campaign continuation。已验证有界正式自动游玩、真实非空策略动作、独立游戏后置状态、下一循环消费、受控停止、成对 checkpoint 和新进程 cold restore。

未通过或不广告：任意用户存档/种子、1066→1453 首条整局、第二独立种子、Council 四门与正式任命、GEN-034 Raiktor 专项 C/D、指定自然事件、同一普通 campaign 的自然继承完整恢复、两年治理、婚姻外交质量、其他政府和 G2 广矩阵。未知强制状态保持 fail-closed；动作结果不明时先查真实状态，禁止盲重试。游戏升级不自动兼容，参见 [MCP/Native 地址定位与升级迁移评估](mcp-ck3-addressing-and-upgrade-migration.md)。
