# Entity directory v1：关系身份搜索与组件级可用性

## 当前结论

- **[static-ready, live pending]** `ck3_search_entities_v1` 已作为独立只读 MCP 工具发布。它只调用一次现有
  `campaign-root-context-v1`，不增加 native mailbox、DLL 写路径或游戏状态 mutation。
- 当前最小切片能发现 `self`、`direct_landed_vassal` 和 `adjacent_external_province_holder` 三类 Character identity，按完整
  generation CharacterID 排序，并支持 relation filter 与 keyset pagination。planner 不再需要预知这三类候选 ID。
- self 的主头衔、首都、immediate/top liege 直接来自同一 campaign-root frame；同帧 `related_character_contexts` 已为直属封臣和
  相邻外部 Province holder 发布原生主头衔、合法可空首都与 immediate/top liege。相邻 holder 保留 source role，同时以 native
  top liege 归一其 realm identity，不再把 holder 身份偷换成独立 ruler。
- 该工具当前只完成 entity directory 的 identity/relationship 子集。character/title/province/realm 全局目录、名称/类型、任意
  filter、title holder/owner、realm relation 和跨页冷恢复 live 互证仍未完成，不能把本页标为 `complete`。

底层 exact-build 身份、Province adjacency、holder leaf 和 player-subrealm 规则见
[campaign-root-context.md](campaign-root-context.md)。该域是 world-state discovery，不是原生 AI 在查询时进行的策略选择，故原生 AI
决策树为 N/A。

## 接口

工具：`ck3_search_entities_v1`

输入：

| 字段 | 合同 |
|---|---|
| `expected_revision` | 当前 public snapshot revision；底层 query 仍要求 paused application-main exact frame |
| `relation_filter` | `any`、`self`、`direct_landed_vassal`、`adjacent_external_province_holder`；默认 `any` |
| `after_character_id` | 可空 positive int32；只返回完整 CharacterID 严格大于该值的 rows |
| `limit` | `1..100`，默认 `50` |

输出 schema 为 `xar.ck3.entity-directory/v1`：

```json
{
  "schema": "xar.ck3.entity-directory/v1",
  "status": "available",
  "snapshot_revision": 17,
  "date_raw": 53182008,
  "relation_filter": "any",
  "after_character_id": null,
  "limit": 1,
  "entities": [
    {
      "entity_kind": "character",
      "character_id": 23456,
      "relationship_roles": ["direct_landed_vassal"],
      "primary_title": {
        "status": "available",
        "value": {"title_id": 34567, "tier_raw": 3, "tier_key": "duchy"},
        "unavailable_reason": null
      },
      "capital_province_id": {
        "status": "available",
        "value": 88,
        "unavailable_reason": null
      },
      "immediate_liege_character_id": {
        "status": "available",
        "value": 12345,
        "unavailable_reason": null
      },
      "top_liege_character_id": {
        "status": "available",
        "value": 12345,
        "unavailable_reason": null
      }
    }
  ],
  "next_after_character_id": 23456,
  "total_matching_count": 5,
  "readiness": {
    "identity_ready": true,
    "relationship_ready": true,
    "primary_title_components_complete": true,
    "realm_identity_components_complete": true,
    "ready": true
  },
  "unavailable_reason": null,
  "source": {
    "capability": "game.command.query-campaign-root-context-v1",
    "query_sequence": 9,
    "game_version": "1.19.0.6",
    "executable_sha256": "2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86"
  }
}
```

`total_matching_count` 是应用 relation filter 后、应用 cursor 前的总数；只有 page 后仍有 row 时才返回
`next_after_character_id`。rows 永远按完整 CharacterID 升序，同一 ID 不能同时出现在 self、直属封臣和相邻外部持有者集合中。

## 组件语义

每个实体组件统一使用：

```json
{"status":"available|unavailable|not_applicable","value":null,"unavailable_reason":"..."}
```

- `available` 必须有非 null `value`，`unavailable_reason=null`；
- `unavailable` 表示底层整帧或未来可选组件可能有值但当前 observation 没有发布；当前 related-character title/liege 行已全部
  由同帧 native reader 闭合；
- `not_applicable` 只用于已经由当前 frame 证明的合法无值，例如 independent self 没有 immediate liege，或 self 没有
  primary title/capital；
- `readiness.ready=true` 证明当前 identity search 和 relationship classification 可消费；`*_components_complete` 分别证明当前
  结果集的 primary-title 与 top-liege components 已闭合。它不代表全局 character/title/realm 目录已经完成。

底层 campaign-root typed unavailable 会原样传播为 directory `status=unavailable`、空 entities 与全 false readiness，不会从旧
frame、存档文本或另一个 snapshot 拼接身份。

## 当前消费者价值与下一施工入口

candidate generator 现在可以用 declarative relation filter 获取玩家、直属封臣或相邻 holder 的稳定 ID、主头衔、首都与 realm
identity，再交给婚姻、外交、战争或后续 realm-state 查询。相邻边界上的多个 holder 可以通过相同 top liege 归并到同一 realm，
同时仍能追溯 Province-holder source role。它暂时不能按姓名、距离、资源或效用搜索，也不能直接选出“最强邻国”。

最低 `ruler-state-v1` / `realm-state-v1` / primary-title succession alerts 已由
[turn-bundle-v1.md](turn-bundle-v1.md) 聚合；完整 bundle 仍缺 income/health/domain/council/faction/partition 观测。本工具的 live 互证与两个来源
vector 共用下一次 already-required paused G2 双查询和 cold restore，不为它单开长跑。

## 静态验收

- native reader fixture 覆盖直属封臣和相邻 holder 的 title/capital/liege/top-realm 解析，source contract 冻结同帧全有或全无语义；
- `entity_directory_contract.py` 覆盖三类 relation、组件状态、稳定排序、过滤、分页、typed unavailable、landless/independent
  `not_applicable`、非法输入与关系集合重叠拒绝；
- `GameplayBridgeService.search_entities_v1` 只消费经过 exact binding/build/mirror gate 的 campaign-root 结果；
- 官方 MCP SDK 已列出并实际调用 `ck3_search_entities_v1`；聚焦 normal/optimized 验收均 GREEN；
- 本包不启动 CK3、不录屏、不使用桌面输入，状态保持 `static-ready / live=false`。
