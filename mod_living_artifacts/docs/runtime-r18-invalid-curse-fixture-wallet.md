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
