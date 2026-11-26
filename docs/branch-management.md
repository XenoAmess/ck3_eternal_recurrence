# Branch management and frozen evidence

## Delivery cadence and minimum-branch rule

These are mandatory operating principles for every work package:

1. **One necessary verification, then delivery.** Run one verification pass
   proportionate to the work package and its risk. Once it passes—or produces
   a reproducible, well-recorded RED boundary—commit the result to the current
   mainline and push it with a normal fast-forward. Continue with the next
   package immediately. Do not repeat an unchanged check or wait for a second
   review unless new evidence changes the conclusion or the owner explicitly
   asks for another pass.
2. **Keep branches few and merge early.** Start from the newest
   `origin/master` and work on it directly whenever the files and runtime
   boundary permit. Create a short-lived branch only for real isolation,
   concurrent write conflict, or a high-risk live experiment. As soon as its
   work package is ready, merge it into `master`; after the exact master CI is
   terminal, delete the local and remote temporary refs. Detached evidence
   checkouts and retained artifacts may stay on disk, but they are not reasons
   to keep a development branch.
3. **Reuse a child process after HTTP 429.** A service-side `429` interruption
   is a scheduling interruption, not a work result. Reuse the original child
   task and its worktree first, then continue the same bounded package with
   local execution or another available child if needed. Preserve completed
   evidence and do not restart unchanged checks merely because the process was
   interrupted.

状态：2026-08-30 起生效。`origin/master` 是唯一集成真相；删除 branch ref 永远不等于删除 worktree、clone、构建目录、
录像、日志或 artifact。

## 默认工作方式

1. 默认从最新 `origin/master` 直接开发、测试、提交和推送。开始前先 `git fetch origin`，记录 exact base SHA。
2. 只有下列具体理由才建分支：需要隔离尚未成品的功能、与另一项真实并行施工冲突，或高风险 live/runtime 实验必须冻结独立
   source。单纯“以后可能有用”、方便堆提交或保存证据都不是理由。
3. 活跃开发分支使用 `wip/<short-topic>`；只有发布平台或版本流程确实要求独立线时才使用
   `release/<product>-<version>`。`release/` 不是长期开发分支。
4. 每个分支必须在下方 ledger 记录：reason、base SHA、owner、acceptance、merge deadline 和 status。成品一旦通过本地门，立即
   合入 master；等待该 master SHA 的官方 CI terminal GREEN 后，删除本地和远端 ref。
5. 禁止 force-push。并发直接推送前重新 fetch 并比较 `ls-remote`；远端已移动时停止当前 push，把自己的提交 rebase 到新的
   `origin/master`，复测后再以普通 fast-forward push 提交。不得覆盖他人的提交。

## 工作树、构建与冻结证据换盘

项目工作目录不绑定 C 盘。新 worktree 优先使用获准卷上的短绝对路径；机器根映射、卷容量、系统增长预留与复制峰值
按[通用存储策略](storage-retention-policy.md)记录。迁移前核对 owner 和实际 writer，记录 exact HEAD、dirty/untracked 状态及
必要内容清单，关闭使用该目录的构建、SDK、MCP 和游戏进程后再复制。保留未提交内容与原冻结证据，不把搬目录当成分支清理。

linked Git worktree 的 `.git` 文件和 common Git 目录含双向路径登记。跨卷复制完成后，使用所属主工作树执行
`git worktree repair <迁移后的绝对 worktree 路径>`，再核对 `git worktree list --porcelain`、新目录的
`git rev-parse --git-common-dir`、exact HEAD 和 `git status --porcelain=v2`。主工作树也迁移时，逐项修复其关联 worktree；
独立 clone 则核对自身 `.git`、alternates 和本地路径配置。未经修复与读回的副本不能作为可继续开发的 worktree。

CMake cache、构建清单、环境 manifest 和启动 argv 可能绑定旧绝对路径。后续构建须用新路径重新配置构建目录，
只按实际生产合同允许的范围复用对象；下一场 runtime/state 经公共准备与资格入口产生新绑定。
旧 manifest、来源 SHA、GREEN/RED/UNKNOWN、路径和文件身份作为历史事实保留，迁移另记旧到新的映射和当前可读性，
不批量改写冻结 JSON 或追认新路径已有旧资格。新 EXE 完整路径的 Defender 登记与实际设置读回另按现行专题执行。

机器 `xenoamess-full-tower-eb9d2c1186` 的背景工作目录目标为 `D:/codex-ck3-background`，state 目标为
`D:/ck3-state/<原 XarAutoplayer 目录名>`；实际状态见[2026-10-24 本机迁移记录](maintenance/2026-10-24-c-to-d-project-storage-xenoamess-full-tower-eb9d2c1186.md)。
新旧副本校验、消费者切换和精确回收各自记录完成情况，文档列出目标路径不表示这些步骤已经通过。

## 分支状态

| 状态 | 含义 |
|---|---|
| `active` | 有明确 owner、交付和期限，正在施工。 |
| `ready-to-merge` | 成品提交与本地 acceptance 已闭合，等待合入 master。 |
| `merged-ci-pending` | 已进入 master，但该 master SHA 的官方 CI 尚未 terminal GREEN。 |
| `retired` | master CI GREEN，关联 checkout 已 detach，local/remote ref 已删除。 |
| `frozen-exception` | 仅为保全脏现场暂留，不允许新提交；应尽快 detach 并删除 ref。 |

`already-contained`、patch-equivalent 和 superseded 不是活跃状态；它们只能进入 retirement ledger，不能继续开发。

## 共享工作树的 Agent 文件所有权

2026-08-31 的 ZhongGuo #361 施工出现过一次已复现覆盖：一条曾经拥有 Workforce 写权限的旧 Agent 被改派为“只读设计”后，
仍按旧上下文运行内存中的生成器，把新 Agent 尚未提交的 generator 与 generated files 一并恢复成旧版本。该事故没有进入
`master`，但造成约 700 行候选改动需要重放。后续在同一工作树并行时执行以下约定：

1. 每组 generator、generated files、tests 和对应 spec 只能有一个 active writer；跨域只读任务不得复用曾经写过该组文件的
   历史 Agent。
2. 改派旧 Agent 前先 `interrupt`，确认它已不再运行；若新任务与旧写域相邻，使用全新 Agent 名称，不能只靠提示词中的
   “只读”覆盖旧上下文。
3. writer 在大段重构完成、尚未生成前先报告 exact source diff；达到可测试原子边界后立即由根线程精确暂存、提交和推送，
   不让大量未提交生成源长期暴露在共享树中。
4. 发现非 owner 写入时立即停止双方，保留 `git status`/diff 证据，指定唯一 writer；随后只从权威 generator 重生全部产物，
   不能手工拼回 generated files 或假定未跟踪文件仍一致。
5. 只读设计如需检查同域文件，应在 frozen SHA 或独立只读副本上进行；不得运行生成器、formatter 或会写缓存到产品树的命令。

这条约定解决的是已经发生的共享工作树覆盖，不是要求为每个 Agent 新建 Git 分支；默认仍直接在 `master` 上快速收口。

## 冻结证据不是开发分支

历史 live source、失败复现、benchmark 或 release checkout 默认使用 detached HEAD。每个新冻结 checkout/clone 根目录默认必须有
`.xar-frozen-evidence.json`：

```json
{
  "schema_version": 1,
  "source_sha": "40-hex commit",
  "purpose": "why this checkout is retained",
  "owner": "person or task",
  "do_not_develop": true,
  "artifact_refs": ["absolute or repo-relative evidence paths"],
  "retention_state": "retained",
  "cleanup_state": "branch-ref-retired; files-preserved",
  "branch_ref_cleanup_at": "ISO-8601 timestamp with timezone",
  "created_at": "ISO-8601 timestamp with timezone"
}
```

marker 是 sidecar，不进入产品 staging；它不得替代 artifact 自身的 manifest/hash。唯一可用的无 sidecar 例外是：写 marker
本身会改变所有者已经交付并冻结的 dirty tree。此时必须在仓库外中央 machine-readable ledger 写入相同 schema，再追加绝对路径、
exact HEAD、`git status --porcelain=v2 -z` hash、`git diff --binary` hash、前后相等证明和“不写 root marker”的理由；该例外不得用于
普通 clean checkout，也不得省略 `do_not_develop=true`。若脏现场暂时无法 detach，只允许建立
`frozen/<short-purpose>` **本地分支**，同时登记 `frozen-exception`：禁止 push、禁止新 commit，待 dirty bytes/hash 已记录后立即
detach、写 marker、删除 ref。删除 ref 时禁止 prune/remove worktree，也禁止删除或搬移 process assets。

## Exhaustive ref audit

一次 common-dir 内的 `git branch --all` 看不到独立 clone 的 branch。声称“分支已清理”前必须：

1. 对当前仓库执行 `git rev-parse --git-common-dir`、`git for-each-ref refs/heads refs/remotes/origin` 和
   `git worktree list --porcelain`；
2. 枚举已知 workspace/process roots，以及 `%TEMP%` 直属 `xar*` 目录；读取 `.git/config`，只纳入 remote URL 指向本项目的
   repository；
3. 对每个 repository 取得 `--git-common-dir`，按 resolved common-dir 去重；同一 common-dir 的多个 worktree 只审一次 refs，
   但逐个检查 dirty status 与关联 branch；
4. 对独立 clone 分别 fetch current master，记录 tip、ancestry、`git cherry` 和 dirty state；不能用另一个 clone 的
   `origin/master` 猜它已同步；
5. 最终再重复枚举，确认只剩 `master`、ledger 中的 active `wip/`/必要 `release/`，以及明确记录的临时 exception。

Python 的最小发现入口：

```python
from pathlib import Path
import subprocess
import tempfile

for repo in Path(tempfile.gettempdir()).glob("xar*"):
    if not repo.is_dir() or not (repo / ".git" / "config").is_file():
        continue
    for git_args in (
        ("config", "--get", "remote.origin.url"),
        ("rev-parse", "--git-common-dir"),
    ):
        subprocess.run(
            ["git", "-c", f"safe.directory={repo}", "-C", str(repo), *git_args],
            check=True,
        )
```

冻结 clone 可能因历史 object pack 不完整而 fetch 报 `unresolved deltas` / `invalid index-pack output`。这属于冻结环境事实，
不是 capability RED；不得为让清理表变绿而修复、重打包或删除证据 clone。正确做法是在健康 audit repository 中临时 fetch 该
clone 的 local tip（不留 persistent ref），再与当前 master 做 ancestry/patch/content 对照，同时把损坏事实写进 inventory。

## 当前 ledger（2026-08-30 consolidation）

| branch / checkout | reason / base | owner | acceptance / deadline | status |
|---|---|---|---|---|
| `wip/zhongguo-phase2-v0.4`（迁移前名 `mod-zhongguo-style-phase2-v0.4`） | 二期 MCP-first 首纵切；WIP `3d135c9` 已拣入 master 为 `688c643` | ZhongGuo phase2 | attempt 06 bounded fixture-live GREEN；master `fa5c78d` 的 CI `33310061893` GREEN，checkout 已在该 tip detach 并写 frozen marker，local/remote ref 已删除，artifact 保留 | `retired` |
| `wip/g2-next-episode`（迁移前名 `agent-mainline-20260827`） | G2 `start-next-episode → gameplay/checkpoint` | autonomous G2 | commit `a348a62`、docs `46afe1d` 已进 master；CI `33306686336` / `33306797242` GREEN；checkout 在 `46afe1d` detach 并写 marker，本地 ref 已删除，artifact 保留 | `retired` |
| `Z:\ck3_mod_rewrite` | 一期 WIP tip `17dc506` 上的用户脏现场 | owner | 已同 tip detach、删除 ref；中央 ledger 保留 exact HEAD/status/diff，绝不删除 36 tracked / 12,600 untracked | `retired` ref；frozen evidence 原地保留 |
| 旧 agent/runtime/release checkout | 已合入、patch-equivalent 或 superseded 的 live 证据 | consolidation | 34 个根已 detach + marker；目录不随 35 个历史 ref 删除 | `retired` |

## 2026-09-02 mainline consolidation

After the `87d557c` master CI completed GREEN, the short-lived parent refs
whose changes were already merged or patch-equivalent were retired. Their
associated clean worktrees were switched to detached HEAD and kept on disk;
no source, build, log, or process-assets directory was removed. Retired refs
include the `agent/kaishek-acceptance-coverage-*` pair,
`agent/kaishek-adapter-refresh-20260902`,
`agent/kaishek-preflight-adapter-20260902`,
`agent/promo-phase2-preflight-docs`, `docs/preflight-policy-20260902`,
`g2-gen034-native-contract-tests`, `promo/phase2-producer-typed-red-20260901`,
and the three `wip/phase2-*` refs. The G2 fresh-run branch
`feat/g2-next-run-preflight-20260902` was merged as `a1f424e` and its ref was
retired after its own CI success. The later G2 protocol regression was pushed
as `a84c53d`; the short-lived `g2/action-step-regression-20260902` ref was
retired immediately. The phase2 loader observation was merged as `a5c079e`
from `phase2/loader-observe-20260902`, whose ref was also retired after the
focused fixture passed.

The independent `Z:\workspace\open_kaishek` checkout follows the same rule:
`feat/government-flag-schema-20260902` was merged as `450b559` and
`feat/perk-schema-20260902` as `a670589`, then the dynasty-perk slice as
`757fb1b`; `feat/dlc-feature-schema-20260902` then advanced `main` to
`7da444d`, followed by `feat/court-position-schema-20260902` at `bd980e7`;
all five short-lived refs were deleted immediately.
Its canonical `main` is `bd980e7`, and only the two pre-existing user branches
(`feat/cli-batch-replay` and `feat/zg361-appeal-replay`) remain. Historical
parent refs with distinct user-facing release/evidence ownership are retained
until their owners request retirement.

The loader callback contract was merged as `56e786c` from
`phase2/callback-probe-20260902` (`7758b9b`); the source branch and remote ref
were deleted immediately after the focused `4/4` test passed. Its detached
worktree and static artifacts remain available for evidence.

## 2026-09-05 branch-debt retirement

The repository had accumulated **199 local branches, 198 GitHub branches, and
293 registered worktrees**. The dominant cause was operational rather than
product divergence: earlier work created one branch and worktree per
diagnostic, frozen candidate, replay, or evidence package, then integrated the
result through cherry-pick or a later reimplementation. The completed branch
refs were not retired. A stale local `master` that was 636 commits behind the
remote also made ancestry-only checks misclassify most integrated work as
unmerged.

The cleanup therefore used current `origin/master`, patch equivalence, commit
subject mapping, and content comparison rather than ancestry alone. It retired
175 patch-equivalent local and remote refs first, then reviewed every remaining
non-protected branch. The final 20 GitHub candidates were all either present on
master or superseded by later production implementations; none required a
merge. Their occupied worktrees were switched to detached HEAD at the same
commit before their refs were removed. Dirty and untracked bytes were retained,
and no worktree, clone, artifact, build directory, or process-assets directory
was deleted. The foreign-root promo-toolchain `main` history was removed from
this repository only after commit `fbdf990` was proven to be an ancestor of
the independent tool repository's `origin/main`.

After this pass, both the local repository and GitHub contain only `master` and
the temporary current integration ref. They point to the same pre-repair commit;
the integration ref must be retired immediately after the in-flight B1 repair
is committed and fast-forwarded to `master`. Future evidence freezes use
detached HEAD by default, and each completed work package retires its branch
ref as part of delivery rather than as a later cleanup project.

## 合并与清理 checklist

- [ ] base SHA、owner、reason、acceptance、deadline 和 status 已进 ledger；
- [ ] 成品 diff 不含另一条 WIP 或测试素材泄漏；本地相关门 GREEN；
- [ ] push 前 `ls-remote` 与预期 master 一致，无 force；
- [ ] exact master SHA 的全部 required Actions terminal GREEN；
- [ ] 每个关联 worktree/clone 在相同 tip detach，dirty 文件数量与 SHA 前后不变；
- [ ] frozen checkout 已写 `.xar-frozen-evidence.json`，`do_not_develop=true`；若使用唯一 dirty-owner-root 例外，中央 ledger 含
      同 schema、exact HEAD/status/diff 与不写 marker 的理由；
- [ ] 删除的是 local/remote branch ref，不是 worktree、clone、artifact 或 process directory；
- [ ] 已枚举并按 common-dir 去重所有 workspace、worktree 与独立 `%TEMP%` clone；
- [ ] 最终 ref 清单只剩 master、ledger 中 active `wip/`/必要 `release/` 和明确 exception。


### 2026-10-05：短路径仍可能超出Windows默认长度

后台第二批从master3e2737b5创建Z:/gbr2时，两个新跟踪的docs/li-yu-dao深层claim路径出现`Filename too long`，Git随后无法reset index并自动回收失败worktree。短路径并不保证所有仓库文件都低于默认路径长度。此真实RED用`git -c core.longpaths=true worktree add --detach <short-absolute-path> <exact-head>`修复；只对本次Git命令启用，不改全机设置、不清理旧树。新checkout后核.git、exact HEAD和clean status再分配owner。原工具回执和未宣称完整log保全的纠正记录在Z:/ck3_mod_rewrite_process_assets/g2-background-round2-20261005/CHECKOUT-RED-RECEIPT.json；六树登记见同目录lanes.json。

## 2026-11-26 主线收口

机器 `xenoamess-full-tower-eb9d2c1186`。起始远端 33 条分支，主 common-dir 有 148 条本地分支。来源包括旧场次冻结候选、已通过等价补丁进入主线的产品分支，以及 Dependabot 请求。

- #789–#797 全部以 rebase 进入 `master`，远端回读为 `MERGED`，开放请求为 0。六条旧 CI 失败记录涉及以前的共享 Java 或验收用例，分别核查失败步骤并补跑当前依赖的对应测试。Jackson 存档核心 23 项通过，Pillow 使用当前包通过 27 项媒体和图像测试以及 DDS 打包产物读回。
- 8 条 `campaign/*`、2 条 `runtime/*` 的当前实现已由主线生产提交覆盖，两个旧 1.20.0.4 实验仍可通过 `1ab7c74222` 的证据和补丁追溯。再核对 `research/e04-r217-runtime-8faa99b`、`work/episode04-r186-fixture-d05b0c780` 的 5 个等价补丁。所有对应工作都由 [95df3809be 官方 CI](https://github.com/XenoAmess/ck3_eternal_recurrence/actions/runs/39957553119) 覆盖，12 个远端引用已退役，10 个同名本地引用和另外 5 个主线祖先引用也已退役。
- 后续主线独立移植了过期 keeper 锁内重验 `b2755053c6`、Dynastic Esotericism 可选礼仪引用 `6d6cee99af`、公开运行前的协作停止 `1ce9b5f2e6` 与 Florin 自定义战争计时 `adfdbb324c`。其中过期 keeper 覆盖相关 CI 步骤的 74 项测试，协作停止的 55 项锁内测试及测试文件严格类型检查通过，战争计时覆盖安装目录只读依赖与 75 项静态测试。官方 CI 的 Crisis20 联合类型修复 `8b0fa04304` 通过该步骤和相邻离线用例。
- 5 条金融市场分支与 4 条交付分支的补丁已在 `master`。2 条旧 DES 分支还有存档检查和验收工具待接入，4 条已合并的 bot 引用仍在。按实际主线 CI 结果继续退役，已检出的本地引用先核对工作树所有权。

退役前的 27 条远端引用与原始对象已保存在可验证的 Git bundle，前置对象由主线提供。原始 GitHub 回读和 Git inventories 在 `D:/ck3-state/ck3-master-integration-20261126`。Bundle SHA-256 为 `ee9aa54f202a25b40afb5f15e74eba5f0e6846d52ab6547f1d41c4dae9bf9970`。本轮只删除 Git 引用，场次目录与已绑定工作树保留。

后续核对同一官方绿色基线，另退役 13 条未检出的等价本地引用。原始提交存于 `local-equivalent-before-retirement.bundle`，SHA-256 为 `40c6e282839c977d1fa8567681a4c53c42f92435ff28f69a4cf39db488b3f870`。

主线继续接入 Native 等待原始快照修复 `59e7cdd125`、词法路径别名回归 `399c31ec15`、DES 原发布和部分验收历史 `164f103921`、选中对象和意见读取 `02e642d16b`、完整家族父级读取 `e1e23a94d6`、帝国恢复离线证据 `758a4ffe2d`。帝国恢复通过 42 项 Save Core 和 6 项 DES 测试，实包核对 55 项产物与 28 个源码文件。目前的原生 Title 读取仍有 int32 范围，公开 UI 验收等待真实 S1 原件，产品版本未更新。Native 等待回归连续 30 轮通过，另有 5 项通过及旧计时夹具的 3 次重复通过，见 `0cb700f714`。

`42e204dbe6` 把相同 Maven 3.10.0 发行包与校验和的来源移至 Maven Central。生产下载、校验及解包 4.057 秒，46 项本地启动测试通过。此前下载超时的两个托管 workflow 都已通过新版的 Maven 准备及读回步骤，继续进行产品验证。[DES 托管回执](https://github.com/XenoAmess/ck3_eternal_recurrence/actions/runs/45798383204) [礼仪融合托管回执](https://github.com/XenoAmess/ck3_eternal_recurrence/actions/runs/45798383150)

10:28 UTC 直接回读显示 5 条远端分支（含 `master`）和 66 条本地分支。金融市场 5 条、Save Core CI、礼仪融合菜单、DES 回调和交接、Jackson、家徽编辑器 Pillow 的额外 11 个远端 ref 均已退役。其提交经等价补丁核对，相关项目的官方检查已通过。家徽编辑器的部署 workflow 亦通过。当前保留两个已合入的 Dependabot ref 等一般 CI，以及两条仍有未验收内容的旧 DES ref。[金融市场](https://github.com/XenoAmess/ck3_eternal_recurrence/actions/runs/45799136613) [礼仪融合](https://github.com/XenoAmess/ck3_eternal_recurrence/actions/runs/45799137654) [DES](https://github.com/XenoAmess/ck3_eternal_recurrence/actions/runs/45799136517) [家徽编辑器](https://github.com/XenoAmess/ck3_eternal_recurrence/actions/runs/45794827652)

55 个干净且在同一官方绿色主线覆盖的工作树完成逐一核对。54 个在原 SHA 上切换为 detached，保留工作树文件及冻结标记，再按原 SHA 删除本地 ref。`codex/person-entry-next-input-97321` 在同 SHA detach 后本机物理文件清单有变化，Git 工作状态仍干净，原 ref 保留。82 条本地 ref 已退役。带本地改动、锁定或仍属其他 owner 的工作树保持各自状态。精确祖先清单和可解包复验的 42 条原始引用 bundle 位于 `D:/ck3-state/ck3-master-integration-20261126/linked-clean-worktree-retirement01`。

10:32 UTC，MCP 2.2.0 与战争 AI 录制 Pillow 13.0.0 的正式依赖图、线性历史和主线等价补丁分别确认。本机对应 MCP 共 36 项、录制 7 项离线用例通过，最后两个 Dependabot ref 已退役。远端仅余 `master`、`work/dynastic-heir-stock-input-20261025`、`work/dynastic-product-reactor-20261030`，开放 PR 为 0。[MCP 依赖图](https://github.com/XenoAmess/ck3_eternal_recurrence/actions/runs/45793880324) [录制依赖图](https://github.com/XenoAmess/ck3_eternal_recurrence/actions/runs/45794809522)

两条 DES 分支的可用原件及离线工具已陆续进入主线。两阶段罪行 fixture 在 `c0a2c51fd3` 通过 13 项 Save Core、22 项 DES 和 Quarkus 打包。仍在分支内的公开帝国恢复接线需要真实原版 UI S1 与持有者快照，旧编排工具依赖冻结场次和仓库外类。现行 v4 和金融存档的重复检查维持原合同。对应分支继续保存，完整官方主线检查仍在运行。

10:37 UTC，`work/dynastic-product-reactor-20261030` 已退役。它与继承人分支自 `4680f73aea` 分叉后仅有两个独有提交。其类型检查环境已由主线的完整 DES CI 步骤覆盖，别名回归由 `b0a5305979` 和 `399c31ec15` 覆盖。共享历史仍由 `work/dynastic-heir-stock-input-20261025` 保留，退役前两条完整引用仍在 bundle。远端现为 `master` 与这一条待验分支，本地为 66 条。[DES CI](https://github.com/XenoAmess/ck3_eternal_recurrence/actions/runs/45801837726) [线性历史](https://github.com/XenoAmess/ck3_eternal_recurrence/actions/runs/45801837661)

11:06 UTC，剩余继承人分支的补丁清单已逐项与主线对照。`a2a423d6ba` 补齐已移植的 Root 协作停止测试的严格类型覆盖，55 项回归通过。`192a4a9446` 接通 DES 验收实际需要的 campaign-root 能力，修复其离线测试的子进程输出等待，3 项产品验收测试及 Quarkus 构建通过。`2bc37bc628` 把当前 HELLO 的攻城能力值传到 Python 兼容入口，常规和优化模式各 8 项通过，相邻 18 项通过。旧场次专属 Java 执行工具依赖未入库的类型，孤立编译可复现失败。公开帝国恢复仍缺真实 S1 及有效原生 Title 证据，Decisions 同帧兼容代码继续核对。远端仍为两条引用，开放 PR 为 0。

`d037addd4d` 移植旧 R28 已复现的 Decisions 可见性读取。原公开 revision 上已有成功 claim 时，使用本次实际可见树返回读取结果。原 UNKNOWN 阻断及原 v1 文件保留，旧分支的同 revision 关闭再开缺少当帧关闭原件。固定 CI 依赖下 156 项通过、4 项预计跳过，另有 31 项消费方回归通过。`ea2a17731d` 修复 Steam 离线配置夹具的两处严格类型失败，183 次相关离线测试通过。最后继承人分支的精确原 tip `c3e46759b397f2f1950b6b46066a67c2df631dcb` 已在原 bundle。官方 CI 尚在运行，公开帝国恢复缺原件的状态保留。

13:16 UTC，远端回读仍为两条分支，开放 PR 为 0。已在独立 bare 仓库还原原 bundle 中的 27 条引用，逐字节比对最后继承人分支的 5 个关键文件。15 个前置对象均可从主线取得。还原回执为 `D:/ck3-state/ck3-master-integration-20261126/dynastic-c3e-isolated-audit/bundle-restore.json`。

最后分支的旧开局夹具只能生成拜占庭 S0。公开帝国恢复仍缺实际付费操作和独立实机回执、后继 S1 物理存档及对应头衔持有者状态。旧注册表将两条恢复 case 设为 ready，但两条操作合同均仍缺存档身份和日期。主线保留已验的离线消费者，现有原生持有者查询只接受 int32 范围。旧容量与执行工具依赖仓库外冻结类。独立 recorder 样例以原源码通过 40 项离线检查，主线现行录制路径和原回执格式消费者已覆盖其有用行为，未发现需要新增该工具的生产调用。DES 旧 reactor 改动已由根 `pom.xml` 的正式按模块构建覆盖，发布 workflow 的步骤名称用现行投影术语。

本地 common-dir 审计起始为 66 条分支，43 条有工作树。另退役未检出的 `holy-order-source-condition30-first-20261006`。8 个提交补丁相同，剩余 mapper 提交除 CMake include 位置外等价于 `700406a4d6`，该 include 在绿色主线中已核对。退役后余 65 条。原 tip 已在 `D:/ck3-state/ck3-master-integration-20261126/local-residue-4bfc/holy-order-source-condition30-first.bundle`，SHA-256 为 `0f77bce1340a13869fcda64e067eb89c8f2d7183960293d2a812bf17a2e9e08f`。Z 盘用户工作树上的两个提交已通过补丁等价核对，工作树有未提交修改。[已覆盖主线 CI](https://github.com/XenoAmess/ck3_eternal_recurrence/actions/runs/39957553119) [DES 专项 CI](https://github.com/XenoAmess/ck3_eternal_recurrence/actions/runs/45801837726)

最后一条 DES 继承人分支的原始 28 个提交已纳入主线的[可恢复归档](handover/archives/dynastic-heir-stock-input-20261025.md)。
已验证从 GitHub 取得单个主线前置提交即可在独立仓库恢复原 tip 和源码树。
主线继续使用已验收的离线合同。公开帝国恢复的 S1 实机证据和旧编排的冻结类型依赖按原状态记录。

15:26 UTC，旧实机冻结候选和后继线性重放是本轮本地分支存量的主要来源。依照已通过的
`95df3809be`，35 条分支引用已退役。原提交、源码与恢复方法见
[旧自动游玩分支归档](handover/archives/retired-local-autoplay-20261126.md)。原工作树维持原提交，
已检出的干净工作树切到同一提交的 detached HEAD，写入冻结标记。未提交源码和在用工作树按现有所有权处理。
分支审计和还原回执位于 `D:/ck3-state/ck3-mainline-closeout-20261126`。
[主线官方 CI](https://github.com/XenoAmess/ck3_eternal_recurrence/actions/runs/39957553119)

旧分支中尚缺的七份静态研究原文和 Construction FIRST02 的离线记录已补回。战斗胜方所属 War 的
1.20.0.3 专用原始实验完整保存于[独立归档](handover/archives/battle-winner-war-membership-12003.md)，
原验证状态和当前原生运行资格各依原记录。

第二批以同一绿色主线为依据，又退役主仓库 17 条和独立克隆 6 条引用，本轮合计 58 条。
带改动的旧工作树在原 SHA 上解除分支绑定，状态、二进制差异及 Git index 摘要前后一致。
锁定初始化的 `nw-activity-guest-value-20260930` 保留。`migration-mods-20261118` 原工作树有未提交改动，按原目录保留。
其 14 条已提交改动分别核对了正式后继，其中 Ox Here 普通冠军薪资由 `6d05e69e67` 接回当前原版计算。
8 项静态用例与 22 文件的可复现打包检查通过。原召唤冠军免费，原发布标签维持原提交。
本轮未发布新 Workshop 版本。独立克隆与第二批回执保存在 `D:/ck3-state/ck3-mainline-closeout-20261126`。

余下远端 `work/dynastic-heir-stock-input-20261025` 的源码归档已入主线，等待 exact `6a97ab3450` 的官方检查。
已补回的历史文档和研究归档由 `894f7d0bc1` 发表，对应本地历史 ref 依该提交的官方结果退役。
旧 Java Tools/休假候选的后继已在主线，更新到其覆盖范围的完整托管检查仍待通过。
[DES 归档 CI](https://github.com/XenoAmess/ck3_eternal_recurrence/actions/runs/45837231107)
[历史资料归档 CI](https://github.com/XenoAmess/ck3_eternal_recurrence/actions/runs/45848944860)

2026-11-27 00:34（UTC+8），`6a97ab3450` 的官方 Java 检查完成并失败。两轮 Tools 各通过 1,248 项测试。随后 qualified 子进程因缺 `artifacts/tools-postqualification/actual.json` 退出，尚未进入完整 reactor、HTTP 和独立 SDK 夹具。归档已在主线并验证可恢复，继续保留最后一个远端旧分支引用。[官方检查](https://github.com/XenoAmess/ck3_eternal_recurrence/actions/runs/45837231107)

2026-11-27，另对本机 11 条剩余引用逐条核查。在 `machine_id: xenoamess-full-tower-eb9d2c1186` 上，以 `84fe1d22e3` 为起点制作了五条旧 Native 分支的 Git bundle。原 tip 在独立 bare 仓库解包和读回，五个前置均是主线祖先。bundle 与校验为 `D:/ck3-state/ck3-mainline-closeout-20261126/remaining-native-backup-20261127/BUNDLE-VERIFIED.json`。Battle 分支使用主线已有归档。当前覆盖这些分支的官方验收仍在运行，引用保留。[历史归档 CI](https://github.com/XenoAmess/ck3_eternal_recurrence/actions/runs/45848944860)
