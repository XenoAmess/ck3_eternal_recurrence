# 本机 CK3 Workshop 本地载荷清理

`machine_id: 4-8e1c2f1861`；实际日期2026-10-25。用户在本次宗教礼仪融合发布任务中明确授权：“你看下steam创意工坊订阅下载的ck3 mod 在这台机器上的 都可以删掉。”此前仅获准清本次自动产生的partial；本条是新增的本机已下载载荷授权。

根据当前 `libraryfolders.vdf` 和 `appworkshop_1158310.acf`，确认实际Steam库为 `C:/Program Files (x86)/Steam`。以该库CK3 app1158310的91个本地item目录固定清单；游戏本体、仓库源码、存档及其他游戏的Workshop未纳入。用户永久保留索引已读取，本机本次清单无命中。Steam后台原生探针确认离线，无CK3进程。

实际删除 **86,120个载荷文件**，87批（每批最多1000），全部成功、0拒绝。执行采用原生文件ID、大小、FILETIME与share0独占同句柄核对；不沿目录名扩大范围，不跟随reparse越界。保留旧hidden控制文件、0B占位和ACL备份，以及未来新产品ID3826756673。目录中的旧控制文件不作为模组载荷计数。

Native实际释放 **38,318,603,536B**；卷free从 `88,543,404,032B` 变为 `126,872,616,960B`。卷空闲增量还包含并发系统变化，不用该增量替代逐文件Native合计。每批前后ACF内容SHA相同，订阅保持，未执行unsubscribe。被删原本地载荷现在不可读，不制造同名证据或把旧缓存通过追认为本次仍可读取。

外置原件根：`C:/workspace/rrf-development-20261024/workshop-local-payload-cleanup-a01/`。

| 证据 | bytes | SHA-256 |
| --- | ---: | --- |
| `PLAN.actual.json` | 46,811 | `9743b4cad3904240ed53e9724c22dbd44e4dca6084469736ca7f10fbc245d739` |
| `ACTUAL.actual.json` | 22,681 | `275ccd84ef24113a84d23fdca1d05f99612c33f3a7195905adc3765273da980a` |

清理后统一账本revision123发出本次顺序发布预算128MiB，包含来源CI32、Java32、SDK/媒体16、元数据/闭场48MiB；物理容量通过。原RRF quota和gross不因回收其他Workshop载荷而获得退款。来源及Java验证分别消费其明确额度；菜单224MiB仍是后继候选，待出版阶段写入结束后另行fresh准入。

本次实际准入：`live-admission/ADMISSION.publication-128MiB-a04.actual.json`，6,854B，SHA `d23a5e02da4b419f3fbda463b34ddc302fa34dc08c183c19737e68dad53cbb26`。清理后freshfree `126,868,594,688B`，保持原系统、安全和其他任务上界，物理余量 `37,975,740,826B`。

后续将只下载发布条目3826756673做正式缓存验收；订阅后台下载在临时联网期间单独观察和控制，任务结束恢复Steam离线。保留本次小回执按record180天复核，大型逐文件删除清单30天后按统一策略归纳；本记录不延长原R8/R10保护期限。
