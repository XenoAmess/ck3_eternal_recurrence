# R08 c/d writer：下一次 Root 独占 external-debugger 专场

当前仅为可执行候选，未启动 observer、未发 SDK、未附加游戏、未构建。c/d writer PC 仍未取得；军事已付金额、同次 NET、payer/cadence 均未闭。旧 R204 的 raw4/context+4A0 与 c/d/context+28/+30 是独立路径。

## 最短现有执行入口

使用 `ROOT-CONFIG.template.json` 填 **新场** actual source commit、原始 fresh snapshot/cash 路径、独立期望身份和一个尚不存在的 watch 目录。不得复用 R204 的 PID/context/window/epoch。配置的脚本只生成 argv，不授予容量、attach 或游戏推进资格。

```text
D:/workspace/ck3_eternal_recurrence/tools/.venv/Scripts/python.exe -B -O -X utf8 build_card.py --config ROOT-CONFIG.actual.json --output ROOT-ARGV.actual.json
```

Root 依次运行该卡的 `prepare_argv`（真实既有 `prepare_writer_admission.py --prepare-only`），成功后读取新 `ADMISSION.actual.json` 的 **`argv` 数组**。不要把数组拼成 shell 字符串。实际 argv 为：

```text
C:/ck3-war-episode04-research-20261004-a01/maintenance-writer-cold-a01/build-a07/maintenance_writer_cold_observer.exe
  --enable-ck3-12004-data-watch
  --fixture-meta NEW/CURRENT-RAW-ADMISSION.meta.txt
  --timeout-ms 30000
  --raw NEW/writer.raw.ndjson
  --ready NEW/writer.ready.json
  --expected-hits 128
  --machine-id desktop-3fevhd2-1c74096080
```

这恰好是稳定的 14 项 native argv（含 EXE）。build-a07 的 exact source 已获历史冷资格与本机 SYSTEM 路径资格；本包只核目录/小回执，未重 hash 或执行 EXE。Root 实际 prepare 会复核原生产器、两 EXE 和 SYSTEM pins。**不追加后来源码才有的 `--capture-known-copy-caller`**。现固定 DR0=2C0、DR1=2C8、DR2=28、DR3=30，没有重定向或仅 c/d 开关；128 是全四槽累计，不是每槽 128。

## 新场必需准入与触发

1. Root 当次实际容量、独占进程/现场和明确 external-debugger 许可；旧 gate 只证明具体项目 EXE 的历史 SYSTEM 设置，旧配额不续期。该场不能仍是 `external_debugger_allowed=false`。禁止同时运行 R06 DR observer 或任何其他 debugger；已有 DR/TF 会在 attach 前拒绝，不抢占。
2. 当次 native source/build/EXE exact4 资格及玩家历史身份已核，map-ready、alive、paused、无待处理原生 modal。原游戏状态与 normal checkpoint 保留，正常玩法/原生 one-day clock，不修改 raw 字段、军费或角色。
3. 独立 fresh snapshot 后，以其 revision 发既有 cash query（`payment_sampling='query'`）。已有受控窗口不得 enable/clear；若 OFF，Root 按原采样合同仅 enable 一次并独立 readback 后重新取得配对 snapshot/cash。cash 必须同时有 `current_raw_context_v1` ready/stable、journal installed/failure0/read_complete、ON/idle/active0、same-owned-no-load、window/epoch，且独立 Root PID/create/gen/actor/revision/native/date/episode 全等。before 工具必须 `ck3_take_snapshot`，cash 工具必须 `ck3_query_war_cash_current_resources_private_v1`。
4. 预先填好实际 native research observation plan 的窗口、终止条件和未知语义，运行：`python -B tools/native_research_plan.py check PLAN --for-observation --output NEW-CHECK.json`。它校验计划，不授权 attach；不向 init 传 EXE 以免重复整 EXE hash。准备可在暂停态充分完成，不塞进旧 3 秒子进程窗口。
5. Root 用 `Popen(ADMISSION['argv'], stdout=..., stderr=..., creationflags=CREATE_NO_WINDOW)` 持有 handle；启动有 create-only claim，启动结果未知时不重投。只有当前 Popen 仍活着且实际新 ready 文件 **`ready is True`、`type(armed_thread_count) is int and >0`** 才可继续。ready 失败、迟到或身份/窗口变化均不 Resume、不重新 Arm。
6. 目标是取得 **当前 payer context 的 c/d 实际 write**。最小自然触发是既有 one-day sentinel 的唯一 Resume 经过一个预先声明的自然结算候选机会；只用现有 Root exact-clock 守卫。上一 R204 retained seq3 确有个人 NET ADD，不能将它的 admission/snapshot 日期推广成 c/d writer 日期或固定月结 cadence。若选同普通 checkpoint 重放，应先离线按实际保留记录指定机会，再 fresh 入场；不能等到 c/d 阳性才延长或重启 observer。
7. observer 最多 30 秒 / 128 累计 slot hits。Root 等其自然终态并保留 pending-event/restore/detach 证据；禁止强杀已 attach watcher。`timeout` / `hit_limit_partial` 常返回 1，不能只靠 exit1 断言恢复失败；消费 terminal `cleanup_complete/restored/detached=true`、`pending_event/process_exited=false`、每个 live generation 原 DR 全六值 readback、thread admission complete。失败不再次 attach，不在 debugger 未 detach 时关闭游戏。
8. observer 退出且 cleanup 处理完后，Root 读同 run fresh cash/payment journal，独立固定 NET/payer 原件。观察时段和同次 invocation 分开：watch QPC 与 admission date 不提供 native payment event token，不能仅按接近时间把 c/d 与某 NET 拼接。

## 消费与可复用新增薄选择器

运行卡的 `consume_argv`，即既有实际 consumer：

```text
python -B -O ck3_autonomous_player/native_bridge/research/maintenance_writer_cold_12004/consume_writer_actual.py --repo REPO --raw NEW/writer.raw.ndjson --admission NEW/ADMISSION.actual.json --cash-response ORIGINAL-CASH --before-response ORIGINAL-BEFORE --output NEW/ACTUAL-WRITERS.json
python -B -O select_cd_writers.py --result NEW/ACTUAL-WRITERS.json --result-sha256 ACTUAL-RESULT-SHA --output NEW/C-D-WRITERS.actual.json
```

选择器只读取已 pin 的原消费结果，不替代 `bind_inputs/project`，不读进程/EXE/原 raw，不删除 a/b。c/d 为 slot2/3 且 offset28/30；保留相同值写、raw_line、线程 generation、寄存器、RIP_after、原 JSON pointer。清理或 thread/event 证据 partial 时保留候选但不授 source-ready；foreign PC 不硬映射为 CK3。零 c/d、128 上限先被 a/b 占满或超时都不等于无 writer/零军费。

唯一新增正向资格是 `C_D_POST_PC_AVAILABLE_FOR_BOUNDED_SOURCE`：有原 consumer qualified c/d、clean finite 终态且实际同 image RVA。仍 `actual_writer_game_date=null`、`writer_instruction_start=null`、`known_producer=false`、`paid_maintenance_raw=null`、`same_net_invocation_proved=false`。原始 a/b/unknown 全在被 pin 的原消费结果，不因筛选而丢弃。

得到新 post-PC 后，下一 source 输入是 `RIP_after-1` 的包含函数实际 .pdata/root，最多 metadata512B/code8192B/48reads；从实际入口完整解码到恰好结束于 post-PC 的指令并核有效地址。不能将 post-PC 直接当 instruction start 或扫描整个邻域。若只得到 copy，先闭直接输入/caller；业务类别、同 NET、payer 和 cadence 各独立。

## Default-OFF passive leaf 的具体停止边界

**当前没有 c/d writer post-PC，因此本轮不改 native hook。** 已证 a/b copy PC 28A645B/28A6466 只写2C0/2C8，不能拿来冒充 c/d。未来 actual PC/source 有安全函数入口时，最小候选范围是 `native_bridge/include/xar_bridge/war_payment_passive_12004.hpp`（可选 typed writer child）、`src/war_payment_passive_12004.cpp`（真实原调用一次、实际 context/write metadata、既有 natural TLS）、`src/war_payment_runtime_12004.cpp`（defaultOFF 安装/rollback），及 `src/war_payment_json_12004.cpp` 和对应 Python strict normalizer/fixture。只有实际 invocation join 闭合才加同次 NET token；payer/cadence不由名称推断。

若新 PC 是函数内 inline store，普通函数入口 detour 不具 live GPR/flags/XSTATE 保存资格；先给精确 ABI/覆盖字节/回滚方案，不照搬入口 hook。此项依赖实际源，不建通用 observer 框架，也不与 R06 ADD/DR 或共享 C++ 同时编辑。

## 本包资格

三个新 focused checks（两项选择器语义、一项真实 adapter parser argv）实际主 venv Python3.14.7 / `-B -O` PASS；未重跑旧8case/24拒绝矩阵。parser case 仅执行真实 main 的 argparse 构造片段，未进入 adapter admission 或 observer。模板中的未来身份均 null，未冒充已准入或已获新 trap。完整 argv/stdio/source pins 见小回执。
