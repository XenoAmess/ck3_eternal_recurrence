# R10 Python执行接线与三臂准入边界

2026-10-17追加；离线审阅机器 `machine_id: desktop-3fevhd2-1c74096080`，来源阅读基线 `611bc985ae95f477dd7314df11f8602cd1e595f3`。本页记录Python实现及离线检查，未分配新场、未接SDK、未构建native、未取得新实机或媒体资格。源码整合、部署和实际游戏结果分别结算。正式A/B/C仍 **0/3**，共同新T0尚未选定。完整来源pins和历史检查回执见[小型来源清单](evidence/episode04-r10-python-execution-12004/source-provenance.json)。

## 本次执行接线

下列9个产品文件来自同一已封候选；存储预算和普通constructor修正一起使用，避免中央wrapper覆盖正确的局部计量。现有A入口不在本次改动内。

| 消费者 | 变化与入口 |
| --- | --- |
| [中央比较器](../../promo/ck3_native_war_ai/episode-04-march-logistics/tools/review02/comparison/r10_compare.py) | `RuntimeTotalBudget.bind_live`计整个实际`io.run`、实际`state_dir/native-session`和ledger，去重并保留下一响应/完整Driver预留。支持合法prepare重试的state-a02，包含run根mcp-calls。state/native-session不一致或越出admitted scene即拒绝。profile组件仍按原准入独立计量。 |
| [Root relay](../../promo/ck3_native_war_ai/episode-04-march-logistics/tools/review02/split_merge/root_relay.py) | 正常constructor可接`--prepared PATH --prepared-sha256 SHA`；证明链须包含同一prepared精确pin、同machine/scene、同正常S0。由prepared.state_dir定位Driver原件，case续行不能替换prepared。旧无prepared入口保留原有限合同。 |
| [B阶段入口](../../promo/ck3_native_war_ai/episode-04-march-logistics/tools/review02/comparison/strategy_b_stages.py) | 新增`move-stage-once / move-stage-post / advance-stage-day / recover-stage-day`，分别发一次动作、独立后态、逐日推进和只读恢复；原split/rest/merge/route及common-horizon阶段保留。新live必须显式prepared和comparison-core两组PATH/SHA。 |
| [B普通阶段](../../promo/ck3_native_war_ai/episode-04-march-logistics/tools/review02/comparison/strategy_b_normal_stages.py) | 执行既有完整packet、once-claim、Move后态及exact-day合同。未知原动作结果只读原响应，不自动重发；未到站不能借common horizon补日。 |
| [B argv组合器](../../promo/ck3_native_war_ai/episode-04-march-logistics/tools/review02/comparison/strategy_b_run_argv.py) | `build`只读取精确metadata、调用pure guard并生成真实argv，不提交游戏请求。`repo/overlay_root`和可选`code_overrides`明确代码来源；入库后均可指同一checkout。common-horizon仍要求实际first-arrival pin。 |
| [C纯策略](../../promo/ck3_native_war_ai/episode-04-march-logistics/tools/review02/strategy_c/strategy_c.py)与[下一决策](../../promo/ck3_native_war_ai/episode-04-march-logistics/tools/review02/strategy_c/strategy_c_next_decision.py) | 完整非空路线中的`embarked`可作为在途状态；保留原Army、target、路线后缀、DATA与时钟条件。海上空路线不能证明陆地抵达。 |
| [C phased入口](../../promo/ck3_native_war_ai/episode-04-march-logistics/tools/review02/strategy_c/phased_relay.py)与[正常operation relay](../../promo/ck3_native_war_ai/episode-04-march-logistics/tools/review02/strategy_c/operation_root_relay.py) | 正常实例自带`strength_at/coherent_stop_core`，读取prepared实际native-session，不再借绑历史state-a01方法。shared guard从显式bundle.repo解析，继续核精确guard pin。没有AST改写、constructor旁路或新增全局source hash门槛。 |

## 沿用当前host与实际输入

当前file-queue host接口已经适用。新场bound helper导出`ASSETS: Path`、`RUN: Path`、`CONTEXT: dict`；`request(identifier,tool,arguments,timeout=...)`返回原始完整envelope，含request/body/is_error/machine_id及原有army_history_evidence。`owner_film_candidate.request`的body-only返回值不能直接当此helper；优先复用现有bound scoped helper。不得补造outer元数据，或借旧run的CONTEXT、PID、episode和Driver。

每个未来臂必须提供：冻结PLAN及同一普通S0、该臂独立冷载runtime、canonical context、实际Root proof/prepared、完整原envelope的request-helper、显式live-binding、同场Root实际capacity和有限deadline，以及各模块精确pins。prepared.state_dir是Driver状态权威；单文件16/32MiB与总runtime预算分别核验。所有新值由真实分配/读回填写，旧a10失败、R191续行或R195 control不能代填。

[pure runtime投影](../../promo/ck3_native_war_ai/episode-04-march-logistics/tools/review02/root_runtime_projection.py)把现Root proof/prepared/context映射为已有R10 runtime schema。`started_at_utc`来自实际process creation FILETIME，保留100ns精度；不能用proof较晚的recorded_at证明冷启动晚于PLAN冻结。它只读小metadata，不哈希EXE/DLL/save、不接SDK、不授冷载或业务资格；现有运行source/DLL/proof guard继续负责执行准入。Python运行来源与native构建来源分别保留，不因纯Python变更新增native重建要求。

真实CLI（占位值须由Root实际输入替换，不是可直接运行的场次）：

```text
<python> -B promo/ck3_native_war_ai/episode-04-march-logistics/tools/review02/root_runtime_projection.py --proof PROOF SHA --prepared PREPARED SHA --context CONTEXT SHA --plan PLAN SHA --evidence-root ROOT --output NEW_RUNTIME.json
<python> -B promo/ck3_native_war_ai/episode-04-march-logistics/tools/review02/comparison/strategy_b_run_argv.py --binding B_BINDING --binding-sha256 SHA --stage baseline --attempt B-baseline-a01 --out NEW_ARGV.json
<python> -B promo/ck3_native_war_ai/episode-04-march-logistics/tools/review02/strategy_c/phased_relay.py prepare --bundle C_BUNDLE --attempt C-prepare-a01
```

B后续每阶段传精确previous-state，Move传实际role Army ID，恢复传原day-start。C按当前phase使用`admit / move-once / path-after / advance / recover-day`及显式common-horizon/recovery。每日上限和D90是现有冻结合同；到场后D90只在真实first-arrival及hold政策通过后继续，不改起始时钟。C的draft-only probe-via与frozen normalconstructor条件保留；Root应先以现只读preview取合法路线，再统一冻结，不绕gate。

## 可移植离线回归与来源范围

原外置候选在上述机器上实际新增13项focused检查通过：B3、C4、shared meter/prepared4、runtime投影2。B含transport/business阶段stand-ins，shared为synthetic IO；C走完整normalconstructor及正常CStages接线。没有重跑旧矩阵，也没有原生或游戏日信用。

入库测试只把外置bootstrap迁到checkout相对位置；B同树guard路径断言同步校正，其他业务断言保持。移植后只做AST/路径/补丁静态检查，**没有重跑这13项**，不能把原外置PASS冒称移植版新PASS。可在后续需要验证新增变化时使用standard unittest发现下列文件：

| 测试文件 | 原实际数量与关注点 |
| --- | --- |
| [B](../../promo/ck3_native_war_ai/episode-04-march-logistics/tools/review02/comparison/test_strategy_b_hot_overlay.py) | 3；真实argv/main/dispatch，guard与预算顺序、prepared/core显式接线、未知原动作不重放 |
| [C](../../promo/ck3_native_war_ai/episode-04-march-logistics/tools/review02/strategy_c/test_operation_hot_gaps.py) | 4；normal provider、state-a02完整query、embarked后缀/登陆、stale/state/unpaused拒绝、中央meter连接 |
| [Shared](../../promo/ck3_native_war_ai/episode-04-march-logistics/tools/review02/comparison/test_runtime_prepared_session.py) | 4；whole-run与prepared侧车计量、容量不足0transport、proof/S0/scene精确绑定 |
| [投影](../../promo/ck3_native_war_ai/episode-04-march-logistics/tools/review02/tests/test_root_runtime_projection.py) | 2；canonical runtime schema、真实FILETIME及严格跨run/路径/冻结时间拒绝 |

本页是[同T0三次独立冷载合同](episode04-r10-next-abc-t0-12004.md)与[总runtime预算](episode04-r10-runtime-total-budget-12004.md)的后续实现说明，保留旧时点的pending/NO-GO和检查记录。R07沿用[boarding控制研究](episode04-r07-v2-boarding-control-12004.md)，R08沿用[费率/资源4应用](episode04-r08-rate-resource4-application-12004.md)与[语义归因审查](episode04-r08-semantic-attribution-audit-12004.md)。R09的[原生selected93微实验](episode04-r09-selected93-micro-actual-12004.md)是历史来源；当前闭卡依据是[R194及其独立反向对照](episode04-r194-forward-split-merge-12004.md)和[Root研究判定](evidence/episode04-r194-forward-split-merge-12004/root-research-decision.json)：R09研究/业务已闭，dynamic/clean/human仍未授。本次没有新增native机制，不重新授实际付款、stock差异或clamp资格。

未来common S0仍须真实选择。R0176普通postmerge与R191 Palermo围城只是不同候选谱系，不能把后者直接冒充原三路线起点；R194同stock100/100不提供distinct-stock、clamp或费用证明。R07/R08未合格的实际账、B驻点实际补给增长、真实C预览、三次独立冷载、逐日完整数据、影片镜头与人审仍按各合同完成，unknown保持unknown，不补零。
