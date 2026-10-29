# 2026-10-29 续工：创建禁用原因实机补验

`machine_id: 4-8e1c2f1861`；时间均为 UTC。本轮从[休假交接](../../docs/handover/2026-10-29-religious-ritual-fusion-vacation-handoff.md)继续。游戏来源提交为 `441d1b96e66fde076507b5947423114a06e1c3b5`，生产实现仍为 `16e74ec285fd727b886a41f2e38652e41e246494`；本记录不追认为此前构建或游戏输入。

## R0054 的实际业务

2026-10-29 的 R0054 / a64 使用 Steam CK3 1.20.0.4，EXE SHA-256 `98702f88a547cde2eaf29a85f93b85f68ee4cf8148336a4f7afaeb75319dd518`。CK3 PID 11560，出生时间 `1793285222.2241364`。公共入口完成新的 freeze、六链资格、runtime、plan、prepare、preflight，六链全部 RAW_EQUAL_PRIOR；复用 Java 55 文件图、Native a09、90 文件验收投影及 v3 fixture，未重编或重复运行既有 236 项回归。

原生开局和夹具自然完成后，玩家 31254，1066.9.16 暂停，当前 Rite150 / Faith13 / Religion8，虔诚499。通过当场原生来源选择器选中诺曼礼 B151，并免费打开草案：

- 默认 3/3 核心时，页面和实际创建按钮悬停均显示双方贡献不足及实际费用500。原生 `rrf_commit` 为 visible=true、enabled=false、clickable=false。
- 通过当场新鲜 query_generation/widget_id 取消一个已选核心后为 2/3，页面与悬停均再显示核心数量要求；贡献和费用原因继续存在，原生按钮仍禁用。
- 取消只提交一次，原生窗口实际隐藏，当前礼仪、信仰、宗教、核心和教义内容不变，钱包仍499。观察批次 `capture_epoch` 本来不同，比较内容时仅排除这个观测身份字段。
- 只读 `rrfa.30` 恰好产生一次 `RRFAT: TEST PASS no_product_change_readback`，无 FAIL。
- 唯一一次原生 checkpoint 后，独立 Java V4 原wait0；同一拒写/拒删句柄的文件身份和 SHA 前后不变。保存中玩家仍用 Rite150 / Faith13、虔诚499，没有 `rrf_` 草案、结果或冷却变量。没有 before-save 完整 AST，因此不声称全部对象字节相同。

两张原始全幅 PNG 均由 Root 实际查看，有 PID/birth、SCREEN、原生按钮状态、坐标换算、悬停和文件身份 sidecar；没有裁切或生成像素。

| 原件 | bytes | SHA-256 |
| --- | ---: | --- |
| `screenshots/ui-R0054/01-default-draft-disabled-create.png` | 4224150 | `fd3389ef23b78f83423868d731c02dbeb883d93ad89af01b8bb6bc8e4619aa96` |
| `screenshots/ui-R0054/02-two-core-disabled-create.png` | 4237826 | `39c48f026fecb0593d3d6c9326c90cf5ec59f40c33face99f60ecfff8ae443a9` |
| `state/profile/save games/xar_checkpoint.ck3` | 68427072 | `33158bfbabfb7b649aa12772726bb06e86f848323ebc9dc49a0aac580f16225c` |
| `R0054-UI-BUSINESS.actual.json` | 155867 | `3e9c29662d1541d9a5cd3da5c7e6013a2484955f9abaea9f0277e897f14ce87a` |
| `single-V4-a01/report.json` | 589494 | `dbea2904818c9b2164eb6d7dec4f41b92c37ec460d5ac0a9f95ead39d2188fc6` |

上述相对路径的场根为 `C:/workspace/rrf-development-20261024/review-fixes-a01/ui-creation-blocker-final-a01`；state 为其 `managed-states/review-zh-ui-creation-blocker499-a01/state`。业务及 V4 原件在 `metadata/normal-close-a01/root-business-oracles-a01`。大原件不复制进仓库。

## 公共入口的超时必须保留

原 hold 截止15:07:12.4287217，正常退出预留180秒，Root 阶段最晚15:04:12.4287217提交。实际五项业务汇总和 response 于15:04:37产生，晚约25秒；入口此前已记录 `Original normal Quit reserve reached; pending Root phase remains GAP`。因此本轮业务补充证据五项齐全，**公共 run/verify 仍均退出2，不能称本场公共验收通过，也不追认原12项完整矩阵**。原超时、awaiting、Root response和正常退出分别保留，未覆盖旧结果或重放动作。

15:05:27正常资源关闭：原生OS0、独立retained OS0、host0；allocator/keeper原wait0。Root原PID4104/wait2已消费。15:05:29前完成显示恢复1024×768并释放SCREEN，CAS14618。关键原件为 `metadata/public-operations-a01/root-execution-a64/ALL-ORIGINAL-TERMINALS.actual.json` 和 `metadata/ROOT-SERIAL-UI-a64-original-b01/ORIGINAL-WAIT.actual.json`。

SDK checkpoint 的 episode身份仍为空、`save_binding_mismatch`，没有授 continuation 资格。原始R0053显示缺陷、R0052的19/20及其他未完成场仍保留；R0054证明当前创建原因显示已修，不替代保存态自然灰色决议提示、正式发布和真实Steam缓存验收。0.2.0-alpha尚未发布。

## 存储

在新有限准备准入下，精确回收R0053的3740个可重建shader文件，逻辑146942067B、原生分配155353904B；保留四个目录、两份存档、图片和167份保护证明，原生身份及内容守卫通过。删除原wait0，回收量仅一次计入gross addback，不降低累计highwater或退款配额。原shader载荷已不可读取；失败结论和必要原件继续保留。原件与执行清单在 `metadata/R53-retirement-execution-b01`，记账CAS357。

保护复核仍为2026-11-01T04:00Z，不因本轮续工自动延长。后续使用新场次、新准入和新的Steam后台离线回执。

## R0055：第35天观测齐备，公共回执字段错误

同一 `machine_id: 4-8e1c2f1861`，2026-10-29 UTC，源码 `c2245a5a756745f14f0ba1769ce31ee05cdcbdcc`。本节外部根为 `C:/workspace/rrf-development-20261024/review-fixes-a01/review-completion-b01`（C18）。公共入口启动R0055/a65，CK3 PID18400、出生 `1793288513.048298`，实际Steam EXE版本及SHA与R0054一致。复用原v5、MTS48/DES56闭包及真实day35存档（69117980B，SHA `001e9f169c346037de53925b4adcfc0e28db3f4c5e038f077f1c30d1cb89a676`），未重编不变Java/Native。

原生恢复确认玩家31254、date_raw53145216、暂停及地图就绪、Rite155/Faith106/Religion8，虔诚raw=-40000、scale100000。前后原生宗教、钱包、日期、信条与教义内容一致，观察字段capture_epoch分别保留。原始`rrfa.22`只调用一次，产生恰一次`faith_persisted_readback` PASS、零FAIL；没有推进日期或写新检查点。

载入时结果窗口打开，完整树查询真实截断；随后只查询实际具名actions/close子树，经本实例generation3/widget1关闭一次。该展示操作执行`remove_character_flag = rrf_result_dialog`，**不宣称所有旗标不变**；没有打开融合草案、resume、apply或付款。

Root已查看两张原始2560×1440全幅PNG及PID/birth、SCREEN、坐标、generation5 sidecar。同一宗教礼仪融合分组中同信仰在前、跨信仰在后，两项均自然灰显；列表行仍可打开详情，不能将灰显标签的enabled=false外推为整行不可点击。同信仰完整提示显示缺少本信仰可用来源及十年冷却，跨信仰显示十年冷却；两项均说明打开草案免费、创建仅成功扣费，未将当前负虔诚作为入口收费限制，没有原始no_item_selected文本。

| C18相对原件 | bytes | SHA-256 |
| --- | ---: | --- |
| `screenshots/cold-R0055/01-same-faith-disabled.png` | 5186338 | `fba4db7229bbb2facb5497680183d337cdda1b53a54a3199078b331019ed4866` |
| `screenshots/cold-R0055/02-cross-faith-disabled.png` | 5208278 | `c036742d8b3ddd03147321725e1e20c6a291a6e28dabc11d5c3eec6a1a8e8fa3` |
| `metadata/normal-close-a01/root-business-oracles-R0055/R0055-DAY35-BUSINESS.actual.json` | 680123 | `240f17e2544e6259fbe6ece1f7260ef348a15f526aa215333814c05fd6a0ec5d` |
| `metadata/public-operations-a01/root-execution-a65/ALL-ORIGINAL-TERMINALS.actual.json` | 13486 | `e8b25631abdfdb965e0f9a1f5406c2c743783e0f662a75f924c6e6fb0a3ca4f0` |

Root回复距阶段截止仍1171秒，却误用`facts`；共享生产消费者读取`assertions`，真实拒绝`Original product GUI/semantic requirements incomplete`。run/verify原退出2，不覆盖原回复。后续发现R0054迟到回复也有同一字段错误，因此除原超时外还存在独立合同错误。后续直接提交`assertions`，不添加字段别名。

R0055于15:55:25附近正常关闭：原生OS0、保留句柄OS0、host0、allocator/keeper原wait0；Root PID5584/出生`1793288449.4257162`原wait2于15:55:32消费，显示恢复1024×768，SCREEN释放14626。新3项观测不追认原20项矩阵、continuation、county地图或发布通过。

## R0056：未启动Game的真实终态

R0056/a66只到公共allocate READY。原启动前容量检查拒绝，旧闭场元数据加后续退出预留超过normal-close子额度；原180秒等待结束后只停止已证实属于本场的never-Game keeper。无public-run、host、CK3、Native报告或控制动作。Root PID12104/出生`1793289908.0017447`原wait1、allocator PID9912原wait0及keeper原wait0均保留。

SCREEN释放前两次分别因缺CLI SHA参数、小写SHA而在CAS前拒绝，原回执保留；第三次实际大写SHA下CAS14630释放，子命令原wait0，真实终态为`waiting/status`、`expired-own-claim-released/unresolved_red`。外层误期待done而退出1，不能据此重放已生效CAS或制造DONE。只读既有latest-screen consumer已接受原waiting回执，闭证为`metadata/public-operations-a01/root-execution-a66/NEVER-GAME-CLOSED.actual.json`。

后续a67因原Prepared已消费而拒绝；a68使用新UI-b02 Prepared，又因R0055不是最新机器分配而拒绝。两次均在注册、SCREEN、Game之前。最新分配仍为R0056，不能用R0055加最新SCREEN替代R0056本身的恢复资格。

共享`validate_allocated_unrun`实测能读取原allocator三联，却不接受本次Root wait文件名/字段、无guard容量等待超时和真实expired waiting释放。旧分支要求的guard、idle或DONE从未产生；不补造或重命名原件。候选及真实拒绝在`metadata/R56-unrun-closure-candidate`。共享修复另获有限8MiB准入，须修共享生产者/消费者及真实reducer回归；禁止在该修复准入下Game或热改旧runtime/SDK。

17:05:57Z共享修复完成闭写。既有生产入口新增`--capacity-wait-root-wait`及独立typed closure分支，保留原Root1、allocator0、keeper0、180秒超时与真实expired waiting释放；READY时stdout按原完整JSON前缀验证，最终日志另验keeper终态。恢复仍进入原writer锁内复验，不授Game、正常退出、业务或发布信用，也不以复用PID认定旧实例仍在。未新增Python生产模块；本旧OS/Game custody模块不在一期Java迁移接管清单。

持久CI新step完整四命令原wait均0：新producer→完整reducer→原writer锁回归10项、旧unrun stages73项、旧prelaunch admission48项，共131项零跳过。两个完整测试模块strict/strict-equality及修改的10个生产函数完整AST strict通过，不外推旧生产大模块全量strict。证明为`metadata/shared-recovery-fix-b01/CI-step-07/COMMAND-SOURCE-EXECUTION.actual.json`，33808B、SHA`2589c361343ddd380531a7e91ba66d69aeb50fa6edf8ea22eba5cd20805a37be`；真实Root cwd、70份源码前后字节相同，执行身份如实为base c224的SCOPED_WORKING_TREE。

真实R0056经新shared CLI和完整reducer只读资格通过，原PID18612/wait0；b02封包9212B、SHA`8530b95c46505dfaa46440186c94670ab1bf953c4cc98c6e3cf1cffcf2765136`，canonical release3028B、SHA`ad0a3d90f506623d8d45d3c8eae1240dae68cc1d91bfac870fccf84582e3befa`。闭证`metadata/shared-recovery-fix-b01/WRITERS-CLOSED.actual.json`3919B、SHA`a57dee3eaf4db69f1a10f545a513dd9a9d622259c21eb120fc8db8451a1a047f`。期间没有allocate、Game、SCREEN、CAS或冻结输入写入。后继仍须新源码冻结、新runtime/Prepared及独立容量准入，不能直接运行旧C18 Prepared。

## 容量与辅助进程补注

R0054关闭后精确回收3740个可重建shader文件、原生分配155353904B；四目录、三存档、截图与失败原件保留。删除原wait0，CAS361只记一次gross addback，总值12318605440B，不降低highwater。原载荷已不可读取，原件在`metadata/R54-retirement-execution-b01`。

本任务只读PowerShell格式化命令PID5388/出生`1793284319.0585272`未退出，曾占约25GB RAM并使分页增长超过旧16GiB预留。原exec session ID被丢弃，**原Popen wait不可恢复**；确认身份及命令后仅终止该辅助进程，新打开OS句柄实际退出1，不冒充原wait。可用RAM恢复约27.5GB、分页回落，原容量失败及进程前后证据保留。不能概称本轮所有辅助命令均有原wait；以上保护复核期限仍不自动延长。
