# Personal parameters：中央独立 executor 验证

此包只验证中央 R6 新增的 `permitted_executor_religion_personal_parameters12002` 实际 admission 与 owner queue。复用冻结的 [provider8](religion_doctrine12002_personal_parameters.md) 和 [mailbox6](religion_doctrine12002_personal_parameters_mailbox.md)，不重新研究 ABI，不修改原 14 文件，不执行旧 provider17 或 mailbox30 main。

新 wrapper 先 include 正式 domain header，再将原 fixture `Pump` 的 primary permit 标识宏映射到 exact named 字段。原 fixture 内有 provider-main 的 define/undef，runner 因此在外部 `temp/` 生成其字节副本，仅一次把最终 `int main(` 改名为 `int PersonalParametersMailboxMatrixUnused(`；其他字节与 helper 完全复用，临时 include 不进 Git，receipt 记录 frozen body 和 temp include SHA。

新 main 直接确认 primary=null、named 指向 exact executor，只运行一个 current personalflags Query。路径为 actual TrySubmit → owner ObserveMainThreadPumpAndDrain → played personal provider → Finish → Wait/Reclaim → 完整 protocol1 serializer。C++ 与 Python 确认 owner epoch/full played ID/date、完整 supported registry、实际 owned Tenet stable keys，以及明确已知 true 与已知 false 的个人参数。

新增文件仅为 `src/religion_doctrine12002_personal_parameters_named_permit_test.cpp`、`research/religion_doctrine12002_personal_parameters_named_permit_tests.py` 与本页。单次 MSVC `/O2 /W4 /WX` **8 项检查 GREEN**，Python 已解析唯一实际完整 packet `named-current-personal-flags.json`。recipe 使用原两项 defines：`XAR_CK3_ENABLE_G2_PLAYER_RELIGION_PERSONAL_PARAMETERS_PRIVATE_QUERY_V1=1` 和 `XAR_RELIGION_MAILBOX_STANDALONE_ADAPTER=1`。artifact 输出到 `Z:/ck3_mod_rewrite/artifacts/g2-offline-2026-10-01/religion-doctrines/personal-parameters/named-permit/`；`result.json` 明确 named-only、primary=null、旧两个 main 未运行，绑定 source/body/temp/wire/executable SHA。没有失败 attempt。

状态为 **static-ready named admission/owner-queue 验证**。该包仅补新查询入口，bare adapter identity shim 不等于生产 WorkerAdapter。实际暂停游戏证据由 root 验证；此处无 CK3/pipe/UI 操作，无共享源码或 Git 写入，不称 live。
