# 六章结构与镜头需求 a03

正式交付20–40分钟，编辑目标30–35分钟，参考32分钟（2/6/7/6/8/3）。`six-chapter-narration-a03.md`是完整六章口播候选；不是已冻结逐句稿或实测32分钟音频。字数与假设时长见 `wordcount-budget-a03.json`。A/B/C和饥饿结果的编辑保留位不配音，不用长静帧填预算。

## 六章内容

| 章 | 参考时段 | 主问题 | 本次内容与保留位 |
| --- | --- | --- | --- |
| E4-01 | 00:00–02:00 | 怎样把足够兵按时以可战状态送到战场？ | 引出人数、库存、更新、路线和费用；限定William/版本/运行，不提前宣布方案胜出。 |
| E4-02 | 02:00–08:00 | 库存、容量、当地上限、月变化如何区分？ | R0164 stock→cap与R0165实际+1分开；TERM中文；R0169局部负例；R0168两阶段加权合军。 |
| E4-03 | 08:00–15:00 | 当前提示、预算与实际人数变化怎样核对？ | R0162两个窗口；R0171预算236/first725false；正式R0172+15→17/净−67有条件回放；饥饿pending。 |
| E4-04 | 15:00–21:00 | 预计时间与实际到达怎样读？ | UI43整条vsnative30首边；Jan25锁定61.875%；停止/改道合同；R0172登船与登陆实际净0窗口。 |
| E4-05 | 21:00–29:00 | 三方案怎样公平比较？ | A/B/C方法与真实pending；R0173同日平分、完整27/37守恒、stock110.37716>childcap100；Jan11trueNET与两种维护；实际付款待补。 |
| E4-06 | 29:00–32:00 | 出发、途中、接战前怎样检查？ | 当前读数→动作结果→实际结算；登陆补员条件新基线；知识代码跨机复用，未知保持。 |

## 逐项镜头需求

下表的“已有”只说明数字/文件或指定单帧权威；全部连续clean spans仍待Root/媒体lane实际审核。没有本稿新增截图、媒体读取、编码、时码或审阅信用。

| Shot | 讲解段落 | 需要的可读画面/动态过程 | 现有权威与剩余需求 |
| --- | --- | --- | --- |
| E4-S01 | C01-01至08 | 原生地图选军→人数/补给→路线→同日编组变化的短引子 | 使用已审原图/encoded单帧只授各自内容；可用动态序列待审，不能暗示ABC成绩。 |
| E4-S02 | C02-01至04 | 军队补给完整tooltip→携带补给概念→当地上限概念/用量 | [TERM索引][term]原始11/11、各自编码10/11；按指定Root8单帧权限取材，16候选仍未审。 |
| E4-S03 | C02-05至08 | R0164补给291.22808→300与完整人数未变；切断并标运行后转R0165 53团9→10 | 数字/身份已闭，R0164/R0165为独立run；动态窗口时码/clean span另验。不能把prepared刷新动画当新增人数。 |
| E4-S04 | C02-09 | 当前军事页“每月补员”checked、“补员兵士”完整提示 | Root指定encoded单帧可读；不新增数字费用/付款或toggle操作镜头。 |
| E4-S05 | C02-10、C05-04 | R0169 Jan29两地当前月变化−4.38596/−8.77192，并标“局部候选不合格” | 真实数字/地图端点已核；当前率不标成已扣库存，winter/territory/统帅原因未知。 |
| E4-S06 | C02-11至12 | R0168 Jan20同地合军动作、两军pre→D0 post、完整27团、数值公式逐项出现 | 实际同暂停merge和两stage数字已闭；既有postmerge单帧不自动授完整动作clean span；upperclamp镜头pending。 |
| E4-S07 | C03-01至06 | 当前损耗tooltip与R0162周期−31/县抵达−127两个独立窗口 | 每个窗口的完整团和日期单独标；兵员净变化不是死亡统计，源＋端点归因限制保留。 |
| E4-S08 | C03-07至08 | R0171前后同暂停6746/6747，路线第一步725，预算236＋条件false | [当前输入包][r171]可复验；GUI素材仍按Root实际原图权威，不能造236已扣动画。 |
| E4-S09 | C03-09至11 | R0172+15→17，6746→6679，库存116.51751→110.37716，实际clock stamp与有条件整数回放 | [正式R0172包][r172]支持数字和条件复核；执行时资格/ledger未知，后帧月getter不是已捕获执行rate。原图encodednull，动态净变化镜头另审。 |
| E4-S10 | P-STARVATION | 本期William实际阈值两侧stock/state、逐团整数写回及同窗事件/补员 | pending；不拿围城、高补给损失或旧Robert代替，不制造饥饿胜出故事。 |
| E4-S11 | C04-01至04 | Jan20军队窗口UI赴利雪43天/Mar4，与原生首边30天并列 | UI来自Root原图审阅，首边来自R0171真实输入；二者范围不同，不用差值生成后续精确时量。 |
| E4-S12 | C04-05至08 | Jan25锁定完整原图＋同暂停首边61.875%；停止前后/改道前后/实际路线结果 | 新锁定原图postfinish/encodednull；旧编码concept不能挂到新native进度。同帧值闭，动态动作两侧另审，loadedcutoff/50%live仍unknown。 |
| E4-S13 | C04-10 | R0172+30→32 province1506→725/embarked，与+42→44 1009→2174/regular/空route | 两窗27actual/37DATA整数均不变；不授海路普遍无损失。Unit190unknown不画成0兵运输图标。登陆18chunk许可变化为新基线提示。 |
| E4-S14 | C05-06至10 | R0173Mar5同paused平分前后，public0/native0与public204/native199，各库存/容量 | `sources/r0173-half-split-facts.json`为本包摘要，实际原包仍保留且入masterpending。数字和提交绑定已核；GUI/encoded/动态过程尚无本稿授信。 |
| E4-S15 | C05-11至13 | Jan11收入/完整支出/trueNET与current/allraised维护分别展示；实际付款事件账 | [NET专题][cash]已闭当前month scope；不用HUD拟合、不重复扣军费。实际登船/其他付款ledgerpending。 |
| E4-S16 | C05-01至05、14至16 | 同一合格save三独立回放，按日期/事件对齐动态路线与结果表 | 全部ABC结果pending；表三行留空、赢家空，不把资格旅行当完整A或B。 |
| E4-S17 | C06-01至10 | 在原生面板完成出发/途中/接战前检查；末尾知识代码来源卡 | 当前primitive可用，角色/军队/版本重新绑定；不是完整策略safeloop/未来费用上限已验。 |

## 三方案结果位（编辑用）

| 方案 | 合格共同起点 | 实际到达 | 完整兵团/人数 | 补给及补员/损耗窗口 | 实际支付 | 结果 |
| --- | --- | --- | --- | --- | --- | --- |
| A整军直走 | pending | pending | pending | pending | pending | pending |
| B分兵恢复会合 | pending | pending | pending | pending | pending | pending |
| C换路线 | pending | pending | pending | pending | pending | pending |

“资格旅行抵达2174”与“Mar5已平分”各有真实结果，未自动闭合两军分开恢复、会合或ABC共同起点。正式冻结时可替换结果块或保留明确研究边界；不承诺未实测的时长/胜负。

[term]: https://github.com/XenoAmess/ck3_eternal_recurrence/blob/accc385ecb4086f8912cd9492f95e049c8065f7d/promo/ck3_native_war_ai/episode-04-march-logistics/evidence/r0169-terms/index.json
[r171]: https://github.com/XenoAmess/ck3_eternal_recurrence/blob/3e2737b5909616cd2ab301da59352250410bafb8/promo/ck3_native_war_ai/episode-04-march-logistics/evidence/r0171-county-inputs/summary.json
[r172]: https://github.com/XenoAmess/ck3_eternal_recurrence/blob/3e2737b5909616cd2ab301da59352250410bafb8/promo/ck3_native_war_ai/episode-04-march-logistics/evidence/r0172-periodic-loss/index.json
[cash]: https://github.com/XenoAmess/ck3_eternal_recurrence/blob/7f1db1a773e647b9f31378d4a9ccf57a60cf9e73/docs/ck3-native-ai/war-cash-net-live-r0168-2026-10-05.md
