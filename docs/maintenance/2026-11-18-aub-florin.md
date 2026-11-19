# 自动升级建筑：Florin 迁移进行中

执行机器 `desktop-3fevhd2-1c74096080`，Steam CK3 1.21.0 / build26622941。2026-11-18T12:49:39Z，现有提取器在实际 `great_project_cathedral_02` 上拒绝缺少普通金币费用，原始失败保留在 `D:/ck3-state/upgrade-20261118/aub-florin-source-review/`。新版地产通过 `primary_district` 指向区域，再由区域指定 `primary_building`；建筑目录新增多层子目录，旧仅扫描根目录的327条结果不是完整新版库存。费用、区域类型及排除规则必须重新核对，不能沿用旧605边合同冒称新版已适配。

先落实生成脚本拆分约定：原两个大型文件拆成80个脚本文件，循环／支付／分派公共定义保留在原入口，165条链分成17组，605个目标门槛分成61组；每文件1–10个顶层定义。原全量render仍作为对照，回归逐个比较完整Clausewitz定义且恰好出现一次，不改原收费、门槛、15次配额及原玩法断言。正式构建白名单由同一生成器清单派生，当前95运行文件，排除fixture及README；生成器check与原构建／缓存／错误合同回归接在既有CI入口内。

首次合并静态检查发现支付校验依赖旧文件顺序：排序后的升级分片先出现参数化调用，旧提取器把它当作函数定义，产生六项真实失败。校验现在明确读取顶层支付定义，新增真实排序后输入的回归，原资金分支和成功计数断言保留。原失败日志不覆盖。

实际结果：生成器check通过，构建器16项通过（含逐定义不变、无重复、每文件上限、费用篡改拒绝、严格缓存和可复现构建）；generator与static validator两个完整文件严格mypy通过，follow-imports=skip。最终实际安装源静态检查仍为RED，唯余上述新版建筑提取失败；源码拆分通过不等于Florin兼容、实机业务或发布。证据见[aub-generated-split-software.json](evidence/2026-11-18-ck3-1210-desktop-3fevhd2-1c74096080/aub-generated-split-software.json)。本次没有改产品版本或Steam发布，下一步继续递归新版建筑／区域数据、费用与升级作用域迁移，然后跑原代表性业务矩阵及生产GUI。外置原件2026-12-18复核。

2026-11-18T14:24:21Z，递归提取器在本机完整安装源通过：3,548个建筑定义、2,644条原版升级边，其中大工程整链排除61条，普通升级2,583条／677条链；七种地产的primary_district→primary_building解析完成。大工程识别采用新版great_project_type并兼容旧标记，不再按普通金币建筑误收。首轮实际提取发现district_level_requirement还有脚本值块，已保留完整块而非强转标量；原失败日志保留。23项既有入口回归、完整提取器严格mypy和实际完整提取通过，版本／目录布局及历史快照覆盖拒绝均有回归。旧冻结数据未覆盖，新图仅在外置目录待采用；生产生成器、运行作用域、费用／配额／回滚业务与GUI尚未取得Florin资格，不改版本、不发布。证据见[aub-florin-recursive-extractor.json](evidence/2026-11-18-ck3-1210-desktop-3fevhd2-1c74096080/aub-florin-recursive-extractor.json)。

本机已闭场XQOL R5/R6的重建型shader及160份字节一致的全尺寸预览副本已按存储策略回收；原截图、日志、正式包、fixture及当前CHT物理保存仍在，唯一MRM暖缓存未动。删除路径不可再读取，保留原图可复核相同像素。共8,620文件／541,102,740逻辑字节，详细时间、容量及保留用途见[清理回执](evidence/2026-11-18-ck3-1210-desktop-3fevhd2-1c74096080/storage-closed-xqol-ui-and-previews-cleanup.json)。

2026-11-18后继：4.0.4／1.21.0开发候选已接入新冻结图，历史快照不覆盖。677链与2,583边生成至329个脚本分片，加固定资源共344运行文件；每分片最多10个顶层定义。省份入口按已建主建筑进入各活跃区域一次，目标资格委托原版`can_start_building_construction_for_owner`，原生即时升级与成功判定均在同一区域，成功后才走原支付／计数函数。原特殊建筑先删再插的路径替换为新版原生原位升级；无损拒绝行为仍待实机证明。15日、15次成功配额、资金策略、超直辖暂停、继承逻辑保留。

只读Native来源复核发现贸易站可由宿主省份以外的人物持有；候选仅在trade_post_district内严格检查owner，外来或未知owner保存为排除区域，逐省清理旧scope，比较先检查存在。未把仅适用于贸易站的district_owning_title泛用于普通区域。尚未发现entrepot第三方owner的原版路径，不将搜索缺失写成运行期证明。

26项完整合同／构建回归通过，generator、extractor、data loader与static validator完整文件严格mypy通过（follow-imports=skip）；最终安装源比对、344文件严格白名单和构建check通过。期间真实失败包括旧建筑名、神龛实际仅四档及第五档其他建筑只需四级区域的验收假设、旧公开文案版本检查，均保留日志后修正。旧1.19/1.20政策断言明确留在历史快照，新版另验当前链与资格。详见[aub-florin-runtime-software.json](evidence/2026-11-18-ck3-1210-desktop-3fevhd2-1c74096080/aub-florin-runtime-software.json)。本阶段未启动Game、未上线Steam、未发布；旧核心实机fixture尚待迁移，不能把静态fixture检查记作新版业务通过。接着进行最小引擎能力验收与原代表性业务矩阵迁移。

最小district-probe-1210场景沿既有prepare_aub入口单独准备，旧完整fixture在Florin上明确拒绝，避免误跑未迁移的旧建筑名。新场景直接调用当前生产链与省份分派，检查原生区域资格、单级升级、精确个人扣费与计数、主建筑修改时省份遍历不重访（同时确认下一档资格和未触15次上限）、资金不足零变化。固定1066阿普利亚Robert，最多一天、不保存，未覆盖的完整资金／直辖／部落／特殊／曼荼罗／继承及真实生产GUI仍为发布要求。准备器完整文件严格mypy通过；已有CI夹具入口6项通过；实际准备成功，334个生产及夹具脚本以既有Java parser四进程、每进程192MiB完成通用语法解析，零失败，仅语法、不是1.21引擎语义或实机。见[准备记录](evidence/2026-11-18-ck3-1210-desktop-3fevhd2-1c74096080/aub-florin-probe-preparation.json)。

本机R0001已于2026-11-18T15:58:39Z正常菜单退出、原Popen0、keeper/CAS闭合，1066-09-15／零推进／零SAVE。8标记取得7个、1个综合断言失败；实际区域castle01→02、精确个人金币扣除及计数1、余额不足时源建筑与余额／计数零变化通过。`primary_mutation_no_repeat_before_cap`的档位／castle03资格／计数子条件未独立记录，随后夹具归一化已覆盖当时状态，失败子条件仍UNKNOWN，不据此断言引擎重复遍历。唯一445B脚本错误来自夹具重复授予已拥有的城垛革新。[R1原件与失败](evidence/2026-11-18-ck3-1210-desktop-3fevhd2-1c74096080/aub-florin-district-R0001-red.json)；公共verify正确拒绝未通过业务证据，本次未发布。

后继只读原版核实：Florin主地产建筑按目标省份文化时代解锁；给payer文化增加三项革新不能保证省份文化达到高中世纪。新夹具仅在隔离场景推进首都省份所属共享文化时代，实际读回时代，再分别记录档位、下一档资格和0–15计数；原综合断言不放松。6项既有夹具回归、准备器严格类型检查、实际prepare及两个受影响夹具脚本Java语法解析通过，生产脚本未改。R1闭场派生shader精确回收4,184文件／183,645,204逻辑字节，零失败，原日志、截图、输入／正式包和唯一MRM暖缓存保留。[夹具修复与清理](evidence/2026-11-18-ck3-1210-desktop-3fevhd2-1c74096080/aub-florin-district-R0001-fixture-fix.json)。新场景实机尚待执行，不追改R1事实。

本机R0002（本地2026-11-19）沿用完全相同344文件产品包，仅更换上述夹具，9/9标记各一次、零FAIL、error.log=0。原生读回：目标省份文化已到高中世纪；整省成功升级5次，主建筑恰为castle02，castle03原生资格已满足，且计数未到15上限，未发生第二档继续升级。直接区域升级的个人扣费／计数精确成立，余额不足零扣费／源建筑不变也通过。1066-09-15／零游戏日／零SAVE，2026-11-18T16:39:30Z经菜单正常退出、原Popen0、keeper/CAS闭合；公共verify对这个最小场景返回PASS，product_release_pass与native_capability_pass仍false。无DLL注入，无新版bridge/ABI资格，也无完整AUB业务／发布资格。[R2记录](evidence/2026-11-18-ck3-1210-desktop-3fevhd2-1c74096080/aub-florin-district-R0002-pass.json)。继续迁移原完整代表性矩阵及生产GUI；不把R2新读数补写为R1当时的子条件。

资金／直辖部分沿原aubt.0..6及日历／阈值辅助事件准备成显式部分场景：17个原PASS条件的完整Clausewitz AST在建筑ID反向归一后逐条相同。新兵营代表为castle_garrison_1..5，准备阶段补目标省份早期中世纪与城堡区域二级，原150+150不足以独立支付250的分账负例改为从当前tier2费用计算每账户cost/2+1；原余额／建筑／计数断言不变。去掉夹具自动启用，必须先操作真实生产六选一面板的优先国库＋超直辖继续，再点隔离验收启动决议；循环／零直辖／超额暂停与恢复／三种账户及不合并支付仍走原生产路径。其余原建筑、配额、曼荼罗、特殊、继承与禁用GUI保持待验，未由此场景覆盖。

8项既有夹具CI回归通过，含17条件逐条不变与真实prepare→合同消费；准备器完整文件严格mypy通过，5个夹具脚本Java通用语法解析通过；不是实机完成。首轮测试收集器只看if漏掉else_if中的直辖归零条件，修正后全部17项匹配，保留原失败。闭场R2派生shader与第二批字节一致预览副本共回收4,377文件／377,019,920逻辑字节，零失败；原图／日志／源码／正式包及唯一MRM暖缓存保留，已删除派生路径不可读取。见[资金场景准备与清理](evidence/2026-11-18-ck3-1210-desktop-3fevhd2-1c74096080/aub-florin-money-preparation.json)。

本机资金R0003在主菜单出现两条非法事件ID错误：Florin拒绝数字部分为0的`aubt.0`，夹具入口定义与决议引用均带此旧编号。EXE的Jomini错误字符串及原版事件说明支持该诊断；多文件重复namespace和scope=none均有原版支持。只取得READY一个标记，17项资金业务未执行，1066-09-15／零推进／零SAVE。原runner于2026-11-18T18:40:51Z超时发出标题栏关闭请求；后续直接检查退出对话框，保持不保存并退出桌面，23:24:50Z原Popen0，keeper/CAS闭合。超时事实保留，process_pass仍false，不把最终退出0追认为场次通过。[R3失败记录](evidence/2026-11-18-ck3-1210-desktop-3fevhd2-1c74096080/aub-florin-money-R0003-red.json)。

入口定义和引用改为`aubt.900`，原17项PASS条件不变；prepare在产生输出前校验事件编号1..9999、每文件namespace、重复定义以及调用中的非法编号。新增回归分别篡改定义／调用为0和10000，均在写盘前拒绝；现有入口9项通过、准备器完整严格mypy通过。通用语法解析不能代替事件ID语义检查，本轮错误证明此边界；修复尚待新场实机确认，产品及Steam发布均未发生。

R3闭场后按本机用途清理：4,184个可重建shader／183,734,611逻辑字节回收；长时间保活的333份展开审计stdout／183,904,246字节逐项校验后压缩为29,998,976字节ZIP，保留所有原始载荷、原argv/result及完整journal。展开stdout路径已不可直接读取，但可按ZIP成员和SHA256恢复相同字节，不追认旧FileID。首轮压缩完成后超过16MiB预估，未进行删除；复用实际已有压缩包重新逐项校验后才释放展开副本。两批精确删除均零失败；唯一MRM暖缓存、CHT物理存档及后续mod所需旧原版源均保留。[容量与归档记录](evidence/2026-11-18-ck3-1210-desktop-3fevhd2-1c74096080/storage-aub-money-R0003-closed.json)。

本机R0004已实际验证完整六选一界面、优先国库／超直辖继续的确认文本及启用后的原生flag条件；资金矩阵前6/17条件各通过一次（默认策略、直辖归零、优先国库单级、零余量继续、超额暂停、恢复继续）。随后礼仪信件阻止继续推进，1066-10-21／36自然日／零SAVE；没有以鼠标或键盘选择事件。保留实际Native实例／定义ID UNKNOWN，静态正文只支持pam_decision_events.0011的来源候选，不外推为实际实例。raw error.log为2,520字节组合格式标签错误，尚未归因，不能称日志为空。23:59:09Z正常菜单退出、原Popen0、无超时关闭请求、keeper/CAS闭合；公共verify正确拒绝未完成的17项。[R4部分验收](evidence/2026-11-18-ck3-1210-desktop-3fevhd2-1c74096080/aub-florin-money-R0004-partial.json)。

后继仅调整隔离夹具：原版pam_decisions.txt4044–4066、4269–4292向发行者同faith的其他统治者投递0011；新场在任何日历推进前，将一次性payer改为现行hellenic_pagan，并要求实际faith、doctrine_no_head与不存在faith.religious_head同时读回。该faith定义／无head教义及set_character_faith调用均有当前原版来源，缺少readback就FAIL；不撤回R4事件、不追改结果、不改产品或17项原PASS条件。此调整仅隔离已知无关投递路径，不保证不存在其他随机事件，也未解决或归因组合格式标签错误。修改后9项入口回归（含17项原条件AST相同）及准备器完整严格mypy通过；新隔离条件的实机读回尚待执行。

本机R0005：无宗教领袖三项实际读回通过，资金前9/17条件各一次（较R4增加超额继续、旧无暂停flag继续、禁用零副作用）；没有业务FAIL。推进到1066-11-20／66自然日后，Robert原版bookmark.1070开局事件读取不存在的pope，引发tooltip脚本错误并阻断剩余矩阵。这是新夹具改变信仰后暴露的原版依赖，不能算产品通过；该事件无官方完成flag守卫，不能发明flag跳过。未选择事件，00:47:03Z正常菜单退出、原Popen0、无标题栏强制关闭请求、keeper/CAS闭合，零SAVE。[R5失败原件](evidence/2026-11-18-ck3-1210-desktop-3fevhd2-1c74096080/aub-florin-money-R0005-red.json)。日志字节与实际上限比较见原件；watcher只看debug.log的不足另列，原error.log不截断。

后续只读来源将R4信件候选收窄为pam_bull_events.0004：其允许正文复用0011，但opening及“就这样吧”按钮同时匹配；仍不追认为Native实例。Pope专用bull决策存在现行角色变量冷却：bulls_decisions.txt497–501／546–549的enact_a_bull_tenet_permitted_cooldown，以及789–793／838–841的enact_a_bull_tenet_forbidden_cooldown，原版effect期限五年。新夹具可在首日之前对已核实际head预置并读回这两个冷却，保留payer原信仰；预置不等于曾执行决策，也不能撤销已排程事件。Robert开局剧情仍须另行处理或显式更换测试payer，不能以没有找到setter为由编造通用decision cooldown接口。

后继夹具显式更换payer：仍从普通书签选Robert1128，首日之前按原版set_player_character接口切换至实际Roger1132；不再改信仰、不取消事件、不复用Robert身份资格。新玩家必须实际为1132／原Catholic信仰／自有城堡首府，并在实际宗教领袖上预置后读回两项既有五年bull变量，才允许启动矩阵；生产六选一也重新在Roger身上操作。当前历史来源为norman.txt647–678、k_sicily头衔历史495–498等；1129实际是另一人物，未使用。原版game_start.txt4117–4119提供当前player作用域切换例；没有找到Roger专属开局派发，不外推为无随机事件。9项回归及完整准备器严格mypy通过，17原条件AST仍全部相同；新角色／冷却实际读回与其余8项资金条件仍待新场验证。

本机R0006已实际读回Roger／Catholic／自有城堡及实际领袖两项既有bull冷却，生产六选一重新操作完成；4/17资金条件通过。1066-09-25／10自然日时贤阶普通事件暂停日历，未选择；静态标题／正文／按钮对应tgp_china_career.0010，但Native实例及定义ID仍未观测。80B“科孚商会”本地化提示在资金矩阵前已出现，之后未增加；无业务FAIL或Script system error。02:21:40Z正常退出、原Popen0、keeper/CAS闭合，零SAVE；公共verify拒绝未完成17项。[R6原件](evidence/2026-11-18-ck3-1210-desktop-3fevhd2-1c74096080/aub-florin-money-R0006-partial.json)。

原版character_levels.txt295–371的贤阶派发要求this!=top_liege，没有一次性intro完成flag。新夹具在变更政体前使用当前原版完整独立事务（00_almohad_invasion_effects.txt254–265及正常交互1620–1629）：create_title_and_vassal_change(type=independency,add_claim_on_loss=no)→becomes_independent→resolve，事务不复用；不伪造flag、不删除队列。独立在变政体前后均须读回，且后者必须has_treasury；原17个PASS条件与产品不变。事务会触发原版on-actions，不预称零副作用；新独立状态仍待新场实机确认。


本机资金R0007完整跑通17项原资金／直辖条件，22个标记各一次，零业务FAIL／Script system error；独立事务前后、Catholic／实际head两冷却与国库资格实际读回成功。原344文件产品包未变。raw error.log仍有4,320B组合格式标签错误，故公共verify继续BLOCKED，整体passed=false；不能用17项通过代替日志或全部产品通过。最后直接可见1066-12-13／89日；DONE在watcher收尾期间出现，原bounded_wall_timeout保留，精确最终暂停日期UNKNOWN。04:11:03Z正常菜单退出、原Popen0，无WM_CLOSE，keeper/CAS闭合，零SAVE。[R7原件](evidence/2026-11-18-ck3-1210-desktop-3fevhd2-1c74096080/aub-florin-money-R0007-seventeen-pass-formatter-open.json)。

下一候选在现行中文house_relation_latest_change_amount的#weak后仅补ASCII空格，保留getter、=+%^标志及全角括号；原版英文同位置已有空格。沿已有localization/replace路径，新增单键文件，345运行文件；这是来源明确的语法候选，尚未取得新场零错误或运行期归因。九语言费用说明同步指向1.21.0。发布构建器实际拒绝过期费用版本和被篡改空格／getter的覆盖；manifest改为入口校验后构造明确TypedDict，拒绝bool／浮点format_version及非法tag形状。37项回归通过，三完整改动文件严格mypy通过；本机原版全图核对、329生成脚本检查通过，更新后的manifest往返／坏类型回归和重复构建逐字节一致检查通过。测试中真实失败与修复见[软件记录](evidence/2026-11-18-ck3-1210-desktop-3fevhd2-1c74096080/aub-florin-formatter-candidate-software.json)。

夹具DONE改为已知专用可见事件，空选项，请求正常单人事件暂停；新场仍需读回实际画面／日期，不预称已暂停。17原条件不改，剩余19条建筑／配额／继承及生产禁用GUI继续为必验。Steam全程离线，未发布AUB。闭场shader按清单精确回收，展开审计／旧EXE／已闭prepare等逐字节校验后无损归档，全部删除零失败；27个重复PNG路径以相同字节硬链接保留，旧FileID不复用。当前原图／错误／CHT物理存档与唯一暖缓存继续保留；原路径可读性、归档及期限见[存储目录](evidence/2026-11-18-ck3-1210-desktop-3fevhd2-1c74096080/storage-closed-gui-lossless-20261119.json)。


资金R0008在加载阶段发现可见完成事件aubt.800缺theme（65B错误）；尚未启动世界、0/22标记、零日／SAVE。直接回主菜单正常退出，04:57:43Z原Popen0／keeper及CAS闭合，无WM_CLOSE；未继续用带启动错误的场景验收，不取得产品或格式修复资格。[R8失败](evidence/2026-11-18-ck3-1210-desktop-3fevhd2-1c74096080/aub-florin-money-R0008-red-theme.json)。当前原版realm主题定义473–486及可见无portrait的global_culture.0005提供合法结构；仅补theme=realm。准备器在写出前拒绝无theme的可见角色事件，真实生产入口回归10项及完整严格mypy通过，原17条件不变；新场实际暂停与格式诊断仍待复测。

本轮R8可重建shader精确回收4,188文件／183,984,751B；另提前到期回收已发布MRM／Ox／CHT的48条过渡EULA／隐私／加载／书签截图路径，独立载荷48,196,489B。排除了现行公共记录及活跃anchor直接引用，保留实际世界、业务UI、失败诊断、退出及发布证据；已退役过渡像素不可读取，不制作替代原件。两批零失败，精确计划／回执保留；[修复来源、软件检查与清理](evidence/2026-11-18-ck3-1210-desktop-3fevhd2-1c74096080/aub-florin-visible-theme-fix-and-storage.json)。
