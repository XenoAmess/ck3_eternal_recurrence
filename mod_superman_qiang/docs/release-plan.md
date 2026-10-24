# 《超人强》发布方案

## 1.2.0实际公开更新（2026-10-24）

同一Workshop item **3812991990**已完成一次原生更新，2026-10-24T02:48:35.240588Z返回EResult=1；完整Steam Change Notes条目 **1792810119** 匿名回读精确匹配930字符、28行及冻结SHA。标题、完整描述、全部tags和Compatible Version侧栏已公开核对。正式tag `superman-qiang-v1.2.0` 固定于 `bcb9e9f11658519c5277e0d304a02e5028bbd760`，GitHub两附件均经实际下载核验。

真实Steam下载35文件与正式manifest一致。`machine_id: desktop-3fevhd2-1c74096080` 的R0037完成限定菜单缓存加载、原进程OS0/native0、Job终止前与最终均0及cleanup=true；Steam已恢复并保持离线，屏幕CAS8575释放。未进入战役、挂载业务fixture或重跑业务矩阵。R0036在游戏启动前遇到共用factory误配，其失败与后继公共修复记录保留；这些共用工具修复没有改变正式mod运行字节。

本次仍保留C2完整逐分支实机缺口、同性设置未独立验收和重复通知根因未定位，不声称整个产品业务矩阵通过。永久[1.2.0 changelog](../../docs/release-changelogs/superman-qiang/1.2.0.md)及[发布报告](release-1.2.0-20261024/README.md)记录实际发布、验收和仓库交付。以下是上传前计划，按当时状态保留。

## 1.2.0同ID发布前计划（历史输入）

2026-10-24，用户已明确授权发布1.2.0并编写相对上一公开1.1.0的永久changelog。目标仅为现有 Workshop **3812991990** 的更新，不再次CreateItem。计划tag为 `superman-qiang-v1.2.0`；上一公开tag/commit为 `superman-qiang-v1.1.0` / `f7fde816e295a62807ab636ee2d93cf307ea69cf`。正式上传和公开回读尚未发生，当前实际公开版本仍为1.1.0。

1.2.0候选新增每对成年在世正式配偶/侧室每月一次的夫妻生活模拟，扩展已接入的脚本受孕概率尝试并处理同次去重。运行包由正式builder的35文件allowlist构建，不含测试夹具，不需要原生组件或外部后台。[完整规则](product-contract.md)和[来源审计](2026-10-23-script-coverage.json)定义本次范围。

本轮实机机号为 `machine_id: desktop-3fevhd2-1c74096080`，游戏为1.20.0.4/build25734779；实际日期、源commit和SHA见[R0030/R0031月度与冷重载](2026-10-24-monthly-and-cold-native-acceptance.md)。这两场的限定公共run/verify通过，不代表全部新增分支通过。**C2医疗50%成功/失败、强制妊娠、双胎及朝圣疾病辅助入口的完整逐分支实机仍有缺口**，不能由来源审计、离线回归、月度或通知场次替代。旧1.0/1.1验收不外推为这些新增分支通过。

[R0033/R0035通知诊断](2026-10-24-notification-diagnostic.md)的0/5限定死亡feed对照未复现累加；R0035真实经验10/6、计数5，但不是五轮完整勾引。根因未定位，逐类型设置及原生HUD实例仍有读口缺口，负断言保留；本版更新说明不写成“修复重复通知”。

发布输入为仓库 `workshop/superman_qiang_description.bbcode` 与独立完整 `workshop/superman_qiang_change_notes.txt`。后者已冻结930字符、28行，归一化UTF-8 SHA-256为 `939510478A9D23EA35A0D99721360B87FE20C3C8E6E07302DDABDC59083A68CD`；无BOM、LF换行、无末尾换行。冻结来源为 `C:/ck3-superman-notification-20261024/release-1.2.0-player-copy-a01/NOTES.frozen.json`，仅为待提交文本，不是公开回读。描述与Notes明确纯工坊月度模拟、脚本受孕失败也计、同次去重、18+存活及匿名边界、原存档继续而历史不补算。

后续按用户已授权的发布流程冻结最终clean source/tag与35文件staging、ZIP和manifest，提交同ID更新；上传成功后分别记录以下实际结果，不能提前填成已完成：

1. 原生Submit回执、实际完成时间、最终tag与commit，以及正式构建SHA。
2. 匿名工坊标题、全文描述、兼容标签和完整Change Notes条目回读；记录真实entry ID、HTML解码及换行归一化后的全文、字符数、行数和SHA精确匹配。原生EResult=1不能替代此项。
3. Steam真实订阅下载与正式manifest逐文件一致，以及CK3实际加载这份缓存的日志。缓存验收仅核字节和实际挂载，不重跑功能、按钮、计数或整套业务矩阵。
4. 恢复Steam离线、正常关闭与释放现场，上传后重建staging移除内层临时remote_file_id；canonical ID只留用户目录外层.mod。
5. 相对1.1.0的永久 `docs/release-changelogs/superman-qiang/1.2.0.md`，填入实际发布与缓存证据，并实际commit/push master与远端回读。公开上传、缓存核对和永久changelog交付分别登记。

## 1.1.0 更新（历史已完成）

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

历史和失败attempt的真实记录不覆盖；原始资产依[通用存储策略](../../docs/storage-retention-policy.md)按用途、期限及容量复核，必要来源另行限期保护，不默认永久保留全部大文件。正式tag指向经审阅源码；后续发布证据commit可以在其后，但不得重新解释或改写被验收staging字节。
