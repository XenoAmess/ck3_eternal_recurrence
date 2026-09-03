# 天朝二期双视频：宣传工具与制作前置复核（2026-09-03）

本次复核只覆盖不启动 CK3 的制作前置，不生成 TTS、FFmpeg 输出或任何占位 MP4。

## 工具版本

在可写 fresh checkout `Z:\ck3_mod_rewrite\_runtime\promo-tool-fresh-20260903` 执行了
`git fetch origin main --prune`。复核结果：

- `HEAD = 57c42fca13ea459432c1caf76e069a1fbccf602c`
- `origin/main = 57c42fca13ea459432c1caf76e069a1fbccf602c`
- 工作树无改动

因此两版正式 TTS/字幕/渲染开始前所需的远端主线更新门已经满足；有新提交时仍须在正式制作前再次 fresh fetch 并重新绑定 receipt。

## 双版本前置链

使用当前仓库中的两套 project config 与 authoring ledger，分别重新生成 no-media runbook：

| cut | runbook | SHA-256 | 结果 |
| --- | --- | --- | --- |
| `character-led` | `Z:\ck3_mod_rewrite\_runtime\phase2-preflight-audit-20260903-0930\character-runbook.json` | `D5036214BF39958D9342219991B2B00F03F126582C2024668BFE4F8529F849C2` | `RED / footage_pending` |
| `institution-led` | `Z:\ck3_mod_rewrite\_runtime\phase2-preflight-audit-20260903-0930\institution-runbook.json` | `3551CC8354E6253CA28EDBC8B7FE2740039D40F30BD4B51C93E7CB4EA2BEE132` | `RED / footage_pending` |

两份 runbook 均成功生成，且各自保留独立 cut、run ID、候选输出路径和后续审片链。authoring ledger 均为 10/10 GREEN；当前没有真实 CK3 八段 clean spans，故正确地停在 `footage_pending`，没有创建工作目录、候选媒体或 MP4。

## 低风险修复

首次直接运行 planner 时，Git 因 fresh checkout 由不同本地服务账户物化而报
`detected dubious ownership`，导致 runbook 无法读取工具 HEAD。已在
`tools/plan_zhongguo_phase2_final_promo.py` 的只读 `_git` 探针中，将
`safe.directory` 绑定到被探测的精确 checkout 路径；不修改全局 Git 配置，也不放宽到其他目录。
修复后同一 fresh checkout 成功生成上表两份 runbook。

## 自动化验证

在 `XAR_PROMO_SOURCE` 指向上述 fresh checkout 的条件下，运行双版本相关测试：

```text
42 passed, 1 warning
```

覆盖 planner、双 cut completion、footage intake、authoring claims validator 和 media preflight。warning 仅为 pytest 缓存目录 ACL，不影响测试断言。

## 当前边界与下一步

当前状态仍为 `static-ready / footage_pending`，不是成片完成。下一项可执行工作是：在稳定且可用的 CK3 桌面会话取得同一 seed/save lineage 的 8 段真实 clean spans，先通过 `zg361_phase2_footage_intake`，再按两份 runbook 分别进行 source review、TTS、字幕、候选、claims audit、双轮 1× 审片、export 与独立哈希回执。
