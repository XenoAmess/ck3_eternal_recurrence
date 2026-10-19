# 新战役月度评分输入与准点终点

2026-10-19 的后继实施入口是纯叶 [`campaign_score_cadence_v1.py`](../../ck3_autonomous_player/src/xar_autoplayer/campaign_score_cadence_v1.py)。它只计算日期、截止计划和现有普通帧的小型投影；不连接游戏、不改策略、不推进日期、不读存档、不写文件。它的存在不证明新局已经部署或真正准点采满360个月。

日历沿用 exact CK3 1.20.0.4 的[原生 CDate 研究](native71-conception-last-child-date-12004.md)：`raw = 43800000 + 24 × (year × 365 + day_index)`；12个月长度为 `31,28,31,30,31,30,31,31,30,31,30,31`，无闰日。来源实现是 `conception_last_child_date_12004.cpp::Decode`、月移位 `8760` 和原版12字节月表；[完整 CDate 专题](army-next-full-cdate-calendar-12004.md)保留构建、EXE SHA、表RVA和证据边界。这里只覆盖正年份、完整原生日界，不使用 Python 的 Gregorian `datetime` 计算游戏月。新局仍须由现场owner核实际EXE/build与该profile相符。

`month_boundaries("1066.9.15")` 返回361项：单列开局基线0，以及第1至360个月。第一项 `1066.9.15/raw53144328`，月1为 `1066.10.15/raw53145048`，月360为 `1096.9.15/raw53407128`；三十年正好10950游戏日。第360月样本也是准点终点，不能另用晚8日的 `1096.9.23/raw53407320` 替代。

最小集成配方如下；外置COW只由runtime owner修改，公共 `service.py`、`strategy.py` 由其各自owner维护。

1. 首次1066普通paused frame建立 `campaign_anchor`，记录固定 `campaign_id`、实际创始角色、实际开局house/dynasty、T0和机器/EXE/新Game来源。尚未观测的house/dynasty保留null，不能凭旧局数值补入。跨ruler、SDK重连、合法继承和普通SAVE均不重置T0、月份或创始分母。
2. 首次普通MET/semantic frame先采基线0，再允许首个advance。每次准备推进时调用 `plan_advance_cap(current_raw, proposed_target_raw, start_date="1066.9.15", next_sample_index=...)`。`advance` 返回原提议与下一未采样月界的较早绝对raw；`sample_due` 要先消费当前既有普通帧，再前移sample cursor；`endpoint_due` 先保存终点样本，再进入既有正常闭场，不再发advance。只有样本文件实际持久化并绑定来源后才前移cursor。
3. **cap必须进入原生截止通道。** `native_driver.py::_execute_life_advance` 的普通 `horizon_days` 是轮询后暂停门限，缩小它或外层用 `elapsed >= 30 years` 停止均不能证明没有过冲。现有 `_advance_exact_day_with_sentinel` 在原生daily callback以绝对 `target_date_raw=start+24` 停止；战斗epoch、committed-route、stationary-objective、route-window各有自己的native sentinel与typed target合同。未来适配必须让每种真实advance的selected step/plan、arm、target、horizon和后验校验保持一致，不能只偷偷改arm字符串或只改最终回执。需要保留普通事件/战争/继承早停及cancel流程，不因评分采样改变战争选择。若适配暂未就绪，保留真实资格缺口，不能声称纯cap已部署或准点完成。
4. `root_p37_mcp_entry.py::root_current_runtime_metrics` 已经为普通MET取得 `driver.take_internal_semantic_snapshot()`。在这同一次快照上调用 `ordinary_sample_candidate(...)`；非月界返回None，月界才附小候选，不增加每日查询、世界扫描或SAVE导出。`root_p37_sdk_queue.py::full_loop` 既有AUTO后paired-MET结算处，用实际MET response path与SHA、AUTO response reference、当前Game/tuple和机器身份包装该候选，按新文件 `month-000.json` 至 `month-360.json` 写出。保留候选的原始frame；不能用较旧snapshot或长期缓存替换。文件不得覆盖；同槽零日动作可保留额外来源reference，但不多记一个月。
5. 基础投影只从同帧 `played_character_gold.raw/100000` 确认现金，其他评分指标带正确unit与显式unknown。玩家战争只保留当前原生列表的小投影；主头衔继承人不冒充合法player-heir，net income不当gross income，domain/direct county不当品质加权realm。若该次普通处理已取得其他同帧合格指标，可在独立adapter里按其完整来源绑定补充；不额外每日反扫大SAVE。E/M/H及任何未闭合指标继续保留区间，不因不完整评分阻塞长局。
6. 若实际日期已经越过未采月界，`missed_sample_indices`明确列缺槽并允许继续到下一个真实月界；不得把当前观测倒填到已错过月份。晚于终点返回 `endpoint_overshot`，不产生准点终点资格。360个确切月界来源样本与360个月完整数值评分是两个不同条件；最终数学只能消费真正已观测、同口径的metric，不以插值、区间中点、90日checkpoint或稀疏MET重建历史。

新增定向测试6项覆盖旧首尾raw锚、CK3无闰日、360月完整时间表、月末夹日不漂移、cap/当前月先采、缺槽与终点过冲、负现金、未知指标、自然继承固定创始anchor。命令为：

```text
set PYTHONPATH=ck3_autonomous_player\src
py -B -m unittest ck3_autonomous_player.tests.unit.test_campaign_score_cadence_v1
```

2026-10-19实际软件验证：`machine_id: xenoamess-full-tower-eb9d2c1186`，由 `tools/ck3_live_run_id.py machine` 读回；同次上述定向命令执行6项通过、退出0。结果与文件身份登记时间 `2026-10-19T01:58:16.899662Z`；纯叶SHA-256为 `ae507020d789853bf7c7c849d590037bf69c2d039ce8b10e62e46946b5c7e929`，测试文件SHA-256为 `790cd18555e6506aeeb42acd372d0fc66e5eaa8b23283a5031e4328d7d238c79`。没有现场RPC、游戏推进、SAVE/Driver正文读取或媒体渲染；不授新Game、整局、月样本或G2信用。具体部署与实际月文件由runtime owner在新tuple的独立回执记录。

2026-10-19 后继已实现实际Python组合，复用[固定Native25绝对截止证据](evidence/native25-absolute-date-deadline-source-review-2026-10-19.json)，不需要新DLL。原生 `ArmTacticalDailySentinelV1` 接受任意未来整日target；Native25实际链接的daily post RVA为 `0x2988FB0`、SetPaused RVA为 `0x383E3E0`。它仍是单slot；本次没有并行多Arm，也不把源码研究当作新tuple实机通过。

- `NativeHeadlessGameplayDriver.configure_campaign_score_cadence_v1(campaign_id=..., start_date="1066.9.15", start_date_raw=53144328, months=360)`显式启用；`bridge/campaign_deadline_v1.py`保留固定T0和下个严格未来月界。未配置的driver保持原语义。
- `GameplayBridgeService.plan_turn`的public返回前和真正共用的`_execute_planned_turn_without_unhandled_capture`入口调用幂等pure cap。AUTO本身调用public `plan_turn`；普通Sway的内部fresh plan绕过public方法，但仍经后者共用dispatch。cap在原before-submit显示、实际执行和记录前完成，不增加MCP查询。
- battle decision、committed route、stationary objective hold使用原canonical builder，只缩短同一次Arm的target，保留actor/army/war/objective、mode、watch顺序、speed及A/B守卫。fixed cruise/epoch由driver按同一cap约束；没有擅自开放speed5或原资格未通过的scope。3日route窗口缩到2日时，只复用同帧已证明窗口的合法前缀；剩1日用现有`life-advance-one-day`窄收尾，其余时间不退化成全程逐日。
- 普通`life-advance`保留原局面的horizon与速度选择，在`bridge/campaign_deadline_transport_v1.py`用**一个**date-only `terminal-a-0`原生sentinel推进至`min(原horizon, 下一月界, 终点)`。新scope名是`campaign_date_deadline`，不冒用旧exact-one-day资格。Arm/Status/Cancel、generation、target、实际ticks、pause、zero overshoot沿真实typed传输和原validator核对；正常路径不另发`pause-map`。早期真实modal按同generation cancel，未知cancel不重发。
- Death Close原transport内部的`driver.execute_step("life-advance")`自然继承同一driver cap。终点处底层返回0日、0时钟动作且`calendar_progress_verified=false`；现行Close合同仍不授liveness，不改成假普通/继承成功，也不越终点推进。

新增必要软件compound是 `test_campaign_deadline_transport_v1.py`：实际Driver `execute_step` → 原primitive executor → Protocol fake wire → 真实Arm/Stop validators。5项通过（含29日、5日和终点3日多日slice、同canonical active-battle target和watch、public/internal共用dispatch及A/B字段、过冲真实拒绝、endpoint零resume、未配置原语义）；末次执行退出0、0.042秒。测试构造的native packet明确为软件fake，不是Native25新局的真实paused或动作资格。首条测试导入曾因fixture的unit路径未入PYTHONPATH失败；设置以下完整测试路径后通过。

```text
set PYTHONPATH=ck3_autonomous_player\src;ck3_autonomous_player\tests\unit
py -B -m unittest ck3_autonomous_player.tests.unit.test_campaign_deadline_transport_v1
```

后继仍由runtime owner在新tuple核真实capabilities、正式启用配置、采baseline和普通月样本、读取第一批native deadline回执。此包不声称30年已经推进、360月已经取得，E/M/H及其他未闭合数值仍为unknown。没有追加每AUTO的外部MCP请求；普通多日时钟内部用原生Arm/Status代替轮询后暂停，实际墙钟收益仍待同策略现场记录。
