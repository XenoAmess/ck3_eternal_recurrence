# R0178：remaining=0 仍不代表实际到达

machine_id: `desktop-3fevhd2-1c74096080`。运行来源 b42afbbd85df3802b1fa6222f7aac403c2adf735/native a08，PID24740/create134365733009843924、episode native-31254-0665741d68fc；读原件时间与精确引用见 [day29/30记录](evidence/episode04-r178-arrival-boundary-12004/CASE.DAY29-30.actual-a01.json)。未读取 EXE、完整 Driver、9MB raw 或接触 SDK/桌面。

day29 独立 full 小读回为 weight2900000、cost3000000、provider0、remaining100000；每日 minimal summary 本身未观察这些 operands，两份来源分列。day30 精确+24/tick1/overshoot0 后，weight3000000=cost3000000、provider0、normalized100000、remaining0；实际 Army93/native85 仍在2624，moving、route[1036]，qualified列表为空，zero_fee_proved=false。ETA到达日53147568是投影，不是省份转移证明。

已持 [actual4 first-edge source](unit-first-edge-arrival-selection-12004.md) 明确：24AB7DD 对 signed post-ADD168 与独立cost作比较，24AB7E4 是严格JG。大于才直接选择 arrival；小于或等于还要 provider byteE 非0。等于且byteE=0走 hold/epilogue。现生产 pure projection 也保留 `progress > cost` 分支。因此 day30 数值与已闭合的 hold 条件一致；这不是采到了实际 callback PC，也不重建完整到达 helper 的所有副作用。

Sentinel 源码先 `original()` 返回，再调用 `ProcessTacticalDailySentinelAfterTickV1()`；后者记tick并在日期deadline触发暂停。该实现没有“先暂停再调用original”的正常路径。日期哨兵本次army_count=0，exact+24不证明每个Unit callback都执行或实际到达；不能只因remaining0就将未到达归因暂停太早。当前观测也确实已有2900000→3000000的进度变化。

Agent与拍摄共用规则：用独立新鲜省份、完整route/state后读判断到达；remaining0、ETA日期或100%进度只作当前预测。若同receiver/route/cost/provider、下一次被调度且准入的ADD仍为100000，则条件weight3100000>3000000会选择arrival分支；这只是held-input预测，不能承诺到达日或登船付款。需要解释异常时，窄读同帧 `current_unit_new_date_schedule_inputs_v1`、`current_unit_new_date_callback_entry_inputs_v1`、`native_army_resolution_v1.raw_reference` 与 `monthly_loss_budget_inputs_v1.unit_native_170_raw`，保留调度/receiver/route变化；不自动加query或重发Move。

随后独立 [day31/32 endpoint补注](evidence/episode04-r178-arrival-boundary-12004/ENDPOINT.DAY31-32.actual-a01.json) 记录：day31/raw53147592 已在1036、embarked、空route；day32仍同省空route，full250/250。实际转移只被括在(53147568,53147592]，未取得首次encoded PTS。day31 movement operands未观察，不能倒填3100000；其summary报告的qualified callback列表原样保留，本包未读cash原件或重跑formal fee consumer，不据此独立授费额/R07 pair PASS。两日均research_only_no_capture、dynamic_footage_credit=false。

day30原45秒录像没有登船发生镜头信用；不能把名为boarding-film的attempt、预测完成日或后续片外endpoint充当片内事件。day31/32原件另列，不覆盖day29/30边界事实。R07完整两arm、连续clean及人工签核仍由各自合同结算。保护复核仍为2026-10-16T07:45:01.597Z，不续期。
