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

> **冻结包说明：**R802 ZIP 内的 `QUICKSTART.md` 和
> `repo\tools\g2_preview_operator.py` 都是 `9bacc5af` 的不可变字节；包内
> QUICKSTART 仍记录最初通过资格验收时的 PowerShell 等价流程。当前这份
> 外部指南只在命令语法上覆盖包内 QUICKSTART，提供经 no-launch 实测的纯
> `cmd.exe` / CPython 步骤；它不修改 ZIP、不把 R802 冒充成最新 master，也
> 不允许用 master 上较新的 operator 覆盖包内脚本。

把 ZIP 解压到新目录，在该目录打开普通命令提示符。资格主机使用 CPython 3.13.2；按包内声明安装运行依赖：

```text
py -3.13 -m venv .xar-preview-venv
.xar-preview-venv\Scripts\python.exe -m pip install --disable-pip-version-check .\repo\ck3_autonomous_player
```

复制 `operator-manifest.template.json` 为 `operator-manifest.json`，替换四类占位符：`<ABSOLUTE_PYTHON_EXE>`、`<ABSOLUTE_EXTRACTED_PACKAGE_ROOT>`、包含 `binaries\ck3.exe` 的 `<ABSOLUTE_CK3_INSTALL_ROOT>`，以及全新空目录 `<ABSOLUTE_NEW_EMPTY_STATE_DIRECTORY>`。取得 CK3 单实例所有权并确认所有受管主机无存活 CK3 后运行：

```text
.xar-preview-venv\Scripts\python.exe .\repo\tools\g2_preview_operator.py prepare-state --manifest .\operator-manifest.json --sample-dir .\sample-resume
```

R802 包内的旧 operator 会复制成对 checkpoint/driver state、把环境绑定迁移到本机并执行零启动预检，但它早于自动回写 manifest 的实现。命令成功后，立即用同一个包内虚拟环境执行下面的确定性同步；该命令只读取 `<state_dir>\ordinary-seed-rebind-v1.json` 的两个 `target_sha256`，经临时文件替换 `operator-manifest.json`，不启动 CK3：

```text
.xar-preview-venv\Scripts\python.exe -c "import json,pathlib; p=pathlib.Path(r'.\operator-manifest.json'); m=json.loads(p.read_text(encoding='utf-8-sig')); r=json.loads((pathlib.Path(m['state_dir'])/'ordinary-seed-rebind-v1.json').read_text(encoding='utf-8-sig')); m['environment_sha256']=r['environment']['target_sha256']; m['driver_state_sha256']=r['driver_state']['target_sha256']; t=p.with_name(p.name+'.sync.tmp'); t.write_text(json.dumps(m,indent=2,ensure_ascii=False)+'\n',encoding='utf-8'); t.replace(p)"
.xar-preview-venv\Scripts\python.exe -c "import json,pathlib; p=pathlib.Path(r'.\operator-manifest.json'); m=json.loads(p.read_text(encoding='utf-8-sig')); r=json.loads((pathlib.Path(m['state_dir'])/'ordinary-seed-rebind-v1.json').read_text(encoding='utf-8-sig')); assert m['environment_sha256']==r['environment']['target_sha256']; assert m['driver_state_sha256']==r['driver_state']['target_sha256']; print('manifest rebind hashes synchronized')"
```

不要手抄或猜测哈希，也不要手改存档或 driver state。`prepare-state` 拒绝覆盖已有 state；若上述同步或断言失败，停止并保留现场，不得进入 eligibility 或正式运行。

这一步已于 2026-09-21 对精确 R802 ZIP 的全新解压目录完成 no-launch 等价验证：源 checkpoint 字节未变，manifest 的环境哈希 `A15A64F260674CD6EA0720301129E20B62B2A990202EA4F4DC7C108B293B36FB` 与 driver 哈希 `4BA00A2C6A28AD3ACB81C4869AC30498B33BDCE665959D2BC46EF6207AB8E1F6` 分别等于 rebind receipt 的两个 target，receipt 与 preflight 都记录 `ck3_launch_attempted=false` 且进程库存为空；receipt SHA-256 为 `C2576D2AF7B57B294729F0319C70CC5E5096FEB74946511E54B341DB30C690D8`，preflight report SHA-256 为 `1F4EA5C524F090B7C56AB9A7F9BD4C170A1D25C12A91FA762F5594E45A38630E`。这只验证 cmd/CPython 准备步骤与原资格流程等价，不新增能力、不替代 R804–R806 实机资格。

## 启动自动游玩

每个会启动 CK3 的 attempt 都必须在静态/preflight 已通过、且再次确认全机无 CK3/injector 进程后，先从**当前仓库 master 根目录**分配一个机器与 mod 作用域内的正式编号。R802 冻结包早于该分配器，因此不要从 ZIP 内寻找或复制它：

```text
py tools\ck3_live_run_id.py machine
py tools\ck3_live_run_id.py allocate --mod eternal-recurrence
```

把第二条命令返回的完整 JSON 原样保存为该 attempt artifact 根目录的 `live-run-identity.json`；其中 `run_id` 是正式编号。R802 operator 的 `--output` 指向该 artifact 根目录下尚不存在的 `operator` 子目录，这样分配记录会在启动前存在，又不会触发 operator 的“一次性输出目录已存在”拒绝。以下命令从 ZIP 解压根开始；`<当前仓库master根目录>` 只替换为本机当前仓库的绝对路径：

```text
set "XAR_R802_ROOT=%CD%"
mkdir "%XAR_R802_ROOT%\runs\eligibility-attempt"
cd /d <当前仓库master根目录>
py tools\ck3_live_run_id.py allocate --mod eternal-recurrence > "%XAR_R802_ROOT%\runs\eligibility-attempt\live-run-identity.json"
cd /d "%XAR_R802_ROOT%"
```

随后回到 ZIP 解压根目录，做两个 paused frame 的只读资格验收：

```text
.xar-preview-venv\Scripts\python.exe .\repo\tools\g2_preview_eligibility.py --manifest .\operator-manifest.json --output .\runs\eligibility-attempt\operator
```

资格 GREEN 且旧进程完全回收后，从正式 production 入口启动：

为正式运行重复上述 process-zero 检查，再执行以下分配并启动：

```text
mkdir "%XAR_R802_ROOT%\runs\formal-attempt"
cd /d <当前仓库master根目录>
py tools\ck3_live_run_id.py allocate --mod eternal-recurrence > "%XAR_R802_ROOT%\runs\formal-attempt\live-run-identity.json"
cd /d "%XAR_R802_ROOT%"
.xar-preview-venv\Scripts\python.exe .\repo\tools\g2_preview_operator.py run --manifest .\operator-manifest.json --output .\runs\formal-attempt\operator --turns 20 --timeout 810 --readiness-timeout 720
```

每轮结束后，从 `live-run-identity.json` 读取完整 `run_id`，再从当前仓库 master 根目录用 `tools\ck3_live_run_id.py status` 记录 `completed-green` 或 `completed-red`；真实 RED 不得标成 GREEN。一次 attempt 的目录名不得复用，失败重跑必须新建目录并重新分配编号。

包内样本从 WarID 5 终局后的和平 checkpoint 开始。R805 实际运行经公共查询选择新的合法战争、typed 宣战、独立观察 WarID 25、下一 turn 消费、征兵、行军和战斗；旧 `offer-white-peace-5` 没有重放。

## 状态、受控停止与恢复

安全暂停与受控停止使用同一个操作：智能体会在安全 turn 边界保存成对 checkpoint/driver state，再退出 CK3；不支持把仍存活的 CK3 进程当作可恢复的“挂起”。恢复必须启动新进程。

在另一个普通命令提示符中进入 ZIP 解压根目录。状态命令显式指向本轮报告；安全暂停/停止只调用一次，然后等待原 `run` 命令返回：

```text
.xar-preview-venv\Scripts\python.exe .\repo\tools\g2_preview_operator.py status --report .\runs\formal-attempt\operator\formal-report.txt
.xar-preview-venv\Scripts\python.exe .\repo\tools\g2_preview_operator.py request-stop --manifest .\operator-manifest.json
```

原 `run` 命令返回后再次执行 `status`，确认返回 JSON 的 `ck3_processes=[]`，并按 operator receipt 确认 injector 已回收。随后再次执行 process-zero 检查，再分配新正式编号并冷恢复同一目标：

```text
mkdir "%XAR_R802_ROOT%\runs\cold-restore-attempt"
cd /d <当前仓库master根目录>
py tools\ck3_live_run_id.py allocate --mod eternal-recurrence > "%XAR_R802_ROOT%\runs\cold-restore-attempt\live-run-identity.json"
cd /d "%XAR_R802_ROOT%"
.xar-preview-venv\Scripts\python.exe .\repo\tools\g2_preview_operator.py run --manifest .\operator-manifest.json --output .\runs\cold-restore-attempt\operator --turns 5 --timeout 810 --readiness-timeout 720
```

`run` 会从 `<state_dir>` 当前成对 checkpoint/driver state 动态取得哈希并执行 no-launch preflight，不需要手工回填 manifest 哈希。

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
