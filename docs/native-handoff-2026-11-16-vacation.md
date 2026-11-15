# Native 休假交接（2026-11-16）

先读[总交接](handover/2026-11-16-java-g2-resume91-vacation-handoff.md)及[源码/证据索引](handover/2026-11-16-java-g2-resume91-vacation-handoff-source-index.json)。最新用户要求休假并编写docs供同事接手；当前没有在途Native编测BEGIN。本文只收束已有事实，未启动JVM、测试、HTTP、Game/Native查询、采样、部署或恢复。

## 已完成的软件资格

| 范围 | 实际首编/复用 | 测试与边界 |
| --- | --- | --- |
| E18实际 canonical fresh batch3 | 3TU/21class（Journal3、Pending7、Life11），209462B；first exit0，受管POST/close完成；schema全21、532 member refs、0gap | owner74新3P，加独立旧direct4P；`cbt74j1` / `cbo74j1` 原XML均保留。实际采用已发生，但取消失败，0新日/SAVE/LOOP |
| 正式 `04a22642` batch | 仅正式Life首编1TU/11class，95607B；现成原字节application10class隔离复用，未重编 | 最终1138 member refs、0gap；`fcb95j1` 独立whole7P/0F/0E/0skip，`2026-11-15T16:27:21.714734Z`结束，托管CLOSE已持有 |
| 正式 `21cc26dd` 10prod+Test1 | 首8TU/96class、现成20class原样复用；6148 refs、0gap | 首whole12为8P4E（jna.tmpdir遗漏）；同4在60s又超时124，成熟120/150s后4P。12个不同方法通过，不称单次whole12绿 |
| Hpp payload/proof分离 | 2TU Ledger19391B与Store65879B，首25class | 新3P/旧12P=15P；未实际采用，不能外推新增类/loader可用或端到端提速 |

actual3的软件闭档：`SOFTWARE-CLOSED-CANONICAL-FRESH-BATCH3-21-NEW3-OLD4-01.json`，11780B / `c67092b47efc53c20f345db276acc955e2736cf94bbaaca7dd82ffd6774f0630`。
正式成员证明：`FORMAL-CANONICAL-LIFE11-REUSE10-TEST7-FULL-MEMBERS-RO01.json`，421431B / `f2798345a5f41666910d0ae0dde8ea5cebe15318504f1cad0954d6ed4da373c9`。
原件绝对路径和其他全SHA见索引；不再编一次已绿组件。

## 现场资格与诊断界限

E18实际采用的Life为50010B / `6e182d3edb9d0b11726ac575e6c12b4acf44b45d4b0468eb4f15571855ffecbd`；正式Life为46122B / `d482f4e24525993078610a8554800bc29aabc4cc5388b345e1528707f41fea11`。实际Core也不同于正式Core。禁止整树覆盖、仅凭formal绿认领实际binary/loader、把新的依赖类型视为既有HCR资格。

最后E18委托START→END3673.2212536秒、0新增日/保存/LOOP；head2001父UNKNOWN。原ARM80已于1996独立确认，新的取消2000在写入前终态拒绝，`BEFORE_WRITE / 0bytes / noACK`；它没有取消sentinel。下一源码必须保留这个真终态。

E17唯一Thread.print证明callback经 `withObserved → PendingBinding → Journal.historical → Archive/Store → GetFileAttributes`；E18 pair5 callback96.8348696秒/true。E18的另一postreturn诊断已永久SKIP0BEGIN；取消前ACK诊断实际栈在拒绝后的归档分支。三个诊断权限均已消费，不重跑、不授CPU比例或唯一根因。

Game145132、keeper56732只引用E18 BEGIN历史身份；本次未核当前存活。长期Quarkus/Maven/outer/persistent-observer310退出与资源释放NOT_HELD，委托END不能替代。没有为交接发STOP或SAVE。

## 冻结的下一候选

CANCEL P0仅有3叶局部RAM：Journal入口修饰、Derived同head fresh batch、Life earlylink。未typing，未形成完整SourceReady。另6叶仍NOT_IMPLEMENTED：Replay、CancellationProof、Composite、RuntimeFactory、Core与Bootstrap；是否还需Session消费者也未闭。

`VACATION-WIP-FREEZE-20261116-01.json` 为13033B / `9debea6dc4ec4631cca688e14a298f34ef822132c1738a54cd3c87ec8609bf84`，列9个BASE精确SHA和部分virtual pins。现有builder/patch不是可以直接首编的统一修复；休假不运行它。A/B模型两候选0POST/0fund，不能等待不存在的模型实现。

待本次休假后明确续行、源码闭合后，Native只接清楚的最小首编scope与必要受影响/负例测试；沿用现有独占输出和受管close，保存失败原件。验证必须保留旧Guard、历史/derived注册资格、实际身份、source body、原期限和零写证据。不可用外层历史只读scope包住会发布snapshot/SEM的整个callback，亦不可将Hpp、新cache或未闭模型混入当前取消修复。

## 资源尾账

最后已闭业务账：raw976582088B、normal24389632B、cap1719664640B（1640MiB）。这是内部物料账，不是OS内存测量；不含后续docs/Git新增。无新增9TU fund，无待退旧unused。

- formal最新3MiB：kept2229858、unused915870已一次退还。
- actual batch4.5MiB：kept2535076、unused2183516已一次退还。
- 旧formal split12、E17和四批模型同样已闭；Git相对upper仍为guard，不全称新增actual。
- Runtime诊断在normal内记账，不虚构独立96KiB返还。托管测试CLOSE不释放 `D:/r64d` 工作树/HEAD/租约。
- `Z:/ck3_mod_rewrite` 原dirty与冻结D树不动；本次交接只在 `D:/r64v0711` 正常发表docs+AGENTS。不为清理资源新增OS查询、kill或删除。

恢复仍由Runtime唯一owner先核当前真实frontier并建立新的有限合同。E18 wrapper已消费、绑定head1995，不能重试。先完成严格零写CANCEL角色、新token/新ordinal3及正ACK/子父独立Status确认，之后才能授普通LOOP和日期推进；软件通过不替代这些实际回执。
