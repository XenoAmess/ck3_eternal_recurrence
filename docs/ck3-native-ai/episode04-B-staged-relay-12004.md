# B 分阶段 relay：共同 S0 → 拆军 → 休整 → 会合重并 → 路线交接

[strategy_b_stages.py](../../promo/ck3_native_war_ai/episode-04-march-logistics/tools/review02/comparison/strategy_b_stages.py)组合已有 Root file Relay、[B next adapter](episode04-strategy-b-next-12004.md)与[冻结 B 策略](episode04-strategy-b-12004.md)。此包只有离线代码、fake transport验证；没有调用真实relay、SDK、游戏、桌面、EXE或native build，没有B实际结果信用。

共享 `split_merge/root_relay.py` 的 `merge-once` 使用初始post-split帧，适合R09零日微实验；真实B休整后不能复用它的same-frame前提。新组合器保留该共享文件和原post-split，B会合时另采fresh packet，并在B子目录独立落一次性merge claim。它没有删除或覆盖共享claim、baseline、旧证据，也不把R09终态当共同S0。

## Root使用接口

模块导入和`--help`完全离线。真正阶段仅由Root显式调用；它复用Root现有的admitted `Relay`实例，不创建SDK连接、游戏会话、录制或时钟。独立B回放使用自己的case-id；不能复用已经有split claim的R09 case。

```python
stages = BStages(
    reviewed_root_relay_module, admitted_root_relay, reviewed_next_adapter,
    frozen_plan, plan_pin=exact_plan_pin, evidence=relative_evidence_reader,
    previous=explicit_previous_state, previous_pin=exact_previous_state_pin,
    s0_arm=actual_existing_R10_B_arm,  # baseline阶段使用
)
result_pin = stages.run("rest")
```

`root_relay`及`next-adapter`均以精确Python源SHA绑定，导入前核对；Relay原有MODULES/sidecar、context/runtime proof/request helper、machine/PID/create-time/generation/actor/episode和期限守卫继续生效。当前共享Relay绑定dcda/R0176正常Robert；本组合器不把它放宽为其他run。Root需选择实际满足其绑定的独立正常冷载场次，否则保留hold。

CLI提供`baseline / split-once / post-split / rest / merge-once / post-merge / route`。保留Root relay已有的repo、context、runtime-proof、request-helper、各SHA、run-id、case-id、attempt和army-id参数，另加：

| 参数 | 用途 |
|---|---|
| `--root-relay / --root-relay-sha256` | 已审阅共享root_relay.py，不复制或改它 |
| `--next-adapter / --next-adapter-sha256` | 已审阅strategy_b_next.py |
| `--plan / --plan-sha256 / --evidence-root` | 原始冻结完整R10计划与既有相对证据根 |
| `--previous-state / --previous-state-sha256` | 上一阶段实际回执的精确pin，禁止glob/latest |
| `--s0-arm / --s0-arm-sha256` | baseline所需既有真实R10 B arm；不能填未来结果 |
| `--self-sha256` | 本组合器自身精确SHA |

每次新attempt；输出为exclusive-create的state pin，继续时显式传入它。`HOLD_`状态CLI退出2；正常读后态或提交记录退出0均不等于业务总体验收。`--help`可直接离线运行，所有live参数说明由它列出。

## 阶段合同

| 阶段 | 实际工作与后续 |
|---|---|
| baseline | 先复用B audit核真实冷载save SHA、runtime、冻结时间/构建及完整T0 projection；再读取fresh Root packet比对逐ID整数、DATA、库存/cap、统帅、位置/route、战争/钱包。日期相同不能替代共同S0。缺实际arm/readback则hold，无split。 |
| split-once | 复用Root既有一次split claim/原生提交。只记录submitted；capability不是legality。 |
| post-split | 复用Root fresh transfer断言和完整Character/DATA链，实际识别child。超时后可用旧baseline state读原请求再做本阶段，不重发split。 |
| rest | 只读fresh packet；记录两军各自实际stationary入站日期，然后判断退出。还没到站则输出现有preview/route依赖，不发Move。没有时钟推进。 |
| merge-once | 两军均有实际退出且在冻结meeting province驻定时，采当前meeting packet并再读same-frame，按冻结main/child方向建立B独立claim后仅提交一次。它不要求回到最初post-split日期。 |
| post-merge | 读取该claim的原请求/响应；独立fresh post-frame证明D存续/S消失、owner/control/site/generation、无关cohort保持；复用ordered physical DATA / Character-role比较并保留真实前后assigned commander。不能把+1缓存当物理补员。 |
| route | 对实际surviving Army返回现有next adapter的goal preview/arrival依赖；不直接发Move，不发clock。不用当前到站读数授首次到场、D90或费用信用。 |

日推进和路线执行仍走Root既有exact-day、preview/Move与实际路线后验链。本组合器交接`army_id / target_province_id / required_preview_step / role`，不能用手写Move ACK跳过该链。Root在实际推进/移动后再调用`rest`或`route`。

## 休整停止条件

从实际驻定帧起算自然日，严格保持计划的`minimum_stock_raw / maximum_deficit / maximum_rest_days`：

- 真实stock达标**并且**实际max-current缺额不超上限，退出原因`threshold`。
- 真实达到最长驻留，即使stock没恢复也退出，原因`maximum_rest_days`，另列`recovery_threshold_observed=false`。
- 缺实际stock/cap或scale，输出`HOLD_ACTUAL_SUPPLY_UNAVAILABLE`与具体`ck3_query_army_strengths / army_ids / expected_revision / ordinary_core_v1`字段；正monthly getter不能填库存。
- 无退出记录即离开驻点、超最长驻留、缺同自然日计量则保留hold/deviation，不事后改策略或重启预算。

Root的R09小投影不含supply字段。组合器只从`packet.refs.strength_raw`指向的**该次完整Driver JSON**及原snapshot响应读回库存/cap；先核原bytes/SHA、query frame、generation和完整scope，不找目录latest，不拿小投影的缺字段填0。typed commander原包也逐军核同帧。

完整正式计划仍经过原`recipe/check_plan`；`compare_fees=true`而R07/R08资格引用缺失会在live Relay构造前停住，不能静默关费用列。当前费用、未来库存变化和兵数变化原因未充分时保持null/hold；本包不构造新的军费、全程恢复或补员预测。

## 单次动作、闭场与资格

所有动作claim在发送前exclusive-create；结果未知或原生拒绝只能读原请求/响应和新后态，禁止删除claim或重发。B merge claim与原pre-meeting raw refs一并保存；post-merge可从旧meeting state加该原claim恢复，仍只读。stage文件仅保存小投影与精确原件pin，不复制完整DATA原包；B子账本有1MiB有限上限，预算满保留最后state并停止扩张。

阶段状态固定`live_B_comparison_qualified=false / research_card_closed=false / physical_refill=null`。新的[9项聚焦验证](../../promo/ck3_native_war_ai/episode-04-march-logistics/tools/review02/comparison/test_strategy_b_stages.py)只测试本包新行为，使用fake Root transport：并行实际入站计时、缺额不豁免、最长驻留未恢复退出、缺stock与正getter分离、休整后fresh meeting/一次claim、超时不重发、原始Driver hydration、绝对期限及仅日期不足以准入S0。没有重跑旧13项next测试，也没有实机资格。

```text
<verified-python> -B -O -m unittest discover -s promo/ck3_native_war_ai/episode-04-march-logistics/tools/review02/comparison -p test_strategy_b_stages.py -v
```

本包外置产物属于可重建derived，使用Root本次active32/metadata17池内1MiB分配；继承原期限，不自动扩容或续期。实际机器、观察时间、源/依赖SHA及测试回执由外置交付清单记录，不能据此宣称其他机器已部署或B回放已执行。
