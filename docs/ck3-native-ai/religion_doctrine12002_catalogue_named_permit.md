# Doctrine catalogue：中央独立 named executor 验证

中央 R4 在 install environment、runtime mailbox、copy 和 admission 增加 `permitted_executor_religion_doctrine_catalogue12002` 后，此包只验证这个新增真实查询入口。原 [provider5](religion_doctrine12002_catalogue.md) 与 [mailbox9](religion_doctrine12002_catalogue_mailbox.md) 源码全部保持冻结，不重复其 ABI 或旧测试矩阵。

新 wrapper 先 include domain header 固定结构，再将原 fixture `Pump` 中的 `permitted_executor` 标识宏映射为 exact named 字段。原 matrix main 改名而不执行；新 main 仅跑 **一个 loaded-catalogue Query**，另直接断言 primary slot 为 null、named slot 指向 exact catalogue executor。它沿未替换的 actual TrySubmit → owner ObserveMainThreadPumpAndDrain → provider → Finish → Wait/Reclaim → protocol1 serializer。

这里只复用 old fixture 的 native memory / FrameAdapter / Pump / Query 代码，不复跑 old empty/unavailable/provider矩阵。新增源为 `src/religion_doctrine12002_catalogue_named_permit_test.cpp`、`research/religion_doctrine12002_catalogue_named_permit_tests.py` 和本页。编译只用 `/O2 /W4 /WX`，defines 与原 query package 相同；bare adapter identity shim 与真实游戏 WorkerAdapter unwrapping 的边界保留。

结果写入 `Z:/ck3_mod_rewrite/artifacts/g2-offline-2026-10-01/religion-doctrines/catalogue/named-permit/`，仅保存一个 `named-loaded-catalogue.json` actual packet。一次 MSVC `/O2 /W4 /WX` **8 项检查 GREEN**；Python 直接解析该实际完整 packet，确认 protocol1、exact step、当前 actor/revision、完整 registry 与 mod stable key。`result.json` 明确 `named_permit_only=true`、`old_matrix_main_executed=false`、`old_provider_tests_executed=false`、primary=null，并绑定实际依赖 source/wire/executable SHA。

状态为 **`static-ready` named admission/owner-queue 验证**。真实暂停游戏 artifact 和 Python SDK 资格仍由对应 owner 验证；这不是 live 证据。无旧 span/旧矩阵重跑、无 CK3/pipe/UI 操作、无共享源码或 Git 写入。
