# CK3 1.20.0.3：470强攻接续取得占领的真实闭环

2026-10-05。**production-live loop**：接续 [前10保存日](siege-assault470-ten-live-days-12003-2026-10-05.md)，再实际12日后取得470占领与围城终止，并匹配同日normal SAVE。Runtime仍 **v73/g78/R46/PID104164/source `d22e9a1cd3fb1062f6c66282f044daafa016718a`**、Robert29829/episode `native-29829-2bc2d599f7f9`；exact CK3 1.20.0.3/Steam25652598/EXE SHA `94b55397abb687a3dcd436805a5d885e6be90fa6c693feb44a9e3bbeeade02a6`、env `20ba8b4f1c4e99c6575a0029adf17ea4cae5e492a5a516fc7fc3b234768a7cbf`均引Root冻结事实。此前firstday/ten产物不读、不覆盖。

- SDK **12352 CLOSED0 GREEN**；实际 **12 whole/calendar/bounded日、288h、partial0**，raw53264736→53265024。正式 **5017→5029/36524**、resumed1864→1876、Oct5/W41 +359→+371；强攻流程至今23保存日、P0恢复79仅历史汇总，不重计旧日。
- 本lane仅一次实读events/receipt小cache：12轮actual core连续+24h，postcondition/paused/map_hud/eventnull，36项set-speed1/resume-map/pause-map均accepted/submitted；末core native105/public49是执行帧，未冠名独立rich或SAVE原件。

| 联 | 实际完成边界（phase/loss引用父转发sealed派生字段） | 结论与未完成 |
|---|---|---|
| Ownership / phase | 前11日和day12 before raw53265000仍未占/assaulttrue，C54957235/rem42765；day12 after raw53265024目标IDs仍含470，但470数据行移除，main301989997/engine268435481 sieging3→regular1@470 | 日域只证明首次移除/army变化，不把missing赋occupied或activeSiege=null。Root同日final TOP补占领证据；generic phase null仅本receipt，不判独立rich RED |
| Work / cost代理 | 470前11个可比较active区间C净+8921180raw、B2311→2074（aggregate−237）/G550；预测cas23→20/work480000→420000raw。终结day12整行缺失，work/强度净差未知，missing不补0。3711全12 C净+9419232raw，末C23699268/B2912/G500/ETA322估计 | 完成11有效区间work/aggregate代理对比，预测不作实测伤亡；不补470完成C=total/100%，Root占领后B0/G25是新scope，不能记成全军/全驻军被杀；真实伤亡counter与成本归因未完成 |
| Events / receipt | 12轮ordinary_events=[]、event_resolution=none，真实连续+288h；24端点×3自军的combat/retreat均false，外敌268435597保持4893/combat2 | 完成执行与空事件收据；foreign combat不记玩家入战，时间ACK不替代Root同日占领与normal SAVE |

- **首次完成边界是day12 raw53265000→53265024**，不是由最终occupied反推更早日期。Root同日提供的 **final TOP**明确470 occupied=true/occupier29829/F6/G25/B0/active_siege=null；匹配normal **h9020/raw53265024/99018510 bytes/SHA `161a70d2196e5bc94e5aa74245454ffa8f1dd03bc6984fde1fcc524f66256fe7`**闭合capture。此lane未读TOP/SAVE原件，未把20965其他owner未交付rich结果归为来源，不声称观察到精确完成tick。
- War117440524 score **25→38**，guard184549452@3711仍sieging；完成的是470占领/围城终止的有限流程，**war victory、县转移、玩家battle、natural succession、completed family均不新增信用**。本段不拆ordinary/assault work或把预测损失当实测，不授本lane新K/M/D测量。

唯一实读 `Z:/ck3_mod_rewrite_process_assets/g2-resume-20261003/runtime-preparation/v73/root-results/v73-current8938-01/ordinary-r46-assault470-next-twelve-days-consumed01/EVENTS-RECEIPT-SECTION-CACHE.json`，**42597 bytes/SHA `d96a2841c89ee6ef784e059d301a85e83c5a238db92d090be4005b833e7d724f`**。父12个新004原件各一次，FULL及original pins仅回链；`receipt-lane/report-fields.json`分列本cache、父phase/loss、Root final TOP/normal SAVE来源。0旧source/帧/TOP/20965/其他section读取、0SDK/窗口/共享/Git/测试/fullbuild；后续战争结算和新日各自另计。
