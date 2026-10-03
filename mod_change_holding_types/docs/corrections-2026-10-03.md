# 2026-10-03 追加勘误

## 目标地产地名

早期 R0002 核验候选的 `gui_observation.selection_and_execution` 和 Markdown 报告将另一个可选地产记录为 Taranto。父任务核对及 R0003 英文原图 `en-city-detail-01.png` 实际显示默认目标 **Trani**，对应中文 **特拉尼**。先前 Taranto 表述为观察记录错误；原报告保留原字节，并以本条追加勘误。实际手动选中、执行和保存重载核验的地产始终为 **Rossano／b_rossano**，相应金币与 holding 状态证据没有更改。

R0003 原图 SHA-256 为 `6fc97697438de22c2394d473480c148900ab54b17ab8fbbabd547d978fa53511`，保存位置与副本见 [R0003 证据索引](live-R0003-reload-2026-10-03/evidence-index.json)。[R0002 原报告](live-R0002-core-2026-10-03/report.json) SHA-256 继续为 `046aa52c68fed91d3f263ae1ed5b727fcd30ebffa696c82ded4fbb90674d7d6a`，没有覆盖或改写历史失败／观察。

## R0003 原始 register 回执被覆盖

父任务报告一次注册重试误写了 R0003 的 `screen-register.json`，现文件是 `ok=false`、`code=CAS_CONFLICT`、`reason=screen claim requires a new task registration` 的错误结果。原始回执此前已直接读取：1256 字节，SHA-256 `cb9f3da41f009dd5de1733350f9a3155d1d6dddcf7f745d08430d74a2eab4f67`；当前文件678字节，SHA-256 `2b1c4cb0b70cde57993cafb8aff2c4154c44370b890c09efa27d1b57ebf9d539`。原 bytes 未另存于本产品保留快照，目前没有恢复，不以任务总线 event 或手写JSON冒充恢复。

当前错误 bytes 已保存为 R0004 外置证据中的 `R0003-register-current-CAS-error.json`，见 [R0004 索引](live-R0004-visual-route-2026-10-03/evidence-index.json)。它证明覆盖后的状态，不是原成功注册证明。R0003 的人物／存档／日志／玩法报告由另存快照绑定，保持原字节；本条没有清除来源回执缺口或改写历史。


## 用户指令更正：仅简体中文实机，其他语言仅格式

依用户最新明确指令，撤销所有九语视觉、英文追加实机、七语／组合冷启动和外语语义／术语／母语审阅计划。当前可执行要求只使用简体中文实机，其他八语只检查格式，见[现行政策](localization-acceptance-policy-2026-10-03.md)。R0003／R0004英文过程和被冻结报告原字节保留，不是中文签核。冻结report里的旧外语pending不是现行发布缺口，也没有被改成PASS。

外置combo／九语helper从未prepare／分配组合或产品artifact ID／admit／launch；保留历史代码与source preflight，并另存NOT_EXECUTED取消记录，后续不执行。此次仅更新本产品文档，没有修改runtime、现有本地化或工具，也没有启动游戏。
