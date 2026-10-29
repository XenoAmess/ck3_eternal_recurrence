# 0.2.0 Alpha：已公开发布，真实缓存已下载

`machine_id: 4-8e1c2f1861`；2026-10-29 UTC（本机为10月30日）。**19:42:56.480675Z已更新同一[Workshop条目3826756673](https://steamcommunity.com/sharedfiles/filedetails/?id=3826756673)，Submit EResult1。** 正式90文件、完整标题／说明／Notes与四张新图一起提交，没有另建条目。真实Steam下载随后EResult1，90文件的路径、大小和SHA逐一与正式manifest一致；R0060已通过公共缓存配置＋实际主菜单加载组合验收并正常退出；独立引擎VFS路径读回仍UNKNOWN，不授完整产品业务通过。

## 固定发布身份

正式内容Source A为`b31664ba659f5a20a188527719367c831734b8c1`，tag为`religious-ritual-fusion-v0.2.0-alpha-publish1`，annotated object为`de305138b17238ef3804cd98894c4b832688dff1`。canonical manifest为90文件、1,289,918B，SHA`3ce7412e8bbaefca8efdd9ed465b398496955ccb603afdd1e75840715280b808`。后继文档、运行入口修复和实机场次不移动该tag，也不改变这份已发布内容来源。

正式包沿用已合格Java／Quarkus JAR的实际validate／build／verify产物；本次网络阶段没有Maven或Native编译。上传后逐项读回staging仍与manifest一致，内层descriptor不含remote_file_id，因此没有重建或覆盖真实Steam缓存。用户目录外层`mod_religious_ritual_fusion.mod`已单独更新为0.2正式staging注册，remote_file_id仅保留外层。

## 公开回读

新鲜Native预览列表从15项变为19项，前15项精确保留，四张补验图追加为第16–19项。匿名API读回公开visibility0、App1158310、完整标题／2691字符说明及Religion／Gameplay／`1.20 'Crozier'`标签。匿名主页面HTTP200，实际“Compatible Version”栏为`1.20 'Crozier'`，真实19项gallery顺序与Native列表相同。四张新CDN JPEG与冻结原件逐字节一致，均2560×1440；封面也与正式thumbnail逐字节一致。详见[截图索引](../../workshop/religious_ritual_fusion_screenshots.md)。

第一次通用回读器实际exit1，原因是直接比较“剥除HTML的文本”和“带BBCode的Notes”。该失败保留。随后将完整公开HTML及冻结BBCode分别解析为同一标题／列表／列表项／粗体／文本事件域，**53项事件和1639个语义文本字符全量相同**，只做HTML实体解码和表现换行转换，没有忽略标点、普通空格或内部换行。公开Notes条目为1793302976。没有重新提交Notes，也不声称服务器原始BBCode字节已读回。初次HTTP429亦保留；冷却后一次普通匿名GET得到HTTP200，没有认证或绕过措施。

## 本机清理与实际下载

用户明确选择继续本机，并追加：“不设置预算缺口；清理范围为与这个mod无关的全部mod”。据此撤销旧约50GB额外缺口门槛，按实际物理容量与统一存储策略执行；没有要求用户再次改变三项长期禁回装规则。

清理只处理本机核实Steam库中CK3 Workshop的无关本地载荷及空目录，保留本模组、相关兼容输入MTS3182367229／DES3826991345、三项策略控制根，以及源码、存档和必要证据。两轮实际共删除4,837文件／21,923空目录，文件实测Allocation合计10,118,775,808B；其中上线后Steam又暂存的无关载荷在恢复离线后清理。未退订账号、编辑ACF或放开DACL；2291024373／2993056101／2962333032持续禁回装。其他项目和个人文件不属于本次清理范围。删除原件不可读取，保留小型身份清单与删除回执；此清理未抵扣旧RRF gross历史。

指定DownloadItem实际完成：App1158310／item3826756673回调EResult1，install flags5（subscribed+installed），实际安装1,289,918B。安装根为`C:/Program Files (x86)/Steam/steamapps/workshop/content/1158310/3826756673`。公共prepare核对真实90文件路径／大小／SHA与正式manifest全部相同，加载配置仅指向原缓存，没有从源码或staging复制冒充下载；引擎独立VFS路径读回的边界见下文。此成功不倒改10月25日两次EResult37，也不能证明未来整个订阅队列不会再暂存。

Steam于19:47:36.985531Z后台原生读回offline=true，PID9328／出生FILETIME`134377767619093018`，客户端11.15.70.27。模式菜单不能完成恢复时，仅在确认下载暂停、没有Game后采用既有正常shutdown／唯一当前账号WantsOfflineMode／offline restart恢复路径；不修改订阅、ACF或ACL。网络SCREEN已释放14667。每次Game仍须新鲜后台离线凭据，不能复用此历史观察。

## 缓存场景与产品边界

R0059／a71使用clean运行源码`33ef4ea6fb385cf56b138bd958c7e466c7cb129b`。实际host1／public2：共享normal-exit入口在主菜单模式错误调用战役身份绑定，在创建CK3前拒绝。无Game／Native报告／控制动作。原失败和原wait保留；Root原1、allocator0／keeper0已消费，SCREEN释放14671。修复共享生产入口与恢复consumer后，须从新的干净源码重新冻结runtime、prepare并实测；冻结的R0059输入不热改，**该失败本身不授菜单加载通过**；后继R0060实测见下文。

共享生成器现只对没有显式normal-exit profile的frontend模式跳过战役身份派生；显式profile及战役路径保留原验证。恢复consumer只接纳本次冻结源码四帧调用链、原workshop_cache Prepared、background ticket／lease与原FILETIME三件组。真实R0059 bundle已由production reducer无mock只读预演通过，仅授资源接续。两组完整相关CI共225项、零跳过、原wait全0；生成器／entry／launcher整模块mypy通过，新增三个类型／函数strict提取通过，不外推allocator整模块strict。首次双main守卫、类型检查及旧SCREEN快照预演失败均保留；没有Java／Native重编或游戏推进信用。

R0057五项UI和R0058三项冷载补验继续按各自范围通过，原注册12／20完整矩阵仍incomplete；SDK episode／save_binding_mismatch、county宗教地图颜色、跨Religion、100核心、完整拒绝／冷却／AI／多人／旧存档覆盖仍有缺口。菜单缓存验收即使通过，也不授全产品业务或product_release_pass。

全部实际原件与精确bytes／SHA见[机器可读发布证据](evidence/publication-0.2.0-alpha-2026-10-29.json)。[离线准备记录](publication-0.2.0-alpha-prepared-2026-10-29.md)保留当时未发布与旧容量判断，后续事实以本文为准。必要Java55／Nativea09、正式包、关键save和代表证据沿现账本于2026-11-01T04:00:00Z复核，不自动续期或删除。


## 后继R0060：公共组合缓存验收与正常退出通过

运行源码为干净提交`2ef9cd84b724ce6fd3fe14bcdb2e66d5964e25ee`，正式包Source A仍不变。P21从合法P19 base重新freeze／六链资格／build_runtime／公共prepare／plan／preflight，六个原wait全0，实际分配上界3,203,072B＜8MiB，没有Java／Native重编。首次授权envelope缺消费者字段的freeze1保留；原225项CI只做有原FILETIME／日志绑定的透明消费投影，未重跑或篡改来源身份。

R0060／a72于20:47:41Z实际启动CK3 PID17756，出生秒`1793306861.5385168`，EXE仍1.20.0.4／SHA`98702f88a547cde2eaf29a85f93b85f68ee4cf8148336a4f7afaeb75319dd518`。单模组profile仅配置真实Steam缓存；90文件再次精确校验，原生只读观测稳定main_menu及250控件树，未启动战役、业务动作或新存档。**public run0、独立verify0，case_acceptance_pass=true、qualified_boundary_pass=true**。证据种类为`COMBINED_MANAGED_CACHE_PROFILE_AND_ACTUAL_MAIN_MENU_LOAD`；独立引擎VFS路径读回仍UNKNOWN、actual_cache_mount_proven_by_independent_vfs=false，不将组合证据冒充独立挂载探针。business_contract_applicable／business_pass／product_release_pass均false。

Root查看真实1024×768菜单，用新鲜截图、实际HWND6030486和原版exit_game_button／FrontEndMainView.OnQuit完成一次合法“退出到桌面”。菜单没有autosave checkbox，未虚构取消勾选。20:52:08Z原生进程退出0，独立保留句柄OS0、Native清理及宿主原wait0；public于20:52:11Z原wait0。Root调用映射CLI的第一组参数被解析器拒绝、未输入；修正为现有click合同后原wait0。为60秒新鲜度补拍一张before，实际共3张PNG，偏离G原计划2张的计数，原图全部保留，16MiB总字节及6MiB单文件界限满足；不倒改原G或声称计数原样合格。

外部Root顺序候选在public0后、宿主原wait回执落盘前提前进入恢复分支；原serial／holder退出1如实保留。Root在同一场既有正常事实和host0齐备后只执行一次独立verify，随后STOP原keeper、消费原allocator0／keeper0并CAS释放SCREEN14676；补完操作原Popen wait0。没有再次run、重放Quit、创建新场或改写原1。后续Root顺序调用须在原期限内等原host回执，不能仅因public先结束就判正常证据缺失。

20:55:43.471678Z后台Steam再确认offline=true，PID9328／FILETIME`134377767619093018`。容量闭场按C20累计Native测量，184,701,320B，各组件及metadata owner字节cap通过；旧G闭场，未用Game额度撤销，gross退款0。保留其他工作包1,888,256B预留，再独立准入最终文档／普通master整合，未提高原owned／gross／quota上限。历史业务矩阵与SDK／county等缺口仍按前文保留。
