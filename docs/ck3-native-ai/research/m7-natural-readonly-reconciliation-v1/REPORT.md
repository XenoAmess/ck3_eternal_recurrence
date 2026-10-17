# M7 自然继承：只读分产核对尚未生成的确定阻塞

对已冻结 SDK44/outer 全链审查发现一处必定拒绝的输入组合：死亡在原 sentinel 执行中被发现、实际继承人已发布，但 `succession_reconciliation` 尚为 `None`。原 terminal helper 只读 SEM 后立即要求 matched reconciliation。SDK 的 SEM 仅投影 Driver 成员；该成员由普通 planner 的既有 Root 读取与 `reconcile_retained_succession_transition_v1` 生成。原 clock 抛错后没有下一次 planner，因此严格 qualifier 返回 None，需停机处理。旧测试用已构造 matched reconciliation，未覆盖这道生产接缝。

**一个最小候选：**只改私有 terminal helper。仍用原 qualified-frame / expected-transition 证明同 Game、暂停、活的实际预期继承人、原 EP/goal；只有 reconciliation 为 None 才进行一次既有 `ck3_plan_turn` 与一次 fresh SEM。plan 必须返回 `ordinary_successor_continuation_ready`，再交给原 full-estate matched qualifier 和原 Continue/Close/SAVE 事务。错误继承人、外来 EP、已有红色分产结果均不启动新查询。原 clock、pending 与请求 ID 不重放，不授原失败回合/日期/业务信用。

这里的 plan 不是“无任何副作用的纯函数”：真实 Root query 会保留观察/历史，planner 更新已有内存 reconciliation；它不执行规划中的动作、不推进日期、不安排镜头。测试在完整当前 `GameplayBridgeService.plan_turn` 入口执行，生产 Driver reconciliation 方法和分产合同未替换；任何 execute/camera 调用均会失败。正例只有一笔 Root 读取、零 gameplay/camera 调用。新 PLAN/SEM 各自留唯一 request/INFLIGHT/response/audit；只读 probe 数为3（包含原 SEM）。

**验证与边界：**6 个新增用例首轮通过；后补正确只读计数仅重验受影响正例通过。错分产真实计算为 `title_distribution_mismatch`，保持原 halt/pending。使用已闭实际3219失败/plan与3221语义外形，继承人发布为明确离线反事实。此次 Continue/Close/SAVE 保持原源码，以已有事务 seam double 验证接线；先前11例完整事务证据仅回链，未重复运行，不能当当前 .4 自然继承实机验收。

完整通路其余结论：正常成功 sentinel 在 queue:3486–3504 先走自然边界；metrics确认后:4476–4562 进入 inline handoff。失败 sentinel 由 partial/gate 分到 terminal helper，补丁只补上述缺失准备。真实 matched heir →逻辑 Continue（无 CK3命令/无重启）→新 EP与 continuity goal（保留 origin/campaign/goal，继承计数+1）→既有 death-modal typed Close 独立清除证明→新 EP SAVE→queue基线/goal/skills focus前台缓存续接。常规 SAVE 两种时局均90日；继承边界额外实际SAVE仅一次，`checkpoint_saved`把90日时钟绑定新 actor/EP。

成功后 predecessor 的 frontend governance/focus 归档再清，LIFE pending/applied receipts 按 EP 严格过滤；新 EP 重新计算 monthly cadence。未知事件/交互在 SAVE前后必须原样保留，下一普通 planner用当前 Native scope处理，既有三 offline workers不依赖角色固定 ID。handoff 内每次现有动作/结果经 compact overlay relay，普通 AUTO仍走既有 before-submit 展示。若本身无可玩继承人、estate真不匹配或Continue/Close/SAVE结果未知，守卫仍保留，补丁不伪造成功。

另有一个非停机证据的 LIFE 排程间隙：战时 `active_event_`、`pending_character_interaction_`、`pending_war_interaction_` 的 query 阶段可能暂让给 LIFE root/perk；unavailable 会恢复原查询。未纳此单一修复，不称必停或继承失败。

新当前局尚无真实自然继承 terminal/目标续接终态。G2保持6/8，M7未验收。SDK45是否合入只由 Root/fresh负责；原44和活45均未修改。候选必须prefix重绑与source-epoch精确pin，不能原样覆盖活动helper。
