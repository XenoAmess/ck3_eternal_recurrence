# 只用 rebase，拒绝新 merge commit

2026-10-07。AGENTS明确要求fetch/rebase/普通fast-forward push，禁止merge和force-push。已经公开的历史merge保留；本次不重写提交、不force，不把远端提交归因到缺少确凿repo/head/task证据的人。

Root于07:15:55 UTC实际启用[master-rebase-only-no-merge-commits规则24634448](https://github.com/XenoAmess/ck3_eternal_recurrence/rules/24634448)：active、bypass_actors=[]，只匹配refs/heads/master，required_linear_history。GitHub有效master规则已实际读回；原branch protection全文before==after，CLA/signed/force-push=false等原设置保持。[实际回执](C:/workspace/ck3-upgrade-20261007/resume-root-02/master-linear-history-ruleset-actual-01/actual-enforcement-receipt-01.json)，SHA `2f0f7c4a8aaa81e5982d2b9318f6e3b942f25b9376ff571d49b781a0f3c1d6a7`。服务器已拒绝新merge；不需要造测试merge push。

既有`tools/git_operator_common.py`继续拒绝wrapper的merge、无--rebase的pull及force push。此次补齐裸git的本机hooks与图历史检查，不重做原Git operator、认证或传输系统。

- `pre-merge-commit`直接拒绝自动生成merge commit；`pre-commit`拒绝仍有MERGE_HEAD的人工提交。
- `pre-push`按stdin每一条ref检查实际local新tip相对remote旧tip的**全部新祖先**，任一commit超过一个parent即拒绝整个push，不用first-parent筛掉侧链merge。删除ref没有新commit。
- 新branch/tag没有remote旧tip时，以本机已获取的`refs/remotes/origin/master`作为已公开baseline，仅排除baseline已有历史，不排除本地新分支或本地merge。baseline缺失/无法读取时拒绝并要求fetch。此基线有意允许保留已公开旧merge；它不替代实际远端fast-forward拒绝或禁止force的原合同。
- 独立`Linear history / No new merge commits` CI只检查master push的实际before..after或PR base..**head SHA**，不检查GitHub临时synthetic merge；完整fetch，无路径过滤，无CK3/产品全测。CI给诊断结果，服务器拒绝由已实际启用的ruleset承担。

本机hook安装须由root显式执行；候选工具`install_local_linear_history_hooks_01.py`默认仅输出计划，`--execute`才写repo-local hooks/config。它拒绝覆盖已有active hooks或core.hooksPath，使用执行时已验证Python解释器，不调用PowerShell。候选准备与验证没有修改主仓hook/config；root现已设pull.rebase=true/pull.ff=only/branch.master.rebase=true，实际hook启用另以安装readback记账，不能把该config当成已安装hook。

本次只读范围是本机`.github/workflows/`下当前可见5份YAML、4个Git operator文件、相关AGENTS/交接条款及当前Git配置，不声称穷尽仓库其他目录或其他机器CI。发现原默认hooks只有sample、无core.hooksPath；原现有CI没有新增commit的parent-count门禁。该观察保留其当时范围。

[隔离proof](C:/workspace/ck3-upgrade-20261007/linear-history-guard-candidate-write-diagnostic-01/LINEAR-HISTORY-SANDBOX-PROOF-01.json)一次10项PASS：仅独立sandbox的init/update-ref/commit-tree构造两parent，以及实际hook调用；没有执行git merge或测试push。覆盖旧published merge保留、新merge拒绝、新branch无遗漏、多ref末项拒绝、人工MERGE_HEAD拒绝和真实PR head/synthetic区别。原sandbox和结果保留；不运行CK3、desktop、源码全测或主仓历史改写。

## 本机实际安装

2026-10-07。安装器已作为 `tools/install_git_linear_history_hooks.py` 保存在仓库，默认只显示计划。Root使用本次已验证的Python执行 `--repo C:/workspace/ck3_eternal_recurrence --execute`，实际写入三个hooks并读回repo-local `core.hooksPath`。原active hooks不存在，没有覆盖其他hook；[实际安装读回](C:/workspace/ck3-upgrade-20261007/resume-root-02/linear-guard-local-hooks-actual-install-readback-01.json)保留路径与事实。配置和hooks属于本机，不自动外推到其他clone；其他机器由同一安装器显式登记。

## 2026-10-07：实际普通push与首次exact CI闭合

Root已采用guard/CI/文档，并将原安装器按相同字节保存为`tools/install_git_linear_history_hooks.py`；本机三个hook实际安装及core.hooksPath读回见上节。原提交`9d562…`经过正常fetch/rebase成为 **`fd282d12f95f1abd6c85919229702783fd55ddf4`**，随后普通push exit0，master clean。该次pre-push实际输出 `no new merge commits (14f07ade00e9ad359da3aa6af3642592ede3f48d..fd282d12f95f1abd6c85919229702783fd55ddf4)`；没有force或历史改写。其唯一parent为`14f07ade00e9ad359da3aa6af3642592ede3f48d`，由本机exact `git rev-list --parents -n 1`独立读回。

同一exact SHA的新 [Linear history run37586770229](https://github.com/XenoAmess/ck3_eternal_recurrence/actions/runs/37586770229)，event=push、attempt1，07:20:58 UTC创建、07:21:33 UTC终态 **completed/success**。实际唯一job/check名 **No new merge commits**，job112678600804，07:21:00→07:21:33 UTC completed/success；`Check actual introduced commits`步骤success。[actual job](https://github.com/XenoAmess/ck3_eternal_recurrence/actions/runs/37586770229/job/112678600804)。本观察只查该exact workflow一次终态及同run job详情；未重跑，也未查询旧checks或其他CI结果。

正常push只有原CLA/signed规则的已有admin-bypass提示；新master线性ruleset24634448保持无bypass，未发生其违规。实际服务器设置、sandbox拒绝证据和本次正常single-parent push分别记账，没有制造merge/test push。[本次薄证据](C:/workspace/ck3-upgrade-20261007/linear-history-exact-ci-observer-write-diagnostic-01/LINEAR-GUARD-ACTUAL-PUSH-CI-READY-01.json)保存exact parent与GitHub原始响应pins。此追加仅记录已发生的push/CI，不授其他workflow、游戏或产品验收信用。
