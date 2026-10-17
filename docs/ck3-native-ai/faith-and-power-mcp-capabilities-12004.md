# 圣地规划 MCP 能力与实际离线资格（1.20.0.4）

2026-10-17。`machine_id: 4-8e1c2f1861`；机器身份来自当次
`py tools/ck3_live_run_id.py machine`。源码审计与本机部署观察为
`2026-10-17T05:27Z–05:36Z`，最终入口补充验证时间为
`2026-10-17T05:37:01.445207+00:00`。本包没有启动 CK3、操作桌面、
执行 native 代码或拍摄。研究机制见[圣地研究](faith-and-power-holy-sites-12004.md)，
原版资源 SHA 见[来源清单](evidence/faith-and-power-holy-sites-12004/source-manifest.json)。

## 当前交付

生产 `create_server` 新增只读工具：

```text
ck3_query_holy_site_planning_knowledge_v1(action="adopt", ck3_build="1.20.0.4")
ck3_query_holy_site_planning_knowledge_v1(action="enshrine_relic")
ck3_query_holy_site_planning_knowledge_v1(action="remove_relic")
```

实现为 `ck3_autonomous_player/src/xar_autoplayer/holy_site_planning_knowledge.py`，
注册在既有 `bridge/mcp_server.py`。它向现有游玩智能体提供候选来源、脚本条件、
成本分支、所需实时观测和操作后验，逐项绑定资源路径、行号、SHA 与来源提交
`074429b3f6d9352a3cf4c5671725fee2f41267ba`。

返回 `qualification=source_reviewed_static`；`requires_ck3=false`、
`state_observed=false`、`native_legality=null`、`action_ready=false`。
这些字段表示本工具只提供版本化研究输入，不对当前局面求值，也不执行动作。
异版本请求返回 `unsupported_build`，不会把 0.4 规则授予 1.20.1。
这是 **static-ready**，不能算 native/live-ready、业务验收或已拍素材。
当前聊天会话没有通过这项测试自动获得新安装的客户端工具；测试验证的是生产服务器注册。

采用知识区分 GUI 候选生产、列表过滤、决议脚本条件与尚未闭合的最终原生许可：

- 候选来自 `actor.every_realm_county → every_county_holy_site`，不是朝圣的当前 Faith 圣地表。
- 兼容条件对站点所有关联 Faith 求 OR；不能只选一教比较。
- `actor.rite` 参数、Faith main Rite 与个人信条各自保留来源；缺少参数观测不算 false。
- 基准 1000 虔诚、免费额度和五年脚本冷却不替代实际费用读回。
- 默认普通/主要等级、实例/库存保留、Active 与真实受益对象仍是待实读问题。

**采用入口有实际影响的限制：** `adopt_holy_site_decision` 在原版
[第 482 行](https://github.com/jesec/ck3-mod-base/blob/074429b3f6d9352a3cf4c5671725fee2f41267ba/base/game/common/decisions/50_holy_site_decisions.txt#L482)
声明 `is_invisible=yes`，文件 SHA 为
`80ad6a6045bdafdce514cbccf59a9cd1370eaef6749d510adcec759468065fb4`。
既有 keyed 决议接口要求真实唯一列表行，不能据接口名字假定可到达这个隐藏动作。
知识返回明确保留 `entrypoint.is_invisible=true` 与
`keyed_decision_list_reachability_verified=false`；下一步须定位原版 HolySite 窗口／选择器调用者。

供奉的已审脚本子规则同时要求控制资格和 actor Faith 关联该站点；移除子规则仅声明控制资格。
这项区别不证明引擎完整许可，也不承诺供奉奖励。两者都要求读取同一 artifact、owner、
inventory、slot、认可集合及真实费用，随后分别验证 ACK 和实际后态。

## 现有原生能力与下一施工入口

| 生产入口 | 可复用内容与边界 |
| --- | --- |
| `ck3_query_player_religion_context_v1` → Driver → `query-player-religion-context-v1` mailbox | 当前 actor/Rite/Faith/Religion 和独立宗教资源。此只读 handler 直接调用 Driver，没有新增 Service hop。源码有 exact 12004 身份验证；当前机器 live 未验。 |
| context 的 pilgrimage siblings | 原生当前 Faith 圣地 ID、Title/Province 对应与朝圣候选。不能代替领地内可采用圣地、圣物库存、类型或等级。 |
| doctrine/Tenet/governance/hostility 既有查询 | 可为后续合法性研究供独立输入；字段与测试存在不证明本机部署或读取成功。 |
| `ck3_inspect_gui_window_tree_v1` | 只开放 topbar、decisions/detail、military、courtier/Vivhite、death 等固定根。没有 religion/HolySite 根；合同明确不提供 rendered text、selected state、tooltip 或 business model。 |
| `ck3_query/select_ingame_decision_item_v1` 与 generic confirm outcome | 真实决议列表行的查询／选择和 UI 结果验证；不能代替隐藏采用选择器或宗教业务后态。没有任意原生 GUI Invoke。 |

下一项 native 施工应沿用现有 Driver/wire/拥有线程 mailbox，先恢复本机 12004 runtime，
再核对并复用既有朝圣链的 HolySite 引用解析，扩展选中站点和 Faith 关联的只读口；
旧路径仍须当前 12004 字节与调用者资格，不能因已有名称就当作本轮已闭合。
候选、实际原版调用者、过滤与最终许可分别定位；不要为拍片另建自动玩家。
供奉／移除须先闭合原版 artifact/site picker 和最终 owner/slot 校验，再实现 typed 单次提交与独立后态。
未发现完整 ABI 前不能用猜测地址、schema 默认字段或 ACK 冒称完成。

本机路径观察出处为外置 `local-deployment-probe.json`（观察时间
`2026-10-17T05:31:07.410600+00:00`）：仓库 `tools/.venv/Scripts/python.exe`
能实际导入生产 MCP server 并执行 `--help`；系统 `py` 缺 `pydantic`。
当前用户尚无标准 per-account venv/native build 或 CK3/operator MCP 注册。
发现的 UUII 历史 DLL 的宗教 flags 均 OFF，不具本轮资格；其他机器文档的
`C:/cbr3`、`C:/csr12`、`C:/workspace/ck3-common-runtime` 不能作为本机部署事实。

## 验证与原始回包

第一批在 `2026-10-17T05:34:33.798343+00:00` 通过六项聚焦测试，包括真正
`mcp.Client(create_server(_NoGameDriver()))` 的 `list_tools` 与七次 `call_tool`。
三种 action 成功，异版本不可用，非法 action、额外 actor ID 和伪造 native-legality 参数被拒。
测试 backend 的 capabilities/snapshot/action/wait 均在调用时抛错；未使用预计算 native DTO。

隐藏入口事实补充后，只运行一次新增的针对性 MCP 测试，通过真实 `call_tool(action="adopt")`
核对隐藏标志、列表可达性未知、精确第 482 行来源及未授 native 许可；未重复不变部分。
测试文件自身不写运行时回执；外置 runner 收集实际 SDK 返回和源文件 hashes。

完整回包保存在当前机器的
`C:/workspace/ck3-faith-and-power-20261017/capability-audit/`，Git 只保留本摘要与来源：

| 原件 | bytes | SHA-256 |
| --- | ---: | --- |
| `holy-site-planning-mcp-qualification.json`，首次六项 | 59,980 | `ce8284afd67b593229de9031032fe0a86bb2672ba52ceee26c27c665c86ae4d8` |
| `holy-site-planning-mcp-qualification-a02.json`，入口补充单项 | 24,399 | `107e1c2c20b50b35eaa37d03d8dd24906f9af3e186831449ea091f564cc28a78` |

旧原件保持原字节，a02 单独绑定最终源码；旧六项通过不追认为新源码的全量重跑。
同目录完整能力审计为 `capability-audit.md`。a02 闭场目录总量为 144,802 B，
低于本 lane 的 150 KB 预算；原件按[通用存储策略](../storage-retention-policy.md)
随本轮工作包复核，不声明永久保留。以上资格均为离线研究工具资格，拍摄仍未执行。
