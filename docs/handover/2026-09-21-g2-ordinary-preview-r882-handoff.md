# G2 标准封建可运行预览 / R882 交接

交接时间：2026-09-21（Asia/Shanghai）

**用户现在可以取得并启动新的 R878 GO 预览包。** ZIP 位于
`D:\ck3_mod_rewrite_process_assets\g2-preview-ordinary-r878-7d215435-stage-20260921\g2-preview-ordinary-7d215435-r878.zip`，
SHA-256 为 `05C4F9DCDC75B4211256CD8A38A642DA5C2B3EE00FB9A6E574263E5668FC5E13`；外部实机资格收据位于
`D:\ck3_mod_rewrite_process_assets\g2-preview-ordinary-7d215435-r878-qualification\g2-preview-ordinary-7d215435-r878-live-qualification.json`，
SHA-256 为 `D9D9838CC44E3BC7183356350E2895856DEA7E61A95423873B75622B72FAC8AB`，状态为
`GO_RUNNABLE_PREVIEW`。`download-manifest.json` 已绑定这两个哈希，SHA-256 为
`EF5FB58E31E78C70C035C5682397574B5D80FC5395B3E50F4698B41E70CB9B8A`。ZIP 大小
87,928,874 字节、2,239 个条目，CRC GREEN；晋升没有改写 ZIP。完整用户指南见
[`../ck3-native-ai/g2-preview-release.md`](../ck3-native-ai/g2-preview-release.md)。

这是一个有界的 ordinary campaign continuation 预览，不是 1066→1453 整局，也不是 G2 complete。权威
[`g2-requirements-v1.json`](../autonomous-agent-progress/g2-requirements-v1.json) 仍为 **1/8**，只有 G2-M1
完成；GEN-034 保持 **3/4**，Council final gate 保持 **1/4**。

## 冻结组合与支持边界

| 项目 | 冻结值 |
| --- | --- |
| CK3 | `1.19.0.6` |
| `ck3.exe` SHA-256 | `2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86` |
| Python agent/source | `7d215435da2b616a228024ac8161ae493f5477ce` |
| Native source | `8adbf94091c80900a0efadcc6fdff7802dd7c732` |
| Native DLL SHA-256 | `FC3367D90200CE08A3E7612DC22D2F6D920744E62EB83EAD62A2B9CF5A6420CF` |
| Injector SHA-256 | `67DD5FB84E7E655F9F9BD095B65629A0FA2B9280704F917E162D0B9A3877785E` |
| Production tree | `8471F6B4333D2D3D0C4DFB1BE1DFF11A586953AE7B920089DFC830164FBF0367`，86 files |
| 生命周期 | `feudal_government / xar_off / ordinary_campaign_succession / no pact` |
| Mod 顺序 | 只有 `mod/xar_autoplayer.mod` |
| DLC 配置 | `disabled_dlcs=[]`；检测到 29 个 installed descriptors，但 entitlement 未单独验收 |
| 包内起点 | R868 的 history 1347、date `53282472`、actor `31853`、防御战争 `WarID 150994969`、常备军 `Army184549472` |

已验证的范围仅为上述 exact build、冻结 DLC/mod/load order、标准封建 ordinary lifecycle 和包内固定 continuation：
正式 `native_auto_run / ck3_auto_turn` 能继续同一防御战争目标，已生效的 h1337 征兵不会重放；能执行真实 typed
行军，读取独立后续 native frame，并由下一 turn 消费；能受控停止、保存成对 checkpoint/driver state，并在新 CK3
进程中冷恢复且不重复已消费动作。

未支持、未注册或未广告：任意用户存档或种子、其他 CK3 build、其他 DLC/mod/load order、其他政府或 `xar_on`
生命周期；Council 四门与正式任命；指定自然事件；同一 campaign 的自然死亡与继承；两年治理、婚姻外交；完整
1066→1453、第二独立种子和 G2 广矩阵。未知强制状态继续 fail-closed，可能停止本次有界运行；动作结果不明时先查询
真实状态，禁止盲重提。

## 用户启动、状态、停止与恢复

R878 ZIP 内不含 CK3、个人凭据、Python 虚拟环境、Workshop cache、可变运行状态或旧日志。把 ZIP 解压到全新目录，
在该目录的普通 `cmd.exe` 中执行：

```text
py -3.13 -m venv .xar-preview-venv
.xar-preview-venv\Scripts\python.exe -m pip install --disable-pip-version-check .\repo\ck3_autonomous_player
```

把 `operator-manifest.template.json` 复制为 `operator-manifest.json`，替换其中四个绝对路径占位符：新虚拟环境的
Python、解压根、包含 `binaries\ck3.exe` 的 CK3 安装根，以及一个全新空白且可写的 state 目录。确认所有受管主机
CK3/injector 进程为零后准备状态：

```text
.xar-preview-venv\Scripts\python.exe .\repo\tools\g2_preview_operator.py prepare-state --manifest .\operator-manifest.json --sample-dir .\sample-resume
```

`prepare-state` 会执行 production-only no-launch preflight 并自动回写 rebound hashes；不要手抄哈希，也不要覆盖已有
state。每次实机前必须从**当前仓库 master 根目录**用下面的固定 state root 分配单调递增正式编号；该根在资格主机上
展开为 `C:\Users\xenoa\AppData\Local\Packages\PythonSoftwareFoundation.Python.3.11_qbz5n2kfra8p0\LocalCache\Local\XarCk3Acceptance\live-run-ids-v1`。
后继轮次从 R883 起，但必须以分配器实际结果为准：

```text
set "XAR_LIVE_RUN_ID_ROOT=%LOCALAPPDATA%\Packages\PythonSoftwareFoundation.Python.3.11_qbz5n2kfra8p0\LocalCache\Local\XarCk3Acceptance\live-run-ids-v1"
py tools\ck3_live_run_id.py allocate --mod eternal-recurrence --legacy-alias R883 --state-root "%XAR_LIVE_RUN_ID_ROOT%"
```

把返回的完整 JSON 保存到 attempt 根目录的 `live-run-identity.json`。可以预建 attempt 根目录，但传给 operator 的
`--output` 子目录必须尚不存在；R874 已证明预建 output 会被合法拒绝。全新解压先做只读资格，再从正式入口运行：

```text
.xar-preview-venv\Scripts\python.exe .\repo\tools\g2_preview_eligibility.py --manifest .\operator-manifest.json --output .\runs\eligibility-R883\operator
.xar-preview-venv\Scripts\python.exe .\repo\tools\g2_preview_operator.py run --manifest .\operator-manifest.json --output .\runs\formal-R884\operator --turns 200 --timeout 810 --readiness-timeout 720
```

每个会启动 CK3 的命令都必须单独 process-zero、单独分配正式编号；上面的 R883/R884 只是示例，不能复用。启动前把
该编号标为 `launch-started`，结束后依据真实结果标为 `completed-green` 或 `completed-red`，所有 `status` 调用也必须显式
传同一个 `--state-root`。

运行状态、暂停/停止在另一个 `cmd.exe` 中操作：

```text
.xar-preview-venv\Scripts\python.exe .\repo\tools\g2_preview_operator.py status --report .\runs\formal-R884\operator\formal-report.txt
.xar-preview-venv\Scripts\python.exe .\repo\tools\g2_preview_operator.py request-stop --manifest .\operator-manifest.json
```

本预览的“安全暂停”就是在 turn 边界请求受控停止、保存成对状态并完全回收进程；不把仍存活的 CK3 当作可恢复挂起。
只调用一次 `request-stop`，等待原 `run` 返回，确认报告、receipt 和进程库存后，再以新编号、新 output 目录启动同一
`run` 完成真正的新进程 cold restore，例如：

```text
.xar-preview-venv\Scripts\python.exe .\repo\tools\g2_preview_operator.py run --manifest .\operator-manifest.json --output .\runs\cold-restore-R885\operator --turns 200 --timeout 810 --readiness-timeout 720
```

- checkpoint：`<state_dir>\profile\save games\xar_checkpoint.ck3`
- Agent state：`<state_dir>\native-session\driver-state.json`
- CK3 日志：`<state_dir>\profile\logs\debug.log`、`error.log`、`game.log`
- 停止请求：`<state_dir>\native-auto-run.stop`
- 运行报告：命令给定的 `<output>\formal-report.txt`；同目录还会有 `operator-receipt.json`

## R874–R882 实机与修复账本

| 轮次 | 正式编号 | 结果 | 关键结论 |
| --- | --- | --- | --- |
| R874 | R0005 | harness prelaunch RED | 预建 `--output` 导致 eligibility 在启动前拒绝；无 CK3、动作或日期推进，清理 GREEN。report SHA `599055FF...F9BE`。 |
| R875 | R0006 | eligibility RED | DLL 已注入且 hello 完成，但把完整 state/profile 放在外部 D: 时，GUI 资源加载阶段未发布 semantic snapshot，721.869 秒 readiness timeout；0 动作、0 日期推进并完全回收。report SHA `092FE7B6...9C36`。 |
| R876 | R0007 | eligibility GREEN | 同一不可变旧候选改为全新 C: 解压与 state 后，139.931 秒内完成 read-only eligibility；actor/date/war/army/campaign-root 一致，0 动作并回收。report SHA `9A5EE698...FF73`。 |
| R877 | R0008 | formal RED | 第 1 turn、动作前触发 `ValueError: turn_bundle title-heir row 0 is malformed`；0 动作、0 日期推进。该 state 保守作废，不从它恢复。report SHA `9E66FE9A...5E56`。 |
| R878 | R0009 | eligibility GREEN | 新 ZIP `05C4F9DC...C5E13` 的全新解压只读资格 GREEN；195.044 秒、PID106908、0 动作，源与 prepared checkpoint 均未变，完全回收。report SHA `2974B4AA...4630`。 |
| R879 | R0010 | formal bounded continuation GREEN | 20/20 turns、9 gameplay turns，继续 WarID150994969；历史 h1337 `raise-troops-default` 保持已消费、重放 0，保存 history1381 pair 并回收。report SHA `9410CCAB...2888`。 |
| R880 | R0011 | cold-restore GREEN | 新 PID178836 从 R879 pair 恢复；5/5、2 gameplay，history1381→1390，同 actor/episode/WarID，征兵重放 0，完全回收。report SHA `F9E28F3B...0445`。 |
| R881 | R0012 | formal typed-action GREEN | turn5 唯一提交 `move-army-184549472-to-45`；`native:4 / revision 5` 独立发布 `army_changed`，turn6 强度查询与 turn7 route query 消费新移动状态，turn8 继续推进；31/31，行军重放 0，受控停止于 history1435 并回收。report SHA `C02B991A...C58F`。 |
| R882 | R0013 | cold-restore GREEN | 新 PID104700 从 R881 history1435 pair 恢复；5/5、1 gameplay，继续同一 WarID150994969，高层目标不变，行军动作重放 0；保存 history1444 pair 并完全回收。report SHA `214E3565...6329`。 |

R877 的根因是 `8adbf940` 给 turn bundle 的 title-heir row 增加了第四个
`capital_province_id`，而 succession freeze consumer 仍只接受旧三字段 exact row。`7d215435` 的 B0 修复同时接受当前
四字段和 legacy 三字段；资本字段存在时必须是正整数，而 succession expectation 仍冻结为稳定的三字段语义。它没有把
缺失/unknown 资本当作安全路线：战争策略仍使用同帧 campaign-root，缺失、无合法候选或全部不安全都 requery/RED。聚焦
agent tests normal/`-O` 为 27/27，独立复核 45/45，扩大相关集 normal/`-O` 为 280/280。修复已在
`master@7d215435da2b616a228024ac8161ae493f5477ce`；R878–R882 是修复后的真实复验。

另有一次在错误默认 state root 下分配出的重复 canonical `R0001`，execution
`c0d91426-f30c-472a-b2d2-8ec4aca68a28`、legacy alias R874。它已标记 `voided`，没有启动 CK3，也没有写入 legacy
轮次 ledger，不属于上表的正式 R874。今后所有 allocate/status 都必须显式使用本文给出的正确 state root，不能依赖默认值。

## 资格证据与当前可恢复现场

外部 GO 收据只选用足以闭合产品门的最小证据链：R878 fresh-extraction eligibility、R881 正式非空 typed action +
独立后置 + 下一 turn 消费 + 受控停止，以及 R882 新进程冷恢复。R879/R880 是保留的中间连续运行证据，不用来替代
R881 的新动作。

- R881 report：`C:\b\g2-preview-ordinary-7d215435-r878-extracted\runs\r881-formal-stop\formal-report.txt`，SHA
  `C02B991ABED16D89E7242EA3A70BDC060AF613EAF1ED187D375D350A0FD8C58F`。
- R882 report：`C:\b\g2-preview-ordinary-7d215435-r878-extracted\runs\r882-cold-restore\formal-report.txt`，SHA
  `214E3565C8F807B3F06DDDDE7FD0C0443336828F8FD1BC2CEDBBB2565A996329`。
- 最终 checkpoint：`D:\ck3_mod_rewrite_process_assets\g2-preview-ordinary-7d215435-r878-qualification\final-pair-r882\xar_checkpoint.ck3`，SHA
  `C4E665F8086D135180F9BCF5420CA0513570C4609C2181586E0FD50F90F484CA`。
- 最终 driver state：`D:\ck3_mod_rewrite_process_assets\g2-preview-ordinary-7d215435-r878-qualification\final-pair-r882\driver-state.json`，SHA
  `845AD53680B165E636EF0F351C88C52AE7E628B13873EF1B1E2D647F5F7A3CC6`。
- R882 收口时 CK3/injector 进程库存为 0，`prior_unconfirmed_action=null`，`next_round_may_restore=true`。

## 下一安全动作

1. 先把本文开头的 exact R878 ZIP 和外部 qualification 收据交给用户；不要重封包、重写 ZIP 内仍为 pending 的
   `candidate-manifest.json`，外部收据才是绑定不可变 ZIP 的 GO。
2. 下一次实机启动前重新盘点所有受管主机并取得单实例所有权；从正确 state root 分配 R883 或更高的实际空闲编号。
   若从 R882 pair 继续，先查询 Army184549472/WarID150994969 的真实状态；不得再次提交已消费的 move，之后从同一高层
   防御战争目标继续并保持 checkpoint 配对。
3. 产品关键链恢复到 Council 四门（already-councillor、guest、pending interaction、replacement fireability）及其正式
   query → policy → typed action → 独立后置 → 下一 turn 消费；四门未闭合前继续不注册、不广告。
4. 无冲突工作继续 GEN-034-D creation-time source-bound 六项证书、指定自然事件/自然继承、两年治理和婚姻外交最低闭环。
   不得用本预览 GO、日期推进或单一 fixed continuation 提升 G2 的 1/8。

## 读取顺序与硬约束

1. 本文、[预览包交付页](../ck3-native-ai/g2-preview-release.md) 和包内 `QUICKSTART.md`；
2. [G2 权威合同](../autonomous-agent-progress/g2-requirements-v1.json)；
3. R878/R881/R882 closed ledgers、formal reports、operator receipts 和外部 qualification；
4. [`2026-09-17-g2-ordinary-war-r795-handoff.md`](2026-09-17-g2-ordinary-war-r795-handoff.md) 了解 R804–R847 既有链；
5. Council 专题交接和 GEN-034 合同。

继续遵守：全受管环境同时只允许一个 CK3；禁止 merge commit、强推共享 master、运行中改加载文件、盲重提未确认动作、
吞掉 RED，或把可运行预览包冒充整局、双种子、“比较正常”或 G2 complete。已封存 ZIP、资格收据、最终 pair、报告和日志
属于交付证据，不随临时 worktree 清理。
