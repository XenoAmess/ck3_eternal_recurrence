# 实际永久入库记录

2026-10-06 09:37:35 UTC，ROOT 执行 004 导入器，结果 `IMPORTED_AND_BYTE_VERIFIED`。新增 [INDEX.json](INDEX.json)为 22,259 字节，SHA-256 `c161c13feb1d8c143e59bccf33e33d49efccba51b5028cf84237be15775d4f07`，绑定 101 个精确载荷。

58 个历史载荷及原索引逐字节保留，旧 gzip 重压缩次数为 0；55 个新原件引用按内容去重，新增 33 次无损压缩，原始与解码 SHA 均验证。大型存档和 DLL／EXE 本体未读取、未入库。ROOT 导入没有执行构建、测试、Git 或游戏操作。

原构建验证器 CRLF 误判、Defender 注册失败及外层退出码 1 保留；新补充核验确认实际编译和链接，并首次运行两项测试，退出码均为 0。导入器 003 的可移除 assert 门禁未执行；004 改为明确抛出异常的 require，保留 003 原件。

实际回执位于 `C:/workspace/ck3_lyd_runtime_20261004/post-r12-readonly-source-root-import-receipt-20261006-004/RECEIPT.json`。该记录不增加实机信用；后继干净提交的构建绑定、I3b／C3／I4 仍待验。

提交前追加文本投影：Git 按仓库规则将两套读回工具的 13 份 JSON 模板统一为 LF，并删除两份共享解析器末尾的额外空行；所有 JSON 值和解析器 AST 保持一致，暂存区 `git diff --cached --check` 通过。原 48 文件应用回执及测试仍描述此前实际字节，不替换其 SHA。15 份原件已外置保留，投影回执为 `C:/workspace/ck3_lyd_runtime_20261004/r13-root-reader-line-ending-projection-20261006-001/RESULT.json`，SHA-256 `5454f67b92fe4c29e5e13cd56a13f7d144e3434c1bb09ed4b319e61852af3f8a`；未重复业务测试。
