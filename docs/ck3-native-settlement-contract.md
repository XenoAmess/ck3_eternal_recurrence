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
继续保留，但现在只负责稍后显示 UI。CK3 1.19.0.6 曾实测死亡 root 的 scorer 后父链不稳定，因此
wrapper 能否在该版本真实死亡路径中完成其尾部 commit 仍必须由下一轮实机确认；当前不把静态顺序
冒充实测结果。

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
`100`、`1000` 或其它 raw scale。当前逆向资料尚未证明 1.19.0.6 内存中 `CFixedPoint` 的 raw
缩放因子；逐版本 native adapter 必须通过引擎类型/accessor 正确解码，再把“1.0 = 1 分”的语义值
交给公共 snapshot。不得直接把未知 raw integer 当分数，也不得在 Mod 侧舍入成整数。

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
4. 仅当 `candidate > old_record` 时调用一次生成的 `xar_write_record_effect`，并写
   `record_written=1`；否则为 `0`；
5. 直接写 `commit_serial=1`，并在死者上添加 `xa_settlement_committed`；
6. 最后写 `ready=1`。其后不再写任何结算字段。

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

`record_written=1` 表示对应的 `xar_hs_ge_<candidate>` 存档内触发位已经由 writer 设置，且 writer
不会为同一死者再次执行。跨存档介质 `tutorial.txt` 仍由 CK3 的 tutorial lesson 队列异步完成；
因此 `ready=1` 不等于外部文件已经落盘。

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

本轮只修改手写生产脚本、静态契约和本文档，没有启动 CK3。`tools/validate_static.py` 检查：

- 有/无继承人两条死亡链各调用同一 wrapper，wrapper 内严格先 scorer、后唯一 commit；
- delayed `xar.1003` 不再包含 scorer、commit 或 record writer，只做 UI 分流；
- record writer 只位于 commit effect 中一次；
- source、八项数值、record result、serial 和 ready 的字段映射；
- `ready=1` 是 commit effect 的最后一次 global 写；
- `xar.1001/1002` 只消费稳定 projection，且没有玩法授权或纪录提交入口。

下一步实机闭环应分别覆盖有继承人与无继承人死亡，并由 native snapshot 读取 source、serial、分数和
record result；有继承人样本必须确认继承人没有 `xa_enabled`，且 agent 未继续替其游玩。
