# native_campaign 保存与 Driver 恢复绑定边界（1.20.0.4）

`machine_id: 4-8e1c2f1861`。2026-10-17T16:49:42Z 至本回执时间只读研究；来源运行 `4-8e1c2f1861--faith-and-power--R0008`，运行源码 `02eea1e57a44a733cb833038b55a5fdc7bd4302a`。精确来源及字节摘要见 [证据摘要](native-campaign-checkpoint-binding-12004.evidence.json)。没有操作游戏、重读或重哈希 `.ck3`，没有补写旧回执。

D3 已实际保存并复制；Driver 状态写替换已返回，但保存绑定仍未确认，冷载恢复未验。这三个结论必须分别进入规划器，不能用一次 `checkpoint.status=saved` 合并成“持久化与恢复全通过”。

| 事实 | 原始来源 | 不能外推 |
| --- | --- | --- |
| `checkpoint.status=saved`，50,210,947 B，SHA-256 `c6095d1dfed9b9c5df6f03e69905b16a2f365128a2ceafe7695f5ebc969c5f0a` | `r8-save-created-D3-a01.json`；canonical `D3-samarra-wisdom-created.ck3.json` 的源/目标摘要完全相同；本次仅复查文件大小元数据 | 不证明 Driver episode/seed 或冷载恢复绑定 |
| `write_replace_returned=true`，`status=unconfirmed`，`save_binding_verified=false` | 同一次保存的 `driver_state_replace_receipt`，状态文件的第 12 条保存记录与 last_checkpoint 完全相同 | 原子替换返回不代表 fsync；不能把文件保存成功改写成 Driver 绑定成功 |
| `native_campaign` 的 episode character/run/seed 均为 null；四个 session 比较字段都相等 | 原始保存回执、实际状态文件及只读重放 | 不能把 null==null 当作非空身份的正向证据；不支持由 after_snapshot 补存档内身份 |

根因属于 Driver 模式合同：[`_with_one_life_episode`](../../ck3_autonomous_player/src/xar_autoplayer/bridge/native_driver.py#L4854) 对 `native_campaign` 提前返回，刻意不建立 one-life 身份；[`_checkpoint_lifecycle_metadata`](../../ck3_autonomous_player/src/xar_autoplayer/bridge/native_driver.py#L12459) 明确输出 lifecycle=null。保存仍复制内部 episode 字段，`_establish_episode_seed` 遇到 null 身份返回 None。公共受管 host 明确设置 `episode_projection=native_campaign`，因此不是实验 case 漏传一个 seed 参数。给纯原版 case 填 one-life 规则或 seed 会改错语义。

[`_persist_driver_state`](../../ck3_autonomous_player/src/xar_autoplayer/bridge/native_driver.py#L11830) 要求 checkpoint 的 episode_character_id、episode_run_id 都非空。本次其余可回读的历史行、checkpoint、session 比较均成立，失败的就是这两个非空条件。attempt 中的 `rogue_one_life / legacy-driver-default` 是内部默认诊断，不参与这段四字段 session 比较，不能把它误当作实际 CK3 规则，或声称 recorded session 因该字段不同而失败。

状态解析与恢复资格也须区分：[`load_native_driver_state_for_resume_payload`](../../ck3_autonomous_player/src/xar_autoplayer/bridge/native_driver.py#L1671) 允许 null/null，本次实际 D3 状态可解析；[`_cold_candidate_ready`](../../ck3_autonomous_player/src/xar_autoplayer/bridge/native_driver.py#L11561) 随后要求非空 episode 身份，本次实际返回 false，且在读取存档正文之前就拒绝。低层 restore 的可选 actor 比较在 expected episode=null 时不会执行，不能用其 PID/date/bytes 检查替代完整恢复证明。

当前安全补强只增加诊断字段：`binding_contract=one_life_episode_identity_v1`、checkpoint 的投影、缺失的两个身份字段清单。外置候选逐 AST 核对原 binding_verified 比较表达式完全未变；六个实际生产持久化函数的合成历史案例通过：完整 one-life 正例保持 replaced；native_campaign null、缺 run、PID 不同、历史日期不同继续 unconfirmed；写失败继续 failed。该资格不证明 D3 存档内玩家/日期、seed 或实际冷载恢复。

游玩智能体应保留已生成的 canonical 存档与保存摘要，不因为绑定诊断重复执行未知保存或业务动作；把 `native_campaign` 的持久恢复锚点标为未支持/未验，不自动采用 one-life seed。后续完整修复应建立明确的 campaign 模式锚点，并让持久化、解析、冷候选、接纳、实际 actor/date/存档摘要后验使用同一身份合同。需要正向验证真实存档身份及实际冷载；不能删除非空比较、自动迁移旧 null，或用当前游戏 snapshot 冒充存档内字段。本期视频无需为此另开游戏。

原始 R8 回执不改写其当时结果；资产保留依通用存储策略，当前必要小证据复核到 2026-10-24T00:00:00Z，不自动续期。a01 分析对 loader 的表述过宽，a02 已明确更正为“结构解析允许 null，冷候选拒绝”，未改任何旧业务证据。
