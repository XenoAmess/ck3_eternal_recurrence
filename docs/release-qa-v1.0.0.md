# Release QA v1.0.0

## Remaining Work / 剩余工作

截至 2026-08-21，以下清单是创建 `v1.0.0` tag 前的权威待办。Steam item
`3784706360` 经公开 API 确认为公开、有效且未封禁；Steam 本身当前不是阻塞项，尚未完成的是
最终候选上传及下载缓存校验。

### Code and CI / 代码与 CI

- [x] 实机确认三个 XAR 决议均归入带琉焰图标的【琉焰卿的永恒轮回】独立分组，三张
  1100×440 DXT1 专属插画在列表与详情页均正确渲染；静态 parity 与
  `xar_decision_group_trait_both_20260821` 实机取证均 GREEN。
- [ ] 修复 clean checkout 的官方 L0：`tools/validate_static.py` 当前无条件读取被
  `.gitignore` 排除的 CK3 原版 `window_succession_event.gui`，导致 GitHub Actions run
  [`32364643040`](https://github.com/XenoAmess/ck3_eternal_recurrence/actions/runs/32364643040)
  在 `Validate generated and static content` 失败。改为从已跟踪投影恢复原版正文、校验
  CK3 1.19.0.6 固定摘要并重新渲染；本机存在原版源时再追加源文件强校验，不提交第二份原版 fixture。
- [x] 修正付费廷臣 trait 图标的信仰上下文：德行、罪恶光效与 tooltip 使用
  `xar_cc_selected_faith`；`xar_decision_group_trait_both_20260821` 证明阿卢克古道【勤勉】为美德、【懒惰】为罪恶，且均不含天主教。
- [ ] 增加铁人模式死亡收尾：普通非铁人单机继续进入观察者；铁人模式必须强制保持暂停，
  通过注册的阻塞窗口打开原生暂停菜单，并走原生保存及退出主菜单确认流程。
- [ ] 为铁人退出窗口新增简中、英文文案，并按发布国际化流程补齐法、德、日、韩、波、俄、西；
  九语言必须通过 key、保护 token、BOM、术语和结构审计。

### Automated Verification / 自动验证

- [x] 通过 Python 编译、no-heir 投影契约单元测试、`validate_static.py`、计分 reference vectors、
  `build_release.py --check` 与 `git diff --check`。
- [ ] 推送修复后确认 GitHub 官方 `windows-latest` 的 validate、计分向量、确定性构建全部 GREEN。
- [x] 重跑 `courtier-creator`：选择阿卢克古道后返回性格页，确认【勤勉】按所选信仰显示为美德，
  且 tooltip 不再引用玩家的天主教信仰。
- [ ] 增加并通过非 debug、非铁人普通继承验收，证明正式环境中的 `observe` 路径真实进入观察者模式。
- [ ] 使用隔离 `userdir`、关闭云存档运行非 debug 铁人验收：验证结算、强制暂停、恢复游戏后重新阻断、
  原生退出确认、铁人存档稳定落盘及返回主菜单；不得触碰真实用户存档。
- [ ] 在最终 mod tree 上串行重跑完整 release-gating CK3 套件与 production projection，保存
  JSON/JUnit、截图、增量日志和 runtime tree hash。

### Manual Sign-off / 人工签核

- [ ] 完成九语言母语级人格、术语及游戏内截断检查；自动结构校验不得代替人工签核。
- [ ] 生成并审阅非 debug 简中干净截图集。
- [ ] 生成并审阅匹配的非 debug 英文干净截图集。
- [ ] 检查廷臣七页、价格栏、九语言最长字符串及支持的 UI 缩放下是否裁切。
- [ ] 确认缩略图在 Workshop 卡片尺寸下可读，并确认标题、首屏核心循环与兼容性说明清晰。

### External Delivery / 外部发布

- [ ] 重新执行 `gh auth login -h github.com`；当前 GitHub CLI token 无效。
- [ ] 人工签核完成后，把 `CHANGELOG.md` 的 `Unreleased` 改为实际发布日期。
- [ ] 在 clean final HEAD 创建并推送 `v1.0.0` tag；此前不得提前打 tag。
- [ ] 运行 `py tools/build_release.py --release`，记录 commit、manifest/ZIP SHA-256 和 83 文件清单。
- [ ] 上传前仅在用户目录外层 `.mod` 恢复 `remote_file_id="3784706360"`，临时把 `path=` 指向
  tagged staging；内层 `descriptor.mod` 继续禁止该字段。
- [ ] 经 PDX Launcher 把同一 staging 更新到既有 Steam item，随后强制重新下载缓存并使用
  versioned manifest 逐文件校验；acceptance runner 同步过的本地缓存不能作为远端发布证据。
- [ ] 创建 GitHub Release，附加同一次 tagged 构建的 ZIP 与 manifest，再恢复外层 `.mod` 的开发路径。

### Explicit Non-gating Backlog / 明确不阻塞 1.0.0

- [ ] delayed `player_heir` carrier 在 `xar.1003` 前死亡时的持久事务 fallback。
- [ ] 无地玩家付费廷臣交付。
- [ ] 付费廷臣配置跨进程保留。
- [ ] 强制交付失败后的无扣金、无存活泄漏角色实机 fixture。
- [ ] 多人同步与多人死亡收尾支持；当前产品仍按单机定位。
- [ ] 30–40 年四夹具完整平衡矩阵；它只属于 soak、稳定性与遥测，不是数值平衡证明。

## Automated Evidence

- Static generated parity, BOM/localization structure, player-only guards, assets and release allowlist: required GREEN.
- Python scoring reference vectors: required GREEN.
- Deterministic double release build: required GREEN.
- GitHub official `windows-latest` runs the L0 checks above and builds uploadable ZIP/manifest artifacts for manual runs or `v*` tags; it does not contain CK3.
- Local CK3 selftest, production smokes, persistence, death edges, with-heir death, bargain timing, progression UI, scoring matrix and paid-courtier scenarios: required GREEN with zero `xar` error lines.
- Landless courtier delivery, process-restart retention and multilingual layout are explicitly uncovered compatibility/presentation cases; they do not downgrade the landed-player functional scenario from GREEN.

Historical local evidence (2026-08-19):

The runs below predate production-code candidate `a19808d`. They remain evidence for the named paths only; they do not validate the paid courtier or the current complete tree.

| Scenario | Run ID | Result |
|---|---|---|
| 57-assertion selftest + expanded shop + scaled Gaze rewards + transaction UI + ledger/contract decisions + AI guard + observer HUD | `xar_accept_t_4fu4zt` | GREEN, 0 `xar` errors |
| Two-process persistence / A writes 405 / B imports 405 without pre-seeding | `xar_accept_ie68yqxu` | GREEN, 0 `xar` errors |
| Actual AI death guard + no-heir native-window settlement + main-menu exit | `xar_accept_fmq_wxxc` | GREEN, eight values visible, 0 `xar` errors |
| Three cumulative production bargains / three exact day-1094 and day-1095 reopen boundaries | `xar_accept_ue4ye_un` | GREEN, nine game years, three ordered production resets, 0 `xar` errors |
| Wise Ruler 3/6/10 milestones / PB lessons / collection / Gaze 10 / ledger pixels | `xar_accept_gqppgi_f` | GREEN, PB 10, collection mask 16, `R 1` / `S 0`, 0 `xar` errors |
| Controlled descendant depth/dedup/dead-intermediate scoring + all 200 production pool dispatchers | `xar_accept_h0lgmvyf` | GREEN, 7 living descendants, depth 6 excluded, 200/200 wire markers, 0 `xar` errors |
| Release projection / first life / zero record | `xar_accept_v6wtivlm` | GREEN, autosaves isolated/restored, 0 `xar` errors |
| Release projection / recorded life / 100 tier, default Growth + 100% | `xar_accept_2sv8bfoi` | GREEN, 0 `xar` errors |
| Release projection / 2000 tier / page-4 Dread + Legitimacy / 1133 reformation | `xar_accept_pq2qn3e6` | GREEN, 0 `xar` errors |
| Release projection / rule disabled | `xar_accept_n_sya3ke` | GREEN, 0 `xar` errors |
| Optimized full selftest regression | `xar_selftest_fast_v4_20260819` | GREEN, 159.411 seconds total; inheritance recovery 2.882 seconds |
| Optimized passive balance smoke / synthetic / two pairs | `xar_balance_synthetic_fast2_20260819` | GREEN, two pairs only; not a 30–40 year balance result |

Release-candidate baseline plus post-review targeted evidence (2026-08-20 through 2026-08-21):

Rows for the full suite retain their original tree fingerprints. Subsequent production changes were confined to the death gates and paid-courtier transaction/GUI paths; those paths were rerun below after review. The then-current 78-file production projection had deterministic L0 evidence, but was not itself put through another complete CK3 suite after every post-review edit. The current branded-decision candidate contains 83 release files and has the targeted runtime evidence below; the final exact-candidate full suite remains pending.

| Scenario | Run ID | Result |
|---|---|---|
| L0 static + scoring vectors + deterministic release projection | local current working tree | GREEN locally, 83 release files; hosted status is tracked separately below |
| Full selftest / 57 assertions / production UI / pool sweep | `xar_selftest_release_candidate_20260820` | GREEN, 57/57, 200-entry sweep, persistence, observer transition, 0 `xar` errors |
| Four production-only smokes | `xar_on_first_life_release_candidate_20260820`; `xar_on_recorded_release_candidate_20260820`; `xar_on_high_budget_release_candidate_20260820`; `xar_off_release_candidate_20260820` | GREEN, stripped staging first/recorded/high-budget/off paths, 0 `xar` errors |
| Two-process persistence restart | `xar_persistence_release_candidate_20260820` | GREEN, process B imported process A tier 445 without pre-seeding, 0 `xar` errors |
| Death edges / AI and no playable heir | `xar_death_edges_postreview_20260820` | GREEN after the shared AI-gate review, AI blocked, eight-value native settlement, main-menu return, 0 `xar` errors |
| Ordinary death with playable heir | `xar_death_with_heir_postreview_20260820` | GREEN after the shared AI-gate review, heir carrier, control transfer, one production score and visible settlement, 0 `xar` errors |
| Three production bargain reopens | `xar_bargain_release_candidate_20260820` | GREEN, each day 1094 blocked/day 1095 opened, cumulative pairs 1/2/3, 0 `xar` errors |
| Contract/Gaze progression UI | `xar_progression_release_candidate_20260820` | GREEN, 3/6/10 PB, collection mask 16, Gaze 10, `R 1` / `S 0`, 0 `xar` errors |
| Controlled scoring and 200 dispatchers | `xar_scoring_matrix_release_candidate_20260820` | GREEN, seven descendants, depth/dedup/dead-intermediate parity, 200/200 branches, 0 `xar` errors |
| Paid custom courtier real UI | `xar_courtier_creator_postreview22_20260820` | GREEN after delivery rollback review, cancel/119-gold/default 120/custom 348/seven tabs/numeric controls/non-default culture and faith/same house/reopen/two delivered courtiers/AI guard, 0 `xar` errors |
| Branded decision group, three illustrations and selected-faith trait context | `xar_decision_group_trait_both_20260821` | GREEN, group icon/title and three list/detail illustrations visible, Aluk Diligent/Lazy identify a virtue/sin and exclude Catholicism, both purchases and AI guard pass, runtime tree `7f9a52e2161a807378448368ebcf0f16a9f625ec2518d5a43f8bbb08127221b5`, 0 `xar` errors |

Current candidate gates:

| Gate | Status | Required evidence |
|---|---|---|
| Local current-tree L0 and deterministic release projection | GREEN | `validate_static.py`, reference vectors and 83-file `build_release.py --check` all pass locally; this is not a hosted or CK3 runtime claim |
| Official GitHub `windows-latest` L0 | BLOCKED | run `32364643040` fails because no-heir parity reads the ignored local CK3 source; clean-checkout projection validation and a new GREEN run are required |
| Full baseline plus post-review targeted CK3 regression | GREEN | the full release-candidate suite passed; changed death paths and paid courtier were then rerun on the reviewed tree with zero `xar` errors |
| Ordinary death with a playable heir | GREEN | `xar_death_with_heir_postreview_20260820`; one compute, dispatch and visible settlement |
| Paid custom courtier | GREEN | `xar_courtier_creator_postreview22_20260820`; both selected origins differ from the player, successful delivery precedes configuration and charge, and remaining landless/process-restart cases are declared coverage gaps |
| Branded XAR decision group and illustrations | GREEN | `xar_decision_group_trait_both_20260821`; OCR proved the native group and three detail pages, while the captured screenshots were manually inspected for the title icon and three distinct illustrations; empty GUI warnings and 0 `xar` errors |
| Selected-faith trait presentation | GREEN | `xar_decision_group_trait_both_20260821`; selected Aluk Diligent/Lazy native tooltips identify the chosen faith's virtue/sin and exclude Catholicism; captured icon borders are manually inspected rather than pixel-classified |
| Ironman terminal flow | OPEN | non-debug isolated-profile proof of forced pause, native save/exit confirmation and main-menu return is required |
| Final exact-candidate CK3 regression | PENDING | rerun the complete release-gating suite after the code and localization changes above |

## Manual Language Sign-off

The structural validator covers all nine languages. Human terminology/persona review remains an external release task and must not be represented as automated approval.

Commit `6e186bb` replaced the then-current seven-language English placeholders. The v2 courtier pass translated 22 active v2 values in each of French, German, Japanese, Korean, Polish, Russian and Spanish with MiniMax-M3 assistance (154 values total), then manually verified exact keys, protected tokens, numeric literals and CK3 1.19.0.6 native terminology; obsolete v1 option labels were removed from all nine languages. The seven new decision-group titles were also translated with MiniMax-M3 assistance, then manually normalized to each language's existing `rule_xar_enabled` brand term while preserving the texticon token. Structural and source-term review is not mother-tongue approval. Simplified Chinese seven-tab rendering is GREEN; the other languages still require in-game clipping review.

| Language | Structural | Human reviewer | Persona/terms | In-game truncation | Status |
|---|---|---|---|---|---|
| Simplified Chinese | GREEN | pending | pending | seven-tab courtier modal GREEN; full pass pending | partial |
| English | GREEN | pending | source reviewed | pending | partial |
| French | GREEN | pending | source/CK3 terms reviewed | pending | partial |
| German | GREEN | pending | source/CK3 terms reviewed | pending | partial |
| Japanese | GREEN | pending | source/CK3 terms reviewed | pending | partial |
| Korean | GREEN | pending | source/CK3 terms reviewed | pending | partial |
| Polish | GREEN | pending | source/CK3 terms reviewed | pending | partial |
| Russian | GREEN | pending | source/CK3 terms reviewed | pending | partial |
| Spanish | GREEN | pending | source/CK3 terms reviewed | pending | partial |

## Manual Presentation Sign-off

- Clean non-debug Simplified Chinese screenshot set: pending.
- Matching clean English screenshot set: pending.
- Thumbnail legibility at Workshop card size: pending.
- No-heir settlement presentation: automated Simplified Chinese proof GREEN; clean non-debug release screenshot remains pending.
- Paid custom-courtier window: all seven tabs, price/available-gold row and longest nine-language strings must be checked for clipping at supported UI scales: pending.
- Steam item `3784706360` upload and downloaded-cache manifest verification: pending.

## Passive Soak / Matrix Telemetry

`balance-long` and the four-fixture passive matrix are non-gating soak, stability and telemetry. GREEN validates fixture setup, cadence, terminal wiring, recovery, sampling and stated error criteria only; it neither certifies numerical balance nor blocks merge or release. Numerical balance requires an explicit strategy, controls and skilled-player evidence.

Known death-carrier edge: normal succession follows the vanilla-style single delayed `player_heir` carrier. If that carrier itself dies before `xar.1003` dispatches, the queued event can be lost; no player-only fallback is currently proven. Initial no-heir deaths and the ordinary living-heir path remain independently GREEN.

## External Delivery

- `v1.0.0` tag, GitHub Release, deterministic release artifact publication and Steam upload: pending.
- Downloaded Workshop cache verification against the release manifest: pending.
- Clean screenshots and thumbnail aesthetic approval: pending.
- Author/source and redistribution permission for all seven derived release assets: recorded from the repository owner in `docs/asset-provenance.md`; no separate public asset license is asserted.
