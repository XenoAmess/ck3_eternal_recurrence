# G2 标准封建预览：PRV-006 已交付与 R888 历史资格

**当前窄范围可运行预览：GO（2026-09-22，PRV-006）。** [冻结 ZIP](Z:/ck3_mod_rewrite_process_assets/g2-preview-ordinary-cad5518-20260922/release/g2-preview-ordinary-h1662-cad5518-prv006.zip) SHA-256 `7503E5D92703F29EA9BF72009FB24A108EFEE914AE6DDE42BB1135D1A6952803`；以下 R888/PRV-005 的 NO-GO 段落是历史快照，不是本包的启动指南。PRV-006 限 exact CK3 1.19.0.6（EXE SHA `2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86`）、agent `cad551895476f3612c33915955cf987c6c0fdc18`、包内原始 h1662 标准封建存档、`xar_off`、仅 `mod/xar_autoplayer.mod`、冻结 DLC 描述与配置；不支持任意存档/种子或完整整局。稳定目录的 release 清单、资格收据及操作指南绑定精确 ZIP，原始报告单独保留；CK3 本体不在包内。

同包 R0067 fresh 只读资格 GREEN、R0068 正式 60/60（turn47 唯一 typed 征兵，独立 ArmyID 变化、turn48/49 消费）、R0069 正式 stop 成对 checkpoint/全树回收、R0070 从此 pair 新 PID cold restore 20/20 且不重复动作。R0069 还自然遇到 `grant_vassal_interaction`，正式 typed 拒绝使 pending 独立清空并在下一 turn 消费。分开的 R0065 最后安全 pair 聚焦复验 R0071：自然 `stress_threshold_special.1001` 一次 typed 选择、独立 stress 100→64、事件清空、下一 turn 消费；这不是 R0069→R0070 同一轨迹。原报告 SHA/成对存档与轮次详情见稳定目录外部资格清单。议会仅 1/4 且公共能力 OFF，治理 R0066 建设 ACK 后物质查询 RED，战争终局/自然继承/整局与第二独立种子未完成；G2 权威仍 2/8。未知范围内强制状态仍须停机留 RED，不承诺无人值守跨全部自然事件。

## 历史记录：R888 与 PRV-005（不可作为当前包操作指南）

**当前可独立启动的用户交付：NO-GO（2026-09-22）。** 下文 R888 是冻结的历史实机资格记录，不是当前默认用户包：原 ZIP 缺包内 canonical run-ID 分配器，无法独立执行文内完整启动/收口步骤。不能修改该冻结 ZIP 或沿用其外部 GO 收据为新包盖章。h1380 自包含候选 R0053 40/40 技术 GREEN 却无非空 typed 动作；h1662 旧 b7 ZIP R0056 有 typed 征兵却在 turn58 战争 RED；master `fadc2e5` 的 PRV-004 ZIP 在 R0058 60/60 有真实征兵却 R0059 冷续遇 `grant_vassal_interaction` 未分类 B0。精确 `master@3da54dc` 的 PRV-005 ZIP SHA `F5EB7657...B282CD` 在 R0062 60/60 有正式动作闭环、R0064 受控停止且成对 checkpoint，但 R0065 从该 pair 的不同 PID 冷恢复第17 turn 遇自然九选项事件 `stress_threshold_special.1001`，现有正式事件消费者不支持并 RED，未盲选。冷恢复进程和前16轮不替代整个使用范围可连续运行；新修复制品仍须事件合同及受影响实机复验。权威 G2 是 `2/8`（仅 M0/M1 complete），预览切片不新增正式里程碑。

截至 2026-09-21，R888 原本按当时限定证据完成 fresh-extraction 只读资格、生产循环、受控停止和新进程 cold restore，并由外部收据标为 `GO_RUNNABLE_PREVIEW`。以下记录保留其原始制品哈希与证据映射供审计；在新的自包含 ZIP 完成全部产品门以前，不应把其中命令当作当前可交付操作指南。

## 获取与冻结组合

- ZIP：`D:\ck3_mod_rewrite_process_assets\g2-preview-ordinary-r888-d559faa6-stage-20260921\g2-preview-ordinary-d559faa6-r888.zip`
- ZIP SHA-256：`F7FAC0F56AB438548F8385C2901BFABE89BCBEEA840E6B46A3C7D1779118E9F6`
- 大小：87,934,382 字节；2,239 个条目；ZIP CRC GREEN。
- 包内 `candidate-manifest.json` SHA-256：`255897B6B29E4F4801C1998153464B55E817530526EA0917AE848A1C88FE4E6A`。
- 外部 GO 清单：同 stage 的 `download-manifest.json`，SHA-256 `6EFE017F50FA0E9F002F9DC98EB5C8625BD6985C9A179D4D29DB98D204F1A58E`。
- 外部实机资格收据：`D:\ck3_mod_rewrite_process_assets\g2-preview-ordinary-r888-d559faa6-qualification\g2-preview-ordinary-d559faa6-r888-live-qualification.json`，SHA-256 `0A74F8226407CC087A73ECB84B29FC80A3E3B4B3E821CBEA2EEE431B343E2757`。

包内 candidate manifest 保留封包时的 `NO_GO_PENDING_EXTRACTED_BUNDLE_LIVE_SMOKE` 状态；外部 GO 收据绑定精确 ZIP 哈希，晋升没有改写 ZIP。包中不含 CK3 本体、个人凭据、Python 虚拟环境、Workshop cache、可变运行状态或历史运行日志。

> **R888 可移植性更正（2026-09-21）：**上述冻结 ZIP 本身没有包含 `tools/ck3_live_run_id.py`，所以原文要求另备当前 master checkout 才能分配/收口 canonical run ID，并不满足自包含操作要求。R888 的 ZIP、哈希和既有实机资格保持原样；不能原地补文件。当前源码已把分配器纳入下一候选包，并把下述命令改为包内入口。新的 ZIP 仍须重新打包并完成独立 fresh-extraction 实机资格后，才能取代 R888；本次静态修复本身不是新包资格。

| 项目 | 冻结值 |
| --- | --- |
| CK3 | `1.19.0.6` |
| `ck3.exe` SHA-256 | `2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86` |
| Python agent/source | `d559faa6d7094cc953f238ef03e9e491cd7e7027` |
| Native source | `8adbf94091c80900a0efadcc6fdff7802dd7c732` |
| Native DLL SHA-256 | `FC3367D90200CE08A3E7612DC22D2F6D920744E62EB83EAD62A2B9CF5A6420CF` |
| Injector SHA-256 | `67DD5FB84E7E655F9F9BD095B65629A0FA2B9280704F917E162D0B9A3877785E` |
| 初始 paired state | history 1380、date `53282688`、actor `31853`、WarID `150994969`、ArmyID `184549472`、native rally Province `8750` |
| 政体/生命周期 | `feudal_government` / `ordinary_campaign_succession` |
| 游戏规则 | `xar_enabled=xar_off`，`ordinary_campaign_no_pact=true` |
| Mod 加载顺序 | 只有 `mod/xar_autoplayer.mod` |
| DLC | `disabled_dlcs=[]`；冻结配置见包内 `config/dlc_load.json` |
| Production mod tree | `8471F6B4333D2D3D0C4DFB1BE1DFF11A586953AE7B920089DFC830164FBF0367`，86 个文件 |

R888 有意复用上述 exact-build native DLL/injector；`d559faa6` 增加的是 Python 侧的 stationary current-rally contact-horizon 策略与恢复回归，之后的无关 native 源码变化没有进入本制品。

## 下一候选的一次性准备（尚待重新打包/资格）

先选择一个实际存在、可写且空间足够的非 `C:` 盘根目录。ZIP 解压根、venv、canonical run-ID 持久状态、游戏/agent state、每轮 runs 输出以及 `TEMP`/`TMP` 必须全部实际落在这个非 `C:` 根下；禁止用解析回 `C:` 的 junction、符号链接或环境变量绕过。以下仅以 `Z:\ck3-g2-preview` 为例，把下一候选 ZIP 解压到 `Z:\ck3-g2-preview\package`，并在该解压根打开普通 `cmd.exe`：

```text
set "XAR_PREVIEW_ROOT=Z:\ck3-g2-preview"
set "XAR_PREVIEW_PACKAGE=%XAR_PREVIEW_ROOT%\package"
set "XAR_PREVIEW_PYTHON=%XAR_PREVIEW_ROOT%\venv\Scripts\python.exe"
REM 仅从未登记过的新宿主使用下一行的新空 ledger；已有宿主见下文。
set "XAR_LIVE_RUN_ID_ROOT=%XAR_PREVIEW_ROOT%\live-run-ids-v1"
set "TEMP=%XAR_PREVIEW_ROOT%\temp"
set "TMP=%XAR_PREVIEW_ROOT%\temp"
mkdir "%TEMP%"
mkdir "%XAR_PREVIEW_ROOT%\runs"
cd /d "%XAR_PREVIEW_PACKAGE%"
py -3.13 -m venv "%XAR_PREVIEW_ROOT%\venv"
"%XAR_PREVIEW_PYTHON%" -m pip install --disable-pip-version-check .\repo\ck3_autonomous_player
```

复制 `operator-manifest.template.json` 为 `operator-manifest.json`，只替换模板已有的四类占位符：

- `<ABSOLUTE_PYTHON_EXE>`：刚创建的 `%XAR_PREVIEW_ROOT%\venv\Scripts\python.exe` 展开后的绝对路径；
- `<ABSOLUTE_EXTRACTED_PACKAGE_ROOT>`：`%XAR_PREVIEW_PACKAGE%` 展开后的绝对路径；
- `<ABSOLUTE_CK3_INSTALL_ROOT>`：包含 `binaries\ck3.exe` 的 CK3 根；
- `<ABSOLUTE_NEW_EMPTY_STATE_DIRECTORY>`：全新且为空的 `%XAR_PREVIEW_ROOT%\state` 展开后的绝对路径。

JSON 中必须填写展开后的绝对路径，不要把 `%...%` 变量文字原样写进去。不要改模板中的版本、哈希、角色、战争、军队、管道或 preview action。确认所有受管主机都没有存活的 CK3 后运行：

```text
"%XAR_PREVIEW_PYTHON%" .\repo\tools\g2_preview_operator.py prepare-state --manifest .\operator-manifest.json --sample-dir .\sample-resume
```

`prepare-state` 会复制成对 checkpoint/driver state、绑定本机环境、执行 production-only no-launch preflight，并自动把实际 environment/driver 哈希回写 manifest。不要手抄哈希，不要手改存档或 driver state；该命令拒绝覆盖已有 state。

上面的新空 `%XAR_PREVIEW_ROOT%\live-run-ids-v1` **只适用于从未登记过的新宿主**。已有受管宿主不得因换 ZIP、venv 或路径而从空 ledger 重新分配 `R0001`：

- 若唯一权威 ledger 已在合规非 `C:` 盘，`XAR_LIVE_RUN_ID_ROOT` 必须继续指向它，不要求把它塞进本次 preview root；
- 若旧权威 ledger 实际在 `C:`，先停止所有 allocator writer，完整迁移 counter、allocation history 和 status history 到一个非 `C:` 根，逐文件核验后让所有调用方一次性切到新根，并停止使用旧根；
- 禁止只迁移 `counter.json`，禁止把旧/新两份同时作为可写 root，也禁止为了方便新建空 root。迁移后的第一次 allocate 必须接续原 `last_sequence`。

## 启动自动游玩

在本项目受管环境，每次会启动 CK3 的 attempt 都必须先确认 process-zero，并用包内分配器取得正式编号。继续在 ZIP 解压根的 `cmd.exe` 中运行；不再依赖外部仓库 checkout，也不允许回退到 `%LOCALAPPDATA%` 等可能实际位于 `C:` 的默认根：

```text
"%XAR_PREVIEW_PYTHON%" .\repo\tools\ck3_live_run_id.py allocate --mod eternal-recurrence --state-root "%XAR_LIVE_RUN_ID_ROOT%"
```

把分配器返回的完整 JSON 保存到 `%XAR_PREVIEW_ROOT%\runs` 下对应 attempt 的旁路收据；不要预先创建下面命令的 `--output` 目录。此处的 `XAR_LIVE_RUN_ID_ROOT` 必须按上一节选择新宿主空根或已有宿主唯一权威/已核验迁移根，不能静默回退默认根。

新宿主第一次使用时先运行只读资格：

```text
"%XAR_PREVIEW_PYTHON%" .\repo\tools\g2_preview_eligibility.py --manifest .\operator-manifest.json --output "%XAR_PREVIEW_ROOT%\runs\eligibility-RNNNN"
```

资格 GREEN、旧进程完全回收并再次取得新编号后，从正式 production 入口启动一个有界连续窗口：

```text
"%XAR_PREVIEW_PYTHON%" .\repo\tools\g2_preview_operator.py run --manifest .\operator-manifest.json --output "%XAR_PREVIEW_ROOT%\runs\formal-RNNNN" --turns 40 --timeout 810 --readiness-timeout 720
```

`RNNNN` 必须替换为刚分配的本轮编号；每轮使用新的输出目录。命令启动后不需要人工代点、推进日期或补参数。它通过正式 `native_auto_run` / `ck3_auto_turn` 循环观察、选择、提交 typed action、读取独立后置帧并在后续 turn 消费。

## 状态、暂停、停止与恢复

状态查询和受控停止在另一个 `cmd.exe` 中运行：

```text
"%XAR_PREVIEW_PYTHON%" .\repo\tools\g2_preview_operator.py status --report "%XAR_PREVIEW_ROOT%\runs\formal-RNNNN\formal-report.txt"
"%XAR_PREVIEW_PYTHON%" .\repo\tools\g2_preview_operator.py request-stop --manifest .\operator-manifest.json
```

只发送一次 stop，然后等待原 `run` 返回。成功的主动停止由以下两项共同证明：formal report 为 `operator_stop_checkpointed/operator_stopped`；operator receipt 为 `completed`、`formal_exit_code=0`。formal 顶层 `ok=false` 只表示没有跑满原 turn 上限，不代表 RED。

原进程完全回收后，重新核对 process-zero、分配新编号，并用同一 manifest、同一 state directory 和新的 output 目录恢复：

```text
"%XAR_PREVIEW_PYTHON%" .\repo\tools\g2_preview_operator.py run --manifest .\operator-manifest.json --output "%XAR_PREVIEW_ROOT%\runs\cold-restore-RNNNN" --turns 40 --timeout 810 --readiness-timeout 720
```

`run` 会动态读取当前成对 checkpoint/driver state，先核对已执行动作的实际状态，再继续同一高层目标；不得手工回填旧哈希、复用旧 output 目录或盲重试已生效动作。

- checkpoint：`<ABSOLUTE_NEW_EMPTY_STATE_DIRECTORY>\profile\save games\xar_checkpoint.ck3`
- Agent state：`<ABSOLUTE_NEW_EMPTY_STATE_DIRECTORY>\native-session\driver-state.json`
- CK3 日志：`<ABSOLUTE_NEW_EMPTY_STATE_DIRECTORY>\profile\logs\debug.log`、`error.log`
- 停止请求：`<ABSOLUTE_NEW_EMPTY_STATE_DIRECTORY>\native-auto-run.stop`
- 每轮报告：命令指定的 `<output>\formal-report.txt`

这里的 `<ABSOLUTE_NEW_EMPTY_STATE_DIRECTORY>` 是模板占位符所代表的实际目录，不要把尖括号文字原样用于命令。每轮结束后，用分配时返回的完整 `run_id` 调用同一包内脚本，如实记录 `completed-green` 或 `completed-red`：

```text
"%XAR_PREVIEW_PYTHON%" .\repo\tools\ck3_live_run_id.py status --run-id <FULL_RUN_ID> --mod eternal-recurrence --status completed-green --reason "bounded preview completed" --state-root "%XAR_LIVE_RUN_ID_ROOT%"
```

RED、超时、未执行和证据不足分别记账；不要把它们改写成成功。

## 实机资格证据

下表同时给出包内 legacy round 和单调 canonical run 的映射；canonical 前缀均为 `xenoamess-full-tower-eb9d2c1186--eternal-recurrence--`。

| Legacy / canonical | 结果 | 关键证据 |
| --- | --- | --- |
| R888 / R0019 | fresh-extraction eligibility `GREEN_READ_ONLY` | 从 h1380/date `53282688` 成对状态冷启动；actor 31853、标准封建、WarID 150994969、ArmyID 184549472、native rally 8750 与 manifest 一致；双 managed query 同 revision，0 UI、0 gameplay action、未人工推进日期，源存档与 prepared checkpoint 未变；PID 34700 回收，postflight process-zero。报告 SHA `EC3E9D800F8FC5A548D68DACE524629D287CEDB9A688865A0FC3ADAE28130E0A`，closed-ledger SHA `9E4950BA914265952365892EF103D4F6E8D1C376A878CC66B34C43179396DC69`。 |
| R890 / R0021 | 受控停止与 paired checkpoint GREEN | 正式入口收到一次 stop，report 为 `operator_stop_checkpointed/operator_stopped`，receipt 为 `completed` / exit 0；PID 156664 回收。落盘 h1459/date `53282904` checkpoint `09882AB1...6ED6` 与 driver `CAF2E59A...147`。报告 SHA `1956FB1D31499AFA29287BB58514B3495B9E11E67ED20271DA872F403A1EB60A`，receipt SHA `CBDC30BB23BADC2CC655BE99EB6EB2BB521D6BD8596D825B4396FAAB2637D3B`，closed-ledger SHA `C3C625EF515CC3573CAA8F4274FE4F67885A030FF2CCB90BE229B000C8544C32`。 |
| R891 / R0022 | 新进程 cold restore GREEN | 新 PID 79556 精确读取 R0021 的 checkpoint/driver pair，保持 actor/episode/WarID/ArmyID 和同一高层防御目标；20/20 turns（12 query、8 gameplay、2 visible），每轮先拒绝 overmatch 下不安全的 Province 45/46 路线，再为当前 rally 8750 读取 fresh complete-scope horizon，仅用 proof-bound step 将日期 `53282904 → 53282952`，后续 turn 继续消费而未重放旧动作；无 blocker，最终 h1484 checkpoint `7121CCE3...386F` 与 driver `E9B7730E...4674`，进程回收。报告 SHA `B4F6B30FC98652E0544E7531977A0090A664803FC4530CAA5F7B4E55F7F189B1`，receipt SHA `28B034BF2595A9E81E51E9BECB2728E1CC46E6D7E3B7223542F547D996BCB3B5`，closed-ledger SHA `72FDA1DF0325212752D636E078BB4A8CAF2C91B54A7CA52C0802A36A16E629EE`。 |

资格收据将 `eligibility_green`、`formal_production_entry`、`nonempty_strategy_action`、`independent_postcondition`、`next_turn_consumed`、`controlled_stop_checkpointed`、`cold_restore_new_process`、`same_high_level_goal`、`no_repeat_consumed_action` 和 `single_instance_cleanup` 全部记录为 `true`。

## 支持边界

当前只支持上述 exact build、标准封建、`xar_off`、冻结 DLC/mod/load order，以及包内 R0018 h1380 普通 campaign continuation。它不是“任意存档自动玩”发行版。已验证正式自动游玩循环、overmatch 下不安全 player-held-county 路线拒绝、fresh complete-scope stationary current-rally horizon、proof-bound 一日留守推进、独立后置帧、下一循环消费、受控停止、成对 checkpoint 和新进程 cold restore。

R0018 在 h1380 后的 history 1381..1392 是未持久化观测尾，恢复时必须回滚；其中 Province 45/46 horizon 不得作为新一轮证明复用。当前 native rally 的一日留守也只有在本帧 fresh、完整敌军 scope 的 contact horizon 明确证明后才合法；不能退化为 generic life-advance。

未通过或不广告：任意用户存档/种子、1066→1453 首条整局、第二独立种子、Council 四门与正式任命、GEN-034 终局 C/D、指定自然事件、同一普通 campaign 的自然继承完整恢复、两年治理、婚姻外交质量、其他政府、`xar_on` 生命周期和 G2 广矩阵。未知强制状态保持 fail-closed，可能让有界预览停止；动作结果不明时先查真实状态，禁止盲重试。游戏升级不自动兼容，参见 [MCP/Native 地址定位与升级迁移评估](mcp-ck3-addressing-and-upgrade-migration.md)。
