# 宗族化密教：2026-10-26 休假交接

观察：2026-10-25T20:31:20Z／北京时间2026-10-26 04:31。`machine_id: desktop-3fevhd2-1c74096080`。用户要求收尾、写交接并停止继续实机。本文件接续D工作树保留的未跟踪 `docs/handover/2026-10-25-dynastic-esotericism-vacation-handover.md`，最新需求与本文件优先；旧未推送patch不可再次直接套用。

## 先看结论

- 当前产品源码已普通推送到 `master`：**`fe6049b287c6e55986857e1fc5f827961b027edb`**。休假交接提交随后增加文档，产品代码不变。正式候选仍是0.2.0，未上传。
- **用户最后取消了两个领袖头衔的政体转换／绑定。最终仅保留帝国级头衔、正常取得路径和对应教派图纹章。不要恢复贤能制／教会制回调或额外贤能制DLC门。** 原教义组合照用户要求保留。
- 最终a07完整默认Maven **38测试，0失败／错误／跳过**；开发35文件、正式九语56文件。21项资源源码＝classes＝打包JAR。新增GUI、图标和帝国领袖尚未实机。
- **九步持久生产链尚未运行**；`post-r18-heads-a01`不存在。测试中临时生成的包不等于已保存的正式staging。不要上传旧52文件包。
- 最近实际场次是 **R0018**，业务正式签署 **0/6**。Root漏传事件查询必填参数，SDK拒绝后共享客户端自动退出。Game原handle0、host原wait1、public run／verify2、keeper／allocator0；业务RED保留。没有R0019分配、启动或新Core预留。
- 20:31Z实际进程清单blockers=[]、SCREEN owners=[]。20:30:51Z后台Steam探针为offline／offline_mode=true；不能将这次回执用于以后启动。

## 最终需求，防止沿用已撤销方案

1. 真正创建／改革为宗族化时，创建者最终拥有族长身份；若操作前已经是Dynast，复用其原Dynasty与House，按新Rite改名，保留各自原纹章，不另造Dynasty／House／创始NPC。普通采用已有预置礼仪不据此接管旧宗族。
2. 旧宗族已绑定别的Rite时，转给新Rite；旧Rite实际改为None，解除旧绑定与仅本产品的背离意见／犯罪来源，不能被维护重新抢回。原版独立罪行保留。
3. AI不能在原版创建／改革选择器主动选择宗族化；AI信徒仍可采用玩家礼仪。任意自创Rite确实无法复制原宗教图时允许一次原生随机宗族纹章；两预设使用上传图。
4. 繁育教派、白绮教派各自为独立Faith＋同名main Rite，归基督教大类。完整三信条、25项指定普通教义、繁育8／白绮2特殊教义、用户图和九语保留。用户再次明确保留“神权制圣职传统＋世俗信仰领袖”组合，不再询问确认，也不擅自改教义以迎合原版选择器。
5. None不显示在礼仪详情，编辑器保留None／宗族化两项。旧金红宗族化图标被用户实际否决；新图应贴合原版轮廓风格，尚待实际小尺寸效果。
6. **两信仰领袖头衔固定帝国级、各用对应Faith图纹章，正常取得／恢复。政体沿原版机制；本产品不转换或持续校正持有者政体。** 用户先提繁育教会／白绮贤能、又提两者贤能，最终均已取消。研究目录 `GOVERNMENT-BINDING.md` 和a06只属撤销前方案／历史构建，不是下一步施工指令。

权威需求：[requirements.md](../../mod_dynastic_esotericism/docs/requirements.md)，测试：[test-plan.md](../../mod_dynastic_esotericism/docs/test-plan.md)，最新状态：[delivery-status.md](../../mod_dynastic_esotericism/docs/delivery-status.md)。

## 源码、工作树和必须保护的用户文件

| 用途 | 实际路径／身份 |
| --- | --- |
| 当前完整隔离源 | `C:/ck3-dynastic-esotericism-20261024/main12`，分支 `work/dynastic-heir-stock-input-20261025`；产品提交fe6049已普通推送 |
| 任务证据根，下面简称A20 | `C:/ck3-dynastic-esotericism-20261024/resume-product-a20` |
| 构建根 | `C:/ck3-dynastic-esotericism-20261024/resume-builder-a20` |
| 指定用户工作区 | `D:/workspace/ck3_eternal_recurrence`，本次读回HEAD仍为 `3c0b5ec8fb5d5ba12724dfdc1a26222b9b768e26`；没有替用户切换／快进 |
| 原Native生产来源 | `C:/w/des1025-prisoner-source-9c4-a02/evidence/final-native-index-a01/native-source-index.actual.json`；Main12 native subtree仍为 `81d5ef66421f073201a7527835ee2d38a88cbfda` |

D树原脏文件 `docs/handover/2026-10-22-war-episode04-vacation-handover.md` 未改：27,327 B，SHA `0c9be93c0e25eeefc5785187885f1eecd1244fbe342806aea314f5db31b402d2`。原3个未跟踪的10月25日handover／snapshot／unpushed patch也未改。新交接另存为本文件，不能把用户旧脏文件一并提交或还原。

本轮先commit293d6dc8，再按已审阅范围fetch `6d3d51bd81c328cfe3be6fd869136b3a4ba67b73`，线性rebase成fe6049，普通push0。没有merge／force。incoming4提交10文件包含共享native构建器和Java CI bootstrap，非纯文档；无DES、native C++／CMake、common host runtime／SDK／POM／workflow改动，未与本轮路径冲突。实际回执：A20 `ROOT-COMMIT-a04.actual.json`、`ROOT-FILTERED-FETCH-a04.actual.json`、`ROOT-REBASE-a04.actual.json`、`ROOT-PUSH-a04.actual.json`；scope在 `remote-compare-6d38-6d3d-a01/`。

## 本轮代码结果与边界

### 宗族复用与旧绑定转移

fe6049已包含此前6d38中的native actor／操作前Dynast／Dynasty／House快照、普通未知Rite延后首次绑定、两预置ready列表、复用与旧Rite真实None清理。只让曾采用该Rite的旧族成员成为后续背离者，避免从未入教的原族成员被误判。

R0017的真实NPC族长错误仍是失败基线，**新复用路径没有完成创建后的独立Save验收**。不能将代码存在、a07或R0018提交一次创建称为修好。详见产品 `docs/2026-10-26-native-dynast-reuse.md`。

### None详情与图标

原版 `window_faith.gui` 详情实例未读 `DoctrineType.IsVisible`，R0018实际截图仍显示None。当前同路径完整GUI仅一条逻辑条件加 `And( DoctrineType.IsVisible, 原Nor3条件 )`，原容器ignoreinvisible保留；编辑器不改。与其他覆盖该GUI的模组需要合并。详见[修订专题](../../mod_dynastic_esotericism/docs/2026-10-26-none-visibility-and-icon.md)。

金红圆树图已被否决。新图为三个人物／家谱树的原创透明轮廓，原图185KB，SHA `751318bc6f91b32a7e257ee457d3166f38a9d12d401caccfcad32908681ed827`。原版着色链保留alpha并提供颜色，因此两张运行DDS为RGB全0的120×120 BGRA8，各57,728 B，SHA `21444eed8611e441d70e77bfb94ac9219750b83a9b8574534ad07324a434be8a`。默认Java配方实际编译／导出0，与候选逐像素一致。没有为用户两Faith图重新生成图像。完整提示词、配方与来源在产品[artwork.md](../../mod_dynastic_esotericism/docs/artwork.md)。新图仍待Game显示，不能标为用户已认可。

### 两枚帝国领袖

`e_des_procreation_papacy`／`e_des_vivhite_papacy`，分别本地化为繁育教廷／白绮教廷。各Faith.faith_details.religious_head绑定对应头衔。已有用户图textured-emblem定义通过同名CoA数据库别名给两帝国使用，正常动态建立分支固定set_coa，其他Faith仍原随机图。

原版正常决议一般需有地、对应Faith且无在任领袖、世俗领袖教义、至少一处符合控制及同Faith伯爵要求的圣地、奉献等级3；基础250虔诚。帝国另加独立或直属领主高于帝国的合法层级条件。保留原版满足条件的自动建立／恢复；dynamic setup仅两Faith选对应静态帝国，避免0001把它覆盖回公国。没有另加免费领取决议。

最终生产文件为新增landed_titles、有限stock temporal trigger／effect覆盖、Faith绑定、CoA别名与九语；**没有新增政府on_action文件、change_government／行政转换helper或贤能制DLC门。** 原版教义本身的DLC资格不被放宽。其他模组覆写同两个stock trigger／effect键时有兼容面。

详见[帝国领袖专题](../../mod_dynastic_esotericism/docs/2026-10-26-empire-heads.md)。政体通用研究已富化到[共享知识](../ck3-government-and-faith-head-12004.md)：教宗国初始教会制为头衔历史明确配置，宗教映射作用于神权人物；帝国等级不是政体开关。该研究不等于本次实际领取验证。

## 构建与CI事实

- a05原退出1：38测试中1项旧ReleaseBuilderTest仍期待31文件；其余无error／skip。原失败保留。
- a06原退出0、38项通过，但有政体绑定，已被用户撤销；记录明确superseded，不可用它的runner生成最终包。
- **a07原退出0，64.4053483秒，38测试无失败／错误／跳过；21资源源码＝classes＝JAR。** 最终开发35／正式56文件。12生产Java、9测试源以release21和现有lint/Werror配置编译；默认mvn3.10.0、Java25.0.4.1。Maven实际home目录名仍含3.9.16，不把绝对安装路径写成执行规范。
- 当前runner：`C:/ck3-dynastic-esotericism-20261024/resume-builder-a20/attempt-a07/java-build/dynastic-esotericism-tools/quarkus-app/quarkus-run.jar`。
- 当前实际记录：产品 `docs/acceptance/rebuild38-a07-2026-10-26.json`（12,605 B，SHA `c80f0a8d6b1e5bab6abfd7d3ab09db2be4f68d35891e8e01f23fd07e4b37356b`）；原Maven回执及stdout／stderr在 `attempt-a07/`。
- **最终9步持久生产链全部NOT_RUN**：dev／release validate、build／verify，core13／sect5／initial3 fixture。外置 `A20/post-r18-heads-a01.NOT_RUN.actual.json`，3,949 B，SHA `0e08311bbcf98eb57dc271dbb3ea7f85a97979fb07573cc9a692a0f26e7095f5`。没有 `post-r18-heads-a01/`。
- 旧 `post-r17-head-fix-a01/` 为31／52文件、旧Java a04，不得冒认最终正式包；其持久9链实际0仍仅对应旧源。

exact6d38远端CI：DES40222604816、RRF40222604807、LYD40222604932、Linear40222604821 success；Official40222604786的step44因缺fixtureProductionRequest而exit1，full parity／HTTP／fresh SDK／cold-warm未执行；CLA未触发。证据在 `resume-builder-a20/ci-6d38-a01`及产品 `docs/acceptance/ci-6d38-2026-10-26.json`。

incoming6d3d改了CiBootstrap，不能把6d38的“与66e同字节”归因外推；上游自己的build-tools636仍记录9fail／1error。fe6049新CI未在本次休假收尾收集，不报告新head全绿，不为此重跑无关平台。

## R0018现场，不能跳过它接旧R0017

最近消费的实际ID：`desktop-3fevhd2-1c74096080--dynastic-esotericism--R0018`。live目录：`A20/runtime-a17/runs/<上述ID>`；state=`A20/attempt-core-a27/state`，operation=`operations-core-a38`，keeper=`keeper-core-a38`。

原Game PID31800、FILETIME字符串`134374283613646318`。真正native创建只提交一次，action request `rite-action-6c1e3ff16e2f411eacb3666c0fc43246`；pending后出现事件实例1。Root查询 `ck3_query_current_event_window_context_v1` 漏传 `event_instance_id`，仅带expected_revision11，SDK校验失败。不是产品错误，不得重放confirm或改原报告。

共享自动typed Quit完整结束，原handle Game0、host原进程1、public run／verify2、keeper／allocator0。`failure_lifecycle_completed=true`、cleanup_ok=true；**normal_close_qualified=false、business_pass=false**。合作STOP后CAS9023→9024释放。实际共享后继消费者返回 `previous-shared-managed-session`、inventory blockers=[]；下一allocate正常引用R0018、keeper-a38和R0018 release，不使用failed-host／bootstrap bundle，也不接R0017。

小闭场 `operations-core-a38/R0018-CLOSURE.actual.json`，4,294 B，SHA `607b346c662fdc455cd07c61c63ec031e3b73498807b54fd5922d8b9deb3cd1e`。所有原统一exec会话已消费终态，无原场控制权遗留。

只保留到两个创建前保存：

| retained-saves文件 | bytes | SHA-256 |
| --- | --- | --- |
| r18-baseline.ck3 | 68,751,831 | de83c0d4e0be7ed7864a0089053067e866e8b21f281965bd262989ae4886797c |
| r18-after-cancel.ck3 | 68,755,225 | fc7d890dc570cbb7ffa75b80a239347fc26e3ee164398ceb2e530f24890aba86 |

各有SDK pin与locked-copy custody。原SDK checkpoint路径已被第二次保存覆盖，不能把当前SDK路径当第一份原件。**没有创建后D0／+1／+2或cold anchor。** baseline独立a08／a10观察均原退出0：Dynasty12156、House12760、存活35544；原D174／H174族长均31254，真实继承人65825（不能沿R17旧ID65849）。D174自有CoA1781完整AST SHA `d166550b7e506c904a60205b1cb428876416c93a0821d3b46a3977b4d2cc692c`；H174没有自有CoA字段，必须保留缺失，不把继承显示误记为自身1781。

独立观察：live `operator-evidence/independent-baseline-observer-a10-a01/readback.actual.json`及核验卡。R18日志20条重复unused诊断对应10个审计字段，未观察unknown keyword／非法scope／解析拒绝，不等于error.log为空。

## 下一步顺序

1. 核当前机器、实际安装、干净源和统一存储策略；不要用旧准入或旧Steam回执启动。用户最终要求是无政体转换。
2. 复用／校验a07Java产物，实际跑9步持久生产链到全新输出，确认35／56清单、21资源、13／5／3 fixture和真实消费者。原行政脚本 `A20/invoke_post_r17_producers_a01.py` 可参考，但须改runner、Source HEAD、authority与新输出；不能原样执行旧源旧卡。
3. 按当前干净HEAD生成新canonical host／runtime／public plan／prepare。拟用runtime-a18、host-a18、prepared-core-a28、attempt-core-a28、operations-a39、keeper-a39、core-a28-administration，**当前全部不存在、未准入**。旧 `invoke_runtime_a17_prepare_a27.py` 只是旧参数参考，不能改被冻结a17图。
4. 准备真正新Core完整4.5GiB及新系统增长基线，前置fresh／source／正常R18闭场／SCREEN／后台offline全部通过后，再公共allocate实际下一编号；没有预先分配R0019。
5. 先查None详情隐藏、新轮廓图实际效果、编辑器两选项；再真实native创建，验证操作前Dynast复用174、名称及各自CoA、无额外Dynasty／House／NPC、最终族长。
6. 原操作卡 `A20/operator-reference/r19-operation-plan-a01/REPORT.md`（19,286 B，SHA `696fc9bb0b0fe982f8cd8f41f55a0e0ae06fc8d552fdc5764a18e5e5deb40b65`）有必要MCP参数与原六phase／25markers。其中预估产品55已过时，最终56。事件查询必须用实际snapshot的event_instance_id；UNKNOWN不重放。D0纯产品Native＋Save先于capture，随后同D0 capture；真实D1／D2各完整读回＋Save后才签phase1，再显式headcells，不让fixture生成对象污染“产品新建”结论。
7. 完成原完整core、同Faith／跨Faith背离、原版罪行保留、赦免／重新背离、出生、自然继承、cold／旧档和两预置矩阵。真实绑定冲突需单独准备Native前态，外置 `operator-reference/transfer-native-variant-a01/REPORT.md` 仅方案，不冒认已有case或PASS。
8. 增加两帝国正常建立／恢复／继承与固定纹章的实际验证。当前preset5文件六stock输入没有自动等于“控制圣地后正常决议领袖”验收，LIVE17／18仍NOT_RUN。保持user指定教义及原版可选限制；别恢复已取消的政府转换测试。
9. 0.2完整验收及正式生产通过后才更新同一Workshop物品并完成公开描述／Notes／真实缓存及加载闭环。必要联网后立即恢复offline。

## 存储、清理与闭场

统一ledger：`D:/workspace/.codex-task-bus/e04-capacity-reservations.json`。最近施工卡r1236/storage124：`A20/capacity/CONSTRUCTION-EXPECTED6D3D-ADMISSION-r1236.actual.json`，SHA `4d6b35ad7a7e4c72d717510363c189a2f9c05ddf08d860d483762a7f01284b55`。原helper `check_construction_a20_capacity_a01.py`，10,991 B，SHA `59684d4243c9d076d73cfd5691a3aaffe3ac27826589746d0fadba77752f616e`。C施工512MiB／D小元数据1MiB，原期限2026-10-26T15:30Z；Core=null。本次文档提交后会关闭闲置施工future，最终状态以外置 `A20/capacity/VACATION-20261026-CLOSURE.actual.json` 为准；**后继必须重新准入，不能沿旧卡继续写大文件或启动。**

完整Git32MiB按全部Main12.git保守扣，不按命令重置；产品push后完整allocation19,167,528 B，余14,386,904 B，交接提交会再小幅增长，后继重测。source／工作树身份与容量不能由D树旧HEAD或别机回执外推。禁PowerShell；新生产开发仍Java＋Maven＋Quarkus；只用默认mvn且>=3.10.0。

本轮按精确FileID／SHA、Root完整清单复核及独占handle删除了可重建的旧shader缓存：先r1231的1761文件215,580,672 B；后r1234→1235的22,155文件872,161,280 B，23批、0失败／未知。后者涉及已闭R14／15／18、R16／17尾部、R1／13的精确shader文件，**并未删除完整profile或任何Save／wire／日志／配置／runtime源码**。旧shader原bytes已不可读，不制造同名替代证据；重建有耗时。后者小回执 `A28-SHADER-ACTUAL-a01.json`（SHA `b10ce7a4eab182f82d177393c77261307c7b3b0614c7cfd2d117dac001b6641d`），完整gzip账本 `A28-SHADER-COMPLETE-LEDGER-a01.json.gz`（443,184 B，SHA `1846ad746c7d00bf7278a0583f6b0f030920a961b660ba235e19ecf38fffd481`）。这些已发生回收不能再计下一轮额度。

结束观察：`A20/vacation-20261026-process-and-source.actual.json`、`vacation-20261026-steam-offline.actual.json`。全部子线程已停止；只读研究成果保留，尤其不要误把已撤回的政府绑定研究当产品需求。大证据依统一存储策略与引用复核，不永久默认保留。

## 发布身份

已有Workshop物品 **3826991345** 的0.1.0公开测试基线不变；0.2.0未上传。只能更新该物品，不新建ID；remote_file_id仅canonical用户目录外层.mod，不能放源内descriptor或预存到上传staging。旧Notes HTTP429不代表成功全文回读；正式缓存下载／逐文件一致／CK3加载仍待验。普通开发保持Steam离线，必要上传才联网并在结束后立即恢复。当前后台offline观察只是收尾事实，不是下次launch准入。
