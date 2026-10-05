# CK3 1.20.0.3：器械军到场后的普通围城实机流

2026-10-05。Readiness 为有限 **production-live loop**：既有器械军已到470后，普通日级观测→实际24h→独立暂停帧→normal SAVE再完成20轮。前置回链 [actual engine delivery](maa-engine-delivery-470-live-transport-12003-2026-10-05.md)、[clock recovery](clock-pause-map-readiness-live-recovery-12003-2026-10-05.md) 与 [siege efficiency](siege-efficiency-inputs-12003.md)，本记录不改策略或新增原生调用。

Runtime仍 **v72/g77/R45/PID122508/source `f26be866fcb1642b81ffbac4707fdc447db1e068`**；Robert29829/episode `native-29829-2bc2d599f7f9`、ordinary campaign/XAR off，environment SHA `ae8140b0e434747c57b2a6223b0602b34c9d49e2ba60df5619f8057bed4aeef9`。Exact build为CK3 1.20.0.3/Steam25652598/EXE SHA `94b55397abb687a3dcd436805a5d885e6be90fa6c693feb44a9e3bbeeade02a6`。

- 唯一SDK **39516 CLOSED0 GREEN**；本批实际 **20 whole/calendar/bounded日、480 raw小时、partial0**，raw53263896→53264376。140 GREEN工具叶＋20 day results＝160原daily JSON；每轮独立暂停/map_ready帧与normal SAVE匹配真实+24h，不借计划max20或resume ACK记日。
- 正式 **4982→5002/36524**、resumed1829→1849、Oct5/W41 +324→+344。旧恢复20与运输12只历史回链、不重读或重计；P0恢复至今52＝20＋12＋本20，只是汇总。器械到场的历史信用不再次计入。
- 末独立帧 **native225/public81/raw53264376**，Robert alive、paused/map_ready=true、activeevent/pendinginteraction null；engine268435481@470 sieging3/route[]、无combat/retreat，War117440524仍active/+25。
- 末whole normal为 **h8920/raw53264376/98897054 bytes/SHA `bc55a3d024f080f6237aebf007af8d7e611733920c6a50546ccd9fd612fa2364`**，来自本轮 `save.observed.checkpoint`。最终pre-save snapshot的 `last_checkpoint_submission` 仍可能指前一天，未拿它替代当天SAVE或信用正常保存未发生的日数。
- 470围城 work **30330515→35282915 raw**（+4952400，scale100000），B3031保持、ETA100→80；3711 work **9859991→12318496 raw**（+2458505），B2941→2912、ETA461→439。两目标仍未占领；ETA是原生估计，变化不计实际日数，兵力下降不由daily缺失供给字段归因。
- 本批首次470破墙的日末观测为 **day02/raw53263944/breach1**，真正normal SAVE **h8866/98703929 bytes/SHA `5ce098c3c390313c2093bfc01cf976808ab1da7390f8d5b7da9072589ef2ad18`**。末帧walls_breached/can_start_assault=true、assault_in_progress=false；assault_daily_progress620000Q与75每日伤亡是原生预测，未算作实际冲锋或伤亡。来源为`days[1].leaves.final.observed.active_wars[0].objective_province_states[0].active_siege.breach_level`及同日`leaves.save.observed.checkpoint`，不猜日内精确触发tick。
- Root曾在raw53263896/h8860独立丰富查询观察470 **K2/M0.94350/D2.47620**，这里只作外部已知prior baseline；不是本20日末帧新测量，不注入daily generic的ordinary/phase null，也不由器械@470/sieging状态重新授K或攻城贡献信用。
- 本轮 **新的K/M/D测量、有效器械贡献归因、围城完成、battle、war victory、natural succession、completed family信用均0**；保持实际普通围城推进的有限scope。后续决策所需fresh rich/health由Root各owner另取，不用旧数填当前空字段。
- 原R44 day03 zero-day `native gameplay step failed: CK3 map state is unavailable` RED仍保留；P0 fix `a6f4a4fc5581af48f7b061c06f953722c47627ea` 与52日后续推进不反推旧具体拒绝类别、失败full-snapshot子域或永久通用故障消除。

唯一本批输入：`Z:/ck3_mod_rewrite_process_assets/g2-resume-20261003/runtime-preparation/v72/root-results/v72-current8751-01/ordinary-r45-post-arrival-siege-twenty-consumed01/FULL-POST-ARRIVAL-DAYS-CACHE.json`，**15007138 bytes / SHA `2a84dfac1c61624b803043680e1d3dd51032fd53c30be29d650facfb27bff078`**。同目录 `receipt-topic-lane/report-fields.json` / `RECEIPT-LEDGER.json` 保存20个独立date/SAVE和七叶pin；父对160原daily JSON各完整消费一次，本lane仅完整读本FULL一次。无TOP/rich/旧12/旧20/共享专题读取，无SDK/窗口/进程/共享/Git/测试/fullbuild动作。
