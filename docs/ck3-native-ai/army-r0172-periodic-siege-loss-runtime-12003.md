# CK3 1.20.0.3：R0172 移动窗口中的周期围攻损失观察

R0172 主军在两个暂停端点之间从 **6746/6747 降至 6679/6747，净少 67 人**。27 个 actual Regiment 和 37 条 DATA 的身份、顺序与 maximum 保持一致；16 个 actual 团、17 条 DATA 的整数人数下降，全部变化与已闭合的原生有序围攻预算分配及 ordinary record 写回规则相符。这是实际人数观察与条件算术复核；**没有新增 applied-loss/refill ledger，不能写成死亡 67 人或窗口绝无补员的证明。**

本专题仅支持 exact 1.20.0.3。SDK ready 中实际 import origins 绑定该新源码树，结束 receipt 保留实际 injector argv 及 a08 路径；来源提交为 `7f1db1a773e647b9f31378d4a9ccf57a60cf9e73`，a08 bridge DLL SHA-256 为 `8d4d80249ccdfed0954181df38d81daec9740f809fe59dc6c3e7b6708872cc28`。该 build 的 EXE pin 为 `94b55397abb687a3dcd436805a5d885e6be90fa6c693feb44a9e3bbeeade02a6`。本两帧公开 Strength `source.game_version` 与 `source.executable_sha256` 均为 null；版本/部署来源由独立 build/session 证据绑定，不能将 null 改写为该包自行从当前进程证明版本。

## 实际暂停端点

| 字段 | batch01 i08 | batch01 i09 |
| --- | --- | --- |
| episode | `native-33388-a329bf767116` | 同一 episode |
| public/native revision | 40/39 | 45/44 |
| date_raw | 53147736 | 53147784 |
| 相对 Jan20 独立基线 | +15 日 | +17 日 |
| Main public/native CArmy FullID | 0/0 | 0/0 |
| 兵员/max | 6746/6747 | 6679/6747 |
| DATA current 合计 | 6741 | 6674 |
| 供给 Q100000 | 11651751 | 11037716 |
| 当前 monthly-change getter Q100000 | −877192 | −614035 |
| 当前 attrition fraction Q100000 | 1000 | 1000 |
| 实际最后供给更新 date_raw | 53147040 | 53147760 |
| native day / selected phase | 389489 /29 | 389491 /1 |
| 实际 Army bucket | 0 | 0 |
| 当前围攻预算 /供给预算 | 67 /0 | 66 /0 |
| 当前 county budget | 236 | 233 |

两端 Main owner/actor 均为 33388，所在省份 1506、完整 route `[725,1009,2174]`、最终 target 2174、`sieging` 状态均未改变。combat/retreat 为 false，active event 与 pending interaction 为 null，gathering 为 `not_gathering`。这些是暂停端点的字段；它们不构成对窗口内全部未观察瞬时事件的排除。

五个 record_count=0 的 actual 团 56–60 各为 1 人，均未变化。因此 DATA 合计比 actual 合计少 5，前后差值稳定；不能把空 DATA 等同于该团 0 人。

## 与原生分配规则的一致性

before 的 `loss_application_inputs_v1` 实际报告 siege_active=true、raid_active=false、供给预算 0、围攻预算 67、`definition_le_zero_soldiers=6677`。正 siege tier 已发布的四团合计 69 人：3/6/9 各 20，53 为 9，均未损失。

原生 `24E3781..24E37A6` 对普通合格集合按团顺序分配 `trunc0(current * remaining_budget / remaining_eligible)`，随后 `26341B0` 按 DATA 顺序写回 ordinary chunk。用预算 67、合格人数 6677 做条件复核，27 团净差与 37 DATA current 差全部吻合；预算余量归零。团 82 从 89 降至 87，说明不能对每团独立机械地取整 1%。

**逐团 eligibility 没有新增 DTO。** 对未发布 siege tier 的团，本复核采用“非正 tier”条件假设，并以实际 aggregate eligible 与已发布 positive tier 合计交叉核对；这是源规则与观察相符，不是假造执行时输入或应用账本。普通 state0/1 DATA 范围内的写回复核不外推至所有特殊 state/角色团生命周期。

37 DATA 的 identity/max/state/两类 permission/monthly fraction/prepared fraction 在本次紧邻窗口均未改变，只有 current/effective current 下降，没有端点整数正增。22 条 `native_can_replenish=true` 且 prepared fraction 非零；37 条 `native_chunk_can_replenish=false`。这支持具体端点上下文，**不证明所有未采到的补员执行为零**。

## 供给更新与 county 的边界

端点间实际过了 2 日；两次 success stamp 相差 30 日。窗口跨 D389490/phase0，Army+188 的完整 storage64 实际改变，grace anchor 完整 storage64 保持不变。供给净差 −614035，即 −6.14035，恰与 after 的当前月 getter 相同。已闭合 `24E4D10` 在成功更新时一次应用 whole signed `24E51A0` rate，再 clamp 到当前容量；不能把端点 2 日或旧 stamp 的 30 日用来乘旧 getter。执行时 getter 未被记录，不能把 after getter 当作已捕获的执行参数。

供给两端均远高于严格 `<10` 饥饿边界，当前 supply-loss budget 为 0；这不是 starvation 正例。

county DTO 两端均可用，fraction 3500/100000、minimum multiplier 70000/100000、loaded minimum soldiers 5。当前 hypothetical budget 236→233 随现兵数改变；条件 actor33388/source1506/first target725/mode1/passesfalse 保持不变。两端 province/route 未变，首边尚未完成，因此本窗口没有实际 county-entry 端点。236 不是县 ID，也不是已扣人数；minimum soldiers5 不是 movement-lock 阈值。

## 独立路线边界

证据包另保存两个净人数不变的实际路线窗口，避免把县损耗预算误作应用事实：

- +30→+32，raw53148096→53148144：province1506→725、route从 `[725,1009,2174]` 缩至 `[1009,2174]`、状态变为 embarked；Main6679/6747、27actual rows和37DATA整数、供给11037716与success stamp53147760均不变。原全军 collector 遇 unit190 `native_carmy_not_found` 失败并保留；独立 Main-only 查询确认 Main，unit190维持 unknown，没有记成0人。
- +42→+44，raw53148384→53148432：province1009→2174、route从 `[2174]` 变为空、embarked→regular；Main及全部 DATA current/effective/max 不变。18条 chunk permission false→true，其中52/53两团 persistent permission也false→true；后续地面实验必须重新建立补员基线。空route使county condition unavailable/null，不能记为false。

两个净0端点不是完整 executor/refill trace。到达存档已由Root实际保留并验证为73,795,635B，SHA-256 `d052a2e412109a28247b8844567100a272998c536711d75f0fbc29ee6a286f6a`、raw53148432；便携包只包含原 JSON pin/proof，不携带或重新读取该大型存档。

最终 bootstrap receipt 记录 SDK/keeper线程退出、错误字段null、Job0/treegone与recorder `NORMAL_TREE_EMPTY`。这是现场关闭证据，不是成片审阅或signoff。

## 复用与未完成

完整原 JSON、来源小型原生切片/build receipt、索引和标准库 verifier 放在 [R0172 证据包](../../promo/ck3_native_war_ai/episode-04-march-logistics/evidence/r0172-periodic-loss/README.md)。`verify_evidence.py` 验 bytes、暂停帧 join、cohort、整数差与条件回放，不执行 SDK/native 函数，也不授予录像审阅或因果账本验收。

可以用于本期口播：“军队仍在移动，这个两日窗口净少 67 人；时钟跨过该军团的周期更新机会，前帧围攻预算及逐团分配与这次实际变化吻合。”仍需明确 applied-loss/refill ledger、starvation 实际跨阈值与整数损失未完成。后续登陆时补员资格可能变化，不能继承本窗口 chunk=false 的排混杂结论。

本专题与便携包只是文件证据整理；不新增游戏推进、录制、完整成片审阅或 signoff 信用。Root 保留原片、失败 collector attempt 及全部现场资产。
