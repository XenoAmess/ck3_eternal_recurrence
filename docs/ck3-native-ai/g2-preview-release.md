# G2 标准封建可运行预览包（ordinary R783 冻结版）

截至 2026-09-16，用户可以取得并启动本页所列的冻结 ZIP。R790 从该 ZIP 的全新解压目录完成只读资格验收；R791 通过正式 `native-auto-run` 继续同一战争目标并在安全 turn 边界受控停止、保存 checkpoint；R792 用另一个 CK3 进程从该 checkpoint 冷恢复 5/5 turn，没有重复已经生效的宣战。预览切片不改变正式 G2 里程碑，权威状态仍为 `1/8`（只完成 G2-M1）。

## 获取与冻结组合

- ZIP：`D:\ck3_mod_rewrite_process_assets\g2-preview-ordinary-r783-stage-20260916T134805Z-6cfba744\g2-preview-ordinary-5ac64152-r783.zip`
- ZIP SHA-256：`AA9CABB5D4CA709E55AB367A94D0C58A088AAD20D540B76F7990DAD1FC81517C`
- 大小：80,971,362 字节；883 个唯一条目；CRC 与包内逐文件哈希验收 GREEN。
- 包内 `candidate-manifest.json` SHA-256：`616C1E3B0943BD49CD85A261621CB0DF449A0F67B337085A7624E4C10FAEFB8F`。
- 外部 GO 清单：同目录 `download-manifest.json`，SHA-256 `A5CB85FE0D9BF96EF844B68055532220498FE8E298F8B2769515EC026AAD4B1D`。
- 实机资格凭据：同目录 `live-qualification-r790-r792.json`，SHA-256 `1EF45C2B14D43C6AA2E953D5BB0E56925F181CDC3819FA3ECE70BCC6F7E5361A`。

包内 candidate manifest 在封包时诚实保留 `NO_GO_PENDING_EXTRACTED_BUNDLE_LIVE_SMOKE`。ZIP 没有为改状态而重建；外部 GO 清单用 ZIP 精确 SHA 绑定封包后的 R790–R792 实机结果。ZIP 不包含 CK3、Steam 凭据、Python 虚拟环境、Workshop cache 或历史运行日志。

冻结版本：

| 项目 | 冻结值 |
| --- | --- |
| CK3 | `1.19.0.6` |
| `ck3.exe` SHA-256 | `2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86` |
| Python agent/source | `5ac6415258d9dfd4eb4e4e72d644dd76008b896a` |
| Native source | `320efe63b57959e6b314072acbe8043476cc56cf` |
| Native DLL SHA-256 | `EB00E44D3FAD25F924566714EBED1EC60438651A90C10CEDB67E0E105B4E4CD2` |
| Injector SHA-256 | `A25D31FED065F214EBCD18545DE7563848C2308FF5F666659DBEFFC1F5C0FDCB` |
| 政体/生命周期 | `feudal_government` / `ordinary_campaign_succession` |
| 游戏规则 | `xar_enabled=xar_off`，`ordinary_campaign_no_pact=true` |
| Mod 加载顺序 | 只有 `mod/xar_autoplayer.mod` |
| DLC 配置 | `disabled_dlcs=[]`；冻结主机发现 29 个 descriptor，未把账号 entitlement 冒充为独立验收 |
| Production mod tree | `8471F6B4333D2D3D0C4DFB1BE1DFF11A586953AE7B920089DFC830164FBF0367`，86 个文件 |

29 个已发现 descriptor 为：`dlc016_cp2`、`dlc007_ep2`、`dlc012_afr`、`dlc014_ep3`、`dlc011_ce1`、`dlc027_cp9`、`dlc003_fp1`、`dlc022_ep4`、`dlc001_preorder`、`dlc010_fp3`、`dlc004_ep1`、`dlc002_sp_day1`、`dlc029_mp1`、`dlc024_cp6`、`dlc009_bp2`、`dlc021_bp4`、`dlc026_cp8`、`dlc005_fp2`、`dlc008_sp2`、`dlc025_cp7`、`dlc013_sp3`、`dlc023_cp5`、`dlc017_cp3`、`dlc015_bp3`、`dlc006_bp1`、`dlc020_ce2`、`dlc028_sp5`、`dlc019_sp4`、`dlc018_cp4`。权威加载配置在包内 `config/dlc_load.json`。

## 一次性准备

1. 把 ZIP 解压到一个新目录。
2. 把 `operator-manifest.template.json` 复制为 `operator-manifest.json`。
3. 替换其中四类 `<ABSOLUTE_...>` 占位符：Python 3.11+ 可执行文件、解压包根目录、包含 `binaries\ck3.exe` 的 CK3 安装根目录，以及全新的可写 state 目录。包内源码、DLL、injector 和样本存档路径都从包根派生。
4. 取得 CK3 单实例所有权，确认所有受管环境没有存活 CK3。
5. 在解压包根目录运行：

```powershell
$Manifest = (Resolve-Path .\operator-manifest.json).Path
$Python = (Get-Content -LiteralPath $Manifest -Raw | ConvertFrom-Json).python
& $Python .\repo\tools\g2_preview_operator.py prepare-state --manifest $Manifest --sample-dir .\sample-resume
if ($LASTEXITCODE -ne 0) { throw "prepare-state failed" }
$Operator = Get-Content -LiteralPath $Manifest -Raw | ConvertFrom-Json
$Rebind = Get-Content -LiteralPath (Join-Path $Operator.state_dir 'ordinary-seed-rebind-v1.json') -Raw | ConvertFrom-Json
$Operator.environment_sha256 = $Rebind.environment.target_sha256
$Operator.driver_state_sha256 = $Rebind.driver_state.target_sha256
$Operator | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath $Manifest -Encoding utf8
```

`prepare-state` 会生成并核验 production-only `xar_off` profile、复制成对 checkpoint/driver state、把其环境绑定迁移到本机，并执行零启动预检。它拒绝覆盖已有配对 state；不要手改存档或 driver state。

## 资格验收与正式自动游玩

先为本次运行登记新的单调 CK3 轮次，再做两个 paused frame 的只读资格验收：

```powershell
$RunStamp = Get-Date -Format 'yyyyMMddTHHmmss'
$Eligibility = Join-Path $PWD "runs\eligibility-$RunStamp"
& $Python .\repo\tools\g2_preview_eligibility.py --manifest $Manifest --output $Eligibility
```

资格 GREEN、旧进程完全回收后，启动正式 production 策略循环：

```powershell
$RunStamp = Get-Date -Format 'yyyyMMddTHHmmss'
$Formal = Join-Path $PWD "runs\formal-$RunStamp"
& $Python .\repo\tools\g2_preview_operator.py run --manifest $Manifest --output $Formal --turns 20 --timeout 810 --readiness-timeout 720
```

样本 checkpoint 已经包含 `WarID=5` 和 `ArmyID=33`。策略会消费持久化目标，不能重复宣战。R790 的全新解压冷启动实际耗时 636.443 秒，因此 720 秒 readiness bound 是实测值；同一已准备 state 的 R791、R792 分别耗时 95.229 秒和 75.368 秒。

## 状态、受控停止与冷恢复

在另一终端从同一解压包根目录请求安全边界 checkpoint 后停止：

```powershell
$Manifest = (Resolve-Path .\operator-manifest.json).Path
$Python = (Get-Content -LiteralPath $Manifest -Raw | ConvertFrom-Json).python
& $Python .\repo\tools\g2_preview_operator.py request-stop --manifest $Manifest
```

查询完成报告：

```powershell
& $Python .\repo\tools\g2_preview_operator.py status --report (Join-Path $Formal 'formal-report.txt')
```

确认 CK3 进程树完全回收后，用新轮次和新输出目录冷恢复：

```powershell
$RunStamp = Get-Date -Format 'yyyyMMddTHHmmss'
$ColdRestore = Join-Path $PWD "runs\cold-restore-$RunStamp"
& $Python .\repo\tools\g2_preview_operator.py run --manifest $Manifest --output $ColdRestore --turns 5 --timeout 810 --readiness-timeout 720
```

位置：

- 游戏 checkpoint：`<state_dir>\profile\save games\xar_checkpoint.ck3`
- Agent state：`<state_dir>\native-session\driver-state.json`
- CK3 日志：`<state_dir>\profile\logs\debug.log`、`error.log`
- 停止请求：`<state_dir>\native-auto-run.stop`
- 每次完整报告：命令指定的 `<output>\formal-report.txt`

R791 的正式状态是 `operator_stop_checkpointed/operator_stopped`，operator exit code 为 0、receipt 为 completed。因为操作者在 200-turn 上限前主动停止，报告顶层 `ok=false` 只表示未跑满原上限，不是 RED。超时、未执行、真正 RED 和证据不足仍分别记账。

## 实机证据

| 轮次 | 结果 | 关键证据 |
| --- | --- | --- |
| R783 | 原始普通 production 闭环 | 正式 typed 宣战；独立下一 paused frame 出现 WarID 5；下一 turn 查询并消费 WarID 5；随后征兵、移动、战斗；20/20。报告 SHA `EF35A85242A95D3FE07A2C3EA8B5D6B3C932E38C49FFFC6E03A2D824AE459337`。 |
| R790 | 精确 ZIP 全新解压资格 GREEN | 两个公共 paused frame 均为 `feudal_government`、`xar_off`、角色 31853、同 episode、WarID 5/ArmyID 33、无 event/pending；9/9，进程清理。报告 SHA `ED366D67FE1E1699BABD7749B193B93F76CD2261E7776912A1CCAE1002BDA6F4`。 |
| R791 | 正式继续并受控停止 GREEN | 13/13 成功，6 个 gameplay turn；继续同一战争目标并出现 `start-assault-6`；安全停止 checkpoint SHA `318884F0DA24A5DC8388335E6FC82976400A91BA99A6E40D76FFCDAA8089148F`；进程清理。报告 SHA `7073FBD8B62C0F130EB99C6E169CB80F6EA41F1291D3A459A22CAFBA7B0E1F88`。 |
| R792 | 新进程 cold restore GREEN | 从 R791 checkpoint 恢复同一角色、episode、目标；5/5，4 个 gameplay turn，零重复宣战；最终 checkpoint SHA `DE8BA3330DFC2586CEE4E754C2C3C43F7F41B5BDB52F2F2FDEA2A9C8C6AF2F1`；进程清理。报告 SHA `B1E8FA374421A7DF25C822E2E8451FEF5C5EEE907610D8E80BD851F4EF977F97`。 |

## 支持边界

当前只支持上述 exact build、标准封建、`xar_off`、单 mod 加载组合和包内普通 campaign continuation。它已验证有界 production 自动游玩、真实非空动作、后续消费、checkpoint、受控停止和 cold restore。

尚未通过或不广告：1066→1453 首条整局、第二独立种子、议会四门和正式任命闭环、typed 战争终局及 truce/settlement、指定自然事件、同一普通 campaign 的自然继承完整恢复、两年治理、婚姻外交质量、其他政府和 G2 广矩阵。未知强制状态必须保留 RED 并停在可核验现场；动作结果不明时先查真实状态，不能盲重试。游戏升级也不会自动兼容，参见 [MCP/Native 地址定位与升级迁移评估](mcp-ck3-addressing-and-upgrade-migration.md)。
