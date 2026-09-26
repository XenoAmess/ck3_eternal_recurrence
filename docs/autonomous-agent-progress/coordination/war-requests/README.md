# 战争需求的 Git 文件通道

本目录让非战争执行者和战争维护者通过仓库的普通提交、PR 与 `master` 交换具体需求。任务总线可以提醒本机执行者，但不承担跨机器交付。当前实际请求见 [`requests/WAR-INPUT-R0244-20260927.json`](requests/WAR-INPUT-R0244-20260927.json)。

## 文件与写入者

| 路径 | 写入者 | 含义 |
| --- | --- | --- |
| `requests/<id>.json` | 发现缺口的一方 | 不可变的输入帧、实际失败、期望合同、来源版本与证据哈希；合入后如有修正，另加带 `supersedes` 的请求 |
| `responses/<id>.json` | 认领的维护者 | `claimed`、`delivered` 或 `blocked`；记录负责人、接口/源码提交、兼容性和验证证据。同一响应文件仅由该维护者更新 |
| `verifications/<id>.json` | 原请求消费方 | 在交付进入 `master` 后，以匹配候选和真实结果写 `passed` 或 `failed`；失败记录新缺口，不把静态检查当实机通过 |

三个目录按相同 `<id>` 关联，互不要求同时创建。读取 `master` 时：只有 request 是待认领；response 为 `claimed` 是在途；`delivered` 且没有 `passed` verification 是待消费；`blocked` 或 `failed` 保留具体阻点。不能通过修改请求中的状态字段伪造完成。只用 `rg --files docs/autonomous-agent-progress/coordination/war-requests` 即可发现文件，不维护人工候选数量索引。

响应 JSON 使用 `schema: "xar.g2.cross-team-war-response.v1"`，至少包含同一 `request_id`、`status`、`maintainer` 与 `updated_at_utc`。`delivered` 时还要有 `source_pr`、`master_commit`、`interface_contract`、`checks`、`live_evidence` 和 `limitations`；未实机验证写明 `live_evidence: null`，不能填一个预测结果。复验 JSON 使用 `schema: "xar.g2.cross-team-war-verification.v1"`，至少包含 `request_id`、`status`、`consumed_master_commit`、`candidate_pair_sha256`、`run_id`、`formal_report_sha256`、`observed_result` 与 `remaining_blocker`。`passed` 必须指向真实匹配运行；失败仍保留失败报告。

## 一次交接

1. 请求方从失败的正式报告提取最小可复现帧，写 request 并附报告 SHA、源 commit、EXE/DLL 版本、actor/episode、当前日期、期望行为和实际结果；用独立 PR 线性合入。绝对本机路径只作原始证据定位，**请求正文必须包含跨机器可读的最小输入**。大型存档、游戏本体与 DLL 不进 Git；如维护者需要完整配对，另约定已验证的资产传输途径并在 response 中记录，不能把本机路径当远端可用。
2. 战争维护者从 `master` 读取 request，建立自己的隔离分支；以独立 response PR 表示认领或说明确切阻点。交付时更新自己的 response，写实际源码/接口提交、查询或策略入口、同帧与资源合同、聚焦检查及实机证据边界。不能用 `claimed` 或 CI 通过替代结果。
3. 非战争消费方仅在新交付进入 `master`、通过受影响验证且有合法配对后消费；把候选版本、正式动作/读回、下一 turn、恢复及失败记录进 verification。`passed` 只关闭 request 指明的缺口，不自动提高 G2 里程碑或 Robert 持久日期。

请求、响应和复验都走普通 PR、rebase-only 集成、exact master 检查及临时分支/worktree 清理。当前未核实战争维护者的具体账号，因此首条请求的 `assignee` 为 `null`；维护者认领时在自己的 response 中填身份，非战争执行者不代签。
