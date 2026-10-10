# 历史代码与采集数据清理：2026-10-10

按用户要求开子线程执行，适用 [通用存储策略](../storage-retention-policy.md) 1.0.0。代码与磁盘两个 lane 分开处理，均不启动游戏、不重跑产品业务矩阵、不清空在用输入或改写 Git 历史。

## 代码结果

第一批已随 `7a54d89a8950ca0cc2f5edd26c78c6c71d36885a` rebase 普通推送：五个旧验收入口删除 277 行不可达 main 尾部。第二批在同一 clean parent 上删除主模组、终态、白绮三个旧入口的 560 行不可达尾部，并同步更新仍检查死代码的静态断言。合计 **8 个入口、837 行死代码**；全部底层 helpers、API、CLI 参数及真实 preflight 保留，受管实机仍由统一 `tools/ck3_mod_acceptance.py` 进入。

第一批现有 12 项 focused checks PASS；第二批现有 9 项 tests PASS（2.742s），变动 runner 静态断言块 PASS，5 个变动 Python 文件可 compile。候选 AST 对照确认 main 保留前缀及所有其他节点等同，Root 应用前后均核 pins。第二批先前失效日志断言和打包尺寸估计失败已如实保留；最终 gzip 仅在内存精确解压用于 `git apply`，没有额外完整源码副本。

详细边界及候选路径见 [旧入口清理记录](retired-mod-acceptance-entry-tails-2026-10-10.md)。源码删除量不作为磁盘释放量；本批没有 native 编译或 Source18 冻结。`7a54d89a` 的 [官方 CI](https://github.com/XenoAmess/ck3_eternal_recurrence/actions/runs/38061774137) 于 15:10:31Z 实际完成，66 success / 20 skipped / 0 failure；不外推到第二批后继提交或实机业务。

## 数据实际回收

| 精确对象 | 实际删除文件数 | 删除前实际 AllocationSize | 当前用途判断 |
| --- | ---: | ---: | --- |
| 49 份已关闭历史 native-report | 49 | 472473600 B | 后续验收已替代，13 份当前 metadata 无直接消费；原结论、薄证据和必要失败知识保留 |
| R61/R62/R64/R65 的完整报告及四类采集 JSONL | 20 | 349114368 B | R69 替代 R61 两相；后继启动成功替代 R62/R64 旧误拒；R68 level3 替代 R65 level0 |
| 合计 | **69** | **821587968 B** | **约 784 MiB，失败 0** |

两批均先核原关闭回执、当前 owner 用途解除、无 active claim/writer、精确路径和 HANDLE identity；没有全盘正文 hash 或递归删除。保留原 GREEN/RED，不制造同名替代文件。上述已删除完整报告/采集 **不可全文重放**；历史路径只是历史引用，availability ledger 明确标注退休，不把后继摘要冒充原字节。当前 R59/R63/R67/R68/R69、R60 已得正式 credit、R31/R33 直接输入以及所有本轮 prepared/source/native 父依赖未纳入清理。

actual 回执根 `C:/workspace/disk-cleanup-20261010/resume-05/`：

- `retired-native-reports-170-actual.json`：2604 B，SHA-256 `24bacee022de941b76a73bba49db2eabc9cf4c6a5be3e515b897de3abfea87d0`。
- `recent-superseded-captures-175-actual.json`：2713 B，SHA-256 `efdcf1501093bff1d9fd0d86ffffdb31681a0e5c1c5e8ce8f277c106d1eb464c`。

卷空闲量两次分别增加 472420352 B、349081600 B，与逐文件实际分配释放不同，残差分别 -53248 B、-32768 B，不虚构来源。累计实际删除为 624429 files / 34253232488 allocated bytes，既往无损压缩另计、不重复相加。

15:12Z 最新容量已满足原单场 2 GiB + 既有其他池 + 系统增长 + 安全余量公式；没有降低门槛或把未来 native 构建预算挪入该场。下一场在本次代码交付 clean HEAD 后重新取得新鲜准入，继续 Source17 PAM 阴性原合同。该容量事实不等于游戏验收通过。

本记录 2027-04-08 复核归纳；外置明细按通用策略 30 日、摘要 180 日复核，活跃输入仍由 owner 按用途及限期保护，不无限续存。
