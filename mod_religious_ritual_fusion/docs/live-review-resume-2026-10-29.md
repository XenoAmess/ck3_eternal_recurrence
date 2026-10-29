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
