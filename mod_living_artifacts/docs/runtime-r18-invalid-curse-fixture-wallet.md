# R18：诅咒夹具初始钱包错误，装备前停止

`machine_id: pc-20260924rtuf-f11af23c08`，观察截至2026-10-23T03:18Z。EXT 为 `D:/workspace/ck3-living-artifacts-20261022`。本场是 **BLOCKED，0自然日、8次计预算调用、1份保存、五项检查均BLOCKED**；没有提交库存GUI打开或装备动作，没有诅咒业务通过信用。游戏已正常GUI退出，retained OS0、原生cleanup、keeper退出和独立资源释放均有实际证据。产品仍未发布。

## 真实输入故障

c19/a25公共allocate `20261023T024408940213Z-allocate` 分配R0018，fresh后台Steam于02:46:20.407137Z确认offline/true；bound preflight实际0后，public run `20261023T024623182946Z-run` 启动。CK3 PID9324、出生1792723600.2433865，host14080、actor31254、generation1、初始date_raw53144328。

Save01 producer于02:53:13.698415Z实际退出0，保存与同帧原生钱包均为 **276金，预期20金**。引擎原始error.log明确拒绝 `xalw_curse_initialize_effect` 的负数 `add_gold`；来源是旧共享 `prepare_curse_fixture.py:69` 的清空钱包模板。原有256金未扣、随后增加20金，得到276金。此故障属于夹具初始化，不将它写成正式“贵族胃口”付款失败。

该场已冻结的生产者位于 `EXT/runtime/c19/mod_living_artifacts/tools/prepare_curse_fixture.py`。引擎日志6255 B、SHA `664abc14d23505087536ca4cb3fe31cde8e2f08a361dfca27acc75a76027878b` 已在 `EXT/environment/r18-invalid-initial-wallet-a01/actual-engine-error.log` 保留；`decision.json` 为2248 B、SHA `0774dde25a2b9b8edc2cb718e97a0e0398cc62a8b9dedcc24dd97982b60ecb2a`，绑定原请求、Save01、同帧原生快照、冻结生产者及本机时间。

## 合规阻断与原结果

原生库存接口在意图准入前拒绝，随后正常请求Root回调。Root没有点击库存或追加通用原生查询，而是使用既有 `InventoryOpenResponse` 的 `blocked / submitted=false` 分支，先经真实 `parse_opening` 校验，再只写一次原回调结果。回调1163 B、SHA `e12520828ca218e6822b519b923c5d2dadbd3c9fbe5cbc27e3591dd7a8ec47fe`；三项GUI完成证据均为null，理由精确引用实际输入故障。

原 `case-output/living-artifacts-curse-representative-result.json` 于03:12:19.005001Z生成，291128 B、SHA `1e43be7359931cd89d47cedc20b82417102d43741de923564f67ad4cb15a72cc`。状态BLOCKED，五项BLOCKED，`original_action_unknown=false`，case/GUI/business/release均false。原件保留其生成时的 `normal_close_pending=true`，后续正常闭场另有证据；不改写为PASS。

当前主线公共入口显式保留原c19产品表、runtime、Prepared和R18 context，执行verify `20261023T031702446912Z-verify`，原Popen与原工具均实际退出 **2/BLOCKED**，返回同一初始钱包错误。没有重跑游戏或修改旧Prepared。

## 正常闭场

Root直接审阅新原图，确认自动保存未勾选，经三次带canonical receipt的坐标工具操作正常菜单退出桌面。Root回执于03:14:36.035983Z生成，1802 B、SHA `f252ec952ebd8fff06b8b05d9b31d16756965123c85e0f0df86c9e243defc70e`。共享owner保留的OS handle实际signaled/exit0，原生进程03:14:30.998920Z退出0，tree_gone/cleanup_proven均true；host最终报告03:14:38.780136Z结束。完整 `normal-close-result.json` 为8757 B、SHA `88eabda099a0aef5f0e6c75060f33cbd94a970f3a41672601ea3257bac6c9ab7`，`normal_close_qualified=true`。

原public run工具43502实际wait0，原host14080实际wait1，历史库存预意图拒绝保留；0不能代表业务通过。保存服务原工具71650实际退出 **3**，精确表示仅完成1/7保存，未将其记作七保存成功。keeper在03:15:17.384713Z获协作STOP，原allocate工具60287实际wait0；keeper最后序号765、thread_exited=true/failure=null。Root随后独立CAS **766** 完成done/resources=[]，证据 `EXT/environment/r18-screen-resource-close-a01/release.stdout.json`。闭场后台probe `r18-post-close-steam-a01.json` 于03:15:40.594281Z确认offline/true，Steam PID8580、出生FILETIME `134371126587222837`。

## 后继边界

R18失败输入、原Save和原回执保持。后继只修共享旧夹具清款模板，并在首份实际保存之后、库存打开或装备之前交叉验证保存与原生初始钱包；不降低五项业务预期，不热改c19/旧Prepared，不新增平行业务实现。该存量夹具与验收适配器维护不属于Python一期Java接管边界。新候选的真实生产者到消费者回归、完整产品类型检查、正常冻结、新Prepared与新鲜存储准入均须完成后才重开诅咒场次。R17 renewed04冷加载输入继续保护，cold仍NOT_RUN；发布资格保持false。

## 04:18Z续记：共享修复与真正后继R19

共享修复主线提交 `e63243e87712581f24f53565c442fa019fc31ec9`：正向 `remove_short_term_gold = gold` 后增加20金，首份真实保存和同帧原生钱包必须同时为20金，异常在库存打开/装备之前BLOCKED；retained evaluate使用同一守卫。既有测试新增真实Prepared部署来源校验及R18的276金故障路径，要求1保存/0装备/0日/五项BLOCKED。完整产品224项、完整53模块strict及cold四条原命令实际全0；独立vanilla-profile8不冒充SDK continuation。回执 `EXT/environment/curse-fixture-wallet-fix-r18-a01/result.json`，11750 B、SHA `3d7d97a966208fd19855491a45c7d0f172ec9f50053c7dc0facd7bc326d13524`；child task-close实际0。

新c20为 `518468a34fe537a866a9bd5cfd8e6f59724afff4`，唯一parent是c19，仅接上述四文件；干净source及 `archive/living-artifacts-c20-source-20261023` 已保全。normal-successor freezer于03:45:48.128324Z实际0，57文件build于03:47:38.690902Z实际0，正式文件与c19逐字节相同；host/SDK/native源码与既有注册证据一致，未编C++。a29公共plan/prepare/preflight实际0，Prepared为34811 B、SHA `d9551342a12301e362418f57c49d6298a45842b3a6e91fb53f9f869153415447`；未覆盖a25。主体回执 `EXT/environment/c20-offline-a29-preparation-a01/a29-result.json`，SHA `45ca6c86881ebec8fe7f6beae1e27ea0ace6f92752eb540e8f2e966459d5e2f4`。

R18闭场三域与18份媒体实际639990387 B、共享task-close0。为新场次准入，按精确资格仅提前回收六份已失去全文用途、可重建的派生melt：R14 checkpoint04–07、R15 checkpoint01、R13 checkpoint05，合625503972逻辑字节；原Save、摘要、官方melter与recipe均保留，R16/R17/R18未删。旧六路径已不可读取，物理释放归因仍null，不以同名重建物代替旧证据；实际回执 `EXT/environment/storage-r18-actual-close-20261023-a01/reclamation-six-actual.json`，11217 B、SHA `a0c96c31ae621c5c8dffc890e42f10ec8fd88b0da50cf33e0efc54a66945de5d`。

新卡 `EXT/environment/storage-curse-a29-20261023-a01` 的fresh双trigger和真实service→readback→producer compatibility均实际0；admission SHA `75213bd8661cc7ce94d0452bd3f6a0cfac636dba58ad2f771c3c5a07c1bc23ac`。单份own D5GiB/C2GiB含c20离线512MiB、other D512MiB/C0，原callback额外606076928 B不减，quota保守余63365951 B，截止2026-10-24T03:35:29.787627Z；旧a25 future own归0，旧卡保留。192MiB仅为七Save计划源上界，实际源超出须在复制前停写重算，不改真实producer合同。R19不启自动保存服务：Root先核实际source bytes/stat，再单次调用原readback；剩余03–07仅委派同一路径的磁盘生产，GUI/MCP与最终退出仍归Root，不写service0。

真正后继由公共allocate `20261023T035353517416Z-allocate` 分配R0019，keeper a29 PID10948、注册序号768；03:55:00.790175Z后台Steam新鲜offline/true，bound preflight实际0后，public run `20261023T035503519066Z-run` 原工具35505持续运行，CK3 PID6576/出生1792727717.318296、host14072。Save01生产者04:02:53.422834Z实际0；保存与同帧原生钱包均为20金，首守卫通过，Root仅打开一次真实库存后回交原生装备。Save02生产者04:15:26.610835Z实际0。本截点仍0自然日、诅咒五项尚无最终结果；原run/allocate尚未退出，不授curse PASS。

同c20的a30已复用真正R17 renewed04完成公共prepare→绑定plan→preflight，三原wait0，formal-only/无fixture，原Save仅引用未复制；Prepared SHA `252a0b9f0662d735aee73c7dd280c1ab2259678eca35bf84bc3a4aa82f65c8c3`，cold仍NOT_RUN，旧a27保持未消费。a30最终2304100 B/98文件，c20静态离线合394617657 B低于512MiB；现场新增另计同一own5GiB，不重复记一份静态profile。来源 `EXT/environment/cold-public-prepare-r17-c20-a30/result.json`，SHA `fcf97581157007af09e9a7c00440b0d44a84a3620614a1a37fbb1065dbc9ee8a`；child-close实际0，父预留不释放。

## 05:33Z续记：钱包夹具已证实，R19在零值读取处停止

同机器R19实际首Save与同帧原生均20金，R18夹具故障已由真实后继排除。R19推进16自然日、110calls、5Save后，在零钱包保存的共享消费者处BLOCKED；该版本Save省略`alive_data.gold`，原生同暂停钱包为0。五项检查均BLOCKED，不授完整诅咒业务通过。原result SHA `964e733c6035ab26a075ac7ac6067eab0d3d04a28743ba2c7ee5b0db0215ee73`，06/07保存NOT_EXECUTED，原结果与冻结图保持。

R19已正常GUI退出，retained OS0、native0和cleanup独立成立，原public run0、host1、keeper0；CAS799已释放，05:21:59Z后台Steam仍offline/true。current-main公共verify于05:32:37.706035Z实际2/BLOCKED。详细原片段、来源绑定、读取链与下一共享修复在 [R19报告](runtime-r19-curse-representative-and-wallet-fix.md)。原a29存储task-close实际0且0删除；不能继续将上节04:18Z快照当作活跃现场。下一场须新候选、新Prepared与重新计入R19资产后的新预算，a30 cold仍未运行。
