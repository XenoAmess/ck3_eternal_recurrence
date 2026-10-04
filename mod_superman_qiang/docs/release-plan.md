# 《超人强》发布方案

## 当前 1.1.0 更新

2026-10-04实际执行完成：同ID仅一次Submit、EResult1，22文件真实订阅核对、完整新Change Notes条目1791095091、介绍和封面/五媒体均已公开回读，Steam恢复离线、CAS4242释放。源tag `superman-qiang-v1.1.0` 指向 `f7fde816e295a62807ab636ee2d93cf307ea69cf`；GitHub双附件实际下载匹配。见[正式报告](release-1.1.0-20261004/README.md)和[永久changelog](../../docs/release-changelogs/superman-qiang/1.1.0.md)。以下保留执行方案，仓库交付另由报告内的实际master收据记录。

目标为同一 Workshop item **3812991990**，tag `superman-qiang-v1.1.0`，上一公开版本 `superman-qiang-v1.0.0`。新增健康候选和原生通知，代码发生变化，必须完成 [增量验收](test-plan.md) 后再以正式 allowlist staging 更新；不能套用未发布媒体候选的“21文件不变”结论。

冻结一男一女封面、三张准确区分能力±1与健康±0.00075的宣传图、正常游玩的性行为事件与新通知实机图、全文介绍和独立完整 Steam Change Notes。上传后匿名回读目标条目完整正文与精确哈希，实际订阅下载核对22文件，并立即恢复离线。最终报告进入 `docs/release-1.1.0-20261004/`，永久 changelog 为仓库 `docs/release-changelogs/superman-qiang/1.1.0.md`；正式发布事实只在实际成功后记录、提交推送。

以下首发方案保留历史，不授权再次 CreateItem。

## 1.0.0 首发方案

工坊标题：**超人强：越超人越强**。当前是新原创产品，Workshop item ID 在实际 CreateItem 成功后才能记录。目标 tag：`superman-qiang-v1.0.0`。描述、封面、实机 media、完整 Steam Change Notes 是独立发布输入，必须冻结精确字节后提交。

遵循 [验收方案](test-plan.md) 及仓库 [独立模组开发范式](../../docs/ck3-mod-development-paradigm.md)。本文件记录计划，不提前写上传、订阅、公开 Notes 或实机已通过的事实。

## 包内容

发布构建仅包含声明的运行文件和资产。源码、生成器、文档、测试夹具及验收日志均排除。内层 `descriptor.mod` 不带 `remote_file_id`；canonical ID 保存到用户目录外层 `.mod`。构建器应支持原创产品没有 upstream ID，不设置假上游或哨兵身份。

原版效果接入投影由生成器产出，绑定准确的游戏来源与 SHA。正式验收和发布使用同一投影字节。简体中文做语义及实机验收；其余目标语言只认证格式，翻译候选按仓库 MiniMax 工作流生成。

## 发布事实与证据归档

正式报告保存在本产品 `docs/release-1.0.0-<date>/`，至少索引：

- source commit/tag、ZIP/manifest/staging SHA 和可复现构建结果；
- 原生 GREEN run 的完整 ID、游戏 exact build 与实机 evidence；
- Change Notes 冻结全文、归一化规则、字符数/行数/SHA；
- Workshop create/submit 收据、预览及实机 media 源与公开 CDN 回读；
- 匿名 item 详情及完整 changelog entry 精确回读；
- 真实订阅缓存下载和 manifest 核对；
- GitHub release 附件字节校验、外层 descriptor、Steam 离线恢复证据；
- 永久仓库 changelog 的 master commit/push。

历史/失败 attempt 永久保留，不覆盖。正式 tag 指向经审阅的源码；后续发布证据 commit 可以在其后，但不得重新解释或改写被验收 staging 字节。
