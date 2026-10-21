# R0233：第二驻点准备失败、普通存档与正常退出

machine_id: `desktop-3fevhd2-1c74096080`。本页以 2026-10-21T23:13:02.285451Z 的 R0233 owner 闭场原件为事实截止点；2026-10-22 日报仅增加本页入口。证据小包和逐 member 来源见 [source-index.json](evidence/episode04-r0233-second-site-20261021/source-index.json)。它们供游玩智能体显式参考，普通 planner 不会自动加载本专题。

R0233 没有完成第二个 B 阳性驻点。该场新增 29 个实际/请求自然日、1 次 Move，新增 rich query、Arm、camera Start 均为 0。累计 lineage 为 143 个实际/请求日、8 次 rich query、2 次 Move；这些累计数字包含旧场，不能当作本场新观测。第二站选择省份 2623；末帧军队 18 已到该省，route 为 `complete_empty`，但没有新驻点业务资格。原 R0232 首站阳性是独立旧观测，没有复制进 R0233 的 `site_observations`。

薄热接保留同一原 Game，但不是同一原 CaseClient。它在退出预留检查处得到 `ValueError: Original normal Quit reserve reached`，状态为 `SAME_GAME_HOT_FAILURE_PRESERVED_NO_REPLAY`，因此没有重放旧动作、借旧 rich 结果制造新 revision，或绕过退出预留继续取样。原 public 返回 2、热接返回 1 是真实失败，正常收尾不把它们改成 0。

后继规划应把“抵达候选省份”“准备通过”“fresh 驻点 before-rich/headroom”“实际单日后验”分开。旧 rich 只能提供调度线索，不能证明当前 stock 或 headroom；到港、换省或经过若干天也不自动证明负补给或增长。下一窗口应在动作前核对实际剩余时间和准备资格，为原 owner 的 Save、GUI Quit 留出时间；未知提交结果不重投。本页没有授予新窗口、第二站阳性或新动作额度。

普通 Save 已有原生 producer 物化与同 actor/bridge PID/connection generation/pipe 的独立 before/after 括接；最终另有独立同 handle 文件 rehash。原 proof 中的 `consumer_rehashed_file:false` 保留，独立 rehash 不反改它。ordinary snapshot 的 episode 字段仍按 missing 表示保存，checkpoint 则是明确的 null；legacy one-life driver 的 `save_binding_mismatch/unconfirmed` 仍保留，不能把普通存档成功改写成 one-life 身份通过。

23:13:02Z owner 闭场确认正常 GUI、原持有 OS 进程退出 0、native 退出 0、host 原 wait 0，keeper/allocator 退出 0，screen CAS 已释放，全部 writer 归零。最终存档日期 raw 为 53150328，actor 31254，Army 18 在省份 2623。当前 canonical Save 为 75,169,786 字节，SHA-256 `bf55ebb267fafad2e5a884211d980e7466ade41261c2393045b8c075641e709a`。旧 `d1b6…` 原路径已被后续正常 Save 覆写，但实际 `autosave_1.ck3` 仍匹配该旧 SHA；不能称旧二进制全部不可读取。本页只归档小回执，不复制或重新读取这些 Save 大文件。

本轮还补齐了战争通知的可复用来源。原版 `window_war_declared_overview.gui` 的 header close 和底部 `dismiss`（`WAR_DECLARED_OVERVIEW_DISMISS`）均调用 `WarDeclaredOverviewWindow.Close`，只关闭通知，没有接受战争、应战或付款 effect。公共 query/close 接口已存在；本轮 ticket 8 的单次 close 是 `verification_pending/action_credit:false`，没有因 pending 重投。后续独立 ticket 9 query 的 hidden/effective false 才证明窗口已消失。

UI 通知关闭不等于战争处理完成。war 31 的防御、title 2217/objective 2610，以及 war 4 的攻击方处境与 −95 战分仍应交给完整 planner，结合当时原生兵力、军费、雇佣应急与领土风险判断；不能把 dismiss 当作已应战。GUI 来源 SHA 与实际 query/post 原件均在小包索引中，此处没有创建新的通用已部署策略或实机能力。

本场 `business_pass:false`，未授兵员增长、第二站 B、完整 B、full R08、one-life 或未来安全。既有正式镜头 9/11、B 1/2 不增加；研究 10/14、业务 7/11、ABC 0/3 保持原计数。原失败、旧主题与当时原件保持原样。
