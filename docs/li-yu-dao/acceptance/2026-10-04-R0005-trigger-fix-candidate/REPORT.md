# R0005 C3 冷载 P0 外置修复候选

基准为冻结提交 `18b1944d1784d3e4ec57189c016335ef135b9b34`。只改 3 文件：领导 trigger authored 模板、对应生成文件、离线集成测试。候选未改 checkout、未进入 R5 当前进程、未调用游戏或 CI。

实际 [R5 日志快照](observed-error.log) 含 4 个 E：`hidden_trigger` 未知；`prev` global link 连续跟随 `prev`，分别出现在 round helper 的两种参数展开和 represented helper。该快照只证明读取时的 4E，不能替代退出后的最终全日志。

修复将 `hidden_trigger` 的原有条件逐项展开；仍要求非 AI、存活、成年、有领地、非 incapable、儒家、lyd_enabled 与当前目录成员。round helper 捕获 ACTOR/round faith，在每个礼仪检查中捕获当前 rite；represented helper 捕获当前 rite/faith。空派豁免仍要求 0 伯爵领，且捕获 faith 中没有任何存活角色奉行捕获 rite。代表仍必须存活、成年、同 rite、非 incapable；没有改成 always，也没有放宽同意、序号、职位、player 或领袖条件。

依据当前本机原版 1.20.0.3 的 `save_temporary_scope_as` trigger 模式：[参数角色捕获再引用](vanilla/00_bastard_triggers-94-105.txt)、[当前 rite 捕获后进入角色并引用](vanilla/passive_rite_learning_triggers-113-130.txt)、[当前 rite 的临时 scope](vanilla/pam_scripted_triggers-6668-6684.txt)、[faith 中枚举角色](vanilla/pam_scripted_triggers-1444-1453.txt)。完整来源路径、文件 SHA 与行号见 [MANIFEST.json](MANIFEST.json)。原版存在这些模式不等于本候选已完成原生 scope 验证。

离线结果：11 项集成检查 PASS；L0 AST/本地化/reference 校验 PASS；领导模板生成字节复核 PASS。新增断言对真实冻结 R5 源码 FAIL，并分别检出隐藏包装、连续 prev、错误信众 rite 身份、AI 发起门禁四个独立突变。每次实际 argv、stdout/stderr、退出码见 [CHECKS.json](CHECKS.json) 和 `checks/` 原始文件。

原生冷载、正式 C3 发起/同意/拒绝、标题与角色 readback、自然 expiry、reload 均为 **NOT_RUN**。此前 L0 通过没有识别这两个原生语法问题；本轮新增的是真实冷载错误的回归约束，仍不把结构解析器当引擎语法或 scope checker。

根在 R5 正常退出并保全后，可导入 authored 模板与测试文件，再运行 `python -B mod_li_yu_dao/tools/gen_runtime.py` 重建正式产物；导入前按 MANIFEST 核对旧文件 SHA。对应生成文件已提供用于 review，禁止在运行中的受管 freeze 上导入。候选统一 diff 见 [candidate.patch](candidate.patch)。
