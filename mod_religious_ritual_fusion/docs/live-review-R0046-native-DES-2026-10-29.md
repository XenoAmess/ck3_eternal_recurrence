# R0046：同一礼仪免费编辑、长名称与DES维护

`machine_id: 4-8e1c2f1861`；2026-10-29T00:37–01:28Z，CK3 1.20.0.4。运行源码为`244240ba915b58eac7f625487e16f0ff3eb9de45`，Native a09实际编译来源为`cbacd3373427ffc9dca016584dffe8baf89d80b6`。本场完成了以下范围的真实业务，但原冻结cold case和八项总验收仍未通过；公开下载仍是0.1.0-alpha。

从R0042实际存档冷载，玩家31254、Rite155、Faith106、Religion8及四核心均正确；没有重新融合、初始化fixture或补虔诚。首次显式只读观察之前，实际离婚教义为`doctrine_divorce_disallowed`，与冻结配方要求的allowed不符。随后合法编辑改为allowed，不能补算首次冷观察通过。Root因此提交incomplete，由原CaseClient正常关闭。

通过历史结果的恢复入口进入同一155的原生编辑模式，设置30个Unicode字符的中文长名称、形容词、信徒单复数及描述，并在真实原生教义组选择DES宗族化。最终CanEdit=true、原生追加报价0。原生窄根`rrf_native_setup_footer`完整查询成功，实际调用其`rrf_native_apply`并仅确认一次；不是typed prepare替代。编辑前后虔诚均为0，Rite/Faith ID不变，团体身份、秘传、律法主义、占星术四核心和七美德／七罪恶完整读回。

自然推进35天至1066.10.22，逐日使用原生推进，没有遇到事件、交互通知或战争。E0、E1、E2和day35分别实际保存，原件按持有拒写／拒删句柄的FileID、FILETIME、SHA核对并独立归档；每份通过共享V4读取完整记录，没有编辑存档。普通SDK仍报告`save_binding_mismatch`及episode_id缺失，不能由原生文件或V4检查替代该资格。

| 阶段 | 原生成员与完整ACTOR读回 | 家族及绑定 |
| --- | --- | --- |
| E0，编辑当日 | 1 | 原生首领认领尚待执行 |
| E1，次日 | 41 | 38人house174、绑定155；65872／65873／65874尚无house或DES采用变量 |
| E2，第二日 | 48 | 全部house174、绑定155 |
| day35 | 48 | 全部house174、绑定155；对照33946仍为Rite0／house2098、无DES变量 |

完整RITE、FAITH、RELIGION、DYNASTY、HOUSE和COAT_OF_ARMS记录确认：DES原生首领认领成功，复用dynasty174／house174，模式`native_dynast_reuse`，首领仍为31254；家族和宗族名称跟随完整礼仪长名，CoA1783四份token SHA一致。E1起配置完成标记存在，setup／open／apply标记及费用waiver均已清除。E1和day35全局两份DES维护列表各恰好包含一次155，维护lease仍存在并已续期。

E0两份来源Rite152／154、Faith13／105完整AST均与冷载输入相同。day35的Rite152首领自然从34232变为36445、Faith13人数缓存变化；Rite154与Faith105仍相同。不将长期自然人口和选举变化归为编辑污染。day35钱包为-0.4，是自然月收入后的实际余额；编辑当日0→0的零追加费证据单独保留。

实际存档：E0为68578038 B／`94da4aa899bde736cfe7357f9835af2568da301c9a031dc6f8b6b754f2591824`；E1为68665323 B／`29dbc35e724a2b963cf8e3e7bcdb160abffe74af7aab9ca3eb5d7948cdba6101`；E2为68718566 B／`d6968274168488f635c031c69ace82132d247496402808a9f57b04d89a83956c`；day35为69117980 B／`001e9f169c346037de53925b4adcfc0e28db3f4c5e038f077f1c30d1cb89a676`。归档位于`C:/workspace/rrf-development-20261024/review-fixes-a01/cold-R0045-retry-a01/checkpoints/`。独立最终冷载尚未执行。

原生退出和保留OS句柄均0，host／keeper／allocator均0；公共run／verify及Root原工具89087退出2，保留业务incomplete。正常关闭资格true，01:28:08Z屏幕CAS14541释放并恢复1024×768。Root实际消费原始wait，没有另起退出流程。

[机器可读业务索引](acceptance/live-review-R0046-native-DES-2026-10-29.json)绑定完整原件`R0046-BUSINESS.actual.json`，49294 B／`7be362062286043e6fc8c483214e3114c41af805069f689b2a357b1e3a541b69`。成员全记录索引143299 B／`b8bb49a3cb0b582989954c79e207ae7e39a2ffbceb5960a8605bd2b5cb0431d3`。失败的操作请求、报告上限拒绝和三名E1缺口均保留，不计通过。

两张合格新UI实拍已追加到同一工坊为第14、15图；重叠窗口与地图提示的诊断图未上传。[素材身份](media/screenshots-R0046-2026-10-29.json)和[匿名公开回读](evidence/workshop-media-readback-R0046-2026-10-29.json)分别记录原图与JPEG。后续仍须完成最终冷载及八项总审查，再决定正式发布，不能用本场35天或商店图片更新授完整通过。
