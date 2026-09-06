# G2 Raiktor white-peace comparison provider（2026-09-06）

状态：**provider static-ready；同帧 white-peace terms observation 与 owner utility evaluation 尚缺，当前仍为 typed RED**。

## 原生输入账本

本包继续绑定 CK3 `1.19.0.6`、EXE SHA-256
`2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86`。施工前重读
[player-war-exit-policy.md](player-war-exit-policy.md) 与
[war-termination.md](war-termination.md)，并重新核对原版
`common/casus_belli_types/00_event_war.txt`，文件 SHA-256 仍为
`BD202AE41EBA3A0E1E7E4277D09ED1E8D8C7E66B378308BB417D974331F9C707`。

原版 `raiktor_claim_cb.on_white_peace` 明确包含：

- declared target claims 保留，weak claim 会强化；
- attacker 承担 `-5F` prestige；
- claimant 与 attacker 不同时可能产生 favor hook；
- white-peace truce 与战俘释放；
- 双方 ally contribution、stress 与 LAAMP payout 等动态分支；
- `allow_hostages=no`。

因此现有 **attacker-defeat / surrender** 六域 observation 不能复用成 white-peace terms；静态脚本
方向也不能替代同帧 actual resource、hook、PoW、truce 与 final recipient response。本包没有改写
原生 AI 决策树，只把这些已经冻结的 native/counter-policy 输入落实为 fail-closed provider 合取。

## 新 provider

输入 contract/normalizer 与合取 orchestration 已拆分为
`raiktor_white_peace_comparison_contracts.py` 和
`raiktor_white_peace_comparison_provider.py`，两个文件都低于 300 行。provider 只在四项输入同时
存在时尝试发布既有
`raiktor-white-peace-comparison-certificate-v1`：

1. `raiktor-white-peace-terms-observation-v1`：同一 paused frame 的 option、final response、
   claims、primary gold/prestige、truce、PoW、favor 与 hostage 结果；
2. `raiktor-campaign-dominance-certificate-v1`；
3. `raiktor-owner-budget-profile-v1`；
4. `raiktor-white-peace-owner-utility-evaluation-v1`：显式 utility interval、model risk 与
   evaluator provenance。

provider 严格校验：

- observation、campaign、utility 的 frame 完全一致；
- campaign 绑定 observation 的 candidate / surrender terms SHA；
- campaign limits SHA 绑定 owner profile 的 pairwise limits；
- utility 绑定 observation、campaign 与完整 owner profile 的 canonical SHA；
- observation 七个 terms completeness 位、campaign 十个 completeness 位、same-frame 位和
  utility model-risk 位全部为真；
- option、terms 与最终 comparison certificate 继续由三方 policy 的 canonical normalizer 校验。

最终 `producer.source_artifact_sha256` 是四项 normalized input SHA 组成的 canonical bundle SHA。
`producer.production_live=true` 还要求 observation 与 utility producer、campaign producer 全部
production-live，且 owner profile production-eligible；任一 fixture/static input 会把它保持为 false。

## 当前诚实边界

当前仓库没有 Raiktor white-peace 的完整同帧 terms observation，也没有 owner utility evaluation；
owner-approved budget source 与 campaign certificate 同样尚未提供。因此当前调用只能返回：

```text
status = evidence_required
comparison_ready = false
production_live = false
comparison_certificate = null
```

缺项分别保留为 `white_peace_terms_observation_unavailable`、
`campaign_dominance_certificate_unavailable`、`owner_budget_profile_unavailable` 与
`white_peace_utility_evaluation_unavailable`。provider 不启动 CK3、不查询 bridge、不生成 action，
也不从脚本、战分、测试 fixture 或默认阈值推演 production terms/utility。

2026-09-07 的
[utility provider 施工审计](g2-white-peace-utility-provider-go-no-go-2026-09-07.md) 进一步确认：owner profile
中的 ceiling/margin 只能做 hard-budget 排除，campaign 只给 continue/surrender interval，现有 combat-entry
系数又不属于退出效用。因而 utility producer 当前为 NO-GO；在 owner-approved valuation model 和真实同帧输入
出现前，不新增只搬运自填区间的 wrapper。

## 离线验收

normal 与 `python -O` 各通过 33 项 focused tests，覆盖完整 SHA/frame 合取、既有 three-way
policy 消费、全部缺项、stale utility hash、cross-frame、incomplete observation/campaign、
malformed observed terms、倒置 utility interval、model-risk 缺失，以及四项 production-live
合取。所有测试数据均为 synthetic/do-not-ship。
