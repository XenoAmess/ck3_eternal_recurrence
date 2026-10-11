旧 Source08–11 已完成可恢复退役：32 批原命令全部成功，删除 31,624 个非 host 文件，gross 逻辑量 563,263,222 B。141 个差异 blob 已保存在恢复 CAS，共 10,721,390 B；恢复内容与新增账本占用单列，不把 gross 当净 free 变化。全部实际小证据见 [原五文件 INDEX](acceptance/2026-10-11-source08-11-recoverable-retirement/INDEX.actual.json)、[FACTS](acceptance/2026-10-11-source08-11-recoverable-retirement/FACTS.actual.json) 和 [原中文报告](acceptance/2026-10-11-source08-11-recoverable-retirement/REPORT.zh.md)。

四个旧 host 与全部目录保留；O7/O8/O10/O11 metadata、Git objects、Cbr2/Cbr3、当前 Source13–15、全部 cache/SAVE 均保留。已退役旧 payload 的可用性改为 RESTORE_REQUIRED：恢复来源为实际 Source15、保留的原 host 与 141-blob CAS，恢复时仍需按原索引核字节。旧 frozen commit、历史 SHA、原失败记录不改，不能声称旧路径正文仍完整可直接读取。

48 MiB 恢复预约首次实际闭账 command001 exit0；CLOSED 原件14061 B / ef58855e080f176151557f3946622a0bf8a94812b5f824dace4267a8d19ebf56。已知新增保留19,633,289 B，加闭账1 MiB上界后的 carry20,681,865 B，未来预约0。最初 closure 源仅在审阅中被拒、未执行，actual failed command=NULL；本次没有伪造失败回执或重跑 preserve/32批。

canonical [CREDIT-EVENT](acceptance/2026-10-11-source08-11-recoverable-retirement/CREDIT-EVENT.actual.json) 的 owner/deduplication_key 与原实际删除绑定，当前未 claim/consume。四事件 gross 合计1,223,826,185 B 仅供未来013一次实际 claim；本专题不执行 claim、不提前写013成功，也不重复旧五SAVE信用。新恢复CAS/ledger增长由独立closure carry计入下一准入，退还预约不等于物理回收。

原日报/周报/maintenance 截至08:15的仅计划事实保留，新增完成事实按本次实际摘要生成截止2026-10-11T00:35:58.659081+00:00追加。原逐项ledger30日、compact摘要180日复核；原源码/缓存/配额期限不续。此项只完成存储退役，没有新增CK3/native/业务验收，第一期保持75% / NOT_GREEN。

精确 `0abb8220f6571c8f741001a41388438a60e75965` 的 Official run38097973635/job114347761010 与 Linear run38097973507/job114347760491 均 SUCCESS。只引用原外置 `exact-0abb8220-ci-terminal-readonly-20261011-001/REPORT.actual.json`（2905 B / 9c9c067ea5b4511d90c6f0e8db0acb3aea2c54a05d058950bc2ff80ad0419b83）及 INDEX11806 B / 8e8c2c34c36fafc4a6b658f5b7001dca07a0fe3f98ba5159695827a984438aff；没有重新查询或搬运大日志。

08:39 CST（00:39 UTC）实际后补：013原命令exit0，四事件单次claims已真实创建并用于新full2GiB CASE7准入，gross合计1223826185 B；其中Source08–11 gross563263222 B。08:35摘要中的unclaimed状态是当时事实，原五文件保持bytes，当前变化见 [013/CASE7实际补记](acceptance/2026-10-11-i4-case7-admission/FACTS.actual.json)。recovery carry20681865 B另计，usage135209295215 +2GiB=137356778863 B，quota余82174609 B。prepare当时仍在执行，未授allocate/live/业务/正常退出信用；原quota/cache期限不续，第一期75% / NOT_GREEN。
