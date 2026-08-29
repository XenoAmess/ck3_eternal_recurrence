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

## 4. 环境与证据边界

- 精确游戏版本：CK3 `1.19.0.6`；EXE SHA-256 `2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86`。
- CK3 前台输入线程已回读并保持 US English HKL `0x04090409`，未恢复中文。
- attempt 的 artifact、隔离 userdir、日志、截图、未完成录屏和 native state 全部保留；保护存储未变化，CK3 进程树已受控回收。
- `7 / 14 / 2` 已四次实机复现；项目诊断归零、史实角色、AI 非独立天朝公爵考核、考核榜 GUI 阻塞与原生页面、京察/D+90、拒办处罚、新人保护以及“上司考定”本人 `3.25` 均已 live-confirmed；本人榜、六张政策卡和正式宣传素材仍等待下一次完整 GREEN。
