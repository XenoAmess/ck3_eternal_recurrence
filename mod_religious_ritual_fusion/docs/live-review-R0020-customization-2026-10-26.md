# R0020：同ID定制保存，独立冷载待验

`machine_id: 4-8e1c2f1861`。场次为 `4-8e1c2f1861--religious-ritual-fusion--R0020`，执行来源为干净提交 `20ffb3994e6db39c744f4c87ea9dbf7766e6374c`。CK3 1.20.0.4，EXE SHA-256 `98702f88a547cde2eaf29a85f93b85f68ee4cf8148336a4f7afaeb75319dd518`。本记录接续[R0016、R0017记录](live-review-resume-2026-10-26.md)，没有发布0.2或更新Workshop。

## 已完成的实际操作

新进程PID5080从保全的R0016-created存档加载玩家31254、Rite155、Faith13、Religion8；日期53144352暂停。进程出生FILETIME为十进制字符串 `134374707552060788`。通过原版编辑界面设置以下内容，并从RRF保存入口进入零报价的原生确认窗：

| 字段 | 实际保存值 |
| --- | --- |
| 名称 | 星辰归一礼仪 |
| 形容词 | 星归 |
| 信徒单数 | 星归信徒 |
| 信徒复数 | 星归信众 |
| 描述 | 由两份礼仪融合形成，保留双方传承。 |
| 图标 | `christianity_cathar` |
| RGB | `[110,55,126]` |

名称输入使用实际Windows INPUT ABI、扫描码Ctrl+A、Unicode与Tab，原始截图显示全文；不能用按键ACK替代。最终确认只提交一次，经原生popup控件执行；通用动作回执的postcondition仍为false，后续独立查询确认窗口关闭、同ID155的新文本实际存在。该回执未重放。确认前后虔诚均为5500，原生报价0，没有追加扣费；游戏日期未推进。

只提交一次checkpoint。真实文件为下述外置根的 `managed-states/review-zh-customize-a03/state/profile/save games/xar_checkpoint.ck3`，68,692,246 B，SHA-256 `8730992ef5a7e39ea5339d5a41069d7ed43342339c9203a93b185d83ed3c4f46`。Java只读inspect-save原wait0，decoder原wait0；解析前后SHA、原生FileID与FILETIME均相同，句柄已释放，没有另导出一份69 MB副本。

完整AST确认上述五项文本、图标及颜色，`texticon=dri_christianity_cathar`、`piety_icon_group=christian`。Rite155只有data块的九个metadata键变化（颜色位于匿名块）；完整tenets状态块、三核心和31项教义与R0016-created相同。来源152、153、第三来源154、Faith13、Religion8的FULL_RECORD AST及canonical SHA均相同；三类完整ID库存分别为156、106、49，没有新增或删除。角色31254新增 `rrf_native_apply_requested` flag，原cooldown/setup flag保留；六项军事缓存数值变化已逐项记录，没有将整个角色记录签为相同。

typed `current_rite_poststate`独立确认五项文本、三核心及31项教义；它的现有schema没有icon/RGB字段，视觉精确值来自保存AST。SDK保存持久化仍为 `unconfirmed / save_binding_mismatch`，没有one-life episode身份，不能由原生文件或AST追认ordinary SaveProof。

定制内容保存不等于产品生命周期已完成：本保存没有 `rrf_native_configuration_complete`，角色仍保留setup/apply_requested及费用豁免。原版 `on_rite_updated` 是延迟钩子，本场始终暂停；不能据此断言钩子漏接。封臣邀请要求complete标记，当前不可准入。下一场先在零日保存冷载比较，随后另立自然日阶段观察原版回调、最终内容守卫、complete、豁免移除及预览状态；不直接补标记或重放Edit。

## 真实失败与后继修复范围

本场draft查询在原生选中槽数100、现有上限64处拒绝；没有执行typed礼仪writer。槽容量不能解释为100项有效信条，后继须复用原生default-slot sentinel合同并保留物理槽号及原writer向量。默认创建描述中的U+0015游戏格式字符与现有严格文本读取器不兼容；纯文本定制后的current读取成功，这不等于已经修复格式描述读取。整窗控件查询仍因2048上限截断，保留实际失败后使用原版UI。完整美德/罪恶catalogue尚未读回。

关闭时Root过早开始手工typed prepare，与原截止前1200秒触发的原CaseClient关闭路径相交。原CaseClient的新query使手工continue签名失效；原生明确 `fresh_backend_query_signature_mismatch`、未dispatch，SDK once claim已消费，没有重试。自动关闭队列失败原件保留，转为原manual-quit请求。Root直接查看当前原版菜单、取消退出自动保存并只点击一次“退出到桌面”，用原始unchecked截图、canonical坐标映射和点击后截图提交真实manual review。不能把这段失败写成typed自动关闭通过。

2026-10-26T08:05:34Z原生确认进程退出0，原保留OS句柄同样退出0；原CaseClient完成finish_hold，宿主08:05:50Z结束、cleanup_ok=true，`normal_close_qualified=true`。public run和Root外层原wait均2，原因是业务incomplete，原失败未改写。keeper、allocator原wait均0，所有原子进程wait已消费。08:08:19Z实际显示恢复1024×768；08:09:23Z按最终keeper序号14050完成SCREEN CAS14051释放，随后才解除来源冻结。

## 原件与验收边界

外置根 `C:/workspace/rrf-development-20261024/review-fixes-a01/customize-R0016-a02`：

| 原件 | 字节 / SHA-256 |
| --- | --- |
| `metadata/save-oracle-R0020-customized-a01/report.json` | 483257 / `6ae0205d72a23507716a5ce9ef942c9f1869ab45a675c4137e046c322d8f1d9d` |
| 同目录 `COMPARISON.customized.actual.json` | 11921 / `2a138e8d0c6097e7e8c6150256409a879df1cf7953942a16c6815830244d9050` |
| 同目录 `original-wait.actual.json` | 3082 / `7841e0a2d89351816b5e2806f74d01e2a667f6501602377f223f41c906dc0eee` |
| `live/<run-id>/native-report.json` | 6944018 / `7b402c523d72e99ab0680c345a163bde58484608fbe930c205bf8987eb872e09` |
| `live/<run-id>/case-output/normal-close-result.json` | 10833 / `82ff454f272b527b19d825dd258ae1253b46e532e1579ebce55c08da6fd1167c` |
| `root-execution-a23/SCREEN-RELEASE.actual.json` | 1345 / `b2fff519fca406ca6771fd787da2676d11b48a19f2445b4266fc77b5107c1d52` |

`screenshots/R0020/03-names-entered.png`、`06-icon-selected.png`、`09-color-done.png`、`10-edit-confirmation.png`及13/14退出截图保留原始内容与映射回执。实际存储补充CAS193→194→195只前瞻调整Root捕获通道，不改冻结grant/runtime；总944 MiB与原期限不变。闭场CAS195→196确认所有通道通过并关闭场次future。按统一策略精确回收3760个可重建cache及一份与checkpoint完全相同的autosave，共225370928分配字节；CAS196→197→198只将实际确认量加入gross退休账，不重置高水。checkpoint及必要来源保留，原退休路径已不可读，不制造同名替代。详细闭场/退休票在先前scene的 `metadata/review-resume-a01/STORAGE.R0020-CLOSED.actual.json` 与 `reclamation-R0020-a01/ACTUAL.actual.json`。

本场证明同ID定制、零追加扣费及真实保存，**尚未证明定制后的独立冷载**。八项整体仍未完成：完整美德/罪恶、亲属/封臣实际改信、可选DES宗族分支及维护后态、超过三核心、无MTS三核心、另一信仰融合模式和最终UI边界仍须实机。下一冷载须新准入、新进程、新状态和新鲜后台Steam离线凭据；保持原九项cold断言，另外显式核对本表metadata、FULL_RECORD及完整库存。InspectOnly的assessment仍是not_assessed，不能借它给metadata自动授予PASS。必要基线和失败原件用途复核为2026-11-01，不由本文无限期续存。
