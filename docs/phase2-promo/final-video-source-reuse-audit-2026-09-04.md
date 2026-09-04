# 天朝二期双片素材复用审计与八段触发条件（2026-09-04）

本次审计只做非 CK3、只读的素材盘点与录制前准备。未启动 CK3，未运行录制器、TTS 或 FFmpeg，未生成占位媒体，也未把 RED、fixture、debug、Frontend 或 paused-map 画面登记成宣传素材。

## 结论

- 当前可进入两版 builder 的真实二期 source span 为 **`0/8`**；人物版与制度群像版目标 MP4 均为 **`0/2`**。
- 当前没有任何已有视频片段可以诚实复用为八段之一。可复用的是 authoring、动作编排、review 模板、canonical seed 与 focused live 业务证据；它们都是后续录制输入或校验依据，不是可剪辑画面。
- 不生成 `zg361_phase2_canonical_source_checkpoint_registry`。现有 artifact 没有同一真实 lineage 下的四份必需 checkpoint receipt，强行生成只会制造假 registry。
- B3 业务链 GREEN 后仍需新录全部八段；八段可以由同一份通过 intake 的原始录屏供两版剪辑共用，但两版的旁白、字幕、候选、两轮 1.0× 真人审片、sign-off、导出和发布回执必须独立完成。

## 已核对的现有来源

| 来源 | 可继续复用的内容 | 不能复用为 source clip 的原因 |
|---|---|---|
| `Z:\ck3_mod_rewrite_process_assets\zg361\phase2-b2-r22-20260904-123400\focused-live` | B2 same-checkpoint 业务验收和后续动作编排依据；outer report 为 `GREEN`、`gameplay_green_claimed=true`、`phase2_b2_same_checkpoint_complete=true` | outer report 明确为 `phase2_promo_capture=false`、`phase2_promo_capture_complete=false`；没有 `cell/promo/capture-timeline.json`，没有 MP4，不能登记成 `phase2_receipt_appeal_pip` 画面 |
| `Z:\ck3_mod_rewrite_process_assets\zg361\b3j-ff-1817` | 证明短路径已到达 Frontend → autosave → paused map，可用于定位下一次 runner 入口 | outer/cell 为 RED，停在业务前 capability gate；没有八段业务动作、postcondition、timeline 或媒体。`cac1e85` 只修复 candidate-only capability advertisement，默认仍为 OFF，尚无 fresh binary/live 结果 |
| `Z:\ck3_mod_rewrite_process_assets\zg361\promo\captures\*\cell\promo\capture-timeline.json` | 历史录制流程与取景经验 | 对全部历史 timeline 的只读搜索得到当前八个 span ID 命中数 `0`，当前 capture mode/contract 字段命中数 `0`。最新的 2026-08-30 clean take 记录的是一期 `policy_card_*` 等标记，不是二期八段，不能跨期冒充 |
| r9 canonical paused seed 及其后续有效 checkpoint | 通过当前冻结合同复核后，可作为新录制的启动输入 | seed/save 是输入，不含八段 clean begin/end、原始录屏或业务 postcondition，不能计入 footage |
| 两版 project JSON、导演稿、claims ledger、review plan/template | 两版剪辑与审片可以在 8/8 intake 后直接使用 | 两个 project 各 10 章目前全部为 `planned`，所有 `artifact_ids` 为空；模板不等于已经审片 |
| 宣传工具 `Z:\workspace\xar_promo_toolchain` | 后续素材到齐后的 source review、builder、审计和导出工具 | 本次只读核验为 clean，`HEAD == origin/main == 57c42fca13ea459432c1caf76e069a1fbccf602c`，`describe=v0.2.1-1-g57c42fc`；工具 ready 不等于 footage ready，正式制作前仍按总合同做 fresh-update 复核 |

## 八段精确缺口与开拍触发条件

所有条目当前均为 `NEW_RECORDING_REQUIRED`，因此总数保持 `0/8`。每段只有在真实 product surface、动作后的原生 provider 状态和 clean frame 边界同时成立时才可记为 `1/8`。

| 顺序 | Canonical span | 当前缺口 | 可以开始该段 clean hold 的触发条件 | 必须在结束前证明的业务结果 |
|---:|---|---|---|---|
| 1 | `phase2_fact_quota_calibration` | 无当前二期 timeline/raw clip | `run_phase2_scoreboard_gameplay_action_cell` 已在真实 product-only 会话就绪；`zg361_scoreboard_modal` 或 `zg361b1.200/.201`、`zg361.1` 对应 surface identity-ready；scoreboard 与 current-event 两个 query 可读 | 执行真实 `select-event-option-N` 后，scoreboard/query revision 发生变化，并保留可读的校准事件身份；schema、ACK 或旧一期 calibration 画面均不能替代 |
| 2 | `phase2_receipt_appeal_pip` | r22 有业务 GREEN，但没有录屏/timeline | `run_phase2_b2_pip_gameplay_action_cell` 到达真实 `zg361b2.40`/`zg361.4` surface；B2 PIP snapshot 与 current-event query 都对同一案卷 identity-ready | 真实 option 动作后，provider 观察到相同 owner/subject/cycle/case 到达所选 response state；r22 只可指导复现，仍须新录 clean span |
| 3 | `phase2_manager_governance` | B3 最后 live artifact 在业务前 RED | `run_phase2_ai_owned_case_gameplay_action_cell` 可进入真实 `zg361mg.120`；AI-owned-case snapshot 与 current-event query 可读；speed/resume/pause 动作可用 | AI-owned case 到达 provider-observed terminal business state；经过时间或命令 ACK 不能代替终态 |
| 4 | `phase2_promotion_compensation` | 只有静态/candidate 接线，没有 fresh live postcondition，也没有真实 source checkpoint | 同一 lineage 的 `capture_promotion_compensation` registry entry 已由真实 `zg361pp.147` checkpoint receipt 生成；current-event 与 promotion-compensation postcondition query 均由 fresh exact binary 宣告并实读；`.147/.150` 与 `zg361comp.1` 可见 | 晋升选择和薪酬回执绑定同一 frozen case。`cac1e85` 的默认关闭 capability 不能单独开门 |
| 5 | `phase2_hc_workforce` | 无 A/B/C clean branch 录屏 | `run_phase2_workforce_m360_gameplay_action_cell` 到达真实 `zg361we.360/.361`；Workforce snapshot/current-event query、save/restore 与 option 动作可用 | A/B/C 三支来自 hash-identical checkpoint，并证明相同 owner/subject case；no-opening 结果也必须可见。三支不是一条自然连续时间线 |
| 6 | `phase2_projects_metrics` | 只有 no-launch/provider 研究，无可用 live checkpoint 或 clip | 同一 lineage 的 `capture_projects_metrics` registry entry 已由真实 `zg361cp.26` checkpoint receipt 生成；`.26/.31` 与 `zg361p3.229` product events identity-ready；loaded-feature manifest/current-event query 可读 | 真实 option 后，项目选择与 contribution/metrics 结果在 identity-ready product events 中可见；静态 handler 或 ACK 不能推断结果 |
| 7 | `phase2_incidents_operations` | 无严格 incident source receipt，无 X/Y/Z 连续画面 | 同一 lineage 的 `capture_incidents_operations` registry entry 从真实 `zg361.50` source checkpoint 产生，并附 strict incident receipt；owner 与 player 不同、played subject 绑定成立；incident snapshot/current-event query 可读 | `zg361ip.190 → .290 → .390` 三个 surface 依序可见，每个 transition 与 closure 都由动作后的 provider state 观察，不能由 ACK、音效或闪切补全 |
| 8 | `phase2_cross_cycle_endgame` | 无第三周期/终局同 lineage 实录 | 同一 lineage 的 `capture_cross_cycle_endgame` registry entry 从真实 `zg361we.356` checkpoint 产生；`run_exact_build_cross_cycle_endgame_seam` 的 event、Workforce、loaded-feature queries 与 typed owner-subject transition 全部可用 | same-lineage played-subject Workforce provider 证明 route C、carried debt/default cycle，以及 owner-visible `.361` 之后的 M361 charter；不得把早先镜头剪成跨周期因果 |

其中 source checkpoint registry 的固定覆盖顺序只有四项：`capture_promotion_compensation`、`capture_projects_metrics`、`capture_incidents_operations`、`capture_cross_cycle_endgame`。当前外部 artifact 树中未发现可接受的 registry 文件；Incident 还必须有 strict receipt，所以本轮保持 registry pending 是正确结果。

## 全局 intake 开门条件

逐段条件全部满足仍不等于素材已入库。一次可供两版共用的 source bundle 还必须同时满足：

1. `report.json`、`cell/promo/capture-timeline.json`、`evidence-index.json`、`cell/04_phase2_seed_loaded.json` 四项齐全、互相索引且哈希绑定；outer/cell 为 GREEN，`gameplay_green_claimed=true`，Phase2 capture complete。
2. timeline 为 schema 2，`capture_mode=zhongguo-361-phase2`、`capture_contract_version=1`、`clean_capture_complete=true`、`missing_clean_spans=[]`、`exclude_ck3_loading=true`。
3. 非空 raw recording 由 evidence index 哈希绑定；八段严格按 canonical 顺序各有 clean begin/end 与 GREEN gate，且每段 `visible_surface=true`、`postcondition_green=true` 并带原生 postcondition evidence。
4. 全部 session 使用同一 canonical seed/save lineage、exact source commit/tree、CK3 `1.19.0.6` 与 exact EXE SHA，录制运行只挂产品 mod；fixture、prior-phase footage、debug、Launcher、loading UI 均排除。
5. multi-session 仅可通过 managed receipt 和同一 lineage 拼接；跨周期段必须保留受控 transition，不得靠剪辑伪造。
6. `zhongguo_phase2_footage_intake.py` 对该 bundle 返回 GREEN 后，才把八段 artifact ID 写入两个 project；之后两版分别进入 source review、TTS/build、claims audit、两轮 1.0× 真人审片、sign-off 与 export。

## B3 GREEN 后的最短执行顺序

1. 冻结 exact source commit、product tree、bridge pair 与当前有效 seed；先让 B3 capability/query/action 预检在 fresh binary/live 上 GREEN。
2. 在真实会话按固定顺序产出四份 source checkpoint receipts 并生成完整 registry；先满足 promotion、projects、incident、cross-cycle 的恢复点。
3. 用唯一的 `--phase2-promo-capture` 会话入口按上述 1→8 顺序录制；失败 take 原样保留，换新 attempt，不覆盖、不登记为 footage。
4. 立即运行只读 footage intake。只有 8/8 GREEN 才更新 source registry/status 和两版 project artifact binding。
5. 基于同一份 8/8 source bundle 并行制作人物版与制度群像版，分别完成全部审片与导出；在此之前状态继续是 `footage 0/8 / MP4 0/2`。
