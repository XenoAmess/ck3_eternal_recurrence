# 天朝 361 AI-owned B1 后台履责 action cell v1

## 状态与目的

- 当前状态：`static-ready / unit-tested / runner-wired / production-live pending`
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

- paused 玩家 CharacterID `29037`（历史角色 `han_6875`）；旧证据中的 `32904` 是其上司，
  不是 played root；
- `date_raw=53147016`；
- 存档、EXE 与 mod tree identity。

它尚未提供一个由 paused native discovery 得到的真实 AI 天朝制公爵+ owner 和直属受评 subject。因此 helper 已可进入正式 runner，但当前不能诚实构造正例查询。最小补充接口应由种子发现流程写入，而不是手填猜测 ID：

```json
{
  "domain_query_matrix": {
    "schema_version": 1,
    "b2_pip_owner_character_id": 0,
    "incident_owner_character_id": 0,
    "workforce_owner_character_id": 0,
    "ai_owned_case_owner_character_id": 0,
    "ai_owned_case_subject_character_id": 0
  }
}
```

这些 `0` 只是此处 schema 示意，不得写进 ready seed；当前 blocked contract 实际使用 `null` 明示尚未发现。正式 seed 必须保存非零 ID、paused MCP 原始响应和哈希。若在 bounded horizon 内 provider 始终返回 `case_not_found`，helper 会给出 `ai_owned_case_producer_seed_unreachable`，表示应调整到可达生日/周期的真实 seed，而不是放宽资格或伪造 receipt。

## 批量实机建议

正式 `--phase2-live-batch` 已接入本 action cell。当前批次的单次 restore 事务为：

```text
pre-restore 四域 provider
  -> save-checkpoint（真实 B2 prompt 仍在）
  -> B2 accept + B2 provider 后置条件（只为清除已冻结的玩家 prompt）
  -> AI-owned bounded life-advance
  -> 新 mechanism_039 / roster_lock receipt
  -> fresh paused binding
  -> restore-checkpoint
  -> post-restore 四域 provider 与 pre 语义投影比较
```

AI-owned helper 仍然不选择任何玩家事件。B2 是前一项已经独立证明的产品 action，放在同一冻结事务内是因为 checkpoint 本身含有该 prompt；B2 清除后才允许 AI-owned helper 进入 event-free timeline。此后如果出现任何玩家事件，helper 只调用 current-event MCP，把完整 typed identity 写进 RED evidence，然后停止，绝不自动点选。

action 原始报告保存在 `05_phase2_ai_owned_case_gameplay_action_cell.json`。runner 只在同时看到以下事实时把该 cell 记为完成：至少一次真实 `life-advance`、`gameplay_action_executed=true`、新 roster-lock receipt、`background_business_complete=true`，以及 `action_ack_is_business_postcondition=false`。ACK 即使 accepted 也不能替代业务回读；RED 返回报告原样保存。恢复使用 AI 业务后置条件之后的 fresh public revision，而不是任一 action ACK 的 revision。

若 action 返回 typed RED（包括玩家事件阻塞），外层仍先从该 RED 后的新 paused revision 执行 restore，再把原始 action RED 传播给 batch；因此失败尝试不会绕过冻结基线恢复，lineage artifact 会分别标出“restore topology GREEN”和“checkpointed action RED”。

默认 horizon 仍为 370 个 `life-advance` / 370 日，覆盖默认年度 pulse；若启用了三年周期规则，应该另备靠近第三年到期点的真实种子，不能简单把长跑超时记成产品失败。每一步和每次 provider 响应都保留在返回报告。AI-owned 成功后，phase-two missing action 只剩 Workforce collective 与 scoreboard named-widget；二者未完成前总结果继续保持 RED/incomplete。

离线回归：

```powershell
& "tools\.venv\Scripts\python.exe" "ck3_autonomous_player\tests\unit\test_zhongguo_ai_owned_case_action.py"
& "tools\.venv\Scripts\python.exe" "tools\test_run_zhongguo_promo_capture.py"
```

普通与 `-O` 都必须通过；它们只证明 helper/runner/fake MCP 合同，不把结果升级为 live。真实 paused artifact 仍待 seed-generation 实机槽释放后取得。
