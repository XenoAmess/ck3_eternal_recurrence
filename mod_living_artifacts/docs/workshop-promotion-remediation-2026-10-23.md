# 2026-10-23 宣传文案与图片整改

`machine_id: pc-20260924rtuf-f11af23c08`，观察时间均为 UTC。

用户指出首传两图带有测试夹具，文案没有充分解释玩法、收益与代价，要求重写、替换素材、在正文嵌图并将 BBCode 入库。Root 接受该问题：R8 的管理说明与六级物品截图属于验收素材，不作为合格的玩家宣传图。旧原件、原上传回执与错误来源保留；不会通过裁掉测试名或改名追认为正常游玩素材。

当前已完成全文重写的是 [正式 BBCode](../../workshop/living_artifacts_description.bbcode)。文案按“觉醒→成长与真实消耗→收益实例→八种重诅咒→停手选择→上手和兼容”组织。四个数值实例来自生产实现，明确触发条件、概率、冷却、金币、压力和控制力代价。战斗等事件不再笼统称为升级经验，镇压不再描述成保留全部收益且无额外代价。

一次独立只读事实审阅覆盖 core/content 生产器、生成脚本与原版回调。Root 已收紧同件联动、县持有人、参与宴会角色、计谋秘密范围、镇压计数清零及安抚计算顺序。关键来源为 [经验与价格](../common/script_values/xalw_values.txt)、[训练与镇压](../common/scripted_effects/xalw_core_03.txt)、[真实喂养结算](../common/scripted_effects/xalw_core_02.txt)、[内容生产器](../tools/living_artifacts_content.py)。这些是源码事实，不额外授予各独有生命周期的实机验收。

图片整改尚未完成。新取材使用独立普通正式 profile，正常选角和游戏规则，保留原物名称、角色、日期、实际效果与来源绑定；不挂业务 fixture，不使用控制台、造物、赋予金币或指定觉醒结果。计划优先选择：

- 合法取得的同一件 ★ 宝物详情，能读清等级、经验、食性与实际异能和代价。
- 同一物品在真实喂养或自然成长前后的状态对比，不用不同物品拼出成长。
- 实际材料与喂养报价；确认窗的图注只说明报价和选择，不冒充已经吞噬或升级。
- 实际管理、镇压报价与期限，说明继续佩戴的选择成本。

没有自然发生的能力、结果或 ★ 物品，就不制造对应画面。精选图、导航原屏与映射前后图均计入新预算；旧菜单卡不授予 campaign。最终只将合格图上传到同一真实物品，并在 BBCode 对应机制段落嵌入实际公开图片链接；不得嵌入仍不合格的旧两图。当前未取得新图，未写假链接或声称媒体替换完成。

已发生的发布事实：首次 Create 与内容 Submit 在 12:42:22Z 成功，真实物品 ID `3825237804`，正式 tag `living-artifacts-v0.1.0` 固定 `052cfb6d8d734014b0101f1e085c7542901eda69`。原两图媒体 Update、订阅、下载均实际退出 0；SDK 缓存为 57 文件/2071121 B。证据在 `D:/workspace/ck3-living-artifacts-20261022/release/living-artifacts-0.1.0-create-final01/`，原两图不能因 SDK 成功而取得宣传质量认可。

Steam 主窗模式切换后产生旧黑窗；Root 经官方托盘“库”重新取得实际主窗，执行官方离线菜单，12:59:38.830760Z 后台原生回执确认 offline/true。13:01:26Z 实际 `ck3.exe` 为 101040248 B、SHA `98702f88a547cde2eaf29a85f93b85f68ee4cf8148336a4f7afaeb75319dd518`。publisher keeper 原工具 7123 实际 0，CAS911 释放。该时点无游戏进程，缓存加载、新图、正文图片及公开 Notes 全文回读均尚未完成；后继匿名回读结果见下。

2026-10-23 的后继匿名公开核验，`machine_id: pc-20260924rtuf-f11af23c08`：原 Popen `13328` 从 `13:46:46.176464Z` 至 `13:46:56.361925Z`，实际 `wait=0`。实际命令与退出见 [command.json](D:/workspace/ck3-living-artifacts-20261022/environment/promo-description-public-readback-a01/command.json)、[exit.json](D:/workspace/ck3-living-artifacts-20261022/environment/promo-description-public-readback-a01/exit.json)。本次仅三次匿名 HTTP 查询，公开 API、更新记录页和物品页均返回 200；没有 SDK、Steam、Game、GUI 或再次提交操作。

公开 API 的同一物品 `3825237804` 描述原始 UTF-8 全文与整改冻结稿逐字匹配：`6604 B`、SHA-256 `95172660fa826ac65bda0b4024ee07a585c465531b61b17221adc295e291843e`。公开页面唯一描述区在去除 BBCode 格式与空白后全文匹配。owner 为 `76561198273714027`，creator app 与 consumer app 均为 `1158310`，visibility 为公开值 `0`；tags 精确为 `Artifacts`、`Events`、`Gameplay`、`1.20 'Crozier'`。原 HTTP body 与排除 Cookie 的响应 headers 均完整保存、未截断，详情见 [summary.json](D:/workspace/ck3-living-artifacts-20261022/environment/promo-description-public-readback-a01/summary.json)。

既有共享 verifier CLI 实际返回 `0`；匿名更新记录页唯一匹配 entry `1792759339`，原版 Notes 经 HTML 解码与换行归一后为 `877 字符 / 23 行`，全文 SHA-256 `852c7ad9817260c8316105024aad00298522cbe70d9f0930f3a1d3277d28dfe0`。本次显式消费正式 `create-final01/change-note.frozen.txt`，没有借旧 `create-a01` 的 674 字符版本通过，也没有重发 Notes。原命令及结果见 [shared-cli-argv.json](D:/workspace/ck3-living-artifacts-20261022/environment/promo-description-public-readback-a01/shared-cli-argv.json)、[verification.json](D:/workspace/ck3-living-artifacts-20261022/environment/promo-description-public-readback-a01/shared-cli/verification.json)。

该独立回读包为 `19 文件 / 223683 B`，无临时文件、future-write `0`；[原件 Pins](D:/workspace/ck3-living-artifacts-20261022/environment/promo-description-public-readback-a01/terminal-pins.json)绑定各份原 HTTP、命令、退出和摘要。存储独立复核数量、字节和 Pins 后，[task-close](D:/workspace/ck3-living-artifacts-20261022/environment/storage-promo-description-public-readback-a01/task-close/20261023T135055548805Z-task-close.json)实际退出 `0`；只关闭该子包，不释放父 other128。

旧两图移除后的空条带见 [SDK 原回读](D:/workspace/ck3-living-artifacts-20261022/release/living-artifacts-promotion-remediation-a01/previews-after-removal-01-call.json)。空条带只说明不合格旧素材已撤除：**普通游玩新图、正式图片上传及正文 `[img]` 嵌入仍未完成**，不能据本次描述与 Notes 回读通过宣称全部宣传整改完成。
