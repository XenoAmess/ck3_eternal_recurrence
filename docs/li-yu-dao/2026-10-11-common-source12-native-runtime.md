# Source12 共同 native runtime：构建与注册已验证，实机资格待验

Source12 以 `05717072b70d4925f10b3d523b6663d2db89d791` 冻结到 `C:/csr12`，在 `C:/cbr3` 完成新的编译链接，并实际绑定 O12 `C:/workspace/ck3-common-runtime/20261011-012`。这次交付补齐共同 MCP 的缓存、宗教 Title、儒教集会与 challenger graph 注册及惰性接收器调用证据；它没有启动 CK3，所有 `actual_live_qualified` 仍为 false，不能授正式 B4/B5、完整 I4 或 whole-product PASS。75%仍只是工作量估计。

## 构建结果与原失败边界

原构建命令于 **2026-10-10 19:41:28.655445Z—20:17:06.031589Z** 执行（本机次日03:41—04:17）。`native-msvc-result.json` 的 `configured/built/build_succeeded` 均为 true；命令 wrapper exit1 的实际原因是 Defender `MSFT_MpPreference.Add` WMI `-2147217407` 设置失败，不能写成编译失败，也不能声称这些新 EXE 的排除设置已经生效。[原 native result](acceptance/2026-10-11-common-source12-native-runtime/native-msvc-result.original.json)、[原构建 wrapper](acceptance/2026-10-11-common-source12-native-runtime/build-command-RESULT.original.json)和[分层 build result](acceptance/2026-10-11-common-source12-native-runtime/BUILD-RESULT.original.json)分别保留。

新 DLL 为 12,445,696 B，SHA-256 `a5dfb768bba4a6bff39884960cd34dcd269059e9b348ca631711d4f3403b8894`；injector 为39,936 B，SHA-256 `9b29a7506948d73c16e62b9a2568ee74701179e70d17d44e73c80e0b1ed4af48`。本包只引用实际 producer 的 pins，不复制或重新 hash 二进制。

## 实际检查按各自范围计数

| 检查 | 实际结果 | 能说明的范围 |
| --- | --- | --- |
| 五项 CTest 首次调用 | 4 PASS，1 FAIL，exit8 | Confucian executor registration、decision outcome、assembly、religious Title 四项通过；默认 mailbox 因 docs 输入为空失败 |
| 原 mailbox 仅补 docs 重试 | exit2：executable identity contract failed | 该默认 fixture 固定 CK3 **1.19.0.6**，对当前1.20.0.4标为 NOT_APPLICABLE；两次失败保留，未冒称 mailbox 全通过 |
| native challenger graph fixture | 1 PASS，exit0 | 原生惰性 graph 数据夹具 |
| Python 原相关集合 | 29项执行：28 PASS、1 SKIP，exit0 | readonly/graph/exact .4 版本合同；跳过项不是通过项 |
| graph serializer interchange 补项 | 1 PASS，exit0 | 使用已生成 native fixture 的单项 serializer 互操作；未重跑原28项 |
| 共同 SDK 注册资格 | 91 PASS、0 FAIL；4次实际 SDK 调惰性接收器 | 默认关闭、显式开启、严格参数模型和 SDK→service 路由；native driver/payload 与实机资格仍 false |

原 [CTest stdout](acceptance/2026-10-11-common-source12-native-runtime/ctest-stdout.log)、[补 docs 原失败](acceptance/2026-10-11-common-source12-native-runtime/mailbox-docs-retest-RESULT.original.json)、[Python stderr](acceptance/2026-10-11-common-source12-native-runtime/python-stderr.log)、[SDK qualification](acceptance/2026-10-11-common-source12-native-runtime/shared-registration-RESULT.original.json)及[实际 metadata](acceptance/2026-10-11-common-source12-native-runtime/shared-registration-METADATA.original.json)保持原字节。四次 SDK 的接收器是明确的 inert double，`native_calls=0/game_calls=0`，不从它们推导 native payload 或游戏里功能成功。

## 实际绑定与剩余入口

O12 binder 原命令 exit0。manifest 为16,491 B / `5f9fbfa3e08dc1c8494573673de87b6678241baf857d62b63126e00614542d90`；runtime 为2,015 B / `e2918cb160bb6c6bfbc8aac371f0a961ab3e7af859d5cef6fd5a2fbf2d7ac340`；binding 为6,767 B / `3a19ff7837d861610b7fe97b75621fb23ea3e5d0dea3f1046df46949c80218e0`。[原 binding](acceptance/2026-10-11-common-source12-native-runtime/SOURCE12-BIND.original.json)保留 source/build/test/provenance 全部绑定，旧 native 资格和旧 shader-cache key 未直接复用。后续必须由公共 prepare/preflight/allocate/run 消费新资格；当前没有新的 PID/session/live 事实。

正式 B5 源码及 CI 是另一层：精确 `70e7c64d814c2ea9a58550f87ac735aa6cade26e` 的 Official `38083886402`、Linear `38083886371` 已由 ROOT 实际读取为 SUCCESS，现成原件在 `C:/workspace/ck3_lyd_runtime_20261004/r53-b5-70e7-ci-terminal-20261011-001`，本包不重复复制或查询。它不改变 native 实际构建源 `05717072...`，也不代表存在合格 B4 世界。B5仍须真实正确世界的 B4 PASS/正常闭场及精确新 SAVE、同动态 Title/完整88与有序45、独立 saved 四字段/law95 和同帧 native 证明；当前业务信用仍为 false。

## 小证据包与容量闭账

[INDEX](acceptance/2026-10-11-common-source12-native-runtime/INDEX.json)列出原件逐文件路径、bytes/SHA及外置引用；[FACTS](acceptance/2026-10-11-common-source12-native-runtime/FACTS.json)只是上述事实汇总。006预约已实际关闭：remaining reserved peak=0，known retained logical bytes=**516,918,142**。[CLOSED](acceptance/2026-10-11-common-source12-native-runtime/storage-CLOSED-RESERVATION.original.json)、[MEASURE](acceptance/2026-10-11-common-source12-native-runtime/storage-MEASURE.original.json)及[关闭原命令](acceptance/2026-10-11-common-source12-native-runtime/storage-close-RESULT.original.json)入包；48,764 B ASSET-GROUPS只保留外置精确 pin，便于存储专题回链。

大 source indices、DLL/EXE、完整构建 stdout、存档与缓存正文不进入本包；当前外置引用继续按原 retention/TTL 管理，不续期，不承诺永远可读。历史失败原件没有删除或改写。本次文档作者没有重跑任何测试、CI/API查询、构建或实机。
