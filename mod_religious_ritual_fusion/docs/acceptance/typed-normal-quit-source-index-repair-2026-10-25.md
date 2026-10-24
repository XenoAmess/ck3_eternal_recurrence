# R0006：typed normal Quit 来源合同修复

`machine_id: 4-8e1c2f1861`；观察时间 `2026-10-24T22:36Z` 起；测试基线提交 `5f4c1043888f24f4caaa6c3f6264614546ccf30c` 加本次工作树补丁。

R0006 的原生退出实际为 OS 0、native 0，清理及 keeper/CAS 闭场完成；CaseClient 原先留下的 `normal-close-error-preserved.json` 与业务失败不改写。此处验证退出证据消费者，不追加游戏业务通过。

`tools/ck3_mod_acceptance_build_runtime.py` 的 source-index producer 输出 `ck3-common-source-index-v1`，`files` 是仓库相对路径到 `{bytes, sha256}` 的映射。旧 `_typed_quit_codec` 和其测试夹具误用绝对 FilePin 列表。消费者现只读取 canonical 映射中的三个固定 SDK codec 叶，验证字段及原字节；不保留列表别名。

真实完整报告继续读回还暴露第二处拒绝：原 plan 的 `fresh_revision=true` 会由共享 host 注入实际公开版本，因此原 plan 未携带 `expected_revision`。现将 SDK 原始 durable request 与结果的原生 revision、角色、PID、代次、FILETIME、库存 SHA、nonce、签名逐项及 JSON 类型核对。R0006 的公开版本为字符串 `"9"`，原生版本为整数 `8`；两域分开校验。显式 plan 版本错误仍拒绝；省略版本仅在明确 fresh 模式且真实 request 已核验时有效。

`TypedNormalQuitEvidenceV1` 新增必填 `confirmation_request: FilePin`。实际消费者只有 CaseClient 的 normal-close JSON 封包及其测试，无其他严格键集 reader。新增字段参加真实报告读取与 JSON 往返验证；缺 request、错版本、bool/浮点类型及跨身份请求均拒绝。

原有四模块 CI 命令完整通过：46 项、0 跳过、原 wait 0。修改范围的完整类型合同和四个完整函数按原源码前缀提取，mypy 2.4 strict 通过。完整 client 默认 mypy 原 wait 1：两项存量环境错误为缺少 `win32gui`、`win32process` 的 types-pywin32 stubs；原日志保留，不声称完整 client 静态通过，不扩展依赖。

外置实际回执：`C:/workspace/rrf-development-20261024/public-chain-a01/r6-typed-quit-a01/VALIDATION.actual.json`，SHA256 `92acdc6a5986d405f566bf5125510d69b227e409e8642fa6b843ef8180f1f4dd`。同目录保留原始 CI/类型退出、原 consumer 两处拒绝复现、真实 R6 全报告正例及错误列表形状反例。离线 witness 的出生时间取原 SDK 事实并联结原 retained 元数据，没有重开旧 PID 或重新验证已释放 OS handle。

未改冻结 runtime/source index，未启动游戏或执行 SDK、C++、Maven 矩阵。现有 CI 四模块命令自动包含新增测试，无新增 runner 或生产模块。
