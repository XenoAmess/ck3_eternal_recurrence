# Master consolidation inventory — 2026-08-30

状态：**master consolidation、官方 push CI 与手动 release-candidate CI/CD 全部 GREEN；无价值游离分支已标记删除**

本清单以 consolidation 起始 `origin/master = 986d7281240334190e109f879eaa2f38877af489` 为基线，目标是把仍有效、且未被
master 等价或更优实现覆盖的能力和 mod 收口到同一个 master。最终 consolidation 基线为
`fa8893923731ae82bb9087dfb868b10bfc20e900`。最初盘点不授权删除任何现场；项目所有者在 2026-08-30
追加要求：无价值游离分支必须明确标记删除。该授权只覆盖已经证明为祖先、patch-equivalent 或 superseded 的
branch ref，不覆盖构建目录、artifact、录像、日志、用户脏工作树或其他过程素材。

## 产品面

| 产品 / 能力树 | 盘点结论 | 处理 |
|---|---|---|
| `XenoAmess_s_Eternal_Recurrence`（Workshop `3784706360`） | 已在 master；发布构建、静态门和既有实机证据完整 | `already-contained` |
| `Eternal_Recurrence_Vivhite_Courtier`（Workshop `3787304042`） | 已在 master；独立 release/acceptance 合同保留 | `already-contained` |
| `ox_here`（Workshop `3790635143`） | 已在 master；唯一 AI 例外和 12 个月/恰好 1 年冷却合同保留 | `already-contained` |
| `mod_zhongguo_style` 0.3.0（Workshop `3792585972`） | 发布产品完整树只在 `origin/mod-zhongguo-style-wip`；tag `zhongguo-361-v0.3.0` 指向 `3932532`，分支 tip `17dc506` 含发布后 fresh-cache/公开页收口 | `merged`：从 exact master 做 `--no-ff` 合并，保留整个 phase-I 产品树 |
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
| `agent-gen031-war-query-same-frame-20260828` | tip 已是 master 祖先 | `DELETE` |
| `agent/battle-pause-reduction`（本地与远端） | `git cherry` 仅 `- 7960e7c` | `DELETE` |
| `agent/perf-120dpm-20260828` | 3 个提交均为 `-` | `DELETE` |
| `agent/sentinel-event-trigger-race-20260828` | `git cherry` 仅 `- dcfe397` | `DELETE` |
| `perf-policy-neutral-rework-20260828` | 2 个提交均为 `-` | `DELETE` |
| `stationary-timeout-1787909000` | `git cherry` 仅 `- b297852` | `DELETE` |
| `origin/agent-defensive-war-native-20260828` | `git cherry` 仅 `- 3223c05` | `DELETE` |
| `agent/perf-production-speed3-20260828` | 唯一残余 `+ 1322b6a` 已被 policy-neutral production gate 取代 | `DELETE` |
| `agent/sentinel-cancel-20260828` | 唯一残余 `+ 5670890` 是已被 generation-bound 协议取代的旧合同 | `DELETE` |
| `integrate/zhongguo-phase1-20260830` | tip 与完成 consolidation 的 master 相同 | `DELETE` |
| `origin/mod-zhongguo-style-wip` | phase-I tip 已是 master 第二父祖先 | `DELETE` |
| 本地 `mod-zhongguo-style-wip` | phase-I tip 已是 master 祖先，但仍承载 `Z:\ck3_mod_rewrite` 脏现场 | `DELETE-DEFERRED`：现场完成迁移/归档后删除 ref；现在禁止强拆 |
| `master` | 唯一正式集成与 CI/CD 准线 | `KEEP` |
| `mod-zhongguo-style-phase2-v0.4` | 当前唯一有效的 v0.4 开发线，基于完成 consolidation 的 master | `KEEP-ACTIVE`；每个成品里程碑及时回并 master |

这里的 `DELETE-DEFERRED` 不是让旧一期分支继续开发。它只是一枚保护用户脏现场的临时引用；任何新代码都不得再以
`17dc506` 为基线。删除 branch ref 也不等于删除 process assets，本清单禁止用 branch 清理名义清理那些素材。

### unfinished-preserved

- `mod-zhongguo-style-phase2-v0.4` 已无损重基到 `fa889392`，原 **20 个 tracked 修改 + 12 个 untracked 文件**
  已形成静态里程碑 `b5a0b0eb4872657ee3de973f54f8089006167ca7` 并推送独立分支。它仍是未完成的下一版本：L0 与
  可复现 release GREEN 不代表 CK3 L1/L2/L3；完成 MCP-first 批量实机验收前不得合入 master 或宣称 production-live。
- `Z:\ck3_mod_rewrite` 主工作树仍在 WIP tip，存在 **36 个 tracked 修改 + 12,600 个 untracked 路径**。
  tracked 中 12 个文件逐字节等于新 master、18 个是 master 历史旧 blob、6 个是旧 WIP 与历史 autonomous 代码/文档的
  未提交组合。产品 provenance 与 7 条 CK3 语法实证是其中仍有效的唯一知识增量，已精确迁入 integration；其余代码由
  当前 G1/GEN-032b/title-map 并集更完整地覆盖。
- 12,600 个 untracked 路径绝大多数是原生构建树、object、日志与历史媒体/artifact；
  `session-ses_fb82.md`（926,620 bytes）、月报/361 过程素材和下一版本 prototype archive 均原地保留，不进 Git、不删除。

## 合并边界

- phase-I 的 `mod_zhongguo_style` tree 必须逐字节等于 WIP tip；phase2 文件不得出现。
- G1/GEN-032b、signed interaction ID、policy-neutral sentinel、same-frame war query 与 title-map typed facade 必须同时存在。
- 只吸收主工作树中确实未被覆盖的知识：ZhongGuo key-art provenance，以及 `ROOT/THIS`、decision 隐含 tooltip、
  activity scope/phase DDS、`ordered_in_list max`、首次 `change_variable` 和 GUI-only variable usage 七条实证。
- 不移动旧 release tag，不删除远端/本地分支，不改写任何用户/agent 脏工作树。

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
