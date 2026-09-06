# G2 owner-authored budget profile provider（2026-09-06）

状态：**provider static-ready；尚未配置 owner-approved source，当前 checkpoint 仍为 typed RED**。

## 交付结果

`raiktor_owner_budget_profile_provider.py` 现在把一份显式提供的 owner-authored JSON
source 渲染成三方退出策略已经冻结的 `raiktor-owner-budget-profile-v1`。provider 会：

- 严格检查 source、approval、pairwise limits 和 white-peace limits 的完整字段集合；
- 复用 policy core 的同一套数值范围、布尔类型和 profile identity 校验；
- 用原始文件的精确 bytes 计算 uppercase SHA-256，并写入
  `profile_source_sha256`；
- 只有 `approval.status=approved` 且同时给出非空 `approved_by` 与秒精度 UTC
  `approved_at_utc` 时，才生成 `status=complete`、
  `profile_production_eligible=true`；
- source 缺失时返回 `owner_budget_profile_unavailable`，draft 返回
  `owner_budget_profile_not_owner_approved`。

本包没有加入任何默认阈值，也没有复制测试 fixture 数值到产品配置。仓库当前仍没有项目所有者
批准的 source artifact，因此这里只闭合了 provider 实现与校验入口，没有把当前 G2 checkpoint
提升为 owner-budget ready。

## Source contract

source contract 是 `raiktor-owner-budget-profile-source-v1`，顶层必须且只能包含：

- `schema_version`、`contract`；
- `approval`：`status`、`approved_by`、`approved_at_utc`；
- `profile_id`、`profile_provenance`；
- `pairwise_limits`：投降 gold、prestige、claims、favor、truce 上限，continue tail-loss
  上限和最小切换 margin；
- `white_peace_limits`：white peace gold、prestige、claims、favor、truce 上限。

draft 必须把 `approved_by` 与 `approved_at_utc` 保持为 `null`；approved 必须给出两项
审计信息。显式传入但路径不存在、JSON/UTF-8 非法、字段多缺、类型错误、负上限、零 margin
或身份漂移均直接报错，不会降级成默认 profile。

消费方调用：

```python
from xar_autoplayer.simulation.raiktor_owner_budget_profile_provider import (
    provide_raiktor_owner_budget_profile,
)

provider = provide_raiktor_owner_budget_profile(owner_source_path)
owner_budget_value = provider["owner_budget_profile"]
```

只有 provider `status=available` 才表示 owner-authored profile 输入本身已就绪；它仍只是 policy
input，不是 campaign dominance、same-frame white-peace、submit 或 postcondition evidence。

## 验收与边界

离线 normal 与 `python -O` 各通过 25 项相关单元测试，覆盖缺 source、approved、draft、
exact-byte hash、approval 元数据、缺阈值、错误类型/范围、坏 JSON 和现有三方 policy 回归。
未启动 CK3，未发送 action，也没有修改 native bridge/MCP public schema。

剩余真实 blocker：

1. 项目所有者尚未提供并批准真实 source 数值；
2. campaign dominance certificate provider 尚缺；
3. same-frame white-peace comparison certificate provider 尚缺；
4. 三项输入齐全后的 paused/live、submit 与六域 postcondition 尚未验收。
