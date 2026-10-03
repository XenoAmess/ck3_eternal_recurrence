# CK3 最新版本适配计划

日期：2026-10-03。当前阶段：来源冻结与代码适配完成，L0 GREEN；实机和发布门待父任务执行。

## 方法与参考

阅读了 [自动升级建筑维护记录](../../docs/auto-upgrade-buildings-maintenance.md)、[来源冻结记录](../../docs/auto-upgrade-buildings-upstream.md)、[验收计划](../../docs/auto-upgrade-buildings-test-plan.md) 和 `tools/build_auto_upgrade_buildings_release.py`。复用的是来源、维护、构建、验收与发布流程，不把建筑自动升级的 605 条边、付款策略或历史 GREEN 套用给本产品。

## 执行顺序

1. 保存公开页面与 Steam 元数据，并冻结完整上游原始目录。核对许可证和来源资产；建立逐文件清单。
2. 同时冻结本机 CK3 version、Steam build、EXE SHA-256 与相关 vanilla 文件 SHA-256。再次核对当前正式版，不能仅修改 `supported_version`。
3. 从源码填写 [功能分析](function-analysis.md) 的未闭合入口；建立旧定义与当前原版的差异表，先写明确产品合同再改代码。
4. 保留需要兼容的存档公开 ID；新增内部名称使用 `cht_` 前缀。canonical descriptor 不含上游或维护版 item ID。运行脚本和本地化均 UTF-8 BOM，descriptor 无 BOM。
5. 仅按确定的实际差异修复 trigger/effect、scope、decision 接口、类型枚举和本地化。本次实机及文案验收只使用简体中文；其他八语只做格式检查，不安排语义／术语审阅或外语实机。
6. 按显式 runtime allowlist 生成隔离 staging 与 deterministic ZIP；README、docs、tools、fixture 和日志均不得进入正式 mod 包。产品工具放 `tools/`，通用能力先检查仓库现有实现。
7. 完成离线解析与构建检查后，由父任务取得本机 CK3 排他槽、新鲜 Steam 离线证据与正式 live run ID；按 [测试计划](test-plan.md) 仅以简体中文执行隔离 userdir 实机。
8. 保存真实 GREEN 和限制后创建新 Workshop 物品。上传前冻结完整 Steam Change Notes 文本、字符数、行数和 SHA-256；匿名回读公开正文，另做全新订阅缓存逐文件校验。立即恢复 Steam 离线。
9. 最终发布事实写入永久 changelog，并由父任务 commit/push 到 `master`。实际上传前，只能使用“待发布／候选”措辞。

## 已执行的适配

实现当前原版 `title_valid`／`DecisionViewWidgetSelectBarony` 接口迁移；保留六种目标、六个 public 决议及其个人金币、革新、和平／成人门。脚本共享六个 `cht_` effect，统一真人与可转换男爵领边界；简中／英文为 44 个完整 key，加入不兼容建筑损失与政府／继承提示。`supported_version="1.20.*"` 只声明兼容范围，真实验收仍绑定 `1.20.0.3`／build `25652598`／精确 EXE SHA。

产品工具已接公共 `tools/independent_mod_release.py`；`build_release.py --check` 做 double-build bytes 比较，`--output` 拒绝覆盖旧 attempt，`--verify --manifest` 对 staging／下载缓存做 exact inventory 与 SHA 校验。正式版本以 `--release-localization` 强制九语文件覆盖和格式；普通L0的简中／英文比较也仅为结构格式检查。

外置 fixture 在 1066 `bookmark_rags_to_riches_duke_robert`／history ID `1128` 的真人玩家进入后，串行调用六个真实生产 effect，另测同类型、AI 和非男爵领负路径。它不证明选择器、决议付款或实际 GUI 执行，这些由父任务独立读回。

## 跨产品成果归属

本产品的决议、迁移政策、素材与专属夹具留在本目录。通用第三方来源清单、staging allowlist／manifest 校验、隔离验收与公开 Change Notes 读回可供其他 mod 复用，优先由父任务整合仓库既有通用工具，避免本目录再次复制 Steam 发布实现。

当前验收范围以[语言验收政策](localization-acceptance-policy-2026-10-03.md)为准：**只进行简体中文实机验收；其他八种语言只做格式检查，不进行语义／术语审阅或外语实机验收。**
