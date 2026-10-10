R51 六个自然日的可核验耗时（只读后继分析）

现有时间戳不支持“六日的业务执行耗时约16分钟”。公开 run 从14:52:10.178011Z开始，第一业务 snapshot 从15:06:28.563536Z开始，第六日后的 snapshot 于15:11:09.355896Z完成：前置为858.386s（14分18秒），业务步骤跨度仅280.792s（4分40秒），从公开run开始合计1139.178s（18分59秒）。前置含冷启动/公共准入/等待，但这些子阶段没有本次可用的精确时间拆分，不能全部称为shader编译或纯加载。

35个具名步骤的host起止累计48.140s；其余232.653s是步骤间隙，不能直接等同队列本体时间。六个advance_day累计28.658s，各为6.564, 4.584, 4.366, 3.873, 4.842, 4.429秒。公开进度投影独立记录6次每次24h、总144h；原观察0..5仅覆盖120h。自然日流逝本身不是这段墙钟的主要部分。

18个model/tree查询在host内累计5.523s，单项0.072–0.857s。每轮都重复三个独立控制plan；两次查询间隙累计71.458s：

| school观察 | 首query至末query完成/s | 三query host合计/s | 两个中间间隙/s |
| --- | ---: | ---: | ---: |
| 0 | 11.951 | 0.240 | 11.711 |
| 1 | 14.076 | 0.551 | 13.525 |
| 2 | 10.892 | 0.846 | 10.046 |
| 3 | 15.001 | 0.880 | 14.122 |
| 4 | 12.244 | 1.575 | 10.669 |
| 5 | 12.817 | 1.432 | 11.385 |

原 queue stdout 的 ACK 为实际发布后时间。样本 observation0000 tree：前一model结束15:06:55.533374Z → ACK15:07:01.910634Z为6.377260s，ACK → host开始15:07:01.935447Z仅0.024813s。第一advance的ACK → host开始为0.074918s。其他相邻步骤常见4–8s间隙；可以确认重复提交边界开销显著，不能在缺少时间戳时把它精确归因于Python启动、文件/pin校验、owner检查、报告读写或轮询。

已读源码为冻结Csr10/tools/ck3_mod_acceptance_client.py。execute_plan先guard、写一次性plan、校验queue pin、新建subprocess并等待其结束，随后await_steps；queue-result仅记录argv与exit_code，未记录子进程起止。await_steps轮询sleep为0.1s。已读host仅最后16993B（offset240000），可见await client.execute(plan)、hold接口及poll默认0.05s；没有读取全部257KB源码，不能凭这些默认值解释全部间隙。最小缺口是CaseClient提交入口、queue子进程起止及guard完成时间，不能用文件mtime补成精确调用时间。

最小可施工后继是使用既有CaseClient.execute_plan(list)，将同一暂停帧上的model-before、detail-tree、model-after合成一个有序只读plan。ROOT已定位observe_decision第181–196行为调用接点，本文未追加读取该adapter。每行仍保留原ID、tool参数、fresh_revision行为；模型前后对paused、PID/generation、actor/date、public/native revision的同一性检查，以及完整GUI模型/footer判定保持。每个自然日继续独立提交days==1；保留实际24h结果、事件边界与独立snapshot验证，不批量推进多日，不重放、不延长hold、不增加新的guard。

该接点可避免每轮两次queue启动/校验边界，但71.458s仅为当次可避免边界的观测上界，不是已测得收益。cold前置不受此改动影响，不能承诺任意剩余冷却在2小时内完成。

第六次school query仍失败且无完成信用。15:11后的失败发生时刻/至15:22公开run返回的间隔原因UNKNOWN；原失败queue-result没有起止时间。CAS原因UNKNOWN；未据head/tail推断owner丢失原因。原public run2、业务RED、无finalSAVE/到期/cold信用不变，不解释raw tick349。

来源首先是已发布docs/li-yu-dao/acceptance/2026-10-10-i4-natural-r51/INDEX.actual.json及其business/SMALL-PROGRESS.actual.json，再按具名actual-results只读768B头/256B尾取得时间（最初3个样本各读1024B头尾）；完整读取范围、范围摘要与所有步骤时间分别在READS.json、TIMINGS.derived.json。实际新读111830B，低于131072B；没有读取native whole-report、Save/PE正文，没有游戏、总线、Git、MAIN修改、重测或R52动作。分析仅保护7日等待ROOT决策，旧资产TTL不续。
