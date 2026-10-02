# 独立 mod 的原版覆盖迁移与可逆投影

2026-10-02，从 [More Tenets Slots(XA) 迁移](https://github.com/XenoAmess/ck3_mod_more_tenant_slots/blob/master/docs/migration-plan.md) 提炼。产品源码、配置和实机报告留在独立仓库。

游戏大版本升级时，先冻结 launcher/build/EXE 和依赖原版文件。覆盖审查必须同时比较文件路径、数据库目录、顶层定义及 scope，不能只检查原文件是否还存在或 supported_version。不同文件名仍可能覆盖同名定义；原版删除一个文件或将 ID 移到另一数据库时，旧 mod 的完整副本可能重新引入已退役类型。

本次 CK3 1.20.0.3 磁盘实例：核心教义从 `common/religion/doctrine_types` 移到 `tenet_types`；创建窗口从 `window_faith_creation.gui` 换成 `window_rite_creation.gui`；信仰创建钩子的 root 由角色改为信仰。这些事实要求重新选择产品扩展入口，不能简单复制新版原版全文进旧目录。具体哈希和产品修复由独立项目报告绑定，不构成所有 mod 的兼容结论。

`tools/ck3_text_projection.py` 提供不依赖 CK3 进程的通用原语：忽略注释和字符串内花括号的结构扫描、唯一命名块定位、SHA 绑定的最小文本替换，以及反向恢复校验。使用者显式传入原版内容、规范化 SHA 和替换集合；工具没有游戏路径、产品 ID、宗教行为或操作者配置。

生成器先检查原版 SHA，再只替换已审阅锚点；验收时逆向移除产品变更，恢复内容必须仍匹配原版 SHA。源文件变更、锚点重复、缺失和额外修改均拒绝，需要重新审阅。SHA 定义为移除 BOM、规范化 LF 后 UTF-8 的摘要，原始文件 SHA 应另记入输入账本。

该结构扫描仅证明引号/花括号与投影一致性，不验证 CK3 语法、scope、费用、UI 布局或原生执行，也不能替代 `open_kaishek` 预验和真实 CK3 验收。调用方自行维护产品合同、发布 allowlist 和实际通过边界。

实际反例见独立项目 [R0001 原生日志](https://github.com/XenoAmess/ck3_mod_more_tenant_slots/blob/master/docs/evidence/live-R0001.json)：将 GUI `spacing` 写成向量 `{ 20 25 }`，结构扫描和投影恢复均通过，CK3 原生读取器仍报 `Malformed token`。该字段在此控件上接受标量。修改控件类型或属性值时，原版相邻控件只能帮助建立假设，最终须由真实加载日志验证属性类型；不能把可逆文本投影称为引擎语法验收。

另一个实际反例见 [R0003 原生状态读回](https://github.com/XenoAmess/ck3_mod_more_tenant_slots/blob/master/docs/evidence/live-R0003.json)：产品源文件中 define 和同名 script value 都写成 100，原生执行 `GetDefine` 却返回 100，`ScriptValue` 返回 3。产品 `mts_*.txt` 排在原版 `pam_values.txt` 前面，后者覆盖同名 ID。修复为排在原版后面的文件名，同时检查原版该 ID 的定义所有者。这个单模组实例不能推出所有数据库的统一加载规则；其他 mod 的同名覆盖仍须独立审阅。

验收关键配置时，除了源文件和冻结哈希，还应记录真实加载后的有效值。对有镜像 script value 的 define 分别读回两者；对列表、槽位和创建结果再检查原生 UI、费用变化与存档实体。源内容相同不等于有效运行值相同。原生调试日志是本次实例的读回通道，不能将控制台文本已粘贴、按键已发送或命令 ACK 当作效果成功。

受管桌面运行的屏幕所有者心跳必须使用当前任务的 `last_sequence` 做 CAS，并保持租约新鲜。首次失败后仅添加序号不能续约已经过期的租约；先按合同释放自己的旧 claim，再注册新任务。运行器须在续约失败等异常路径中关闭自己启动的进程，并写出退出回执，避免 Python 已结束而游戏继续占用桌面。产品冻结输入变化应分配新 run，保留旧 RED。

槽位验收还必须区分生产列表、可达布局与消费者索引。独立项目 [R0004](https://github.com/XenoAmess/ck3_mod_more_tenant_slots/blob/43765b0ffa53ea84e398e02e64086915be387624/docs/evidence/live-R0004.json) 在 CK3 1.20.0.3 实际读取到 100 个原生教义槽，拖动纵向滚动条也能到达第 100 槽；点击该槽却发生原生访问异常。冻结 EXE 的只读调用链显示，打开窗口的消费者使用教义槽号索引另一组教条条目，未在读取前检查该数组范围。不能把 producer 的数量、同名的索引 getter、可滚动显示或前几槽成功，直接外推成全部槽位可操作。

因此，扩容控件的验收应分别记录：实际列表数量、首尾及跨页可达、首尾实际选择、费用与条件、创建结果，以及保存和重载。空槽可保存也不能代替空槽打开/选择安全。优先操作已经审阅的滚动条；鼠标滚轮产生输入或页面移动，不能单独证明末端已经到达。按钮按住期间的坐标换算工具可能拒绝移动以避免意外拖拽；显式拖拽须在输入前将两个端点都按同一原始画面和实际桌面尺寸校验映射，并保留拖拽后的业务画面。

当 GUI 方法名似乎可复用时，可由隔离 debug userdir 的原生 `dump_data_types` 取得当前注册接口。独立项目 [R0005](https://github.com/XenoAmess/ck3_mod_more_tenant_slots/blob/eb27c6ba47e44b298382e4fd4c337b9d2e505311/docs/live-R0005-selector-investigation.md) 保存了实际导出的接口文件摘要和调查边界。方法名或 getter 的存在不证明参数语义兼容；缺少某个导出也不能证明所有内部方法都不存在。发生原生崩溃时同时保留进程退出码、崩溃日志和 dump，不能只依据没有 GUI 解析错误判 GREEN。该反例是测试方法的富化，不构成新的宗教 MCP 能力或产品修复验收。

验证入口：`python tools/test_ck3_text_projection.py`，覆盖真实生产投影/恢复路径、原生 controls 保留、变更拒绝、歧义锚点及注释/字符串扫描。
