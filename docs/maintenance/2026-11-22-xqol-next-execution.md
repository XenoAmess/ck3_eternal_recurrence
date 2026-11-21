# XQOL 1.1.3 / current267 接续执行包

本包为 SourceOnly 候选，实机排在当前白绮组 DJC 完成之后。产品为
`mod_xenoamess_quality_of_life`，canonical `3798133925`，上一公开版1.1.0；
现1.1.3候选尚未发布，旧 `xqol-v1.1.2` 不移动。目标机器
`desktop-3fevhd2-1c74096080`，CK3 1.21.0.3 /26785313 /859f0d…0aa28。
本包没有 Game、JVM、Native、Steam、Git或发布操作；最终执行状态是 PENDING。

## 已有资格和新版差异

- 当前28个runtime文件991266B逐SHA与已封267软件回执相同，没有再跑原12项测试或28文件双构建。
  原双构建manifest `b897ee81bc1fbc4ca989abf4911c67b92dde12643818fef7f5dea02215eaf766`、
  ZIP `03eb3ca92ca1ee34b30cfcbb598f2e1c540324a122cef1a39e62608d3849153f` 是候选软件资格，
  不是正式tag身份。原old-pin exit1和缺Workshop依赖的static exit1仍保留。
- 19份声明输入中18份原字节未变，唯一政府文件当前为40825B /5f271469…4623f。
  三个实际行政机制政府键的完整当前定义已解析和资格检查；旧bd6e政府全文没有保留，
  不声称旧新全文语义等价。此次绑定没有修改继任投影、玩法、滑条或九语正文。
- 简中118B替换仅为 `#weak` 后增加一个空格，保留完整金额表达式。当前补丁SHA
  `41ba1efe9cc6c295a83522ab032edcc3bd71b3c3c7afddff88a9ae2f5fa5a982`。
  这项源修复不能证明R4的17条1530B诊断都源自同一key。
- R4完整27个核心marker/零FAIL/24日/正常退出，只属于266，且原1530B错误仍在。
  R6的宋帝资格、空error.log和取消0/1/49/50读回50，只属于266；51只有draft，
  其余取消、保存、恢复与官职UI没有通过。旧1.20的scope关闭及历史公开1.1.0也不变成267通过。

精确来源为 `xqol-current-government-a01.json`、`xqol-florin-core-R0004-pass.json`、
`xqol-florin-ui-R0006-partial.json` 及 `remaining-products-impact-map2-a195/REVIEW.md`。

## 原合同与最短接续

|单元|应取得的新鲜事实|既有入口及界限|当前通道|
|---|---|---|---|
|Saved启动|原Robert1128/.15，桥只消费一次；原Song资格仍实读|本包两个producer的显式 `--saved-entry-bridge`；仅一份fixture|源码及NoGame就绪，自动启动实际NOT_RUN|
|官职与开关|当前实际Song/政体/法、自然候选及同一玩家行off/on/restored扣分1000000，真实AI任命和holder/heir读回|`xqol_florin_ui.json`原civic/military检查；不能用core生产effect调用代替UI|无已部署XQOL后台入口，PENDING|
|滑条|真实打开、原50、生产Save100后重开100、恢复50后重开50及干净地图；代表取消仍应实读|旧精简 `ui_tail` 原4步可作最短独立单元。若申报 `migration-ui-1210`，其既有25项不能把四步冒全P|缺实际控件/事件选项入口，PENDING|
|118B修复|实际负数家族关系对象与最新变化值，原新闻/hover实际文本及完整未过滤error.log|只验证新增分隔修复；不构造字符串冒render，不借AUB同key通过|无对应正式只读/hover入口，PENDING|
|核心|原继任/移除/死亡/转封和真实索款/改信/赎囚/释放后果|已有完整 `migration-core-1210` 27marker，60自然日；不改谓词，也不把旧266场改成267P|Saved桥仅恢复原引擎入口；Core/Date/正常Quit依本场exact资格，普通事件可能阻塞|
|防御与反向合同|原免费/付费排除、去重、资源及合同方向|`xqol_defense_and_ui.json`原23marker/33日，独立于滑条；不因新补丁扩大为全宗教或新增矩阵|旧专用adapter不能沿旧Full执行，仍独立PENDING|

这里没有将历史计划每个未覆盖项新设为本轮硬门，也没有删掉现有case义务。
最短下一场是零日Saved UI资格加原精简slider smoke；它只授自己的有限事实。
当前267真正新增输入的政府UI、未闭UI及118B负数render继续分别签收，不能由启动、
六项NoGame回归或旧核心27marker推全产品发布。若选择运行现完整Florin core/UI/defense
case，必须按各自原清单签收；本包不隐式把这些case改成子集PASS。

## Saved桥候选及原入口

只修改既有 `tools/prepare_xqol_1_20_fixture.py`、`tools/prepare_xqol_ui_fixture.py`
及其原回归文件，未加生产模块。默认celestial/admin/UI输出的完整树哈希与原件相同。
Saved模式去掉同场新开局hook，只添加三份原成熟ScriptedGui/gui/scripted_widget接线，
`trigger_when` 配合 `on_start`，GetPlayer.MakeScope为实际root，1×1透明、不置顶不抢焦点。
原human1128、alive、1066.9.15、未消费及未初始化条件在IsShown和effect中完全相同；
先保存自有once flag，再进入原准备。Core仍投递原 `zqa120.1 days=1` 和原daily链；
UI仍使用原Song预条件、一次切换及原AI三域信仰准备，不设置产品开关、pending或滑条。
冷载已消费原件、已经是Song或不同日期时跳过；不编辑原savedPair，也不补造marker。
Core与UI fixture不得同时挂载。

```text
python -B tools/prepare_xqol_1_20_fixture.py --repo <actual-repo> --output <new-core-fixture> --scenario celestial --saved-entry-bridge
python -B tools/prepare_xqol_ui_fixture.py --repo <actual-repo> --output <new-ui-fixture> --saved-entry-bridge
```

以上两种既有CLI在本包外置源码上实际exit0，识别实际859F/26785313；六个新增回归全P，
三个完整修改模块沿现有follow-imports=skip/no-cache配置类型检查0。首次外置mypy
未设MYPYPATH且增强check-untyped产生11条旧代码/导入诊断，原失败保留，后续使用正式
原配置及typed新UI返回；没有改老代码来洗掉旧诊断。所有原核心marker、effect、
60日上限和runtime28均未改，桥实机调用/正常退出仍NOT_RUN。

## 最小后台接线需求

当前Native owner已明确：没有部署XQOL toggle/slider/governor/appointment/负数新闻hover；
AUB决策raw只到SourceOnly/部分软件，没有正式owner。v24/v26仅known letter0003/.a，
v27仅GDP0500/.a，不能把它们当通用SelectEvent或xqol.100。

1. 固定决策只需现有六个 `xqol_enable/disable_*` 与 `xqol_mass_conversion_decision`：
   真正打开/查询/选中/CanConfirm/一次Confirm，后态另读。复用已证AUB raw结构，按
   XQOL实际键和当前owner实现窄接线；不要求FullSDK或任意决策执行器。
2. `xqol.100` 只绑定实际当前instance、所属玩家、真实widget、两项定义
   `xqol_mass_conversion_event_confirm/cancel` 和fresh nativeCan。确认才提交draft并dispatch，
   取消只移除draft。现letter/GDP白名单不扩用，不能直接fixture写变量代UI通过。
3. 滑条实际控件 `xqol_conversion_threshold_scrollbar` /handle 与原101条route，
   只需0..100 typed状态/真实生产输入及提交后重新打开读回；不调用任意ScriptedGui充控件。
4. 官职只读当前title-law/候选/score并做限定普通appointment/confirm；自然候选不足正规PENDING，
   不补trait/flag/分数。负数家族关系需要真实对象/值和官方文本来源，不能只返回补丁字符串。

由Native唯一集成与Java正式消费者维护现路径；本包没有启动这几项Native大改。

## Prepare、预算与退出

现主registry没有 `migration-core-1210` / `migration-ui-1210`，旧
`legacy_celestial_source` 明确blocked；旧 `ui_tail` ready仅是旧adapter声明，
带SCREEN fallback不符合当前静默要求。已有外置 `gui-products-a26.json` 包含两个Florin
case，曾plan exit0，但其旧runtime/lease pins不能直接执行。Java应沿已有公共prepare，
以当前产品28清单、桥fixture和当场common runtime/genuineGSV Saved配置构造新private selection。

```text
python -B tools/ck3_mod_acceptance.py prepare --runtime <fresh-common-selection> --products <fresh-XQOL-selection> --product xqol --case migration-ui-1210 --case-inputs <actual-inputs> --prepare-output <new-root>
```

没有mint request/deadline、ready、argv或新profile，本包JSON这些字段为空。SDK/Native未知
不妨碍独立源工作，但未具备对应真实后台动作时不启动计时等待，更不恢复前台点击。
如果先制备可复用Song世界，DJC后可单独做一次“Saved桥资格→三个原Song marker及fresh
Core→必要的一次真实checkpoint→正常Quit”的零日baseline场；它没有开关/滑条/官职业务信用。
后继同一物理Saved世界冷载只读取已消费状态，不重复准备。只有实际需要保存该世界时才单独报价SAVE，
不为等控件能力让baseline场长期空跑。
已有初始f488 B0可作明确的候选Saved来源（Robert/.15，非纯原版；旧DES残留要披露），
不是已合格XQOL源。正式制备仍核实际人类/宋帝原条件；复制一次，不编辑或重写原保存。

前瞻profile上界24MiB，含B0单次12472221B复制、runtime991266B、fixture小于100KiB、
必要staging/ZIP/config/NTFS余量，不含Game。Game可先按独立1GiB磁盘包络规划；Game内存沿实际Root场的13GiB Job上限另评估，
Java沿实际Frozen/operator argv；这些都是未准入的前瞻。物理SAVE若实际证明需求出现另按256MiB报价，零日UI不强加保存。
Core原60日、UI原1日（目标0日）、defense原33日和各原墙钟期限均不改；普通事件阻塞时只处理
已实际支持的精确原版选项，未知立即停，不延时/重放UNKNOWN。结束沿真实current owner正常Quit，
以creator/GSV Popen0、Job0和lease释放签收，不用ACK当退出。

## 正常发布及独立cache加载

业务有限范围和未测项明确签收后，由正式Git owner正常提交推送，建立新的
`xqol-v1.1.3`（不动旧tag），运行原builder的 `--release --workshop-item-id 3798133925`
并绑定exact tag/source。候选零revision构建不能替代正式身份；不重跑已过12软件测试来充实机。
准备增量changelog相对公开1.1.0，保留缩减范围；标题/完整description/Change Notes/兼容标签
沿现发布规范。必要上线仅覆盖canonical上传、公开全文回读及实际SDK下载，随后重新离线。
内层descriptor无ID；外层指向实际目标并使用3798133925。

发布后只复用公共 `workshop_cache`：实际Steam下载28文件与正式manifest的大小/SHA精确核对，
独立最小化菜单场只挂该真实cache、无业务fixture；保存实际挂载路径/初始化日志或现公共组合加载证据，
正常退出。不新游戏、不选人、不重复业务，也不新增VFS/FullSDK门。现有builder实际验证语法为
`--verify <downloaded-cache> --manifest <formal-manifest> --workshop-cache`。
正式构建/发布轻量输出可先报8MiB，独立cache菜单场前瞻1GiB，全部由Root未来按fresh容量单独准入。

候选只写D，Root36-a343同池中的4MiB顺序子额，不新增36、不退还旧spent；C新增0。
本包执行数据、逐文件source pins与实际检查退出见外置manifest及 `execution-plan.json`。

## Saved生命周期依据补充（a02，仅来源与文档）

Saved模式的实际入口是 `gui/scripted_widgets/<prefix>_saved_entry_widgets.txt` 注册的
具名window实例。GetPlayer有效后，其具名state动态计算
`GetScriptedGui(...).IsShown( GuiScope.SetRoot( GetPlayer.MakeScope ).End )`，
条件进入该state才由 `on_start` 调用同root的 `Execute`，再受effect内完全相同的守卫约束。
这不是为某个on_action取了新名字；Saved输出已将原new-game hook替换成注释，
不等待 `on_game_start_after_lobby`，也没有请求operator手动调用ScriptedGui。

当前安装两份stock已按完整SHA复核：`game/gui/hud.gui`239779B，
SHA `35bb7ceffe17222a7de8796cec5a676349e2294de406df261f623ce48d112f01`，
312–324行是动态 `trigger_when`→`on_start`；
`game/gui/window_pam_christian_church.gui`81897B，
SHA `82c6a6a1a09aab0fc7f53492d1bffc17e8f4fe5e5d08a12e08e3b38d67eefb46`，
49–53行由 `GetScriptedGui(...).IsShown` 进入state。stock这些行证明生命周期/API用法；
它们本身不证明任意mod已被实例化，GetPlayer-root Execute组合的实际来源为下列成功S0。

同26785313的真实成功Saved启动在
`D:/ck3-state/upgrade-20261118/djc-ordinary-v3-s0-profile-a231`。
其 `fixture.shared-manifest.json`1987B/SHA
`6f37ddf4c2bf2b7db816181adc9a24634402270964f4c659758fdac5df68f573`
以及 `prepared/prepared-case.json.profile_files` 绑定实际装载三叶：

- `common/scripted_guis/djcg_saved_entry_guis.txt`1346B，
  SHA `1ff4a6ce1c06661068ca1d22fbb5489dfd3c3b6a8bc853dfe612beb2be4138b8`；
- `gui/djcg_saved_entry_bridge.gui`1239B，
  SHA `39dc41e2bfabd20fa746d61470c25dd1e2bb3eeed588f73f992e4356f07563ea`；
- `gui/scripted_widgets/djcg_saved_entry_widgets.txt`68B，
  SHA `7898b91fb45bcdae6c332a732797979f72322f143d8f8c0db88038887171f964`。

S0的 `djcg_saved_entry_bootstrap` state经namespace替换后，与本包两个实际XQOL生成
window的startup state原文完全相同；1×1透明window属性、widget注册和GetPlayer-root
IsShown/Execute组合共用。fixture guard和准备body按各产品原实际入口改变，不把S0战争
观察器或业务状态带入XQOL。
`actual-S0-closure-a240.json`15946B/SHA
`4e4d6dc854228b21f636ca042fb957e79b4f25681f2b3c1e505427ceff1b556f`
记录该S0 setup marker一次、Game6988实际normal0/Job0。S0后续missing-variable诊断和
raw physical false仍保留，单独复用成功启动事实，不称原S0全部clean。

新XQOL自动执行仍是 **NOT_RUN**。六项回归、两个CLI和类型检查只授软件/结构资格；
首次XQOL场仍须观察自身entry及三个原Song marker、实际Core和正常退出。
完整窗口/pin/相同state实读比较见外置
`a02-lifecycle/startup-lifecycle-provenance.json`3625B/SHA
`73bb801c9a38dd77a99bac6e906f229bdba8b4391c3b07704db29e1ce1410eee`。
