# 2026-10-05 G2 后台接手施工

实际接手登记时间：2026-10-05T19:14:19+08:00（Asia/Shanghai）。本页接续 [v73 休假交接](2026-10-05-g2-v73-war-background-maintainer-vacation-handoff.md)，记录后续执行，不改写交接时的事实。

用户本次明确要求：“注意，不要开启ck3，我自己要玩。你先只做后台能做的。”并允许最多 64 并发。**当前只进行离线源码、测试、编译、文档和 Git 交付；游戏及界面由用户使用，实机推进等待用户后续授权。**旧交接中允许恢复游戏的指令仅代表当时授权。没有启动、注入、连接、查询或操作 CK3，也不更改用户游戏配置、存档、工坊缓存或 Steam。

源码基线为 `origin/master` 的 `3f2025ca8cfac4e298210925ca0e472025ae5d51`。Root 使用独立 detached 工作树 `Z:/gb0`；八条实现线分别使用 `Z:/gb1`–`Z:/gb8`，隔离共享 bridge 文件的并行编辑。原仓库用户现场、`Z:/g38` 交接树和 `Z:/g78` v73 冻结树保持保全。工作树登记在外置 `Z:/ck3_mod_rewrite_process_assets/g2-background-20261005/lanes.json`，构建与报告回执也写入该外置根。

## 本轮工作包与验收

| 工作包 | 交付目标 | 离线验收及后续边界 |
| --- | --- | --- |
| 完整路线 ETA | 在现有行军查询发布 signed Q100000 prefix durations 与最终 remaining；不重复减 current progress | 新路径 fixture/序列化与 consumer 验证；实际抵达、paused readback 待实机 |
| 独立器械军参围资格 | 发布实际省份 CUnit occurrences、原生 Army、完整 eligibility 和合格 regiments | 复用已闭 native 资格树；K/M/D 实际变化及器械抵达待实机 |
| chunk 数值补员 | 接入现有军力字段的整数算术 consumer，区分合法零与缺失 | chunk cap、截断及已有输入路径测试；不预测未知 F 或下月到账 |
| 损耗分配 | 发布按 stored order 的 supply、siege/raid writer requests 与可计算边界 | 精确算术和 missing-input 用例；未闭最终 setter，不能称最终兵损 |
| 首次接战人物输入 | 补 source-closed `pre_291e210_1640` 与两 registry bindings | DTO、源阶段和消费路径；完整 Entry/人物构造仍部分完成 |
| 实际战场 geography | 通过现有 battle transition/control 发布 terrain、width、retained crossing/holding | 原查询权限和三路径保持一致；不将 retained geometry 当未来接战输入 |
| 盟友拒绝原因 | 原生 CanSend=false 返回 typed rejected 和完整 selected terms | 一个受影响调用用例，零 command/ACK；unknown 保留原异常 |
| 普通 holy order hire | 接入 source-closed 普通 typed provider、dispatch、MCP | 构造/注册/序列化离线测试；雇主、扣款、public CUnit 后态与 live 待验 |

本轮按必要性开八个并行 owner；64 是上限，不是必须占满的目标。Root 唯一源码/Git 整合者，并集中验证新增 native 目标；本机构建采用低优先级、有限编译并发，避免与用户游戏争抢资源。每包一次与风险相称的验证，复用交接中的研究和旧构建证据，不重复旧实机或全 EXE 扫描。

`open_kaishek` 预验：本轮工作对象为 exact-build 原生内存 DTO、序列化、typed consumer 与 native command 布局，不属于 CK3 脚本 parser/finite-runtime 可覆盖语义；记为 `not-applicable`，使用相应离线 fixture。实际失败 attempt 原样保留，测试通过只记 `static-ready` 或局部静态资格，没有真实 paused artifact 不增加 live 信用。

历史日账维持 **5035/36524 正常保存日、resume1882、10-05 +377、G2 5/8、NW2 2/4、自然继承0**。末 whole h9048 和零日 normal h9052 同为 raw53265168；用户自己的游戏进度不计入自动任务。本轮新增自动游戏日为 0，War117 的实际结算、3711 攻占、完整战斗 forecast 和原战役长期目标仍未完成。

结果、测试及提交随每包交付追加在下方，并同步至当天日报和 W41 周报。


### BG-1 盟友拒绝 consumer 完成（2026-10-05 后台接手）

完成：已观测 CanSend=false 经 registered MCP → service → driver 返回 typed rejected，完整保留 C88、first-failed、报价和战争关系；零提交、无 command ACK，unknown 继续原异常。解决旧 helper 丢弃已采样拒绝原因的真实消费缺口。源提交 e2ef3c8d，Root 线性采用 99329688；本报告随该包普通 push。

验证：`python Z:/ck3_mod_rewrite_process_assets/g2-background-20261005/call-ally-diagnostics-gb7/run_validation.py` 两个聚焦用例一次 GREEN，1.576 秒；diff check GREEN。回执与原日志位于同目录 ROOT-DELIVERY.json / VALIDATION.json / validation.log，未重跑旧测试。Readiness 为 Python consumer static-ready，仍无新 live、邀请/参战/扣款或游戏日信用；5035 历史日账不变。下一步为其他后台包整合；动态 C88 和真实邀请独立后态等待用户实机授权。

并行拓扑追加：在八个实现 owner 之外，新增两条仅消费缓存/冻结窄窗口的功能研究，分别闭合最终兵损 setter2657EA0..2657F0E 和 Entry post-A/B291C2B3..291C334。必要性是这两个已知原生输入缺口仍阻碍完整数值/接战消费；不重复已闭树，不接触运行游戏。Root 合并其知识和报告，原实现不等待研究结果。


### BG-2 chunk 数值补员 consumer 完成

完成：现有 `query_army_strengths` 新增 `same_input_replenishment_v1`，按真实 full-DATA operands 计算条件 chunk 请求；chunk maximum×prepared、64位乘法、trunc0、缺额封顶、qualified native0和重复identity alias均保留。解决已有字段尚无数值消费的缺口，不聚合alias或猜未知 F。源提交21e0093c；Root线性采用并随报告普通push。

验证一次：`py ck3_autonomous_player/tests/unit/test_replenishment_numeric.py --artifacts Z:/ck3_mod_rewrite_process_assets/g2-background-replenishment-20261005`，5个聚焦用例GREEN，覆盖现有service消费、算术/截断、合法q0、missing F、alias/conflict和coverage。diff check GREEN；回执同目录 ROOT-DELIVERY.json / offline-validation.json。Readiness为数值consumer static-ready；没有新native构建、game/pipe/UI/Steam操作、paused artifact或新增游戏日。真实下一步是用户授权后fresh query；冻结R46的精确F缺失，不报真实F或下一月到账。历史5035日账与未闭战争/自然继承不变。
