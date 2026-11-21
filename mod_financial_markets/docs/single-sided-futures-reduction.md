# 单边期货减仓：缺失scope比较与R0054失败

2026-11-21，machine_id: `4-8e1c2f1861`。本文区分实际失败、已采用源码、软件验证和后继实机；不提供旧账修复或动作重放授权。

R0054连续14日观察中，原SHORT231与close150的SELL232都有103分/gross103/fee1成交记录，但audit2为INCOMPLETE：新仓152引用native83888107悬空，原LONG150没有完成应有减仓。原archive、pipeline、audit2、run2/verify2及正常关场原件全部保留。存在成交记录不能替代抵押、仓位和现金权利完整，累计GUI仍4/6。[实际失败证据](../../docs/maintenance/evidence/2026-11-21-financial-markets-r0054-reduction-failure.json)。

独立原始字段核对确认：152名义short_margin103不是已入金证明，悬空预留的实际余额仍UNKNOWN；账户14353的98分冻结全部属于旧150，不能再覆盖新152的空头权利。玩家账户54可用8230→8255、冻结448→430，净增7只是跨14日的整体账户差，不能当作孤立两笔交易的利润或完整清算通过。

单边SELL close只准备sell_slice，不存在buy_slice。旧脚本在分摊和归档两处直接比较 `sell_slice != buy_slice`；真实引擎不会把“现存scope不等于缺失scope”当true，两个步骤因而被跳过。旧有限解释器使用Java对象与null的不相等，曾错误地让该路径通过；此前软件绿没有覆盖真实引擎语义。

最小修复先判断sell_slice存在，再明确处理buy_slice缺失的单边分支；仅在两个scope都存在时比较身份。分摊与归档两处同步，不新增现金、价格、深度、做市对手或结算规则。解释器将任一操作数缺失的scope等号/不等号都判false，并保留显式 `NOT exists` 分支语义。新增四项实际脚本回归覆盖缺失scope比较、真实挂SHORT后单边LONG close、单边SHORT close、同源双边close只分摊/归档一次。

定向6项检查操作退出0/30.3596988秒；受影响整类27项检查操作退出0/48.675108秒。完整金融验收操作退出0/260.3426878秒，其中原Maven wait0/259.0890075秒。616个不同方法全部通过，失败/错误/跳过均0，405个产品源在完整窗口内保持一致。两组定向检查有重叠，不与616相加；方法通过不等于全部模块重编或实际引擎通过。[软件证据](../../docs/maintenance/evidence/2026-11-21-financial-markets-single-close-software.json)。

R54已经生成的坏引用和原仓不会因加载新脚本自动修好。此修复不补写历史、不重新分摊已终态委托、不重放231/232。后继拟由完整、未含两张单的R52终档 `46061b6c7602347aab3a44625a8fe323a893218e932b13fc32eb1df2e86b0e98` 独立种子，采用既有saved_campaign后台和新的scenario命名空间建立验收fixture分支；场景合同仍待正式准入。这不是新原版书签世界、R54恢复、时间连续进展或删除/重置旧单。其普通GUI新动作和独立保存须重新核两边永久身份、原仓减少/终结、替代仓抵押、费用及完整权利图；相同数字ID也不能跨场景混为旧动作。R54作为失败原件保留。正常Game/Host/Job/keeper0和资源释放不替代该业务验收。

## R0055后继：只完成独立基线

`independent-seed19` 已从完整R52终档建立独立验收fixture分支，沿既有saved_campaign后台完成一份新同日SAVE。15401条完整记录、15315条App15投影及globals/news/PRIMARY均与声明种子一致；公共run0/verify0、有限case/boundary通过，Game/Host/Job/keeper/allocator及CAS15927资源释放已核。零新增自然日、零新业务，累计GUI仍4/6。

本场没有验证新SHORT或减仓，也未采用P1 receipt02；不是R54恢复、主线回滚、新书签世界或旧231/232重放。R54坏引用及原减仓失败保留，后继必须用普通GUI新动作和独立保存重新核完整权利图。10份已证重复的旧profile副本虽已退役为不可读，两个场次的外部归档声明全部保留（跨场去重5档），未删除失败原件或退还spent。[基线、实际闭场及逐路径退役记录](../../docs/maintenance/evidence/2026-11-21-financial-markets-r0055-independent-seed-and-retirements.json)。
