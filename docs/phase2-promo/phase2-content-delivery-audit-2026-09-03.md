# 天朝二期内容交付审计（2026-09-03）

这是一份只读审计记录，回答“二期已经做了什么、还缺什么、现在能并行做什么”。
它不启动 CK3，不调用 TTS/FFmpeg，不生成占位视频，也不把静态或 fixture 证据升级成 live。
审计基线为当前 integration worktree；时间以 `2026-09-03` 本地工作日为准。

## 一句话结论

二期的代码、领域合同、双版本导演与制作链已经达到 `static-ready`；宣传工具也已更新到远端
`main`。当前真正未闭环的是完整二期 product projection 的实机启动/seed，以及由此依赖的八段
真实 clean spans。两版最终 MP4 仍不存在，因此 T0 不能标记为 complete。

## 已完成的部分

| 层次 | 事实与证据 | 当前边界 |
| --- | --- | --- |
| 361 目录与运行合同 | `mod_zhongguo_style/docs/361-mechanism-manifest.json` 记录 361/361 目录、A/B/C 合同、38 个领域和中央 hook 连接；`361-phase2-full-implementation-program.md` 明确逐号运行合同与验收矩阵 | 这是设计/中央可达性，不等于 361 个完整 CK3 玩法闭环 |
| 二期脚本与生成结果 | 二期 B1、B2、career/HC、manager、credit/project、incident、metrics、workforce/endgame 等生成器及脚本已在源树；`tools/validate_static.py` 返回 `LOC VALIDATION OK` 与 `STATIC VALIDATION OK` | 仍需 exact-build 实机解析、暂停态 provider 结果和多周期验收 |
| 发布树 | `tools/build_release.py --check` 返回 `86 files, deterministic manifest and ZIP` | 发布树可复现不代表 Workshop/正式发布已授权或完成 |
| 双宣传片 authoring | 人物版与制度群像版各有导演稿、项目配置、claims ledger、审片计划和独立输出名；两份 `validate_phase2_authoring_claims.py --validate-only` 均 `GREEN`（10 章、8 个 gameplay cue） | 所有 gameplay 章节仍 `planned`，cue `release_usable=false`，没有真实媒体 |
| 宣传工具前置 | fresh clone `Z:\ck3_mod_rewrite\_runtime\promo-tool-fresh-20260903` 已验证 clean，`HEAD == origin/main == 57c42fca13ea459432c1caf76e069a1fbccf602c`；工具版本 `0.2.1`，测试 `263 passed/2 skipped` | 已满足“正式制作前更新到远端主线”的前置；每次真正渲染前仍需再次 fetch/核对 |
| 无 CK3 的制作链 | 二期 phase2 测试集在绑定最新工具后通过：mod-side `314` tests、root `135` tests，均 exit 0；故意的 media-preflight synthetic RED 是负例断言 | 测试只证明合同和 fail-closed 行为，不能产生游戏素材 |
| CK3 启动环境基线 | 最新无 Mod、无 bridge 的正式 Steam EXE/CWD/有效 disposable userdir 记录（`ck3-bare-nomod-startup-evidence-2026-09-03.md`）到达 Frontend，约 42.25 秒后正常退出；旧的 pre-loader 崩溃 attempt 仍原样保留 | 证明游戏本体启动链可用；不证明完整二期 projection、native readiness 或 seed 可用 |

## 当前未完成与阻塞

1. **完整二期 projection 仍未闭合。** core、B1、case-kernel、incident、manager、B2 的最小依赖闭包已有约 50 秒到 Frontend 的 GREEN 证据；包含 workforce 的组合及 201-file direct union 在原版 `on_action 881` 后长时间停滞，尚未形成完整 Frontend/seed 证据。对应失败 attempt 见 `ck3-workforce-bisect-evidence-2026-09-03.md` 与 `ck3-direct-union-v2-bisect-evidence-2026-09-03.md`。
2. **八段真实素材为 `0/8`。** `phase2_fact_quota_calibration`、`phase2_receipt_appeal_pip`、`phase2_manager_governance`、`phase2_promotion_compensation`、`phase2_hc_workforce`、`phase2_projects_metrics`、`phase2_incidents_operations`、`phase2_cross_cycle_endgame` 均缺少同源 CK3 clean span、checkpoint/save SHA、provider postcondition 和清理回执。
3. **两版成片均未生成。** `zhongguo-361-phase2-character-led.mp4` 与 `zhongguo-361-phase2-institution-led.mp4` 目标文件不存在；旧一期静帧/旧 smoke 片不能替代二期 lineage，也不能拿来签核。
4. **native/provider 证据仍是下一道门。** 业务 postcondition 合同已静态实现，但 promotion/compensation、projects/metrics 等真实 provider 查询尚未取得 paused/live 响应；`native-readiness` 和 seed contract 仍保持 RED。
5. **人审、导出和外部发布尚未开始。** 两版各自需要 source review、candidate 1× review、claims signoff、export receipt；视频发布目标也没有独立 authority receipt，不能自动上传。
6. **361 全量状态不能被宣传片状态代替。** 当前总账为 `central-wired=357`、`ck3-live=4`（001/018/069/357），其余 357 项没有逐号 CK3 live 证据；这与“代码已经落盘”是不同维度。

## 现在可以在无 CK3 条件下立即并行的工作

| 工作包 | 可执行动作 | 交付判据 |
| --- | --- | --- |
| workforce 缩小 | 使用 `tools/phase2_workforce_block_segments.py` 对 `zg361_workforce_endgame_runtime_effects.txt` 做只读、brace-balanced 分段；输出放 `_runtime`，按依赖顺序供下一次单槽 A/B 使用 | 不改 canonical 源文件；每段有 source SHA、block range 和可复现 manifest |
| 静态/生成回归 | 继续使用项目 venv 跑 `validate_static.py`、`build_release.py --check`、二期生成器测试；发现差异只修数据源/生成器 | 结果与当前 GREEN 基线一致，提交明确测试回执 |
| 证据账本 | 将每轮 CK3 A/B 的输入文件数、SHA、FrontEnd、退出码、清理状态和 RED 原因追加到 phase2 evidence/index 与日报 | 失败 attempt 不覆盖；状态只按证据升级 |
| 双片准备 | 保持两套独立 runbook/claims ledger；素材到齐前不运行 TTS/渲染。可提前复核命令、字幕安全区和审片模板 | 两套配置 SHA 与 shared claims SHA 相互匹配，仍标 `footage_pending` |
| 工具 freshness | 正式 TTS/渲染前对 fresh promo checkout 再做一次 `fetch origin main --prune`、clean 和 `HEAD == origin/main` 检查 | 保存 tool-head、测试摘要和 receipt；不使用旧 checkout |

## 13:10–13:15 实机闭环更新（只记录既有独占运行）

为定位 `on_action` 后的启动停滞，恢复 runner 依次比较了同一 Steam
EXE/CWD、有效 userdir、DLC 与 warm cache 下的几个静态投影。这里的
`frontend_gui_complete` 只表示 `gui/frontend_main.gui` 已加载，正式 Frontend
仍要求 `End loading of history`；因此不能把前者单独升级为 GREEN。

| 投影 | product 文件/字节 | 结果 | `error.log` | 最后加载标记 |
| --- | ---: | --- | ---: | --- |
| legacy 51（对照） | 51 / 7,137,587 | `frontend` | 0 | `Total of : 879`，随后 history 完成 |
| callable-core | 66 / 14,430,022 | `timeout` | 2 | `Total of : 881` |
| event-core | 81 / 14,802,010 | `timeout` | 323 | `Total of : 881` |
| event + loc augmentation | 162 / 15,060,079 | `timeout` | 68 | `Total of : 881` |
| event + full loc fan-out | 261 / 15,924,897 | `timeout` | 0 | `Total of : 881` |

最新完整本地化尝试的报告为
`_runtime/formal-phase2-event-locfull-20260903/report.json`，SHA-256
`C43FAF6AC59A7D4A185D77D6A5509E17CF960E6D38A8939EC39F9C1E3F3BFAC1`。它在 180 秒超时并由
runner 正常清理，窗口与 `frontend_main.gui` 均出现，但没有
`End loading of history`。`locfull` 将 event-core 的本地化错误降为零，仍未改变
`Total881` 停滞，故缺失本地化键不是当前挂点的充分解释。对照日志显示无 Mod 的
`Total879` 后会进入 `Database Node Init Time` 与 history；新增投影在 `Total881`
后连第一条数据库初始化标记都没有。此项维持 `native/provider = RED`，失败 attempt
保留供下一轮 workforce/central 分段 A/B 归因。

## 依赖解除后的时间估计

这是条件 ETA，不是承诺的日历时间：

- 完成有效二期 seed、并确认 8 段 clean span 的录制环境后，采集与 intake 约需 `20–40 分钟`；
- 两版 TTS、字幕和候选渲染可并行，每版约 `45–90 分钟`；
- 每版 source review、最终 1× 审片、signoff 与本地 export 还需额外两轮人工审阅时间；
- 在 workforce/完整 projection 的启动证据和真实素材出现前，不能给出“几点看到成片”的诚实固定时间。

## 本次审计动作边界

本审计只读源文件和既有 evidence，运行了静态校验、发布树检查、authoring validator 与无 CK3 的
phase2 单元测试。没有启动真实 CK3、没有点击协议/通知、没有访问商店、没有购买/付款、没有调用
TTS 或 FFmpeg，也没有修改生成文件或 canonical runtime。
