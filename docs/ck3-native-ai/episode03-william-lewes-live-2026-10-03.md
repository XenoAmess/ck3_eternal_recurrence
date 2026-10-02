# 第三期：William 刘易斯围城，本机 1.20.0.3 实机研究验收

整理日期：2026-10-03（Asia/Shanghai）。本次已闭合真实开局取数、合军与行军、普通围城的一日推进、短暂强攻的启停，以及城破后的占领与战争分项回读。验收范围限于下述本机样本；它不把旧 1.19 实机或 1.20.0.2 研究当成本机 1.20.0.3 验收，也不意味着所有桥能力已验收。

所有原始 JSON、请求、回执、截图、连续录像、旧尝试和失败结果永久保留在 `D:/ck3-war-episode03-20261002-a01/`。仓库只保存本文及[精简证据索引](episode03-william-lewes-evidence-index.json)，不复制 CK3 二进制、存档或大体积原片。索引记录实际文件路径、bytes、SHA-256、证据范围及详细报告入口；详细报告继续保留逐条 request/response/receipt 的 pin。本文整理仅读取既有证据，没有重新调用游戏、SDK、桌面或任务总线。

## 版本、会话与来源绑定

根执行任务标记为 R0156，本案实际 SDK 会话为 `live-a06`，episode 为 `native-33388-ebbc6357f8b6`，CK3/bridge PID 15372，玩家 William 的 native character ID 33388，War 1、对手 32399、target title 202。战争查询的 canonical CB 是 `norman_conquest_cb` / database index 23，不能改称普通 `claim_cb`。原版 William 存档经正常前端加载；本节的角色、日期和 war 身份来自实际回执，地名另以原图中的“刘易斯围攻战”“南撒克逊”对应。

实际 hello 报告 `ck3-1.20.0.3-msvc-x64`、adapter ready、exact build match；CK3 EXE SHA-256 为 `94b55397abb687a3dcd436805a5d885e6be90fa6c693feb44a9e3bbeeade02a6`。生产 DLL 来自外置 `native-build-unit-zero-a03/xar_ck3_bridge.dll`，4,505,088 bytes，SHA-256 为 `eb03ee5cf602b110fb04642fdd5bd023a35de926a3ec94f12b035d37e2c2a686`。其构建记录的 117 个 BOOL 开关全部 OFF，编译 adapter capability 集合保持 62 项；实际 hello 还包含桥协议能力，不能把两种计数混为一谈。所选 12 项 native CTest 全部通过，包括实际 .3 semantic worker；这是离线构建证据，不代替下文实机后态。

启动前的新鲜 Steam 离线证据是 `steam-offline-challenge-a17-graphics-recovered`：两张原始 1920×1080 图有不同的当前 UTC/nonce challenge，根代理直接审阅“离线模式”；图形/采集恢复后的新像素有独立回执。本文另直接审阅已保全的 challenge-2 原图，不把截图时间戳单独当作新鲜度证明，不声称进行了新的桌面采集。

`runtime-source-live-a06-before.json` 冻结 387 个输入：382 个 Python 源文件、2 个 bootstrap 输入、DLL 1 个、额外 EXE 2 个。after-capture 和 after-stop 扫描均 `PASS_DISK_INPUTS_UNCHANGED`，无 added/removed/changed。城破原始 transport 回执实际报告 211 个已加载项目 module 的 `__file__`，逐个落在 `D:/we3` 并与 before manifest 的磁盘 bytes/SHA 匹配。早期 CArmy 审阅报告记录 210 个模块；这是采样时点不同，不用早期列表替换末段列表。路径与磁盘来源一致不等于已读取驻留 Python 代码字节，也不证明旧 pyc 的内容；这两个边界继续保留。

## 实际问题修复与零号完整 ID

原版 William 样本暴露了 public CUnit ID 0 在 action expansion 中被当作非法正值的问题。修补覆盖真实 public CUnit 的严格 `0..INT32_MAX` 合同、普通动作 grammar 和相应原生 producer/查询字段；bool、负数、溢出、错误类型及不规范十进制仍拒绝。没有过滤或隐藏军队 0，也没有把所有 character/war/province/siege/native handle 都改成可为 0。

随后军力查询又实际拒绝 `army_strengths[0].native_carmy_id=0`。只对 ArmyStrength DTO 该可空字段改为严格非负 int32：null 表示没有解析到原生 CArmy，0 表示经 storage/完整 generation ID 验证的合法 CArmy。生产读取器和 serializer 原已支持这个值，因而这次 DTO 修补未改变上述 DLL。knight 嵌套及其他 native handle 的原合同没有被此字段外推放宽。真实 producer→serializer→严格 Python 的 19 行夹具、91 项 normal/`-O` 回归和独立 MSVC army fixture 检查通过，实际 a06 又闭合了同帧成功回读。

开局 `native:2` / native revision 2 / public revision 3 / date_raw 53144328 同帧的 raw、public snapshot、strength query 和四分项 query 一致；实际 CUnit/CArmy 为整数 0，current/max 1000/1000、1 团、available。五军如下，当前人数合计 5660；人数本身不除 100000。

| public CUnit | native CArmy | 团数 | current / maximum |
| ---: | ---: | ---: | ---: |
| 0 | 0 | 1 | 1000 / 1000 |
| 1 | 1 | 3 | 920 / 920 |
| 2 | 2 | 3 | 1220 / 1220 |
| 3 | 3 | 3 | 920 / 920 |
| 4 | 4 | 3 | 1600 / 1600 |

实际合军使来源 1、2、3、4 依次消失并保留目标 0；后续增援使用完整 public ID `16777220`，不得把低 24 位槽号 4 当作同一军队。路线仍严格核对 status、source_count 和完整列表，无法观察的路线不伪造成空列表。实际跨海段有 `embarked` 与 `complete_nonempty`，登陆和最终驻守有 `complete_empty`。此前 .3 路线 producer 的状态/count 不一致已通过新 DLL 的真实回读恢复；这一成功不扩写为所有观测面已修复。

普通 move/preview 的目标由实际公告 `action_steps` 决定。向友军当前自境省份 2174 的请求曾在 Python 投影层被拒绝，没有向 native 发送订单；本场通过已公告的战争目标 1506 汇合后继续。合军、增援后的当前指定围城军队曾 `0→16777220→null→0`；null 是无法唯一 join 到 public unit 的真实未观察值，不补填旧军队，也不把 `besieging_army_id` 当成唯一工作量贡献者。

## 一日推进、守军与增援

省份 1506 / 完整 Siege ID 6 / War 1 是本场持续核对的对象。C 表示当前工作量，T 表示总工作量，G 为驻军，B 为当前合格参围兵力；work/fraction raw 有各自 scale，B/G/current_soldiers 是人数。截图显示公元 **1067 年 1 月 10 日**，不是 11 月。

| 暂停端点或阶段 | 原生/public revision、date_raw | 实际读数与变化 |
| --- | --- | --- |
| 1 月 10→11 日 | 192/193→195/196；53147136→53147160 | 同 Siege6，C 2.46→4.92，净 +2.46；T 305.434、G420、B5660、fort3 两端相同；breach0、assault=false |
| 守军/总量改变的下一段 | 53147184→53147208 | G420→460，T305.434→325；C7.38→9.84 仍 +2.46；预计剩余122→129日 |
| 增援到场第一日 | `live6-reinforcement-arrival-a01` step1 | B5660→6746，C24.60→27.06 仍 +2.46 |
| 增援下一日及合军后的新一日 | 同一 Siege6，输入重新绑定 | C27.06→29.84、29.84→32.62，各 +2.78；后者 T325/G460/B6746 相同 |

一日动作 raw date 差精确为 24，reported/requested horizon 1 日、速度 1，暂停结束。对应原图显示 fort3/G420/B5660、60 攻城武器、每日 2.4；增援后的 1 月 21 日原图显示 B6746、G460、69 武器、每日 2.7。GUI 是一位小数展示，不能由 `|1` 自行确定完整 formatter 的截断/四舍五入规则；2.4/2.7 不能替代原生净变化 2.46/2.78，tooltip 分项低精度加总也不是精确 raw 复算。

器械贡献的静态研究因此作了必要勘误：当前人数须经 `count/stack` 归一化后与 effective siege stat 固定点相乘，不能写成“siege_value×当前人数”。精确 .3 指令段 proof 及旧文档字节都保留；[推进专题](episode03-siege-progress-1.20.0.3.md) 已回链勘误。60→69 是当前 GUI 参与器械显示，不能仅凭这个差值证明武器型号、团规模或购买贡献的完整归因。标准 JSON 不独立发布普通 D getter；上述 +2.46/+2.78 是实际区间净 C 变化，尚不闭合全部 modifier/phase 账本。

## 缺口与短暂强攻

1 月 29 日原图显示“小缺口”，native breach1；后续 4 月 19 日原图显示“大缺口”，native breach2。对应 tooltip 分别显示事件间隔 -10%/-30%，只证明当时界面与状态；本次标准 JSON 不发布完整 Siege phase/history、疾病/断粮等级或独立 phase counter，普通 `ordinary_events=[]` 不代替这些字段。GUI 当前16天或12天也不能说成“下一事件还剩16/12天”，或唯一反推出军官/trait/XP 来源。

短暂强攻的直接前后如下；139/139 项 request/response/receipt 检查见 `assault-real-readback-a02`。a01 的路径分隔符比较误报保留，a02 明确勘误，没有改旧实机回执。

| 字段 | 开打前 native251/public252 | 一日后 native255/public256 |
| --- | ---: | ---: |
| date_raw | 53147592 | 53147616 |
| C / T | 52.08 / 325 | 68.46 / 325 |
| G / breach | 460 / 1 | 460 / 1 |
| eligible B | 6746 | 6578 |
| assault 日 work / 损失预览 | 13.6 / 168 | 13.2 / 164 |

开打返回 `assault_started`，随后完整暂停帧确认 flag=true；速度1的一日推进后，C 实增 **16.38**、比例增加5.04个百分点、B 净少 **168**。16.38 是围城总净变化，13.6 是起点强攻 work 预览；其差2.78只是算术余量，本样本没有独立工作量账本证明各 producer 的贡献。B 减少与损失预览相同，仍不能声称逐团死亡归因或“所有强攻必扣预览人数”。完整 CArmy 的上一兵力查询早了8日，两次完整兵力查询相隔9日，不能把它改称 CArmy 的一日损失。

停止返回 `assault_stopped` 与同 Siege flag=false、can_start=true/can_stop=false、C仍68.46。钉定的 driver 合同等待同 War/Province/Siege 的暂停后置再返回，因而不是仅有 ACK；但该停止响应没有独立完整 date/paused 对象，不补造这些全局字段。强攻日后总分仍0，没有该日新的四分项 after 查询。随后普通围城收尾，不拼成“持续强攻导致城破”。

## 4 月 22 日完成、占领与战争分项

`fall-real-readback-a01` 的119/119项检查闭合三日收尾和新鲜 after query。末段强攻已关闭：

| 日期与暂停帧 | date_raw | C / T / remaining | 本省状态 |
| --- | ---: | --- | --- |
| 4 月 19 日 native363/public364 | 53149512 | 318.11 / 325 / 6.89 | 未占领，Siege6 |
| 次日 native366/public367 | 53149536 | 320.87 / 325 / 4.13 | 未占领，Siege6 |
| 最后在围 native369/public370 | 53149560 | 323.63 / 325 / 1.37 | 未占领，G484/B6384、fort3、breach2 |
| **4 月 22 日 native372/public373** | 53149584 | 对象已消失，不发布 C 终值 | occupation_observable=true、occupied by33388、siege_observable=true、active_siege=null、G25/B0 |

三次真实一日动作逐一对应相邻暂停帧；前两日各 +2.76 work，第三日只捕获完成态，不补写 C=325。军队0原地、route complete_empty、非战斗/撤退，sieging(code3)→regular(code1)。同完成 frame/date 的直接军力查询读到 CUnit0→CArmy0 available、27团、当前 **6384**、最大6747。完成后 B0 表示没有活动围城，不表示6384人死亡；public snapshot 的 soldiers=null 也不伪填6384。

| 四分项 query | battles | imprisonment | occupation | ticking | attacker / defender 总分 |
| --- | ---: | ---: | ---: | ---: | ---: |
| 4 月 19 日，同 native363/public364 | 0 | 0 | 0 | 0 | 0 / 0 |
| 4 月 22 日，同完成 native372/public373 | 0 | 0 | **13** | 0 | 13 / -13 |

这个 before 距完成3日，目录名 `immediate-before` 不能改成最后在围的同日四分项采样。原图最新战争 tooltip 显示南撒克逊占领 **+13.2%**、当前上限 **+150%**，总分显示+13%；DTO发布整数13。不能把GUI13.2、DTO13和静态150混为同一个精度或声称已经达到上限。`norman_conquest_cb` 定义确有0.8目标比例和双方占领cap150；GUI已观察到当前上限150，但底层加载后的 side policy raw字段、原生 n/N collector、held-goal clock和小数 ticking 仍未直接读取。详见[占领与战分专题](episode03-occupation-war-score-1.20.0.3.md)。41条 objective province 投影不是公式分母。

省1609在末段始终由第三方31280占领，场中另有挪威占领背景；这个native字段本身不确定31280属于哪方参战者或关联哪场战争。本实验没有隔离这些并发战争、其他 Siege或军队。仅最后一天的已发布 occupation/holder 行中1506改变，不能由此认定整个世界只发生该事件，也不反推出“单城恒为13”或计分分母。其他 Siege16777230/省1606仍变化。

完成相邻原图显示通知“围攻获胜”“你现在控制了南撒克逊”，地图军队6384。`ui6-163225-9bbcae09` 与 `ui6-163445-0409322b` 当前郡面板明确显示法定 title holder 为 **公爵利奥夫温（Leofwine）**，占领者为“你”。这支持区分当前军事占领与法定领有，不构成围前/围后同一 owner pair 对照或和平割让验收。通知显示奖励 **9金币**；原生余额659.04942→668.40942净增 **9.36**，没有收支ledger，不把全部9.36归奖励，也不指定0.36余量来源。

## 保全、退出与剩余交付

实际城破 raw 是 `live-a06/responses/163137-b65bb795.json`，SHA-256 `f026fd974dc974f151484f29f5522f51d67ec2c7a23e43bf671a4fae9ba9c9e5`；已发布 raw 叶值与完成公开帧一致，public额外 source、remaining/布尔等投影不要求整字典字节相等。diagnostics.last_error=null、snapshot rejection=0；publish诊断存在deduplicated记录，不能概括成“全部diagnostics=0”。helper历史的 `game_outcome_certified=false`、未重交 mutation、未独立live window检查值保留，不用报告总PASS把它们改写。

城破 checkpoint 为 `william-lewes-fall-1067-04-22.ck3`，74,680,288 bytes，SHA-256 `fb0336fe3d570031fa640dc7b0b6d311b09fd62c9dec7b8b18aa47861453d8b0`。受管会话正常 stop，bootstrap session.ok=true、sdk/supervisor error=null、SDK与keeper线程退出，cleanup_proven/tree_gone=true、job最终0进程、最终CK3 inventory为空。after-stop仍387输入未变；显示已恢复1024×768。`live6-finished-release.json` 保存 CAS release 退出0及任务总线完成 sequence3821。正常stop是受管进程树清理证明，不掩盖回执内 CK3 termination exit_code=1，也不把它冒充自然退出0。

`capture-10` 到 `capture-17` 的原片、probe、marks与录制进程回执保留；其中原片15实际城破首次出现 PTS 的独立复验仍 **pending**，本文只闭合其录制文件/probe和原生/相邻图后态，不宣称该首现时间已复验。当前 script、render、production admission、外部交付均仍待完成；没有对最终成片的人类1×完整审阅或签核。后续重编码/替换字节须重新绑定证据与人工签核，不重新解释旧尝试。

相关机制入口：[军队与完整ID迁移](army-1.20.0.2-migration.md)、[路线可观察性](army-route-read-status.md)、[围城推进](episode03-siege-progress-1.20.0.3.md)、[围城事件](episode03-siege-events-1.20.0.3.md)、[强攻](episode03-assault-1.20.0.3.md)、[占领与战分](episode03-occupation-war-score-1.20.0.3.md)。各专题的静态来源边界照旧；本页是它们的本机 .3 实例证据，不覆盖专题原始研究结论。


## 2026-10-03 补验：原片12–17完整解码与城破首次画面

本补验追加到上一节的历史状态之后：此前“原片15首现PTS复验pending”是报告冻结时的状态；现仅此项已由独立原片复验闭合。最终报告为 [review.md](D:/ck3-war-episode03-20261002-a01/review-captures12-16-a01/review.md)（SHA-256 `559ea16b9e1a23fbeaf02687f46d4a26488ab4083b256f5e40f8a1cdfda51343`）及 [review.json](D:/ck3-war-episode03-20261002-a01/review-captures12-16-a01/review.json)（SHA-256 `05b820ee4166b50c21d35f71d9fed8625f597acb9e64ad9e28382b798ceea01d`）。原始失败尝试、既有回执和上文边界均保留，未改冻结的九个制作输入。

原片12–17全部实际解码，共9866帧，所声明机器条件检查PASS。报告的AI看图范围为42代表帧、197个半秒网格样本和87个关键窗口连续帧，不是9866帧全部逐图验收，也不是对最终成片的人类1×完整观看或签核。原片15的精确邻帧定位如下，`n` 保持审阅器的实际编号，不按30fps元数据猜算PTS：

| 原片15实际帧 | 原始PTS（秒） | 独立复验定位 |
| ---: | ---: | --- |
| n1432 | 52.733 | 首次占领画面的前一帧 |
| n1433 | **52.767** | 首次占领画面 |
| n1438 | 52.967 | 围城界面淡出完全消失 |

已选原片区间仍为 `[50.033,59.500)`，cue092保持不变。首次画面PTS与4月22日的原生占领后态是两种相邻证据，不把影片PTS解释为native revision或原子同步时间。本文另直接查看上述三张原分辨率PNG：n1432仍金币659、正常围城、无占领条纹，但底栏日期已显示4月22日；冻结复验报告把该帧日期写为Apr21。此处保留报告原字节并记录这一局部勘误，前态仅指占领前态，不宣称日期/金币/占领字段同时刷新；首现n1433与淡出n1438的定位不变。

原片14的n191/6.733秒仍为正常每日2.7，n192/6.767秒首现强攻每日16.3及停止按钮；n1147/40.867秒仍1月29日，n1148/40.900秒首现次日和每日15.9，下一帧n1149/40.933秒地图军标才变为6578，此时围城兵力窗仍显示6746。末帧n1682/59.967秒仍有停止强攻按钮。因此本片没有拍到停止强攻，不能给它配“镜头内停止成功”的验收结论。片外typed `ck3_stop_assault` 的同Siege暂停后置回执仍有效，按上文记录其证据范围；UI每日16.3/15.9不改写成强攻单项producer的13.6/13.2，不借本次原片定位扩大归因。

本次只解除原片首现PTS这项pending。最终script/render、production验收、外部交付仍由根代理按实际结果另行闭合；当前没有最终成片的人类1×签核，本文不替制作流程宣称完成。
