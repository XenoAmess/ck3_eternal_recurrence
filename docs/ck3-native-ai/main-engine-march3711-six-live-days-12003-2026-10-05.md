# CK3 1.20.0.3：主军与器械军向3711的6个真实行军日

2026-10-05。停机前的有限 **production-live loop**：两支已派遣军队沿保留路线继续6日，器械军实际到中间路点3717，尚未3711会师。实测绑定 **v73/g78/R46/PID104164/source `d22e9a1cd3fb1062f6c66282f044daafa016718a`**、Robert29829/episode `native-29829-2bc2d599f7f9`；CK3 1.20.0.3/Steam25652598/EXE SHA `94b55397abb687a3dcd436805a5d885e6be90fa6c693feb44a9e3bbeeade02a6`、env `20ba8b4f1c4e99c6575a0029adf17ea4cae5e492a5a516fc7fc3b234768a7cbf`由Root提供，[前470捕获产物](siege-assault470-capture-live-loop-12003-2026-10-05.md)保持冻结且未重读。

- 本批实际 **6 whole/calendar/bounded日、144h、partial0**，raw53265024→53265168，requested budget完成且SDK已closed。正式 **5029→5035/36524**、resumed1876→1882、Oct5/W41 +371→+377、P0恢复85仅汇总；没有下一批日数或到达信用。

| 联（military行仅引父转发sealed派生FAST） | 实际输入与边界 |
|---|---|
| Movement | engine268435481首次3717为day6：before raw53265144@470/route[3717,3711]→after raw53265168/native138/public25@3717/route[3711]；仍moving7→3711。main301989997全部6日仍470/route[3717,3711]/moving7；未把route长度当ETA或3711到达 |
| Siege / proxy | guard184549452@3711/sieging3，同Siege486539314 C23699268→24279868（+580600raw）、B2912→2883（aggregate−29，不归因）；G500/F6/breach0/assaultfalse/未占领、ETA322→319仅估计。7generic phase字段及soldiers null仅本批generic日域，不判rich RED |
| Events / receipt | 本lane唯一小cache含6轮日期连续+24h，postcondition/paused/map_hud/eventnull、ordinary_events=[]/event_resolution=none；18项时间动作accepted/submitted。12端点×3自军combat/retreat均false，外敌4893/combat2不记玩家接战 |

- 首次3717路点与第6日 normal **h9048/raw53265168/99036288 bytes/SHA `9354912f261fca203aeda8e0cedaef6c5b579c210444556faefc590233db783d`**日期匹配，SAVE为 **Root验收事实**，本lane未读原件。后续0日query SAVE **h9052/SHA `e0a7fb224723c62296a60ce6683c7b7f2e7614a6d6536e6a3ab8cbf2a5840cec`**不替代6日normal SAVE、也不增加日数。
- 完成六日接续与首次waypoint观测；**3711会师/新增Kfort或K/M/D测量、strategy complete、war victory、player battle、natural succession/new family信用均0**；War score38保持。Movement lane的source_field_path string/map初稿错误已修自有normalizer并保留Harness RED，未重读小cache或动作，不是capability RED。
- Root已在 **2026-10-05 07:22:48 UTC**正常停止R46 PID104164/managed47337（CLOSED0），留给用户游玩数小时。这里仅离线封存；0SDK/gameprocess/window/prepare-stage-build/profile动作，后续新日与到场验证由Root在用户再次授权使用CK3后另行执行。

唯一实读 `Z:/ck3_mod_rewrite_process_assets/g2-resume-20261003/runtime-preparation/v73/root-results/v73-current8938-01/ordinary-r46-main-engine-to3711-six-days-consumed01/EVENTS-RECEIPT-SECTION-CACHE.json`，**16021B/SHA `7305336e65990ef927262d96af57cfb120d4a8a46b4286c83eb161225638a94a`**；父6个新004各一次，FULL **365407B/SHA `629708ec0b8941189a29193fee4198c2695ea424ba4fa6c36a4dcdd98cc1b955`**与original pins仅回链未读。`receipt-lane/report-fields.json`保留6轮及Root/父字段来源；0旧source/TOP/其他cache读取、0共享/Git/测试/fullbuild。
