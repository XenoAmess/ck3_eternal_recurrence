# R2 真实运行错误与主树离线修复

本记录对应 `machine_id: pc-20260924rtuf-f11af23c08`，观察时间 `2026-10-21T21:37:38+00:00`。机器身份由 `tools/ck3_live_run_id.py machine` 实际读回；原始文件路径、字节数和 SHA-256 均见[配套 JSON](runtime-r2-issues.json)。这是**真实运行 RED 后的离线修复记录**，修复后新加载和业务验收状态均为 `NOT_RUN`。

## 绑定的真实输入

- 场次：`pc-20260924rtuf-f11af23c08--living-artifacts--R0002`，原进程 PID `10924`，原 `psutil.create_time()` 秒值按字符串保留为 `1792617442.7227743`，native generation `1`（不是整数 FILETIME；generation 由 root 的 retained native binding 提供，出生时间另有原始 identity 回执）。
- 原冻结源码：外置 `runtime/c03`，实际 `git rev-parse HEAD` 为 `c78bec01ca1bc48aa85d19b370f5f12ed31e599f`；内容生成器 SHA-256 为 `deedfc0df0f39f15f6e652dd72d229c161a38a0977fab86eaefb0621b7c3f5a9`。
- 真实加载正式候选：`builds/candidate-46cac62bd`，由本场 `allocated-context.json` 绑定。其 `common/scripted_effects/xalw_content_01.txt` 为 247779 字节，SHA-256 `5a0e3d3d0e865a2b104fff5b01dd94d2e811000e5b9a090fad1cef73bd07bb7a`。
- 原错误日志：外置 `runtime/profiles/living-core-a03/state/profile/logs/error.log`，518693 字节、6562 行，SHA-256 `81deb752a5b48b8d9f3267f3aebc977b185796eae076df73440699c79ae933c4`。日志时钟是本机 UTC+08，`05:18–05:23` 对应 `2026-10-21T21:18–21:23Z`。
- 原 v1 adapter 回执 `living-artifacts-core-result.json` 在 `2026-10-21T21:24:24.527367+00:00` 将 `CORE-NATIVE-EQUIP-01` 记为 `BLOCKED`：其原罗贝尔身份判定与实际场景不符。后续独立原生查询已证明原件 `402` 真正装备，详见下方追加结果；v1 原始回执不回写为 PASS，也不据此宣称经验或喂养通过。

源码修复没有手工改写原 profile 的 mod/fixture 脚本、冻结 c03、candidate46、已安装游戏或 Steam；实际游戏推进、保存及运行器写入日志/回执照常保留。持续写入的运行回执以后可能改变；本记录 SHA 只绑定观察时实际读取的字节，不将后续文件自动追认为同一证据。

## 独立错误组

| ID | 原始表现和归因 | 主树处理与资格 |
| --- | --- | --- |
| R2-01 | `xalw_content_01.txt:1096` 将 `{ value=… subtract=1 }` 直接作为 trigger 比较右侧，产生 `Unknown trigger: value/subtract` 和 `Link: value` 解析错误。 | 此前 `17aca6aa2` 已改为 `save_scope_value_as` 计算，再比较数值 saved scope。源修复完成；新加载 `NOT_RUN`。 |
| R2-02 | 1 条 decision 缺 `ai_check_interval`，3 条声明 `ai_targets` 的 interaction 缺 `ai_frequency`。 | core owner 已补真实原生调度字段；内容层未改这部分。新加载 `NOT_RUN`。 |
| R2-03 | 空 `xalw_curse_1/2` 各读取失败 **98 次**，相同失败派生 **196 条 unset-scope** 和 **196 条 invalid-left**；合计 588 个 script-error 报告。大量行数来自每条诊断附带调用栈。 | 这是空槽读取这一根因的多层诊断，不能算成 588 个独立 bug。前轮同级 presence 补丁不构成惰性边界；后续真正分支保护及其新 SHA、结构回归见末节。新加载 `NOT_RUN`。 |
| R2-04 | hidden event 的 `immediate` 中，`debug_log` 动态本地化缺少完整 eventdata 上下文；因而保存名 `xalw_fixture_item` 有 19 次 failed-type，`xalw_fixture_owner` 有 3 次，并级联 promote/convert/loc 诊断。[既有语法记录](../../docs/grammar/pitfalls.md:200)已有实证。这不能归因于少 `scope:` 前缀；该记录第 205 行也说明脚本 `scope:` 不能直接搬入 loc 数据表达式。 | 生产 visible localization **未改**。需要改的是 hidden logger 的观测方式，不能通过给 loc 批量加前缀假修复。旧进程的破损 observer 不能证明完整 XP 后验。 |
| R2-05 | `loan_bad_debt`、`last_wine_host` 各两条 set-but-unused；fixture 变量/targets、`historical_artifact` 另有源诊断。 | 保留真实诊断，不补假 getter 或无意义读取来消日志。保存账本不等于已证明有生产消费者。此组不能替代 R2-03 的功能修复，也不冒充 runtime clean。 |
| R2-06 | v1 adapter 的原罗贝尔身份判定返回 `BLOCKED`，与后来原生观察到的真实玩家 `31254` 不符。 | 保留 v1 失败；后续真实动作和独立回读可各自取得局部结论，不将 v1 BLOCKED 当作“实际无法装备”，也不由局部装备成功外推完整验收。 |

本场实际捕获的空槽错误只涉及诅咒，不能声称已经观察到空异能/rank 的同类错误。检查生产源码发现它们具有相同的直接取值方式，因而一并补守卫，避免下次走到这些分支才再次报错。

## 本次内容修复

修改[内容生成器](../tools/living_artifacts_content.py)，修复后 SHA-256 为 `ef86e4e8452366ecd82ab9fc82da09ca8380078f41779abdffa1bc5104bc99fa`。

1. 增加共享 `_slot_presence(kind, slot)`，在每次槽 ID/rank 比较及随后的取值前，确认 **ID 和 rank 均存在**。覆盖持续投影、最高阶 selector、同件联动、出走、锈蚀、秘密传承、嫉妒目标选择和下一次突变权重。没有给空槽写 `0` 或制造占位词条，缺 rank 的不完整槽也不会被当成有效能力。
2. 首次嫉妒月与尚无嫉妒记录的真实突变，先检查 streak/last_month 是否存在，再读取数值。仍保留“三个真实装备月后下一次实际突变”的原合同。
3. 建设抵扣在尚未初始化借款月结的角色上，先检查 periods/arrears 是否存在，再判断有没有真实债务；不存在债务时走正常建设收益。
4. 锈蚀的上次耐久快照是数值，改用 `has_variable` 表达数值存在，而不是对象作用域的 `exists`。未观察到真实快照时不推断修理。

前轮离线补丁采用同级 `has_variable` 与比较，原版虽有同形写法，但[既有陷阱第 211 行](../../docs/grammar/pitfalls.md:211)已证明同级条件不保证按书写顺序短路。因而上述补丁与只检查文字先后的结构测试**尚未建立真正惰性边界**；需要 `trigger_if` 的 presence limit 包住全部依赖读取，或等价两层 effect `if`。保留前轮源码 SHA 及测试历史，不追认其已解决 fresh-load 问题；后续修复及新加载另行追加。

## R2 后续真实结果与现场限制

本节仍对应同一机器 `pc-20260924rtuf-f11af23c08`、PID `10924` 和 R0002。原 `native-report.json` 在持续追加；配套 JSON 将另加本次读取的 SHA，保留前次捕获值。

- `2026-10-21T21:45:57.872165+00:00` 的 `root-r2-target402-equip-a01` 提交真实装备动作；`21:47:22.840240+00:00` 的 `root-r2-target402-independent-equipped-read-a01` 独立读回原件 `402` 的 `equipped=true`。**装备 402 的局部业务后验通过**，不等同于 v1 adapter 整 cell 通过。
- `root-r2-core-natural-day-001` 于 `21:48:26.995093+00:00` 开始，真实原生日期 `53144328→53144352`；day-002 于 `21:52:14.436207+00:00` 开始，日期 `53144352→53144376`，两步均记录 `ok=true`。这只证明两个自然日实际推进。
- day-003 于 `2026-10-21T21:52:23.507208+00:00` 开始，失败为 `campaign pause readback lost the complete same-owner frame`。不能把该次推进认定为完成，更不能算作月结、自然经验或成长 PASS。
- [外置桌面探测](D:/workspace/ck3-living-artifacts-20261022/environment/r2-input-desktop-a01.json)准确观察时间为 **`2026-10-21T22:03:33.493465+00:00`**：`OpenInputDesktop` 失败，`open_error=5`，`foreground_hwnd=0`；记录仍枚举到 PID10924 的可见 CK3 窗口。该证据说明当前输入桌面不可访问，不能由窗口存在推断可正常操作或已退出。
- 资源闭场仍等待本场原 deadline；此时没有正常退出完成证据，也没有发布完成事实。本节不触发游戏、Steam、鼠标或焦点操作。

## 离线结果与后续读回

- 新增[内容生成回归](../tools/test_content_generation.py)，3/3 通过。测试扫描**实际生成的 AST**：每个 slot/rank 左值比较前有双 presence guard；内容层不会初始化空槽；嫉妒首次状态有守卫；trigger RHS 不再出现内联算术块。这是结构测试，不是 CK3 解释器。
- 新测试及其他 owner 当时已落文件加入后，实际全模块 strict mypy **18 文件通过**；目录的 9 项合同测试也全部通过。后续源变化仍需按统一门禁复验。
- [63 项目录](content-acceptance-cells.json)已根据当前主树重新计算 SourceRef SHA 和 anchor，实际生产者→JSON→严格 parser 往返与来源校验通过。63 项仍全部 `NOT_RUN`，没有因此取得 live 信用。
- 新加载应保留新 PID/出生时间/generation、实际 staging 清单和日志原件，重新观察空槽 bootstrap、首月结算、一次实际成长/突变，以及非空诅咒持续项。每项继续按[验收方案](test-plan.md)和目录的真实业务动作及独立后验验收。
- 旧进程中只读 getter 的修补、调用 ACK、callback log 或“error.log 没增加”的局部观察，都不能替代修复版重新加载，更不能替代佩戴、停级、扣费、销毁材料和跨级经验的业务后验。

## 2026-10-21 22:14 UTC 追加：惰性修复及失败资源闭场

仍为 `machine_id: pc-20260924rtuf-f11af23c08`。真正修复版生成器 SHA 为 `126cedc1c65db6b8d93db139aca994c17948623c5e92c83c26080875dec5f64d`；前述 `ef86e4e…` 是需要继续修复的历史补丁，不能作为当前来源。槽 ID/rank 以及可选记忆、债务、日期、旧主人和耐久字段的依赖读取，现已放入 `trigger_if` 的 presence limit 之后，并以同父 `trigger_else = { always = no }` 处理缺失。空槽继续保持缺失。6 项 AST 回归检查实际父子关系并拒绝旧同级写法；当时全工具 59 项测试、22 文件 strict mypy、49 文件生成及离线静态检查通过。63 个验收 cell 仍全部 `NOT_RUN`；此修复未在 R2 已加载脚本中生效。

R2 原定期限没有延长。原公共 run 实际退出 2，原 host 的真实 Popen wait 在 `22:09:21.322046Z` 返回 1。终态 native report 为 9,994,068 字节，SHA `6f5232609b5b6deee0177ab3811ceb939e0a526af674736bffb65017e4f25998`，`finished_at=22:09:20.819822Z`，managed thread 已结束、cleanup 为 true；原 job/tree/control/inventory 完整闭场守卫也通过。实际进程清点为空。这些事实证明失败资源清理，不证明正常 GUI 退出：原 retained HANDLE 记录仍是 `signaled=false`，`normal_close_qualified=false`，没有补造成功 review。

Root 在 `22:10:10Z` 写入唯一 cooperative STOP，等待原 allocator 实际退出 0；keeper 的 parent 回执为退出 0、thread_exited=true、failure=null、最后序号 319。CAS release 为序号 320，管理完成事件为 321，独立 task-bus list 确认无 screen owner。`r2-screen-resource-close-a01` 因 CLI 要求大写 SHA 而拒绝，未改变资源；纠正格式后的真实成功回执在外置 `environment/r2-screen-resource-close-a02/`，拒绝原件保留。共享 `previous_session_closure` 对原终态报告返回 `previous-shared-managed-session`，下一场仍须重新准入。

[实际库存原图](evidence/r2-inventory.png)及[来源](evidence/r2-inventory.provenance.json)已经保全到仓库。这是英语测试夹具界面，拍摄时尚未装备，能展示目标和四种原生稀有度材料；不能算作自然生成、成长、中文版界面或正式 Workshop 图片上传。月结、完整业务验收与发布依然未完成。

## 2026-10-21 22:40 UTC 追加：最终离线检查

同一机器的统一 wrapper 在 `22:36:47–22:36:57Z` 实际执行工具目录 88 项测试、26 文件 strict mypy 及生产静态检查，全部退出 0，检查期间完整产品来源 SHA 未变；原始 argv、Popen/wait、stdout/stderr 和完成回执在外置 `environment/final-product-validation-a01/`。之后把库存拒绝匹配进一步收紧为 R2 实际完整错误，加入“其他错误仅提到相同文字”负例，15 项相关回归及 26 文件 strict 再次通过。

核心生成器进一步修复了同形可选日期、旧债务、饥渴减免、空槽升级及 UI 首次安抚资格的惰性读取，保留“缺少安抚冷却时允许首次使用”的语义。`xalw.1` 续链与初始化、发现入口共用 `xalw_owner_needs_monthly_trigger`，所以失去最后物品仍继续旧债月结；无物无债才停止。此版 core 源 SHA 为 `9e8ddae7884902e8ceb19743fc704dbdfed8cea4b51f79fc17074a9b22f1e6f3`。含“真正无物品后至少两个月仍催款”的验收仍为 `NOT_RUN`。

公共日期读回只在原 deadline 内只读等待两路 publication 收敛，原完整帧守卫通过后才提交一次 pause。最终 66 项相关回归通过；实际同配置 checker 按 AST 定位两个已改 host 函数，基线 20 条类型错误降为 0。历史研究 host 其他范围仍有诊断，未宣称全 host strict 通过。完整来源、诊断和实际进程回执见外置 `environment/running-date-shared-final-source-a01.json`，R2 第三天失败不追认为通过。

`22:16:59.929455Z` 的后台 Steam 查询仍为 offline，未抢焦点或截图；`22:21:11.357305Z` 的下一场桌面准入探测仍返回 `OpenInputDesktop` error 5、foreground 0。下一场尚未启动。闭场存储检查于 `22:17:00Z` 完成，当前两组仍服务于进行中的任务，未删除资产；沿用统一策略及原机器预算，不建立永久保留。
