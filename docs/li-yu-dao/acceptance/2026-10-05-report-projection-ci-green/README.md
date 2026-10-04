本记录绑定提交 `a2f09421a1cfcd8a0cbe480933864edfd575d352` 的真实 GitHub CI。通用 Official Runner CI 的 run `37231135004`、job `111520817550` 已 completed/success：60 步成功，20 个可选发布步骤跳过。完整步骤、合并日志、精确 workflow 定义与原始响应保存在 [CI 证据包](ci-a2f09421a-20261005-001/REPORT.md)。

本次归档修复未触发儒家专题 CI。9 个未截断 Git trees 证明改动仅涉及验收报告归档，产品树在 a2、其 parent 与 c40 三处均为 `34f78d27ca82ea212d3346ad920ad602b356b930`；专题 workflow 受监控路径没有变化。

提交 `c40e28a157447f8ab67889a2355e7cbd0fe3a43f` 的儒家专题 run `37230134838`、job `111517885981` 曾实际 success：155 单测，70 runtime 文件、889 双语 key、68 事件，双构建 GREEN。产品树相等绑定了这一既有专题结果，本次没有 rerun，不能记录为新的专题测试执行。c40 的通用 CI failure 和其原始证据继续保留在[既有 RED 记录](../2026-10-05-I3b-commit-ci-red/README.md)。

原始响应、日志和 workflow 定义均以无损 gzip 投影入库。每份压缩字节与解压后的原始字节分别绑定大小和 SHA-256，52 份映射已逐一实际解压复验，源文件和旧证据未改写。包内 56 份文件及 INDEX 的入库路径由独立 import-plan 唯一列明。

上述结论仅证明精确提交的 CI 与源字节绑定，不证明 CK3 实机、反复合流/分裂、领袖、章程、存读档或正式发布通过。
