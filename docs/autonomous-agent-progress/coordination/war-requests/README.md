# 战争需求的 Git 文件通道

本目录让非战争执行者和战争维护者通过仓库的普通提交、PR 与 `master` 交换具体需求。任务总线可以提醒本机执行者，但不承担跨机器交付。当前请求以 `requests/` 文件为准，其中 [`WAR-INPUT-R0244`](requests/WAR-INPUT-R0244-20260927.json) 和 [`Robert H2743 退战`](requests/WAR-ROBERT-H2743-EXIT-20260928.json) 均有独立响应；H2743 的[响应](responses/WAR-ROBERT-H2743-EXIT-20260928.json)还列出了待通过 OneDrive 精确传输的四类原始资产与 SHA-256。

## OneDrive/WAR 精确资产通道

项目所有者于 2026-09-28 授权两台机器此后在各自 OneDrive 根目录下的固定 `WAR/` 目录直接双向交互，发现需求、传输精确资产和回传校验回执，不再经用户逐次转述。**Git `master` 中的 request/response/verification 仍是任务与状态的权威记录**；OneDrive 目录名、同步提示或文件到达本身不代表请求已认领、交付或通过实机复验。

每个请求使用 `WAR/` 下独立子目录。传输前先从对应 request 和 Git evidence 冻结本次所需的相对目录、每个文件名、字节数和 SHA-256；发送方只放该清单中的文件，接收方只对该清单执行选择性同步或下载，并在本机逐文件复算大小与 SHA-256，保存带来源帧、实际路径、时间和结果的外置回执。接收方在请求子目录中新增约定的 ACK 或响应文件，不覆盖来件；Git 通道的 response 再引用它并明确实机证据边界。此前不得下载其他 OneDrive 文件的限制继续有效，不得为发现新需求而进入或下载无关目录内容；只读目录名与元数据检查可以用于定位新的 `WAR/` 来件。任何资产传输均不授权 CK3 启动、玩法动作或窗口接管。

CK3 实例与 operator MCP 按机器分别管理：每台机器最多一个 CK3，本机启动只依赖本机 live 状态、正式配对及实际共享资源条件；另一台机器运行 WAR31 本身不占用本机窗口。早期 H2660 全局窗口等待请求由 [`requests/WAR-WINDOW-ROBERT-H2660-PER-MACHINE-20260928.json`](requests/WAR-WINDOW-ROBERT-H2660-PER-MACHINE-20260928.json) 更正；原请求保留作历史记录。Git 传递更正与成果，不充当实时锁，也不允许调用另一台机器的 MCP。

## 文件与写入者

| 路径 | 写入者 | 含义 |
| --- | --- | --- |
| `requests/<id>.json` | 发现缺口的一方 | 不可变的输入帧、实际失败、期望合同、来源版本与证据哈希；合入后如有修正，另加带 `supersedes` 的请求 |
| `evidence/<id>.*.json` | 发现缺口的一方 | Git 内可读的正式失败报告、operator 回执或精确摘录；request 用仓库相对路径及 SHA-256 引用 |
| `responses/<id>.json` | 认领的维护者 | `claimed`、`delivered` 或 `blocked`；记录负责人、接口/源码提交、兼容性和验证证据。同一响应文件仅由该维护者更新 |
| `verifications/<id>.json` | 原请求消费方 | 在交付进入 `master` 后，以匹配候选和真实结果写 `passed` 或 `failed`；失败记录新缺口，不把静态检查当实机通过 |

三个目录按相同 `<id>` 关联，互不要求同时创建。读取 `master` 时：只有 request 是待认领；response 为 `claimed` 是在途；`delivered` 且没有 `passed` verification 是待消费；`blocked` 或 `failed` 保留具体阻点。不能通过修改请求中的状态字段伪造完成。只用 `rg --files docs/autonomous-agent-progress/coordination/war-requests` 即可发现文件，不维护人工候选数量索引。

响应 JSON 使用 `schema: "xar.g2.cross-team-war-response.v1"`，至少包含同一 `request_id`、`status`、`maintainer` 与 `updated_at_utc`。`delivered` 时还要有 `source_pr`、`master_commit`、`interface_contract`、`checks`、`live_evidence` 和 `limitations`；未实机验证写明 `live_evidence: null`，不能填一个预测结果。复验 JSON 使用 `schema: "xar.g2.cross-team-war-verification.v1"`，至少包含 `request_id`、`status`、`consumed_master_commit`、`candidate_pair_sha256`、`run_id`、`formal_report_sha256`、`observed_result` 与 `remaining_blocker`。`passed` 必须指向真实匹配运行；失败仍保留失败报告。

`evidence/*.json` 在 `.gitattributes` 中按原始字节保存，避免 Windows/Linux 换行转换破坏请求中的 SHA-256；文件内容仍是可直接解析的 JSON。请求与响应的普通 JSON 走仓库常规文本规则。

## 一次交接

1. 请求方从失败的正式报告提取最小可复现帧，写 request 并附报告 SHA、源 commit、EXE/DLL 版本、actor/episode、当前日期、期望行为和实际结果；把分析所需的失败报告或精确摘录放在同一 PR 的 `evidence/`。**仅在另一台机器 `git fetch` 后能读到全部请求和失败证据，才算需求传达。**首条 R0244 请求同时携带完整 44 KB 正式报告、operator 回执和配对身份清单；其中的 `Z:` 路径仅是报告生成时的历史字段，接收方不必访问该盘。大型存档、游戏本体与 DLL 不进 Git；若实机复验需要完整 save/driver/sidecar，另约定已验证的资产传输途径并在 response 中记录，不能把本机路径当远端可用。
2. 战争维护者从 `master` 读取 request，建立自己的隔离分支；以独立 response PR 表示认领或说明确切阻点。交付时更新自己的 response，写实际源码/接口提交、查询或策略入口、同帧与资源合同、聚焦检查及实机证据边界。不能用 `claimed` 或 CI 通过替代结果。
3. 非战争消费方仅在新交付进入 `master`、通过受影响验证且有合法配对后消费；把候选版本、正式动作/读回、下一 turn、恢复及失败记录进 verification。`passed` 只关闭 request 指明的缺口，不自动提高 G2 里程碑或 Robert 持久日期。

请求、响应和复验都走普通 PR、rebase-only 集成、exact master 检查及临时分支/worktree 清理。当前未核实战争维护者的具体账号，因此首条请求的 `assignee` 为 `null`；维护者认领时在自己的 response 中填身份，非战争执行者不代签。
