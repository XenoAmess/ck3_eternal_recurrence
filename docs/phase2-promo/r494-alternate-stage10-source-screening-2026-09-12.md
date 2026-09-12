# R494 Stage 10 替代来源离线筛选（2026-09-12）

## 目的与结论

R494 证明旧玩家经理 `29037` 会在原 source 后第 88 天被 exact-build 原版强制退休事件淘汰。替代路线不回到 D+299 重放 104 天，而是复用 R494 在事件前自动保存的 `1068.1.1` 单玩家 checkpoint，先切换到另一个已经处于 B1 固定尾链的玩家经理。

离线 discovery 共找到 18 个仍带 B1 manager serial 的 root，其中 11 个同时满足：角色存活、天朝直属经理拓扑成立、至少一名直属有地封臣、当前 B1 subject 列表与 processing 列表数量相等、全部引用属于当前 owner/cycle/case exact tuple 且状态统一为 `7`。下一次 source-capture 选择经理 **`27181`**：

- 即时上级 `32904`，`k_henan`、tier 4、`celestial_government`，五名直属有地封臣；
- B1 `cycle/case=5/5`，subject、processing、exact 均为 5，五个 case 均为 `state=7 / active=1 / roster=1`；
- 五个 `zg361b1.122` 已在原生 scheduled-event 队列中排到 `1068.1.31`，距 checkpoint 30 天；
- exact B1 域不包含已知会在 23 天后被 `.0630` 移除官职的 `29037`；切换玩家不会要求绕过该原版事件；
- 家族在存档中为 `house_aspiration_status=powerful`，但这不等于已经证明 `is_dominant_family=yes`，因此不把它写成免疫强制退休的保证。

该候选只获得 **offline prelaunch qualified**，不等于 live source READY。新的原生玩家切换必须在零游戏时间推进下重新确认 `27181 -> 32904`、玩家唯一性、tier/government/game rule，并由 MCP 原生保存；随后新的 Stage 10 receipt 还要绑定本页全部输入哈希。未完成这些步骤前 P1 仍为 `8/9`，P2 继续 `LOCKED`。

## 通用 discovery 资产

[`inspect_ck3_save_character_scope.py`](../../tools/inspect_ck3_save_character_scope.py) 新增 `--discover-root-variable`，与既有 `--root-character-id` 互斥。新输出 kind 为 `ck3_character_scope_discovery_offline_v1`，枚举所有带指定变量的 Character root，并按调用者请求读取 root 变量、持久列表和列表引用角色的变量。它仍只读、hash-bound、路径无关，不依赖操作者、机器、账号或 CK3 轮次。

focused unittest normal/optimized 各 `2/2` GREEN，`py_compile` 与 `git diff --check` GREEN；没有运行全量测试或启动 CK3。

## 冻结证据

运行目录：

`Z:\ck3_mod_rewrite\_runtime\p1-stage10-r494-alternate-source-screening-20260912`

| artifact | SHA-256 | 说明 |
|---|---|---|
| R494 `live-state/profile/last_save.ck3` | `00D4118249BF4BD94E80F6D5A69E95E559817724F2E03B4654115B30B5885A1F` | 65,234,462 bytes，`SAV0101` |
| `r494-last-save-melted.ck3` | `4A8F93FA6AF9CC5B94C3D7DE2EBC3B3A7537E867A39A73F2227D9DB0F8F3B1E9` | `1068.1.1` exact melted input |
| `r494-last-save-topology.json` | `3F8EA14BACC7CED19F8E8FFC27AE21BDAD55BF832C392ABCA0740F8AB5830A69` | single-player `29037`，71 个天朝经理拓扑候选 |
| `r494-last-save-b1-manager-discovery.json` | `5F79A4236D69FF3B06F98CD5476C230D4B35CB011FBF1E8A947DDFFC1C3F4289` | 18 个 B1 root 与其引用域 |
| `r494-last-save-qualified-summary.json` | `4543F32B33DB127EAE92B98BBA19F1353F7E14DED54F224052A654975637F525` | 11 个完全一致候选 |
| `scheduled-27181.json` | `7763E629412AB029FE3871E3F7BF04EA4471C0B7B0C261D86B930553EB3848C7` | 五个 `.122 +30d` |

`r494-last-save-qualified-summary.json` 是本次候选排序的消费层诊断，不作为新 schema 或下游合同。其一次性原因是当前只需要从这一份冻结 lineage 选出一个替代经理；影响面仅限下一次 source-capture activation。可复用的 save 解析和多 root 发现已经迁入通用 CLI。若第二份 lineage 再次需要自动合并 topology、exact tuple 与 scheduled-event 报告，必须在再次启动 CK3 前把合并逻辑提升为参数化 consumer；迁移期限就是第二次复用需求出现时，不能复制该诊断脚本。

## 原版风险边界

exact-build `celestial_retirement_law_5` 设置 `celestial_retirement_age_5`；`tgp_is_above_retirement_age_trigger` 对该档位返回 `always=yes`。因此所有 governor 都可能通过 `governor_removal_interaction` 被移除，不能用候选年龄证明安全。原版 interaction 的 AI target 是 vassals，base `-10`，并受同家族、对立、governor efficiency、派系、忠诚、联盟和 opinion 修正；当前公共只读接口没有发布任意候选的完整 AI 分值。

本次只利用已经发生的确定事实缩短风险窗：R494 的第一次 `.0630` 精确指向 `29037`，R494 自动存档到该事件只余 23 天；候选 `27181` 的 B1 exact 域不含 `29037`。这不能保证后续绝无新原版中断，所以新的 action 仍保留通用 fail-closed 行为；如果新来源再被场景失效事件打断，应淘汰该来源并停止，不能用循环试错替代可观察输入。

本包修改了通用离线 CLI/output kind，属于接口与数据格式增量；根仓 commit+push 后必须立即同步 open_kaishek 兼容说明。公共 Operator MCP、DLL、游戏文件、启动配置和加载顺序没有变化。
