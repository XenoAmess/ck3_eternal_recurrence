# 跨 mod 的 CK3 错误日志归档与分组

2026-10-02：通用实现为 [triage_ck3_error_log.py](../../tools/triage_ck3_error_log.py)，纯标准库、离线运行。
它将一次日志读取保存为原字节快照，再对全部已识别记录计数、对多行 E 报错分组、按脚本位置排名。
输出没有 GREEN/RED 游戏验收结论，也不推断崩溃或挂起根因。

## 先复用已有 MCP

本次先检查主仓现有 [诊断实现](../../ck3_autonomous_player/src/xar_autoplayer/ck3_runtime_diagnostics.py)、
[MCP 注册](../../ck3_autonomous_player/src/xar_autoplayer/bridge/mcp_server.py) 与
[本地环境观测合同](../ck3-local-environment-observation-mcp.md)，没有修改它们，也没有连接生产 MCP。

| 需要解决的问题 | 已有实现 | 本次落点 |
| --- | --- | --- |
| 正式 live 日志/crash 查询 | `ck3_query_engine_diagnostics_v1`，服务器绑定 profile、固定日志名、64 MiB 上限、E/F/W 计数、前 N 指纹/tail | 继续使用已有 MCP |
| 定向错误全文计数，包括前 N 指纹以外的低频错误 | `ck3_query_engine_log_literals_v1`，精确单行字面量、完整有界扫描、计数与 SHA 来自同一 payload | 继续使用已有 MCP |
| 归档原字节与同字节分析 | 已有 diagnostics 文字、size/hash 分开读取；字面量接口不产出源文件快照 | 新离线 CLI，两次内容相等才保存快照 |
| 通用标题下的具体多行 `Error:` 与 `Script location` | 已有指纹基于单行 header，尾部有界 | 新离线 CLI，不截断分组排名 |
| 按根脚本位置与 caller 排名 | 当前接口无完整排名 | 新离线 CLI，两种角色分开计数 |
| 日志达到声明上限后的覆盖边界 | 现有文档已禁止把零字面量命中外推到封顶之后 | 记录阈值、字面量、最后记录，保持同一边界 |

这是既有 live 能力的离线分析补充，未新增任意路径 MCP，也未迁移独立项目的 live runner。
若以后暴露 typed MCP，应复用此解析函数并继续由服务器固定 profile/日志名；CLI 的显式路径参数不能直接变为 MCP 参数。

## 使用

从已有封闭日志或独立项目保全的日志运行；输出必须指向一个不存在的新 attempt 目录。

```text
tools\.venv\Scripts\python.exe tools\triage_ck3_error_log.py --source _runtime\your-run\logs\error.log --output-dir _runtime\error-triage-a01
```

可选参数 `--declared-error-cap N` 接受来自当次构建/配置证据的正整数；没有默认引擎上限。
可选 `--cap-marker-literal TEXT` 对调用者给出的非空单行字面量做完整逐行精确计数。
它们都不是自动检测引擎封顶的 heuristic，正文中的数字或角色 ID 不会触发任何封顶判定。
没有固定本机账户、游戏路径、mod ID、PID、存档或第三方源码输入。

每次生成四份文件：

| 文件 | 内容 |
| --- | --- |
| `source.log` | 输入的完整原字节，包括 BOM、换行与无效 UTF-8 字节；不重新编码 |
| `triage.json` | 完整分组与排名、原字节大小/SHA、源路径、工具 SHA、记录边界、解析与封顶证据 |
| `groups.csv` | 所有 E 分组的数量、emitter、具体 error、主脚本位置与稳定 group ID |
| `script-locations.csv` | 所有已识别 primary/caller 位置，各自在记录中的出现次数 |

stdout 只给总数及前十组摘要；完整 JSON/CSV 不受前十项限制。CLI 成功返回 `0`，输入变化、超限、
无效参数或既有输出返回 `2`。既有输出拒绝覆盖；写入中断产生的 partial attempt 保留，重跑另建目录。
原日志只读。真实日志可能包含本机路径与玩家信息，应留在对应项目的私有运行证据中；主仓只维护通用实现与合成夹具。

## 分组和位置计数合同

- 识别 `[time][LEVEL][emitter]: message` header，兼容无 emitter 的 `[time][LEVEL] message`。
  `LEVEL` 为单个大写字母；总数涵盖全部已识别级别，`error_record_count` 只计 E。
  F/W 等级计入 `level_record_counts`，本 CLI 的脚本分组仅针对 E；已有 MCP 继续提供 F/W 指纹。
- 每个 header 至下一个 header 前的所有行组成一条记录，包括空行和 caller 链。
  JSON 保存每组第一条完整 decoded 代表记录及所有出现的行范围；全部原记录保存在 `source.log`。
  每组不重复保存十万份相同 body。
- 分组键为 emitter、header message、所有独立 `Error:` 行与主脚本的 file/line/context。
  不仅按 `Script system error!` 归组，也不归一化数字、ID 或路径。
  未识别到 `Error:` 时使用 header message；未识别到主位置时保留空位置。
- 第一个 `Script location: file: ... line: N (context)` 为 primary，其他同格式位置为 caller。
  所有 E 记录的已识别 caller 都参与完整排名，并通过 group ID 关联分组；不只统计代表记录的 caller。
  同一条记录中相同 role/file/line/context 重复出现时只计一次；不同记录分别计数。
- 分组按次数降序，再按 emitter/error/group ID 排序；位置按次数降序，再按 file/line/context 排序。
  同一源路径、源字节、工具字节与参数产生相同输出；输出目录不参与报告内容。

计数表示这些字节中诊断记录的出现次数。一个根因可产生大量记录，一个分组也可能包含多个原因；
数量不能替代语义审查、修复优先级或独立 bug 数。

## 稳定字节、解析和覆盖边界

读取遵循已有独立日志工具的前后内容比较方法：两次有界读取完全相等后才创建输出。
报告计数、SHA 与保存的 `source.log` 均来自该 payload。它没有暂停引擎、原子文件快照或证明日志永远不再增长；
持续增长的输入应先由所属运行任务保全封闭副本，再分析。单日志上限沿用现有诊断接口的 64 MiB。

UTF-8 正常时按 `utf-8-sig` 解析；遇到解码错误时记录首个错误字节区间与原因，用替换字符继续解析，
原字节快照仍完整。报告还保留 preamble 行数、未识别的 header 样式、无主位置的错误数、多 `Error:` 行数和
末行是否换行。当前格式之外的 header、位置或 continuation 不被伪称已解析；原文可按行范围核查。
最后一行未换行只是线索，也可能是正常文件形式，不能直接断言日志截断。

`cap_evidence.error_records_reach_declared_cap` 只比较 E 数量与调用者声明的上限；
`marker_lines` 只证明所给字面量在这些行中出现；`engine_cap_confirmed` 始终为 `null`。
`record_boundaries` 中的 time 是原始日志 header 时间，不是模拟日期。
达到阈值、出现字面量、最后时间与后续缺日志都只能结合当次引擎配置和运行证据解释，
不能自动把某种错误的零命中变成封顶后无错误，也不能把终止时间变成游戏停止日期。

## 来源与验证

需求来自独立 mod 的真实长局排错：通用 header 大量重复、错误详情与 caller 分散在后续行，
前 N header 指纹无法给出全部位置计数；日志达到已有运行所证明的错误上限后，也不能用后续缺日志作通过证据。
本次提炼了该项目 `tools/triage_runtime_errors.py` 的 header/continuation 与前后字节比较方法；
只读参考版本 SHA-256 为 `4b6ac247fc0a1a814a6050e5f45fda0450ebc5eab451b09dcf619cfcc39f9642`。
没有复制 mod 内容、真实日志或存档，旧工具、旧 run 及其原 schema 都保持原样；外部适配另行迁移。

主仓审计基线为 `c53daab2434f001e56d98bdab1be3e87987db48a`。已有 diagnostics/MCP registration 的审计 SHA 分别为
`3fbd9340e59d9bcaad16dea5c460d0c9750398c423cd90cb09afc6f091453b67` 与
`87183b80ef1b426961b8d2db758e8ee60ae7325faeb25cfd217203d7033d330a`；本包没有修改它们。

可重现的小型合成合同在 [test_triage_ck3_error_log.py](../../tools/test_triage_ck3_error_log.py)：

```text
tools\.venv\Scripts\python.exe -X utf8 tools\test_triage_ck3_error_log.py -v
```

2026-10-02，Python 3.14.7：**8/8 PASS**。覆盖多行原文、不同 caller 的全量计数和重复位置去重；
数字/位置/context 的精确区别；E 上限与总记录数的区别；空文件、无效 UTF-8、未知 header 和无换行尾部；
无 emitter 与多 Error 行；变化读取拒绝；CLI 的 BOM/CRLF 原字节、确定性输出、CSV 读回、旧 attempt 拒绝覆盖；参数与大小边界。
一次额外小型 CLI 合成例读回 4 条总记录、3 条 E、2 组、主位置 3 次与两条 caller 2/1 次，全部 9 项聚合检查通过。

本机 append-only 验证入口为 `_runtime/cross-mod-error-triage-20261002-a02/check.py`，结果为同目录的
`summary.json`、stdout/stderr 与 `cli-a01/`；它是忽略的本机证据，不是需要其他机器具备的固定路径。
合成源 SHA 为 `d1204127de19a7acea3f513ead20aa4e732592b3ed2cfa4ff605fa16d11d8d07`。
冻结工具 SHA 为 `1f99a0d0eb62716212d72582a1edd897a50d3125b36e3ca6b318e6382da1dae2`；
测试 SHA 为 `36cdaaaf74af51cac70318337a62761fdee28546d9c5c0941ca13ea881785f69`。

`open_kaishek=not-applicable`：本包解析引擎输出记录，不执行 CK3 script/parser/trigger/effect 或 replay 语义。
游戏实机与生产 MCP 均 **NOT_RUN**，桌面输入为 0。这些检查只证明通用日志合同；不改变任何 mod 的验收状态。
