# Steam Workshop Compatible Version 自动维护

本项目从 CK3 1.20 开始自动维护工坊的 Compatible Version。该分类对应普通 Steam item tag；当前精确值为 `1.20 'Crozier'`。它是发布版本的兼容声明，实机覆盖范围仍以各产品验收和永久 changelog 为准。

## 机制与单一版本来源

[Steam Workshop Item Tags 官方文档](https://partner.steamgames.com/doc/features/workshop/tags)说明，提交的普通 tags 可按游戏配置归入可见分类，分类中的名称必须与实际 tag 精确匹配。[SetItemTags](https://partner.steamgames.com/doc/api/ISteamUGC#SetItemTags)负责设置完整 item tag 列表，随后通过 SubmitItemUpdate 提交。

CK3 的[示例物品 3182367229](https://steamcommunity.com/sharedfiles/filedetails/?id=3182367229)右栏显示 `Compatible Version: 1.20 'Crozier'`；其值链接使用[普通 requiredtags 分类筛选](https://steamcommunity.com/workshop/browse/?appid=1158310&browsesort=toprated&requiredtags%5B%5D=1.20+%27Crozier%27&section=readytouseitems)。这是字段机制的证据，不用于推断本项目其他物品已回补成功。2026-10-06 的来源核验、历史 HTTP429/SSL 失败和未写入边界保存在[原始审查](C:/workspace/ck3-upgrade-20261005/steam-compatible-version-primary-audit-agent-01/review-01.json)，6782 bytes，SHA-256 `a34dfbd8f43e2dc2be779e423a757b38fda6ce33d4e3c8a861c5894961cb6c7c`。

兼容值唯一来源是当次正式发布 descriptor.mod 的 `supported_version`，先提取 major.minor，再查[唯一 registry](../ck3_workshop_mcp/src/ck3_workshop_mcp/compatibility_tags.py)的 `CK3_WORKSHOP_VERSION_TAGS`。`1.20.0.3`、`1.20.*` 和 `1.20` 都映射到当前值。不得从 mod 自身版本号、描述、旧构建常量、源码候选或页面更新时间猜兼容版本。

CK3 1.20 以前返回 None，并原样保留标签；公开 1.19 产品不能因为新源码声明 1.20 就提前回补。1.20 及以后遇到未知 minor，或 supported_version 缺失、重复、格式错误时，构建／发布先拒绝。升级到未来 minor 时，先核实其实际 CK3 分类值，再只在上述 registry 增加一次映射；各构建器和原生发布随后自动取新值，不在产品脚本中另建映射。

## 产品清单与正式构建

[workshop/products.json](../workshop/products.json)登记本仓库全部 14 个玩家产品的目录、维护目标 ID、禁止上传的上游 ID、正式构建入口与参数；不固化当前公开版本。无 ID 的开发产品不能猜测目标，维护版只能更新自己的 canonical ID。上传前检查实际 owner、consumer/creator app `1158310` 和物品身份；预期项目 owner 为 `76561198273714027`。

[薄 descriptor renderer](../tools/workshop_compatibility_tags.py)调用同一 registry，仅渲染 descriptor 的兼容标签；它不改变业务文件，不证明实机通过，也不发布。原生发布从实际正式 staging 的 descriptor 再派生标签。已接入路径为：

| 产品 | builder |
| --- | --- |
| 琉焰卿原版 | tools/build_release.py |
| 白绮独立版 | tools/build_vivhite_release.py |
| 肃清曼荼罗 | tools/build_remove_mandala_release.py |
| 体验优化 | tools/build_xenoamess_quality_of_life_release.py |
| 重整河山 | tools/build_reclaim_the_motherland_release.py |
| 驱策朝贡国 | tools/build_tributary_expansion_directives_release.py |
| 天朝经商贪腐 | tools/build_celestial_commerce_corruption_release.py |
| 自动升级建筑 | tools/build_auto_upgrade_buildings_release.py |
| 牛来 | tools/build_ox_here_release.py |
| 天朝特色361制 | tools/build_mod_zhongguo_style_release.py |
| 礼与道开发版 | mod_li_yu_dao/tools/build_release.py |
| 法理征服维护版 | mod_de_jure_conquest/tools/build_release.py → tools/independent_mod_release.py |
| 地产转换维护版 | mod_change_holding_types/tools/build_release.py → tools/independent_mod_release.py |
| 超人强 | mod_superman_qiang/tools/build_release.py → tools/independent_mod_release.py |

完整正式发布沿用各产品的 tag、staging、实机、上传、完整 Change Notes、公开回读、fresh-cache、上传后无 ID 重建和永久 changelog 的 master 交付门禁。发布前冻结正式 descriptor bytes/SHA、supported_version、registry 值及完整预期 tags。只替换已识别的版本 tags，其他 tag 的原字符串和顺序必须保留；例如实际 `"Balance "` 末尾空格不能 strip、改为 `"Balance"`、排序或去重。提交完整列表，不可只提交版本 tag 而覆盖其他分类。

此前实际检查见[外置交接](C:/workspace/ck3-upgrade-20261005/compatibility-renderer-actual-01/handoff-01.json)：14 个 builder 双构建、7 个调整的静态 validator、14 个真实未来 minor 渲染路径均通过；测试副本中共 1413 个非 descriptor 文件逐字节相同。未来版本标签只注入测试进程，没有加入正式 registry。这些是构建／元数据检查，不是新增游戏或公开发布事实。

## 已公开版本的 tags-only 回补

已有实际验收、正式发布证据的版本可只补兼容 tags。允许从该公开 release 的固定 commit 提取其原始 published descriptor，保存到新的外置 `metadata-anchor/descriptor.mod`，绑定产品、commit、提取来源和 bytes/SHA；不重新解释为当前源码，不重新渲染或上传其 content。anchor 只是本次版本派生的只读输入，不是正式发行包。

使用原生已有物品 update 的显式 `tags_only=true` 路径：

1. 读取并冻结目标物品的实际完整 tags，以及 app/owner/item 与已公开 release 身份；保留非版本 tag 原值和顺序。
2. 从固定公开 descriptor 派生版本 tag，冻结完整待提交列表及 anchor 身份。
3. `StartItemUpdate(app, item)` → `SetItemTags(full_expected_tags)` → `SubmitItemUpdate(handle, NULL)`。不调用 content、title、description、visibility、preview 或 additional preview setter。
4. 保存实际 SDK 回执，随后匿名读取该物品完整 tags 和 details 右栏，核对精确列表、Compatible Version 值及 requiredtags 链接，确认旧版本标签被正确替换；保存 URL、UTC、原始 HTTP bytes/SHA 和解析结果。
5. 追加永久 metadata 修订记录并提交、推送 master，绑定原公开 release、anchor、前后完整 tags、SDK 与公开回读证据及实际结果；保存 Steam 恢复离线回执。

[SubmitItemUpdate 官方说明](https://partner.steamgames.com/doc/api/ISteamUGC#SubmitItemUpdate)允许 NULL change note。上述仅标签回补不构成新内容 release，不新增 Steam Change Notes，不修改旧发布版本／日期或虚构新的验收；无需为相同业务内容重跑实机或重新下载内容。永久记录保存为 `docs/workshop-metadata-revisions/<product-key>/<date>-compatible-version.md`，包含原公开版本的 changelog 链接和本次范围。API callback／EResult=1 仅为提交结果，完整匿名 tags 与 sidebar 未核对时继续记录 METADATA_PENDING。HTTP失败保留原件，不写成功；若发现业务内容或额外 setter 变化，应停止将该操作作为 tags-only 回补收口。

## 2026-10-06 范围快照

此表仅记录截至本次文档准备时的仓库发布证据，不声明正在进行的 8 项 SDK 标签回补成功。

| 数量 | 发布／源码边界 | 产品 |
| --- | --- | --- |
| 8 | 已有正式公开 1.20 记录，可按已公开 descriptor 准备回补 | 白绮、自动升级建筑、肃清曼荼罗、牛来、琉焰卿原版、法理征服、地产转换、超人强 |
| 4 | 源码 1.20，公开仍为旧 1.19 版本；等待实际维护发布 | 体验优化、重整河山、驱策朝贡国、天朝经商贪腐 |
| 1 | 源码和公开 0.3.0 仍为 1.19.0.6，不预标 1.20 | 天朝特色361制 |
| 1 | 1.20 开发版，没有 Workshop ID | 礼与道 |

前 10 个迁移产品为白绮、自动升级建筑、肃清曼荼罗、牛来、琉焰卿原版、体验优化、重整河山、驱策朝贡国、天朝经商贪腐和361。法理征服、地产转换、超人强、礼与道属于批次外独立产品，也纳入自动标签维护。后续状态以各产品实际发布与 metadata 修订记录为准。

2026-10-06 01:00（上海）完成上述 8 项公开版本的实际 tags-only 回补及匿名核对；原 tags、完整旧 Notes、内容 handle、描述和预览 handle 均已核对。各产品永久修订记录和原始证据 pins 汇集在[本批记录](workshop-metadata-revisions/2026-10-06-compatible-version.json)。Steam 已恢复离线。此项元数据修订不增加 1.20 迁移产品的正式发布数量。

## 发布测试夹具的兼容字段（2026-10-06）

正式构建接入 descriptor 投影后，使用当前 1.20 版本的人工测试描述符也必须提供唯一的 `supported_version` 和 `tags` 块。若用例要比较源码／staging／launcher descriptor 的原始字节，应预置正确的 `1.20 'Crozier'` 标签，使投影保持这些合法夹具的原始字节；不能为迁就旧夹具放宽生产检查。

[CI 37348249239](https://github.com/XenoAmess/ck3_eternal_recurrence/actions/runs/37348249239) 的白绮发布测试执行了 18 个方法，其中 12 个方法在 descriptor 投影入口产生 20 个 error，均因旧人工描述符缺少 `supported_version`。这属于测试夹具 RED；同路径的牛来、体验优化夹具亦缺该字段，独立发布器夹具已有当前版本但缺 `tags` 块。现已只补齐这四处人工描述符，生产 renderer、registry 和真实产品描述符保持原样；白绮的内容改写／混合换行反例继续保留完整合法元数据，使各反例仍只针对其原本要验证的差异。

2026-10-06 01:38:46–01:38:49（上海），仅重跑白绮 12 个失败方法，以及同因影响的牛来 5、体验优化 5、独立发布器 9 个未执行构建方法，合计 31/31 GREEN。白绮此前通过的 6 个方法和其他无关用例未重跑。[外置测试回执](Z:/ck3_mod_rewrite_process_assets/g2-background-round4-20261005/release-fixture-ci-fix/ROOT-DELIVERY.json)记录逐组选择、命令、时间、日志与哈希；本次修复不增加游戏或发布验收事实。
