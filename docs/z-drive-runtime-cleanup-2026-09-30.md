# Z 旧 runtime 清理：2026-09-30 历史摘要与证据映射

> 2026-10-10 主线整合：恢复来源提交 `68eed8ddd8177ba9d07d355b224a1beb39fed07c` 的研究。下文“当前”均指原调查时的构建与样本；没有新增实机验收，也没有把结论外推到 CK3 1.20.0.4。文中外置原始路径是历史定位，本次未重新读取那些原件。

原报告记录23:06完成294个旧目录及23个内层源码工作树登记移除，最终失败0。原目录合计147,805,022,830 bytes / 1,484,944文件；126个native state、103个operator候选、26个stage index及39个其他M6准备/测试目录。清理按实际内容与源码状态选择，目录名带live没有被单独当作删除依据。

归档旧定位为 `artifacts/cleanup/2026-09-30-z-runtime/`。当时保留386,429文件 / 98,060,452,989 bytes逻辑内容，去重35,117对象 / 41,024,453,510 bytes原始唯一内容，gzip/raw对象占5,545,752,604 bytes。另排除1,098,515缓存及中间文件 / 49,744,569,841 bytes；manifest和恢复样本另计。

旧绝对路径的精确查找方式：`retained/manifests/<原目录名>.json` 的每个member记录相对路径、原始size/SHA、`object`与`compression`，再映射到 `retained/objects/<hash>.gz` 或`.raw`。这份映射用于寻找当时保存的字节，不证明旧原件今天仍存在；本次没有重新读取归档或执行恢复。

首轮282目录成功、12个因 `Filename too long` 失败；原报告保留首轮RED并记录长路径重试成功。这是长度问题，没有冒称管理员权限不足。旧报告还记载存档、DLL、JSON、operator manifest的真实恢复抽样及hash核对；该历史结果不升级为当前恢复或玩法GREEN。

| 旧索引 | 当时 SHA-256 |
|---|---|
| `retained/object-index.json` | `83da9730e5e9ffd062881c1e2efb43d74fe79d7afd6e0c60d82225c00444c586` |
| `archive-summary.json` | `7001754c3c2d1755dc5a432bfb700630371e5e62c461cd7d0b15553429312201` |
| `cleanup-result.json` | `0eadaa540c57435ced5456571b0cabb032c688cba5a77880b5333ab0bb435f63` |
| `restore-smoke-result.json` | `c15862b3063d738d9e4306b58b171feb0f7fd467bfb80eb58e785955d4baa316` |

当时整盘free增加151,266,103,296 bytes，包含同期间其他写入及文件系统影响，不能当作任务净释放量。当前期限、容量、保护项与回收规则由 [统一存储策略](storage-retention-policy.md) 覆盖；不恢复旧永久保留或一次性执行器。本轮当时也没有重复玩法验收。
