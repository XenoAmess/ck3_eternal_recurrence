# 实测工作流程（CK3 mod 调试）

## 启动与日志

```powershell
Start-Process "...\binaries\ck3.exe" -ArgumentList "-debug_mode"
```

日志目录 `Documents\Paradox Interactive\Crusader Kings III\logs\`：

- `error.log` — 解析错误（加载期）+ 运行时脚本错误（带调用栈和文件行号，**最有价值**）。累积式，按时间戳过滤
- `debug.log` — `debug_log` effect 的输出（jomini_effect_impl.cpp:450 前缀，带文件行号）
- `gui_warnings.log` — GUI 警告
- 解析错误在到主菜单前就会全部写入，启动游戏到主菜单即可完成静态验证

## 全自动验收 runner（tools/run_acceptance.py）

runner 共用同一套现场备份恢复、静态校验、工坊同步和 OCR 大厅导航。`selftest`、`persistence-restart`、`death-edges`、`death-with-heir`、`bargain-reopen`、`progression-ui`、`scoring-matrix`、`courtier-creator`、`balance-long` 加载开发树；四个生产 smoke 会先生成 production-only release 投影，再将该投影 `/MIR` 到工坊缓存后启动 CK3。

```powershell
& "Z:\ck3_mod_rewrite\tools\.venv\Scripts\python.exe" "Z:\ck3_mod_rewrite\tools\run_acceptance.py"
& "Z:\ck3_mod_rewrite\tools\.venv\Scripts\python.exe" "Z:\ck3_mod_rewrite\tools\run_acceptance.py" --scenario on-first-life
& "Z:\ck3_mod_rewrite\tools\.venv\Scripts\python.exe" "Z:\ck3_mod_rewrite\tools\run_acceptance.py" --scenario on-recorded
& "Z:\ck3_mod_rewrite\tools\.venv\Scripts\python.exe" "Z:\ck3_mod_rewrite\tools\run_acceptance.py" --scenario on-high-budget
& "Z:\ck3_mod_rewrite\tools\.venv\Scripts\python.exe" "Z:\ck3_mod_rewrite\tools\run_acceptance.py" --scenario off
& "Z:\ck3_mod_rewrite\tools\.venv\Scripts\python.exe" "Z:\ck3_mod_rewrite\tools\run_acceptance.py" --scenario persistence-restart
& "Z:\ck3_mod_rewrite\tools\.venv\Scripts\python.exe" "Z:\ck3_mod_rewrite\tools\run_acceptance.py" --scenario death-edges
& "Z:\ck3_mod_rewrite\tools\.venv\Scripts\python.exe" "Z:\ck3_mod_rewrite\tools\run_acceptance.py" --scenario death-with-heir
& "Z:\ck3_mod_rewrite\tools\.venv\Scripts\python.exe" "Z:\ck3_mod_rewrite\tools\run_acceptance.py" --scenario bargain-reopen
& "Z:\ck3_mod_rewrite\tools\.venv\Scripts\python.exe" "Z:\ck3_mod_rewrite\tools\run_acceptance.py" --scenario progression-ui
& "Z:\ck3_mod_rewrite\tools\.venv\Scripts\python.exe" "Z:\ck3_mod_rewrite\tools\run_acceptance.py" --scenario scoring-matrix
& "Z:\ck3_mod_rewrite\tools\.venv\Scripts\python.exe" "Z:\ck3_mod_rewrite\tools\run_acceptance.py" --scenario courtier-creator
& "Z:\ck3_mod_rewrite\tools\.venv\Scripts\python.exe" "Z:\ck3_mod_rewrite\tools\run_acceptance.py" --scenario balance-long --balance-fixture count
& "Z:\ck3_mod_rewrite\tools\.venv\Scripts\python.exe" "Z:\ck3_mod_rewrite\tools\run_balance_matrix.py"
& "Z:\ck3_mod_rewrite\tools\.venv\Scripts\python.exe" "Z:\ck3_mod_rewrite\tools\run_terminal_acceptance.py" --mode observer
& "Z:\ck3_mod_rewrite\tools\.venv\Scripts\python.exe" "Z:\ck3_mod_rewrite\tools\run_terminal_acceptance.py" --mode ironman
& "Z:\ck3_mod_rewrite\tools\.venv\Scripts\python.exe" "Z:\ck3_mod_rewrite\tools\run_vivhite_acceptance.py"
& "Z:\ck3_mod_rewrite\tools\.venv\Scripts\python.exe" "Z:\ck3_mod_rewrite\tools\run_vivhite_acceptance.py" --scenario vivhite-alone
& "Z:\ck3_mod_rewrite\tools\.venv\Scripts\python.exe" "Z:\ck3_mod_rewrite\tools\run_vivhite_acceptance.py" --scenario original-then-vivhite
& "Z:\ck3_mod_rewrite\tools\.venv\Scripts\python.exe" "Z:\ck3_mod_rewrite\tools\run_vivhite_acceptance.py" --scenario vivhite-then-original
```

原 mod 场景基线与边界：

- `selftest`：默认场景，保持原有完整死亡/计分/UI 全链；只有此场景读取 `--import-record 0|100`。
- `on-first-life`：固定 `xar_on` + 纪录 0，真实接受契约，OCR 验证 `xar.0010` 的「未燃之世」及「前世余烬」「余烬位阶」，再进入祝福窗口即结束，不触发死亡。
- `on-recorded`：固定 `xar_on` + 纪录 100，真实接受契约，验证生产商店（优先补充 100 点 OCR 证据；标题与 `shop event fired` 同时证明非首世分流），不购买商品，直接开始此生并进入祝福。
- `on-high-budget`：固定 `xar_on` + 纪录 2000，在默认成长 + 100% 下 OCR 确认 2000 预算，翻到第四页真实购买 250 分恐怖值和 500 分正统性服务，返回第三页购买 1133 分宗教改革，断言余额 117、一次性选项消失，再进入祝福。
- `off`：固定 `xar_off` + 纪录 0，进局后观察 30 秒；契约标题或本次新增的任意 `XAR:` 启用日志均判 RED。
- `persistence-restart`：一次外层备份内启动两个 CK3 进程。A 从纪录 0 跑完整 selftest 并真实写入非零 lesson，进程树完全退出后固定 handoff SHA-256；B 不调用纪录预置函数，以新日志 offset 断言 importer 精确命中 A 的位阶及 request/ready/consumed 全链。该场景禁止非零 `--import-record`。
- `death-edges`：固定 selftest + 导入位 1，真实杀死带 `xa_enabled` 的 AI Roger，断言生产计分被 `is_ai=no` 阻断；再逐日使当前继承人失去继承资格，直到 `player_heir` 不存在后真实杀死玩家，验证前向提交链、原生继承窗内的八值结算、无“继续扮演”、退出确认和返回主菜单。随机原生事件会由 recovery 点击底部选项后继续日 tick。
- `death-with-heir`：固定 selftest + 导入位 5，在确认玩家存活、启用且确有 AI 继承人后，以 acceptance-only 心脏事件触发普通玩家死亡。runner 必须精确点击原生「继续扮演」，确认控制权已转移给人类继承人，再等待生产计分/分流/可见结算各恰好一次。2026-08-20 共同 AI 闸门 post-review 复验 GREEN：`xar_death_with_heir_postreview_20260820`。
- `bargain-reopen`：固定 selftest + 导入位 2，但不进入主 selftest。独立 bootstrap 调用生产契约/运行初始化，并用 release 会整文件剥离的 acceptance-only `immortal` 固定九年观察体存活；随后真实点击三轮 `xar.0004` 祝福与 `xar.0005` 咒痕。安全 wire id 只由 acceptance instrumentation 固定，祝福/诅咒仍走生产 dispatcher。每轮成交后保留生产 option 的 `xar.0006 days = 1095`，另设仅观察状态的 day-1094 probe；脚本保存成交时的 `current_date` 并在两条路径相减，断言累计对数 1/2/3、session 在祝福后为 1 且 `xar.0006` 重置为 0、XP `0→1→2→3`、拒绝数 0、1094 日不重开、1095 日精确重开及第三对后的完整新窗口。runner 用鼠标选择速度 5，并以底栏渲染日期 OCR 判断游戏是否仍在推进；debug marker 只负责机制断言，合成键盘不参与。
- `progression-ui`：固定 selftest + 导入位 3，通过玩家限定 acceptance 编排依次调用生产贤王契约进度 effect，真实点击 3/6/10 三个生产里程碑事件；随后调用两次生产成交 effect 达到【琉焰之视】10 XP 并点击其生产里程碑事件。runner 要求 `tutorial.txt` 精确稳定为该契约的 PB 3/6/10 与完成四个 lesson，再从原生决议打开账簿，同帧 OCR 确认当前 `0/10`、历史 `PB 10`、贤王图鉴、`R 1` 与 `S 0`。该场景不伪造 PB、图鉴或里程碑状态，acceptance 只负责安全地产生生产入口所需的玩家行为。
- `scoring-matrix`：固定 selftest + 导入位 4，先保存历史角色的生产计分与只读 preview 基线，再创建受控谱系：同一后代经兄妹两条路径可达、另一支穿过已故第一代延伸到第五代，并额外创建第六代排除项。跨事件边界后要求新增宗族/家族计数恰为 7、头衔桶不变、临时去重 flag 全清、preview 增量为 1.4 且与生产总分误差不超过 0.01。随后 200 个 wire ID 逐一调用生产 apply dispatcher；每个实际命中的分支自行写 marker，下一事件再断言 100 次祝福计数、代表修正、最终稀有度和 100 XP 已提交。
- `courtier-creator`：固定 selftest + 导入位 6，从带琉焰图标的【琉焰卿的永恒轮回】原生决议分组真实打开七页契页，并依次打开账簿、契约、廷臣三张原生详情图取证。随后验证取消零副作用、119 金确认禁用、默认 120 金成交、年龄/六维步进、五类生成 trait 目录、动态文化/信仰、同家族、348 金配置关窗重开保留、第二次实际角色交付与 AI 拒绝。runner 对文化只点击缩进子项，对信仰等待选择 effect marker；选择阿卢克古道后必须返回【心性】，分别从【勤勉】与【懒惰】原生 tooltip 读到该信仰的美德与罪恶，且两者均不得出现天主教。创建角色必须同时不同于玩家文化与信仰。2026-08-21 权威定向报告：`xar_decision_group_trait_both_20260821`，三图、美德/罪恶上下文、两次购买与 AI 闸门 GREEN，0 `xar` errors。
- `balance-long`：必须指定 `--balance-fixture count|king|emperor|synthetic`。runner 把原版 81 个规则全部重建为当前 1.19.0.6 声明的默认值，追加 `xar_on`、成长 + 100% 和仅开发夹具；大厅仍走已验证的罗贝尔路径，生产初始化前再切换到史实奥塔/腓力一世/亨利四世或脚本标准化奥塔替身。固定选择第一项祝福与咒痕，不做 CK3 战略操作；逐对采样生产分数，30 年后允许自然死亡，否则在 40 年右删失。生产链在 dying root 有效时先保存 `scope:xar_dead` 并向 `player_heir` 排入 `delayed = yes` event，再内联计算；carrier 随后交付 record、settlement 和 kind 4 terminal wire。继承窗只走专用 OCR 路径；不把新统治者继续当作同一寿命采样。GREEN 只证明夹具、逐笔 1095 日节奏、被动策略、结构化采样和零 `xar` 错误，完整边界见 `docs/balance-test-protocol.md`。
- `run_terminal_acceptance.py --mode observer|ironman`：以非 debug CK3、禁用云存档和仓库外一次性 `-userdir` 运行开发验收夹具。observer 要求结算后出现原生【正在观察】；Ironman 要求 modal 强制暂停、原生暂停菜单可打开、点击继续后重新阻断、原生保存确认、返回主菜单、同一进程内重载同一存档后再次阻断。包装器在运行前后逐文件比较真实 Documents 的教程/规则/启用项/设置及全部 `*.ck3` 存档，以及本地 Steam `userdata/*/1158310` 后备目录；两组都必须在退出后的五秒观察窗保持基线聚合哈希。远端 Steam 服务不在此证明范围内。仅当场景与后置检查均 GREEN 时才删除隔离 userdir，再把实际删除结果写入报告。
- 自主玩家 Phase A 的 non-debug 实机 smoke 在 2026-08-22 发现当前 Steam 客户端会在部分直启退出后改写 `userdata/<account>/1158310/remotecache.vdf` 的顶层 `ChangeNumber`，稳定运行也会刷新该文件 mtime；真实 Documents 和云存档条目未变。自主玩家不回写或恢复真实文件，而是把 `ChangeNumber`/mtime 作为 Steam 自有易变元数据单列 before/after，比较时只规范化该整数并对其余字节做 SHA-256。任何云存档条目字段或其他 userdata 文件差异仍判 RED。该白名单是 1.19.0.6 + 当前 Steam 客户端的实测边界，不应悄悄放宽既有 terminal acceptance 的历史验收口径。
- 同轮 fresh-log 实测还表明：`cloud_save=no` 只禁止本局写云档，并不阻止 CK3 前端枚举已有 Steam Cloud 存档 meta。隔离 profile 的正常存档为零，production tree/原版文件均无 PoD 引用；但 cloud meta 中的 17 个旧 PoD 规则 key 与两张 PoD 贴图引用和 `error.log` 逐项匹配。与此同时 enabled inventory 精确只有【琉焰卿的永恒轮回】，全部 mount 只来自已安装 DLC 或隔离 production tree。因此这些报错是旧云档前端元数据，不是第二个 mod 被加载。自主玩家 isolation smoke 必须归档非空 error log，并写入 `clean_engine_boot_required=false` 与 `engine_diagnostics.zero_diagnostics=false`；其 GREEN 只证明单 mod 隔离和可见主菜单，不得表述为零引擎错误。该来源判断有内容全匹配、零隔离存档与 mount 反证，置信度高；尚未用 ProcMon/ETW 做因果 I/O 跟踪。
- 自主玩家 Phase A 的正式退出证据为提交 `11ab443050132341bb27f6f924d792772f397396` 在同一环境指纹下的三次连续 GREEN：`20260821T180045Z-a3c49b20`、`20260821T180248Z-7ad2dd83`、`20260821T180531Z-9c6bb34b`。三份历史 format v1 `events.jsonl` 与最终 `report.json` 均已用当时的 `validate_smoke_report()` 重新计算 hash chain 并做一致性校验，语义硬条件另行逐字段断言；每次都满足两帧可见【新游戏】、精确单项 enabled inventory、唯一隔离 production mount、零未知 mount、退出后二次日志解析、Job 成员 1→0、双源 CK3 inventory 为空、watchdog/控制文件消失和 production tree 不变。真实 profile 与 Steam userdata 回到 baseline 后连续稳定 5 秒；Workshop descriptor 内容哈希与目标树路径/大小/mtime 只做退出后一次 baseline 比较。该三连由 supervisor 终止 CK3，不证明 graceful exit，也不是有效得分局；完整边界见 `docs/autonomous-player-phase-a-evidence.md`。
- 自主玩家的 post-resume 崩溃门禁使用 `agent.py crash-smoke`，不能复用普通 `smoke` 的 `finally` 来模拟。外层 verifier 持有 state/launch mutex 和 protected baseline；subject 先发布完整身份与命令契约的 ready，outer 验证后固定真实 supervisor 进程句柄并写 ack，subject 必须验证 ack 后才可创建 CK3。ready、ack、armed 都写 UTC 与 Windows 同机跨进程可比的 monotonic 时间；UTC 必须可解析且为零偏移，实时路径强制 monotonic 严格满足 `ready < ack < armed`，无密钥回放只验证归档记录值与字段关系自洽。随后 subject 创建 suspended CK3、先加入 nonce 命名的 kill-on-close Job 再 resume，并把两个 Python 父子 sentinel 加入同一 Job；detached watchdog 只等待 subject。外层固定 supervisor、CK3、两个 sentinel 和 watchdog 的精确进程句柄，只对 supervisor 句柄注入退出码 77，且不得持有 Job handle。只有四个 Job 相关句柄均退出、命名 Job 已销毁、watchdog 句柄退出码为 0、四类控制文件消失、全局 CK3 双源清点连续 5 秒为空，才能设置 `cleanup_proven=true` 并开始 protected postflight。普通可捕获失败必须 finalize 为 RED；`KeyboardInterrupt`/`SystemExit` 等外部异步中断仍先执行句柄清理，但可留下 `finalized=false` 的 provisional，不能作为任何验收证据，若清理未获证明则 unsafe marker 与全局进程清点继续阻断下一次启动。
- crash run 的 artifact 层必须在同一 validator、仓库代码与 OCR runtime 下可自包含回放：两张连续的 2560×1440 PNG、完整 OCR bbox、运行时日志前缀、DLC mount 冻结白名单、owner/handoff、supervisor ready/ack、armed、三份 crash 前控制文件、watchdog final、environment 与 production manifest、protected before 都以 run-relative path + SHA-256 入 manifest；protected after 只在 cleanup 已证明且获准执行 postflight 时存在。运行期绝对路径仅与报告记录的原执行目录绑定。复制整个 `runs/<run-id>` 后，validator 从副本读 artifact，不再实时扫描原游戏 DLC 目录，并从 PNG 重跑同一 OCR 以绑定像素与【新游戏】文本；这不是跨机或脱离当前仓库/OCR adapter 的自包含格式。GREEN 与任何声称 cleanup 成功的 RED 共用同一清理语义验证函数和完整五事件序列，但 validator 尚未逐项把每个 event payload 的全部语义与 report/artifact 交叉绑定。若 storage postflight 已成功但随后 profile/tree 复核失败，RED 可保存这段局部成功证据，但不得声称 production tree 已验证。该报告固定记录 `integrity=unkeyed_sha256`、`claim=archive_schema_and_internal_consistency_only`、`historical_execution_authenticity_proven=false`；无密钥链不是数字签名，复制后的归档不能独立证明历史执行真实性。
- 2026-08-22 首次本机 `crash-smoke`（`20260821T201701Z-crash-9708619d`）在创建 CK3 前按预期 RED：`tools\.venv\Scripts\python.exe` 在本机不是透明替换，而是保留一个 venv redirector，再由它启动基础解释器中的真实 subject，进程链为 `outer → redirector → subject`；把 `Popen.pid` 当 subject PID 会误判“不是直接子进程”。独立休眠探针进一步实测：redirector 的 `ExecutablePath` 与命令行 `argv[0]` 都是 venv launcher，而真实 subject 的 `ExecutablePath` 是基础解释器、`argv[0]` 仍保留 venv launcher。崩溃门禁因此只接受 `outer → subject` 或恰好一层 `outer → authenticated redirector → subject`，分别绑定两段 PID/父 PID/创建时间/映像，并对两进程解析同一套完整隐藏入口 argv；两跳仅允许真实 subject 的映像与 launcher argv0 按该实测关系分离。subject 先发布 nonce 绑定的 ready，outer 认证并固定真实 supervisor 句柄后回写 acknowledgement；ack 到达前禁止启动 CK3。armed/report 另存 redirector 身份与退出码，watchdog、sentinel、注入句柄和 `subject_pid` 始终绑定真实 subject，禁止任意祖先搜索。该 RED 只定位启动器语义，不能算崩溃回收通过；后续 GREEN 见下。
- 同日第二次本机 `crash-smoke`（`20260821T211059Z-crash-833b9587`，环境 SHA-256 `64fa69124f341dfcae6ffc7422ca7b07ec1d9b0e82373c7453c7fe49368994a2`）已通过两帧可见主菜单、单 mod load、四个 Job 相关 pinned handle 退出和命名 Job 销毁，但 detached watchdog 与 Job teardown 竞态中对同一已认证 CK3 handle 调用 `TerminateProcess` 得到 `ERROR_ACCESS_DENIED`。旧实现异常后只等待 1 秒，因此 watchdog 正确返回非零，outer 将运行 finalize 为 `cleanup_proven=false` / `unsafe_cleanup=true` 的 RED，禁止 protected postflight，并保留 record、ready、watchdog error 与 unsafe marker；稍后的当前态清点为空不能回写该历史结论。修订把正常终止、WMI 行先消失和 `TerminateProcess` 异常三条路径统一为最多 20 秒的同一 pinned-handle 排空，只接受 handle signaled；fallback 和五秒稳定空窗使用独立预算，outer 最多等待 watchdog 90 秒。非零 watchdog 结果还必须归档并绑定结构化 failure、final/error 原文和 control-before，unsafe RED 的搬移回放不能删改这些诊断后仍通过。
- 陈旧 crash control 绝不由 `prepare-profile`、`smoke` 或下一次启动自动删除。只能显式执行 `agent.py recover-stale-control --run-id <finalized-RED-run-id>`：在 state/launch 双锁内验证 source report 与归档哈希、环境和 game exe、record/ready/marker nonce、所有记录 identity 当前不存在、命名 Job 不存在、双源 CK3 清点稳定为空；成功 report 先以“active marker 已消失且 marker 归档哈希匹配”为完成条件写前日志，再做末次即时 inventory、末次 Job absence，最后用 nonce+哈希 CAS 归档 unsafe marker。该 CAS 是最后一次 recovery 证据/控制提交，之后不再写 recovery report/artifact；锁实现仍可清理自己的 owner 文件。write-ahead report 可在 CAS 前已含条件式 `ok=true`，单看该字段不算成功，必须由 `validate_recovery_report()` 同时观察 active marker absent 与归档 marker SHA-256 匹配。旧事故的外置 watchdog-final 不受源 report manifest 绑定，恢复证据必须明确 `source_report_bound=false`，不能把它当成历史 cleanup 证明。恢复另建 report，声明 `historical_cleanup_proven=false`、`current_absence_proven=true`，源 crash RED 永不修改或升级；任一未知、漂移或中途失败都保留/恢复 marker 并 RED。旧 RED `20260821T211059Z-crash-833b9587` 已由 `20260821T215805Z-recovery-46a3518c` 显式恢复并经 `validate_recovery_report()` 重放通过；源 report SHA-256 仍为 `eb429f5513f6610b433ee0349e571cd4f4fd8278cb666fbfc58c01896aa6a68f`，四份 control 原哈希归档且 active 路径消失。该恢复只解除阻塞，不改变旧 RED。
- runtime 实现提交 `98d55caf3ed4a398b0a3bd7bc8e6ee16591d8f26` 在环境 SHA-256 `5e7fb63ef98a7fd802caa864b64c593053c68bfb5f1798321cde6b02d6cd0d5f` 下完成本轮资格：普通 `smoke` `20260821T215910Z-780cd6cb` 与 post-resume `crash-smoke` `20260821T220127Z-crash-adc0ac63` 均 finalized GREEN。该历史 normal 是 format v1：`validate_smoke_report()` 只复算其无密钥事件链、final tail 与 finalized/ok，下面的 load/cleanup/protected/production 硬字段另行逐项断言；`validate_crash_report()` 重放 crash 归档的完整 schema 与内部一致性。两次都是 non-debug、两帧可见【新游戏】、enabled inventory 精确单项本 mod、唯一隔离 production mount、零未知 mount；crash run 中真实 supervisor 精确句柄退出码 77，CK3 与两个 sentinel 所在命名 Job 销毁，四个 pinned handle 退出，watchdog 返回 0，四类 control 消失，双源 CK3 连续 5 秒为空，之后 protected postflight 与 production tree 复核通过。两份都没有作出游戏内玩法选择、`valid_score_episode=false`，不证明规则页已视觉确认 Growth+100，也不是有效得分局；ordinary/crash 的旧主菜单观察器可能发送合成 Alt 获取前台，不能将其称作全程零输入证明。
- Phase B 的 `agent.py menu-smoke --timeout 180` 是独立 sealed lifecycle，不复用 acceptance 的导航或普通 smoke 的 OCR 聚焦副作用。命令在启动 CK3 前必须从当前 state 中找到同一 environment、时间有序的 self-contained format v2 ordinary GREEN 与 post-resume crash GREEN，完整重放后复制进本次 run；当前 runtime 一旦改变，旧资格自动失效。场景能力精确只有 `main_menu.new_game`，大厅 `bookmark_lobby.start_game` 必须保持 forbidden；fresh frame 后、任何鼠标移动前向主 `events.jsonl` fsync `ui_input_armed`，最终只允许一次 `SendInput(LEFTDOWN+LEFTUP)` 批次。GREEN 必须看到两帧稳定书签页，RED 必须保留实际 receipt/WAL 前缀并仍走受控清理。无害 Win32 helper 已实测 96 DPI、client/screen 换算、前台/Z-order/180×120 topmost 遮挡、WMI 空 `ExecutablePath` 的 pinned-handle 信任和两记录输入；桌面枚举中可见的 `(0,0,1,1)` ghost HWND 仅在宽高都不超过 1 时忽略，最终点击点仍须由 `WindowFromPoint` 精确命中。Windows foreground-lock 偶发拒绝 helper overlay 抢焦点时，夹具只记录实际前台结果，但独立 Z-order 遮挡反证仍必须拒绝目标像素。该 helper 不等于 CK3 实机输入；在提交、重新 prepare 并取得同环境两项资格前禁止运行 menu smoke。
- 2026-08-22 的第一次真实菜单竖切以提交 `226d80e`、环境 `219c77d9d5e8b7e50e32314f2f8fcb57130fedc3c853880677e4149c425556ba`、ordinary `20260822T005515Z-03f296c7` 与 crash `20260822T005727Z-crash-38023ffc` 资格运行。`20260822T010001Z-menu-193c8062` 在任何 `ui_*` WAL、action receipt、鼠标移动或 `SendInput` 前因 CK3 失去前台而安全 RED；tracked cleanup、全局 CK3 空清点和 protected/production postflight 均完成。该不可变报告同时实测到 COM WMI 的 DMTF 创建时间 `20260822090033.870978+480` 与 PowerShell CIM UTC ISO `2026-08-22T01:00:33.8709780Z` 表示同一进程时刻，且 29 个 DLC mount 按引擎日志顺序而非字典序出现。回放器现严格解析两种时间后比较 UTC，并保留 DLC engine order、要求绝对白名单成员和不重复；旧 RED 已可原样回放但仍是 RED。后续前台协议在唯一窗口绑定后先 fsync `foreground_activation_planned/armed`，只允许一次 direct `SetForegroundWindow` 与至多一次 caller→当前 foreground thread 的严格 attach/detach fallback，detach 或身份未知时不重试；成功才写 finished attestation。`GetLastInputInfo` 相等只记录采样值未变，不证明无人输入。该修订改变 runtime，旧两项资格不能用于下一次菜单尝试。
- 提交 `af3df58` 在环境 `31e68f6d8e439643a7ff8fcb6029d72f93a85ead2d74bb58d24042c382753f72` 下重新取得 ordinary `20260822T020912Z-7dc8269d` 与 crash `20260822T021144Z-crash-b010d18c` 两项 GREEN。唯一一次后续菜单 run `20260822T021436Z-menu-c9b3d667` 在稳定主菜单观察前因客户区被外部置顶窗口 `(2130,1095)-(2560,1392)` 遮挡而安全 RED。公开回放确认无 `visible_main_menu_attested`、`ui_*`、receipt、鼠标或 `SendInput`，tracked cleanup、双源空清点与 protected/production postflight 完整。事后只读活体查询把 HWND 定位为 Kaspersky `avpui.exe` 的 WPF `AlertWindow`，但原 run 只绑定 HWND/矩形，产品身份不是历史归档证明。自主玩家不自动关闭安全软件通知；外部窗口须由用户自行处理，原 run/候选不得重试。
- 后续 ordinary producer/report 已升级到 format v2：两帧 PNG/OCR、initial/final debug 前缀、load、diagnostics、精确 process/pre-resume/shutdown、protected、production 与完整 artifact inventory 全部使用 run-relative 引用，公开 `validate_smoke_report()` 从归档字节重跑 OCR、日志解析和硬条件，并支持搬移后删除源目录。最终 event 先以 report-body hash 写入并 fsync；最终 report 用同目录临时文件先 flush/fsync，再 atomic replace provisional。live 菜单资格和新 archive 只接受 v2 normal；v1 仅允许外层为历史 RED、且没有任何 `ui_*` 输入 WAL、bookmark、navigation、action/receipt 的菜单档只读回放；纯观察 PNG/JSON 可以保留，但永不授权输入。无密钥 SHA-256 仍只证明 archive schema 与内部一致性，不证明历史执行真实性。该升级改变 runtime 指纹，因此 `af3df58` 的 ordinary/crash 资格只保留为历史证据，下一次尝试必须在新提交与新 environment 下重新取得两项资格。
- 提交 `38fd5fa` 在环境 `75f8c6b0271d82183ba2d345a48e4a191e36ea2fd85d98b9a8d30327ce6c7367` 下取得 ordinary v2 `20260822T033531Z-9a595275` 与 crash `20260822T033759Z-crash-f289e776` 两项公开回放 GREEN。唯一菜单 run `20260822T034104Z-menu-49f9b8bd` 的 foreground transaction 以 `already_foreground` 完成，且未调用 SetForeground/attach/合成输入；两次已落盘 capture 都通过前后 foreground/unobscured guard，但 PNG 是 2560×1440 全黑、OCR 为空，第三次 capture 的前或后 guard 才报告 foreground lost。主链无 visible 主菜单、`ui_*`、bookmark、navigation、action/receipt 或 SendInput，cleanup、双源空清点、protected 与 production postflight 全部通过。旧异常未保存失败瞬间的 actual foreground HWND/PID/TID，因此当前档不能区分外部抢焦、同进程另一 HWND 或空前台；下一提交必须先把单次只读 loss sample 绑定进主链与公开 RED replay，禁止用延时或第二次 foreground activation 猜测性重试。
- 提交 `c8531be` 把 typed foreground-loss 证据接入 sealed lifecycle；环境 `925b8deafa0053fffb2522b86770bb377fbbb5e28a28e53a559ce1ecc40584cc` 下的 ordinary v2 `20260822T045930Z-6ce9874f` 与 crash `20260822T050200Z-crash-95b63c14` 均公开回放 GREEN。唯一菜单 run `20260822T050447Z-menu-0eae4606` 在 `capture.pre_grab`、sequence 2 记录 actual raw/root 为同全屏矩形、不同 PID、class=`Ghost`；该 owner 的 `OpenProcess` 被拒，所以历史 process identity 只能是 unknown，不能用停机后 CIM 追认 `dwm.exe`，更不能把 Ghost 当 CK3 代理。主链无 visible 主菜单、任何 `ui_*`、navigation、action/receipt、鼠标或 `SendInput`；cleanup、Job/watchdog/control、双源空清点与 protected/production postflight 全部通过。该档是可回放 RED，原 run/候选不得重试。
- 提交 `39860a0` 在所有 `SetForegroundWindow`、`AttachThreadInput` 和输入前增加 exact-target 响应稳定门。门前做完整 WMI/唯一窗口认证；门内与门后仅使用 pinned process handle、exact HWND/PID/TID/client rect、`GetLastInputInfo`、`SendMessageTimeoutW(WM_NULL, SMTO_BLOCK|SMTO_ABORTIFHUNG|SMTO_ERRORONEXIT)` 与 `IsHungAppWindow` veto，不做 WMI、全桌面枚举或输入。总等待不超过 30 秒且受场景 deadline 约束；成功必须由至少 21 个响应样本组成、相邻间隔 250–500 ms、连续覆盖至少 5 秒，last sample→gate finish 与 gate finish→direct/attach/第二次 Set/完成各不超过 500 ms。hung、无响应、调度空洞、identity/geometry/tick 变化均在 mutation 前 fail closed。证据嵌入 `foreground_activation_finished`，新 `foreground_protocol_version=2` 的 GREEN/RED completed foreground 都必须带 gate；缺版本只允许四份既有零输入 RED 的 run ID + final-event digest 固定回放。环境 `d343278a3e2d046c7aadc2ad90d75640aadca483b3192801234f4e8a096befa2` 下 ordinary v2 `20260822T060233Z-be4794fb` 与 crash `20260822T060508Z-crash-123c80f3` 均 GREEN；随后唯一菜单 run 的真实响应稳定证据通过，因此该门已在 CK3 上运行，但不等于菜单导航 GREEN。
- 唯一 run `20260822T060758Z-menu-fc73b5c5` 在稳定主菜单、fresh frame 与已 fsync 的 `ui_input_armed` 后把鼠标移动到 `(600,558)`，hover OCR/patch 也匹配；最终提交前 caller token 年龄约 5.85 秒，超过当时覆盖整段流水线的单一 5 秒 TTL，以 `visible control token expired at input submission` 安全 RED。receipt 固定 `pointer_input_may_have_occurred=true`、`button_click_may_have_occurred=false`、`send_input.accepted=null`，所以 `SendInput` 未调用，没有 LEFTDOWN/LEFTUP 或点击。shutdown attestation 为 Job 1→0、tree gone、watchdog/control absent、双源 inventory 空；protected baseline 与 production tree 后置相同。原 run/候选不得重试，不能将这次 RED 记作书签大厅或有效局。
- 根因是 caller 的 5 秒 TTL 同时承担 admission、fresh capture、WAL、鼠标移动和较慢 hover OCR，而非状态漂移。修订不扩大全局 TTL：caller token 仍为 5 秒且只负责 admission；fresh observation 签发 5 秒 `fresh_move` lease，绑定 frame/target/caller 父授权/绝对 action deadline；hover observation 再签发 5 秒 `hover_click` lease，绑定 frame/同一 target/fresh 父授权/同一 deadline。两份 lease 均一次性消费，分别紧邻 pointer move 与 `SendInput`；capture 返回时若已越过绝对 deadline 必须拒绝，postcondition 只能使用 deadline 剩余时间。新报告以 `visible_action_protocol_version=2` 让公开 validator 复算 claims、父链、时序和 WAL；旧 `20260822T060758Z-menu-fc73b5c5` 仅按 run ID + final-event digest `aef3dc4d0dc6bbcaf117dfaabc1d27b263309ec2f58cab5b9a14aa4ffb46396d` 固定只读兼容。后续真实候选均完成 `SendInput` 2/2，证明该 liveness 修复已生效。
- 2026-08-22 实机 run `20260822T074235Z-menu-60587e33` 已成功提交【新游戏】的单次点击，但 CK3 1.19.0.6 随后显示中国教程欢迎窗，阻断书签大厅识别。退出后的隔离 `pdx_settings.txt` 实证：旧键 `promt_for_tutorial=no` 不会关闭该提示，遗漏的新键 `prompt_for_china_tutorial` 会被引擎补成 `yes`；隔离 profile 必须同时写入两者为 `no`。该 run 不得重试，修订后须重新 prepare、ordinary/crash 资格化并仅运行一个新菜单候选。
- 提交 `fc1d9bc` 的唯一菜单 run `20260822T075944Z-menu-f66f06b7` 已无欢迎窗：receipt 记录 `SendInput` 2/2，主链写入 `ui_action_finished(status=confirmed)` 与 `bookmark_lobby_attested`，两帧稳定画面均为真实书签大厅。其最终ization 却被 `menu smoke full capture sequence differs` 拒绝，因为成功证据序列 `16,17,18,19,21,22` 中的 sequence 20 是已归档的 post-click `unknown` 转场帧。validator 现仅在 hover 与首个稳定大厅帧之间允许这种严格向前的间隙，主菜单/fresh/hover 与两张大厅稳定帧仍各自要求连续；该 provisional run 不改写、不升级为 GREEN。
- 提交 `7cb1545`、环境 `531e529f7b301330e902ecf7b44821a462a83ffd9dd4359b23a8482a73590057` 依次取得 ordinary `20260822T080818Z-c0fa1742`、crash `20260822T081016Z-crash-fa350c80` 和 menu `20260822T081240Z-menu-f3d8a8a5` 三项真实 GREEN。menu receipt 的【新游戏】批次为 `requested=2/accepted=2/last_error=0`，无教程欢迎窗，最终两帧均分类为 `bookmark_lobby`，报告 finalized/ok=true，清理与 postflight 完成。这是自主玩家首个真实可见菜单动作 GREEN；它不包含角色选择或【开始】点击，下一功能竖切从书签大厅继续。
- 每次运行都写 `report.json` 与 JUnit `report.xml`；JSON 包含 run ID、UTC、版本、Git SHA、实际 runtime tree SHA-256、source mode、CK3/平台/Python 环境、场景、结果、artifact 清单、各阶段秒数和错误原因。terminal 包装器另记三份 harness 文件的聚合 SHA-256。即使中途失败，也会先恢复现场再写 RED 报告；后置存储或清理检查失败时，包装器会同步把已有 JSON/JUnit 降级为 RED。`tutorial.txt`、`presets.txt`、`dlc_load.json` 与 `save games/autosave*.ck3` 备份位于独立临时目录；运行期只启用本工坊项，结束后原样恢复并删除备份，手动命名存档不移动。

白绮独立版矩阵边界：

- `run_vivhite_acceptance.py` 默认串行运行 `vivhite-alone`、`original-then-vivhite`、`vivhite-then-original`。每格都用全新的仓库外 disposable `-userdir`，从源码构建 Vivhite 精确 27 文件 production projection；双 mod 格还构建原 mod production projection，12 文件外部 `erva` 夹具始终最后加载。
- standalone 夹具投影会剥离 `# ERVA_DUAL_ONLY_BEGIN/END` 区域，禁止残留任何 `xar_`/`xa_` 运行时引用。双 mod 两格分别证明 ERVC 348 金配置和 XAR 120 金配置互不污染、两个原生决议组/窗口同时存在、各交付一名廷臣且各扣款一次。
- runner 不读写真实工坊缓存，不调用原 runner 的同步或全局杀进程路径。所有 Steam library 的 `workshop/content/1158310` 根、真实 profile、仓库和 Steam userdata 都是 artifact/userdir 禁区；全部 `ugc_*.mod` 必须含绝对路径并落在已发现的 CK3 Workshop 根。前后比较真实 profile、Steam cloud 后备目录、descriptor 精确哈希及每个已注册 target 的递归 path/size/mtime 元数据。最终安静窗从一次完整相等扫描结束后才开始计时，等待五秒后再做完整复扫。
- 正式矩阵不加 `--keep-userdirs`：只有场景、阻塞性项目日志、保护存储和删除检查全部 GREEN 才删除该格 userdir。`error.log`、`gui_warnings.log`、`database_conflicts.log` 同时扫描 `xa_`/`xar`/`ervc`/`erva`；仅原 mod 冻结代码的两个 loc-only rarity 警告走逐字窄白名单并写入报告。矩阵以 JUnit 先落盘、JSON 最后原子发布；任一 postflight 失败都整体降级 RED。
- 每格由 debug mount 记录反证实际 product 顺序、无额外启用 mod 且 fixture 最后；启动前后还要求 launcher `rawVersion/exePath` 与 CK3 可执行文件 SHA-256 不变。独立 detached watchdog 在 runner 被强杀时只按记录 PID 终止该 CK3 进程树，绝不按镜像名全杀。
- CK3 冷启动可在大厅按钮消失后继续加载数分钟；必须等底栏日期 HUD 实际出现才开始点决议。原生决议分组标题可能附带条目计数；具体决议行必须精确 OCR，并以相邻 bounding-box 顺序证明各行直属对应组，不能把组标题中的同名文本当成行。marker tailer 只消费换行完整记录，CK3 退出后再 flush 尾行并逐 marker 要求恰好一次。

普通场景冷启动通常约 2 分钟；`bargain-reopen` 还要在速度 5 下实走 9 个游戏年，预计整场约 16-22 分钟，随机原生事件多时更长。所有场景都输出 `RESULT: GREEN/RED` + 退出码。判定依据：

1. `tools/validate_static.py` 通过：八套脚本生成器与三张决议 DDS 逐文件 parity、全部运行文件 UTF-8 BOM、9 语言 loc 引用与首世/账簿/廷臣窗口格式 token parity、原生决议分组/前缀图标/三张独立插画、自动发现的全部 XAR event/decision AI 闸门、挑战继承/成长基线、契约 hook/PB/图鉴/里程碑、生产/selftest 共用入口、21 个当铺购买 effect、付费廷臣五类目录计数/数值边界/原生元数据与冲突/玩家隔离/确认前零副作用/单次扣金、无继承人 fallback/原生继承窗投影、奖池过滤/权重/稳定 ID、descriptor 与发布资源；其中 `tools/validate_loc.py` 负责动态 wrapper、custom-loc 和 modifier 名。
2. debug.log 的 57 个具名 `XAR: TEST PASS`、`XAR: TEST sweep complete`、零 `FAIL` 及 `DONE` 标记全部出现（自测 effect：`common/scripted_effects/xar_selftest_effects.txt`，
   由游戏规则第三档 `xar_selftest` 触发，检查器 xar.0007 嵌套在结算事件 xar.1001 里跑）
3. OCR 真实接受契约、购买外交、结束商店，再依次真实点击重抽、拒绝、祝福、封印、第二次祝福和最终咒痕；验证动态文本无 raw/fallback，并断言 token 消耗、拒绝基线、封印免除效果及封印后的正常咒痕。
4. 从原生右栏进入决议面板，真实执行【琉焰账簿】并关闭，断言快照生成和五个临时 global 清理；随后真实执行【选择本世契约】并选择【征服者】，断言生产 effect 写入契约。
5. 通过 acceptance-only GUI 直接调用 `DefaultOnCharacterClick(GetPlayer.GetID)` 打开玩家原生人物页，以 DDS 模板定位【琉焰之视】，hover 后 OCR 确认“当前分量”实时渲染。
6. 结算确认后必须从原生 HUD OCR 到「正在观察」，证明观察者切换真实完成。
7. **error.log 中任何包含 `xar` 的日志，以及任何 `failed to read trait level star texture` 都视为项目失败**，不再白名单过滤。后者必须单列，因为 `_stars_N.dds` 是按 track entry 数生成的通用路径，错误行本身不含 mod 前缀。
8. 铁人终局必须三次读取同一底栏日期证明时间冻结，并完成原生菜单 resume 重阻断、自动保存退出、主菜单重载和重载后重阻断；真实 Documents 受保护文件与本地 Steam userdata 后备目录快照任一变化均判 RED。

截图证据和 JSON 摘要在控制台报告里的 artifacts 目录。

### GitHub 官方 CI 与本机 L1-L3

`.github/workflows/static-ci.yml` 只使用 GitHub 官方 `windows-latest`。每次 push/PR 都安装最小静态依赖并执行 Python 编译、no-heir 投影测试、两套 release manifest 测试、`validate_static.py`、`validate_vivhite_static.py`、计分 reference vectors 和两套 `build_*_release.py --check`；手动触发或对应 `v*`/`vivhite-v*` tag 时额外构建并上传匹配的 ZIP/manifest，tag 构建仍要求 clean worktree、HEAD 上存在正确命名的版本 tag。

官方 runner 没有 CK3、Steam 授权、工坊缓存、用户目录或可靠交互桌面，因此禁止调用 `run_acceptance.py` 或 `run_vivhite_acceptance.py`，也不能把云端 L0 表述成引擎或 UI 已验。官方 CI 能证明生成器 parity、BOM/loc、玩家/AI 闸门、release allowlist、acceptance 剥离和构建可复现；不能证明 Paradox 运行时语义、跨存档落盘、鼠标/OCR 或游戏日期推进。

真实游戏层在本机串行执行并保存 artifacts：

- L1：`off`，production release 投影冷启动、引擎解析及禁用规则负例。
- L2：`selftest`、`persistence-restart`、`death-edges`、`death-with-heir`、`bargain-reopen`、`progression-ui`、`scoring-matrix`、`courtier-creator`，覆盖 57 项机制断言、200 effect body 与 200 dispatcher runtime sweep、两进程持久化、AI/无继承人/普通继承死亡边界、三轮生产交易的 1094/1095 日边界、PB/图鉴/里程碑生产链、受控后代去重/深度/死亡中间节点计分，以及付费廷臣两次真实交易与动态目录。
- L3：`on-first-life`、`on-recorded`、`on-high-budget`，覆盖 production-only 首世、已有纪录和第四页高预算真实 OCR/点击。L2 的交易 UI、决议、trait hover 和无继承人窗口也计入整体 L3 证据，不重复启动。
- 白绮独立版并行门禁：专用三格矩阵覆盖 standalone 完整购买链、双 mod 两种实际 mount 顺序、状态隔离、各自单次交付/扣款、AI 闸门、零阻塞性项目诊断及真实用户存储零改动；该矩阵不使用原 mod 的 Workshop item 或真实缓存，已知原 mod loc-only 警告必须透明记录。

本机报告必须记录 JSON/JUnit、截图、runtime hash 和本次增量 `debug/error/gui_warnings`；发布 QA 引用具体 run ID，不把未运行的远端 CK3 状态写成 GREEN。GitHub tag artifact 只提供经过 L0 验证的候选 ZIP/manifest，不自动创建 GitHub Release 或上传 Steam。

### 覆盖边界（什么算验过、什么不算）

**验过的**：
- 奖池全部 200 条目的**运行期执行**：自测在死前跑 `xar_test_sweep_effect`（生成器产出，
  每条 code 内联按序施加），带 `xar` 上下文的报错会被 error.log 扫描抓红（drain 修正漏定义就是这样抓到的）
- 引擎解析 + PostValidate 静态校验全部生成文件
- **当前校验范围内的静态 loc 全覆盖**：event/custom-loc/GUI/trait/rule/modifier 引用、奖池目标键与五个 wrapper 精确表达式，均检查 9 语言。
- 生产契约接受、商店外交购买与结束、祝福三选一、诅咒二选一的简中实际像素渲染和点击。
- 商店样例的扣款 `200→175`、整数价格 `25→30`、纯脚本小数涨价 `11→14`、外交增长，以及余分换金币。
- 契约事件与纯脚本 selftest 都调用 `xar_enable_player_pact_effect`、`xar_initialize_run_state_effect`；外交生产 option 与 `25→30`/扣款脚本样例都调用 `xar_buy_diplomacy_shop_item_effect`。静态校验禁止两处重新内联对应实现。
- 14 个可重复购买商品和宗教改革/三种高价批量商品/三种冠冕服务各自调用具名生产 effect；166600 点自测先购买原四种固定商品并断言余 5467，再购买重抽、封印和三种冠冕服务并断言余 3217、代币涨价和所有权。商店结束调用 `xar_finish_shop_effect` 完成余分兑换、清零及垂青会初始化。
- 原生 trait track 的 100 XP/10 级、每对 +1 XP、满级状态及 hover 当前分数的实际像素渲染；hover 公式还与死亡结算值作脚本断言。
- 生产里程碑 effect 在 10/20 XP 发放早期单枚代币，30-100 XP 逐步升级为重抽/封印组合，并同步增加原生属性；selftest 精确断言 30 XP 奖励和 40-100 XP 累计奖励。UI 真实消耗重抽与封印，并验证拒绝未发祝福、封印未施加首个咒痕、下一次正常接受施加了咒痕。
- 传说祝福只抽到稀有/传说诅咒、拒绝每次 -1% 最终分、request/ready/consumed 零值导入、同阈值不破纪录、跨阈值破纪录、cap 量化、死亡结算、纪录写入和教程落盘。
- 0/25/50/100% 继承的生产 effect；1200、5000、50000、166600 四档均实机脚本断言无额外预算封顶，2000 production-only UI 场景覆盖第四页冠冕服务和 1133 分宗教改革。AI 兄弟 scope 还会实际调用契约进度和导入消费 effect，确认 `is_ai = no` 在运行期阻断。
- 奖池 200 个 effect body 的运行期语法/引用 smoke test
- 静态验证首世 0 纪录分流和 selftest 200 点优先分支，并逐阈值校验账簿 candidate/next/gap 生成关系、cap 状态、七个展示字段及禁止写纪录/资源的边界；纯脚本自测直接调用生产 `xar_prepare_ledger_effect`，断言非负分数、投影关系和历史纪录不变后清理临时 global，不打开账簿 UI。
- 原生决议面板实际点击【琉焰账簿】和【选择本世契约】：账簿 UI 验证只读快照及关闭清理，契约 UI 验证确认页、`xar.2000` 和【征服者】生产选项。
- 账簿生产 UI 用三个连续事件分别捕获即时分数、投影阈值、复制显示快照；2026-08-18 实机证明只用一个或两个事件会让同一 `immediate` 的读后写依赖产生 `none`，三阶段链为 0 `xar` errors。
- `persistence-restart` 两进程实测：A 写入非零余烬 lesson 后完全退出，B 在 `process_b_preseeded=false` 且 `tutorial.txt` handoff SHA-256 不变的前提下导入同一位阶；JSON 记录两 PID 生命周期对应的耗时、位阶和 hash。
- 真实 AI 死亡负例：目标明确带 `xa_enabled`，引擎 `on_death` observer 确认死亡，但 `XAR: computing score on death` 在 AI 区间内未出现且分数 sentinel 未变。无继承人链验证 `player_heir` 确实为空、计分/写位与快照按前向事件边界提交；OCR/像素覆盖八项数值、无「继续扮演」、原生退出确认及主菜单。最新 GREEN：`xar_accept_fmq_wxxc`，0 `xar` errors。
- 独立 `bargain-reopen` 开发树场景覆盖生产一场一对语义：三轮真实 options/dispatchers、累计对数 1/2/3、session `1→0`、XP `0→1→2→3`、拒绝数 0。每轮 acceptance-only day-1094 probe 与生产 `xar.0006 days = 1095` 都用 `current_date - 成交日` 分别精确断言 1094/1095，三个生产 reset marker 必须有序且第三次确实打开下一场。2026-08-19 首次完整 GREEN：`xar_accept_ue4ye_un`，九游戏年、三次生产 reset、0 `xar` errors。
- 独立 `progression-ui` 开发树场景覆盖生产贤王 3/6/10 和【琉焰之视】10 XP 事件的正文、选项与真实点击；四个 tutorial lesson 必须精确落盘，原生账簿必须同帧显示当前 `0/10`、`PB 10`、贤王已完成、`R 1`、`S 0`。2026-08-19 首次完整 GREEN：`xar_accept_gqppgi_f`，图鉴 mask 16，0 `xar` errors。
- 独立 `scoring-matrix` 开发树场景实测 1–5 代计入、第六代排除、同一后代双路径只计一次、穿过已故中间节点后继续计分、清理不对 dead scope 执行 flag effect，并比较 preview/生产误差。全部 200 个稳定 wire ID 还会逐一穿过生产 dispatcher，结合冻结语义契约证明 ID→effect/filter/weight 映射。2026-08-19 GREEN：`xar_accept_h0lgmvyf`，200/200 marker，0 `xar` errors。
- 非 debug 终局双路径实测：`xar_terminal_observer_nondebug3_20260821` 从开发夹具中的生产 `observe` 分支进入原生观察者 HUD；`xar_terminal_ironman_nondebug9_20260821` 完成强制暂停、resume 重阻断、原生自动保存退出、主菜单同进程重载与重载后阻断。两轮都实际 hover 十级【琉焰之视】，其完整 1–10 轨道可见且不再产生旧 run 中的 248 条 `_stars_10.dds` 错误。铁人轮的三个日期检查均强制读出并固定在同一日，隔离存档重载前后路径/大小/SHA-256 相同；真实 Documents 的 9 个受保护文件与本地 Steam app 1158310 userdata 的 2 个文件在五秒观察窗内聚合哈希不变，隔离 userdir 删除后实际不存在。两轮 runtime tree 均为 `235d92fb36fd1052b0261c05f059e525d76a06231a7b92a8a27cc8e6764d242a`，harness 为 `f56a0e364198e6fe1be465d447d1f5170965de275e6a28e4d443ca68934e7b9f`，且均为 0 project errors。该证据不等于 release projection 运行或远端 Steam Cloud 审计。
- 2026-08-21 最终 exact-candidate 套件绑定提交 `45cf7ea`：`xar_final85_selftest_20260821`、`xar_final85_persistence_20260821`、两条 `xar_final85_death_*`、`xar_final85_bargain_20260821`、`xar_final85_progression_20260821`、`xar_final85_scoring_matrix_20260821`、`xar_final85_courtier_creator_20260821` 与四条 `xar_final85_on_*/off_20260821` 全部 GREEN，0 project errors。开发树 runtime 为 `235d92fb36fd1052b0261c05f059e525d76a06231a7b92a8a27cc8e6764d242a`；四条 production smoke 实际加载从它构建并剥离验收夹具的 85 文件 projection `29dde4460b7f86b1779e902712e856776dd99de703802a92a64c1fa39c28d221`。每条报告均保存 JSON/JUnit、截图与增量日志；该结论只关闭自动化候选回归，不替代九语言人工审校、干净截图、Workshop 强制重下载或发布签核。
- 2026-08-21 白绮独立版 hardened schema-v2 三格矩阵 `ervc_acceptance_hardened_final_20260821`：非 debug CK3 `1.19.0.6` 串行完成 standalone 与双 mod 两种加载顺序，3/3 GREEN、0 blocking project diagnostics。Vivhite production projection 为 `93fb559a61ace1a3c2bd8a9680a0ed5039db765753da8c787d28b0dd67c09fef`，原 mod projection 为 `97b9f386ab17364eec0859be1f7c6407816a27a396b2edcf6427d697789ba2ab`；debug mount 顺序逐格精确匹配请求顺序且 fixture 均最后加载，两种顺序都证明两个决议组及其直属决议行、ERVC 348/XAR 120 独立状态、最终 532 金与两次独立交付。双 mod 格各自透明记录原 mod 冻结代码的 `xa_curse_a_rarity` / `xa_curse_b_rarity` 两类 loc-only unused-variable 已知警告，没有以漏扫 `xa_` 隐藏；除此之外 `error.log`、`gui_warnings.log`、`database_conflicts.log` 无项目诊断。CK3 可执行文件逐格前后 SHA-256 均为 `2d00ff3101ef70b566f2fcbae292f09263199c80e9dc8f139b82d7d96f83db86`。真实 profile、Steam cloud 后备目录、82 个已注册 Workshop target 的 162,960 项递归元数据在完整扫描后再等待五秒并复扫，聚合哈希保持 `ed9a9cce6db99148f08aac997d38caae00f64c79827fdb1dcf642c3af9c38336`；三个 disposable userdir 与 detached watchdog 均实际退出/删除。该证据不替代 clean committed-candidate 重跑、品牌差异审阅或新 Workshop cache 验证。

- 2026-08-21 发布本地化候选矩阵 `ervc_release_final_20260821`：3/3 GREEN、876.590 秒、0 blocking project diagnostics，Vivhite projection 更新为 `6242ca7eec1b33f6da939c3a161b7338011122780c4740c6e831e2de0e20577c`；原 mod、两类 fixture、CK3 EXE 与受保护存储哈希均保持上述值。七页功能、两种双 mod 加载顺序和全部购买/隔离 marker 再次通过，三个 userdir 与 watchdog 均已消失。
- 2026-08-21 clean committed-candidate 矩阵 `ervc_release_clean_6575997_20260821` 绑定完整提交 `6575997b14a90b0afda75fdde304170206478c21`：3/3 GREEN、910.962 秒、0 blocking diagnostics，runtime/fixture/EXE/受保护存储哈希与上一轮完全一致。standalone 同时留存决议入口和七个子页的八张 2560×1440 原始截图；tag `vivhite-v1.0.0` 指向同一提交。
- 2026-08-21 白绮 `1.0.1` clean committed-candidate 矩阵 `ervc_v101_clean_092e61b_retry_20260821` 绑定完整提交 `092e61bf2fa9d90167eea91369ac8bb4bfa1b543`：3/3 GREEN、887.637 秒、0 blocking diagnostics。Vivhite production projection 为 `f00898467746145316ff850c898d6402709e19c612044f9945d3af280d0e576c`，原 mod 与两类 fixture 哈希保持不变；9 个真实 profile 文件、2 个 Steam cloud 文件、82 个已注册 Workshop target 的 162,960 项元数据在五秒复扫前后保持 `541376448f2073679434cc2aac109c619a4efca89e911bb12e0c6dcd800a4e22`，三个 userdir 均删除。前一目录 `ervc_v101_clean_092e61b_20260821` 因 JetBrains stale-index 通知遮住大厅【开始】而在任何 fixture marker 前 OCR RED；原报告保留 RED，关闭通知后使用全新目录完整重跑，不把基础设施失败重标为 GREEN。

**没验的**：
- 数值是否符合最初产品意图仍需人工平衡审阅；冻结契约能阻止未审阅的 `50→500` 或 ID 重排，但不能证明首次冻结前的设计值天然正确。
- 付费廷臣尚未独立验证无地玩家交付、跨进程配置保留和九语言窗口截断；`xar_final85_courtier_creator_20260821` 已在最终树覆盖登陆玩家的完整功能链及真实非默认文化/信仰。
- 长期平衡只有 `synthetic --balance-smoke-pairs 2` 的短烟测证据；kind 4 自然死亡、40 年/14 对/pair 10 和四夹具串行矩阵均未完成，但这些只属于非门禁 soak/stability/telemetry，不证明数值平衡。
- 九语言已有源文本，不等于母语级术语/人格审核或游戏内窗口截断验收。

### 关键事实（2026-08-17 实证，血泪）

- **游戏加载的是 Steam 工坊缓存，不是仓库 dev 目录**：dev .mod 带 `remote_file_id` 后启动器
  把它和工坊订阅合并，播放集里生效的是 `mod/ugc_3784706360.mod`
  （内容在 `Z:\SteamLibrary\steamapps\workshop\content\1158310\3784706360`）。
  **改完代码在游戏里看不到，先怀疑这个**。runner 每次跑前 robocopy /MIR 仓库 → 工坊缓存
  （用户已批准，不恢复；工坊更新时 Steam 会重下复原）。
- **大厅规则选择持久化在 `player\game_rules\presets.txt` 的 `LastAppliedRules` 块**，新开局重放它；
  改规则文件的 `default` 不影响已有档案。runner 会先移除该块内全部 `xar_on/xar_off/xar_selftest`，再写入场景目标值并验证同时只剩一个（事后恢复）。
- **pyautogui 合成键盘事件进不了 CK3**（esc/space/+ 实测全部无效），鼠标点击有效。
  解暂停只能点底栏日期旁的 ▶（坐标 (2315,1410)@2560x1440）。
- 速度 5 也必须走鼠标：原生 `timeline_widget` 最右侧 `speed_5` hitbox 中心约 `(2536,1418)@2560x1440`。2026-08-19 对照截图与原生 `hud.gui` 实测：该按钮只执行 `SetGameSpeed`，不会解除手动暂停；但关闭运行中弹出的原生事件会自动恢复时间，此时再点 ▶ 反而会暂停。`bargain-reopen` 现 deliberate-click 速度 5 后先观察底栏日期 2 秒，仅在尚未前进时 deliberate-click OCR 识别出的日期按钮，最终要求日期在 10 秒内前进才视为成功。
- 旧 acceptance runner 每次 OCR/点击前会用 `AttachThreadInput` + Alt 抢回并反证 CK3 前台；2026-08-19 曾实测裸 `SetForegroundWindow` 被 Windows 前台锁静默拒绝后，runner 把 OpenCode 整窗识别成事件选项。该做法只属于旧验收工具，不能移植到合法自主玩家。Phase B sealed menu smoke 改为主证据链 write-ahead 后的一次 direct exact-HWND 激活，以及至多一次 caller→同一个稳定前台线程的严格 attach/detach fallback；不使用 Alt、PyAutoGUI、鼠标或 `SendInput`，任何身份、detach 或前台后置条件未知都立即 RED 且不重试。
- `parentanchor = center` 的小型验收 widget 不要点击精确屏幕中心：锚点可能落在 64×64 控件边界并穿透到地图。`xar_trait_test_window` 改为点击中心内偏移 20 px；最终咒痕后还要先按渲染出的“暂停”状态锁住一日死亡计时，完成特质 hover 后才恢复时间。2026-08-20 CK3 1.19.0.6 实测。
- 主菜单【新游戏】也必须 deliberate-click 并以罗贝尔书签实际出现作反证；2026-08-19 实测 OCR 找到按钮后的一次瞬时点击可被 CK3 丢弃，runner 若直接进入 30 秒书签等待只会在原主菜单超时。
- 安全软件、Chrome 与 JetBrains 通知都可能置顶遮住大厅“开始”按钮。2026-08-22 两次 opening 实测同一 YouTube/Chrome 通知持续覆盖该按钮；Windows Toast 总开关和应用级 banner 开关不足以阻止它再次出现，最终必须把 Chrome Default profile 的默认通知和 8 个显式允许站点全部改为阻止。用户已持续授权自动游玩期间立即关闭任何右下角 Toast；只能点击通知自身的【关闭】，不得点击通知正文。原 RED 保持原结论，清理后使用全新 run。
- 截图读坐标要用 PIL 裁真实 PNG（2560x1440）实测——聊天里显示的图有缩放，目测坐标必歪。
- 2026-08-22 `20260822T130230Z-opening-cb15ab30` 再次实证这一点：聊天预览把 2560×1440 缩到
  2048×1152，直接读出的 HUD 生活方式中心 `(278,1118)` 必须两轴同时乘 1.25；只修 Y 得到
  `(278,1398)` 会以 `SendInput 2/2` 点中角色压力状态条，画面继续保持 `map_hud`。原版 `hud.gui`
  的 `bottom_left_button_row` 排列与真实 PNG 共同给出生活方式按钮中心约 `(348,1398)`。
- 修正坐标后的 `20260822T131930Z-opening-a4f7cfab` 已真实打开【选择生活方式】：标题框
  `[1192,30,1370,64]`，军事框 `[842,367,913,407]`，管理框 `[1208,367,1279,408]`。
  旧 classifier 把居中标题限制在左侧 `x≤0.24`，因此画面虽正确却连续判 unknown；选择页标题区域应覆盖
  屏幕中部 `x=0.40..0.60`，军事/管理仍由各自可见 OCR 框动态定位。
- `20260822T133343Z-opening-1c6306f5` 随后已真实进入军事生活方式页；标题 `[60,57,325,100]`，
  【生活方式重心】`[501,284,617,308]`，【当前：无重心】`[500,328,617,352]`，可点击的【权威重心】
  `[430,706,526,734]`。旧 fixture 把前两项虚构在 y≈520/565，导致真实页面再次判 unknown；分类区域现按这张
  2560×1440 实机 PNG 校准，权威按钮继续从 OCR 框动态取点。
- 发布截图还要检查画面中心：2026-08-21 的 non-debug terminal artifact 实测把 CK3 原生
  `clausewitz/gfx/cursors/software_cursor_normal.dds`（100x100）留在 `(1280,720)`；它在地图上是深色方框，
  还会透过半透明事件窗，看起来像坏掉的事件控件。该方框不是 mod GUI。发布衍生图应优先换用无光标帧或收紧裁切；
  若只能用同帧事件图，只能从同一次 run、同一固定事件背景的无光标帧恢复该区域，并在截图来源文档记录坐标，禁止
  用生成式补图伪造游戏内容。软件光标滞留在画面中心的具体引擎触发条件**未查明**；规避必须依靠发布前逐帧检查，
  不能假定移动 Windows 硬件光标就会让它从 `ImageGrab` artifact 中消失。
- OCR 定位按钮必须避免正文中的同词。2026-08-21 铁人 modal 的正文含“打开游戏菜单”，全屏 `contains=True` 会点到正文而不是底部按钮；按钮改在 modal 区域做精确匹配。RapidOCR 还会把 CK3 字体的“余烬”稳定识别为“余焰”，流程断言因此使用唯一后缀“已封存”，不修改正确的产品文案。
- `pdx_enum_setting.cpp` 在真实 profile 和隔离 profile 均可能先记录 `Could not find enum 'l_simp_chinese' ... default 'l_english'`，但随后实际画面仍是简中；该启动期 debug 行不能单独证明最终渲染语言，验收以画面 OCR 和本地化结构为准。2026-08-21 非 debug 铁人实测。
- 隔离 runner 只终止自己记录的 CK3 PID。若 preflight 后、真正 launch 前又出现任意 `ck3.exe`，必须 RED 并拒绝启动测试，不得调用按镜像名全局强杀；否则会误杀用户刚开启的真实会话。后置安全检查同样属于权威结果，失败时 JSON、JUnit 与退出码必须一起 RED。2026-08-21 runner 审阅加固。
- full selftest 的最终咒痕 option 不能只在 1 游戏日后排入强制死亡：character event 关闭会自动恢复时间，runner 尚在打开账簿/契约/trait hover 时，死亡窗便可能抢先覆盖决议面板。acceptance-only 首次 `xar.0008` 现留 30 日 UI 宽限，若 importer 尚未交付才继续逐日轮询；release 投影完整剥离该夹具。2026-08-21 两次非 debug 铁人 RED 截图复现。
- 长测日期 12 秒不推进时禁止盲点固定坐标。runner 每次用单调递增序号保存 `stall_<场景>_<序号>.png`、候选框标注图和完整 OCR JSON：在画面下部找真实选项，并在候选栏中优先同一 x 轴纵向堆叠的最下行。点击后必须观察到日期继续推进；连续三次仍卡住立即 RED，并由执行者读取这些截图/OCR 分析，不能继续空点到总超时。2026-08-18 实测定位：全宽事件【摆脱尘世】的选项约在 `(0.68,0.79)`，旧恢复点 `(0.38,0.72)` 落在正文空白处。2026-08-19 【诺曼人的西西里】实测三个真实选项纵向对齐在 `x≈930`，人物名位于 `x≈1377/1841`，按右侧优先会误开人物面板；【埃玛成年】仅有一个左侧选项 `x≈930`，人物名/关系则纵向对齐在 `x≈1505`，不能只按列密度判断。【对未来的思考】实测人物页会在真实选项下方露出被纵向裁切的地图标签，OCR 将其识别为高框并误当成同列最末选项；经典选项现限制为 `x=0.34..0.41`、`y≤0.75` 且 OCR 框高不超过画面 `3.5%`。互动信函【要求改信】【剥夺头衔】会把真实 `拒绝/同意` 按钮放到 `y≈0.79`，其效果正文却占满旧候选区，因此两个精确动作标签优先于正文。全宽【波希米亚的宫廷】正文会侵入 `x≈0.42`，真实选项位于 `x≈0.68`；没有经典栏时，runner 先选右侧纵列，再退回中栏。同期实测 `debug.log` 在无事件时可长期没有日期行，不能用它单独判断冻结；长测改读底栏 `公元 Y年M月D日` 的实际像素。
- 2026-08-20 【精神崩溃：心脏疼痛】的花体选项没有被 OCR 读出。旧特判把 y 写死为画面高度 `0.91`，实际点到 `(928,1310)` 的地图并循环 122 次；真实按钮框为 `[621,1020,1247,1064]`、中心 `(934,1042)`。现从标题下方 Canny/Hough 横边配对出全部符合 CK3 option 比例的矩形，按框尺寸、横向对齐和置信度选择；检测不到可信框就不点击，同一 resume modal 三次无进展立即 RED。离线缩放到 0.75/1.0/1.25 倍均命中同一归一位置。
- 暂停链因场景而异。`selftest`/`death-with-heir` 的普通继承路径是：开局默认暂停 → 原生继承窗强制暂停 → OCR 精确点击「继续扮演」约 `(1453,1129)` → 等待生产结算事件；不得把继承窗右栏约 `(1721,1048)` 的「处于战争」状态交给通用纵列算法。
- `balance-long` 的自然死亡同样使用精确「继续扮演」路径，但生产 terminal 不再依赖死者 event 排队：`on_death` 先保存 dead/carrier scope 并排入存活继承人的 `delayed = yes` dispatch，再内联计算；延迟边界后只用预先建立的 pact/fixture character globals 认证，不重查会在死亡时清除的角色 flag。runner 最多等待 30 秒 kind 4 terminal wire，且不采集继承人的后续普通样本。
- 大厅路径坐标（2560x1440）：新游戏 (600,560) → 1066 罗贝尔卡 (1600,1230)（有儿子必有继承人）
  → 开始 (2257,1245)。结算确认选项 (1130,1041)（点了进观察者模式，桥有效）。
- 2026-08-22 opening 实测罗贝尔标签 hover 后会从中心 y≈1211 上移到 y≈1203，且标签/卡片像素持续动画；点击标签本身不会选中。自主玩家因此从唯一 OCR 标签派生 `(0,-130)` 的头像点击点并按住 120 ms，只对该控件允许最终 hover patch 动画，仍保留唯一标签、窗口前台、点击点归属与后置 `bookmark_lobby_selected` 反证。
- 同次 opening 后续实测，“开始”按钮的 hover 说明框会盖住地图上的罗贝尔标签；已选中状态必须改用右侧详情面板的【公爵罗贝尔，51岁】与可见【开始】共同分类，不能继续依赖被 tooltip 遮挡的地图标签。
- 【开始】按钮的 hover 高亮也会在 OCR 帧与最终点击前 patch 之间持续改变像素；`20260822T095109Z-opening-10f49d7e` 已实证两个 SHA-256 不同且 `SendInput` 尚未调用。opening 合约因此只对该按钮放宽静态 patch 相等，仍要求唯一【开始】、右侧罗贝尔详情、前台/点击点归属与点击后【终末之契】反证。
- 关闭 Chrome 后，提交 `3a292c8`、环境 `13496c86f545eee215a5adac679c027c05ad03d5f789b99fdee6b3c02e720221` 的
  `20260822T095721Z-opening-019ba6a7` 首次 GREEN：新游戏、罗贝尔、开始三次收据均 `SendInput 2/2`，最终两帧 OCR
  【终末之契】与【又见面了，旅人。】，随后 Job active 归零、tree gone、双源 CK3 inventory 为空。该 run 没有点击契约选项。
- 随后的提交 `c8a27d5`、环境 `f54ca88ac450ae8d2c4d7401e115695069ac10781e2a37e8af14cc5d3521304d` 中，
  `20260822T102802Z-opening-4cc459ce` 完成七次 `SendInput 2/2`：接受契约、开始此生，并按可见文本选择
  【兵棋的余局（+500军事经验）】与较低损失的【千面的哑剧（-1000谋略经验）】。最终连续两帧识别 `map_hud`，
  Job active 归零、tree gone、双源 CK3 inventory 为空；这是首个完成祝福/咒痕对并进入地图的可计分开局基线。
- 提交 `106278f`、环境 `f11b248ccc09bb80b5a9d92f0b9e3bc19646af333d21ccd0961183d583c09cbe` 的
  `20260822T111130Z-opening-a27391b9` 又执行第八次 `SendInput 2/2`，从地图 HUD 打开玩家角色页。最终双帧分类为
  `player_character`，OCR 读出罗贝尔本人、配偶、玩家继承人与 7 名臣属；截图人工复核正确，进程树与双源 CK3 inventory
  清理为 GREEN。该切片用于证明地图内状态读取，不代表已完成任何治理决策。
- 用户真实纪录靠 tutorial.txt 备份/恢复保护；默认 selftest 与 `on-first-life/off` 会剥掉 `xar_hs_ge_*` 行（纪录 0），`on-recorded` 固定预置 100；`--import-record 100` 仅改变 selftest。
- restore watchdog 等 runner 退出后，只终止 runner 启动的 CK3 PID，再用临时文件 + `os.replace` 原子恢复并做 SHA-256 校验。2026-08-20 实测发现宿主超时会终止 runner 的整个子进程树，普通 `Popen(CREATE_NO_WINDOW)` watchdog 也被一起杀死，遗留隔离后的 `dlc_load.json` 与测试 autosave；已从该次精确 backup 全量恢复并核对六项 hash。watchdog 现由 WMI `Win32_Process.Create` 启动在 runner 进程树之外。2026-08-19 另实测 dev selftest autosave 会让下一次 release 投影扫描已剥离的 `xar_selftest` 规则键并误报；现启动前先完整复制并校验全部 `autosave*.ck3`，写 ready 标记后才移走，结束时删除测试 autosave 并恢复原件。
- 2026-08-19 长期平衡摇测发现当前播放集还启用了四个自动控制/改宗 mod，会污染领地、信仰与资源结果。runner 现同时备份 `dlc_load.json`，启动前把 `enabled_mods` 精确收敛为 `mod/ugc_3784706360.mod`，杀死测试 CK3 后再恢复；watchdog 同样覆盖此文件。
- `--artifacts-dir` 只创建调用方给定的新目录；CI 上传只包含从本次日志 offset 起的新内容，严禁用 `%TEMP%\xar_accept*` 通配上传，因为 `xar_accept_backup_*` 可能含玩家现场。
- 2026-08-21 同一发布候选的第一次矩阵在第二格到达主菜单前发生 CK3 原生 `C0000005`，crash bundle 停在数据库图标初始化，无 fixture marker、无 blocking project diagnostic，运行树、EXE 与受保护存储未变。该 RED 必须原样保留；只有全新 userdir 的同格重试完整 GREEN，且随后另一全新目录的正式三格矩阵 3/3 GREEN，才能把它判为一次性引擎冷启动崩溃，禁止直接重标原报告。
- Windows Python Launcher 的 `py <script.py>` 会解释脚本首行的 `/usr/bin/env python3`，可能选中 `PATH` 里的另一套 Python，而不是刚由 `py -m pip` 安装依赖的默认解释器。2026-08-21 实测该分裂让非固定 Pillow 重建的三张 DXT1 DDS 与仓库字节不同，产生假 stale；项目 `.venv` 的 `Pillow==12.3.0` 与官方 CI 均 GREEN。遇到素材 parity 全红时先打印实际解释器和 Pillow 版本，本机 L0 优先直接调用 `tools\.venv\Scripts\python.exe`，禁止为消除环境假红而重写已发布素材。
- `ToggleGameViewData('character', GetPlayer.GetID)` 可能保留地图当前选中角色；要确定打开玩家本人，直接用原版 `button_me` 同款动作 `DefaultOnCharacterClick(GetPlayer.GetID)`（2026-08-18 实测）。
- trait 含原生 `track` 时，UI 会自动读取 `gfx/interface/icons/trait_level_tracks/<trait_key>.dds`；缺文件会在真正 hover 时写 VFS error，主 trait 的 `icon =` 不会替代它（2026-08-18 实测）。
- 原生决议右栏按钮是 `F8` 对应的羽笔图标；合成键盘无效时可按屏幕比例 `(0.987, 0.367)` hover，先 OCR 验证“决议”tooltip 再点击。低处条目必须在滚动框内下滚到中段后用 `deliberate_click`，否则底缘 hit-test 会关闭面板但不选中。决议触发的事件或 scripted GUI 关闭后，决议面板会随动画恢复；先等待并复查面板标题，再决定是否点 HUD，否则会把刚恢复的面板反向关掉（2026-08-18/20 实测）。

## 断点标记法（链路定位）

在每个环节插 `debug_log = "XAR: <步骤名>"`（项目约定 XAR: 前缀），然后：

```powershell
(Select-String -Path "...\logs\debug.log" -Pattern "XAR:").Line
```

链条断在哪一目了然。生成器生成的文件也可以带标记（本项目导入 scripted_gui 每条都带 k 值标记）。

## 运行时行为验证

- 全局存储落盘：直接读 `tutorial.txt` 数 `xar_hs_ge_*` 条目
- 控制台：`die`（死亡链）、`event xar.0001`（手动触发事件）、`effect xxx`（跑 effect）
- 修改后必须重启游戏（无热重载）；`-load` 启动参数实测无效（1.19.0.6）

## GUI 调试

- debug 模式工具栏：`Gui.Debug`、GUI Editor、Script Profiler
- 可视化调试面板：临时注册一个可见窗口，用 `text = "[Tutorial.GetStepText]"` 之类实时显示数据表达式的值（本项目用它发现 Tutorial 上下文在外部窗口为空）
- GUI 表达式解析错误：`error.log` 的 `pdx_data_factory.cpp` / `pdx_gui_factory.cpp` 条目（含文件行号）

## 自动化测试 harness（GUI 桥方案，已被 runner 取代）

GUI state + `ExecuteConsoleCommand` 可以在进游戏后自动执行控制台命令（打标记、设变量、触发事件）。注意：窗口必须注册；`ExecuteConsoleCommand` 在 state 的 on_start 里可用性未完全验证（本项目后来改用真实链路测试，最终定型为上文的全自动验收 runner）。

## 排障心法

1. **先分清"没加载/没注册"与"加载了但没触发"**——CK3 大量失败是静默的
2. 报错要看完整调用栈（"while building tooltip/description" 这类后缀说明评估时机）
3. 怀疑优先级：目录名 > BOM > 注册 > scope 类型 > 求值时机（并发/延迟）> 逻辑
4. 对照原版/成熟 mod（POD）的同类写法是最快的验证手段
