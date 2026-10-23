# 活武器：度假交接（2026-10-23）

用户于本轮明确要求温和收尾并交接。**开发与发布任务暂停，未发布 Steam Workshop，没有物品 ID；不要把本次交接当作产品验收完成。** 不再启动后继实机场次或上传。

本交接的执行机器为 `machine_id: pc-20260924rtuf-f11af23c08`，Windows 名称 `PC-20260924RTUF`。时间采用 UTC；本地为 Asia/Shanghai。以下安装、桌面、路径、Steam、容量和实机事实仅属于这台机器，换机器必须重新观察。

## 恢复执行补注（2026-10-23）

用户随后明确要求继续执行，撤销本交接开头的暂停状态。原度假闭场事实保留；后续恢复、c18 正常冻结和 R15 失败见 [恢复场次记录](../../mod_living_artifacts/docs/runtime-r15-resume-and-inventory-refusal.md)。新进度不把历史离线测试或失败场次追认为产品验收。

恢复后的 R16 已完成47自然日、7次保存、8项阈值检查及75金实际扣款，并在同进程补验安抚25金、正常GUI退出。旧公共验证字段遗漏、修复后重新验证与后继门槛见 [R16实际结果](../../mod_living_artifacts/docs/runtime-r16-gold-debit-and-normal-close.md)。下文度假截点原样保留，不能当作恢复后的当前执行状态。

截至2026-10-23T02:49Z，R17按c19/a28实际完成198自然日、852次计预算调用、7份保存，五项计时检查全PASS：首次扣25金、同日续期扣45金、旧90日事件保留新期限、第180日自然到期、第198日恢复成长为L2/XP0/成长序号1。两个原生中断均单次处理、独立核消失并完成既有来源离线复核。原结果1246547 B、SHA `66eef39ddb82121adcf86bc53bcf075078b1ad6cdbc6d19dca34d49f0c8cf5d0`；正常GUI退出、retained OS0/native0和cleanup均有独立实际证据，public run0、keeper0/CAS750释放。host1及库存预意图拒绝保留，不写全host GREEN。闭场Steam于02:24:15Z后台确认offline/true。见 [R17实际结果](../../mod_living_artifacts/docs/runtime-r17-paid-renewal-and-expiry.md)。

R17原公共verify `20261023T022452008067Z-verify` 于02:28:47.303428Z实际退出1：冻结c19在重算自然日证据时缺少 `xar_autoplayer` 导入。原失败保留；current-main既有 `case_imports` 已含完整隔离导入维护，c19缺少该更新，本次没有新增生产修复或临时PYTHONPATH。Root只切当前公共入口，显式保持原runtime/products/Prepared/context，新verify `20261023T023440382570Z-verify` 于02:38:59.402638Z原Popen及原工具80834均实际退出0，重算五项后case/GUI/normal close/qualified boundary均true；原结果Pin精确未变，不改冻结图或原件、不重启游戏，整体business/release仍false。a27已从真正renewed04完成离线prepare、绑定plan和preflight，cold实际仍NOT_RUN；余下按curse_representative→cold→发布推进，不扩63格或重跑已绿NPC/喂养。最终发布前description、单数Notes及永久changelog将明确代表实测和其余独有高风险生命周期未逐项验；Notes变化须保留旧674字草稿并重新冻结，不复用旧intent。下文度假历史NOT_RUN及旧预算保持原事实，不能当作恢复后的当前状态。

R17三域+28media最终2258970847 B、共享task-close0；仅R14 checkpoint01–03三份派生melt已按精确清单实际删除311663158逻辑字节，raw原件/官方melter/recipe保留，R17/R16未删，不臆定物理释放量。新正式卡 `EXT/environment/storage-curse-a25-20261023-a01` 的fresh检查及consumer compatibility均0，own D5GiB/C2GiB、other D512MiB/C0，截止2026-10-24T02:38:39.601285Z；旧a28 future own归0、旧卡保留。最终交接SHA `fdbdcb1c4742e393ad9befa9374afc96dc5cc304ee2e2217c2512bb5b7f4f30a`，精确来源见R17专题，不沿用下文旧预算作新准入。

**R0018已在夹具初始输入处BLOCKED并正常闭场。** 首份真实Save与同帧原生钱包均276金而非20金，引擎拒绝旧夹具的负数 `add_gold`；不是正式胃口付款结果。Root经既有严格回调写blocked/submitted=false，未提交库存GUI或装备动作。原结果五项BLOCKED、0日/8calls/1Save/UNKNOWNfalse，原public run0、host1、保存服务3（仅1/7），各自退出分别保留。正常GUI退出、retained OS0/native0/cleanup及keeper0成立，Root独立CAS766释放资源；03:15:40Z后台Steam仍offline/true。current-main公共verify op031702446912实际2/BLOCKED，未重写旧结果。见 [R18真实故障与闭场](../../mod_living_artifacts/docs/runtime-r18-invalid-curse-fixture-wallet.md)。下一步修共享夹具及首Save钱包前置守卫，完整回归后正常冻结新候选与新Prepared重测；不热改c19/a25，不把已闭场R18当作活跃场次。cold仍NOT_RUN，仍无物品ID或发布。

**04:18Z当前现场是R0019/c20/a29，勿重复allocate或开局。** 共享钱包修复e63243e87已通过224产品测试、完整53模块strict及完整cold四命令；c20 `518468a34fe537a866a9bd5cfd8e6f59724afff4` 仅c19加该四文件，normal freeze/build及a29 plan/prepare/preflight全实际0，正式57文件完全相同，archive标签已推。新预算 `storage-curse-a29-20261023-a01` 已消费fresh双trigger/真实consumer0，单own5GiB含offline512MiB，截止2026-10-24T03:35:29Z；六份旧派生melt实际回收及原件保留见R18专题。真实R19 allocate op035353517416原工具68408持续运行、keeper `living-curse-a29`/PID10948；03:55:00Z新鲜offline后，run op035503519066原工具35505运行，CK3 PID6576/birth1792727717.318296、host14072。两份保存producer均0，首Save与原生均20金，Root已单次GUI开库存，装备由原生adapter接手；尚无最终五项结果。剩余Save03–07由storage_resume逐个检查实际源≤192MiB后单次调用既有readback，Root不可重复调用；不启自动service、不写service0，GUI/事件/正常退出仍Root独占。a30改用同c20且仍引真正R17/04，prepare→bound plan→preflight全0，实际cold仍NOT_RUN；旧a27保持未消费。主线已推7c6da62ef，首发description、单数Notes及NOT_RELEASED changelog已明确代表实测与未逐项生命周期，旧674字packet保留，最终须重新冻结。

**05:33Z续记：R0019已BLOCKED并正常闭场，当前无游戏现场。** c20夹具钱包修复实际成立：首份保存/原生均20金；装备使健康由4.6616降至3.4616，卸下恢复4.6616。第16自然日原生钱包降至0、压力45，但Save05的玩家`alive_data`省略整个`gold`字段，共享读取器报`Nonunique/missing saved field: gold`。原结果425444 B、SHA `964e733c6035ab26a075ac7ac6067eab0d3d04a28743ba2c7ee5b0db0215ee73`，16日/110calls/5Save/五项BLOCKED/UNKNOWNfalse；06、07保存未执行，不能把局部读回升为五项通过。正常GUI退出、retained OS0/native0/cleanup独立成立，public原wait0、host原wait1、keeper原wait0；Root独立CAS799释放resources=[]，05:21:59Z后台Steam为offline/true。current-main公共verify `20261023T053221748325Z-verify` 于05:32:37.706035Z原Popen及原工具68033实际2，保持原BLOCKED和原件SHA。见 [R19真实读取故障](../../mod_living_artifacts/docs/runtime-r19-curse-representative-and-wallet-fix.md)。下一步在共享消费者窄修经精确版本、来源与同暂停原生零值佐证的字段省略，完整回归后正常冻结c21、新Prepared重测完整17日/7Save；不改c20或旧证据。a30 cold保持NOT_RUN，无Workshop ID、未发布。

主线exact `7c6da62ef75bb392a3093d44c85c77a171302057` 的Official run39895913075/job120226203972于05:24:40Z实际success，144步骤success、20条件skip、0fail；step111共享验收05:20:01Z及124policy05:24:14Z均success。Cold39895913002/job120226203481于03:41:32Z独立success。薄终态没有逐测试日志或Java artifact，不外推旧测试计数、SDK continuation或HOF原生wire资格。

**07:24Z续记：R0020/c21/a31已实际启动，勿重复allocate或开局。** 当前机器仍为 `pc-20260924rtuf-f11af23c08`。c21 `d32238154123bd0c9476577fcd6bf8f5762e2b7d` 已正常冻结，正式57文件与c20逐字节相同，无新C++构建；共享reader仅在精确版本、原存档来源与两个同暂停原生Q0证明成立时接受省略的gold，其他缺失/重复/错误类型仍拒绝。维护的公共SDK导入scope和verify JSON边界已同步，未夹入主线后续E02/host/native实现。最终226产品测试、完整53模块strict、cold四命令及公共入口必要回归均原退出0；整个旧公共模块strict仍有36条存量诊断（原50、新增0），不得称全模块类型通过。详见 [R20来源与执行记录](../../mod_living_artifacts/docs/runtime-r20-curse-and-zero-wallet-reader.md)。主线 `574e79e206c5d1863e60b62be91eef570be779f8` 及c21 archive标签已正常推送。

公共allocate `20261023T072019561525Z-allocate` 分配真实R0020，原工具37372仍持有keeper `living-curse-a31`/PID12428。07:23:02.392782Z后台offline/true后，bound preflight原0，public run `20261023T072305306085Z-run` 原工具18593运行中；host13724，CK3 PID13272/birth1792740199.351401，当前自动加载，业务未终态。Root独占GUI/MCP/退出；storage_resume仅服务本场实际pending的01–07只读producer，每份一次，Root不可重复调用。当前a31 own3GiB/C2GiB卡已实际采用，source复制前96MiB、melt产出后128MiB软上界及5份profile Save边界保持；c21全部offline实际401588616B，小于同own内512MiB。不得沿用旧a29的192MiB计划界限。a32同c21、真正R17/04的cold prepare→bound plan→preflight均0，但仍NOT_RUN，不能启动第二个游戏。尚无Workshop ID，仍NOT_RELEASED。

**08:08Z执行所有权更正：保存03–07现由Root唯一生产，不再委派storage_resume。** 保存观察代理遇执行容量异常，已于07:59:55.164286Z明确ACK：01/02原wait0，03尚未启动，所有producer进程归零、无待消费工具。Root随后单次完成03（原工具77422实际wait0，melt103766643B），没有重跑01/02；旧存储代理已停止所有保存生产。当前仍R0020/c21/a31，首保存与原生均20金，健康4.6616→装备后3.4616；卸下后第三份解析尚待最终投影，仍无五项终态。Root后续读回使用新鲜 `before-heavy-write-a03/20261023T080703043665Z-before-heavy-write.json`（5686B/SHA `e593c534cfc5e1d0517de881e39f58041df365201dfdb705558d2091a0c9e629`），同a31四卡未改。实际引擎显式Save还有last_save/autosave轮转副本，R20首/二/三profile Save数3/4/5；cold预算不能沿用“仅两份Save”推断，须按新实际链重算，a32仍NOT_RUN。

## 入口与必要约束

**10:31Z最新：c22离线验证/正常冻结工作已开始，当前无Game。** R21正常闭场和原context public verify0均已收口；Root精确审阅后30叶实际回收2359428214逻辑字节（R20七melt+23旧profile重复Save），原Save/recipe/失败与纯读分析保留，旧叶路径已不可读取。新a33卡 `EXT/environment/storage-curse-a33-20261023-a01` 已实际采用/fresh双0/真实consumer0，own D3GiB/C2GiB含offline512MiB、other单D128MiB；admission6884B/SHA `22395fd2d16c985c6e6df4943b2b4d6565da11cd8b41642db3d26badc6c441a2`，Root14Pin全核。a32未来own归0/旧卡不改，截止仍10/24T05:30:11Z。c22只用c21+a02审计补丁，保持c21 v1阈值合同，不夹main v2/host/SDK/E02；新组合完成全产品/53strict/cold四命令/3修改测试strict后才正常freeze/build57/a33公共plan→prepare→preflight。successor_readiness只做该offline512工作，禁止allocate/run；Root独占后继GUI/MCP/七保存/退出。R20原FAIL与normalclose=false不变，产品仍NOT_RELEASED、无ID。最新存储与原件可用性见[R21末节](../../mod_living_artifacts/docs/runtime-r21-renewed-save-cold-persistence.md)。

**10:08Z最新：R21冷启动六项PASS并正常闭场，当前无游戏。** 真实R17续期原Save已在c21新进程加载，0日/4calls/1Save；结果29765B/SHA `f1cb00b58bdef4d37c5a26e4c50b10ed55bda0e6be8b182980fa614bcffe5322`。Root10:05:31Z审阅自动保存未勾选并正常退出到桌面，retained OS0/native0/host0/public工具39003 wait0成立，keeper原allocate10555 wait0，Root CAS857释放；10:06:27Z后台仍offline/true。第一次无context verify原2保留，显式实际context后的op100705487069/原工具7991实际0。详见[R21完整记录](../../mod_living_artifacts/docs/runtime-r21-renewed-save-cold-persistence.md)。主线审计修复已正常fetch/rebase/push至af31cb8b95c63ade9477155059636fc19cb7d074，exact Cold/Linear CI success，Official仍运行。R20另作纯读七Save一致性复验actual0、五检查一致通过，原FAIL/normalclose=false不变；七melt全文读取已终止，后续回收须精确审阅并保护原Save/recipe/小投影。下一步正常c22候选重测诅咒，再完成首次发布；仍NOT_RELEASED、无ID。

**09:52Z当前状态：R20已FAIL并完成失败资源闭场；R21/c21/a32正在真实cold加载。** R20最终17日/160calls/7Save/五项FAIL，原552173B结果SHA `87be6d71ec24a983a8601998512383309864e6ad8279b26e94f27b3ea1994d8f`；唯一审计故障是库存预意图拒绝被最终消费者当作必须成功行。Root退出截图超龄而映射拒绝、无点击，原hold到期后native清理exit1；normal_close=false、retained OS0=false。原public工具18593 wait2、host1、allocate37372 wait0，失败reducer实际0只授行政接续；Root CAS848释放。current-main显式原c21 verify工具5071实际2，历史FAIL保留。共享4生产文件已修严格审计，完整232 tests/53模块strict/cold四命令通过；纯读R20一致性分析不替代新实机或正常闭场。

新cold卡 `EXT/environment/storage-cold-a32-20261023-a01` 已正式采用，own D1.5GiB/C2GiB、other D128MiB，旧a31未来own归0，截止2026-10-24T05:30:11.582444Z。按真实引擎保存链预留5份profile Save；source96MiB/melt软128MiB/硬256MiB守卫保持。仅获准R13两份派生melt精确删除208244814逻辑字节，原Save/recipe保留。09:51:32Z公共allocate分配真实R0021，keeper628/lease852；09:51:59Z新鲜后台offline/true、bound preflight0后run095201138990启动，CK3 PID13924/birth1792749135.039667、host2856。Root独占唯一保存producer、GUI与退出，勿重复allocate或开局；当前cold尚无终态。详见[R20最新完整记录](../../mod_living_artifacts/docs/runtime-r20-curse-and-zero-wallet-reader.md)。此卡不涵盖新c22或诅咒场，仍无Workshop ID、NOT_RELEASED。

- 仓库：`D:/workspace/ck3_eternal_recurrence`；产品：`mod_living_artifacts/`；外置工作包：`D:/workspace/ck3-living-artifacts-20261022`，下文简称 `EXT`。
- 实际解释器：`EXT/runtime/venv/Scripts/python.exe`，Python 3.13.17。**不用默认 Python 3.15，不得调用禁止的 Windows Shell，遵循 [AGENTS](../../AGENTS.md)。** Windows 命令使用 `cmd.exe`，带空格的游戏路径通过现有 Python argv helper 传递。
- 新开发遵守当前 AGENTS 的 Java/Maven/Quarkus 规则；本轮是一期迁移范围外的存量生成器维护及 CK3 脚本修复，不是新建 Python 生产模块的先例。
- CK3：`1.20.0.4 / build25734779 / Steam beta 1.20.0`；EXE `C:/SteamLibrary/steamapps/common/Crusader Kings III/binaries/ck3.exe`，101040248 B，SHA-256 `98702f88a547cde2eaf29a85f93b85f68ee4cf8148336a4f7afaeb75319dd518`。这是本轮加载绑定，不代替下次启动前的实际重验。
- Steam 模式只在后台确认。普通开发、实机保持离线；下次受管启动前重新运行 `tools/steam_offline_state_probe.py --receipt <新路径>`，只接受新鲜 `offline / offline_mode=true`，不能复用历史回执或抢焦点确认。
- 所有新实机从 `tools/ck3_mod_acceptance.py` 的公共 `plan / prepare / allocate / preflight / run / verify` 进入。不能直接运行历史 host/runner；不能热改冻结的 c16/c17/c18、shared-source、既有 Prepared 或原始证据。
- Root helper：`_runtime/living_public_next.py`、`living_start_prepared.py`、`living_live_status.py`、`living_service_checkpoints.py`。外层成功不代替原 child exit、业务结果及原生后态；`ok=false` 且无 finished_at 的正在执行步骤不是终态失败。
- 截图点击必须新原图、真实尺寸、明确内容矩形、`desktop_coordinate_map.py` 与 receipt。当前原桌面曾为 1920×1080，**不得作为下次默认值**。旧 HWND/PID 和旧坐标都不是下一场资格。绘制经常延迟，第一次截图仍为旧画面时应重新截图，不重复点击。
- MiniMax 七种外语翻译已完成；不要重新索要或输出密钥。此文不保存密钥。实际配置凭据保持在本机既有环境配置；发布前只检查存在性，按现有本地化流程执行格式检查。

## 用户需求与当前实现

玩家和 AI/NPC 都能获取、装备、培养；装备时自动成长，不设置手动升级许可；卸下免费停级并失去效果；付费压制只暂时生效。喂养按原版 common/masterwork/famed/illustrious 四档，无 CD。活武器名以 **★** 开头。首发实现按 **12 项能力、8 种诅咒、4 项组合、9 种语言**说明；不要把设计预留的 36/32/10 当成已交付。

设计、Elona 研究及验收方案都已在 [产品 docs](../../mod_living_artifacts/docs/)；发布说明为 [工坊正文](../../workshop/living_artifacts_description.bbcode)。实际截图已进仓库并做过匿名字节核对，见 [R8 图片回执](../../mod_living_artifacts/docs/evidence/r8-public-images.json)。它们尚未上传到本产品的 Steam 物品，因为物品尚未创建。

## 已有验收；不要重复整套矩阵

| 范围 | 实际结果与边界 |
| --- | --- |
| R8 核心成长/喂养 | 47 自然日、320 次调用、7 保存、4 检查 PASS；装备跨月自动成长、卸下停级、同日四档喂养成立。见 [报告](../../mod_living_artifacts/docs/runtime-r8-continuous-growth-and-feeding.md)。 |
| R12 NPC | 47 自然日、194 调用、4 保存、16 检查 PASS；有地持有者、男爵、无地廷臣实际装备、AI 喂养及培养。脆弱 NPC 仅候选绑定有信用。见 [报告](../../mod_living_artifacts/docs/runtime-r12-npc-continuous.md)。 |
| R13 喂养预览 | 原流程 BLOCKED 保留；原 PID 内维护续行 PASS。87 累计调用、5 保存、0 自然日；取消保留材料，80/200/500/1200 XP 连续喂养，最终 L6/XP572/成长序号5。5 张原图直接审阅；无 CD。见 [报告](../../mod_living_artifacts/docs/runtime-r13-feeding-preview-and-normal-close.md)。 |
| R14 阈值/压制 | **旧 c16 存在实际金币扣款错误，不能 PASS，也没有新版实机信用。** 自动 L10/992→L11/0、训练 +25 XP、威望与压力读回已成立。最终各分项和闭场在本文末尾补记。 |
| c18 修复候选 | 218 单元测试 PASS；完整 53 文件 strict PASS；生成 49 文件、check/static PASS；实际注册 203 工具 PASS。只有源码准备，freeze/build/后继实机未执行。 |

R13 已正常 GUI 退出，实际 OS/native exit0，CaseClient normal_close 合格；host 仍为 RED/exit1，原因是历史库存打开的预意图拒绝，外层 public exit0。keeper 原 wait0、CAS 序号574后 done/resources=[]，Steam 19:05:55Z 实际离线。原只读 scheduler 被精确终止，原工具退出15，**不记作 OS0**。完整细节在 R13 报告，不要改写历史结果。

## 当前关键故障与已提交修复

R14 `threshold-checkpoint-03.json`：L11/XP25、金币747、威望2350、压力25；首次压制后的 04：金币仍747、威望2300、压力33，期限389453、chain1、timer sequence1、hunger2 都已写入。SAVE 与同日原生钱包一致。引擎 error.log 明确拒绝负数 `add_gold`；这是脚本付款错误，不是倍率或报价 scope 未解析。

修复原提交 `1e4026b1e98af3a3b95a5a79d93fb29ee135f5ef`，已整合并推送为 `c0e9070021d758d31b1938e16eb8575e9403f457`。只改两个共享生成器的四处付款模板，以正值 `remove_short_term_gold` 覆盖 10 个实际扣款点；奖励、报价、破产惩罚、状态计时不变。已同步 25 个 catalog 来源 Pin。原 suite 的一次 catalog 未迁移失败保留，更新后完整 218 tests/312.577s/exit0，53 文件 strict/exit0。详见 [故障与修复](../../mod_living_artifacts/docs/runtime-r14-gold-debit.md)和其中完整小日志快照。

**仍须重新加载验证：** threshold 首次扣75；timer 首次25/续期45；贵族胃口实际扣款和破产代价；安抚一次正扣款。不要改低验收预期，也不要因离线测试通过就发布。安抚可在新 threshold 已完成后、同一受管进程尚待正常退出时，另作一项原生前后钱包核对；不能冒充原七保存用例或增加第八个同合同保存。

## 冻结源、Prepared 与接手顺序

- c16：`a7bc6ebe66cd04a06b15e6a67d251836a94a6e67`，R13/R14 使用，旧扣款错误存在。
- c17：`a79d38ca4735679d629734c157983e9687049c3d`；runtime `EXT/runtime/runtime.a79d38ca4.json`、57 文件 staging `EXT/builds/candidate-a79d38ca4`。a21 timer 与 a22 curse 的 plan→prepare→preflight 实际六步全0，来源分别151/162项，**但仍含旧游戏脚本，不应用来验证扣费修复**。
- c18：`5b1408fb3cc7b359eb5a43342861e8a521ab9d28`，parent 精确为 c17，仅加上述 Gold 修复。目录 `EXT/runtime/c18` 干净；source/applicability、生成 check49、静态与实际203注册完成。`EXT/environment/mcp-registration-c18-a01.json` 已存在。
- c18 source 已用 `archive/living-artifacts-c18-source-20261023` 归档；其他必需历史标签包括 `archive/living-artifacts-c17-20261023`、`archive/living-artifacts-cold-v2-source-20261023`。
- **NOT_RUN：** c18 freeze、57 文件 build、a23 threshold/a24 timer/a25 curse 的 config/Prepared。`runtime.5b1408fb3.json` 和 `candidate-5b1408fb3` 没有生成，不要猜路径存在。实际收口回执：`EXT/environment/c18-readiness-a01/vacation-handover.json`，SHA-256 `85cd08009611b4c2aea39d4d0396790b460705131f8df638eebe43d5a4506db1`。

恢复任务后先读当前 AGENTS、核机器与存储，再用现有 freezer 正常后继入口：

```bat
D:/workspace/ck3-living-artifacts-20261022/runtime/venv/Scripts/python.exe -B -X utf8 D:/workspace/ck3-living-artifacts-20261022/environment/freeze_common_runtime.py D:/workspace/ck3-living-artifacts-20261022/runtime/c18 5b1408fb3cc7b359eb5a43342861e8a521ab9d28 --normal-successor --registration-evidence D:/workspace/ck3-living-artifacts-20261022/environment/mcp-registration-c18-a01.json --host-change-evidence D:/workspace/ck3-living-artifacts-20261022/environment/cold-profile-inventory-v2-source-ready-a01/result.json
```

先消费实际 exit0，再使用已维护的 `_runtime/living_prepare_c13.py c18` 构建并创建 a23 threshold 新配置；其后逐项公共 plan→prepare→preflight。a24/a25 仍需按新候选创建新配置，不覆盖旧树，不提前写 `previous_*`。已证明 host/native 可复用，**不重编 C++，不把最新 master 的其他 host/native 改动随意夹进候选**。下次 allocate 才获取真实新 run ID，前场身份取本文最终实际闭场记录；fresh offline→run-context→bound preflight→public run 顺序不可颠倒。

剩余代表实机顺序：新 threshold 修复复验 → suppression_timer → curse_representative → cold_persistence。timer 为7保存、最多212自然日；cold 使用其真正 renewed checkpoint04，带 top-level saved_campaign 及8项闭合来源。历史 R8 的离线 cold prepare profile 已 consumed，不能拿它启动实际游戏。不要为四档喂养再扩四场 cold，也不要求穷举63格或重复已完成 NPC/喂养。

## 存储与只读保存服务

统一策略仍为 [通用存储策略](../storage-retention-policy.md)及 [参数](../storage-retention-policy.json)。旧中央三文件已过本轮续用期限，不覆盖、不用于未来保存；新卡为 `EXT/environment/storage-review-v2/` 的 profile、ledger、reservation、admission.json。

19:14Z 的人工预算基于766358项获准根 metadata：实测逻辑占用33167060012 B，另保守加完整 Java 并发峰值5621737288 B；D 默认 quota50010521600 B。own 剩余总上界 **D 6 GiB / C 2 GiB**，另留其他任务 D 2 GiB、系统增长 D 8 GiB/C32 GiB及策略 safety；不是每个新场各6GiB。复核截止 **2026-10-23T19:14:12.883278Z**，不是自动续期。截止前也须计入已经消耗的新增输出；换机器重新清点。

一次 R14 保存的实际 original约70.6MB、melted约104MB；不要为接手全文复制或重复解析全部保存。政策允许评估可重建派生副本，但当前关键 Save、未解决失败和原身份材料仍需按用途保留，不能整树删除。本轮没有删除资产。

既有服务已支持显式新目录，调用格式为：

```text
<PY> -B -X utf8 _runtime/living_service_checkpoints.py <真实LIVE> <新鲜before-heavy-write.json> 7 case-output --storage-dir <本机有效STORAGE_DIR>
```

它只调实际只读 Save producer，不发游戏动作。实际终态路径已修成 `case-output/entry-run-result.json`，不再等不存在的顶层 finished_at；未完成全部保存时返回非零，不授业务 PASS。22项参数/真实原件回归、完整两个文件 strict已通过，见 `EXT/environment/storage-review-v2/harness-terminal-validation.result.json`。R14 已运行进程是在这个终态修复前启动，但达到7保存后会自行退出；最终实际退出见闭场段。

## CI 与 Git 接手边界

Cold workflow 的长路径、临时路径 canonicalization、缺 MCP、缺 mypy 已分别用真实 hosted RED 定位并修复。已推送提交 `39f65e751`、`f56e39f78`、`882925352`；单独 cherry-pick 后者不自动包含前者。真实 GREEN run **39844397768**：214 产品 tests/58.645s、完整6模块 strict、saved profile v2 8 tests、SDK vanilla profile 8 tests；这些是离线/类型资格，不是 cold 实机或发布通过。回执 `EXT/environment/java-ci-qualified-child-a01/cold-source-39844397768.qualification.json`，SHA `f483ffed042413b5bf431c80b35fcac18257df737e2e05c1793380de562a08d5`。

Java Official 的实际历史 RED 为 scratch 枚举中 AccessDenied，尚未进入 full reactor/HTTP。共享 guard 已窄修并推送 **f58a776e93656b19b164e2ce96249aca69d17c62**：最多4次/25ms，仍消费原期限/中断；持续拒绝、其他IO及链接仍失败，不吞权限错误。38项目标 tests（22 Bootstrap/9 ControlBuild/7 SourceLimit）及16 main+13 test完整 release21/-Xlint:all/-Werror 编译通过；本机实际编译器 GraalVM25，不外推 JDK21 runtime。度假交接时 **Official CI39847545078 / job120064700121 尚在运行**，不声明全绿，接手者只读实际终态再判断。子任务无本地 Maven/watch 进程。回执 `EXT/environment/java-ci-qualified-child-a01/guard-repair-final-handoff-a01.json`，SHA `3430f55f0c9a29d28d9fcfddca0d6a5dfaf3efd1fc879a501c1db35f371f8a82`。

此前通过的45 Feast tests、其他旧 reactor失败及官方作业未执行阶段都保留；不要重跑全部458项来替代定点修复。主仓与隔离整合树的提交 ID 可能不同，上述原提交/远端等价提交都保留；以实际 fetch/log 和 archive tag识别，不 force push。

## 发布与截图尚未完成的部分

现成操作包为 `EXT/release/living-artifacts-0.1.0-create-a01/`：`RUNBOOK.md`、`STEAM_MODE_AND_NOTES_CARD.md`、`CACHE_ONLY_CARD.md`。这是准备材料，没有实际 Create/Submit。

1. 修复后代表实机完成并审阅实际日志，正式 tag 与干净 source一致；只用 builder生成 staging，不把开发 fixture/overlay/测试输入上传。当前公开版号拟0.1.0，首次发布为 initial baseline。
2. 工坊正文与 Change Notes 是独立交付。现冻结 Notes674字符/19行，归一化 SHA `381e2bf2aedad8236b6591396868748dbc3c4945d7714a405151d78c0b4fb2a3`；若内容变化重新冻结。EResult1不证明公开，必须匿名回读真实entry全文、字符/行数/SHA。
3. 仅上传/下载目的临时上线，实际完成或终止立即恢复离线。模式切换用当时官方 Steam 菜单/UIA；后台 probe负责后态。WAL begin/restore 是 stub，不能当实机开关。账号在线占用约束适用于在线启动游戏；本任务缓存游戏在离线确认后启动。
4. 首次 Create 的 target_item_id=null；只取真实返回 ID，不猜 ID，不因未知结果重发 Create。真实 ID分别登记主仓两份产品清单；canonical remote_file_id只留用户目录外层.mod。上传后重建无内层ID staging。
5. 已有两张真实 R8 PNG和全画幅JPEG候选；GitHub公开图已验证，Steam追加预览仍未执行。不要拿AI图替代实机证据。R13五张预览、R14 L11管理原图仍在 `EXT/media/`，按需明确来源使用。
6. 缓存验收只要求真实 Steam 下载文件与正式构建逐项相同及 CK3实际加载，不做业务复验、不挂fixture、不新开局。现成公共 `--case workshop_cache` 可用。c17/c18原冻结清单的ID为null，不热改；操作卡给出登记真实ID后 registered正常后继复用方案，无新C++build。字段层支持外部清单不等于本次已经授予它launch资格。
7. 上传、真实缓存加载、正常退出/离线，以及永久 `docs/release-changelogs/living-artifacts/0.1.0.md` 提交推送与正式 tag缺一不可。没有这些就继续标 NOT_RELEASED。

## 本次最终闭场

最终观察时间：`2026-10-22T20:37:54Z`；machine_id 与本文开头一致。

- R14 实际完成 **47自然日、257计预算调用、7真实保存；8项检查中7 PASS、1 FAIL**，总体 FAIL。唯一失败为 `SUPPRESS-ACTUAL-WALLET-90-DAY`；没有把压制期限或其他通过项当成金币扣款通过。结果于 `20:31:15.689680Z` 写入原 `case-output/living-artifacts-threshold-result.json`；最后为1066.11.1、L11/XP25、装备中且压制期限保留。公共 verify 阶段未另行启动。
- 第7保存 producer 于 `20:17:20.626659Z` 实际 wait0；只读服务原 session48633 实际 exit0（chunk `a75b37`），7个保存全部完成、未提交游戏动作。
- Root 直接查看原始退出确认框，确认自动保存未勾选，于20:36:59Z选择正常“退出到桌面”。`normal-quit-root-result.json` SHA `584b7ddb69f31cd8097405ce456d3fccba3e91eb70073b785ccf18b643bf8725`；`normal-close-result.json` 实际持有句柄 signaled/OS exit0、native process exit0、cleanup_proven/tree_gone、`normal_close_qualified=true`。没有强杀游戏。
- 原 host 实际 exit1，native-report 总体 RED，业务总体 FAIL；这些原终态保留。原 public run `EXT/environment/public-operations/20261022T191449579164Z-run/exit.json` 于 `20:37:17.806034Z` 记录实际 wait0，原工具99658也实际 exit0（chunk `988bc9`）。外层0不是业务PASS。
- Keeper STOP于 `20:37:35.687593Z`；原 allocate `20261022T190609368723Z-allocate` 的工具37807实际 wait0（chunk `1c4996`），keeper thread exited/failure=null/last_sequence611。CAS释放在 `EXT/environment/r14-screen-resource-close-a01/`，实际序号 **612、done、resources=[]**。
- Steam新鲜后台回执 `EXT/environment/steam-offline-r14-vacation-close-a01.json` 于 `20:37:54.707025Z` 确认 offline/true。Steam PID8580、出生FILETIME `134371126587222837`、版本11.15.70.27与原来源绑定；该事实只属于此次观察，不代替下次启动准入。
- 本机 CK3 枚举为空；所有本任务子代理已完成，本地无遗留保存服务、Maven或CI watch进程。既有共享服务和 Steam 客户端没有因本任务被关闭；远端 GitHub CI可自行完成，本文不等待或冒充其后续终态。
- 存储闭场实际 exit0、0删除：`EXT/environment/storage-r14-vacation-close-a01/20261022T203754547733Z-task-close.json`。人工未来写入预留收回为0，见 `EXT/environment/storage-review-v2/vacation-reservation-close.json`；旧 profile/ledger/reservation/producer-spec 均保留原字节。**旧6GiB/2GiB卡现在仅作历史证据，恢复任务须重新核预算并登记，不因原 review_at尚未到期而直接继续写入。**

当前原始证据与后继源码已保全；没有启动R14之后的游戏场次、发布或下载。本轮执行到此停止，接手优先从 c18 后继冻结与首次扣费复验继续。
