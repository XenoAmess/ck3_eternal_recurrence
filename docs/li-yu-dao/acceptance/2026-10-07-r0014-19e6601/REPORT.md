# R0014 已闭合、B4/B5 业务 RED 验收归档草稿

独立外置 successor 草稿，截止原B4/B5 RED、原game/client/keeper句柄exit0、CAS3429释放及实际只读闭合核验；原第一轮草稿保持。实际执行源为 `19e660105e05395caa6cc95e76c299312ee89d51`；本草稿尚未入库，本稿已纳入第二轮及第三轮 B1/B2/B3；B4 已实际提交但约束未通过；实际ACK/B5和游戏exit0已纳入；Client/keeper/CAS终局回执已在本稿末节纳入；旧pending稿保持原样。业务、最终日志覆盖、修复后新HEAD与新cold验收、正式入库及发布未获得信用的事项继续明确留空。

礼与道整体仍为 **NOT_GREEN**，约 70% 为工作量估计。尚未发布 Workshop；I3b 已有第三轮 B3 保存签署与 ready 观察，B4 正式提交和新 title18373 创建已观察，但完整 B4 约束不通过、B5实际终局仍RED，whole mandate尚无信用。历史 R0013 的 G2/G3 `*_mailbox_submit_unavailable` RED、R14 B1 两次严格读取 RED 及原错误字段摘要均保留。

## 精确源码与构建

master `19e660105e05395caa6cc95e76c299312ee89d51` clean 的冻结导出为 `C:/lr14s1`，native 3563 文件，构建前后源码相同。生产产品仍是原 70 文件 staging，ZIP 和产品树未改变。具体导出、manifest、ZIP 的路径、字节数及 SHA 取自[原始导出 REPORT](raw/2460c05683f5f74d06c0554c230ef7a31abad093bb016c525a4f974b20be3e83.json)。

build004 为当前冻结源码的独立冷构建，未复用旧对象或 DLL。[原始 RESULT](raw/a8d51253ccf4cf79687f1d4b3fdc93c9c21837278b04f27cdffe376680885e85.json)记录编译和四项 focused tests 成功，六个目标产物及新 runtime.lib 均有实际 SHA。DLL SHA-256 为 `4e10f698fc133ddb4c047d8a90b1d2633f4494db5eafdfe5a1d3d61c48423849`；新 runtime.lib 为 `2051f6227c42541404361d3ae868053ffc5644ae2fe20a97780d864a671d9041`。Ninja 队列分母为 426，[原 stdout](raw/1684d2b1aa3c1acf13c2a7c4f183b0fef45ec05994f4c8f2445c1a90839b21a0.stdout)可见 425 条 `/426` 编号，最后为 DLL 链接，避免把显示条数改写成另一个数字。

| 实际 focused 程序 | 实际退出码 | stdout 的检查数 |
| --- | --- | --- |
| assembly predicates | 0 | 70 |
| religious title readback | 0 | 无输出；不推断检查数 |
| challenger graph | 0 | 1342 |
| mailbox registration | 0 | 37，包含 production registration contract |

11 个正式 flag ON，player control OFF，BUILD_TESTING ON；精确 flag、程序、argv 和 stdout/stderr 引用保存在 REPORT.json。fixture 输出中的 `live=false` 保持原意，不能把这四个程序授予实机信用。

Defender 登记仍 **settings_failed**，原 outer exit code 1。[管理员实际失败读回](raw/91d82194268d00cfe668c191237507a20dd3b5dfc7c444d8501d0df1e81cb823.json)为 WMI Add 内层 `-2147217407`，5 个精确 EXE 没有成功读回。[本机只读 broker 检查](raw/6412daf665b0aeb262d7cee553c0dfe9f9811ec66b7410412d0f2e027d449762.json)确认当前受保护安装目录和固定任务缺失，历史别机安装文档不能代替本机事实。故编译与测试成功不等于环境登记整体 GREEN。

## 实际 MCP 与第一组 G2/G3/G4

原 SDK 元数据为 24 项显式 challenger 工具，默认 21 和显式 readonly 23 的兼容入口保留，player control 关闭。[元数据原件](raw/35c46e596428950c38c17d92f9c7263be60737ea5e7178120a80aa342141ea93.json)和[24 项原件](raw/d08c6d24be13b32b0cd3bbef30c2f31141a4222caf67bd57836444ed33085fd9.json)有独立 SHA。

Client session `c78874edd4204810a50ce436e2296753` 与 native bridge session `065244bdf4ce4b3fbfbf667eb8a9c757` 是两个不同身份。实际 attach 使用 build004 DLL 并得到 paused actor 31254、date_raw 53144712、public revision 2 / native revision 1；[原始 attach SDK](raw/d21f77e81a4be5a4b6c04334ab9c56985cba9e7abbb46e5d24ac2c931f3740eb.json)与初始原句柄回执均已封存。

实际 seq5 G2 accepted/observed、predicates_complete=true，完整 51 成员及 1 个 Rite，capture epoch 5791；seq6 G3 accepted/observed、legal_head_title_absent=true，epoch 6627；seq7 G4 accepted/observed、graph_complete=true，epoch 31513，对 Faith107/104/106 的完整 challenger 集合分别为 0。三次 SDK isError=false，日期不变，证明修复后的三个 mailbox route 已实机提交成功。原件分别为 [G2](raw/24e6e1b68f0c4b734afb19bb596fdc7bcf2527879826c548fc86d8819624ae16.json)、[G3](raw/f8a2608287fd715d3a7349730a8656bc1f8062db84133e36c091e9b078477cbb.json)、[G4](raw/a2b12b000f7622cbddd9954c016e95a3aa471701bc16facce9406244418dc94d.json)。

G3 的 headless 意味着当前没有 head title，title holder/properties/laws 的叶值仍为空；G4 此次验收覆盖空集合，非空 challenger/sponsor 记录仍缺本轮实机覆盖。G2/G3 没有原生 HoR Getter；不得从存档 HoR、headless 或 G4 空集合推断 native HoR。原字段资格中的 `runtime_acceptance=null` 原样保留，实机 route 信用单独由本节 SDK 回执支持。

## 第一轮业务窗口

正式 begin seq16 的后续实际 observation `postcondition_verified=true`：[原 SDK](raw/11fc0b867228ee89ef82357e94c27852fe09b8cd027d308c3ea1f296f463f1b3.json)。此前只读 query 的 `row_widget_datacontext_verified=false/action_qualified=false` 为该模型固定输出；confirm 使用独立正式 receiver 与后置观察，具体证据见[只读诊断](raw/74d21984afa641e3cfe3fc05a3e078ef9debe7ad76143763978612d8358fe90a.json)。

| 窗口 | 轮次 | 实际保存与 native 对照 | 保护 |
| --- | --- | --- | --- |
| B0 提案前基线 | 无活动提案 | typed baseline / native joined；正式 round reader 未执行 | 87/87 |
| B1 正式 begin 后 | S1/N1/P1 | 403/403；51 成员、2 elector、全部未投票 | 87/87 |
| B2 代表选定 | S1/N1/P1 | 404/404；Rite169 delegate31254 | 87/87 |
| B2a 封存后自然投票 | S1/N2/P2 | 353/353；人类31254 YES，NPC65865 NO | 87/87 |
| 正式 cancel 后 | S1/N2，phase 清除 | 393/393 owner/serial 清理 | 87/87 |

Rite169 的 counties=0、members=51，因此为活动学派；total=2、yes=1、`3*yes-2*total=-1`，signed=0，signature_requested 缺失，readiness=false 符合源码。NPC 的 NO 是合法业务结果，不能称为读取器错误或强制改票。原 B1 摘要错误选用 raw Rite rows 的派生空字段保留；[独立 corrective supplement](raw/3a69a4cb2e6df65cafb62b5c7719ec7e819bb16f2510c65f45eb2fcae67ea97a.json)以 state.schools[] 给出实际计数。

正式取消通过官方 decision 路径：[SDK 原件](raw/3be500995d35f96131d64fd4181371ed87400b896541b7e1cecd3e25b9e196ef.json)；[取消终局 INDEX](raw/9190005d8df9ec5df50cebd433b26ec8e2d4757c129dd4b361837011bc72946d.json)记录 393 清理和 87 保护全部匹配，以及已实际执行的 10 项 focused/negative tests。本草稿没有重复测试或读取存档 body。gold1043/piety3150/prestige2200 保持，钱包差额为 0。取消保留 actor S/N 与本轮历史，清除活动阶段、captured lists 和本轮 owner/serial 绑定的成员/Rite 字段；政治头衔、Doctrine、office 及其他 owner/serial 保护不变。

静态重议规则在[源码只读包](raw/0dab5919248114b52d476b8f80a6b484d4bebc3f7a7d796592a20cbcbc3e5bec.json)：未见显式 cooldown、重复提案次数或 begin/cancel 费用；新 begin 仍需满足正式入口和锁条件，S/N 各递增，seal 再递增 N。旧事件依赖原 S/N/P，不得复用为新轮投票；新 NPC 票为自然新轮响应，不能保证从 NO 变 YES。该静态包 future execution=null，实际后续须独立追加。

## 读取器修复与资格边界

本轮使用独立 external003 reader `6fadb96d25093746632dbaf450d810a203a5213d06730c17e95eea5fd68757cb` 与 author `8efcb4b1b048ea2b4819fecd48be8a9e934babc2dbe73461f91e622e8b66ca05`。只改 number() 的实际数字叶编码，兼容 present numeric 省略 zero 的 value 以及 UINT64 编码的 signed -1，仍拒绝缺失、unknown 和错误引用种类；[14 项实际 focused 回执](raw/8f387d0b9d830dd2b5946914c639a44cd2cac9a3cf847ed4494ff36034abc26d.json)及原 stderr 保存。

[afterclose review manifest](raw/e72b541b4c04f89df532a9f4e489dd12fb6259e7b11e1809fb751fc47693c45b.json)是 6 目标最小补丁，包含 reader、2 tests、2 fixtures、说明。原 14 项信用复用，既有 20 项在隔离 mirror 对精确候选实际通过；未应用到 main，必须在实际游戏与 helpers 闭合、screen CAS release 后处理。源码资格仍区分 semantic protocol HEAD632 与 actual execution HEAD19。

冻结 reader 的 `native_reference_qualification=UNKNOWN`、`CALLER_SUPPLIED_NOT_NATIVE_AUTHENTICATED`、`INCOMPLETE_NATIVE_QUALIFICATION` 继续保留。阶段匹配数与实际 G2/G3 回执分别记录，不能将原 legacy assessment 改成 GREEN 或自动授予正式 mandate。

## 第二轮与第三轮实际追加

第二轮使用 S2/N3/P1 正式 begin 及选代表，B1 403/403+87/87，B2 404/404+87/87；封存后 S2/N4/P2，B2a 353/353+87/87+8 源锚匹配，人类 YES、NPC65865 再次自然 NO，yes1/total2/Q=-1/signed0。[第二轮 B2a 原件](raw/60614b9a802c784f316c102068c60bc02b0f9172caf93384c46ed3f06c6e8591.json)与[第二轮 cancel INDEX](raw/e3c81d15a7de79e22f21854f0be97dcf3d784b46e7500344ca6c165f681463f1.json)单独保全。正式取消 393/393+87/87，S2/N4 保留、phase 清除，wallet 三项差 0；实际 public27/native26，G2/G3 epochs630671/630891。两次 NO 均是合法投票观察，不改写为 RED 读取器或强制改票。

第三轮 B1/B2 是 S3/N5/P1，51 成员、2 electors、1 human，B1 无 delegate 后 B2 delegate31254。B1 403/403+87/87、B2 404/404+87/87、各 13 源锚；[B1/B2 continuity 原件](raw/3347438bb02a614afeb08974b8fe5af77f30fbcbfe814801018edef9f3455ec6.json)12/12 实际一致。B1 frame public30/native29、epochs689213/689441；B2 public33/native32、epochs700545/700767。

第三轮自然进入 lyd.413 签署窗，seq121 原生 query root31254、seq122 正式 option1，seq123 saved public39/native38/native:38，同 date_raw53144712。seq117 的 lyd.412、seq119 的 lyd.411 UI root 也均为人类31254，不能仅按 event key 将其视为人工操纵 NPC。保存与事件 SDK 原件独立留存；此后[第三轮 B3 INDEX](raw/eb59a494b9ce429cad25f870006642e6057db29f201ce128a822ce11e9a6a9af.json)和[summary](raw/61bd3c006cc77707e1e84148158c3504d693fe7b6e0983b984aca83a044293ef.json)实际读回 S3/N6/P2，人类 vote1/player_yes1，NPC65865 vote1/player_yes0，Rite169 yes2/total2/Q2/delegate31254/signed1/signature_requested1。357/357 reader、87/87 保护、20/20 source/B2 continuity 匹配，signed-precommit saved readiness=true；G2 complete/G3 headless 实际 epochs772591/772817。

B3 ready 为保存与来源锚点的实际观察。冻结 reader 仍有 legacy reference UNKNOWN 与独立 formal event context UNKNOWN，whole formal/product/native HoR 信用为空，不写成正式立统或完整 GREEN。约 90 MB 的各份原存档留在原外置目录，本报告只复用既有 INDEX 的固定 path/size/SHA，不再复制或读取存档 body。

## 预览错误及 afterclose 候选

[诊断原件](raw/8252d3eac30b5f271901735e32740607203dfff804e834786614f5a912004f7d.json)证实 preview 路径读取未定义 serial/nonce/phase 的 source 缺口；原 snapshot37862448 B、431410 行、SHA `7c578191d35383e9f685c66866789dde6df4a8198d4e57c02f1ba77bfb88584d` 继续外置保留，只引用 hash。100000 条 E headers 中 99422 条与 I3b 相关、66282 条有显式 tooltip/description 标签、9 个签名。未标标签的 wrongtype 不能全归为 preview，也不能仅由 100000 推断 engine cap；该固定字节窗口不能证明之后无错误。

[afterclose manifest](raw/252ae26f37ebcc34ed7e46bce5c085c3fb51b8a9aea8a6fb7e31f451ed4381a8.json)为 2 MODIFY+3 ADD：generator 与生成的 setup effect 加 presence guards、实际 fixture、focused test 与说明；11 个生成目标中只有 setup effect 变化，业务 AST 保持。新 6 offline tests 实际通过且无 skips，首次 dependency failure 原件保留。候选尚未应用到本轮 HEAD19，原生 renderer 接受 guard、实机 preview 错误消失仍待下一 cold，不能写成 R14 源码已经修复。数字叶 afterclose 6 目标候选及原 14+必要 20 tests 同样未入 main。

## 最新环境与 upstream 边界

[最新 Defender 只读 DIAGNOSIS](raw/28e1e0427ff8995a997043c365ea4078ffe0e39514d23512b51ea6e11d7133d2.json)实际 admin=true，WinDefend/WdNisSvc Disabled/Stopped/PID0，Winmgmt running，provider 声明存在；MSFT_MpComputerStatus 读回 `0x80041001`，MpPreference ExclusionPath 返回 NULL。这是实际禁用配置及未完成的精确五 EXE 登记事实，不能称为恢复成功或把 NULL 数组改成已排除；禁用者、唯一根因、修复结果均未证明。当前 broker 安装缺失事实仍保留，本报告不改变服务、策略或系统设置。

本轮 live main 仍 `19e660105e05395caa6cc95e76c299312ee89d51` clean。只读本地 tracking 观察 `origin/master`=`6866e45eef7600b9e3506ce26453f47f3b253de2`，HEAD 与 upstream left/right=`0/54`。当前实机未 fetch/rebase。afterclose 合入两候选与报告时必须先处理实际 upstream 新增、重新核 current beforeHash 与最小增量，不能把 candidate19 直接外推到未来合入 HEAD，原加载源/导出/build004 证据保持原样。

## B4 首次实际约束不匹配

正式 commit seq130 query lyd.430 event117、seq131 option1 得到 public41/native40；seq132 实际 lyd.431 event118 的 new_title saved scope 原生 typed ID18373。seq133 保存 public42/native41/native:41，随后 G2/G3 同帧读取。[根执行保存 RESULT](raw/66047513385fb4afc50d4f74e53a322f2d16e70deac3b4a60a8d641a8e10c560.json)固定1245181 B、SHA `66047513385fb4afc50d4f74e53a322f2d16e70deac3b4a60a8d641a8e10c560`。所有这些 SDK isError=false，仅证明各正式调用及声明的后置观察。

[首次严格 reader 原件](raw/15aeb39fe3cb3e106869ed378224b93ff0ba963bc18593a769d03ead094b409b.json)是 `OBSERVED_CONTRACT_MISMATCH`；[实际差异](raw/1782caee4b90dd2a455272e0e20f6f6f55e9c7a6e205e23be75d7820efecde71.json)为 **STATE38/47、9 false；保护80/87、7 false**。阶段名 success_postcommit 与目录名描述触发窗口，不能覆盖这次原始 RED。原 STATE/typed checks、expected hash 和 reader 合同未修改，实际 result_code=1/S3/N6、phase已清除也不等于整体成功。root 在首次B4 RED后暂停ACK进行诊断；后续实际ACK/B5见下节，原B4/whole mandate不获通过信用。

title18373 的保存 holder31254、owned1、ownerFaith107 已有实际字段；同帧 G3 的 head_title_full_id18373、holder31254、4 native properties 和 temporal succession law 可独立比对。原 G3 marker/ownerFaith 叶仍为 NULL，ownership 由存档 typed变量支持。原 reader title资格及独立 eventcontext UNKNOWN 保持，title 的局部创建事实不能替代政治/Doctrine/角色保护与正式全部合同通过。

[B3→B4 AST 差异原件](raw/973d111ff2fa5ca8f3511c8e14fd4c1a35a5a60ae828d3c6f5407beaf4e1325c.json)精确列出 9 项失败：Faith107 完整 Tenet/status 投影、Faith107 native Temporal、5 个政治头衔2230/2231/2235/2262/2264 fullAST、faith_and_receipt_actual_title_agree、actual_faith_religious_head_actor。**Rite169 temporal 检查通过**；Faith107 direct Doctrine 列表 before/after逐项相同，doctrine_no_head仍在，不能报告为 Faith/Rite全部Doctrine被改写。

后两项暴露旧 reader 字段假设：实际 saved Faith religious_head 是18373 Title ID，religious_head_title字段不存在；旧 reader把前者当Actor并读取后者。诊断与原失败分开，不把这些检查倒填通过。另5个政治头衔 holder均仍为31254，实际 heir候选列表发生变化；actor protected landed投影中的 laws新增same_faith_succession_law及候选删项是真实副作用。7项保护失败就是5个政治fullAST、actor landed投影、Faith完整投影。钱包及差额的原 typed观察留在 REPORT.json，本稿不推断未获验证的费用行为。

本稿没有放宽合同、更新expected哈希、运行修改版reader，亦未热补丁、改主仓或再次调用游戏。原 Faith direct Doctrine 不变与 derived投影变化分别记录；接下来是否需要 reader、产品修复或额外原生证明，等待执行者依据精确来源诊断，不能仅凭成功事件重命名 GREEN。

## B4 分类与 B5 实际终局

[原 B4 sealed INDEX](raw/1a87e71cf80c20c54083b2bb877734e6a8a2ee906c56abf54fdebb699d242fba.json)13562 B、SHA `1a87e71cf80c20c54083b2bb877734e6a8a2ee906c56abf54fdebb699d242fba`，以及[源分类 REPORT](raw/31ac676cc6f345d786e9cde2e56b5c5fb7609c689bc15800aec14e69f6d85a59.json)永久保留原38/47、80/87 RED。源分类区分实际owned Title的保存/native匹配、旧reader字段模型矛盾、直接Faith与Rite Doctrine、政治heir/actorlaws副作用；不改原STATE、不放宽保护合同、不倒填成功。

执行者随后通过正式结果 ACK 并保存 B5。[B5 sealed INDEX](raw/59bd06ac43eb269458994762c21eac8e5e7a0e04f61661c6e18b91803a7dad6d.json)14085 B、SHA `59bd06ac43eb269458994762c21eac8e5e7a0e04f61661c6e18b91803a7dad6d`；[B5 summary](raw/da9f81bc5cb7f56bfd4e49a58aaa390cbe0d2b392ce72995a2127d6171ad5a4c.json)原 strict reader仍 **38/47、保护80/87、full_B5_pass=false**，S3/N6、result_code=1、phase=NULL，原真实code1不改称partial code。

独立同buffer导出51 captured成员和Rite169，387/387全stamp清理匹配；B4→B5 ACK continuity20/20，新增9 focused tests实际通过，不重复运行。B5 frame public44/native43/native:43，G2/G3 epochs875751/875983，同date53144712；title18373 AST/ownership、四native properties与law均保持，post-ACK额外费用gold/piety/prestige均0。清理/ACK局部通过与整体B4/B5 RED分别授信，R15成功cold尚未发生，nativeHoR/whole mandate/product信用仍NULL。

## 原游戏正常退出与旧失败保留

实际SDK142–148按普通退出链运行。[SDK148原件](raw/fb9c0814c9f7069011653f67c001d027823319631bee011135eaf4e4b62e5945.json)12819 B、SHA `fb9c0814c9f7069011653f67c001d027823319631bee011135eaf4e4b62e5945`；[native原件](raw/a97c79b3fbc86a044ae614f4cf389e8c4e085ee0bd69e747b7c46a3c82bfc13c.json)5908 B、SHA `a97c79b3fbc86a044ae614f4cf389e8c4e085ee0bd69e747b7c46a3c82bfc13c`。SDK147 preconfirm retained handle wait258，SDK148同PID14776、FILETIME134357694970696165、token8345f504f533bbc4ed641c481ed32730等待signaled/exit0，typed_normal_exit_observed=true。source inventory2118fe7d45f3086144d0320300ddd9f8399b6049d0a5f7bc83aa685c8dcef54f；observer调用native_submission_count=0，未重发退出callback。

SDK145 continue_preparation原结果仍dispatch_unknown_claimed及ValueError签名理由，claim已consumed/retry_authorized=false；原SDK isError=false保持。实际caller输入确为64位lowercase hex，不能报告为caller无效输入。之后SDK146 freshquery confirmation_visible=true、stage_consumed=[true,true,false]证明准备callback已执行；没有重试该业务action。SDK147初次等待仍timeout，SDK148独立原句柄exit0才提供游戏退出事实。native观察中orderly_exit_verified=false和autosave_verified=false原字段不改，**autosave保持UNKNOWN/无信用**。

完整SDK142–147包含重复大snapshot，继续留在原永久外置run，仅将实际path/bytes/SHA及明确派生的result projection写入[NORMAL-EXIT-RAW-REFERENCE-INDEX.json](NORMAL-EXIT-RAW-REFERENCE-INDEX.json)；SDK148及native148的小原件完整保全。这些JSON读取不接触save body，也不发SDK请求。

[helper-close source003 INDEX](raw/a27f148aaf5af263ef3306ab739635ed3a9d08ed27e956fd011547fc53b6202d.json)与[实际只读check](raw/6b58f5bfe28b25d266181578d3874f8dde7a9df16230003e661ad85acf5a7726.json)exit0，仅检查SDK148精确绑定，Client_close_requested=false、keeper_STOP_requested=false、lease_mutated=false。原001把Python holder_source当JSON的只读失败、002对真实dispatch is_error:null的错误拒绝均由DELTA及原stdio回执保留；003只修精确byte-ref与serializedSDKisError alias消费，未执行任何helper/CAS动作。

## 实际原句柄退出、CAS 释放与只读闭合核验

[Client close RESULT](raw/463138f9988212ad8a16a215a8dbf2abc6fbb6b82eec4d066d2c51e264169160.json)1328 B、SHA `463138f9988212ad8a16a215a8dbf2abc6fbb6b82eec4d066d2c51e264169160`；[keeper stop RESULT](raw/736024d4a6dc23dbd513aeaa846d009af647da8f0ff990c2644ebcaf2283271a.json)2382 B、SHA `736024d4a6dc23dbd513aeaa846d009af647da8f0ff990c2644ebcaf2283271a`。原保留 Client PID14976/FILETIME134357722948157728/HANDLE500 与 keeper PID19384/FILETIME134357691090686315/HANDLE504 均由原 holder16108 观察 wait0/exit0；没有重新打开 PID 来代替原句柄证据。[HELPERS-CLOSED](raw/55664be507f3580b167e49760094a910837e2c6f5ea3673ef236ceef9b45d8a3.json)3708 B、SHA `55664be507f3580b167e49760094a910837e2c6f5ea3673ef236ceef9b45d8a3`、原 holder FINAL 和 keeper FINAL 一并保全，keeper 最后 sequence3428。

[实际 RELEASE](raw/1254af6680acf89316893102f00e64bd6636aa643c8a5c8017e308caf238d322.json)1291 B、SHA `1254af6680acf89316893102f00e64bd6636aa643c8a5c8017e308caf238d322` 明确 ok=true、task DONE、resources=[]、last_sequence3429。[实际 after-list 原 stdout](raw/b98ed9f1ecc749030fc8b3a40b6349d9bc99133328db037fecce0655b471b554.stdout)104025 B、SHA `b98ed9f1ecc749030fc8b3a40b6349d9bc99133328db037fecce0655b471b554`，ok=true、157 tasks、零 ck3-screen 占用。首次 release001 因 expected CLI SHA 小写被拒，exit3，在 CAS mutation 前停止；source004 只纠正 CLI expected SHA 的大小写。第二次实际 CAS 已成功，随后写 `AFTER-LIST.actual.json` 时与已经存在的 `after-list.actual.json` 在 Windows 大小写不敏感路径上冲突，产生 [原 postwrite FAILURE](raw/2919f9db0c1360200c52379d52df8ed45c07ae9cc40d0c55a1e200bcb98ff2d0.json)。该后置 FileExistsError 不能撤销已经发生的释放，未重发 CAS，原失败和第一次拒绝均保留。

[实际 CLOSED INDEX](raw/639cea99a6d099679361fa205852f810d24165a259958658aba88de7c6207c91.json)4812 B、SHA `639cea99a6d099679361fa205852f810d24165a259958658aba88de7c6207c91`；[原 PREVIOUS-BOUNDARY](raw/de1a0fee95083b1db75ece4c6231b428ac78e660f1b3802a4da8cf9f1d62a172.json)3054 B、SHA `de1a0fee95083b1db75ece4c6231b428ac78e660f1b3802a4da8cf9f1d62a172`；[原 verifier execution](raw/e6ed8f9b8522448598350cdf398c7f89c0fc72e82aac611589583b8938da96fe.json) exit0，精确绑定实际 SDK148、两 helper 原句柄退出、keeper FINAL 和 CAS3429。[PROCESS-ABSENCE](raw/9f2e0880a214eae8c6b656c4894818f8610c615e59582914802d475cdd23a574.json)另以实际新枚举证明 game/client/keeper/holder 原 identities 均不存活、无当前受管 native 服务；这是退出后的独立 absence 观察，不是 exit0 证明。SDK148/HELPERS-CLOSED 原句柄证据承担退出码资格。

本轮生命周期现为 **ACTUAL_RUN_CLOSED**；业务仍为 **RED**。B4/B5 原38/47与80/87没有放宽或改写，387/387清理、20/20 ACK continuity 与9focused通过只授予相应局部事实。原 native orderly_exit_verified=false、autosave_verified=false 保持，autosave UNKNOWN。最终 error log 覆盖窗口尚无额外终局资格；旧 preview 错误及失败回执不覆写。

[实际 Steam 离线偏好字段](raw/061982aa0051c4c042ab7881d06628f918e0bc66d74b5fcb85e4e5c52a14092a.json)仅显示 WantsOfflineMode=1、SkipOfflineModeWarning=0，实际无 MostRecent；早先单数字段/selector UNKNOWN 保留并有追加勘误。该偏好读回不能取代下一次实机的新鲜离线画面审阅，没有 Steam 操作。

## 闭合后的归档基线与下一次资格

只读实际主仓现为 `1a09b47d352e0a93243e9f12420ec6948dac2e8c`，原 R14 loaded/export/build 永久绑定 `19e660105e05395caa6cc95e76c299312ee89d51`；旧 behind54 只是此前 tracking 快照。执行者已对现有本地 origin objects 做 fast-forward，不能由此声称网络已取得最新远端资格。三处现有索引追加与新日报的 beforeHash 重新读取当前主仓，详见 ARCHIVE-APPEND-PROPOSAL.json；不得用旧pending草稿覆盖 upstream 新增的一般进度记录。之后 owner 若修改目标文件，应用前再次绑定 beforeHash。

本报告纳入的 numeric、preview 及 B4 分类均为外置修复候选或静态诊断；R14加载源没有这些后续修复。未来实际修复HEAD及新冷构建/新实机另开轮次，不继承本轮成功资格。上游关于 CK3 1.20.0.4 的迁移文档明确指向 Z 机器/Z:/SteamLibrary，不更换当前 C 机器1.20.0.3的版本绑定。全产品NOT_GREEN，约70%仍是工作量估计，Defender Disabled与5新EXE未登记仍无GREEN，未发布Workshop。
