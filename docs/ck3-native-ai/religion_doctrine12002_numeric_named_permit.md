# Numeric special parameters：中央独立 executor 验证

这是中央 R5 增加 `permitted_executor_religion_numeric_special_parameters12002` 的最小集成验证。复用已冻结的 [Numeric](religion_doctrine12002_numeric.md)、[Faith numeric final](religion_doctrine12002_numeric_final.md) 和 [组合 mailbox](religion_doctrine12002_numeric_mailbox.md)，不重复 ABI、旧 numeric15、final10、cache mailbox39 或组合31矩阵。

新 wrapper 先 include domain header 固定结构，把原 fixture `Pump` 的 `permitted_executor` 宏映射到新字段。原组合 fixture 内部已有 cache-main 的 define/undef，不能用一层外部 main 宏覆盖：runner 只在外部输出目录 `temp/` 生成该 frozen fixture 的副本，精确一次把最终 `int main(` 改名为 `int NumericMailboxCombinedMatrixUnused(`，其他字节原样保存；所有内存、native final callback、FrameAdapter、Pump、Query helper 保持原文，仓库原文件保持不动。两个旧 main 均不执行，临时 include 不进 Git，并在 receipt 记录原 source 与临时 include SHA。

新 main 只跑一个 current-versus-main 的实际 Query，并直接断言 primary=null、named 指向 exact numeric executor。真实 TrySubmit → owner ObserveMainThreadPumpAndDrain → 两个 observer → Finish → Wait/Reclaim → protocol1 serializer 输出 `named-current-versus-main.json`；C++ 和 Python 检查同 epoch、date、完整 actor/Rite/Faith ID，以及 actor adjustment -5、main adjustment +5 与 native final30。

仅新增 `src/religion_doctrine12002_numeric_named_permit_test.cpp`、`research/religion_doctrine12002_numeric_named_permit_tests.py` 与本页。中央字段落盘后，单次 MSVC `/O2 /W4 /WX` **8 项检查 GREEN**，Python 已解析唯一实际完整 protocol1 packet。defines 与原 numeric mailbox recipe 相同：`XAR_CK3_ENABLE_G2_PLAYER_RELIGION_NUMERIC_SPECIAL_PARAMETERS_PRIVATE_QUERY_V1=1` 和 `XAR_RELIGION_MAILBOX_STANDALONE_ADAPTER=1`。结果目录为 `Z:/ck3_mod_rewrite/artifacts/g2-offline-2026-10-01/religion-doctrines/numeric/named-permit/`；`result.json` 记录 primary=null、exact named slot、source/generated include/wire/executable SHA 和旧矩阵未执行。没有失败 attempt。

状态为 **static-ready named admission/owner-queue 验证**；该验证只补新入口，bare adapter identity shim 不等于生产 WorkerAdapter，不提升为 live readiness。暂停实机 artifact 由 root 验证。无 CK3/pipe/UI 操作，无共享源码或 Git 写入。
