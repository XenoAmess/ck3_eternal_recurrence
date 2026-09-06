# G2 white-peace owner utility provider 施工审计

状态：**NO-GO / no implementation / no public interface change**。

本轮只判断现有生产输入是否足以实现
`raiktor-white-peace-owner-utility-evaluation-v1` producer。结论是否定的；因此不新增默认权重、
外部 JSON wrapper、fixture 转生产适配或 action/readiness 字段。

## 已有输入能证明什么

- white-peace terms observation 合同描述同帧 option/recipient response、claim disposition、primary
  gold、attacker prestige、truce、PoW、favor 与 hostage 结果；它是结果事实，不含 owner valuation。
- owner budget profile 只给 hard ceiling 与 `minimum_switch_margin_raw`：允许损失多少 gold/prestige/claim、
  是否允许 favor、最长 truce，以及 continue/surrender 的 tail-loss 上限。它能排除越界候选，但不能把
  不同域折算成 `owner_utility_q100000`。
- campaign certificate 已要求并携带 continue/surrender utility interval，但没有 white-peace interval，
  也没有可供 white-peace 重算的每域 owner coefficient。
- `combat-entry-eu-v1` 的 coefficient inventory 服务于 attack/avoid/wait-reinforce，并且 activation 仍关闭；
  它不是战争退出的 owner preference，也未绑定当前 Raiktor candidate/terms/profile。

因此，依据现有输入只能计算 white-peace hard-budget breach，不能产生保守
`white_peace_lower_raw/white_peace_upper_raw`。把“未越过上限”当成正 utility、用战分/战争时长打分，或从
测试 fixture 复制区间，都会把未知 owner 偏好冒充 production evidence。

## 重开条件

只有以下事实都有明确来源后才实现 producer：

1. 项目所有者批准的退出效用模型，明确 gold、prestige、claim、favor、truce、PoW 与其它纳入域的权重、
   非线性/阈值、uncertainty 和 tail-risk 处理；
2. 模型版本与 source artifact SHA-256 可绑定，且与 owner budget profile 的身份/审批一致；
3. 完整同帧 white-peace observation 与 production campaign certificate 可用；
4. producer 能把 observation/campaign/owner 三组 canonical SHA、paused frame、model risk 和 utility interval
   一起写入现有 utility contract；
5. 至少一个真实 paused artifact 可复算并由项目所有者验收结果，而不是只验证 schema。

届时优先复用现有 `raiktor-white-peace-owner-utility-evaluation-v1` consumer contract。只有真实模型证明字段
不足时才修改 schema；在此之前不增加一层只搬运调用方自填 utility 区间的 provider。

## 当前边界与回归

本轮增加定向回归：当 observation、campaign 与 owner profile 全部完整而 utility input 单独缺失时，
white-peace provider 必须只返回 `white_peace_utility_evaluation_unavailable`，certificate 为 `null`，
production-live 为 false。normal 与 `python -O` 的 G2 intake/provider/policy 矩阵均通过。

当前真实状态不变：white-peace comparison unavailable、三方 recommendation/action/automatic surrender 与
`GEN-034` 均保持 false/unresolved。下一项非 CK3 工作只能等待 owner-approved utility model 或新的 production
observation/campaign producer 证据；排他 CK3 槽中的 source-specific live adapter 仍是独立 live 主线。
