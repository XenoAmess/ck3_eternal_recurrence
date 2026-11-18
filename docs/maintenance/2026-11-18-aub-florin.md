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
