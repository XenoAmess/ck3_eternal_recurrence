# G2 标准封建可运行预览包（ordinary R878 冻结版）

截至 2026-09-21，R878 精确 ZIP 已完成 fresh extraction 资格、正式 production 非空动作、独立后置帧、下一 turn 消费、受控停止 checkpoint 和新进程 cold restore，并由外部资格收据绑定为 `GO_RUNNABLE_PREVIEW`。它取代 R802，成为当前交付版本。正式 G2 仍为 `1/8`，只完成 G2-M1。

## 获取与冻结组合

- ZIP：`D:\ck3_mod_rewrite_process_assets\g2-preview-ordinary-r878-7d215435-stage-20260921\g2-preview-ordinary-7d215435-r878.zip`
- ZIP SHA-256：`05C4F9DCDC75B4211256CD8A38A642DA5C2B3EE00FB9A6E574263E5668FC5E13`
- 大小：87,928,874 字节；2,239 个条目；ZIP CRC GREEN。
- 包内 `candidate-manifest.json` SHA-256：`B477D6C07787D8595BE7928A0F08AE5892990A13DCE0ADD863BE8455C3A6564B`。
- 外部 GO 清单：同 stage 的 `download-manifest.json`，SHA-256 `EF5FB58E31E78C70C035C5682397574B5D80FC5395B3E50F4698B41E70CB9B8A`。
- 外部实机资格收据：`D:\ck3_mod_rewrite_process_assets\g2-preview-ordinary-7d215435-r878-qualification\g2-preview-ordinary-7d215435-r878-live-qualification.json`，SHA-256 `D9D9838CC44E3BC7183356350E2895856DEA7E61A95423873B75622B72FAC8AB`。

包内 candidate manifest 保留封包时的 pending 状态；外部 GO 收据绑定精确 ZIP 哈希，晋升没有改写 ZIP。包中不含 CK3 本体、个人凭据、Python 虚拟环境、Workshop cache、可变运行状态或历史运行日志。

| 项目 | 冻结值 |
| --- | --- |
| CK3 | `1.19.0.6` |
| `ck3.exe` SHA-256 | `2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86` |
| Python agent/source | `7d215435da2b616a228024ac8161ae493f5477ce` |
| Native source | `8adbf94091c80900a0efadcc6fdff7802dd7c732` |
| Native DLL SHA-256 | `FC3367D90200CE08A3E7612DC22D2F6D920744E62EB83EAD62A2B9CF5A6420CF` |
| Injector SHA-256 | `67DD5FB84E7E655F9F9BD095B65629A0FA2B9280704F917E162D0B9A3877785E` |
| 初始 paired state | history 1347、date `53282472`、actor `31853`、WarID `150994969`、ArmyID `184549472` |
| 政体/生命周期 | `feudal_government` / `ordinary_campaign_succession` |
| 游戏规则 | `xar_enabled=xar_off`，`ordinary_campaign_no_pact=true` |
| Mod 加载顺序 | 只有 `mod/xar_autoplayer.mod` |
| DLC | `disabled_dlcs=[]`；冻结配置见包内 `config/dlc_load.json` |
| Production mod tree | `8471F6B4333D2D3D0C4DFB1BE1DFF11A586953AE7B920089DFC830164FBF0367`，86 个文件 |

## 一次性准备

把 ZIP 解压到一个全新目录，在该目录打开普通 `cmd.exe`。资格主机使用 CPython 3.13.2；按包内固定依赖创建运行环境：

```text
py -3.13 -m venv .xar-preview-venv
.xar-preview-venv\Scripts\python.exe -m pip install --disable-pip-version-check .\repo\ck3_autonomous_player
```

复制 `operator-manifest.template.json` 为 `operator-manifest.json`，替换四类占位符：

- `<ABSOLUTE_PYTHON_EXE>`：刚创建的 `.xar-preview-venv\Scripts\python.exe` 绝对路径；
- `<ABSOLUTE_EXTRACTED_PACKAGE_ROOT>`：当前解压根；
- `<ABSOLUTE_CK3_INSTALL_ROOT>`：包含 `binaries\ck3.exe` 的 CK3 根；
- `<ABSOLUTE_NEW_EMPTY_STATE_DIRECTORY>`：一个全新、空的本机可写目录。

确认所有受管主机都没有存活的 CK3 后运行：

```text
.xar-preview-venv\Scripts\python.exe .\repo\tools\g2_preview_operator.py prepare-state --manifest .\operator-manifest.json --sample-dir .\sample-resume
```

`prepare-state` 会复制成对 checkpoint/driver state、绑定本机环境、执行 production-only no-launch preflight，并自动把实际 environment/driver 哈希回写 manifest。不要手抄哈希，不要手改存档或 driver state；该命令拒绝覆盖已有 state。

## 启动自动游玩

在本项目受管环境，每次会启动 CK3 的 attempt 都必须先确认 process-zero，并用当前 master 的分配器取得正式编号。先在当前仓库 master 根目录打开 `cmd.exe`，资格主机验证过的持久根和分配命令为：

```text
set "XAR_LIVE_RUN_ID_ROOT=%LOCALAPPDATA%\Packages\PythonSoftwareFoundation.Python.3.11_qbz5n2kfra8p0\LocalCache\Local\XarCk3Acceptance\live-run-ids-v1"
py tools\ck3_live_run_id.py allocate --mod eternal-recurrence --state-root "%XAR_LIVE_RUN_ID_ROOT%"
```

若宿主使用不同的 Python 安装形态，应使用该宿主已经登记的同一持久根，不能静默回退默认根。把分配器返回的完整 JSON 保存到 attempt 根目录；不要预先创建下面命令的 `--output` 目录。

新宿主第一次使用时先运行只读资格：

```text
.xar-preview-venv\Scripts\python.exe .\repo\tools\g2_preview_eligibility.py --manifest .\operator-manifest.json --output .\runs\eligibility-RNNNN
```

资格 GREEN、旧进程完全回收并再次取得新编号后，从正式 production 入口启动一个有界连续窗口：

```text
.xar-preview-venv\Scripts\python.exe .\repo\tools\g2_preview_operator.py run --manifest .\operator-manifest.json --output .\runs\formal-RNNNN --turns 200 --timeout 810 --readiness-timeout 720
```

`RNNNN` 必须替换为刚分配的本轮编号；每轮使用新的输出目录。命令启动后不需要人工代点、推进日期或补参数。它通过正式 `native_auto_run` / `ck3_auto_turn` 循环观察、选择、提交 typed action、读取独立后置帧并在后续 turn 消费。

## 状态、暂停、停止与恢复

状态查询和受控停止在另一个 `cmd.exe` 中运行：

```text
.xar-preview-venv\Scripts\python.exe .\repo\tools\g2_preview_operator.py status --report .\runs\formal-RNNNN\formal-report.txt
.xar-preview-venv\Scripts\python.exe .\repo\tools\g2_preview_operator.py request-stop --manifest .\operator-manifest.json
```

只发送一次 stop，然后等待原 `run` 返回。成功的主动停止由以下两项共同证明：formal report 为 `operator_stop_checkpointed/operator_stopped`；operator receipt 为 `completed`、`formal_exit_code=0`。formal 顶层 `ok=false` 只表示没有跑满原 turn 上限，不代表 RED。

原进程完全回收后，重新核对 process-zero、分配新编号，并用同一 manifest、同一 state directory 和新的 output 目录恢复：

```text
.xar-preview-venv\Scripts\python.exe .\repo\tools\g2_preview_operator.py run --manifest .\operator-manifest.json --output .\runs\cold-restore-RNNNN --turns 200 --timeout 810 --readiness-timeout 720
```

`run` 会动态读取当前成对 checkpoint/driver state，先核对已执行动作的实际状态，再继续同一高层目标；不得手工回填旧哈希或盲重试已生效动作。

- checkpoint：`<state_dir>\profile\save games\xar_checkpoint.ck3`
- Agent state：`<state_dir>\native-session\driver-state.json`
- CK3 日志：`<state_dir>\profile\logs\debug.log`、`error.log`
- 停止请求：`<state_dir>\native-auto-run.stop`
- 每轮报告：命令指定的 `<output>\formal-report.txt`

每轮结束后，用分配时返回的完整 `run_id` 调用 `ck3_live_run_id.py status`，如实记录 `completed-green` 或 `completed-red`。RED、超时、未执行和证据不足分别记账。

## 实机资格证据

| 轮次 | 结果 | 关键证据 |
| --- | --- | --- |
| R878 / canonical R0009 | fresh-extraction eligibility GREEN | actor 31853、date 53282472、标准封建、WarID 150994969、ArmyID 184549472、campaign-root 双查询同帧一致；0 gameplay action、0 UI、checkpoint 未变；PID 106908 回收。报告 SHA `2974B4AA9E742701F6ED3C022363B0CD020B446521F8A4A73D72B280D1914630`。 |
| R881 / canonical R0012 | 正式非空动作与受控停止 GREEN | turn 5 提交 `move-army-184549472-to-45`；独立 native:4/revision 5 发布 `army_changed` 和目标省 45；turn 6/7 消费新状态，turn 8 继续路线；31/31、9 gameplay turns；h1435 checkpoint `CE37987A...466F5`，driver `4D5E896B...AEF96`；同一 move 重放 0；PID 206308 回收。报告 SHA `C02B991ABED16D89E7242EA3A70BDC060AF613EAF1ED187D375D350A0FD8C58F`。 |
| R882 / canonical R0013 | 新进程 cold restore GREEN | PID 104700 从 R881 精确 pair 恢复 actor/episode/WarID 和行军目标；5/5，1 gameplay turn，先消费恢复状态而未重复提交 move；最终 h1444 checkpoint `C4E665F8...84CA`、driver `845AD536...A3CC6`；进程回收。报告 SHA `214E3565C8F807B3F06DDDDE7FD0C0443336828F8FD1BC2CEDBBB2565A996329`。 |

## 支持边界

当前只支持上述 exact build、标准封建、`xar_off`、冻结 DLC/mod/load order 和包内普通 campaign continuation。已验证正式自动游玩、真实非空行军动作、独立游戏后置状态、下一循环消费、受控停止、成对 checkpoint 和新进程 cold restore。

未通过或不广告：任意用户存档/种子、1066→1453 首条整局、第二独立种子、Council 四门与正式任命、GEN-034 终局 C/D、指定自然事件、同一普通 campaign 的自然继承完整恢复、两年治理、婚姻外交质量、其他政府和 G2 广矩阵。未知强制状态保持 fail-closed；动作结果不明时先查真实状态，禁止盲重试。游戏升级不自动兼容，参见 [MCP/Native 地址定位与升级迁移评估](mcp-ck3-addressing-and-upgrade-migration.md)。
