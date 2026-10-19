# 罗贝尔三十年 v20261019：新局执行记录

用户在2026-10-19明确要求：后续评分结算片改为15秒，旧片不改；复盘首局并写入智能体；随后从1066重开罗贝尔三十年v20261019；继续性能优化及高并发G2研究。这一指令解除旧交接的“暂不开下一局”。

执行机器为 `machine_id: xenoamess-full-tower-eb9d2c1186`，本轮由 `tools/ck3_live_run_id.py machine` 实际读回；本节记录时间 `2026-10-19T02:07:20Z`（clock工具）。此时仍处于新局启动准备，**新Game、首次1066存档、普通推进均尚未发生**。后继运行事实另追加，不倒填本节。

## 已交付源码与复盘

已实际普通推送的公共源为 `d90d5e79ac7d22b3376ca70f3fccebd3faef516f`（本地b417f430经fetch/rebase后的身份）。[首局复盘](robert-first30-lessons-2026-10-19.md)区分已确认的AUTO193授独立、知识/定义ID绑定错误、主线修复未证明冻结场采用、陈旧held缓存和缺失运营采样；不把统治县10→2全部归因于一个窗口。

版本化[经验目录](../../tools/g2_saved_campaign/robert_first30_lessons_v1.json)及[实际采用复验](../../tools/g2_saved_campaign/qualify_robert_first30_lessons.py)让新SDK与已审固定源码逐叶比对，再由实际loader核新state中的民粹知识跨ID复用。它不是游戏业务通过证明。公共[评分入口](campaign-score-presentation-v1.md)现为450帧/30fps/15秒，全部九章保留；旧60秒评分片、首局09成片及无声素材未改动。[月度日历叶](campaign-score-monthly-cadence-v1.md)使用CK3固定365日/raw24，计划1066.9.15→1096.9.15；实际截止接线和完整评分输入仍须分别验证，纯叶不授准点能力。

## 并行研究及采用边界

| 包 | 已完成内容 | 此刻边界 |
| --- | --- | --- |
| M0 | [反抗领主战争白和政治代价来源](g2-m0-research-2026-10-19.md) | 原合同complete保留；不改投降倾向，不当作本局已发生处罚。 |
| M1 | [fresh direct县与realm未知分离](g2-m1-research-2026-10-19.md) | additive turn bundle，未知不能误报空集；不是完整realm失地跟踪器。 |
| M2 | [98条知识携带及旧批事件闭合](g2-m2-research-2026-10-19.md) | 新state仍需实际迁入；7条exact-only保留限制。 |
| M3 | [resident继承P51采用与期待时差](g2-m3-research-2026-10-19.md) | 软件组合已验，实际新运行采用和自然继承待观察。 |
| M4 | [合法贷款决议门槛/十槽费用源码](g2-m4-research-2026-10-19.md) | C++未编译/部署，完整本金债务及到账unknown、资金信用0。 |
| M5 | [非主导宗主战争风险覆盖缺口](g2-m5-research-2026-10-19.md) | 无新采购权限；目标命中不等于必失地。 |
| M6 | [generation0观察修复及完整采用闭包](g2-m6-research-2026-10-19.md) | 真实新增具名收益→自然有用终态→普通消费仍缺。 |
| M7 | [新Game冷恢复后的resolved义务缺口](g2-m7-research-2026-10-19.md) | 后继限定lineage源码继续研究，不迁pending/UNKNOWN；更多seed/government未补。 |

G2原定义仍为M0–M7，**6/8**。六个原完成项不重开验收；M6/M7为剩余重点，研究与录制/游戏成绩分列。

Python首批性能优化把派系历史查找从全量收集改为惰性逆序，16种旧新路径等价、新增3例通过；8853行最近4行命中的局部测量0.519→0.041毫秒，miss路径略慢。原战争测试一个宣战断言在旧新helper均失败，未为测试改变策略。第二批大combat过期帧前置拒绝候选此刻尚未提交/冻结，不能计入当前新SDK。

Native [四条临时JSON字符串边优化](knight-json-streaming-performance-2026-10-19.md)只有固定源全文守恒验证，未编译/部署，不能称实机提速。新局计划复用已资格Native25；最终DLL/EXE与广告仍由本次实际启动核对。

## 新局准备与容量

唯一现场owner为runtime准备线程。旧screen声明已按精确CAS退休，旧Game51028退出1及旧异常闭场原样保留；新租约由既有keeper维护，不复活旧PID。用户再次明确确认Steam离线。runtime已在新外置attempt取得窗口位移与亲审离线图（2026-10-19T01:57:13Z），没有切Steam在线、重启ToDesk或操作个人OBS；这只是该时点准备事实，不替代未来必要的新鲜检查。

业务SDK已按公共d90d5e79的canonical Git对象冻结1420叶、58,720,484 B；为满足真实environment/runtime消费者一致性，另建同commit的clean sparse host，保留旧host与第一次freeze历史。候选根为 `D:/codex-ck3-demos/2026-10-14-robert-30year/continuation42-cold-prep/p51-fresh1066-v20261019-prepare01`，实际运行/profile仍待安装。旧P51会构造退役蓝窗且要求overlay HWND，因此当前正在将新录制入口、relay ACK与门禁迁到现有无窗口decision-text publisher；禁止只换标题或伪造旧HWND。

[本机新容量摘要](evidence/robert30-v20261019-capacity-summary01.json)记录新的64GiB首阶段峰值与24小时复核，截止 `2026-10-20T01:48:56.993837Z`，并行小研究256MiB包含在总额中。全部其它预留621,808,745,452 B与首局OUT146,027,527,160 B继续保守计入，未把旧例外、删除epoch或free当新授权。旧媒体三个派生候选仅列计划、没有删除。C/Z重型写入未准入；小型必要配置及源码记录与重型资格分开。

下一步沿既有清洁开局入口完成真实Host/App/Queue/Native/EXE绑定、知识迁入与一次采用复验、无旧蓝窗录制、原生frontend选择1066 Robert及初始SAVE；普通推进前落实同一次native sentinel arm的日期截止。当前尚不报告开局或任何新游戏日。

## 02:26后继：新Game进程已启动，游戏日尚未推进

同一 `machine_id: xenoamess-full-tower-eb9d2c1186`。runtime owner于2026-10-19T02:26:24Z取得新启动回执：Game PID214568、birth FILETIME134368503807325674，新profile/0 mod/无旧SAVE，Native25 DLL仍为 `a1448baa860a88826cbb9ae50ab67c93506560f2772c0515e4ef51e934002f40`，新pipe `\\.\pipe\xar-g2-robert30-v20261019-campaign01`。注入子进程exit0、tree-gone；主Game句柄由原supervisor持有。实际来源为外置新场的 `ROOT-ACTUAL-GAME-LAUNCH.json`，记录路径由后继完整运行清单固定。此刻MainMenu尚待录制放置/实际像素准入，App/Queue尚未启动，不能计1066角色、初始SAVE或新游戏日。

新SDK/state对固定reference的实际经验资格attempt02已PASS（23202 B/SHA `f25b10da60b545f52fbb2a0ba70d7a46caf13475b4e1fc54c73b5d236f26d147`），含已审民粹知识cold-ID绑定。attempt01因经验目录把 `bridge/native_driver.py` 误写为根路径而FAIL；该数据错误已精确修正，原失败保留，不能把它写成SDK缺失。三个真实newSDK清洁frontend软件合同已通过；早前fixture旧schema/换行溢出及旧import优先级问题保留其诊断，未放松生产门禁。

日期截止公共实际driver/executor/Protocol软件组合已完成5项，覆盖单Arm多日、Plan/target一致、Sway内部规划旁路、route窄收尾和终点不再resume；新Native25运行tuple真实采用仍待首批结果。后继combat过期帧优化22种等价与4项回归通过，4MB合成输入0.5333→0.0020秒，不能外推整局。原生JSON优化现有9组C++字节/SHA一致验证；109.28→108.02毫秒的计时区间重叠，不认定可靠提速。EXE登记不可用已保真实回执，实际采用经授权的独立Python/DLL离线备选，没有更改Native25/系统设置。

M7后继源码已补完成resolved台账与精确checkpoint的新Game谱系：原证明精确保全后才能退役，pending/UNKNOWN不迁移，原 `_checked` 不放宽；普通AUTO零新增查询，仅resolved SAVE多一次真实小帧。软件消费者组合及旧进程不可观察分支分别定向验证，当前不计新实机/G2完成信用。全部后继源码将一次合批冻结后再启动App/Queue，不热换正在运行的App。

## 02:36后继：最终业务冻结完成，录制首试正常清理

同一 `machine_id: xenoamess-full-tower-eb9d2c1186`，观察时间2026-10-19T02:36:06Z。后继源码已实际推送为 `dc4b7d56787ac769c809d1ab0d7b6057be2377e6`，业务SDK采用src02共1423个Python文件、58,769,189 B；保留Host/Game的d90d5e79身份。实际采用目录与独立Git对象reference进行经验资格attempt03，PASS，回执22,718 B，SHA `5eefe8e98d70908d80edaa77493ea0396b728ab7c367116aa9f89e3458720743`。此前失败和通过回执均保留。

来源固定在同一外置根 `D:/codex-ck3-demos/2026-10-14-robert-30year/continuation42-cold-prep`：`robert30-v20261019-campaign01/runtime/ROOT-FINAL-SDK-FREEZE-P37.json`（399,506 B，SHA `db68e72afa3ef6e562af656ad0b341471e4ee63f52e011405ff3ba3b22912c95`）、`p51-fresh1066-v20261019-prepare01/PRE-APP-SOURCE-ADOPTED05.json`（3,398 B，SHA `3d00b102c9389f49fc23484b5368d823a444f8cd700f4723792a5ee7dbe16ee5`）及该准备目录的 `LESSONS-QUALIFICATION03.json`。M7只提取小型相关pins，未复制完整inventory或读取活Driver。

专用portable OBS配置范围已获得实际存储追加准入，计入原64GiB而非新增预算；个人OBS及二进制不写。来源 `D:/codex-ck3-demos/2026-10-19-robert-v20261019-storage01/STORAGE-ADMISSION-OBS-SCOPE01.json`（7,573 B，SHA `e951f2eeba0afdb153a613290f70c876c147a951ac9cd4c654d9139a7cda4179`）。02:33:26Z小型容量观察为D可用891,818,803,200 B，距既有guard 73,498,543,132 B；不是新的全卷预算。

录制首attempt的自有OBS PID181812抢焦点，实际foreground由Steam HWND52505028变成该OBS HWND83305260，触发原守卫；worker随后正常OBS exit0并确认inputs_unbound，失败MKV仅约13KB。Game与decision-text publisher保留，未恢复或操作用户窗口。此刻仍为MainMenu、App/Queue未启动；修正仅在唯一runtime owner处进行，尚无1066角色、基线SAVE或新游戏日信用。

## 02:47后继：录制阻点与并行后继

同一 `machine_id: xenoamess-full-tower-eb9d2c1186`。第二次录制启动 `a30b0a91-c277-49ca-a984-1269e809166b` 的自有OBS PID2396仍触发原foreground守卫，已正常OBS0/unbound；新增诊断将变化定位到 `Qt653QWindowIcon` 隐藏主窗，而非首次向导。显式tray/SW_SHOWMINNOACTIVE没有解决实际故障。AGENTS.md:503明确要求最小化且不抢焦点，因此未采用隐藏自有窗占foreground的放宽方案。下一候选复用已有AppView路径，将retained-generation唯一自有OBS主窗移至Game所在Desktop1，不激活、不切桌面、不恢复用户窗口；原最终foreground守卫继续执行。来源为runtime的失败attempt与 `p51-obs-owned-desktop-review01` 四项合成资格，后者不代表实际移动成功。Game与publisher保持，仍MainMenu/App未起。

首失败worker的原请求实际有PID250672/birth134368507483354329；08诊断曾误读为未留birth，后继已更正。其当前进程不存在不等于历史exit0，历史exitcode保持unknown。存储追加范围仅按精确request tuple、当前absence/空端口/未armed未started/OBS正常退出及无写占用核验许可专用配置归档和新profile，不扩大64GiB或删除媒体。

[M1月度来源映射](g2-m1-monthly-observation-source-map-2026-10-19.md)确认当前普通月度数值仍只有gold；已有cash-v2尚未进入同帧MET，不能把AUTO前态财务移到动作后月点。[M5参与战争事实后继](g2-m5-participating-war-threats-2026-10-19.md)确认普通战术已有all-participant敌军覆盖，并给出未接消费者的去重关系投影；CB及双方主将已有query DTO，剩余重点是后果消费者与未发布宗主战争范围，不新增采购/投降权限。

WAL实验恢复修复及98项知识实际迁入观察已在 `b000c9a623eec88a48c95a2f8e2ad72eaf59198e` 推送。[隔离资格](evidence/driver-wal-qualification-2026-10-19.json)保全144行全部字段，JSON键顺序差异及首失败不隐去，计时缺失保null。实验仍default-off，不修改当前src02；后继性能源审计发现只读query本已有延后持久化，不能将所有零日回合都归因于完整写入。研究与现场并行，不把未采用候选、软件测试或等待自然证据计为G2完成；仍6/8。
