# CLA 与轻量签署检查器

## 目标与边界

本仓库使用按 PR 签署的 Contributor License Agreement。目标是留下明确、可复核且与具体贡献绑定的授权记录，同时避免运行
外部 CLA 服务或维护额外账号与数据库。

权威文件：

- 法律文本：`CLA.md`，当前版本 `1.2`；
- 贡献流程：`CONTRIBUTING.md`；
- 机器配置：`.github/cla-config.json`；
- 检查器：`tools/cla_check.py`；
- Actions 入口：`.github/workflows/cla.yml`；
- 必需提交状态：`CLA / signed`。

## 为什么采用按 PR 签署

签署证据是贡献者本人在 PR 下发表的完全一致声明。GitHub 公开保存账号、正文、时间戳、评论 URL、PR 和关联提交；机器人只读取
这些既有记录并报告结果，不需要：

- 外部 CLA SaaS 或 GitHub App；
- Gist、签名分支、数据库或对象存储；
- 个人访问令牌；
- Web 服务、容器或常驻进程。

代价是贡献者每个 PR 都要签一次。对于当前贡献规模，这是比维护跨 PR 身份数据库更小、更透明的操作成本。

## 判定规则

检查器读取 PR 作者、PR commits API 和普通 issue comments API：

1. PR 作者必须签署；
2. 配置开启 `require_commit_authors` 时，每个能映射到 GitHub 账号的提交作者也必须签署；
3. `Co-authored-by` 中的 GitHub noreply 地址会映射为对应账号；无法映射的作者会停止自动通过并请求人工复核；
4. GitHub Bot 账号和配置中的明确豁免账号不要求签署；
5. 每个待签账号必须用自己的账号发表正文完全等于 `acceptance_statement` 的评论；
6. 评论被编辑或删除时会重新检查；
7. 维护者核验线下/企业签名或无法映射作者后，可添加 `cla:manual` 标签作为显式人工覆盖。

人工覆盖是紧急出口，不应替代正常电子签署。标签变更会重新运行检查并在机器人评论中公开记录结果。

## Actions 与权限

工作流使用 `pull_request_target`，因为 fork PR 的普通 `pull_request` token 不能写评论或提交状态。它只检出默认分支上的四个受信文件，
绝不检出、构建、导入或执行 PR head。`issue_comment` 事件用于在签署评论创建、编辑或删除后立即复核。

最小 `GITHUB_TOKEN` 权限为：

- `contents: read`：读取默认分支检查器；
- `pull-requests: write`：读取 PR 与提交作者，并创建或更新一条带隐藏 marker 的机器人评论；
- `statuses: write`：在 PR head SHA 上写入 `CLA / signed`。

不用仓库 secret。第三方 action 只有按完整 commit SHA 固定的官方 `actions/checkout`。

GitHub 将 `issue_comment` 和 `pull_request_target` 工作流关联到默认分支 SHA，而非 PR head；因此检查器通过 commit statuses API 明确把
结果写到 PR head SHA。Bot 评论中的 CLA 链接则固定到本次实际检出的受信默认分支 commit，使签署版本可以永久复核。
分支保护应把 `CLA / signed` 设为 `master` 的必需状态。

`pull_request_target` 是高权限事件。仓库的 Actions event policy 必须允许它；任何后续修改都不得加入 PR head checkout、PR artifact
下载或对 PR 内容的代码执行。GitHub 的官方安全说明：
<https://docs.github.com/en/actions/reference/security/securely-using-pull_request_target>。

## 运行与故障处理

本地纯测试：

```text
py tools/test_cla_check.py
```

线上重查：Actions → `CLA bot` → Run workflow，输入 PR 编号。常见情况：

- **缺签名**：按机器人给出的精确文本逐人评论；
- **无法映射的提交作者**：让对应作者使用关联 GitHub 邮箱重新提交，或由维护者核验后添加 `cla:manual`；
- **机器人评论没有刷新**：手动 dispatch；
- **状态一直 Expected**：确认 Actions 已启用且 event policy 允许 `pull_request_target`；
- **API 权限错误**：检查 workflow 顶层四项 permissions，禁止改用 PAT 掩盖配置问题。

## 升级 CLA

实质修改 CLA 时必须同时：

1. 提升 `CLA.md` 的版本与生效日期；
2. 更新 `.github/cla-config.json` 的 `version` 和 `acceptance_statement`；
3. 更新 `CONTRIBUTING.md` 中供复制的签署语句；
4. 更新测试向量；
5. 重新部署后检查一个测试 PR 的缺签、签署、删除签署和人工覆盖四条路径。

按 PR 签署意味着旧评论不会自动授权新 PR，也不会被新版协议追溯替换。

## 法律文本来源与审阅边界

CLA 参考了 Harmony Contributor License Agreement 1.0 的结构与授权边界，并针对本仓库的代码、文档、翻译和媒体贡献采用统一文本。
它不是版权转让。涉及特定司法辖区、未成年人、雇佣成果或企业批量贡献时，维护者和贡献者仍应按需取得专业法律意见。
