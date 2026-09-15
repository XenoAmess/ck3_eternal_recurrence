# CK3 1.19.0.6 `death_management.1007` 继承人死亡压力后置

## 结论与证据边界

- **[static-confirmed]** 本专题绑定 CK3 `1.19.0.6 (Scribe)`，`ck3.exe` SHA-256 为
  `2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86`。
- **[historical production-live action]** R374 已在唯一 CK3 进程中选择 authored option 1/native 0，event instance
  `1046 -> null`、snapshot `native:1779 -> native:1780`、revision `1780 -> 1781`，事件 advance 已验证。
- **[material comparator static-ready, live pending]** 当时的 state snapshot 尚未发布玩家压力，所以旧 action 不能补写成
  material-delta 证据。当前 registry choice、effect profile 和同角色压力比较器已经闭合，但仍没有由当前实现产生的前后实机读数。

R374 的 pre-selection report、hot park 和 driver snapshot 仍存在，但 driver state 明确为 `last_checkpoint=None`，原进程已结束。
它们是可复核证据，不是可冷恢复的存档。今后只在正常 campaign 再次撞到该事件时完成一次 bounded material 验收，不为单事件长跑。

## 原版调用与效果树

`on_death` 把死亡送入隐藏的 `.0001`；它只为仍在世、且 `player_heir` 恰为死者的头衔持有者建立继承人死亡收件人。`.0002` 先分派配偶、囚禁、软禁和战死等更高优先级通知；普通 `.1007` 还要求收件人是死者的近亲或扩展亲属，并在事件打开时仍有替代 `player_heir`。普通标准封建 campaign 可以自然遇到它，但任何继承人死亡都不保证打开此事件。当前严格合同只接受无 killer 的 R374 shape：

```mermaid
flowchart TD
    A[on_death] --> B[隐藏 .0001 收件人采集]
    B --> C{在世头衔持有者的 player_heir 等于死者?}
    C -->|否| Z[普通 .1007 无继承人收件人]
    C -->|是| D[隐藏 .0002 优先级分派]
    D --> E{配偶、囚禁、软禁或战死优先?}
    E -->|是| V[其他通知或事件]
    E -->|否| F{收件人与死者为近亲或扩展亲属?}
    F -->|否| N[普通继承人界面消息]
    F -->|是| G{打开时仍有替代 player_heir?}
    G -->|否| X[.1007 trigger 不成立]
    G -->|是| H[.1007 玩家 ROOT 与继承 scope 投影]
    H --> I{与已验无 killer 三 scope shape 同帧严格匹配?}
    I -->|是| J[正式策略选唯一 authored1/native0]
    I -.->|killer/known_killer 或新 scope shape: unknown| R[保留 RED 与真实 paused frame]
    J --> K[stress_impact base=minor_stress_impact_gain]
    K --> L[after 仅显示 tooltip]
    L --> M[独立后帧核验旧事件消失与玩家压力]
    M --> O[下一正式 turn 消费关闭结果]
```

`deceased_character_stress` 虽由上游传入，但 `.1007` 本身不读取它。唯一物质效果是对 ROOT 施加
`minor_stress_impact_gain`；`00_stress_values.txt` 的 authored base 为 `+20`。after block 只展示 tooltip，不写游戏状态。
精确 killer、known_killer 或缺失 new_memory 的投影尚无同版本自然 paused 证据；出现时正式策略保持 blocked，不用唯一选项绕过 scope 合同。

## 直接消费边界

通用 direct-projection policy 仍默认拒绝需要扩展 scope 语义的合同。本包只为 `death_management.1007` 准入
`unique_character_scope_excludes`，并使用通用检查器证明 `dead_character`：

1. 是 `status=available / type_key=character`；
2. 携带可用 full CharacterID；
3. 不等于 materialized `$player`；
4. 与三个 scope 名、类型、数量以及唯一 native option 共同严格匹配。

其它带 unique-exclude 或 scope variant 的事件仍保持 blocked，不因本包自动进入 planner。

## 结构化效果与后置

选择档案为 `xar.ck3.vanilla-event-choice-effect/v1`：authored base `+20`，runtime delta 明确为 non-exact。人物的
stress-impact adjustments 与压力上限尚未作为同帧输入发布，因此可验证关系是
`played_character.stress_points / non_decreasing`：

- `post > pre`：`verified_change`，可计 material evidence；
- `post == pre`：`verified_no_change`，事件可以安全关闭，但不计 material evidence；
- `post < pre`、CharacterID 漂移或读数缺失：失败或不可用，不能冒充通过。

planner 绑定选择前 snapshot ID、revision、玩家 full CharacterID 与压力点。native action 已经会记录前后玩家压力，service 复用
现有 material-postcondition envelope，无新 mailbox、native reader、等待或桌面操作。
正式 `strategy.py` 的 `active_event_registry_choice` 仅在 registry 同帧匹配且 typed step 已广告时返回动作；
`native_auto_run.py` 对旧事件实例 advance 和注册物质后置失败保留 RED。下一次自然 `.1007` 的有界门须在普通 production campaign 中取得真实前后压力、独立后帧和下一 turn；R374 的 ACK/advance 不能补成这项证据。玩家自身自然死亡后的同 campaign 继承是另一个 G2-M3 门，不由本事件证明。

## 聚焦验证

- registry policy、unique-exclude drift、effect profile 和 material comparator：normal/optimized 各 `25/25` GREEN；
- 由上一条 registry 新增暴露的六个旧计数断言已从 `187/333` 同步到真实 `188/334`，对应 record 模块
  normal/optimized 各 `45/45` GREEN；
- `py_compile` 与 `git diff --check`：GREEN；
- 本包未启动 CK3、录屏器、注入器或任何桌面输入。

## 证据

- 原版事件：`Crusader Kings III/game/events/death_events/death_management_events.txt:1948-2057`，SHA-256
  `31591A2F2D3A61E65853CC43B9BEF4B001FEB75EA1502861D2FB9AC054AB1FB7`；
- 压力值：`Crusader Kings III/game/common/script_values/00_stress_values.txt:25-34`，SHA-256
  `104A7EF94EE9DA1092F23AEB2FD9DC971B08C695415F3B7EBFB628F381D26395`；
- R374 pre-selection report：`_runtime/p2r374-active-boundary-continuation-live/death-management-1007-red-report.json`，SHA-256
  `B69243825168B01F11C0CBDEBC321C277E3AC22CEEC2F50650ABB9C0994D1D64`；
- R374 action/advance：[`../autonomous-agent-progress/weekly/2026-W37.md`](../autonomous-agent-progress/weekly/2026-W37.md)；
- exact contract/analysis/observation：
  `ck3_autonomous_player/src/xar_autoplayer/vanilla_events/records_death_management.py`。
