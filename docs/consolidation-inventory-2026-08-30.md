# Master consolidation inventory — 2026-08-30

状态：**能力与文档已收口到 `22553a8`，官方 push/dispatch GREEN；历史 branch refs 已按保全合同退休，待本清理账本提交的 exact CI GREEN**

本清单以 consolidation 起始 `origin/master = 986d7281240334190e109f879eaa2f38877af489` 为基线，目标是把仍有效、且未被
master 等价或更优实现覆盖的能力和 mod 收口到同一个 master。第一轮 consolidation GREEN 基线为
`fa8893923731ae82bb9087dfb868b10bfc20e900`；branch-retirement 文档基线为
`388cf37c09e3f0fc335fb8681813a60ff06edda0`。最初盘点不授权删除任何现场；项目所有者在 2026-08-30
追加要求：无价值游离分支必须明确标记删除。该授权只覆盖已经证明为祖先、patch-equivalent 或 superseded 的
branch ref，不覆盖构建目录、artifact、录像、日志、用户脏工作树或其他过程素材。

## 产品面

| 产品 / 能力树 | 盘点结论 | 处理 |
|---|---|---|
| `XenoAmess_s_Eternal_Recurrence`（Workshop `3784706360`） | 已在 master；发布构建、静态门和既有实机证据完整 | `already-contained` |
| `Eternal_Recurrence_Vivhite_Courtier`（Workshop `3787304042`） | 已在 master；独立 release/acceptance 合同保留 | `already-contained` |
| `ox_here`（Workshop `3790635143`） | 已在 master；唯一 AI 例外和 12 个月/恰好 1 年冷却合同保留 | `already-contained` |
| `mod_zhongguo_style` 0.3.0（Workshop `3792585972`） | 发布产品完整树只在 `origin/mod-zhongguo-style-wip`；tag `zhongguo-361-v0.3.0` 指向 `3932532`，分支 tip `17dc506` 含发布后 fresh-cache/公开页收口 | `merged`：从 exact master 做 `--no-ff` 合并，保留整个 phase-I 产品树 |
| `mod_zhongguo_style` v0.4.x 开发基线 | #001/#018/#069/#357 首纵切已形成 commit `b5a0b0e`；只有 L0/source-model/script-wiring 证据 | `merged-static-ready`：双父 merge `ec339ed` 收入 master；未启动 CK3、未发布，不提升为 fixture-live |
| `ck3_autonomous_player` / native bridge | master 含 G1 与 GEN-032b；一期分支含 landed-title typed MCP/native wire | `merged`：保留双方语义并集；能力数组 65、mailbox executor 13、CTest 44 |

## 分支与提交分类

### merged

- `origin/mod-zhongguo-style-wip = 17dc506fb3d5acfdab49b79fe235087d40ab7768`：完整 phase-I 产品、
  title-map MCP、release/Workshop/promo 证据与 CI/CD 脚本。本次正式 integration merge 的第二父提交。
- 本地旧 `master = 5fbed522`：它是 WIP 的祖先，27 个 ZhongGuo 提交已由 WIP 完整覆盖，不再单独合并。

### already-contained

以下分支的提交经 `git cherry origin/master <branch>` 全部显示 `-`，或 tip 已是 master 祖先；不重复合并：

- `agent-gen031-war-query-same-frame-20260828`
- `agent/battle-pause-reduction`
- `agent/perf-120dpm-20260828`
- `agent/sentinel-event-trigger-race-20260828`
- `perf-policy-neutral-rework-20260828`
- `stationary-timeout-1787909000`
- `origin/agent-defensive-war-native-20260828`

### superseded

- `agent/perf-production-speed3-20260828` 的旧 `1322b6a` promotion patch 不与 master patch-id 相同，但同一
  stationary speed-3 production 能力已由后续 policy-neutral scope、live `63.232 d/min` hard gate 和更严格
  sentinel 绑定替代。机械合并会回退当前策略/诊断实现。
- `agent/sentinel-cancel-20260828` 的旧 `5670890` 使用 `...cancel...v1-N`、`cancelled` 状态与旧返回帧；当前 master
  已改为 generation-bound `...v1-generation-N`、paused/generation 检查和后续 GEN-030/032 终端边界。旧实现不再接回。
- 主工作树中 7 个未跟踪 helper/source 文件的 blob 均能在 master 历史中找到，后来已经删除或被正式 runner 取代：
  `run_current_event_scopes_live_acceptance.py`、`one_generation_run.py`、两份对应测试、canary helper/handoff 和
  `run_one_generation_canary.ps1`。它们作为现场保留，不重新加入发布树。

### branch retirement ledger

以下标记只处置 branch ref；关联 worktree 先转为 detached HEAD，因此文件、未跟踪素材与历史构建现场继续原地保留。
`DELETE` 的证据已经用 `git merge-base --is-ancestor`、`git cherry origin/master <branch>` 和上述 superseded
实现对照闭合，不再为这些分支开新审计或恢复旧实现。

| 分支 | 证据 | 标记 |
|---|---|---|
| `agent-gen031-war-query-same-frame-20260828` | tip 已是 master 祖先 | `RETIRED` |
| `agent/battle-pause-reduction`（本地与远端） | `git cherry` 仅 `- 7960e7c` | `RETIRED` |
| `agent/perf-120dpm-20260828` | 3 个提交均为 `-` | `RETIRED` |
| `agent/sentinel-event-trigger-race-20260828` | `git cherry` 仅 `- dcfe397` | `RETIRED` |
| `perf-policy-neutral-rework-20260828` | 2 个提交均为 `-` | `RETIRED` |
| `stationary-timeout-1787909000` | `git cherry` 仅 `- b297852` | `RETIRED` |
| `origin/agent-defensive-war-native-20260828` | `git cherry` 仅 `- 3223c05` | `RETIRED` |
| `agent/perf-production-speed3-20260828` | 唯一残余 `+ 1322b6a` 已被 policy-neutral production gate 取代 | `RETIRED` |
| `agent/sentinel-cancel-20260828` | 唯一残余 `+ 5670890` 是已被 generation-bound 协议取代的旧合同 | `RETIRED` |
| `integrate/zhongguo-phase1-20260830` | tip 与完成 consolidation 的 master 相同 | `RETIRED`；worktree 已接管 local `master` |
| `origin/mod-zhongguo-style-wip` | phase-I tip 已是 master 第二父祖先 | `RETIRED` |
| 本地 `mod-zhongguo-style-wip` | phase-I tip 已是 master 祖先；dirty tree 同 tip detach 后 hashes 不变 | `RETIRED`；现场仍原地冻结 |
| `master` | 唯一正式集成与 CI/CD 准线 | `KEEP` |
| `wip/zhongguo-phase2-v0.4` | 当前唯一有效的 v0.4 开发线，基于 `22553a8` | `KEEP-ACTIVE`；本 L1 slice GREEN 后、第二 slice 前回并 master |

旧一期 ref 已删除，但 dirty checkout 和 process assets 均未删除；任何新代码都不得再以 `17dc506` 为基线。本清单禁止用
branch 清理名义清理那些素材。

### unfinished-preserved

- `wip/zhongguo-phase2-v0.4` 已无损迁到 `22553a8`，原 **20 个 tracked 修改 + 12 个 untracked 文件**
  已形成静态里程碑 `b5a0b0e97413a35a3ec50dad525251970fb659f0`；该成品切片现已通过 merge `ec339ed` 收入
  master。worktree 仍有两份未提交 acceptance 施工文件，字节继续保留；L0 GREEN 不代表 CK3 L1/L2/L3，后续仍必须 MCP-first
  合批实机，不能宣称 production-live。迁移前冻结 SHA-256：fixture `zga_effects.txt =
  0DE4BBDA09303AF95D264DF711EC69F391E2C1672C0FE5574100E04FA87B3F2A`，runner `run_zhongguo_acceptance.py =
  0396480674DBB059AF20CD8B93E7015E3CBE33C4C0C2EF0F4FD9C983E0352D0E`。
- `Z:\ck3_mod_rewrite` 主工作树已在同一 WIP tip `17dc506` detach，仍存在 **36 个 tracked 修改 + 12,600 个 untracked 路径**。
  tracked 中 12 个文件逐字节等于新 master、18 个是 master 历史旧 blob、6 个是旧 WIP 与历史 autonomous 代码/文档的
  未提交组合。产品 provenance 与 7 条 CK3 语法实证是其中仍有效的唯一知识增量，已精确迁入 integration；其余代码由
  当前 G1/GEN-032b/title-map 并集更完整地覆盖。
- 12,600 个 untracked 路径绝大多数是原生构建树、object、日志与历史媒体/artifact；
  `session-ses_fb82.md`（926,620 bytes）、月报/361 过程素材和下一版本 prototype archive 均原地保留，不进 Git、不删除。
- 独立 G2 common-dir 的继续施工现场已由 `agent-mainline-20260827@388cf37` 无损迁到
  `wip/g2-next-episode@22553a8`，仍有 4 modified + 1 untracked。它不是已成品能力，不并入本轮 commit；五份文件已按
  SHA-256 前后逐字节验证。SHA-256 依次为：
  `cli.py 97D439D2...19042`、`native_auto_run.py 3999A98F...367B9`、`native_session.py 079D3A52...09857`、
  `test_native_auto_run.py 6C040100...DA416`、`next_episode_run.py 1B05F6E2...4EC77`；完整 64 位值保存在本轮交付记录。

## 第二轮 exhaustive ref / clone 审计

第一轮只审了 `Z:\ck3_mod_rewrite` common-dir，遗漏了一个独立 G2 common-dir 和 15 个独立 runtime clone。这里按
[`branch-management.md`](branch-management.md) 重新枚举所有 `refs/heads`、`refs/remotes/origin`、worktree 和 `%TEMP%`
直属 `xar*` repository config；同 common-dir 去重，但逐 worktree 保留 dirty 证据。

### Z: common-dir

- 祖先：`agent-gen031-war-query-same-frame-20260828`、旧本地 `master=5fbed522`、一期 WIP `17dc506` 与完成第一轮的
  integration branch；能力和文档均已在 master history。
- patch-equivalent（`git cherry` 全为 `-`）：`agent/battle-pause-reduction`、`agent/perf-120dpm-20260828`、
  `agent/sentinel-event-trigger-race-20260828`、`perf-policy-neutral-rework-20260828`、
  `stationary-timeout-1787909000` 与远端 `agent-defensive-war-native-20260828`。`-` 证明整个 commit patch（包括 docs）已存在，
  不需要再机械 merge。
- 唯一 `+ 1322b6a` 的旧 speed-3 promotion 已被 `a790c5a/a2c81a0/95a466b` 的 policy-neutral selector、
  `63.232 d/min` hard-live gate 和 scope binding 覆盖；旧 branch 在专题文档中没有 master 缺失的事实行。
- 唯一 `+ 5670890` 的旧 cancel 使用 `...v1-N` / `cancelled` 与一度把 30 秒停滞归因于 wait envelope。后续同 checkpoint
  60 秒仍停在 `53267040`，证明 active event 阻断日更；当前 master 以 paused + exact generation CAS 到 `idle`、下一臂
  `generation+1` 和独立 player-decision boundary 取代。`90d3cf79`、两份 RED hash、60 秒反证和 `6421f80c` GREEN 均已保存在
  `battle-speed-control.md`、`army-controller.md` 与日/周报，因此删旧 ref 不丢经验。

### 独立 G2 common-dir

- 祖先：旧 `master=480f287` 与 `agent-mainline-20260827=388cf37`。
- patch-equivalent（每个 graph-unique commit 的 `git cherry` 均为 `-`）：
  `agent-adaptive-war-speed-20260828`（2）、`agent-crush-no-pause-20260828`（1）、
  `agent-defensive-war-native-20260828`（1）、`agent-sentinel-driver-integration-20260828`（3）、
  `fix-full-watch-unavailable`、`fix-peace-life-horizon-20260828`、`peace-query-hotpath-20260828`、
  `sentinel-candidate-gate-20260828`、`sentinel-strategy-integration-20260828` 和 `sparse-pause-20260828`。
- 唯一 `+ 8c306ed` 的 stationary-objective-hold canary 已被 production master 严格超集覆盖：当前实现保留 typed
  WarID/subject/objective/date、完整全军 watch、fresh post-stop 与原测试文件，又增加 decision-boundary cancel、policy-neutral
  selector 和 speed-3 live gate。旧专题只有“explicit canary / not production”三行被后续 live 事实取代，没有遗漏文档事实。

### 15 个独立 runtime clone

从 `%TEMP%` 直属 `xar*` 且 `.git/config` remote 指向本项目的目录复现发现；另一个命中目录是上述 G2 common-dir，按
common-dir 去重。14 个 clone fetch `388cf37` 成功，local `master` tip 都是严格祖先且 `git cherry` 为空：

`0848d61`、`f1230f6`、`32a0eb4`、`c21c096`、`3bd8934`、`8efa23f`、`aff784d`、`0ceb7d8`、
`9ff04ae`（两个独立 clone）、`cf98648`、`79b8d2a`、`7cb0b75`、`e0688c7`。这些是 live/benchmark source
checkout，不是遗漏开发线。

例外 `xar-event-scope-impl-commit-20260827-1045` 从 origin fetch 时在该冻结 clone 内报
`unresolved deltas` / `invalid index-pack output`，这是 pack/index 不一致的环境证据；目录不修、不删。健康 repository 随后从该
clone 成功临时导入 local tip `a860702`（无持久 ref）并完成内容对照：它已由同父 `5bc5485` 的
`701b3f8 Publish event scopes and unblock event choices` 语义超集覆盖。a860 的 13 条路径中，
相对 701 有 11 个 blob 逐字节相同；两处差异是测试把“多合法选项一律阻塞”升级为 bounded degraded choice，以及专题追加
exact candidate/DLL/injector/artifact hash、两次 startup RED、desktop identity 边界和诚实 live gate。当前 master 后来只进一步演进
`ck3_11906.cpp`、该测试和该专题，其余 10 个 a860 implementation blob 至今仍逐字节相同。

`xar-persistence-benchmark-9ff04ae` 另有两份 tracked benchmark 脏文件；其中 `_encode_driver_state_locked`、compact JSON、
`write_bytes_atomic` 和“禁止 full history payload clone”测试均已进入当前 master，且 current tests/driver 又包含后续状态与并发门。
两份脏文件仍按原 SHA 保存在 clone，不作为新能力重复合入：driver
`860B021C76BE50626FDE0DB317C62F46DA5F8D29EA84470257EF3B64A7B00F8C`，test
`313DAD3A7A86FEBEF69FB6ECE964B14D077B550CEB53B619A265DCDFE7E0BB0C`。

### 主脏工作树知识复核

- 15 个 tracked 文档/入口中，`asset-provenance.md`、`current-event-scopes.md`、`grammar/pitfalls.md` 三份已与 master
  逐字节相同；其余 12 份 root blob 可在 master 历史定位，`weekly/2026-W35.md` 是旧状态的组合快照。
- 对所有 root-only hunk 逐行复核后，只剩 pre-G1、旧 GEN 状态、旧 canary 命令或已被 typed exception / live 证据取代的描述；
  当前 master 已保留对应 artifact、失败原因、恢复合同和后继结论。历史 canary handoff 本身已由 master 跟踪并在进度 README 标成
  “历史”。因此没有为了“全收口”而把过期状态覆盖回当前文档。
- 仍有效的 key-art provenance 与七条 CK3 脚本经验已在第一轮精确迁入；本轮新增的真正遗漏经验是“单 common-dir 看不见独立
  clone”和“冻结 clone fetch 损坏时在健康 repo 临时对照、不能修删证据”，现已写入 `branch-management.md` 与
  `testing-workflow.md`。

## 合并边界

- phase-I 的已发布 0.3.0 tag/Workshop 物料保持不变；master 允许另含已明确标为 static-ready 的 phase2 开发代码。
- G1/GEN-032b、signed interaction ID、policy-neutral sentinel、same-frame war query 与 title-map typed facade 必须同时存在。
- 只吸收主工作树中确实未被覆盖的知识：ZhongGuo key-art provenance，以及 `ROOT/THIS`、decision 隐含 tooltip、
  activity scope/phase DDS、`ordered_in_list max`、首次 `change_variable` 和 GUI-only variable usage 七条实证。
- 不移动旧 release tag；只在新 master 官方 CI GREEN 后删除已经证明为祖先、patch-equivalent 或 documented-superseded 的
  branch ref。先 detach 同 tip、写 frozen sidecar 并复核 dirty SHA；不删除 worktree、clone、artifact 或 process assets。

## 验收入口

1. 完成 no-ff merge、冲突语义检查、phase-I tree equality 和 phase2 exclusion。
2. 在仅安装 `tools/requirements-static.txt` 的 Python 3.13 venv 跑 `.github/workflows/static-ci.yml` 全部公共步骤。
3. 对 native/autonomous 冲突跑完整 unit discovery 与 fresh MSVC/Ninja Release CTest。
4. 推送 master 后等待 push workflow GREEN；再手动 dispatch master，验证四套 candidate build 与 artifact upload GREEN。

## 2026-08-30 本地 integration 结果

- no-ff merge 以 exact `origin/master` `986d7281240334190e109f879eaa2f38877af489` 为第一父、
  `origin/mod-zhongguo-style-wip` `17dc506fb3d5acfdab49b79fe235087d40ab7768` 为第二父完成冲突解算。
  11 条实际冲突按产品、native、共享工具/CI 与进度文档逐项保留双方最新语义；未使用 phase2 工作树作为输入。
- staged `mod_zhongguo_style` tree 为 `61cbdcfd23ecdaa666b39ff186c823b3f7bb3eb0`，与 WIP tip 的产品树
  逐字节一致；phase2 专属 runtime、测试与文档路径扫描为 0。
- 仅安装 `tools/requirements-static.txt` 的 Python `3.13.2` 环境已逐项运行 `static-ci.yml` 全部公共步骤，
  四套产品的静态校验与可复现 release 均 GREEN。ZhongGuo release 仍为 51 files，ZIP SHA-256
  `7ECF185749A6DEB10C7B260EEC70040299EDBD0BE96F49D5418000221BC32BA2`。
- 官方 runner 原 RED 的直接原因是两个桌面 runner 单测在 import 阶段无条件加载 `pyautogui` 等 live-only 依赖；
  修复限于测试内安装最小 import stubs，未把桌面/OCR 依赖塞进 L0 requirements，也未改生产 runner。
- autonomous unit discovery：`1496 tests / 3 skipped / 0 failed`，耗时 `150.836s`。本次 integration worktree
  显式 junction 到冻结游戏树，原先 10 个环境型 `test_environment.py` RED 因而也按原测试合同通过。
- fresh MSVC/Ninja Release build：222 steps；CTest `44/44` GREEN，source fingerprint
  `BC721794399C735D530B3A99AFFA9982364EB06F53F7035A4EF069B5760CEDAE`，DLL SHA-256
  `2FAB665017DA824DC3A3BA1E85D6EF3F32FB7772A1554EC0D4D21B9368B6E7C9`，dependency mode
  `direct-2052-utf8`。构建目录与所有失败的命令行尝试均保留在 process assets，没有清理。
- 最终 consolidation SHA 为 `fa8893923731ae82bb9087dfb868b10bfc20e900`。官方 push run
  [`33301863644`](https://github.com/XenoAmess/ck3_eternal_recurrence/actions/runs/33301863644) 与同 SHA 的手动
  workflow-dispatch run [`33301945134`](https://github.com/XenoAmess/ck3_eternal_recurrence/actions/runs/33301945134)
  均为 terminal `SUCCESS`；后者完成四套 candidate build 与 artifact upload。artifact `9729238097`
  （`release-candidate-master-33301945134`，6,415,687 bytes）已原样保存在
  `Z:\ck3_mod_rewrite_process_assets\zg361\merge-phase1\actions\fa88939-dispatch-33301945134`。
- 首次 push merge SHA 为 `7ebb78d5904c06ad3847ded316301939296979c3`；官方 run `33301313411` 在
  `Test ZhongGuo 361 generators and acceptance contracts` RED。两个直接原因均为 L0 测试 fixture 偶然读取不存在的
  `CK3_EXE` / vanilla `00_game_rules.txt`，本机游戏 junction 曾遮住它们。最小修复只为相应用例提供 fake executable 与
  explicit vanilla-rule fixture，并为 provenance parser 动态构造最小 `han.txt/e_china.txt` 历史数据库。暂时移走
  integration 的游戏 junction 后，`static-ci.yml` 全部公共步骤已在“游戏路径不存在”条件完整 GREEN；原 RED run 保留，
  修复提交为 `ddc3f2045683f9fcf78c035a65c3b84e837ec239`。
- fix SHA `ddc3f2045683f9fcf78c035a65c3b84e837ec239` 的 run `33301609323` 通过上一轮失败 step，
  随后在 promo step 因 runner 无 ffmpeg 及 `%TEMP%` 的 8.3/长路径混用 RED。最小修复让纯 title-card/still 的
  draft/validate-only 路径不再发现未使用的 ffmpeg；video clip 与真正渲染仍硬性要求 ffmpeg/ffprobe。证据相对路径比较先
  `resolve()` 两端。本机从 PATH 移除 ffmpeg 后，promo 三命令组 GREEN；ZhongGuo 51-file formal staging 仍可复现且
  ZIP SHA-256 仍为 `7ECF185749A6DEB10C7B260EEC70040299EDBD0BE96F49D5418000221BC32BA2`，即修改只落在
  未发布的 promo tooling/tests。后续 `fa889392` push 与 dispatch 两轮已按上一条闭合。

## 第二轮 exhaustive consolidation 本地结果（17:31）

- phase2 静态 milestone `b5a0b0e97413a35a3ec50dad525251970fb659f0` 已由双父 merge
  `ec339ed56ab94ab2fe2d27ef220709318b5ac7d2` 收入从 `388cf37` 开始的 integration；两份未提交 acceptance 文件仍原字节
  留在 phase2 worktree，本轮没有启动 CK3，也没有把 `static-ready` 写成 live。
- 首轮无游戏树矩阵在 promo source contract RED：旧 validator 扫描整个 event 文件，把 phase2 从已冻结 result case 绑定 saved
  scope 误判为 legacy result event 重读 live review。修复只把禁令限定在 phase2 marker 之前的 `.2/.3/.4`，并新增 mutation
  回归证明 legacy token 仍会 RED；promo 定向复测 GREEN。
- 第二轮在 release localization RED：phase2 新增 40 个 core key，真实合同是 `2048 keys / 18 batches`，旧值为
  `2008 / 17`。MiniMax 只翻译新增 `core_03` 的 40×7，旧 119 个候选从 0.3.0 reviewed artifact 逐值保留；完整 126-file
  artifact `Z:\ck3_mod_rewrite_process_assets\zg361\localization\phase2_static_20260830_1724b` 的 translation-plan、complete-index、
  candidate-audit、seed-provenance SHA-256 依次为 `06209E5A...DE0A / C7C34A6C...AB8E / 1864D89C...F884 /
  46AF80A3...E09CC`。apply 只允许新增 key 是现有 source-order suffix；非前缀漂移继续 RED。
- 第三轮在 `validate_local` 识别七语重复：phase2 为结构加载而加的七份 English placeholder 文件，已被 canonical 七语正式译文
  完整取代，故删除这 7 个占位文件而不是降低 duplicate-key 门。最终 `35/35` release-loc tests、七语 key/order/protected token/
  target script/no-placeholder audit 与 `validate_local` 全 GREEN。
- 最终从头、临时隐藏本机 CK3 junction 的官方公共矩阵 terminal GREEN：主/Vivhite/Ox/ZhongGuo release tests
  `6/6、17/17、7/7、7/7 + cache 6/6`；361 generators `13/13`、scoreboard `10/10`、fixture/promo/workshop 全绿；
  media `6/6 + 8 JPEG`、promo `27/27 + 10/10`、MiniMax caller `26/26`、showcase `9/9`；四套 static 与 build-check 全绿。
  ZhongGuo development staging 是 51 files，manifest `8c96169c8394e6d361aa7936010672c0a9f24c77284a54bba9b600586128d8e1`、
  ZIP `b9d85f566be1ef7595ab8780baa12f003c36bb551cdcb549f3fd6e25272e0096`。它只证明当前 master 开发树可复现，未发布。

## 官方 GREEN 与实际 branch-ref 退休（17:58）

- 第二轮 consolidation 提交 `22553a882f1e3a0f7a70209611c0e9189718c3d0` 已普通 fast-forward 推到
  `origin/master`。push run [`33304348481`](https://github.com/XenoAmess/ck3_eternal_recurrence/actions/runs/33304348481)、
  workflow-dispatch run [`33304422168`](https://github.com/XenoAmess/ck3_eternal_recurrence/actions/runs/33304422168) 与同 SHA 的
  phase2 WIP push run [`33304583259`](https://github.com/XenoAmess/ck3_eternal_recurrence/actions/runs/33304583259) 均为 terminal
  `SUCCESS`。dispatch artifact `9730002463`（`release-candidate-master-33304422168`，6,434,230 bytes）已下载到
  `Z:\ck3_mod_rewrite_process_assets\zg361\merge-phase1\actions\22553a8-dispatch-33304422168`。
- 四套 candidate 的 manifest / ZIP SHA-256 分别为：main `CCC64938...C85A / AE64843F...6E49`、Vivhite
  `0C6FCE0B...3597 / B5D7F276...0C08`、Ox `8838AFEF...7629 / 2EAACBAF...18FD`、ZhongGuo
  `3D5F37E2...A57F / B9D85F56...E0096`；它们是 CI release candidate，不改变既有 Workshop 发布声明。
- 实际退休 **36 个 local refs**：Z common-dir 10 个（含一期 WIP 与临时 integration ref）、G2 common-dir 11 个、15 个独立
  runtime clone 的 `master`；另以普通 `git push --delete` 退休 4 个 remote refs。远端现只剩 `master` 与
  `wip/zhongguo-phase2-v0.4`；Z common-dir 只剩同名两条，G2 common-dir 只剩 `master` 与 `wip/g2-next-episode`；15 个独立
  clone 均为 detached HEAD 且无 local head ref。未删除或移动任何 worktree、clone、artifact、录像、日志或 process directory。
- 34 个保留根已写 `.xar-frozen-evidence.json`；`Z:\ck3_mod_rewrite` 是唯一中央 ledger 例外，以免 marker 本身改变所有者脏树。
  该根 detach 前后仍为 `17dc506`，status/diff hash 仍为 `1a95274e...201f / d0b7f574...c2d6`。phase2 两份 dirty 文件仍为
  `0DE4BBDA...3F2A / 03964806...2D0E`；G2 的 4 modified + 1 untracked 五个 SHA 仍为
  `97D439D2...19042 / 3999A98F...367B9 / 079D3A52...09857 / 6C040100...DA416 / 1B05F6E2...4EC77`。
- `%TEMP%` 最终发现命中 16 个本项目 repo config；按 resolved common-dir 去重后是 1 个 G2 common root 与 15 个独立 clone，
  没有隐藏开发分支。event-scope 冻结 clone 的 origin fetch/index-pack RED 仍原样保留；其 `a860702` 已有健康仓库语义超集证明，
  因 stale upstream 唯一使用本地 `branch -D` 删除 ref，clone 目录与对象未修、未删。dirty persistence 两文件仍为
  `860B021C...F8C / 313DAD3A...B0C`。
- machine-readable cleanup 根目录为
  `Z:\ck3_mod_rewrite_process_assets\zg361\merge-phase1\cleanup-20260830`。关键证据 SHA-256：
  `pre-cleanup-inventory.json 695FDA72...E57D`、`z-common-detach.json 53A33438...40B`、
  `g2-common-detach.json BEE0B05D...34C7`、`independent-clone-detach.json 9D817D44...8AFF`、
  `freeze-marker-index.json 6FD77BF4...59B`、`local-ref-deletions.json D65F00B8...26CF`、
  `remote-ref-deletions.json 8CC35453...A103`、`dirty-root-central-ledger.json A0192457...ECFC`、
  `master-workline-transition.json FD2E62A6...8315`、`post-cleanup-inventory.json 9AF435B8...5624`。
