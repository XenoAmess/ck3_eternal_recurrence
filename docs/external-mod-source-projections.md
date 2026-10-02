# 独立 mod 的原版覆盖迁移与可逆投影

2026-10-02，从 [More Tenets Slots(XA) 迁移](https://github.com/XenoAmess/ck3_mod_more_tenant_slots/blob/master/docs/migration-plan.md) 提炼。产品源码、配置和实机报告留在独立仓库。

游戏大版本升级时，先冻结 launcher/build/EXE 和依赖原版文件。覆盖审查必须同时比较文件路径、数据库目录、顶层定义及 scope，不能只检查原文件是否还存在或 supported_version。不同文件名仍可能覆盖同名定义；原版删除一个文件或将 ID 移到另一数据库时，旧 mod 的完整副本可能重新引入已退役类型。

本次 CK3 1.20.0.3 磁盘实例：核心教义从 `common/religion/doctrine_types` 移到 `tenet_types`；创建窗口从 `window_faith_creation.gui` 换成 `window_rite_creation.gui`；信仰创建钩子的 root 由角色改为信仰。这些事实要求重新选择产品扩展入口，不能简单复制新版原版全文进旧目录。具体哈希和产品修复由独立项目报告绑定，不构成所有 mod 的兼容结论。

`tools/ck3_text_projection.py` 提供不依赖 CK3 进程的通用原语：忽略注释和字符串内花括号的结构扫描、唯一命名块定位、SHA 绑定的最小文本替换，以及反向恢复校验。使用者显式传入原版内容、规范化 SHA 和替换集合；工具没有游戏路径、产品 ID、宗教行为或操作者配置。

生成器先检查原版 SHA，再只替换已审阅锚点；验收时逆向移除产品变更，恢复内容必须仍匹配原版 SHA。源文件变更、锚点重复、缺失和额外修改均拒绝，需要重新审阅。SHA 定义为移除 BOM、规范化 LF 后 UTF-8 的摘要，原始文件 SHA 应另记入输入账本。

该结构扫描仅证明引号/花括号与投影一致性，不验证 CK3 语法、scope、费用、UI 布局或原生执行，也不能替代 `open_kaishek` 预验和真实 CK3 验收。调用方自行维护产品合同、发布 allowlist 和实际通过边界。

实际反例见独立项目 [R0001 原生日志](https://github.com/XenoAmess/ck3_mod_more_tenant_slots/blob/master/docs/evidence/live-R0001.json)：将 GUI `spacing` 写成向量 `{ 20 25 }`，结构扫描和投影恢复均通过，CK3 原生读取器仍报 `Malformed token`。该字段在此控件上接受标量。修改控件类型或属性值时，原版相邻控件只能帮助建立假设，最终须由真实加载日志验证属性类型；不能把可逆文本投影称为引擎语法验收。

受管桌面运行的屏幕所有者心跳必须使用当前任务的 `last_sequence` 做 CAS，并保持租约新鲜。首次失败后仅添加序号不能续约已经过期的租约；先按合同释放自己的旧 claim，再注册新任务。运行器须在续约失败等异常路径中关闭自己启动的进程，并写出退出回执，避免 Python 已结束而游戏继续占用桌面。产品冻结输入变化应分配新 run，保留旧 RED。

验证入口：`python tools/test_ck3_text_projection.py`，覆盖真实生产投影/恢复路径、原生 controls 保留、变更拒绝、歧义锚点及注释/字符串扫描。
