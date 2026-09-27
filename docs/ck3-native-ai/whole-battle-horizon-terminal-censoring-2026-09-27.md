# 整场试算的观察窗：追击第 4 日终局门

`research_envelope.py` 旧实现只在 main 阶段检查 `horizon_days`：第 1 个未来日已经判出胜方，也会立刻模拟完整三日追击，把胜负和全部追击损失计入只要求 1 日的预测。短窗胜率、`no_resolution` 和 P90 硬损失因而混入观察窗外的结果。这不是原版机制差异，而是研究内核的时间截断错误。

本次重新运行 [exact-build 终局反汇编核验器](../../ck3_autonomous_player/native_bridge/research/verify_combat_terminal_controlflow.py)，对原版 `ck3.exe` SHA-256 `2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86` 与[冻结锚点](../../ck3_autonomous_player/native_bridge/research/fixtures/combat_terminal_controlflow_1_19_0_6.json)逐字节验证通过。`0x27FB6C6` 每日先增 phase-day；`0x230A2EF` 决定是否过追击期限，`0x230A3C7` 调伤亡 tick，`0x230A3F9` 在越过期限时才写 done；manager 的 `0x27FB73E/74A` 随后正常 finalizer/移除。原版三日追击的伤害在 day 1、2、3，普通日更到 day 4 才完成 finalizer。无 route 清零或 skip-pursuit 分支仍可能在判胜当天同步转入 done，不能统一追加四日。

现在研究内核从判胜日向后只运行观察窗内的追击 tick；若窗口结束时还未到第 4 日 finalizer，返回 `no_resolution`，保留已发生的 main 与窗内追击硬损失，不提前消费完整追击/结果 envelope。窗口覆盖第 4 日时，才运行原有三日追击核并记一次终局日。完整追击的数值核没有改变，改变的是**何时把它计入统计**。两个 manifest 的 `simulator_build` 均从 `v2` 提升为 `v3`，以免旧短窗结果与修正后结果共用模型身份。

聚焦回归使用同一冻结 pre-contact 数据构造的合成 active-resume 状态：side0 当前兵力置零、败方可 route、原生已过 14 日撤退门。它验证时间语义，**不是新实机逐日回放**：

| 未来观察窗 | 旧内核 | 修正后 |
| --- | --- | --- |
| 1 日 | 已判玩家败，`battle_days=4`，玩家 hard loss raw `49992` | `no_resolution`，`battle_days=1`，玩家新增 hard loss `0` |
| 2、3、4 日 | 均提前跑完三日追击并计作已分胜负 | 依次只运行 1、2、3 个追击伤害 tick；仍 `no_resolution`，`battle_days` 分别为 2、3、4 |
| 5 日 | 已判玩家败，`battle_days=4` | 已覆盖第 4 日 finalizer，玩家败，`battle_days=5`，玩家 hard loss raw `49992` |

生产 `forecast_fixed_contact` 的默认观察窗为 120 日；游玩策略的两处固定接触试算及防守减压入口也使用 120 日，且没有直接消费 `battle_days` 字段。故正常较早结束的胜率结果只会在接近第 120 日边界时改变；短窗 API 调用和临界晚结束案例受影响最大。`contact_admission` 已通过 `no_resolution / sample_count <= 0.10` 限制未决样本，修正后它能看到真实的观察窗截断。`ActiveMainResumeResearchKernel` 目前仍是 research-only；角色 phase events、增援/离场、动态优势和 AI 撤退政策等缺口不因本次修正而闭合。

聚焦测试在 [`test_active_combat_resume_kernel.py`](../../ck3_autonomous_player/tests/unit/test_active_combat_resume_kernel.py) 覆盖追击 day 1/2/3 与 day 4 finalizer 的五个观察窗，且断言完整三日追击仍只在足够时间时调用。静态核验不等于本次拿到 CK3 live parity；追击与终局跨日逐帧对拍仍须由受管实机任务验证。
