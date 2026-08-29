# ZhongGuo 361 Style 实机测试报告（2026-08-30）

## 1. 宋帝首轮分布缺陷

用户在宋帝京察中观察到 `7 × 3.75 + 16 × 3.5 + 0 × 3.25`。23 人严格 361 的权威结果应为 `7 / 14 / 2`，原画面不是合法舍入。

缺陷由两层问题叠加：

1. 首次安装时，旧实现把所有没有模组快照的在任官员都当作新人，导致 23 名存量官员全部享受 3.25 保护；
2. 修正存量/新人语义后，末位 `ordered_in_list` 仍省略了 `max`。CK3 1.19.0.6 的 `ordered_*` 在省略 `max` 时只处理第一项，所以名额变量虽然是 2，实际只发出一个 3.25，表现为 `7 / 15 / 1`。

提交 `9b3b7fb` 的局部修复先建立仅含非新人的 `zg361_bottom_candidates`，再以 `max = list_size:zg361_bottom_candidates` 完整排序遍历。这样既不会少取，也不会把未过滤 cohort 长度作为 `max` 而触发范围错误。静态回归禁止删除该动态上限。

实机 attempt `Z:\ck3_mod_rewrite_process_assets\zg361\promo\captures\zga_20260830_0302_current_9b3b7fb_mcp2` 已在 CK3 1.19.0.6、1066 史实赵曙、23 名直属官员中取得离散日志：

- `bootstrap_cohort_n = 23`；
- `bootstrap_pending_375_n = 7`；
- `bootstrap_pending_35_n = 14`；
- `bootstrap_pending_325_n = 2`；
- `bootstrap_bottom_slots = 2`；
- `bootstrap_actual_bottom_rows = 2`；
- 结算前 `bootstrap_first_review_strict_7_14_2` PASS；
- 结算后 `bootstrap_first_review_result_7_14_2` PASS。

同局的 361/361 机制账本和幂等性也已通过。该 attempt 的整局结果仍为 **RED**，不能作为完整发布签核：首轮 `stream.validate()` 错误地提前要求只会在后半段第二轮出现的真实新人产品 marker；同时校准选项 tooltip 在枚举未入考核池的直属封臣时暴露了 unset-variable 诊断。

## 2. 由该 RED 触发的最小后续修复

- 验收器把 `ZG361: newcomer enters first review with 3.25 protection` 从首轮产品 marker 集移到 `final=True` 的后半段产品 marker 集；最终门槛不删除、不降级。
- `zg361_can_calibrate_demote_trigger` 对 `zg361_pending_grade` 的读取改放到 `trigger_if + has_variable` 门内。
- `zg361_is_current_liege_review_record_trigger` 把 reviewer、serial 和上司 serial 的存在性检查放在同一个 `trigger_if.limit` 中，只有全部存在才比较变量；`trigger_else = { always = no }` 保持缺记录者不合格。

原因是 CK3 trigger 的同层 AND 条件不保证短路；把 `has_variable` 和 `var:` 比较平铺书写，仍会在 tooltip 预求值时读取不存在的变量。

第二次完整 attempt `Z:\ck3_mod_rewrite_process_assets\zg361\promo\captures\zga_20260830_0314_current_0f3e200_mcp` 再次取得 23 人 `7 / 14 / 2`，且项目诊断数为 0，证明上述 tooltip 修复已在实机生效。同局还通过考核榜安全区按钮、原生右侧窗口抑制与关闭、管理/本人页切换、政策驾驶舱、标题栏与背景关闭、真实榜单行跳转、京察强制弹窗、免费规划器和主持选项后的原生即时暂停。该 attempt 仍为 **RED**：后半段个人结果载体尚未到期，runner 先触发了墙钟超时。

## 3. 京察后 D+90 等待的验收器 RED

该 RED 不在产品考核链。夹具在真实 `zg361.40` 京察弹窗出现的同一日固定调度 `zga_acceptance.3 days = 90`；只有该隐藏载体到期后，才会打印 `personal_result_switch_scheduled` 并进入真实“上司考定”产品链。最新日志没有该载体的 PASS 或 FAIL，说明它尚未执行，而不是执行后条件失败。

即时暂停 sidecar 记录起点 ordinal `389359`、到期 ordinal `389449`。失败时保留的 `fatal_state.png` 显示日期 ordinal `389403`（1066-11-10）且无事件 modal、游戏处于暂停：只推进了 44/90 个游戏日，距到期仍有 46 日。旧 runner 只在进入等待时启动一次五速，此后仅在“识别并关闭了事件弹窗”时恢复时间；CK3 因无 modal 的通知设置静默暂停后，它无法自愈，90 秒墙钟最终耗尽。

最小修复保持产品和 D+90 夹具合同不变：等待器现在复用同一局已经连接的原生 MCP，读取 `paused`、`speed` 与 `date_raw`；发现无 active event 的静默暂停时，提交 `set-speed-5` 与 `resume-map`，并要求原生日期真实增长后才继续。恢复前会再次 pump 目标 marker，避免穿过刚到达的“上司考定”。墙钟上限放宽为 240 秒，只作为失控兜底；每局写出 `10_personal_switch_timeline_gate.json`，记录到期日、原生观测和每次恢复原因。

第三次完整 attempt `Z:\ck3_mod_rewrite_process_assets\zg361\promo\captures\zga_20260830_034605_current_c4921dc_mcp` 第三次实机证实 23 人严格分布为 `7 / 14 / 2`。同局的 D+90 等待器成功发现并恢复无 modal 的静默暂停，真实跨过到期日，该 MCP 恢复链现为 **live-confirmed**；随后真实“上司考定”弹窗明确显示本人绩效 `3.25`。

该 attempt 仍为 **RED**：点击“认命”后，夹具 policy 001 在次日抢先弹出，占用了原定的本人榜截取步骤。证据表明这是 runner 在关闭个人结果后等待 HUD/暂停太慢与夹具次日调度相撞的 choreography 问题，不是 361 分布或“上司考定”产品缺陷。

第三次 RED 后的针对性修复将个人结果和六张政策卡的关闭切换到原生 MCP 控速/暂停，不改产品逻辑或夹具日期。

第四次完整 attempt `Z:\ck3_mod_rewrite_process_assets\zg361\promo\captures\zga_20260830_0415_current_e043596_mcp` 第四次实机证实 23 人严格分布为 `7 / 14 / 2`，并已通过 361/361 机制账本、史实角色来源、AI 非独立天朝公爵考核、考核榜 GUI 阻塞与原生页面、京察、D+90、拒办处罚、新人保护，以及“上司考定”明示本人 `3.25`。

该 attempt 的 **RED** 仅发生在点击“认命”之前：runner 错误要求同一 modal snapshot 必须同时满足 `speed = 1` 与 `paused = true`。`set-speed-1` 命令 ACK 已为 submitted，`dedicated_server.log` 也记录 `Changing game speed to:0`；但失败等待 loop 的 observations 没有在 RED 前落盘，因而“当时原生帧持续是 `paused = false`”只能作为由终止分支得出的强推断，不能写成已有逐帧 artifact 直接证明。现有证据指向 runner 门禁过严，没有新的产品 RED。

当前最小修复为 **static-ready**：点击前只强制验证 ACK 已提交，且 event identity、`date_raw` 和角色未变，`speed`/`paused` 仅记录不作阻塞；点击后要求 event instance 已变化且仍在同一 `date_raw`，仅在需要时条件提交 `pause-map`，随后要求连续三帧冻结。每一阶段均先写 sidecar 再进入下一步，避免下次 RED 再丢失失败 loop observations。

## 4. 第五次完整 attempt：产品链已到政策卡，标题 OCR 假 RED

第五次完整 attempt `Z:\ck3_mod_rewrite_process_assets\zg361\promo\captures\zga_20260830_0445_current_859d811_mcp` 第五次实机证实宋帝 23 人严格分布为 `7 / 14 / 2`。同局还通过：361/361 机制账本及幂等性、史实角色来源、AI 非独立天朝公爵考核、考核榜安全区与右窗阻塞、管理/本人页、制度驾驶舱、标题 X 与背景关闭、史实榜单行跳转、京察强制弹窗与免费活动规划、D+90 静默暂停恢复、拒办处罚、新人保护，以及“上司考定”明示本人 `3.25`。点击“认命”后的同日冻结、本人的 3.25 榜单和本人页重复点击也首次实机通过，上一轮的 modal pause blocker 已闭合。

该 attempt 的唯一 runner 终止点在第一张政策卡。卡片已经于 1066-12-28 正常置顶并稳定停留至少 21 秒；`clean_policy_001_dispatched` 恰好一次，`clean_policy_007_dispatched` 仍为零。前置门用规范化标题匹配已经认出“KPI 分项证据单”并保存 `12_policy_001_preemption_target_event_visible.png`，紧接着的重复门却用原始字符串包含匹配等待 `KPI 分项证据单`；RapidOCR 稳定返回不含空格的 `KPI分项证据单`，因此把肉眼可见的产品卡误判为 RED。该次未进入政策卡关闭前的 MCP speed-one gate，所以没有政策卡 active-event instance 的持久化原生 sidecar，不能为它补写推测 ID。

同一实机画面和日志还给出两项必须在下次启动前合批修复的直接证据：

- 测试夹具直接向新切换的史实领主触发 `zg361m.1`，没有复刻产品 dispatcher 的组织账初始化；同时产品 `zg361_refresh_org_climate_effect` 的六个阈值仍裸读变量。事件 option tooltip 会独立预演同级 effect，不提交前一个 choice effect 内的初始化，结果六个 `zg361_org_*` 变量各报错 4,240 次，共 25,440 条。修复既在首张 clean carrier 前初始化，也在产品生成器中以 `trigger_if + has_variable` 保护六个阈值；后者保证任何合法 fresh 入口都不会依赖夹具兜底。
- 政策标题以 ASCII `#001` 开头，被 CK3 当成本地化格式标记吞掉；中文描述中的 `\n` 又被生成器二次转义为 `\\n`，画面遂显示字面量。生成投影现将中文编号写为“第001号”、其余语言写为 `No.001`，并只保留 CK3 所需的单反斜杠换行 token。

runner 现直接复用已经通过规范化匹配的政策卡截图，不再追加较弱的原始空格 OCR；三个问题均已有定向回归并通过，状态为 **static-ready**。下一步只运行一次新的完整合批实机，不再重复前四轮已闭合的代码审计。

## 5. 第六次完整 attempt：原版单选信件截断 D+90

第六次完整 attempt `Z:\ck3_mod_rewrite_process_assets\zg361\promo\captures\zga_20260830_0520_current_49777d5_mcp` 第六次实机证实宋帝 23 人严格分布为 `7 / 14 / 2`，并再次通过此前的产品、361/361 账本、史实角色、AI 公爵考核、考核榜 GUI、京察与新人保护门。该局 `project_diagnostics = []`，证明上一轮六个组织账 unset-variable tooltip 错误已经归零。

该 attempt 的 **RED** 仍是 runner 阻塞，不是产品或 D+90 夹具失败。`10_personal_switch_timeline_gate.json` 记录京察后起点 `date_raw = 53144616`、到期 ordinal `389449`；原生 `set-speed-5` 与 `resume-map` 均提交成功，但日期只推进到 `53144688`，即 1066-09-30、共 3 天，便停在 `active_event_instance_id = 5`。`fatal_state.png` 明确显示原版单选信件 `court_events.1011`《我曾经的主人，》与唯一选项“叛徒！”，而 marker 始终为 0；因此载体还差 87 天，根本尚未执行，没有任何 `ZGA: TEST FAIL` 可归因于产品。

根因是 runner 丢弃了 MCP 已经发布的 `active_event.option_count`，只保留 instance ID，然后仍依赖 classic character-event OCR 标题区域。该信件标题中心约为 `x = 0.4824, y = 0.3486`，落在旧标题区域之外；同一截图离线重放得到 `promo_event_modal_evidence = false`，但安全选项分类其实已经得到 `center_event_option`。MCP 又正确拒绝在 active event 非空时盲目恢复时间，于是形成 240 秒死锁。

针对性修复现为 **static-ready**：personal-switch sidecar 保留 `option_count`；只有 MCP 证明事件恰好一个选项、视觉分类又排除继承屏并找到强选项几何时，才在同一 event instance、同一日期和 fresh revision 上依次提交 `pause-map` 与 typed `select_event_option(1)`，并要求旧 instance 变化、日期不变且仍暂停。多选事件不走原生盲选；目标 marker 在操作前后继续 pump，“上司考定”标题也继续受保护。定向回归已覆盖本次 centered letter 布局、`paused = false → pause → native option 1 → instance change`，下一步只做一次完整合批实机。

## 6. 第七次完整 attempt：史实赵曙自然死亡

第七次完整 attempt `Z:\ck3_mod_rewrite_process_assets\zg361\promo\captures\zga_20260830_0556_current_f8955f3_mcp` 第七次实机证实宋帝 23 人首轮分布在结算前后均为 `7 / 14 / 2`：日志为 `bootstrap_pending_375_n = 7`、`bootstrap_pending_35_n = 14`、`bootstrap_pending_325_n = 2`、`bootstrap_actual_bottom_rows = 2`，且 `bootstrap_first_review_strict_7_14_2` 与 `bootstrap_first_review_result_7_14_2` 均 PASS。361/361 机制账本、幂等性、史实 cohort、AI 非独立天朝公爵考核、考核榜 GUI、京察及免费规划器也再次通过。

该 attempt 在 D+90 中止于真实继承屏，而不是 361 产品 RED。保留截图 `cell/10_personal_switch_wait_04_interruption_blocked_succession.png` 和 OCR sidecar 证明：赵曙于 1066-11-16、34 岁时死于心脏衰竭，界面要求继续扮演继承人赵项；runner 按宣传片“连续使用真实指定角色”的合同拒绝自动改演继承人。原版精确构建历史把 `han_8052` 设为 `health = 2`，同时赋予 `depressed_1`、`physique_bad_2`、`possessed_genetic` 三个各 `health = -0.5` 的特质，起局有效健康约为 `0.5`；原版 `DIE_HEALTH_TRESHOLD = 3.0`，因此在约百日的片场时间线上死亡不是可忽略的小概率噪声。

针对性修复只进入外部隔离夹具，状态为 **static-ready**：初始化真实赵曙时添加 `health = 10`、持续 120 天的本地化“御医监护（隔离验收）”角色修正；在切换至史实受考官员之前的同一 effect 帧显式移除，并分别要求 `recording_health_guard_applied` 与 `recording_health_guard_removed_before_switch` PASS。120 天到期提供异常路径兜底；正式产品树和 release staging 均不包含该文件，史实角色、姓名、头衔与 cohort 不变，也没有使用永生特质或继承人续演来伪造宣传素材。定向夹具合同、runner 合同、Python 编译和启动 wiring 回归均已 GREEN；下一步只跑一次完整合批实机。

## 7. 第八次完整 attempt：健康夹具闭合，政策事件同窗换定义误判

第八次完整 attempt `Z:\ck3_mod_rewrite_process_assets\zg361\promo\captures\zga_20260830_0625_current_586650c_mcp` 第八次实机取得宋帝 23 人 `7 / 14 / 2`，结算前后两道严格 marker 均 PASS，项目诊断仍为 0。新健康夹具首次实机闭合：初始化时 `recording_health_guard_applied` PASS，D+90 到期并成功触发 `personal_result_switch_scheduled`，切换史实受考公爵前 `recording_health_guard_removed_before_switch` PASS；随后真实“上司考定”明确显示本人 `3.25`、KPI 与位次，本人所属考核榜也实机打开。说明第七局的赵曙自然死亡 blocker 已解除，且保护没有跟随玩家进入受考角色。

该 attempt 继续通过考核榜按钮及阻塞矩阵、京察强制弹窗、免费活动规划器、拒办处罚和新人保护，并首次把修正后的政策卡第001号《KPI 分项证据单》完整显示、录制并提交其真实选项。整局仍为 **harness RED**：提交 #001 后，产品立即把同一事件窗口替换为 `zg361.6`《你被列入末位淘汰名单》。`12_policy_001_close_immediate_pause_gate.json` 证明点击前后日期始终为 `53146848`；containment `pause-map` ACK 后最后三帧均为 `paused = true`、同日、角色稳定，时钟事实上已安全冻结。但 CK3 对前后两个不同定义都发布 `active_event_instance_id = 7`、`option_count = 4`，旧门仅以 instance ID 改变判定转场，因而制造 false negative。`fatal_state.png` 肉眼及 OCR 均证明顶层定义已经换成末位淘汰事件；这份视觉证据只用于诊断，不作为新放行条件。

针对性修复现为 **static-ready**：保留原 instance-ID 快路径；同 ID 时只在同日冻结后调用现成 `current_event_window_context_v1` MCP，并要求 canonical `event_definition_key` 从调用方声明的前序键（政策卡为 `zg361m.N`，个人告身为 `zg361.4`）发生变化。query unavailable、定义未变、日期漂移或角色变化仍 RED；通用 revision、option_count、OCR 和“已经暂停”都不能代替身份。下一张政策卡前的有界 interruption 处理会对真实 `zg361.6` 明确选择“掀桌起兵”：它保留史实角色和头衔，但会真实建立独立派系；随机申诉、夺爵与致仕不用于连续片场。定向回归已覆盖同 ID 的 `zg361m.1 → zg361.6` GREEN、同 ID 同定义 RED、原 ID 变化路径和日期漂移 RED；下一步仍只跑一局完整合批实机。

## 8. 第九次完整 attempt：#020 已切到 #022，共用选项文字制造假 RED

第九次完整 attempt `Z:\ck3_mod_rewrite_process_assets\zg361\promo\captures\zga_20260830_0651_current_cdda2f5_mcp` 第九次实机取得宋帝 23 人严格 `7 / 14 / 2`：`bootstrap_pending_375_n = 7`、`bootstrap_pending_35_n = 14`、`bootstrap_pending_325_n = 2`、`bootstrap_bottom_slots = 2`、`bootstrap_actual_bottom_rows = 2`，结算前后两道严格 marker 均 PASS。361/361 机制账本与幂等性、AI 非独立天朝公爵考核、考核榜按钮和完整 GUI 阻塞矩阵、制度驾驶舱、京察强制弹窗与免费规划器、D+90、拒办处罚、新人保护、史实上司告身中的本人 `3.25` 以及本人所属考核榜也都再次通过；`project_diagnostics = []`。政策卡 #001、#007 已完成可见捕获和真实选项提交，#020 也已真实显示。

本局最终仍为 **harness RED**，但产品转场已经成功。`12_policy_020_preemption_interruption_01.png` 显示 1066-12-31 的第020号《晋升包与跨部门答辩》；RapidOCR 把标题中的“晋”误读为“普”，旧的 OCR stop gate 因而没有认出预期目标，并误把 #020 当成普通中断点击 C“这季度先不碰，登记制度债”。`final_debug.log` 随即记录 `ZG361M: CASE 020 CHOICE C APPLIED` 与唯一一次 `clean_policy_022_dispatched`；`timeout_12_policy_020_preemption_interruption_01.png` 和 `fatal_state.png` 已在 1067-01-01 明确显示第022号《软 HC / 编制预算》。所以 #020 并未卡住，产品也没有漏派发 #022。

旧关闭门只比较被点选项的 OCR 文本和屏幕坐标。全部政策卡的 C 选项本来就共用“这季度先不碰，登记制度债”，#020 与 #022 又使用同一按钮位置，因此后继卡仍命中该启发式，8 秒后被误报为“选项未消失”。这段失败 artifact 没有保存点击前后的 event-window MCP snapshot；decision sidecar 中的 `native_active_event_instance_id = null` 只表示该调用没有接入 native service，不能据此声称原生桥当时观测到了空事件，也不能事后推断 instance 是否复用。

针对性修复现为 **static-ready**：政策 preemption 调用会把预期 canonical key `zg361m.N` 与原生 service 一并传入；runner 用当前 snapshot 的 active instance 和 public revision 调用 `current_event_window_context_v1`。只有顶层可见 modal 的 canonical key 等于目标 key 才保存目标帧并停止清理，MCP unavailable、identity readiness 不足或视觉标题与 canonical 身份冲突均 fail-closed。真正需要清理的中断会先原生降至一速，再以同日 instance/definition 转场和连续冻结为权威后置门；重复选项文字只保留为诊断，不再决定成功。定向回归覆盖本局真实 OCR“第020号普升包与跨部门答辩”、目标零点击、MCP unavailable RED、同 ID `zg361m.20 → zg361m.22`、同文同位后继和 revision 绑定；Python 编译、宣传 runner 合同测试、`git diff --check` 与 exact-build promo preflight 均 GREEN。下一步只运行一次新的完整合批实机，不重复审计此前已闭合链路。

## 9. 第十次完整 attempt：政策身份查询早于原生暂停

第十次完整 attempt `Z:\ck3_mod_rewrite_process_assets\zg361\promo\captures\zga_20260830_0723_current_385e557_mcp` 第十次实机取得宋帝 23 人严格 `7 / 14 / 2`，结算前后的离散人数、末位名额和实际末位行全部一致。该局再次通过 361/361 机制账本与幂等性、AI 非独立天朝公爵考核、考核榜按钮和 GUI 阻塞矩阵、制度驾驶舱、京察强制弹窗与免费规划器、D+90、拒办处罚、新人保护、史实上司告身中的本人 `3.25` 及本人所属考核榜；`project_diagnostics = []`。因此产品当前没有新增 RED。

本局在政策卡 #001 已经肉眼可见时结束为 **harness RED**。`cell/12_policy_001_preemption_event_definition_identity_unavailable_gate.json` 记录 `BridgeUnavailableError: event-window queries require a paused CK3 snapshot`。根因是 classic event modal 会阻止地图时间继续走，但公开 native snapshot 的普通 `paused` 字段仍可为 `false`；旧 runner 在取得真正 `paused=true` 的 snapshot 前便调用 paused-only 的 `current_event_window_context_v1`。桥按合同拒绝查询是正确行为，不是事件身份能力缺失，也不是政策卡产品失败。

针对性修复现为 **static-ready**：可见事件需要 canonical 身份时，runner 先绑定 active event instance、`date_raw`、played character 和起始 public revision；若尚未普通暂停，以该 revision 提交原生 `pause-map`，逐帧要求事件、日期和角色不变，取得 `paused=true` 的新 public revision 后才查询 `event_definition_key`。目标卡仍然零点击；暂停 ACK 拒绝、等待超时、上下文漂移或 identity unavailable 均 fail-closed，并先写 `*_prequery_pause_gate.json`。定向回归覆盖运行中 modal 的 `revision 40 → pause-map → paused revision 41 → identity query`、already-paused 快路径、暂停时日期漂移、MCP unavailable、真实 #020 OCR 漂移及同文同位后继；Python 编译、宣传 runner 合同测试、`git diff --check` 和精确构建 preflight 均 GREEN。下一步直接运行第十一次完整合批实机，不再重审此前已闭合链路。

## 10. 环境与证据边界

- 精确游戏版本：CK3 `1.19.0.6`；EXE SHA-256 `2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86`。
- CK3 前台输入线程已回读并保持 US English HKL `0x04090409`，未恢复中文。
- attempt 的 artifact、隔离 userdir、日志、截图、未完成录屏和 native state 全部保留；保护存储未变化，CK3 进程树已受控回收。
- `7 / 14 / 2` 已九次实机复现；项目诊断在第六至九次 attempt 均维持归零。史实角色、AI 非独立天朝公爵考核、考核榜 GUI 阻塞与原生页面、京察/D+90、拒办处罚、新人保护、“上司考定”本人 `3.25`、本人榜及政策卡 #001/#007/#020 均已 live-confirmed；政策 preemption 的 canonical-key 目标门、其余政策卡与正式宣传素材仍等待下一次完整 GREEN。
