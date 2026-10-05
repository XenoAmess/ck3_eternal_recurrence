# CK3 1.20.0.3：470强攻后的首个真实保存日

2026-10-05。Readiness 为有限 **production-live loop**：Root原生强攻启动后，实际推进、观察与正常保存首日；[强攻合法性与原生链](episode03-assault-1.20.0.3.md)是既有研究入口，本记录只写本轮真实结果，不重读旧源/帧/case或改策略。

冻结绑定为 **v73/g78/R46/PID104164/source `d22e9a1cd3fb1062f6c66282f044daafa016718a`**、Robert29829/episode `native-29829-2bc2d599f7f9`；CK3 1.20.0.3/Steam25652598/EXE SHA `94b55397abb687a3dcd436805a5d885e6be90fa6c693feb44a9e3bbeeade02a6`，environment SHA `20ba8b4f1c4e99c6575a0029adf17ea4cae5e492a5a516fc7fc3b234768a7cbf`。完整冻结元数据由Root提供，此lane未读取冻结文件。

- Root SDK44379独立确认启动后 assault=true/CanStop=true、0日h8945；其原始launch属于War_goal。SDK **96712 CLOSED0 GREEN**，实际 **1 whole/calendar/bounded日、24h、partial0**，raw53264472→53264496；正式 **5006→5007/36524**、resumed1853→1854、Oct5/W41 +348→+349。此前56日只历史汇总，恢复至今57不重计旧日。
- 本lane唯一实读为events/receipt小cache。执行core为native11/public5、postcondition、paused/map_hud/eventnull；actions仅set-speed1→resume-map→pause-map且均accepted/submitted，实际日期+24h支持推进，ACK本身不代替独立观察/SAVE。
- 下表phase/losses行引用父转发的其他section owner已派生FAST，events行来自本lane唯一小cache；未读取另两个cache或新的17098查询原件。

| 联 | 首日实际输入 | 完成与未完成边界 |
|---|---|---|
| Phase / work | 470 assault/CanStop前后均true；C36272855→37264295，combined Δ991440/Q100000＝9.9144work；phase length/counter/canAdvance/event/selectedenum前后null | 完成强攻仍active与总work变化观测；未完成phase trace或ordinary/assault分项拆解 |
| Losses | 470 B3001→2926（aggregate−75）、G550不变；预测cas75→73/work620000→600000raw；3711 B2912/G500/assaultfalse，CΔ97436raw | 完成aggregate强度对比；实际/current casualty counter缺失、ArmySummary soldiers=null，未证明−75均为强攻伤亡；预测值不是当前损失计数 |
| Events / receipt | ordinary_events=[]、event_resolution=none、activeevent=null；三项时间动作均submitted，实际+24h/paused后置 | 完成本轮执行/空事件收据；不把时间动作ACK冠名强攻启动或独立SAVE原件 |

- 正常SAVE **h8948/raw53264496/98800507 bytes/SHA `38b1caf126cd4c68ee360d7dfdf937d06cab414f4e0e710b4a142c8966c2d2af`**、独立assault仍true、末paused/map_ready/Robert alive/eventsnull均为 **Root验收事实**；本lane没有读SAVE或独立snapshot原件，execute native11/public5不是独立17098查询帧。
- War117440524仍+25，三自军sieging3/route[]/targetnull/无combat与退；未授围城完成、war victory、battle、natural succession、completed family或本lane新rich K/M/D测量。损耗lane初selector多匹配已从其typed派生cache修正并保留attempt，不是新的游戏故障；没有重读section或重跑SDK/测试。
- Root后续10日45827仍active，与本1日独立。本包不打开该数据、不授未来日数或结果；首日闭环完成，阶段轨迹、分项work及损失归因仍未完成，后续由各观测owner补口。

唯一实读输入 `Z:/ck3_mod_rewrite_process_assets/g2-resume-20261003/runtime-preparation/v73/root-results/v73-current8938-01/ordinary-r46-assault470-first-one-day-consumed01/EVENTS-RECEIPT-SECTION-CACHE.json`，**4733 bytes / SHA `772d7ae5436bbe418bc1b1a0402aaeccf7729511e3ec6e9fbceacfee12bb36e0`**；父唯一004原件SHA `38787de79e69e371114f630ebf2867b6fdf645b456e8ef801c008cb5939d8e4a` 及FULL cache SHA `bf317db97edf8782010edab47e13a250a174db4f580e14a4ab7b9667ec563e52`仅pin回链，未读取。`receipt-lane/report-fields.json`区分本实读、父派生与Root验收来源；本lane0原件/TOP/SDK/窗口/共享/Git/测试/fullbuild。
