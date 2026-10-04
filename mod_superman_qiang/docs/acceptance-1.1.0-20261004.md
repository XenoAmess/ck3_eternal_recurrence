# 1.1.0 增量验收：健康与紧凑通知

实际针对性实机GREEN：健康20场景、真实冷重载、普通自身/他人通知正文与特质持有人、查看只读及一步免确认入口。此结论不等于重新跑完首发42矩阵，也不等于正式版本已发布。candidate L0已通过；正式tag绑定构建与Steam发布/公开回读仍pending。[机器可读报告](acceptance-1.1.0-20261004.json)绑定原件路径/bytes/SHA与范围；[复现入口](health-native-acceptance-tools-1.1.0.md)提供新健康夹具与独立检查工具。

同一实际CK3 1.20.0.3/EXE94b55397…，冻结SDKf643b32e…/DLLad3bbb4e…与产品源分开。A3产品22件绑定ff5b112d…；A4仅一个interaction49af8002…取消多余确认，另21件逐字节相同，因此健康已验输入保持。正式clean commit/tag须再证明22字节一致，不能把SDK或dirty候选冒充正式产品tag。

| plan ID | 实际状态 | 对应范围及边界 | 运行 |
| --- | --- | --- | --- |
| H0 | GREEN candidate L0 | A3 L0 plus A4 unique interaction single-leaf parser/static/tests/build/verify; formal tag-bound gate pending |  |
| H1 | GREEN targeted live | Forced health helper exact75 plus only-health-eligible and reverse production pair/7-candidate dispatcher actual health selection; no statistical claim | R0019 |
| H2 | GREEN targeted live | 3.00074/3.00075 plus same-day second call floor; both capacity directions and reverse departure saved | R0019 |
| H3 | GREEN targeted live | Native player exact75, all40 basehealth unchanged, raw signed scale conservation; negative mitigation, repeat rebuild, growth/flip/zero, immediate zero/negative | R0019 |
| H4 | GREEN targeted live | New owned game process loads actual after checkpoint;40 characters signed decimal vars/base/scale and native466235 unchanged | R0020 |
| H5 | GREEN scoped representative/composed regression | R19 actual equal XP counts6/6 no-health; actual diplomacy/prowess representative±1, pair counts6/2. Unchanged counter/anonymous/original hook contracts use historical1.0 evidence and A4 source comparison; no claim this20-case round reran anonymous or all7-candidates-empty native scenario. | R0019 |
| U1 | GREEN targeted live | Actual70percent ordinary self/NPC one-menu-click directtoast; no confirmation;correct portrait/name/count,2rows6skills,health5decimals | R0021, R0022 |
| U2 | GREEN scoped actual UI + source inventory | R21 holder trait actuallyhovered; R21/R22 before/after XP/7ledgers/modifiers/basehealth/6base/traits unchanged;14 modifier names/value source reviewed by inventory, not14 separately photographed windows. Bodydirect, toast-hover notclaimed. | R0021, R0022 |
| U3 | GREEN raw gameplay source | R22 accepted exact unaltered native ordinary P2 XP1 screenshot. Public encoded strip/tag publication independently pending. | R0022 |
| P1.1 | PENDING publication | No formaltag/build/upload/cache/changenotes credit from live session |  |

## 实际证据

- [R0019健康20场景](live-R0019-health-1.1.0.md)：独立保存40角色基础health/六基础数组不变，账本raw严格守恒，保存单个正负modifier倍率正确；native玩家466160→466235/100000，精确75ticks。底线与同日二次、±百万容量方向、负修正抵消、重建/翻转/清零、接收0/−1即时getter和代表技能回归。
- [R0020新进程重载](live-R0020-health-reload-1.1.0.md)：只挂原fixture三件定义、不含on_action/events；变量/经验/基础/scale不变，native466235保持。
- [R0021普通UI](live-R0021-normal-ui-1.1.0.md)：真实普通P2双方经验1；实际GUI70通知文字可读与持有人trait提示通过，before/after不写状态。仍保留500×210空白确认窗RED，未改写这轮失败。
- [R0022免确认UI](live-R0022-compact-ui-1.1.0.md)：普通右键只选择一次直接通知，自身和NPC两入口真实通过；同普通after档actualsave对照保持，最终进程0/keeperCAS4230释放。

最终正常NPC原图为 `C:/ck3-superman-qiang-110-20261004/acceptance/live-H0005/ui-NPC-direct-toast70-clean-A0002/screen.png`，1024×768，SHA `7b74e180a0bccf2bfdad678bff7bf363d77b57c37e9329de0283fa9f1a8840c6`。48岁阿梅利娜/真实经验1次、2/3/12/12/2/0、健康4.16622(0.00000)和所有净0可读、人物及普通地图同屏；parent直接审原图接受。素材源是真实正常seduce_outcome.2020旧campaign，UI轮没有fixture/debug/控制台/改变量。R21旧图保留；第5正式media纯裁切编码/公开图另由宣传与发布流程绑定。

Parent另独立消费原始native与saved multiplier：`C:/ck3-superman-qiang-media-redo-20261004/root-native-health-delta-A0001.json`、`root-independent-health-saves-A0002.json`。各原件准确SHA在机器报告，不将其‘reload/UI false’历史scope改成新通过；后续R20/21/22由各自真值关闭。

## 保留错误与未覆盖

R17夹具把effect scale写成var导致80条实际Failedreadscale；生产原本definition-local blockscale未改，A4夹具修正后才在R19运行。R18缺原injector是预启动环境voided，旧obj/lib最小重链接新binary有真实身份，DLL没有重建。R22首次controller因prepare未完成过早提交、identity缺失而在launch前退出；等待后新controller实际只启动一次。所有原stdio/日志/输入保留。

R19完整日志164E含148夹具unusedvar、theme1、unknownformatter14和原版AI活动1。R20十条fixtureunused；R21原版scheme primary40script+4targetnotfound；R22全日志见本轮报告。不宣称全局零错误，unknown formatter来源保持未知，primary无sxad不冒充完成vanilla对照。无本轮已定位的sxad语法/作用域/显示错误，实际机制与UI精确证据按范围通过。

不验证寿命增加年/月、7分支统计分布、多人/成就或其他游戏版本。健康抵消可让有效变化不对称，raw±75并非健康总值总是对称；零/负健康仅即时受控sample。首发匿名/原版接入和全六技能矩阵继续是[1.0.0历史证据](acceptance-1.0.0-20261004.md)，本轮未虚称新增7项all-empty/anonymous实机复验。14modifier为源码库存审阅；不是14个窗口逐一实拍。原生通知正文直接呈现属性；失效hover图片没有被记为详情通过。

原始全路径过程库存见 [raw索引](acceptance-1.1.0-20261004-raw-index.json)，包含shader/preparedinputs、stdio、MCP收据、截图、原save/melt、decoder/checker、失败attempt以及任务租约。永久保全、未清理旧资产。


最终第5张已纯裁切/编码并由root直接审阅：[05_notification.jpg](../../../workshop/superman_qiang_media/v3/05_notification.jpg)，785×364、138982B，SHA `51ac5484e3a82bcac65c65c2fe3fe3d058c2868715980171192f1d1886c0d6ff`；原图副本、裁切/provenance及root-review同目录，精确bytes/SHA也进入机器报告。这张展示正常角色真实经验1次的记录，不把原本平手的普通性行为当作健康吸取画面；健康±75机制证据是另轮R19夹具，不混进宣传。公开上传仍独立pending。
