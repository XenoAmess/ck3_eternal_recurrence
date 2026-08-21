# Release QA v1.0.0

## Release Record / 发布记录

`v1.0.0` 已于 2026-08-21 从 commit `d558fba07cbe80020d03bcaac1994e3327c27624` 正式发布。
Steam item `3784706360` 与 GitHub Release 使用同一 clean-tag 构建；以下保留发布前门禁与外部交付的
权威证据。明确列出的非门禁 backlog 与冻结后独立版工作仍未完成。

### Code and CI / 代码与 CI

- [x] 实机确认三个 XAR 决议均归入带琉焰图标的【琉焰卿的永恒轮回】独立分组，三张
  1100×440 DXT1 专属插画在列表与详情页均正确渲染；静态 parity 与
  `xar_decision_group_trait_both_20260821` 实机取证均 GREEN。
- [x] 修复 clean checkout 的官方 L0：从已跟踪投影恢复原版正文，校验 CK3 1.19.0.6
  canonical text SHA-256 后重新渲染；本机存在原版源时再追加强校验，不提交第二份原版 fixture。
  `tools/test_gen_no_heir_gui.py` 的四项契约测试、模拟无游戏源的完整静态校验均已 GREEN；当前
  85 文件代码提交 `ac524dc` 的官方 run
  [`32425375023`](https://github.com/XenoAmess/ck3_eternal_recurrence/actions/runs/32425375023) 同样 GREEN；其后的证据文档 HEAD
  `45cf7ea` 也由官方 run [`32425512587`](https://github.com/XenoAmess/ck3_eternal_recurrence/actions/runs/32425512587) 验证为 GREEN。
- [x] 修正付费廷臣 trait 图标的信仰上下文：德行、罪恶光效与 tooltip 使用
  `xar_cc_selected_faith`；`xar_decision_group_trait_both_20260821` 证明阿卢克古道【勤勉】为美德、【懒惰】为罪恶，且均不含天主教。
- [x] 增加铁人模式死亡收尾：普通非铁人单机继续进入观察者；铁人模式强制保持暂停，
  通过注册的阻塞窗口打开原生暂停菜单，并走原生保存及退出主菜单确认流程。
- [x] 为铁人退出窗口新增简中、英文文案，并按发布国际化流程补齐法、德、日、韩、波、俄、西；
  九语言已通过 key、保护 token、BOM、源术语和结构审计。母语人格与游戏内截断仍属于下方人工签核。
- [x] 补齐十级【琉焰之视】要求的 `_stars_10.dds`，由 `compose_trait_stars.py` 程序化生成并做逐字节 parity；
  新运行期门禁会捕获不含 `xar` 的 trait-level star texture 错误。

### Automated Verification / 自动验证

- [x] 通过 Python 编译、no-heir 投影与 release manifest 单元测试、`validate_static.py`、计分 reference vectors、
  `build_release.py --check` 与 `git diff --check`。
- [x] 推送修复后确认 GitHub 官方 `windows-latest` 的 projection tests、validate、计分向量、确定性构建全部 GREEN。
- [x] 重跑 `courtier-creator`：选择阿卢克古道后返回性格页，确认【勤勉】按所选信仰显示为美德，
  且 tooltip 不再引用玩家的天主教信仰。
- [x] 增加并通过非 debug、非铁人普通继承验收，证明开发验收夹具中的生产 `observe` 分支真实进入观察者模式。
- [x] 使用隔离 `userdir`、关闭云存档运行非 debug 铁人验收：验证结算、强制暂停、恢复游戏后重新阻断、
  原生退出确认、铁人存档稳定落盘及返回主菜单；不得触碰真实用户存档。
- [x] 在最终 mod tree 上串行重跑完整 release-gating CK3 套件与 production projection；12 个 debug 场景和
  两个非 debug 终局场景全部 GREEN，并保存 JSON/JUnit、截图、增量日志和 runtime tree hash。

### Manual Sign-off / 人工签核

- [x] 仓库所有者确认九语言母语级人格、术语及游戏内截断检查通过；自动结构校验仍不作为该人工结论的替代。
- [x] 仓库所有者确认非 debug 简中干净截图集通过审阅。
- [x] 仓库所有者确认匹配的非 debug 英文干净截图集通过审阅。
- [x] 仓库所有者确认廷臣七页、价格栏、九语言最长字符串及支持的 UI 缩放无阻塞性裁切。
- [x] 仓库所有者确认缩略图在 Workshop 卡片尺寸下可读，标题、首屏核心循环与兼容性说明清晰。

### External Delivery / 外部发布

- [x] GitHub CLI 已重新认证，`gh auth status` 确认 `repo` 与 `workflow` scope 可用。
- [x] 人工签核完成后，把 `CHANGELOG.md` 的 `Unreleased` 改为实际发布日期 `2026-08-21`。
- [x] 在 clean final HEAD `d558fba` 创建并推送 annotated tag `v1.0.0`；master run
  [`32430340954`](https://github.com/XenoAmess/ck3_eternal_recurrence/actions/runs/32430340954) 与 tag run
  [`32430427684`](https://github.com/XenoAmess/ck3_eternal_recurrence/actions/runs/32430427684) 均 GREEN。
- [x] 从独立 clean-tag worktree 运行 `build_release.py --release`，复现 tag workflow artifact：85 文件，
  manifest SHA-256 `6d5ab831aa21978de1531c0381acab7d6aff6c282c1c989a10aaa9f03d4b1408`，
  ZIP SHA-256 `6b243c797f6d7757e8974f51e6d90256f2d443613ea2bbc7bf933917f86e64aa`。
- [x] 上传前仅在用户目录外层 `.mod` 设置 `remote_file_id="3784706360"` 并临时指向 tagged staging；
  上传后已恢复开发路径并保留外层 item ID。canonical staging、仓库与 GitHub ZIP 的内层 descriptor 均无该字段。
- [x] PDX Launcher 日志记录 `Publishing mod started` / `Publishing mod succeeded`；Steam API 返回新
  `hcontent_file=7526310401290648781`、文件大小 5,650,532、最终 BBCode 与公开可见性。将旧缓存整目录移出后，
  Steam 控制台从空路径强制重下载；`--workshop-cache` 仅规范化启动器的 descriptor 换行重写与精确 item ID，
  其余 84 文件和完整文件集合逐字节匹配 versioned manifest。
- [x] GitHub Release [`v1.0.0`](https://github.com/XenoAmess/ck3_eternal_recurrence/releases/tag/v1.0.0)
  已公开，附加同一 tag workflow 的 ZIP 与 manifest，GitHub asset digest 与上述 SHA-256 一致。

### Explicit Non-gating Backlog / 明确不阻塞 1.0.0

- [ ] delayed `player_heir` carrier 在 `xar.1003` 前死亡时的持久事务 fallback。
- [ ] 无地玩家付费廷臣交付。
- [ ] 付费廷臣配置跨进程保留。
- [ ] 强制交付失败后的无扣金、无存活泄漏角色实机 fixture。
- [ ] 多人同步与多人死亡收尾支持；当前产品仍按单机定位。
- [ ] 30–40 年四夹具完整平衡矩阵；它只属于 soak、稳定性与遥测，不是数值平衡证明。

### Post-freeze Parallel Standalone Release / 冻结后并行独立版

- [x] 原 mod 内容已冻结，并在仓库根目录创建同级 `Eternal_Recurrence_Vivhite_Courtier/`，展示名为
  【琉焰卿的永恒轮回：典造琉焰廷臣·白绮特供版】 / **Eternal Recurrence: Glassfire Courtier Creator - Vivhite Edition**。
- [x] 独立版静态生产树不依赖原 mod，只保留【典造琉焰廷臣】功能；轮回、商店、计分、契约、账簿、教程记录等机制全部不带入。
- [x] 独立版使用隔离的 `ervc` 脚本/GUI ID、descriptor、生成器、构建与静态验收；`ervc_acceptance_hardened_final_20260821` 已在非 debug CK3 `1.19.0.6` 串行证明独立加载和双 mod 两种加载顺序，版本单独为 `1.0.0`。
- [x] hardened schema-v2 三格矩阵 JUnit 为 3/3 GREEN、0 blocking project diagnostics。Vivhite production projection 为 `93fb559a61ace1a3c2bd8a9680a0ed5039db765753da8c787d28b0dd67c09fef`；实际 debug mount 顺序逐格匹配请求顺序且 fixture 最后，两种加载顺序均渲染两个独立决议组及直属决议行，保留 ERVC 348/XAR 120 配置，各交付一名廷臣并各扣款一次。双 mod 格仅窄白名单并记录原 mod 冻结代码的两类 loc-only `xa_curse_*_rarity` unused-variable 警告。
- [x] 三个 disposable userdir 与 detached watchdog 均实际退出/删除；CK3 可执行文件前后 SHA-256 保持 `2d00ff3101ef70b566f2fcbae292f09263199c80e9dc8f139b82d7d96f83db86`。真实 profile、Steam cloud 后备目录及 82 个已注册 Workshop target 的 162,960 项元数据在完整扫描后等待五秒并复扫，聚合 SHA-256 保持 `ed9a9cce6db99148f08aac997d38caae00f64c79827fdb1dcf642c3af9c38336`。
- [x] 独立版 pinned L0 通过 17 项 release tests、静态/生成 parity、原 mod 共同门禁及双重确定性构建；未打 tag 的 27 文件候选正确记录 `git_tag: null` / `workshop_item_id: null`，manifest SHA-256 为 `2f7aecd2621dc10cf81df6fcf14b82b74f2e645bf3f37c72c3ccca502123a87a`，ZIP SHA-256 为 `9ad24ad26521e721c417462296134f2f794d3187cd72cfa316a5fa250828ce5e`。
- [ ] 独立版首次上传必须创建新的 Steam Workshop item；不得复用原 mod 的 `3784706360`，新 ID 只保存在该 mod 的用户目录外层 `.mod`。

## Automated Evidence

- Static generated parity, BOM/localization structure, player-only guards, assets and release allowlist: required GREEN.
- Python scoring reference vectors: required GREEN.
- Deterministic double release build: required GREEN.
- GitHub official `windows-latest` runs the L0 checks above and builds uploadable ZIP/manifest artifacts for manual runs or `v*` tags; it does not contain CK3.
- Local CK3 selftest, production smokes, persistence, death edges, with-heir death, bargain timing, progression UI, scoring matrix and paid-courtier scenarios: required GREEN with zero project error lines.
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

Rows for the older full suite retain their original tree fingerprints. Subsequent production changes were confined to the death gates and paid-courtier transaction/GUI paths; those paths were rerun below after review. The then-current 78-file production projection had deterministic L0 evidence, but was not itself put through another complete CK3 suite after every post-review edit. The Ironman-terminal and ten-star candidate contains 85 release files; its targeted evidence appears below, followed by the final exact-candidate suite.

| Scenario | Run ID | Result |
|---|---|---|
| L0 static + scoring vectors + deterministic release projection | local current working tree | GREEN locally, 85 release files; hosted status is tracked separately below |
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
| Non-debug ordinary terminal / native observer HUD | `xar_terminal_observer_nondebug3_20260821` | GREEN in the development fixture, production `observe` branch visible, ten-level trait track rendered, protected Documents files and local Steam userdata unchanged for the bounded postflight, disposable userdir actually removed, runtime tree `235d92fb36fd1052b0261c05f059e525d76a06231a7b92a8a27cc8e6764d242a`, 0 project errors |
| Non-debug Ironman terminal / native save, exit and reload | `xar_terminal_ironman_nondebug9_20260821` | GREEN in the development fixture, 57/57, ten-level trait track rendered without the prior 248 star-texture errors, three mandatory readable frozen-date checks, resume reblocked, native Ironman save confirmation, main-menu return and same-process save reload reblocked; nine protected Documents files and two local Steam userdata files for app 1158310 retained identical aggregate hashes through a five-second postflight, disposable userdir actually removed, runtime tree `235d92fb36fd1052b0261c05f059e525d76a06231a7b92a8a27cc8e6764d242a`, harness `f56a0e364198e6fe1be465d447d1f5170965de275e6a28e4d443ca68934e7b9f`, 0 project errors |

Final exact-candidate evidence (2026-08-21):

Every report below records Git commit `45cf7eacb276610ed3ed62bb933e0cc1936c51c8`, CK3 `1.19.0.6`, JSON/JUnit,
screenshots and incremental logs. Development scenarios loaded runtime tree
`235d92fb36fd1052b0261c05f059e525d76a06231a7b92a8a27cc8e6764d242a`; the four production smokes built and loaded
the stripped 85-file projection `29dde4460b7f86b1779e902712e856776dd99de703802a92a64c1fa39c28d221` from that same source tree.

| Scenario | Run ID | Result |
|---|---|---|
| Four production-only smokes | `xar_final85_on_first_life_20260821`; `xar_final85_on_recorded_20260821`; `xar_final85_on_high_budget_20260821`; `xar_final85_off_20260821` | GREEN, first-life/100-record/2000-budget/rule-disabled paths, 0 project errors |
| Full selftest / 57 assertions / production UI / pool sweep | `xar_final85_selftest_20260821` | GREEN, 57/57, 200-entry sweep, native decision UI, trait hover and observer transition, 0 project errors |
| Two-process persistence restart | `xar_final85_persistence_20260821` | GREEN, process B imported process A record 455 without pre-seeding; handoff and pre-exit SHA-256 both `81d8f07d2ee90ba553ebcb3b63954a89b5a31f4b884cb314b2acadea67915ae7`, 0 project errors |
| Actual AI death and no playable heir | `xar_final85_death_edges_20260821` | GREEN, actual AI death blocked, synchronous eight-value settlement visible, native exit returned to main menu, 0 project errors |
| Ordinary death with playable heir | `xar_final85_death_with_heir_20260821` | GREEN, player precondition, heir control transfer, one production score and visible settlement, 0 project errors |
| Three production bargain reopens | `xar_final85_bargain_20260821` | GREEN, every pair blocked on day 1094 and reopened on day 1095; cumulative pairs and XP reached 1/2/3, 0 project errors |
| Contract/Gaze progression UI | `xar_final85_progression_20260821` | GREEN, 3/6/10 PB lessons, collection mask 16, Gaze 10 and ledger `R 1` / `S 0`, 0 project errors |
| Controlled scoring and production dispatchers | `xar_final85_scoring_matrix_20260821` | GREEN, seven living descendants through depth 5 with dedup/dead-intermediate coverage, preview parity and 200/200 dispatchers, 0 project errors |
| Paid custom courtier real UI | `xar_final85_courtier_creator_20260821` | GREEN, cancel/119-gold gate/default 120/custom 348/seven tabs/numeric controls/Aluk faith context/two purchases/AI guard, 0 project errors |

Current candidate gates:

| Gate | Status | Required evidence |
|---|---|---|
| Local current-tree L0 and deterministic release projection | GREEN | compileall, four projection tests, six release-manifest tests, `validate_static.py`, reference vectors and 85-file `build_release.py --check` all pass locally; this is not a hosted or CK3 runtime claim |
| Official GitHub `windows-latest` L0 | GREEN | code commit `ac524dc`, run [`32425375023`](https://github.com/XenoAmess/ck3_eternal_recurrence/actions/runs/32425375023), and evidence HEAD `45cf7ea`, run [`32425512587`](https://github.com/XenoAmess/ck3_eternal_recurrence/actions/runs/32425512587); clean checkout passed compile, four projection tests, static validation, scoring vectors and deterministic 85-file build |
| Full baseline plus post-review targeted CK3 regression | GREEN | the full release-candidate suite passed; changed death paths and paid courtier were then rerun on the reviewed tree with zero `xar` errors |
| Ordinary death with a playable heir | GREEN | `xar_death_with_heir_postreview_20260820`; one compute, dispatch and visible settlement |
| Paid custom courtier | GREEN | `xar_courtier_creator_postreview22_20260820`; both selected origins differ from the player, successful delivery precedes configuration and charge, and remaining landless/process-restart cases are declared coverage gaps |
| Branded XAR decision group and illustrations | GREEN | `xar_decision_group_trait_both_20260821`; OCR proved the native group and three detail pages, while the captured screenshots were manually inspected for the title icon and three distinct illustrations; empty GUI warnings and 0 `xar` errors |
| Selected-faith trait presentation | GREEN | `xar_decision_group_trait_both_20260821`; selected Aluk Diligent/Lazy native tooltips identify the chosen faith's virtue/sin and exclude Catholicism; captured icon borders are manually inspected rather than pixel-classified |
| Ordinary and Ironman terminal flows | GREEN | `xar_terminal_observer_nondebug3_20260821` and `xar_terminal_ironman_nondebug9_20260821`; non-debug development fixtures proved ten-level trait rendering with zero project errors, native observer, forced pause, resume reblock, native save/exit, main-menu return, same-process reload reblock and bounded local-storage isolation |
| Final exact-candidate CK3 regression | GREEN | commit `45cf7ea`; 12 debug reports plus the source-hash-matched observer/Ironman non-debug reports cover the complete release-gating suite, with runtime hashes recorded above and 0 project errors |

## Manual Language Sign-off

The structural validator covers all nine languages. Repository-owner confirmation on 2026-08-21 separately closed the human terminology, persona and in-game truncation gate; that approval is not inferred from automation.

Commit `6e186bb` replaced the then-current seven-language English placeholders. The v2 courtier pass translated 22 active v2 values in each of French, German, Japanese, Korean, Polish, Russian and Spanish with MiniMax-M3 assistance (154 values total), then manually verified exact keys, protected tokens, numeric literals and CK3 1.19.0.6 native terminology; obsolete v1 option labels were removed from all nine languages. The seven new decision-group titles were also translated with MiniMax-M3 assistance, then manually normalized to each language's existing `rule_xar_enabled` brand term while preserving the texticon token. Structural and source-term review alone is not mother-tongue approval; the repository owner separately confirmed the release-level human and in-game review on 2026-08-21.

| Language | Structural | Human reviewer | Persona/terms | In-game truncation | Status |
|---|---|---|---|---|---|
| Simplified Chinese | GREEN | repository owner | GREEN | GREEN | approved |
| English | GREEN | repository owner | GREEN | GREEN | approved |
| French | GREEN | repository owner | GREEN | GREEN | approved |
| German | GREEN | repository owner | GREEN | GREEN | approved |
| Japanese | GREEN | repository owner | GREEN | GREEN | approved |
| Korean | GREEN | repository owner | GREEN | GREEN | approved |
| Polish | GREEN | repository owner | GREEN | GREEN | approved |
| Russian | GREEN | repository owner | GREEN | GREEN | approved |
| Spanish | GREEN | repository owner | GREEN | GREEN | approved |

## Manual Presentation Sign-off

- Clean non-debug Simplified Chinese screenshot set: approved by repository owner on 2026-08-21.
- Matching clean English screenshot set: approved by repository owner on 2026-08-21.
- Thumbnail legibility at Workshop card size: approved by repository owner on 2026-08-21.
- No-heir settlement presentation: automated Simplified Chinese proof GREEN; clean non-debug release screenshot approved by repository owner.
- Paid custom-courtier window: seven tabs, price/available-gold row, longest nine-language strings and supported UI scales approved by repository owner.
- Steam item `3784706360` upload and clean downloaded-cache manifest verification: completed on 2026-08-21.

## Passive Soak / Matrix Telemetry

`balance-long` and the four-fixture passive matrix are non-gating soak, stability and telemetry. GREEN validates fixture setup, cadence, terminal wiring, recovery, sampling and stated error criteria only; it neither certifies numerical balance nor blocks merge or release. Numerical balance requires an explicit strategy, controls and skilled-player evidence.

Known death-carrier edge: normal succession follows the vanilla-style single delayed `player_heir` carrier. If that carrier itself dies before `xar.1003` dispatches, the queued event can be lost; no player-only fallback is currently proven. Initial no-heir deaths and the ordinary living-heir path remain independently GREEN.

## External Delivery

- `v1.0.0` tag, GitHub Release, deterministic release artifact publication and Steam upload: completed on 2026-08-21.
- Downloaded Workshop cache verification against the release manifest: GREEN for all 85 files after strict launcher descriptor normalization.
- Clean screenshots, multilingual layout and thumbnail aesthetic approval: completed by repository owner on 2026-08-21.
- Author/source and redistribution permission for all seven derived release assets: recorded from the repository owner in `docs/asset-provenance.md`; no separate public asset license is asserted.
