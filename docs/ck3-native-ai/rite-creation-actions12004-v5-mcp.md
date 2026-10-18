# 1.20.0.4 教改草案的 MCP 执行合同

本能力复用 `RiteCreationWindow`、原版完整 Can、原确认弹窗和现有 NativeDriver。
它服务一般教改规划；一期双向采用圣地使用相同入口。
既有[教改查询](religion-reform12002-query-context.md)和
[创建分支条件](religion-reform12003-current-draft-creation-terms.md)的旧版本实测仍按原版本保留。
本包精确绑定 1.20.0.4 / EXE SHA-256 `98702f88a547cde2eaf29a85f93b85f68ee4cf8148336a4f7afaeb75319dd518`，
来源为版本 registry 与本轮 exact-build 合同，不在这里重新哈希 EXE。

现有 MCP server 增加三个默认关闭的通用入口：

| 入口 | 作用 |
|---|---|
| `ck3_query_player_rite_creation_action_context_v1` | 当前草案、完整 Can、报价、实际创建分支、原弹窗阶段及原生身份 token；不打开草案 |
| `ck3_execute_player_rite_creation_action_v1` | 有限 operation：打开创建或编辑、选择核心信条、选择教义、五种名称字段、打开确认弹窗、一次最终确认 |
| `ck3_collect_player_rite_creation_action_result_v1` | 只等待或读取原请求结果；不重发动作 |

显式 opt-in 是 `--private-player-rite-creation-actions`，生产 host 及其 child 都转发。
Driver 同时要求实际 DLL 发布 `player_rite_creation_action_v1`；源码中存在 reader 或旧 DLL 验收不抵当前 capability。
公开参数只包含当前 source Rite 的完整 ID 断言和有限 definition keys。
玩家、Faith、连接代际和原生帧从当前状态取得；不接受任意角色、指针、RVA、GUI 路径或调用者提供的 Can。

规划器依次执行：

1. 读取当前 actor / Rite / Faith / Religion / main Rite 及原生权限。管理圣地权限与创建新信仰权限分别判断。
2. 打开原创建草案；通过真实核心信条或教义候选及完整 CanPick 选择，读回所选 key。名称字段限 name、adjective、adherent、adherent_plural、description。
3. 查询实际分支和价格；`create_faith`、`create_rite`、`edit_rite` 是原生结果，expected kind 仅断言，不能强制切换分支。
4. `prepare_confirmation` 使用刚观察的原生 token，只打开原弹窗。它不等于命令提交。
5. 再读实际 active modal、同一草案窗口、原 modal Can 和独立完整 Can，并取得新 token。最终确认使用 Driver 自己缓存的这一份实际原生响应。
6. `confirm_once` 先将 episode + actor + source Rite 的意图 claim 排他写盘并 fsync，再经原 `_execute_primitive_step` 发送一次。换 public/native revision、token、连接或 request ID 不产生重试资格。
7. 独立读取新身份、当前与主要礼仪的核心/参数、方向性敌对度、虔诚钱包和目标圣地的原生采用许可。

原生 token 的 payload 生产与消费链须由 C++ exact-build provider 闭合，Python 不对猜测的 DTO 或包含指针的内存自造“完整草案哈希”。
原 Create/Edit modal 只借用窗口，Accept 时才复制草案；不能把弹窗本身描述为不可变草案副本。
原 Confirm `C46380` 包含 Accept 和原关闭处理，不能只调用 Accept 虚函数。

结果未知时保留 claim 和原始结果位置。collect 只收原请求，对未知结果保留 claim，不推断当前许可。
明确的未提交结果分别处理：现有 primitive 在 endpoint.send 前抛出的专用 revision/capability 错误，或完整匹配原生响应明确未尝试 dispatch 且不可能已经 queue 时，先持久保存原意图及安全拒绝原因，再释放该未执行意图。
这允许重新观察后提出新的合法请求，不触发自动重发；超时、异常、畸形响应和任何可能已入队的结果继续保留未知 claim。
原生 ACK、队列可能已接收、实际创建身份和采用成功分别记录。
`evaluate_independent_poststate_v1` 使用现有实际 context/snapshot reader 的前后结果，分别报告身份模式、主要礼仪关系和虔诚原始差额与报价的数值比较。
缺钱包保持 null；同一 Faith 下新 Rite 不算新 Faith；IDs 不变不能单独证明编辑内容生效。
该比较不证明核心参数、其他资源变化、宣称的净收益或下一动作许可。

本轮验证记录：machine_id `4-8e1c2f1861`，2026-10-18，外置 `RITE-ADAPTER-VALIDATION-*`。
十一项聚焦 Python 合同测试通过真实 NativeDriver primitive、现有验收 case 准入与实际 MCP；其中一项经实际 MCP Client/server，两次成功响应和两次拒绝。
Native I/O 使用明确标注的合成 endpoint，不是新编 C++ packet，也不是实机资格。
测试覆盖 public/native 不同序号、禁止参数、unknown/null 保留、claim 先 fsync、重启防重复、只收迟到结果、身份/钱包分别判断。
C++ 资格、SDK 构建、当前部署和双向教改实拍需各自后继实际回执；本记录没有授予这些通过事实。

2026-10-18T07:42:59Z后继，同机窄补齐现有两个只读能力的公共case路由：`ck3_query_player_religion_draft_resource_costs_v1` 与 `ck3_query_player_religion_hostility_v1`。case allowlist、host CLI及child转发、Driver opt-in与实际MCP工具发现保持一致；只开放显式声明者。两项焦点检查通过，包含上述四种声明组合及缺少required声明的拒绝，并修复旧手工Selection测试夹具未设置新增默认关闭属性的问题。候选补丁SHA-256 `97b02e4c42ce9d5a4355b61ef11d7854812e3e0ddb27bd4c5b2181c973dfe2fb`，Root核对主树应用字节与已测候选逐文件相同，没有重跑旧11项或十分钟整套检查。这是公共路由资格，不是费用、敌对度实机读回。

原[e8 CI失败](https://github.com/XenoAmess/ck3_eternal_recurrence/actions/runs/39107154883/job/117615400953#step:70:603)与[a5 CI失败](https://github.com/XenoAmess/ck3_eternal_recurrence/actions/runs/39107346352/job/117615962153#step:70:603)保留，各为同一旧手工夹具属性缺失；后继提交按自己的自然CI结果记录，不能追改原失败。
