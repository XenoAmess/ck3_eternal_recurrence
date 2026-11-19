# AUB 新版 GUI 分项验收与再次启停

machine_id: `desktop-3fevhd2-1c74096080`。观察为2026-11-19 UTC／11月20日上海时间；游戏为1.21.0.3 Florin/build26785313，EXE SHA-256 `859f0d380098adcb130eb9d453458222749fcdf6d46126ad0ed99d78f9a0aa28`。

R0024实际完成六项完整中文标签和六项悬停、三个原有预览，且只实际确认默认策略；首轮实际启用／禁用及独立四标记读回通过。同一暂停日期1066-09-15、界面资源142/2200/150未变（显示值不冒充精确Native数值）。第二次启用和最终禁用未执行，原case保留4/7 PARTIAL，公共verify实际退出2，缺少`actual_decision_cooldown_readback`；不能因退出正常或部分GUI通过改为全绿。[分项原始审阅](evidence/2026-11-18-ck3-1210-desktop-3fevhd2-1c74096080/aub-gui-r24-business-partial.json)。

原Popen于18:36:18.287551Z返回0，未发送WM_CLOSE或超时强关，零自然日／零SAVE。开始退出比原1500秒软限制晚4.581秒，真实偏差保留；原1800秒硬限制未超。keeper退出、CAS10704释放，Repo/Git/Steam/SCREEN/Game租约已全部归还。[闭场](evidence/2026-11-18-ck3-1210-desktop-3fevhd2-1c74096080/aub-gui-r24-close-partial.json)。

新增公共case `aub_florin_gui_reentry.json`，由原制备器`--scenario florin-gui-reentry`进入。只在精确已审1.21.0.3上制备，复用原fixture全部字节和七个只读观察标记，重新取得新鲜初始状态，并实际完成两轮默认启用／禁用。必须同日立即再次可用且实际执行，资源、日期、暂停与四标记逐步读回，最终禁用并正常退出；禁止推进到已排队的生产day1。六悬停与三预览属于R24独立产品证据，不要求重做，也不计入新case通过项。R24原结论保持，资金／继承和整产品资格仍独立。

完整受影响fixture模块26测试零skip、制备器整文件strict mypy通过；新实际CLI在显式本机安装映射下退出0，收据精确记录1.21.0.3/build26785313及7标记、NOT_RUN、无Native装载。首次CLI缺少本机路径映射，在写输出前失败；仅补环境重跑CLI，未重复已通过的测试，原失败保留。[软件回执](evidence/2026-11-18-ck3-1210-desktop-3fevhd2-1c74096080/aub-gui-reentry-software.json)。新增case尚未实机，也没有新增Workshop发布。

R24业务开始前存在原版Great Wall generated-map诊断：文件声明count11，实际8行transform，每行10分量，原error.log1005B保留。实际安装967B/SHA256 `e5431bba7d5fe4456b924799e6a112c43a55f0cb676a4f1bd458c42a8dcf328b`；当前本地depot1158311/manifest7584914003502786044的精确路径、size及SHA1与它一致，manifest payload CRC也一致。这只排除相对该本地清单的文件损坏，不冒称Valve签名或新CDN验签，不修改安装、不清日志、不授原版错误豁免。[实际来源](evidence/2026-11-18-ck3-1210-desktop-3fevhd2-1c74096080/stock-great-wall-gate-source.json)、[本地清单比对](evidence/2026-11-18-ck3-1210-desktop-3fevhd2-1c74096080/stock-great-wall-gate-local-depot.json)。

按通用存储策略，第二批精确回收31个可替代宣传视频副本／11组，分配139026432B，保留21条代表路径且身份、时间、哈希未变。与已记第一批合计48路径、分配514547712B；净卷差不当单文件回收量。唯一视频、当前业务截图、存档、旧UNKNOWN与冻结SDK未删。[第二批清单](evidence/2026-11-18-ck3-1210-desktop-3fevhd2-1c74096080/expired-duplicate-promo-media-a02.json)。R24另精确回收本场4420个shader，分配97992096B；窗口卷空闲增量514469888B中额外416477792B来源UNKNOWN，不冒称均由本次删除产生。20个已释放普通导航PNG按12个唯一FileID实际回收13516800B，业务／失败图保留。所有旧被删路径按原回收记录不可读，不制造替代原件。


## R0025 冷profile实际分项

同机2026-11-19T19:17:27.362109Z新场，公共制备明确省略可选warm_cache，360文件profile实际分配2943368B，整卷准备窗口净7520256B；没有复制旧4168 shader，也不追改旧warm/压缩recipe的524MB未知差额。新冷Game前瞻340MiB各类预算保持，按逐类实际已用与未花余额计算后继容量，避免从fresh free重复扣已经花过的整额。

本场独立完成真实第二次Enable及.830同日、资源不变读回，真实5/7；最终Disable/.840/DONE未执行，最终仍ENABLED，公共verify仍实际退出2/BLOCKED cooldown原要求。不能拼接R24把任一原case升为通过。首个关闭动作19:42:34.259982Z，晚原soft目标6.897873秒；19:43:19.996957Z原Popen0，未WM_CLOSE/timeout，未勾退出自动保存，零自然日／零SAVE。keeper/CAS10717全部释放。[本场闭场原件](evidence/2026-11-18-ck3-1210-desktop-3fevhd2-1c74096080/aub-gui-r25-close-partial.json)。

冷场在world/业务前再次出现同一个GreatWall原版1005B诊断，原日志保留；不是raw0或新vanilla豁免。36个唯一业务／失败／退出PNG均保留。独占句柄及逐FileID/SHA保护下精确回收本场4168个可重建shader，分配192101776B、零失败；整卷增量192208896B的额外107120B来源不归本次删除。原340MiB和闭场12MiB未来预留均已闭0，实际未花不伪记为spent或跨场续用。

下场仍保留同日两轮完整业务与原七标记。根据实际cold导航约10分钟、到第二启用约14分钟业务及末段/正常关闭开销，拟只对新场前瞻设置1920秒soft关场、2100秒hard；原25分钟失败／部分范围不改。Steam维持离线，尚无新发表。

## R0026 完整两轮通过

同机2026-11-19T20:39:17.537599Z新冷场，来源HEAD `9c60b530def8d7b7c8a56d4aaecc754d993e29cf`。本场原七marker各出现一次，全部五项声明业务通过：新鲜Robert1128初始禁用、实际默认Enable／Disable、同日立即再次实际Enable／Disable，以及四次独立日期、暂停、资源和四标记读回。最终禁用，1066-09-15手动暂停，界面金币139、威望2200、虔诚150与本场初始相同；不套用R24/R25的142金币，不冒充精确Native数值。零自然日、零SAVE。20:51:48Z最终清除四标记及DONE完成，20:53:30.019672Z原Popen真实wait0，未WM_CLOSE或timeout，正常退出自动保存未勾选；keeper无故障退出，CAS10727释放。[完整业务审阅](evidence/2026-11-18-ck3-1210-desktop-3fevhd2-1c74096080/aub-gui-r26-business.json)、[闭场](evidence/2026-11-18-ck3-1210-desktop-3fevhd2-1c74096080/aub-gui-r26-close.json)。

公共verify实际退出0，process、closure、gui_business、case_acceptance和business均true；product_release与native_capability均false。原GreatWall诊断1005B保留，raw_zero仍false，未过滤或豁免。R24/R25原PARTIAL不变，也不把旧266建筑业务自动提升为267整产品资格。

本场前瞻308MiB分配为profile200／PNG64／logs12／metadata24／NTFS8，实际新增分别192102264／53112832／6509496／8746688字节，均在原分类预算内；未连续测得瞬时峰。原Game总852.482073秒，正常关闭早于soft目标1154.683434秒。47个唯一PNG均保留；独占身份／SHA核对后精确回收4168个本场shader，事前分配192101776字节，零失败；整卷增192733184字节中的额外631408字节不归本次删除。308MiB及闭场12MiB未来预留均已归零。

后继仍需实际完成三项继承；R23公国业务通过但共同INCOMPLETE和超限保留；旧资金场17项业务通过及其原版／法院回调诊断仍待分别闭合。这一个GUI case通过后继续推进其他较小产品的完整验收与原条目发表。
