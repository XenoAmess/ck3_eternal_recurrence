# R0073：原版儒家基线通过，学派准备超时

本场 CK3 1.20.0.4，EXE SHA-256 `98702f88a547cde2eaf29a85f93b85f68ee4cf8148336a4f7afaeb75319dd518`，产品源码 `041b2d19fba4d79db919b35943c4d41ad2ef440d`。RUN `bf-202609141645-5434332d4d--li-yu-dao--R0073`，CASE `lyd-release012-keypaths-20261012-024`，keeper `20261012-a36`；实际 PID6284，创建时间1791821087.5746667。2026-10-12 UTC执行，闭场为中国标准时间2026-10-13。

ROOT亲审本场新鲜窗口位移、Steam离线画面和挑战nonce后启动。正式构建83个文件与实际profile逐文件一致；启动标记仅确认夹具将本人的礼仪设为原版经学，不提供制度授权。基线cell实际qualified=true：actor31254，faith `confucian_faith`31，原版经学rite32，原主rite33；GUI信仰领袖为“无”。初始实际学识12。完整G2当时记录4675名信众、38礼仪、2活跃礼仪：经学仅本人且没有合格选举人，道学4674名信众、25县、275名合格选举人。其余无存活信众且无县的礼仪休眠。原版Faith/main rite保留，没有另建儒家共宗。

实际执行一次“入儒门，习经礼”，通过当次typed `lyd.1`映射提交native option0一次。后续新鲜查询确认faith仍31、main rite仍33，本人rite变为150、有效学识13。没有选择白沙、支付T35/T08、捕获议案、提名、投票、签署、创建宗主或保存政治检查点。界面中的“提出学统之议”经直接审阅属于独立制度主张；仅打开详情，没有确认执行。正确转派决议是`lyd_change_school_decision`，“择师问道”/“考察诸家”。

准备阶段沿原900秒绝对截止，于2026-10-12T16:33:23Z超时；没有续时、重放欢迎选项或补写通过。原始错误保存为`TimeoutError: Original normal Quit reserve reached; pending Root phase remains GAP`；本次实际触发的是wrapper固定准备时限，不是已证实的宗主机制拒绝。public run原始返回2；verify原始返回2，明确因最终`lyd-headship-first-result.json`不存在而BLOCKED。不能将其`NOT_RUN`字段解释为游戏没有启动，也不能将已通过基线外推为全部业务通过。

正常退出独立通过。原版菜单取消退出自动存档，单次点击“退出到桌面”；点击回执的foreground_changed_after_click发生在CK3退出后切回Steam，未重试。保留HANDLE实际OS0，native process_exit0，进程树/看门狗/control清理完整，normal_close_qualified=true；public run于16:47:09Z结束。恢复显示1024×768，ROOT亲审当次新Steam离线图；原allocator等待0，keeper停止0，CAS按原5214精确释放，16:49:13Z返回0。业务错误原件保持。

外置根目录`C:/workspace/ck3_lyd_runtime_20261004/lyd-release012-headship-followup-storage-admission-20261012-035`。本场固定总额度768MiB、原到期17:18:08Z；桌面子额度因canonical点击原始PNG开销从32MiB重分配为96MiB，总额度和截止未增加。没有生成三个预留的大SAVE，也没有新native构建或完整36项矩阵。闭场实际用量与剩余额度以该根目录的最终存储结算为准，归还未用额度不等于垃圾回收信用。原件按[统一时效策略](../../../storage-retention-policy.md)复核，不承诺永久保留。

| 原始小证据 | bytes | SHA-256 |
| --- | ---: | --- |
| SUPPLEMENTAL-ADMISSION.actual.json | 10361 | db8952319878ad1c45a97fd4216d8a899c1796adc363ed762b11241a03755f65 |
| ROOT-RUN-BINDING.actual.json | 以原件为准 | 绑定实际R0073/CASE024/keeper-a36，不绑定历史运行 |
| run-command-001/RESULT.actual.json | 1784 | b3b5fde04347d43c0d995b869057cb870c4538862e2504b20e5c169548beb8a4 |
| verify-command-001/RESULT.actual.json | 1791 | bcf743f7af3352a8ad8b9ed51f6dfe3aa52d58cee70297c99f78995025b0477c |
| RESOURCE-CLOSE.actual.json | 19748 | 357805db0a3c421e41443f7b38a7cb9903993d5352bd76f722a1477b338eb51e |

后继修复已落地到 `lyd_release012_keypaths_adapter.py`：仅准备阶段且合同显式声明时，ROOT可以请求按精确决议key定位“择师问道”、T35、T08详情，最多三次。每个intent在提交前消耗，失败不重放；每次原生调用前重新检查原阶段至少剩300秒、总时限至少保留900秒，绝不重置原时钟。导航不执行Confirm或事件选项，不授予IsValid、成本、效果或宗主信用。旧合同未声明该入口时继续禁用；本场封存合同不修改。

针对性检查原始回执在上述外置根目录 `navigation-tests-command-001/RESULT.actual.json` 与 `navigation-tests-command-002/RESULT.actual.json`，分别于16:57:22Z、17:01:38Z返回0。检查包含精确三步导航、白名单、阶段及ROOT身份限制、失败intent不重放、次数上限、原截止边界，以及第一步耗时导致第二步余量不足时停止。该结果证明工具边界，不证明后继实机已执行。

主动T35静坐求得为150威望、临时学识+6；T08授业传经为100金且需真实成年廷臣、临时学识+4。两者须在捕获议案前执行，并用新鲜G2确认本人学识至少15及全部活跃礼仪存在本派合格代表。之后仍需真实逐派三分之二、全玩家同意、当前serial/nonce签署及创建前后完整政治SAVE比较。

本场完整宗主、强化教义主动实践、B4/B5/C3及全部36项实机效果仍未通过。当前公开Steam仍为0.1.1 Alpha内部测试，0.1.2没有上传。
