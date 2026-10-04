# R6 验收草稿补充（二）：进度、并发配置与 D+2 边界

本补充是一份新的外置候选，供最终报告收口时引用。原 795 件草稿、7 件 D+2 补充和 I3b 独立审查包均保持原样。R6 当前仍运行且暂停；正常退出、SDK 关闭、屏幕租约释放和源冻结释放均为 **PENDING**。本补充不将整体改为 GREEN，也不把将来的 C2 操作或费用结算预填为成功。

根代理给出的 **60% 是综合开发估算，非测试通过率**。时间节点同样是预估：

| 日期 | 预估交付 |
| --- | --- |
| 10 月 5 日 | 落地本轮验收报告，交付基础礼仪与修习阶段版本 |
| 10 月 6 日 | 正式统一分裂首轮完整验收及修复 |
| 10 月 7—8 日 | 领袖建立、对立学统、同意与拒绝、保存重载 |
| 10 月 9 日 | 一期回归、可交付构建和总报告 |

朝代限制归二期。日期与工作范围来源为根代理消息，不是已完成的游戏验收事实。

本机 `C:/Users/Administrator/.codex/config.toml` 第 10—11 行实际包含 `[agents]` 和 `max_concurrent_threads_per_session = 64`；文件 271 字节，SHA-256 为 `1811b67906e96a3784b6786237a29db3c2bf5534ebf98cf6ce262883ddc7e051`。本补充只保留这一段及整体 hash，未复制其他配置。官方 [Configuration Reference](https://learn.chatgpt.com/docs/config-file/config-reference?translationFallback=ja-JP) 将该字段定义为并发 spawned-agent threads 上限，计数不含 primary，旧 `max_threads` 是别名。

当前会话工具指令仍声明 **4 个总并发槽，包含自身**。配置中的 64 与当前会话的 4 来自不同证据与计数口径；文件写入不能证明当前工具已采用新值。本轮未热重载、未重启会话、未做 64 并发试验，不能写“64 槽已运行”。

三项先前 root-tool-only 失败作以下精确说明：root0007 的非法闭式名 `codex_apps.ck3_query_native_snapshot` 在本地 `validate_request` 被拒绝，未 dispatch、未 SDK；`r6_native_action` 首个 helper 错读 instance key，后续新 6139... v2 修正且无 game side effect；`draft_v2` assertion 计数错误，目标文件未生成，v2b 后续成功。这些是根代理消息对工具结果的说明，原草稿的缺少回执事实保留，不制造本地 raw stderr 或 SDK 调用。

D+2 独立保存读回已经冻结，结果只限 `PASS_ACTUAL_D_PLUS2_OBSERVATION_ONLY`。请求推进一天，实际原生日期由 1066.9.15 变为 **1066.9.17**，raw date `53144328→53144376`，实际经过两日。相关存档 SHA 为 `97fe09b4d9ff9cfc59bfbeb4b9ff7bf795538cfa22c8fd07ac73c6dd2b61eee5`、90,494,024 字节，原件永久外置，不复制进此小包。

保存的 Faith 32/104 仍是 35+1 礼仪结构，两名实际 NPC 65856/65857 的派属和 actor 相关政治保护状态按该读回检查保存。朱子 native `head_of_rite` 自然变成 actor 31254，没有 C3 任命；两 Faith 的 HoF title 仍不存在。正常时间推进可改变人物、钱包和 native 礼仪领袖，不能要求所有世界数值完全静止，也不能从这个自然变化推断领袖系统通过。任何依赖现任 native HoR 的代表签署必须复核当前实际身份；另行提名的学者代表须明确独立制度政策。

存档 base Learning 为 14，fresh exact total Learning 没有可读值；旧资格记录 8/7/8 与 setup_before8 没有改写。根代理观察到资格夹具消失、正式决议可见，与当前 eligibility 一致，但不能独立证明 exact total=15，更不能把先前 qualification RED 改成成功。正式 C2 资源、决议、提案、赞拒、签署、迁移与实际费用结算的后续证据仍待根代理提供。

此前 whole error.log 达 100000 条 native 输出 cap；此后缺少日志行不能称运行无错。本文未读取当前游戏日志、未附加游戏、未操作屏幕、未调用 CI 或 Git。D+2 compact summary、自然 graph 变化、NPC 小投影与原索引保存在 `evidence/d-plus2/`；配置、当前会话和仅消息事实分开标明来源。
