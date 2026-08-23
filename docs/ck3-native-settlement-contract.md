# CK3 native 一代制死亡结算契约

更新时间：2026-08-24；Mod 目标版本：CK3 `1.19.0.6`。

本文定义 Rogue 一代制自动游玩的 Mod → native 结算交接。玩家死亡或 played-character
切换仍然终止本局，继承人只承载结算事件，绝不成为下一位可玩角色。

## 1. 两条死亡路径与唯一提交点

生产链保持已经过实机验证的两种引擎时序：

```text
有存活 player_heir
  on_death
    → 在死者仍有效时保存 xar_dead
    → 在继承人上预排 delayed xar.1003 carrier
    → 同步 xar_compute_and_commit_death_settlement_effect
      → xar_compute_score_effect
      → xar_commit_death_settlement_effect
    → xar.1003 / xar.1001 只递送可见 UI

无 player_heir
  on_death
    → 同步 xar.1000
      → 同步 xar_compute_and_commit_death_settlement_effect
      → 同步 xar.1003 / xar.1002 UI 递送
```

手写 wrapper `xar_compute_and_commit_death_settlement_effect` 是两条路径共享的唯一业务入口：它在
同一死亡 effect 内先调用生成的 scorer，再立即调用唯一 commit，完成纪录信号与 agent 投影。
`xar.1003`、`xar.1001` 和 `xar.1002` 都不计算分数、不写纪录、不发布 agent 状态，也不授予玩法权限。

有继承人时必须在 scorer 后的同一个手写 wrapper 内发布 native payload，不能等 delayed carrier：
native 可能先观察到 played character 从死者切到继承人并进入 terminal。预排的存活继承人 carrier
继续保留，但现在只负责稍后显示 UI。2026-08-24 的 CK3 1.19.0.6 minimized live 已确认死亡 root
能进入 wrapper、完成 scorer 并开始 commit；该次故障是 record writer 不返回，使其后的旧 publication
顺序不可达。修复后的先发布顺序仍须在下一次实机死亡中确认，不把本轮静态检查冒充修复后实测结果。

## 2. 稳定全局投影

所有字段都是 save-scoped global variable；它们不依赖当前 `GetPlayer`，所以控制权切到继承人后仍可读。

| 字段 | 类型 / 语义 scale | 含义 |
|---|---|---|
| `xa_settlement_ready` | 整数，scale 1，`0/1` | 发布闸门；只有 `1` 时其余字段才属于一份完整提交 |
| `xa_settlement_commit_serial` | 整数，scale 1，`0/1` | 本 episode 未提交为 `0`，唯一终局提交为 `1` |
| `xa_settlement_source_character` | character scope target | 本局原玩家 `scope:xar_dead`；native 解析为稳定 CharacterID |
| `xa_settlement_final_score` | CK3 `CFixedPoint`，语义单位 1 分 | `xa_run_score` 的无损脚本变量副本 |
| `xa_settlement_score_before_reject` | CK3 `CFixedPoint`，语义单位 1 分 | 拒绝惩罚前的所选计分轨 subtotal |
| `xa_settlement_record_candidate` | 整数，scale 1 分 | 量化后的候选余烬位阶 |
| `xa_settlement_old_record` | 整数，scale 1 分 | 本局导入的旧量化纪录 |
| `xa_settlement_record_delta` | 有符号整数，scale 1 分 | `candidate - old_record` |
| `xa_settlement_blessing_count` | 非负整数，scale 1 | 已完成祝福/诅咒对数 |
| `xa_settlement_refusal_count` | 非负整数，scale 1 | 拒绝次数 |
| `xa_settlement_contract_progress` | 整数，scale 1 | 本世契约进度，当前规则为 `0..10` |
| `xa_settlement_record_written` | 整数，scale 1，`0/1` | 本提交是否调用了量化纪录 writer |

`final_score` 与 `score_before_reject` 保留 CK3 原生 `CFixedPoint`，Mod 没有把它们乘以猜测的
`100`、`1000` 或其它 raw scale。CK3 1.19.0.6 的离线静态逆向现已闭合：转换函数 RVA
`0x3A41DA0` 把 signed `int64` raw 除以 RVA `0x4594E08` 的 `100000.0f`，RVA
`0x3A48E16` 的 signed magic-division 序列独立证明同一除数。因此该版本 adapter 以
`{"raw": <int64>, "scale": 100000}` 无损发布两项分数；逐版本 adapter 仍必须分别重证，
不得把本版本 scale 继承给未知 exe。

公共 native snapshot capability 为 `game.state.xar-one-life-settlement`，state key 为
`one_life_settlement`。未发布或任一必需字段不能精确解码时为 `null`；完整对象为：

```json
{
  "ready": true,
  "commit_serial": 1,
  "source_character_id": 12345,
  "final_score": {"raw": 12345678, "scale": 100000},
  "score_before_reject": {"raw": 13000000, "scale": 100000},
  "record_candidate": 123,
  "old_record": 100,
  "record_delta": 23,
  "blessing_count": 4,
  "refusal_count": 1,
  "contract_progress": 8,
  "record_written": true
}
```

除两项 score 外的数值 global 在内存里同样使用 numeric EventTarget/CFixedPoint；adapter
只有在 raw 可被 `100000` 精确整除时才发布语义整数。`ready` / `record_written` 还必须精确为
`0/1`，不会舍入或强制转型。

## 3. 发布与幂等规则

新一局初始化只执行：

1. `xa_settlement_ready = 0`，使旧 payload 失效；
2. `xa_settlement_commit_serial = 0`。

这两个字段在玩家接受本世契约时无条件赋值，不能用 `has_global_variable` 门控：CK3 会静态注册
被脚本引用的 global 名，变量可能表现为“存在”但值仍是 `none`。

提交时：

1. wrapper 若发现死者已有 `xa_settlement_committed` character flag，判定为重复调用并跳过 scorer/commit；
2. 写 `ready=0`；
3. 写 source 与全部 payload；
4. 若 `candidate > old_record`，先写 `record_written=1`；否则保留为 `0`；
5. 直接写 `commit_serial=1`，并在死者上添加 `xa_settlement_committed`；
6. 写 `ready=1`，完成终局 payload 发布；其后不再写任何结算字段；
7. 仅当 `record_written=1` 时，最后调用一次生成的 `xar_write_record_effect`。

这里故意先发布终局、再进入教程纪录 writer。2026-08-24 minimized live（PID 119596）中，真实
`die` 后 native revision 11 已检测到 `played_character_changed`（episode CharacterID 29829，继承人
38822）；`debug.log` 只有 on_action line 103 的 `XAR: computing score on death` 与 effect line 139 的
`XAR: new record, writing bit`，之后没有发布终结，30 秒以上仍为 `settlement=null/pending`。这证明
writer 在该实机路径不返回，使旧顺序中位于其后的 `record_written`、`commit_serial` 与 `ready` 不可达。
新顺序让 native 先取得完整终局；若 `record_written=1`，Python terminal 仍会有界等待
`tutorial.txt` 中对应量化位稳定，因此不会把尚未持久化的纪录判为完成。

Rogue 模式明确禁止在同一存档继续扮演继承人，因此一个 save-scoped episode 只需要 `0 → 1`，不为
不存在的第二位可玩角色建设跨生命计数器。直接赋 `1` 也兼容升级前已经签约、尚未拥有该变量的存档；
native 把 episode 起始时缺失的 serial 归一为 `0`。

native reader 应缓存本 episode 起始 serial。死亡或 played-character 切换后，只有同时满足以下条件才
生成 terminal settlement：

- `ready == 1`；
- `commit_serial == 1` 且比 episode 起始值新；
- `source_character` 解析出的 CharacterID 等于 episode 原 played CharacterID。

该条件让 native 可以在继承窗/事件硬暂停期间继续做纯技术 handoff，同时不会把继承人误当作新一局。
读完后不得继续为继承人规划婚姻、战争、存档或时间推进。

## 4. 纪录持久化边界

`record_written=1` 表示本次提交需要写入对应的 `xar_hs_ge_<candidate>`，不表示 writer 已返回或
外部文件已经落盘。Mod 在发布 `ready=1` 后调用 writer；跨存档介质 `tutorial.txt` 仍由 CK3 的
tutorial lesson 队列异步完成。

需要保证跨局纪录后再退出 CK3 时，native terminal 还必须等待相应 lesson 在 `tutorial.txt` 中出现
并稳定，或执行已有的等价 persistence handoff。该等待只在 `record_written=1` 时需要；Mod 侧不能用
另一个脚本变量伪装成外部文件已经持久化。

## 5. 玩家限定与继承人边界

- 入口仍由 `is_ai = no` 加 `xa_enabled` / `xa_player_pact_character` 双认证限制到原玩家。
- `xar.1003` 的 carrier 只负责读取死者已提交的 globals 并打开 UI。
- 结算 effect、`xar.1001`、`xar.1002` 均不调用 `xar_enable_player_pact_effect`，不添加
  `xa_enabled`，也不把 `xa_player_pact_character` 改指继承人。
- 继承人即使因原生 succession 暂时成为 `GetPlayer`，也没有任何玩法入口；一代制 agent 在读取结算后
  返回主菜单/开始下一独立 episode。

## 6. 当前验证范围

本次顺序修复没有重新启动 CK3；故障依据来自第 3 节记录的 2026-08-24 minimized live。Mod 静态链由
`tools/validate_static.py` 检查；native reader 另由 pinned-exe anchor scanner、fresh MSVC build 和
离线 CTest fixture 覆盖。native 静态 RE 已证明：

- global container accessor slot、entry key/value 布局与 string-ID accessor；
- numeric EventTarget kind/raw ABI 与 CFixedPoint `100000` scale；
- scope EventTarget validity/object resolver；source 只有在完整 CharacterID 反解回同一
  `CCharacter*` 时才成立；
- `ready=0`、缺字段、非整除整数和非 Character source 都产生明确 `null`，不会发布部分对象。

Mod `tools/validate_static.py` 继续检查：

- 有/无继承人两条死亡链各调用同一 wrapper，wrapper 内严格先 scorer、后唯一 commit；
- delayed `xar.1003` 不再包含 scorer、commit 或 record writer，只做 UI 分流；
- record writer 只位于 commit effect 中一次；
- source、八项数值、record result、serial 和 ready 的字段映射；
- `record_written=1`、`commit_serial=1`、死者 committed flag、`ready=1` 严格先于最后一次 writer 调用，
  且 `ready=1` 之后不再直接写任何结算字段；
- `xar.1001/1002` 只消费稳定 projection，且没有玩法授权或纪录提交入口。

下一步实机闭环应分别覆盖有继承人与无继承人死亡，并由 native snapshot 读取 source、serial、分数和
record result；有继承人样本必须确认继承人没有 `xa_enabled`，且 agent 未继续替其游玩。
