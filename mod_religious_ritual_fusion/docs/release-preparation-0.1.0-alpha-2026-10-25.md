# 0.1.0 Alpha 发布准备

`machine_id: 4-8e1c2f1861`；准备观察时间 `2026-10-25T05:27:26Z`。标准版本 token 为 `0.1.0-alpha`，展示名称为 **0.1.0 Alpha**。这是首次公开版本的 initial baseline 候选；本文不记录尚未发生的上传或 Workshop ID。

用户于 2026-10-25 明确要求发布当前测试版。发布范围与既有验收事实分别记录，不将发布授权改写为实机通过。

## 实际业务边界

- [R0008](acceptance/R0008-2026-10-25.md) 实际创建并采用 Rite 153，保留来源、三个核心信条、教义、收费、冷却和历史的真实保存证据；独立后态比较为 12 PASS、2 未观察项。
- [R0010](acceptance/R0010-2026-10-25.md) 实际冷载 R0008 结果，八项保存比较通过；原生只读观察与历史界面有真实证据。
- 上述场次的公共阶段仍存在 GAP，不能称为整场验收全部通过。Faith 创建、跨 Religion、拒绝矩阵、十年到期消失、AI 和多人尚未完成实机验收。此发布保留这些限制，建议以备份存档体验 Alpha。
- 本次仅修改版本、发布图片声明、语言文件及对应 Java 文件格式和构建合同；不修改融合脚本或 GUI，也不改写历史场次结论。

## 正式载荷与语言

正式清单为 `tools/product.json` 的 22 个手工文件，加 `catalog/generated-files.json` 的 53 个生成文件，共 **75 文件**；相对此前 67 文件增加七个语言文件和 `thumbnail.png`。发布只使用 Java builder 的显式 staging，不包含源码工具、catalog、docs、验收 fixture 或存档；内层 descriptor 不携带 `remote_file_id`。

当前游戏安装的 launcher 语言选项、九个原版目录及 yml header 已实际核对：简中、英文、法文、德文、日文、韩文、波兰文、俄文和西班牙文。来源记录为外置 `publication-java-a01/LANGUAGE-SOURCES.actual.json`，绑定当前 EXE SHA、原版版本 1.20.0.4、build 25734779 和 launcher 配置 SHA。

简中和英文原文件保持原样。其余七种语言由已有只读 MiniMax-M3 候选工具生成，每种 **65 keys**，合计 **455 条**；仅做 key、BOM、header、双引号、转义、scope、图标、格式标记和换行 token 的格式检查。候选回执为 `publication-java-a01/TRANSLATION-CANDIDATES.actual.json`。非中文不声明语义审阅、母语审阅或实机显示通过，也不恢复这些非中文发布门槛。

Java validator 对清单里实际声明的语言执行结构与保护 token 检查；不在日常 CI 发起翻译，不增加翻译完整度或非中文实机门禁。版本字段由 product、descriptor 和最终 manifest 共同使用 `0.1.0-alpha`；图片必须列入清单并具有 PNG 签名。

## 构建状态

Root 已提供 512×512、696,215 bytes 的 PNG 缩略图；封面素材不作为实机验收证据。本轮唯一默认 Maven 完整验证命令为 `mvn --batch-mode --no-transfer-progress -f mod_religious_ritual_fusion/tools/pom.xml verify`，实际退出 0，20 tests、0 failures、0 errors、0 skipped，耗时 36.401 秒，结束于 `2026-10-25T13:32:30+08:00`。实际重编译 14 个 main 与 7 个 test Java 文件，沿用 `--release 21`、`-Xlint:all -Werror`；新增回归从 prerelease product 经真实 generator、非英文格式与 token 消费者到正式 builder/manifest/verify，并拒绝 scope token 漂移、错 key 和非法版本。

新 JAR 的 `validate --source mod_religious_ritual_fusion` 实际退出 0，完整声明 75 文件通过；这一格式验证包含九语言同一键集与保护 token。原生游戏语言来源、MiniMax 候选、本轮 Maven 与 CLI 原始日志保存在外置 `publication-java-a01/`。正式 staging 将在 Root 固定最终 clean commit 后生成，最终 source revision、清单 SHA 和来源 pins 以 `publication-java-a01/HANDOFF.actual.json` 交付。构建成功只证明所列发布内容，不增加上述业务验收范围。

上传、实际 Workshop ID、匿名公开回读、Steam Change Notes 和缓存加载验收由 Root 在真实操作完成后另记；本文件与构建交接不冒充这些事实。
