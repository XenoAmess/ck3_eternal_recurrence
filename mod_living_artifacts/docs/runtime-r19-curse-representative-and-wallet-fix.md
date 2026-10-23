# R19：诅咒代表场与夹具初始钱包修复

`machine_id: pc-20260924rtuf-f11af23c08`。EXT 为 `D:/workspace/ck3-living-artifacts-20261022`。最新核据截至 **2026-10-23T05:32:37.706035Z**：R0019/c20/a29 为真实 **BLOCKED：16自然日、110次计预算调用、5份保存、五项均BLOCKED、original_action_unknown=false**。错误为 `ValueError: Nonunique/missing saved field: gold`。首份保存与同帧原生初始钱包均为20金，首守卫和前三份健康中间证据保留，但不授五项通过。现已正常GUI退出、retained OS0/native0且cleanup已证、原run0/host1/allocate0，keeper退出后独立CAS799释放资源；公共verify实际退出2，保持BLOCKED，产品未获发布资格。

## 来源与修复范围

R18 的276金错误输入、五项BLOCKED及正常闭场保留在[原专题](runtime-r18-invalid-curse-fixture-wallet.md)。R19 使用正常后继 c20 `518468a34fe537a866a9bd5cfd8e6f59724afff4`：唯一parent为c19 `0b96283d7d3eed696ffca6ddb3ac2f3459651776`，仅接主线修复 `e63243e87712581f24f53565c442fa019fc31ec9` 的四文件。正式57文件与c19逐字节相同，host/native/请求实现未夹入其他主线变化，未重编C++。

既有夹具生产者改为原生正向 `remove_short_term_gold = gold` 后 `add_gold = 20`；既有诅咒适配器在首个Save之后、库存打开或装备之前同时核对保存与原生钱包必须为20金，异常仍五项BLOCKED。原五项断言、17自然日、7 Save、420次计预算调用合同保持。此次是夹具与验收维护，不将输入修好本身计为正式贵族胃口付款通过。

完整产品224项、完整53模块strict与cold四条原命令的实际资格见 `EXT/environment/curse-fixture-wallet-fix-r18-a01/result.json`，11750 B、SHA `3d7d97a966208fd19855491a45c7d0f172ec9f50053c7dc0facd7bc326d13524`。c20正常冻结、57文件build及a29公共plan→prepare→preflight的原始退出均为0，见 `EXT/environment/c20-offline-a29-preparation-a01/a29-result.json`，13289 B、SHA `45ca6c86881ebec8fe7f6beae1e27ea0ace6f92752eb540e8f2e966459d5e2f4`。这些离线资格不替代本场业务结果。

| 本场固定输入 | 字节数 | SHA-256 |
| --- | ---: | --- |
| `EXT/runtime/runtime.518468a34.json` | 2658 | `528416300887dea0303e6c01c4da42c781e1673590c974b380814bfe5dfee9f4` |
| `EXT/runtime/common-manifest.518468a34.json` | 26313 | `a4f263e7d3e8b2e4cf3a9866f1578b1b2e11c5065ed08c372ba8cdc9a84c4880` |
| `EXT/runtime/prepared/living-curse-a29/prepared-case.json` | 34811 | `d9551342a12301e362418f57c49d6298a45842b3a6e91fb53f9f869153415447` |
| `EXT/builds/candidate-518468a34.manifest.json` | 10569 | `4b277087db82f57fffce1de6993f907dc94677c5fe799e2e4f03151d0c0194b9` |

## 实际启动与动作所有权

公共allocate `20261023T035353517416Z-allocate` 分配 `pc-20260924rtuf-f11af23c08--living-artifacts--R0019`，原工具68408；keeper为 `living-curse-a29`、PID10948，注册序号768。03:55:00.790175Z后台Steam新鲜回执为offline/true，Steam PID8580、出生FILETIME `134371126587222837`，来源为本场 `steam-offline-r19-20261023-a01.json`。bound preflight实际0后，公共run `20261023T035503519066Z-run` 启动，原工具35505；公共子进程13016、host14072，CK3 PID6576、出生 `1792727717.318296`。原场次hold截止 **2026-10-23T05:31:14.580958Z**。

actor31254、generation `1`；血契物品402、贵族胃口物品403、已有判定的未装备候选404。前三份checkpoint均为1066.9.15、date_raw53144328。该截点两条公共operation均尚无 `exit.json`；不能把启动ACK、生产者0或当前进程存活写成run/allocate成功退出。

Root独占GUI、MCP与实际游戏动作。本场不启自动 `living_service_checkpoints`，因此没有自动service进程或service0事实。每份pending Save先核实际源bytes与stat不超过201326592 B（192MiB计划上界），再单次调用既有 `living_checkpoint_readback.py`，完整原producer身份、SHA及存储守卫保持。Save01–02由Root执行；03–07仅委派storage_resume完成同一磁盘生产路径，报告维护者不重复调用、不读全文melt或重parse大Save。

## 前三份真实保存：钱包与血契装备效果

保存与独立同暂停日期原生读回均由原共享消费者闭合。以下健康值单位为Q100000；金币raw `2000000`即20金。前三份压力均15，金币、声望与压力的保存/原生投影一致。

| Save / 自然日 | 真实装备状态 | 原生健康raw | 保存 / 原生金币raw | 原readback实际退出0时间（UTC） |
| --- | --- | ---: | --- | --- |
| 01 / 0 | 血契未装备；胃口未装备 | `466160` | `2000000` / `2000000` | 04:02:53.422834Z，PID13544 |
| 02 / 0 | 血契已装备；胃口未装备 | `346160` | `2000000` / `2000000` | 04:15:26.610835Z，PID10732 |
| 03 / 0 | 血契已卸下；胃口未装备 | `466160` | `2000000` / `2000000` | 04:23:27.831965Z，PID6956 |

因此前三份中间证据实际呈现装备后健康下降1.2、卸装恢复至原值，且同日钱包/压力不变。候选404在三份投影中均未装备。全合同仍须七份保存及真实动作审计的最终evaluate，不能提前把该中间结论写成五项全PASS。

| 小型checkpoint投影（本场 `case-output/`） | 字节数 | SHA-256 |
| --- | ---: | --- |
| `curse-checkpoint-01.json` | 19276 | `c1179bffa1c96a53e0dda9b91d8e9c2d2f95961b8a4b8aa0effe6a7ebba0267b` |
| `curse-checkpoint-02.json` | 19275 | `95c77d17d8db8b6f9f4e5421680ecd045bd065e861724ba524b1c4429b01f4cb` |
| `curse-checkpoint-03.json` | 19276 | `3f65715ee1bdae6b4edbb4514929c2c9f9971149256cdfa6d10c07424bc48235` |

三个retained `original.ck3`分别为71081729、71082319、71082293 B，均低于计划上界。SHA依次为 `3f32d87173d72c9ed63789278f55e375958696b2656a6dc79c5978b244d8944c`、`cb0b2987c15562d2580dd712722f7127e5d347a3a8ae13f0e4bb102ec3250f3b`、`2464eb17f1da3f52f4563379eba298cefb9eba7e570d955056f8f9cec3b149ef`。它们位于 `EXT/observations/<R0019>/checkpoint-01..03/`，各自原melt/process/recipe及callback保持；本文引用既有小投影与process，不重复解档。真实readback原wait与源计划检查在 `EXT/environment/r19-manual-readback-a01/checkpoint-01..03-original-wait.json`、对应 `*-source-plan-check.json`。原wait三份均明确 `actual_original_popen_wait=true / returncode=0 / game_actions_sent=0`，不把Rakaly子进程退出单独当作全部生产链退出。

## 库存GUI的实际审阅边界

Root只打开一次库存；使用canonical坐标回执 `EXT/media/r19-inventory-open-a01.png.json`（1522 B、SHA `adb18879bee782b16879020a831596bdea8abb74ffe9432f70ace34c0bf69794`），并实际审阅延迟取得的原图 `20261023T041001173735Z-r19-inventory-actual-after-a01.png`。该图2423383 B、SHA `1cee93da667ef007511013071d355b6a86163c49ed2b1ddf16b28e1179ffd980`，Root记录库存可见、7件物品、两件星名活器、武器槽空、显示20金。审阅原件 `EXT/environment/r19-inventory-root-review-a01.json` 于04:11:00.026944Z生成；`equipment_submitted_by_root=false / business_pass=false`。随后实际装备由受管原生路径提交。历史接口在意图准入前拒绝的记录保留，不能把GUI回调成功追认为原接口从未拒绝，也不能由截图直接授五项业务信用。

## 04:36:59Z续记：第四份生产链完成，适配器投影待落

Save04 原readback PID9136 于04:36:09.313067Z实际wait0（04:36:01.264885Z开始），`actual_original_popen_wait=true / response_exists=true / game_actions_sent=0`，见 `EXT/environment/r19-manual-readback-a01/checkpoint-04-original-wait.json`。retained original为70298130 B、SHA `9b213b06a7e1e00ffec525ff709f1ac88bddcaa02da0f92659ad3b605dd2124f`；melt为103197902 B、SHA `8272e21500d0259ede94f44db468faa1cfeba9212d947b62d8e7a91fffc733a2`。独立Rakaly process亦为exit0/failure=null，但这是生产链内部阶段。

此截点 `curse-checkpoint-04.json` 尚未落盘，未把producer完成误写为适配器已消费，未推断该份钱包、压力、装备、自然日或月份守卫。后续仍由既有受管路径取得实际原生读回；报告不补查询、不重调用producer。

## 04:43:02Z续记：第四份已消费，首个月界保存已生产

`curse-checkpoint-04.json` 已落：19046 B、SHA `303c5933d2610c364e73a975c3528719874ec2b9875f3a1410339434e9e258cc`。对应1066.9.30、自然日15、月12801；血契未装备、贵族胃口已装备、候选未装备。保存与原生钱包仍为 `2000000`、压力15，原物品402保持L1/XP0/pending0/growth_sequence0。该份未安排健康查询，明确为UNAVAILABLE，不能借用前三份健康值。

Save05 原readback PID13308 于04:42:21.587859Z实际wait0，开始04:42:11.987130Z，原wait明确 `actual_original_popen_wait=true / game_actions_sent=0`。retained original为70515647 B、SHA `4e228b0697850c41adeca6a723429900ad93f0e429e644b8039863470473ff44`；melt为103891691 B、SHA `4bc993efa804a8c776bec08b5a29ba88d4ba611d47af5b6aa27e60d920828a7a`，process0/failure=null。此截点第五份适配器投影尚未落，不先写本月实际收费、压力或五项通过。

## 04:47:29Z续记：真实结果BLOCKED，五项未通过

原 `case-output/living-artifacts-curse-representative-result.json` 于 **04:45:53.520758Z** 生成，425444 B、SHA `964e733c6035ab26a075ac7ac6067eab0d3d04a28743ba2c7ee5b0db0215ee73`。实际字段为 `status=BLOCKED / actual_natural_days=16 / actual_public_calls_budgeted=110 / actual_saved_observations=5 / original_action_unknown=false`；case_contract、gui_contract、business、product_release均false。原result保持生成时的 `normal_close_pending=true`，后续正常闭场另补独立证据。

| 合同检查 | 原结果 |
| --- | --- |
| `CURSE-BLOOD-EQUIP-REMOVE` | BLOCKED |
| `CURSE-APPETITE-BOUNDED-PAYMENT` | BLOCKED |
| `CURSE-SAME-DATE-NO-RECHARGE` | BLOCKED |
| `CURSE-NEXT-DAY-NO-RECHARGE` | BLOCKED |
| `CURSE-CANDIDATE-PERSISTED-JUDGEMENT` | BLOCKED |

五项原reason均为 `ValueError: Nonunique/missing saved field: gold`，各 `observed={}`。第五份保存的磁盘生产已0，但 `curse-checkpoint-05.json` 未落；第六、七份未请求、未生产，不记七Save、17日完成或同日/次日不重扣。原 `curse-evidence-journal.json` 为37047 B、SHA `21ce4271f3eac6e581e2b0c87bb3f947066877e7b6b22a45694dc331d18e3795`。报告不读全文melt或猜测缺失字段代表的数值，不把这一读取阻断直接写成正式付款逻辑失败。

`normal-quit-awaiting.json` 已要求Root合法菜单退出，`host_error_preserved=null`；`manual-quit-awaiting.json` 保留原hold截止，`automation_failure_preserved=null / helper_replay_or_new_budget=false`。这两份请求证明进入正常退出等待，不证明GUI已退出、进程已归零或keeper已释放。Root独占实际退出与收尾，报告不代回退出请求，不发新游戏动作。

## 真实正常闭场与公共verify2

Root直接审阅05:15:52.081373Z退出确认原图中的空自动保存复选框，随后用canonical映射回执正常Quit to Desktop；没有重试游戏业务动作。Root quit回执于05:17:42.187195Z生成，1813 B、SHA `b2540f91bfa58201c44656e33d0d6aaf7994df66dea7b56a72f637c221931ab9`。原共享owner保留的OS handle实际signaled/exit0；原生进程于05:16:06.566429Z结束，process_exit_code0、tree_gone/cleanup_proven均true，最终进程清单为空。原host报告于05:17:45.508543Z结束，host_error=null。独立 `normal-close-result.json` 为8786 B、SHA `815b086d35abad051e2ee6816e874fbd29065a6cae368df443c83dbeecf4a798`，`normal_close_qualified=true`；原case result的 `normal_close_pending=true` 未被改写。

公共run原工具35505实际wait0，Popen13016于05:17:46.148649Z returncode0；原host14072实际wait1。keeper协作退出后，原allocate工具68408实际wait0，Popen6964于05:20:21.363616Z returncode0；keeper报告05:20:21.135741Z、last_sequence798、thread_exited=true/failure=null，独立资源释放仍由Root完成。随后CAS **799** 于05:21:58.381587Z完成done/resources=[]，原 `EXT/environment/r19-screen-resource-close-a01/release.stdout.json` 为1383 B、SHA `d9d1c2be66f9dc06cff2606a5456cc01296a608def186694d1d7b4ab6b8090a9`。后台Steam probe于05:21:59.116278Z确认offline/true。外层run0、keeper0和正常退出不授业务PASS。

当前主线公共入口显式读取原c20 runtime、产品表、Prepared和R19 context，调用原冻结消费者执行verify `20261023T053221748325Z-verify`。原工具68033及Popen12132实际退出 **2/BLOCKED**，结束05:32:37.706035Z；stdout441884 B、SHA `f09a78a7f20e80213aedfe7cec9d5f241d198b09c2d2ee73d19fb132079a3b54`，保留相同gold字段错误。case_contract/gui_contract/case_acceptance/qualified_boundary/business/release均false；正常闭场独立为true。没有重启游戏或补造第六、七份保存，06/07为NOT_EXECUTED。

## 后继维护边界

R18输入失败与R19读取BLOCKED分别保留。只读窄提取已区分第五份角色31254的gold整块缺失与重复：本例直接gold条目数为0，同暂停日期53144712的原生 `case-snapshot-0054.actual-results.json` 明确Q0。原字节角色片段9516 B、SHA `157449d69de163bf05c3acafe745bfaa8de83900488ab7a291911a2dd3dbc3c6`，来源绑定 `EXT/environment/r19-zero-wallet-consumer-a01/evidence.json`。这只是确切版本/来源的零钱包对照，不授普适“缺失等于零”规则或完整付款验收。共享reader修复与回归正在另包维护，本报告不先写修复通过，不热改本场c20、Prepared或原证据。

a30使用R17真正renewed04的离线Prepared已就绪但cold仍NOT_RUN，旧a27未消费。发布仍须代表诅咒场和cold实际闭合；不扩为63项全矩阵通过，也不因新读取故障省略原五项要求。

本文单文件更新预算≤1MiB，计现有a29 other512MiB；机器与父卡不变，不新hold、不改卡、不释放父预算。写前通用检查为 `EXT/environment/storage-r19-report-child-a01/task-start/20261023T043308981898Z-task-start.json` 与 `before-heavy-write/20261023T043310941203Z-before-heavy-write.json`，两原退出均0。此版已交Root作独立闭场文档提交，报告维护者暂停该文件写入；不将停止编辑追认为父存储预留已释放。
