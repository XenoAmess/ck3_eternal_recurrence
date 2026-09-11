# R461 Workforce owner 查询 revision 重绑与来源淘汰

## 结论

R461 暴露的 `ZhongGuo workforce owner revision is stale` 是只读查询与游戏主线程推进之间的短暂绑定竞争，不是 Workforce 产品状态损坏。最小 Python 合同补丁已在同一轮次热重跑中生效：两次同类 stale revision 被重新取帧消化，没有提交游戏输入，也没有重启 CK3。

随后，原版事件 `tgp_dynastic_cycle.0081` 的无条件 immediate 块真实破坏或重组了本产品场景所依赖的领地与 manager 血统。R391 来源因此被判定为 Stage 11 不可继续，不能计入 P1，也不得再次重跑。R461 同时确认该帧没有符合 Stage 10 合同的 AI 直属 manager。P1 保持 `6/9 = 66.7%`，P2 最终宣传视频继续硬锁定。

## 运行绑定

- exact build：CK3 `1.19.0.6`；`ck3.exe` SHA-256 `2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86`。
- production tree SHA-256：`84443728419E390024936809778C98D4BF4B529747FF776DE0F2FD4DC97E58CE`。
- 输入存档：`autosave_1.ck3`，`152,482,676` bytes，SHA-256 `93745B2FE52AD31D7878D22BD1AB7898D3D09AA97AFB2BEAC1C009FC17964527`。
- 当前轮次 R460：frontend warmup，PID `144456`，到达可响应 Frontend 后结束。
- 新轮次 R461：正式 gameplay，PID `122896`，connection generation `1`；全程唯一 CK3 实例。
- 第一次 MCP 配置在 CK3 启动前因 projection manifest 名称不符而 RED；没有消耗轮次，也没有产品输入。
- 实际运行目录：`Z:\ck3_mod_rewrite\_runtime\p1-stage10-stage11-r460-r461-20260912-attempt02`。

## 第一次产品尝试：revision RED

Stage 9 的 `.390` 已由 current-event provider 观察并关闭。Stage 11 第一次自然推进后执行 owner-view Workforce terminal probe，调用链为：

`zg361_phase2_terminal_stages_action_cell.observe_workforce`
→ `BridgeService.query_zhongguo_workforce_owner_snapshot_v1`
→ `NativeDriver.execute_step`
→ native bridge `query-zhongguo-workforce-owner-snapshot-v1`。

`resume-map` 已提交，但 Python 短暂保留了上一张 paused public snapshot；native 主线程处理只读查询前游戏帧已经推进，exact-build revision 门正确拒绝旧帧。失败帧保留了 `resume-map`、紧接的 stale query，以及异常收尾 `pause-map` 的命令历史。

- RED：`native gameplay step failed: ZhongGuo workforce owner revision is stale`。
- 证据：`terminal-stages-red-attempt-01.json`，`1,576,075` bytes，SHA-256 `7AE446243258342DC31026CB9B5045010032A6C382BAEEADD02E203EBE34E6DC`。

## 最小合同补丁

补丁只在 Stage 11 owner-view 只读 probe 内识别四种已经定义的 paused binding/revision 瞬态错误。命中后记录旧 revision、日期和错误，返回调用方立即取得新 snapshot；不提交游戏输入。连续第四次仍不能取得稳定绑定时继续 RED，避免把系统性故障拖成长跑。

修改位于：

- `tools/zg361_phase2_terminal_stages_action_cell.py`
- `tools/test_zg361_phase2_terminal_stages_action_cell.py`

聚焦验证为正常 Python `14/14` GREEN 与 `python -O` `14/14` GREEN。补丁提交 `2af7543ce236dc65fbbbc24f8a15a4544150f19c` 已推送；未修改 bridge、schema、DLL、游戏文件、启动配置、加载顺序或公共 MCP 接口，因此不触发 open_kaishek 兼容层代码更新。

## 同轮次热重跑：补丁生效，场景失效

热重跑继续使用当前轮次 R461，没有重启 CK3。运行中出现两次 stale revision，均记录为 `stage11_query_rebinds`，随后重新取帧成功；`stage11_consecutive_query_rebinds` 回落为 `0`。这构成补丁的同轮次实机验证。

之后在 `date_raw=53619984` 撞到原版事件 `tgp_dynastic_cycle.0081`。该事件的无条件 immediate 块已经破坏或重组领地与 manager 血统；唯一确认按钮无法恢复产品场景，所以 action cell 按合同保留 RED 并停止。Stage 11 为 `NOT_EVALUATED`，不能以动作 ACK 或 Stage 9 证据冒充 terminal。

- RED：`dynastic_cycle_chaos_immediate_shattered_product_lineage`。
- 第二次证据：`terminal-stages-red-attempt-02.json`，`4,404,395` bytes，SHA-256 `6FF528CDF2F179017767D19EC99A357B40DE5701C335EEF3D17995A665AA9207`。
- canonical RED：`terminal-stages-red.json`，内容与第二次证据相同，SHA-256 `6FF528CDF2F179017767D19EC99A357B40DE5701C335EEF3D17995A665AA9207`。
- 部分存档：`terminal-partial-attempt-02.ck3`，`157,176,788` bytes，SHA-256 `D5118BAA82A88C8ADE49D988A487260740E045A617A260512F54C03A4EC71793`；仅用于失败取证，不是合格 Stage 11 来源。

同一 `.390` 帧上的 Stage 10 selector 返回 `status=unavailable`、`unavailable_reason=no_bounded_ai_direct_manager`，且 `selection_attempted=false`。因此 R461 没有生成 `zg361_stage10_player_subject_source_v1` receipt，不能用于独立 Stage 10。

## 清理与后续边界

- canonical cleanup：`09_phase2_native_session_cleanup.json`，`32,917` bytes，SHA-256 `A45A1CF5AB291DDA0077CCDB4EC423560AE9E7C034F37774C75814516C515388`，GREEN。
- managed cleanup：`terminal-stages-managed-cleanup.json`，`34,550` bytes，SHA-256 `ABCD4C93C95990D9090302E80D31196A16878328309857B0C62CB5C4812DB766`，GREEN，`ck3_pids_after=[]`。
- 当前轮次 R461 已结束；旧轮次 R460 已结束；CK3=0，Operator MCP=0。
- 下一次实际启动必须使用新轮次 R462。
- R391/R461 失败血统不得再重跑。下一步只筛已存在的、明确绑定 `.390` 且 selector-positive 的 Stage 10 来源，以及未被 `.0081` 破坏的 Stage 11 来源；若均不存在，再施工新的最短来源捕获路径。
