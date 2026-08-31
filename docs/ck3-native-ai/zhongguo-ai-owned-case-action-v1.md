# 天朝 361 AI-owned B1 后台履责 action cell v1

## 状态与目的

- 当前状态：`static-ready / unit-tested / production-live pending`
- 实现：`ck3_autonomous_player/src/xar_autoplayer/bridge/zhongguo_ai_owned_case_action.py`
- 测试：`ck3_autonomous_player/tests/unit/test_zhongguo_ai_owned_case_action.py`
- 只读后置条件：`game.command.query-zhongguo-ai-owned-case-snapshot-v1`
- 唯一提交的游戏动作：已有 production `life-advance`
- OCR、坐标、测试决议、测试 GUI：全部不参与

这个 action cell 验收的是项目所有者授权的第二个 AI 例外：在任、有地、天朝制、AI 公爵及以上直属上司可以在后台履行管理职责；伯爵与男爵不因此取得考核他人的权限，只能作为受评者。helper 本身不向 AI 下达一条“替它做考核”的作弊命令，而是在真实 CK3 时间线上等待 mod 的年度 producer 自行触发，再从 paused 原生 provider 读取结果。

## 真实 producer 链

当前产品链的静态入口为：

```text
yearly_playable_pulse
  -> zg361_annual_review_on_action
  -> zg361_jingcha_annual_dispatch_effect
  -> zg361_issue_jingcha_mandate_effect
     -> zg361_b1_open_cycle_effect
        -> zg361_b1_initialize_subject_case_effect
           -> zg361_case_kernel_record_operation_effect
              operation_id = 39
              choice = 1
              receipt = owner/subject/cycle/case/state
```

`zg361_issue_jingcha_mandate_effect` 的玩家分支可以发可见京察召集令，授权 AI 分支只写后台日志；B1 延迟阶段事件本身也都是 `hidden = yes`。action cell 不把这些静态脚本当作实机完成证据：它们只解释要等待哪个 producer，GREEN 仍必须来自同一 real owner/subject 的 paused provider 回读。

## GREEN 合同

默认 `require_transition=true`。调用前已有的回执只能作为 baseline；GREEN 要求在至少一次真实 `life-advance` 后观察到严格更新的 cycle/case，并同时满足：

1. owner 是存活 AI，effective government 为 `celestial_government`；
2. owner 的主头衔 tier 为 `3..6`，即公爵、国王、皇帝或霸权级；
3. subject 的 immediate liege 就是该 owner；
4. route 为 `authorized_ai_background` 且 `visible_event_allowed=false`；
5. operation 为固定 allowlist `39 / roster_lock / pre=1 / post=1`；
6. policy 为 `mechanism_039 / choice=1`；
7. receipt 为 `recorded`，并与 case 的 owner、subject、cycle、case 严格 join，state/choice 均为 `1`；
8. provider 自身六项 readiness 全绿且保持 paused same-frame binding。

`life-advance` 返回的 ACK 只证明时间动作请求经过了 gameplay bridge。即使 ACK 写着 accepted，provider 没有上述回执也保持 RED；反过来，最终业务判定只由 fresh provider 后置条件决定。报告固定写出 `action_ack_is_business_postcondition=false`。

`require_transition=false` 仅提供幂等的只读后置条件检查：若调用前已有合法回执，它可以返回 GREEN，但会明确写 `gameplay_action_executed=false`，不得拿来冒充本轮 action coverage。

## 可见事件边界

action cell 既不选择事件，也不清理“一选项事件”。如果推进中出现玩家可见事件，它会：

1. 保持 paused；
2. 用 `query-current-event-window-context-v1` 读取真实 event definition identity；
3. 返回 `player_visible_event_interrupted` RED 和完整 identity；
4. 把事件处理留给独立玩家策略，再由 caller 重试本 cell。

这既避免用事件 ACK 冒充 AI 后台业务，也避免 AI manager 的授权例外被扩张成“可以操作玩家界面”。

## 当前实机阻塞与最小种子接口

仓库现有 `tools/zg361_phase2_seed_contract.json` 只冻结：

- paused 玩家 CharacterID `32904`（历史角色 `han_8052`）；
- `date_raw=53147016`；
- 存档、EXE 与 mod tree identity。

它尚未提供一个由 paused native discovery 得到的真实 AI 天朝制公爵+ owner 和直属受评 subject。因此 helper 已可进入正式 runner，但当前不能诚实构造正例查询。最小补充接口应由种子发现流程写入，而不是手填猜测 ID：

```json
{
  "domain_query_matrix": {
    "ai_owned_case": {
      "owner_character_id": 0,
      "subject_character_id": 0,
      "owner_primary_title_tier": 3,
      "owner_government_key": "celestial_government",
      "owner_is_ai": true,
      "subject_is_direct_subject": true,
      "discovery_artifact": "<paused MCP artifact path>",
      "discovery_artifact_sha256": "<sha256>"
    }
  }
}
```

两个 CharacterID 的 `0` 只是此处 schema 示意，不得写进 ready seed。正式 seed 必须保存非零 ID、paused MCP 原始响应和哈希。若在 bounded horizon 内 provider 始终返回 `case_not_found`，helper 会给出 `ai_owned_case_producer_seed_unreachable`，表示应调整到可达生日/周期的真实 seed，而不是放宽资格或伪造 receipt。

## 批量实机建议

同一次 CK3 启动中先跑现有 phase-two read-only provider 矩阵，再运行本 action cell。默认 horizon 为 370 个 `life-advance` / 370 日，覆盖默认年度 pulse；若启用了三年周期规则，应该另备靠近第三年到期点的真实种子，不能简单把长跑超时记成产品失败。每一步和每次 provider 响应都保留在返回报告，caller 负责原子写入本轮 artifact 目录。
