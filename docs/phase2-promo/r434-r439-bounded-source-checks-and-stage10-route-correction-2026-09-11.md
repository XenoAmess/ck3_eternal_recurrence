# R434–R439：有界 source 核对与 Stage 10 路线纠正

日期：2026-09-11

状态：**R434/R439 是 B3 focused selector 查询，不能作为 P1 Stage 10 `.120` 的 source 资格判定；R435 只判定 R432 的 Stage 11 owner-view provider 不可用；R437 为零游戏日 Stage 11 source-boundary RED。P1 仍为 `6/9 = 66.7%`，P2 仍为 `LOCKED`。**

本批没有发现新的 mod 产品故障。四次 session 均有界且均已清理，但 R439 仍是一次可避免的重复验证：2026-09-07 日报已明确记录 R159 不具备 B3 所需的两层 AI 管理关系。启动 R439 前没有先命中这条既有结论，违反“已有证据直接复用”的执行原则。本页保留 artifact，同时如实记录这次方法失误。

## Stage 10 两条不同的角色路线

离线按当前产品脚本闭合后的角色拓扑如下：

1. `zg361_p2c_on_review_published_effect` 在完成 B1 公示的考核者身上初始化 Central；该角色是 Central root/owner。
2. Central Stage 10 从 root 的直属封臣中冻结满足 `zg361_is_celestial_liege_trigger` 且 review serial 落后的 manager cohort。
3. 每个冻结 manager 是 F/AK case subject，Central root 是 case owner。Stage 10 的真实中央终态是全部冻结 F/AK case terminal；空 cohort 是合法 N/A。
4. F case 到 `state=5 / active=0` 时，仅当 subject `is_ai=no` 才排 `zg361mg.120`；AI subject 明确静默完成。

因此存在两条不能混用的路线：

| 路线 | Central owner | F subject | 可见 `.120` | 对应资格入口 |
|---|---|---|---|---|
| player-owned Central / B3 focused | 玩家 | AI 直属 manager | 否，AI 终态静默 | `query-zhongguo-manager-subordinate-selector-v1` 可为 B3 选择 AI manager 及其直属下属 |
| player-visible manager result | AI 上级（单人局） | 玩家本人 | 是 | 必须证明玩家是该上级的直属合格 manager，且上级的 Central 已进入包含玩家的 Stage 10 F case |

当前 P1 机器字段仍名为 `central_stage_10_terminal`，实际硬门要求的是第二条路线的真实 `zg361mg.120` 加 F provider terminal。它不能从玩家自己的 Stage 9/10 Central 时间线推导，也不能用第一条路线的 selector 资格代替。

旧 `zg361_phase2_terminal_stages_action_cell.py` 把 Stage 9、`.120`、Stage 11 串在同一玩家 owner 时间线上，是验收编排错误。玩家自己的 Central 到 Stage 10 后会在后台静默处理 AI manager，因此等待 `.120` 没有因果可达性。R390 在 runner 等待 `.120` 期间已经进入 Stage 11，正是该错误的实机表现；后续不得再用同一编排长等 `.120`。

## R434：R432 的 B3 focused selector 查询

R434 从 R432 checkpoint 只调用一次 `query-zhongguo-manager-subordinate-selector-v1`，查询前后日期均为 `54487200`。结果为：

- `status=unavailable`
- `selector_kind=zg361-bounded-ai-direct-manager-selection-v1`
- `provider_observed=false`
- `unavailable_reason=no_bounded_ai_direct_manager`
- manager/subordinate 均为 `null`

该结果只说明 R432 中没有可供 B3 focused 路线使用的“玩家直属 AI manager → 该 manager 的直属下属”组合。它既不满足也不否定 `.120` 的“AI 上级 → 玩家 manager”路线，不构成 P1 Stage 10 产品 RED。

## R435：R432 的 Stage 11 零日查询

R435 从同一 R432 checkpoint 只调用一次 owner-view Workforce provider。查询前后日期均为 `54487200`，返回：

- `status=unavailable`
- `readiness.ready=false`
- `terminal=false`
- `terminal_kind=none`
- `unavailable_reason=subject_projection_read_failed`

因此 R432 不能直接提供 Stage 11 terminal，`stage11_gate_satisfied=false`。查询没有推进时间，也没有发送玩法输入；该 checkpoint 不再为 Stage 11 重跑。

## R437：R398 并非 `.242` checkpoint

离线比对确认 R398 所加载产品中按 Workforce/Stage11/Central 路径筛出的 257 个文件与当前 R430 候选逐字节一致。这个结果只允许比较产品实现，不能证明 R398 输入存档已停在 `.242`。

R437 实机载入后的初始 paused snapshot 为 player `32904`、`date_raw=53611200`、`active_event=null`。operator 在要求 `.242` 的入口身份检查立即停止：`actual_advance_days=0`，没有事件选择、没有查询或提交 `.360`，随后 managed cleanup GREEN。历史 R398 实际从这个存档继续约 189 游戏日后才到 `.242`；旧“`.242` 首入 checkpoint”描述错误。

R437 是 source-boundary/harness RED，不是 mod 产品 RED。不得从该输入重新执行 189 日的单项长跑。

## R439：已知结论上的一次可避免重复查询

R159 contract 绑定 player-manager `32904` 与其 direct reviewable subject `26347`。2026-09-07 日报已经明确写明：该 seed 不具备 B3 的“AI 直属经理 → 经理直属下属”关系。R439 未先复用该记录，又启动一次 selector 查询；这是启动前 evidence lookup 不完整造成的流程失误。

R439 的事实结果仍原样保留：查询前后 player `32904`、日期 `53154120`，返回 `NO_ELIGIBLE_MANAGER_PAIR_IN_CHECKPOINT / no_bounded_ai_direct_manager`，manager/subordinate 均为 `null`；没有推进日期、没有事件或玩法动作、没有重试，cleanup GREEN。

这个结果只重复排除了 R159 的 B3 focused 资格。它没有淘汰 R159 作为所有其他路线的输入：R159 的 player-manager 身份反而与 `.120` 的 subject 角色方向一致，但 contract 没有绑定玩家的上级身份、上级 Central 状态或玩家 F case，因此仍不足以成为 `.120` near-boundary source。没有这些正向证据前不得启动时间线试探。

## 证据

| 轮次 | artifact | SHA-256 |
|---|---|---|
| R434 | `Z:\ck3_mod_rewrite\_runtime\p1-stage10-source-r434-20260911\live-artifacts\stage10-zero-advance-source-qualification.json` | `9ADDB2D82CB094FFE39C2C17A36949E1E7D47C3FB0A5FE1B44D3DA4DFC626625` |
| R434 | canonical cleanup | `1BEE071F5478420C9C45B019A3418C5284C30872150B4AFA61BE094404642281` |
| R435 | `Z:\ck3_mod_rewrite\_runtime\p1-stage11-status-r435-20260911\live-artifacts\stage11-zero-advance-terminal-query.json` | `402E91D16B8F815CB6C32E14D38069C577D47D087AA64E5A24E0632BA3A988CA` |
| R435 | canonical cleanup | `336B302BAA2719D4B0B15F7F9F7DB1692B924BE32D6950A0E62E5D74E301F14A` |
| R437 | no-launch preflight | `A7DBC8C68C18B5312903789B964F0280A0BAA00724C1F170CA05D0B67AA10467` |
| R437 | `Z:\ck3_mod_rewrite\_runtime\p1-stage11-terminal-r437-20260911\live-artifacts\stage11-bounded-terminal-live.json` | `B1F8A8038A1D6456A234F39048331FAAA620E4A0560CC2659D19C4D2C5EE4C11` |
| R437 | canonical cleanup | `341A333C0C829B810D0C7CB0E33B197B5937F1F7F0B1447C2758531B9052EECC` |
| R437 | operator cleanup | `1932156F8F7E2C6246F049C0DC9A9C413064D3160E9A09A8FCFF2F16AC80D43F` |
| R439 | R159 source contract | `BAD92E689FEDF460F5E194E55AE1D56BE881D0D83AC091113593150182131033` |
| R439 | `Z:\ck3_mod_rewrite\_runtime\p1-stage10-r159-source-r439-20260911\live-artifacts\stage10-zero-advance-source-qualification.json` | `D2CE38B5D855843DE70D50589D10E170AA4AE77EB09CAEFB2FCCDD2ADF733AD6` |
| R439 | canonical cleanup | `5BEC7631A16D9CCFB2B2B6AF3BE0CD00C65ED7E8B807E5DD5C5CED7B82B02851` |

四轮清理后的 CK3/injector inventory 均为空。runtime operator、profile 和 artifact 均在仓库外 `_runtime`，没有修改 mod 产品树。

## 后续执行边界

- Stage 10 `.120` 只接受已离线证明“上级 Central owner → 玩家 F subject”身份与 near-boundary case 状态的 checkpoint。不得再用 B3 selector 作为 `.120` source 门，也不得从玩家自己的 Central Stage 9 继续长等 `.120`。
- R159 只保留为 player-manager 基线；在补齐上级身份和上级 Central/F case 证据前不启动。R432/R434 只保留为 B3 selector negative evidence。
- Stage 11 只接受真实 `.242`、`.360`、owner-view terminal 附近的 checkpoint，或在另一个有独立产品价值的有界流程自然到达时即时保存。不得重跑 R398 的 189 日前缀。
- 单个 runner 只负责角色拓扑一致、因果相连的事件。Stage 9/11 的玩家 owner Central 路线与 `.120` 的玩家 subject 路线分开收据，最终由 P1 assembler 合并。

找到正向合格 source 前，Stage 10、Stage 11 和代表性终态 cold restore 均保持 PENDING；不再用未知 source 做实机筛选。
