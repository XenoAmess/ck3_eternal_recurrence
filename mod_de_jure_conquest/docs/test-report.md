# 当前测试报告

日期：2026-10-03。当前结论：**1.0.0 候选源码、16文件正式语言静态与可复现构建通过；实机与发布待完成。**

## 当前结果

| 检查 | 结果 | 证据／边界 |
| --- | --- | --- |
| 上游 bytes | 已冻结 | 8 文件／138655 字节，tree SHA见 `upstream.md` |
| 源码迁移 | 候选完成 | `implementation.md`；不等同引擎实机 |
| 日常 L0 | GREEN | 外置 `de-jure-static-R0003/report.json`，实核9文件，最终allowlist16 |
| 双语严格 parser | PASS | 共享 `parse_ck3_localization` 两语各15 key |
| 正式其他七语 | format-certified | 主执行者生成候选并认证键／占位符；不代表七语界面实机 |
| 正式16文件静态 | GREEN | 最终canonical LF输入的 [R0002永久副本](release-static-2026-10-03-R0002.json)，release_localization=true，完整16文件 |
| 可复现构建 | 16文件PASS | 公共builder双构建manifest／ZIP一致；尚非tag绑定发布包 |
| 外置夹具生成 | parser PASS | `de-jure-fixture-R0002`，9真实CB战争场景／72预期PASS；未执行 |
| Open Kaishek 确定性子集 | NOT_RUN | 本工作包未找到 sibling checkout；完整探测由主执行者协调 |
| CK3／Workshop／缓存／Change Notes | NOT_RUN | 尚无实机GREEN或发布事实 |

所有外置 artifact 位于 `C:/workspace/two-mod-maintenance-20261003/`。`de-jure-static-R0001`、`R0002`、`R0003` 报告与 fixture `R0001`、`R0002` 独立保留；没有覆盖历史 attempt。R0003 `checked_runtime_file_count=9`、`runtime_allowlist_count=16`、`release_localization=false`、`live=NOT_RUN`。

双语最终冻结：EN `719ad53ee0b238afae6ab70691492e2b5e8d3095fbde27263bb080b693d0399a`；CN `214c3afcd66a5c534d9b44b5bc429579d9f3bb75265f765732b4cf4adbb553b2`。历史9文件构建 manifest SHA `72881fb61ee36fb21feeffb8bc9f54312f616152afa51c5f8a667d5e9d9dcb3c`，ZIP SHA `2f84c8ddfd2645b9cbc553703047f980e7ce2795e56274bf72f1721b9a388059`；后续格式变化已使这些hash不适用最终包。

历史16文件双构建：manifest SHA `a3e43482f2bacc0633204c41d242c0d3dbbdb870c746eb3fd2fc56f24e8506df`；ZIP SHA `c4869ed4653cc2d4389f880cd7f804776d2db02ac69cc3dea60fdd5f08aac756`。实际命令使用已验证实体Python执行 `mod_de_jure_conquest/tools/validate_static.py --release-localization --report C:/workspace/two-mod-maintenance-20261003/de-jure-static-R0004/report.json` 与 `mod_de_jure_conquest/tools/build_release.py --check`；返回码均0。之后七语canonical LF输入字节已变化，本段保留当时identity，不能再作为最终上传包身份。

## 最终canonical LF静态报告永久保存

主执行者提供 `C:/workspace/two-mod-maintenance-20261003/mod_de_jure_conquest-release-static-R0002.json`，现以精确bytes另存为 [release-static-2026-10-03-R0002.json](release-static-2026-10-03-R0002.json)。源文件与仓库副本SHA-256均为 `54cbd92efdb19c4918f5ce28348539ec1618b847ccf6ee12863c0572924d4738`，结果GREEN、16文件、正式九语，`live=NOT_RUN`。旧R0001／R0004等报告未改写。

这里canonical LF指最终运行文件输入；报告JSON本身保留来源CRLF字节，没有重新序列化。只读比较确认当前16个runtime hash全部与该报告一致，未执行新的static／build／live。发布文本与源码一致性复核、完整草稿字符数／行数／SHA及精确文件记录见 [复核说明](release-documentation-review-2026-10-03.md) 与 [机器回执](release-documentation-review-2026-10-03.json)。

两个翻译输入失败由主执行者保留：上游 yml 的仅空白行和EN行尾空格不满足共享 parser。逐行规范化后直接以同一生产 parser 验证15 key，不更改公共parser。该失败属于输入格式，不是CK3产品RED。

完整原版 `00_landed_titles.txt` 的匿名嵌套数组不在建筑用途parser覆盖范围，本次未声称其整体parse成功。随后用已有具名block extractor读取 d_capua、k_sicily、e_italy：d_capua含capua／napoli；k_sicily含玩家apulia；e_italy含roma／firenze；vannes都在目标外。

夹具Actor为1066罗贝尔 `history_id=1128`，不是诺曼底角色。经原版 `start_war`／`end_war` 调用生产CB与hook，读取资格、参战者、目标、持有人和战争退出；没有直接调用生产胜利helper冒充结算。脚本开战不证明宣战UI扣款，强制end_war不证明原生议和合法性，矩阵也未覆盖并发战争／自动军队／保存重载／低威望边界；按 [test-plan.md](test-plan.md) 后续追加。

## 来源取得前的历史记录

下表保留首次页面阶段状态，已经由上方当前结果覆盖，不是现在的结论。

| 检查 | 结果 | 证据／边界 |
| --- | --- | --- |
| 自动升级建筑处理方式研究 | 已读取 | 根 docs 的维护、上游、测试计划与构建／静态代码；仅研究，不复跑旧产品 |
| 上游公开页面 | 已读取 | 名称、作者、三档公开功能与评论；见功能分析 |
| 本机 CK3 rawVersion | 已读取 | `launcher/launcher-settings.json`：1.20.0.3 |
| EXE／原版 CB schema hash | 已读取 | 见 `upstream.md`；这是文件冻结，不是实机 |
| 原版宗教／法理战争结构 parser | PASS（原版输入） | 复用 `extract_auto_upgrade_buildings.parse_clausewitz`；不证明本产品源码或战争语义 |
| 原始 mod bytes | WAITING | 主执行者取得来源；尚无代码分析或 import |
| 授权来源文件 | NOT_VERIFIED | 尚未读取许可证／作者许可记录 |
| 产品 parser／L0 | NOT_RUN | 尚无运行源码 |
| 可复现 staging／ZIP | NOT_RUN | 尚无产品 allowlist |
| CK3 加载／功能矩阵 | NOT_RUN | 未启动游戏；没有最新 build GREEN |
| 新 Workshop item／缓存回读 | NOT_RUN | 尚未创建物品 |
| Steam Change Notes／永久 changelog | NOT_RUN | 尚无发布事实 |

## 实际执行记录

使用 `C:/Users/Administrator/AppData/Local/Programs/Python/Python313/python.exe` 执行外置 `C:/workspace/two-mod-maintenance-20261003/de_jure_inspect.py`，读取原版 EXE hash、CB schema 和 launcher version。首轮因误寻根目录 `launcher-settings.json` 产生 FileNotFoundError，随后改为读取实际 `launcher/launcher-settings.json`，成功。该失败是只读检查脚本路径错误，未加载产品，也不是产品 RED。

本工作包已登记 task bus `de-jure-conquest-20261003`，资源 `mod_de_jure_conquest`；没有领取屏幕资源、修改 Steam 状态或启动 CK3。

另执行外置 `de_jure_vanilla_research.py`，用仓库已有 Clausewitz parser 解析两份原版 CB 文件，读取顶层字段和选定结算块，结果通过。当前 `C:/workspace/open_kaishek` 不存在；尚未进行完整工具探测，因此不把这次路径检查写成 Open Kaishek 产品／语义 RED。

新增任何通过事实时追加精确 attempt 与 hash，不能用此报告把计划变成完成。自动升级建筑的旧版本验收不得外推到本产品或 CK3 1.20.0.3。
