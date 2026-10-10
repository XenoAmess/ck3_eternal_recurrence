# 2026-10-11 R52 就绪超时与实际闭场

R0052 的公共 run/verify 均实际 exit 2，首次业务步骤之前超时，0 业务动作、0 SAVE、0 游戏日推进。一期保持 **75% / NOT_GREEN**。实际小原件见 [INDEX](acceptance/2026-10-11-i4-natural-r52/INDEX.actual.json)，前置 Source11/CASE3 准入见[预检记录](2026-10-11-i4-source11-preflight.md)。

## 时间边界

本场绑定 Source11 `b539d0180b66a22ec4efa2ccf5c6acd40339e621`、O11、独立 CASE3、a14 keeper 与运行时冻结 MAIN `7b22ca5af8883a3a87f357109fa9113a92f6f8d5`。以下时间均为 2026-10-11 CST：

| 原实际事件 | 时间 |
| --- | --- |
| 公共 run 开始 | 00:24:06.191641 |
| host report 开始 | 00:24:12.581909 |
| 首个原生 semantic frame | 00:39:09.921505 |
| 公共 run 返回 readiness timeout | 00:39:10.956682 |
| 存档当前 actor/date 实际绑定完成 | 00:39:12.539320 |
| host 进入 hold（原 hold deadline 减 7200 秒推导） | 00:39:13.268813 |

原生帧可用之后仍须完成存档身份与初始阶段验证。本场 qualified restore 晚于公共退出 **1.582638 秒**，hold 晚 **2.312131 秒**；不能解释为已经在公共期限内进入 hold、只是轮询漏读。公共等待与 host 冷载等待各自建立 900 秒计时，但起点和覆盖阶段不同。原 CaseClient 起点未落盘，不能用公共命令开始时间冒充它；冷启动缓慢的具体原因仍 UNKNOWN。

下一源码工作包补公共等待的实际起点、截止和终态回执，保持既有 900 秒上限，不重启旧窗口、不接受截止后的业务资格。统一权威 deadline 的行为调整另需明确合同与验证；本场不追认通过。

## 实际行政收尾

Root 使用现有正常 Quit API，在独立 `administrative-close-001` 保留原 PID 820、创建时间与实际进程句柄。直接审阅中文游戏菜单、取消 `autosave_exit` 勾选后，经统一坐标换算点击“退出到桌面”。没有重放业务或延长原 8400 秒绝对上限。

实际保留句柄 OS exit 0；native job/tree/control 清理、原 host Popen wait 0、独立行政关闭命令均完成。原公共 `case-output/normal-close-result.json` 继续缺失；独立行政结果只证明收尾。公共 verify 仍 `NOT_RUN_OR_PRESERVED_FAILURE`、business false。native report 的生命周期 GREEN 不代表产品业务 GREEN。

最终 Steam 新鲜窗口位移画面由 Root 直接审阅，底部显示“离线模式”；桌面恢复原 1024×768。第一份 STOP 候选误要求 supervisor 原件不存在的 `run_id` 字段，实际 exit 1，未写 STOP；保留失败后，后继只改为原件中实际 PID 与精确 `--run-root` argv 绑定，执行 exit 0。keeper 原线程/allocator 原等待均 0，最后 owned sequence 4551；公共 CAS release 实际完成，task done/resources=[]。

00:59:18，预约 003 闭账实际 exit 0，未来写入预约剩余 0，限定新增目录保留逻辑量 **441327935 B**，当时 C 盘可用 **622230110208 B**。无新增删除，无旧 seed/native/source 重计、无缓存 seed 复制或 native build；物理占用及历史峰值仍未知。期限见[当日存储记录](../maintenance/storage-retention-2026-10-11.md)。

## 并行分析与正式下一门槛

R51 的精确耗时分解见[原分析](acceptance/2026-10-11-i4-natural-r52/r51-six-days-duration-report.actual.md)：公共 run 开始至首个业务 snapshot 为 **858.385525 秒**；首个 snapshot 至第六日后 snapshot 为 **280.792360 秒**。六次自然推进的 host body 合计 **28.658156 秒**，35 个 host step body 合计 **48.139512 秒**，step 间隙合计 **232.652848 秒**。重复提交边界占明显等待，但子进程、pin 校验及任务总线各自占比未计时，不作归因。把三个同轮只读观察合成有序 plan 仍只是建议，尚未实现或验收。

正式 B4/B5/C3 的依赖复核见[原分析](acceptance/2026-10-11-i4-natural-r52/formal-next-case-readonly-report.actual.md)。当前 O11 没有 G2/G4 对应 MCP 注册及 capability 声明，不能只补 metadata 启用；B4 holder 漂移的生产根因仍 UNKNOWN，不能无差别重复原工厂实验。B5 公共 adapter 可独立施工，但必须先绑定实际 B4 PASS 的新 SAVE88、同一个动态 T 与正常闭场，再作零工厂冷重载。C3 继续依赖同一个真实 T 与有效 challenger/sponsor 图。本轮没有给这些正式业务增加通过信用。
