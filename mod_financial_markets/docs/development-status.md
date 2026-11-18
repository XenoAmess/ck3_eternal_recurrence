# 施工状态

2026-11-18，machine_id: 4-8e1c2f1861。

## 当前状态（14:52 UTC 更新）

第四场`R0004/a82`载入后普通Full可用，但唯一强制读取请求排队8秒后被Native明确拒绝，新请求未见owner开始执行。已按真实失败关闭受管场并释放：Game失败exit1、Job0、tree gone；公共run wait2，keeper原wait0。没有金融动作、推进日或SAVE。正在修原生有界唤醒及错误证据，后续继续实际业务验收；失败不计为整Mod通过。

期货源码复核另发现AI只使用已有钱包余额、未从真实金币准备保证金，以及新定期合约的到期日选择与AI参与缺口。两项正在生产调用链补齐，不把永续多空按钮已经存在当作整个期货市场完成。

## 截至14:22 UTC的准备记录

第三场 `R0003/a81` 实际载入原存档，13:50:32Z 获得精确 1.21 Full：玩家31254、存活、地图就绪、暂停、日期53144328、金币255。暂停且语义不变时，普通 snapshot 持续返回同一 `native:1`，原启动守卫要求两份递增 Full，遂在原1800秒期限失败。公共 run 原 wait2/1805.433秒，Host原wait1；受管失败清理为CK3 exit1、Job0、tree gone，不能称正常退出。keeper原wait0后，14:16:03Z CAS `15224→15225` 释放。本场没有业务动作、游戏日或SAVE。

已采用独立 `ck3_take_fresh_full_snapshot_v1`：复用原DLL的关联只读查询，核实际ACK、read_request_id、完整原包、递增revision及相同PID/连接。普通snapshot与运行中的推进观察不变。新10项组合含12种异常刺激通过，受影响Saved14及旧版2项另行通过；实际capability3项通过。金融七个saved case均声明此工具，未重编Native或伪造新帧。

AI付费宣传关注队列和真实本金认购修复已采用，受同一个总日预算约束；满额AI发行在原注册币遍历及时完成，保留玩家手动完成及不同继承项目的pending。详见[AI运行合同](ai-attention-runtime.md)。原生产品现在有160个运行文件；真实自然募集、队列保存和交易仍待新场验证。

14:20:42Z，采用共享流式SAVE审计及AI修复后的完整金融工具`mvn verify`实际wait0/34.793秒：160项通过、0skip，56个主源码和20个测试源码实际编译，Quarkus默认入口打包成功。此前共享save-core的10项通过并install。本轮SAVE两项JUnit复用52个合成断言，不能当真实存档认证；命名审计入口、真实1.21编码与冷载仍须实测。原件见`operations/MVN-save-core-audit01`及`operations/MVN-financial-ai-save-full01`。

## 截至13:37 UTC的准备记录

第二场 `R0002/a80` 已实际创建 CK3 并注入 Q05 DLL，连接实际返回精确 Florin HELLO。Saved startup 遗留的 `.4` 守卫立即拒绝新身份；后续 300 秒为 finally 的收尾 snapshot 等待，并非正常启动等待。原受管环境失败清理为 CK3 exit 1、Job 0、tree gone，不能计正常退出。keeper 与原 allocate wait 0 后，CAS `15207→15208` 实际释放；没有业务动作、游戏日或 SAVE 通过。完整因果及原件见[共同验收记录](../../docs/maintenance/2026-11-18-machine4-financial-acceptance-control.md)。

本场加载日志还暴露了真实脚本解析问题。关场后已采用保持原公式的数值比较修复、意见衰减期限修复、正数扣款 API 与无用交互 AI 调度声明修复，尚待新场重载及真实金额对账。Saved 启动按精确版本识别，Florin 等待实际 owner 与两份递增的完整帧，旧版保留原分支；Core 的 partial/unavailable 消费同时按实际 HELLO 绑定，不能跨版本混用。

13:13:58Z，完整金融工具 `mvn verify` 实际返回 0：143 项通过、0 skip，49 个主源码和 16 个测试源码实际编译，Quarkus 打包成功，原进程总墙钟 34.064 秒。包含六个后续验收 profile 的生成、衍生品关联账户/合约/债权、继承观察基线防覆盖及保守容量边界；这些 profile 只生成观察器，不注入生产资金或资产。六场均已接入公共准备入口，尚无对应游戏业务信用。JUnit 原件保全在 `C:/workspace/ck3-market-task-20261118/software-10-financial-full01`，原进程回执见 `operations/MVN-financial-followup-full01/ORIGINAL-WAIT.actual.json`。当前正在完成共同 Host/Core 联合检查并准备新场，未把软件通过当成交易、保存或整个 Mod 通过。

共同 Host/Core 的当前组合 26 项及 Core strict 已通过。同根运行包绑定另暴露原 Q05 无 `observed_at_utc` 与旧 reader 假设不一致；最小读取兼容修复的 9 项已通过，保留原 Q 与原构建时间，不伪造资格时间。新包继续复用未变 Native，下一场仍须实际验证 loaded Full、钱包与保存。

源码复核另确认 AI 募资可达性缺口：35,586 个角色在默认每日512候选下约70日才轮转一次，长于30日募资期；广告只影响最多8人，AI登记后尚未主动本人认购。正在独立准备有界关注队列及真实本金认购修复，仍受同一总日预算、随机选择、外部认购比例与真实现金约束；此修复尚未采用或实机验证，不能称 AI 市场已验收。

## 截至 12:27 UTC 的准备记录

共同 Florin 运行包 `runtime-core03` 已实际组装成功；Q05 使用同一 Native 编译缓存，未重编 C++。正式 DLL SHA-256 为 `2716d740cb145eae319cf7776fe4f0a46b5c325b6196026d0541a5eed292836c`。共享单日推进和完整角色 ID 消费修复已提交推送，但仍未取得游戏运行行为信用。

首场 `R0001/a79` 的 prepare、已准备 plan 和 preflight 通过。公共 run 的 Host 在创建 Game 之前，被 Saved inventory 守卫拒绝：观察包仍含 `xfma_start.txt` 新开局钩子。原失败和 profile 保留，keeper/原 allocate 正常退出，CAS 已释放；游戏日和 SAVE 均为零。

最小观察器修复已移除该钩子的输出，继续只通过正常 GUI arm。实际 Java emitter 到公共 Saved inventory 和 Host 复制的新增组合回归通过，受影响 8 项通过；完整金融工具随后 `mvn verify` 130 项通过、0 skip，Quarkus 打包成功。新的实际场次仍待执行。完整事实、路径与时间见[共同验收记录](../../docs/maintenance/2026-11-18-machine4-financial-acceptance-control.md)。

## 截至 11:07 UTC 的施工记录

用户明确要求继续做完完整产品。A0是历史原型，不是本任务的交还终点；下文A0通过与失败保留原范围。当前正在把完整现货、发行主体、期货、价格来源、债务新闻和自定义市场界面接入同一原生账册。共同接口见[运行合同](runtime-contract.md)，没有以Java参考计算替代游戏实现。

新增游戏规则提供2,048／4,096／8,192种活跃币容量、AI每日128／512／1,024个候选和独立新增风险开关。默认4,096币、512个AI候选；扩展档仍属实验配置。关闭新增风险不会删除旧持仓、债务或结算义务。

09:43:53 UTC，首轮增量Maven实际47项全部通过：原现货26、原子账册批次3、发行9、退市生命周期7和新增界面引用/窗口注册构建检查2。42个main源与7个test源编译，Java21，15.344秒。09:44:42 UTC，债务8、危机策略3和世界新闻4共15项另行全部通过，11.873秒。这两轮是软件结果；完整期货、原生脚本、GUI和压力场次仍需后继实际验证。

09:34:38 UTC，本机Steam11.23.65.88通过新精确Native配置实际读回离线（同进程/模块、两次离线byte=1、tray状态4）。[共享修复与来源](../../docs/maintenance/2026-11-18-machine4-steam-native-offline-1123.md)已提交推送。旧08:43探针不可用的事实不改写。新版1.21的普通事件选项后台提交仍在迁移，实机业务尚未开始；不借用1.20地址，也不恢复游戏前台。

10:09:02 UTC，完整工具验证126/126通过，Maven20.251秒；涵盖现货与原子账册、发行与真实出资认购、退市、期货、价格来源、债务危机新闻及验收夹具。后续修复了强平余单错误留簿、旧开仓价越当前风险带的问题，10:25:10 UTC期货15项和验收夹具6项共21/21通过，30.789秒。153个runtime文件的BOM检查通过。以上均为软件或静态结果。

公共后台GUI消费者实际35项通过、1个旧1.20夹具缺失跳过；新增1.21跨语言原件链另10项通过。原生债务和期货公式已依据CK3 `max`为上限、`min`为下限修正，仍待引擎金额验证。共享DLL在同一缓存中构建完成，19项独立基线程序及CTest全部通过；首次基线链接失败保留，修复只涉及测试目标生产body隔离。DLL尚未装载。

10:28完整金融工具验证128项中127项通过、1项因新增互动未及时列入运行清单失败；补齐清单后7项构建合同独立重跑全部通过，不记作一次完整128项绿。10:33共同Java控制链31项通过。10:55静态CLI校验155个运行文件、209个effect及每语言468个本地化键通过。现货已补上真实有资买盘深度，退市读取上一完整日的合格交易量；期货新增永久合约号和仓位号。A0交易入口永久关闭，历史资产仍供一次性迁移。

11:07:17 UTC，最终完整金融工具`mvn -f mod_financial_markets/tools/pom.xml verify`实际128/128通过、0跳过，28.190秒；复用已有编译缓存，main/test均无重编，Quarkus重新打包成功。原失败仍保留。该轮包含最新155文件清单及本地化；这是完整工具软件验收，不是游戏引擎或整Mod业务验收。

新增1.21 Native配置合同由真实CMake File API绑定791个生产TU及19个测试目标，25项消费者测试通过。实际DLL SHA-256为`22da249e8de425ad605693d062cd691e7b2dd3a334f21a7a090fc98e06111b4e`。完整正式资格还需最终干净提交后的预冻结、同缓存no-work构建及结束复验；首轮dirty编译不补造预冻结。

共同运行包最近可信基线仍为1.20，正在补齐实际1.21安装身份迁移输入；不能把旧manifest换hash当成运行兼容。共同Python五组194项通过，既有巡礼只读/执行数据消费三组115项通过，均不授金融游戏行为通过。

首场采用隔离旧原版存档，夹具只提供正常按钮启动的只读观察，不生成币、金币或订单。实际开市、付款、同日买卖与物理SAVE需要由生产GUI完成并独立对账；本轮完整产品实机仍为NOT_RUN。共享启动、每日推进和正常退出的1.21消费链正在补齐。

本轮完整任务预留峰3GiB、增长上界6GiB，10:27:51 UTC C盘可用74,326,544,384字节，容量与当日配额均通过；未清理资料。执行机器仍为4-8e1c2f1861。

## A0 历史交付边界

已开始 A0 原型。一个 Mod，共用金融底座，现货与期货作为内部模块维护。阶段范围、退出标准和性能预算见 [实现计划](implementation-plan.md)，具体用例见 [测试验收](test-and-acceptance-plan.md)。

Java 参考账本已实现稳定账户/币/受益人 ID、有限供应发行及增发、真实费用金库、100 枚一手、整数分、价格时间优先、部分成交、原订单累计手续费、冻结与撤单、关联受益人自成交拒绝、跨币共享资金和失败整笔回滚。日序可以同日幂等推进，但尚无期货日清算。该核心是开发参考，不是游戏运行时，也未证明 CK3 性能。

发行资金参考计算已加入：微型R20需要6金费用或限制，剩余14金；标准R200需要55金费用或限制，剩余145金。费用、维护预存、履约保证金和做市资本分别记账。实际认购、滚动融资上限、风险服务准入仍需生产接线。

14个游戏文件已落地：收费发行、有限双向报价/买卖、每日AI候选、持仓故事和托管候选、玩家决议/互动/回执、中英本地化。首包保护值为32个累计登记身份，并非最终容量。详见[A0原生说明与来源](a0-runtime-notes.md)。完整订单簿尚未接入游戏；合格继承管理入口、全世界公平发现和存档寿命仍待补。

## 已有软件结果

2026-11-18 08:46:16 UTC：

~~~text
mvn -f mod_financial_markets/tools/pom.xml -Dtest=FinancialMarketTest test
~~~

26 tests，0 failure / 0 error / 0 skipped，JUnit 0.426s，Maven 27.844s，exit0。包含确定性随机资金/币守恒序列、先成交外部订单后遇自成交的全笔回滚、跨币余额不能重复冻结。Java release21，-Xlint:all -Werror 编译通过。软件结果不授游戏交易或存档通过。

08:58:55 UTC 新增执行：mvn -f mod_financial_markets/tools/pom.xml -Dtest=ListingFundingTest,PoolQuoteTest test，9项全部通过，Maven14.594s，exit0。两档发行资金分类及A0有理数池报价/双边手续费、最小成交拒绝和溢出边界通过；这是独立计算模型，不证明原生脚本精度。

09:02:17 UTC 执行 mvn -f mod_financial_markets/tools/pom.xml -Dtest=BuildContractTest verify：新增5项构建合同测试全部通过，Maven15.765s，exit0；Quarkus augmentation 1758ms，工具打包完成。含BOM/未定义effect/未列入runtime文件/本地化不一致/路径逃逸/输出覆盖/清单SHA等边界验证。

本轮共40个不同软件用例全部通过。随后对最终报价作用域修订文件运行Quarkus CLI validate：14文件、11个effect、每语言26键，exit0。两个native文件的修订仅有静态信用；事件上下文、引擎语义和业务仍NOT_RUN。GitHub新增 financial-markets-static 工作流执行完整软件验证，不调用游戏。

显式清单见[运行文件清单](../runtime-files.json)，候选工具输出content/与独立manifest.json，排除tools、docs和验收数据。外置候选与实际文件SHA保留在 C:/workspace/ck3-market-task-20261118/candidate-a0-01；这不是已发布包或实机通过凭据。

源码568d763833679612bd493aad20b1a60779c856a4的候选14文件已实际构建成功。首次官方[CI 44272883501](https://github.com/XenoAmess/ck3_eternal_recurrence/actions/runs/44272883501)在Windows checkout阶段因历史promo长路径失败，未运行任何测试；失败不改判。后继补齐与既有工作流一致的core.longpaths环境配置，重新触发官方CI，金融代码和14个runtime文件未改动。

后续审阅将native本金/费用公式调整为先转分再做除法和费率，减少固定点中间截断风险，数学预期不变。此变更尚无引擎精度信用；新候选使用外置 candidate-a0-02，保留01原输入，不覆盖历史包。最终CI及外置manifest绑定实际后继源码。

## 实机状态

本机此前已更新到 CK3 1.21.0 / build26622941，见 [本机更新记录](../../docs/maintenance/2026-11-18-machine4-ck3-update-and-market-design.md)。本轮 08:43 UTC 进程只读检查未见 CK3，未启动游戏、注入或恢复旧自动游玩。

08:43:20.845669Z 公共 steam_offline_state_probe.py 实际 exit2：status=unavailable，reason=cdp_not_enabled，native_provider_unavailable=invalid_input，owned_debugger_candidates=0。原件：C:/workspace/ck3-market-task-20261118/implementation-steam-offline-probe-01.json。该结果不能证明当前在线，也不能作为可启动凭据；本产品尚无1.21共同后台业务场次和公共adapter资格，实机状态为 NOT_RUN / prerequisite BLOCKED。

不通过抢前台或复用1.20 DLL绕过。第一场先做金额精度、故事实体/死亡托管、保存冷载及日历合同，再扩大到百币和完整每日委托簿。

## 后续未完成

1. 完成已采用 Saved Florin 身份、owner/Full 消费与脚本解析修复的共同检查，再按公共入口准备新的隔离场次；未变 Native 继续复用原资格。
2. 实机验证金币精度、正常GUI付费发行、同日现货买卖、AI资金、物理SAVE与冷载，保留真实失败。
3. 扩大到已实现的发行主体、宣传操盘、认购、期货多空杠杆/债务、退市、继承和20种剧情及全球新闻；六个后继场次已具备软件验证的观察包和公共准备定义，实机尚未执行。

4096/8192尚未压测，不是已支持容量；尚未 Workshop 首发。

## 工程与资源

默认 Maven 实测3.10.0，Java25.0.4.1，编译目标21。源码及增量构建/候选包峰值预留256MiB，08:43 UTC C盘可用74,891,210,752字节；完整旧库存加512MiB保守增长上界仍低于当日有效配额，未删除旧资料。原件及容量保护按通用存储策略复核，不将历史构建永久保留为默认。

跨产品可复用的是整数资金/资产守恒用例和清单打包合同。当前金融策略专属于本产品；工具留在tools内部，公共实机入口直接复用，不另建host/DLL/启动器。未来有第二个消费者时再提取稳定Java模块，避免在接口未验证前扩散原型。
