# R304–R313 projects/metrics source checkpoint 实机捕获（2026-09-08）

## 结论

R313 已在 CK3 1.19.0.6 的真实暂停现场完成 `capture_projects_metrics` schema-2 source checkpoint，结果为 `GREEN / captured-real-checkpoint`。捕获器在 owner `32904` 仍为当前玩家时，通过 explicit-subject MCP 读取 subject `30938` 的 CP26 source state；随后使用 native 通用换人命令把当前玩家切到 subject，并在同一 date、PID 与 connection generation 下执行原生保存。全程 `mcp_only=true`，未使用 fixture、控制台、OCR 或坐标。

canonical source registry 因此从 `1/4` 推进到 `2/4`：已捕获 `capture_promotion_compensation` 与 `capture_projects_metrics`，仍缺 `capture_incidents_operations` 和 `capture_cross_cycle_endgame`。这个增量只关闭 source evidence，不新增 strict business scene、full-tree definition 或 stage，也不产生宣传视频素材；T0-P2 继续 `LOCKED`。

## 冻结输入与 exact-build 身份

- CK3：`1.19.0.6`；EXE SHA-256 `2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86`。
- exact R296 product projection：`Z:\p2p296tooltip\phase2-product-projection.json`，`1,031` files，逐文件验证通过；manifest SHA-256 `292A52CA74B7176D076A63B0D86459C177188BD33838058B79FC15B9399E3A80`。
- exact R296 product/source tree SHA-256：`FBC162A55130CB7F8B6BAFBE443DA9A06589B475B5C225FA9C2BE3C2DBCEF80B`。
- R296 capture lineage SHA-256：`9A3643E6BBF8491FADE90582BC0DD7CC6CCDD10F0E3F04D45D0F93137AAB517D`。
- R296 CP26 UI receipt SHA-256：`BEEC1282DAE0F8F417D9B63B263F366B55C8F8DFBD251DE0257856CAE93D7462`；它绑定 Route A、owner `32904`、subject `30938`、date raw `53246712`。
- source checkpoint：`Z:\ck3_mod_rewrite\_runtime\p2r301cp26cursor_state\profile\save games\xar_checkpoint.ck3`，`89,563,632` bytes，SHA-256 `7584F32E1D3556A7740FE1E11FA5AF67706A47C99A25E52E1E69213673D15870`。
- R304–R312 使用的 native bridge：`2,447,872` bytes，SHA-256 `A35B29CF83F5658A0AF5066CED742D676FFBA39398260BFA7206C72B553AE49B`。
- R313 使用包含 optional-identifier 最小修复的 native bridge：`2,447,872` bytes，SHA-256 `D45CD041097069BBFD5A88BCAAE1F14CA57511F164966376040574928C544B00`。

R304–R313 每次均从上述 source checkpoint 克隆隔离状态、挂载同一 exact R296 product，并在结束后重新核对原 source checkpoint 的大小和 SHA-256；原证据未被覆盖。

## R304–R312 RED 谱系

| Run | 分类 | 实机结果与收敛结论 | report SHA-256 |
| --- | --- | --- | --- |
| R304 | provider semantic RED | 先从 owner 换到 subject 再查询，provider 返回 `unavailable / variable_context_unavailable`；证明这一顺序不能形成 source capture。 | `4263A813484B4F7FFF61969337689BE23F696017E61F9E9F4634890F43272165` |
| R305 | provider semantic RED | 保持 owner 为当前玩家，以 explicit subject 查询仍返回同一 unavailable；排除了“必须先换人”这一解释。 | `4050D327A1ADB9B494C09D4BDF5589E1601557F42A74C1039B023E9E4CA20891` |
| R306 | harness/unit RED | naive hydration 从 raw `53246712` 前进到 `53246736`，但 runner 把 raw delta `24` 错当 24 天；同时撞到 event instance `314`，被 bounded event-free gate 拒绝。 | `5FCB56439A4F85D6ACD35C440D04CBFD35B8EFF8AEA49E279E393D2E87ED3FFC` |
| R307 | harness/unit RED | exact-one-day native composite 已得到 event-free paused frame，但 runner 仍把 raw `24` 判成 24 天；这确认 CK3 `date_raw` 的 `24` 单位才是 1 天。 | `CB8114C06F714B35ACF85023E40440B0260F9E7475E597405375A8E21EF24A48` |
| R308 | provider semantic RED | 修正单位后，D+1 hydration 为 `GREEN`，provider 仍返回 `variable_context_unavailable`；单纯推进一天不解决问题。 | `02E91B72C45279149DB45027BCC8727F7D7A8466B7561C743E92FB20E2A74D14` |
| R309 | harness timing RED | 为读取下一 product event 而 resume，但未在 bounded frame 停稳，报 `post-CP26 event did not stop on the bounded frame`。 | `D975615D6184FA783098CE247BD6B44B57F58DBD65441FE33D839FE961A8C4AD` |
| R310 | harness timing RED | 增加 pause 后仍在稳定 snapshot 之前读取，同样未停稳；没有形成可用业务结论。 | `8BD1AFB315E76ED10FC4EDFF193C07C0A275713A1A54D2C606A3C99E89AE380C` |
| R311 | provider semantic RED | 已稳定识别真实 `zg361cp.31`（event instance `315`），经 exact current-event MCP 选择 option 1，回到 date raw `53246760` 的 event-free paused frame；provider 仍返回 `variable_context_unavailable`。这排除了“尚未 materialize/需要更多时间”的主假设。 | `55BC49A932DFEF00CF9F0A95E29ABCC35BD1ACD0CB35FECCA601A2AD8C23BD3D` |
| R312 | harness timing RED | bounded 多事件 runner 在下一事件出现时观察到 `paused=false`、event instance `314`、elapsed raw `24`，按精确事件门禁拒绝继续选择；该次是 harness RED，不改变 R311 的 provider 诊断。 | `F4E2A3DBC502DB087BD57845F1BE5DB7E73EF9887353B677CF259A7EA531ECAC` |

所有九个 RED 均保留为失败证据；每次 cleanup 都是 `GREEN`、failed checks 为空，并且 original source checkpoint unchanged 为 `true`。

## R311 根因与 R313 最小修复

R311 的决定性证据是：真实 `.31` 已被稳定识别和处理，现场又推进了两天，provider 仍把整个查询降级成 `variable_context_unavailable`。R313 换入修复后的 bridge 后，在最初 CP26 paused owner frame、date raw `53246712`、elapsed `0` 天即返回 `available / cp26_ready_p3_absent`，没有推进时间，也没有选择任何 materialization event。前后只改变 native reader，因此根因定位为 provider 的 identifier 读取语义，而非 CK3 状态尚未 materialize。

具体缺陷是 `zg361_cp_pending_player_event` 在这个 CP26 source frame 合法地尚未创建，但旧 reader 把“该标识符不存在”与“identifier table/context 真正不可用”统一返回为失败，继而错误地把整个 allowlist 查询报告成 `variable_context_unavailable`。

R313 的修复范围保持最小：

- `ResolveVariableIdentifier` 与 native row reader 区分 `resolved`、`identifier_absent`、`unavailable`。
- 仅允许 `cp_pending_player_event` 的 `identifier_absent` 投影为 typed unavailable：`status=unavailable`、`unavailable_reason=variable_absent`、`value=null`。
- 其他所有 allowlisted identifier 仍是必需项；任一缺失继续 fail closed 为 `variable_context_unavailable`。
- 回归夹具覆盖“只有 pending cursor 可缺失”以及“其余任一标识符缺失均失败”，没有放宽整张 provider 合同。

## R313 真实捕获

### Provider source state

- source event：`zg361cp.26`；Route A；date raw `53246712`；capture delay `0` 天。
- owner / subject：`32904 / 30938`；source identity `[owner=32904, subject=30938, cycle=4, case=2]`。
- contribution：receipt id `1`、revision `3`、value `1`。
- portfolio：`provider_observed=true`、`closed=0`；P3 result identity 与 metrics result 均未建立，`p3_initializer_not_run=true`。
- pending player event：`unavailable / variable_absent`，按本 source checkpoint 合同解释为尚无 durable pending cursor，而不是 provider context 故障。
- provider checkpoint state：`cp26_ready_p3_absent`。完整 provider 的 terminal `readiness.ready=false` 是预期值，因为这是 P3 前的 source frame；source capture 只要求 owner/source identity、CP26 contribution 与同帧绑定真实可读。
- 初次 provider probe 即可用：elapsed `0` 天，materialization event keys 为空。没有 blind native composite，也没有把 action ACK 当作业务后置条件。

### Native 换人、保存与绑定

source binding 为 PID `199252`、generation `1`、date raw `53246712`、player `32904`、paused、无 active event。native `set-played-character-v1-30938` 返回 `status=switched`、`postcondition_verified=true`、`episode_rebind_performed=true`；换人后的 checkpoint binding 仍是 PID `199252`、generation `1`、date raw `53246712`，player 变为 `30938`。因此 `generic_character_rebind_used=true` 是有独立 receipt 的真实 MCP 换人，不是外部控制台或夹具伪造。

换人后通过 native save 冻结 checkpoint；post-save snapshot 继续保持同一 PID、generation、date、player、paused 与 event-free 状态，仅 revision/native revision 单调前进。

### Artifact 与哈希

以下哈希均已对实际文件重新计算，并与 report/registry 内声明逐项一致：

- R313 report：`Z:\ck3_mod_rewrite\_runtime\p2r313projectssource\report.json`，`172,945` bytes，SHA-256 `9225D94ABCA8E47AFF0D2CBB3BE51785E28F5C0781F412F4B1D917B13046E76F`。
- schema-2 source registry：`projects-metrics-source-registry.json`，`59,899` bytes，SHA-256 `7F80326DA8B0EBBBCEE26DE21E2A55A6F74AAE989D567F9B8909BD1F7B3190DE`。
- cumulative `2/4` artifact：`phase2-source-capture-two-of-four.json`，`142,334` bytes，SHA-256 `8128750541EE7683EAB5CAD83CFDAF11FCCE47F8017019E3B5541A76F1AD603A`。
- frozen checkpoint：`frozen-checkpoint/01-phase2_projects_metrics-72fb7d0f04c8b584.ck3`，`89,548,228` bytes，SHA-256 `72FB7D0F04C8B584555C35AC87313A5581FA8610344F72ABA4758904BC4C433B`。
- provider receipt：`frozen-checkpoint/01-phase2_projects_metrics-72fb7d0f04c8b584.provider-receipt.json`，`8,191` bytes，SHA-256 `3F98E84388EEC8918DCE4ACBC72F0013143588A5E244844F53A14581A9670F0A`。
- player-switch receipt：`frozen-checkpoint/01-phase2_projects_metrics-72fb7d0f04c8b584.player-switch-receipt.json`，`1,922` bytes，SHA-256 `3868C67B100080051B528B3061F77677C568CB675088E383C71F5655251672E3`。
- archived UI receipt：`frozen-checkpoint/01-phase2_projects_metrics-72fb7d0f04c8b584.ui-receipt.json`，`29,274` bytes，SHA-256 `BEEC1282DAE0F8F417D9B63B263F366B55C8F8DFBD251DE0257856CAE93D7462`。

cumulative artifact 同时逐字节引用 promotion source artifact `Z:\ck3_mod_rewrite\_runtime\p2r294bresume3\04_promotion_source_checkpoint_capture_v2.json`，SHA-256 `75CB49FD38FAD0D28923D08452FD73B1CF7CCDB049066B528B46FC6B86E63AC8`。它明确标记 `canonical_registry_ready=false` 与 `incomplete_for_canonical_4_entry_registry=true`，没有把 `2/4` 冒充最终 registry。

## 清理与进度边界

R313 cleanup 为 `GREEN`，failed checks 为空；唯一 PID lineage 为 `199252`、connection generation lineage 为 `[1]`，原 source checkpoint 在收尾复核中仍为 `89,563,632` bytes / `7584F32E1D3556A7740FE1E11FA5AF67706A47C99A25E52E1E69213673D15870`，`original_source_checkpoint_unchanged=true`。

本轮只把 source evidence 从 `1/4` 推进到 `2/4`，所以既有项目口径保持不变：T0 `50%`、strict scene `4/361`、full-tree definition `106/626`、stage `8/11`、宣传 footage `0/8`、MP4 `0/2`。T1 仍为 `90%`，T2 current horizon 仍为 `100%`，总体仍为 `67.5%`；T0-P2 继续 `LOCKED`，最终宣传视频尚未开始。

下一工作包按 canonical 顺序进入 `capture_incidents_operations`：先复用当前 schema-2 registry/assembler 合同与 native MCP 换人链建立 no-launch readiness，再串行取得真实 paused incidents/operations source frame，使 source registry 从 `2/4` 推进到 `3/4`。

本工作包的实现、合同、测试与报告已由 commit `4eec135540f51ed2f51879a8aa49a0ae3bcf789f` 普通 fast-forward push 到 `origin/master`；同步流程仅使用 fetch/rebase，没有 merge 或 force-push。
