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

PowerShell 的最小发现入口：

```powershell
Get-ChildItem $env:TEMP -Directory -Filter 'xar*' | ForEach-Object {
  $repo = $_.FullName
  if (Test-Path (Join-Path $repo '.git\config')) {
    git -c "safe.directory=$repo" -C $repo config --get remote.origin.url
    git -c "safe.directory=$repo" -C $repo rev-parse --git-common-dir
  }
}
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
