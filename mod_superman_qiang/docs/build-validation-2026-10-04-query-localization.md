# 角色查询界面修复候选的 L0 证据

原生 R0007 的正常角色查询界面暴露 `sxad.1.desc` 数据表达式错误。A0004 在九语言中把该描述的 14 个 `[scope:sxad_view_subject.` 前缀机械改为 `[sxad_view_subject.`，继续使用原生保存的角色作用域。相对 A0003 的真实 staging，九份本地化逐字节等于这一替换；另外 13 个正式运行文件完全相同，六项账本和 modifier 机制没有改变。

生成器 `--check` 认证全部 13 个生成文件逐字节一致；静态验证为 GREEN，九语言各 24 keys，UTF-8 BOM、header、引用及保护 token 检查通过。新外置 `fixture-a12` 的五个脚本/descriptor 文件已经由实际 open_kaishek JAR parse/roundTrip 通过，零 diagnostics。该结果只证明语法可解析，不能替代 CK3 对效果上下文和玩家界面的验证。

未重复运行未受影响的 8 项 AST/静态测试、5 项发布测试和双构建。其 A0003 原始证据保持原样；正式 tag 对应的最终双构建由发布流程执行。

此次候选为精确 22 文件，实际 build 与 manifest verify 均通过，绑定 Git commit `2873141e76177f52e218aa7da05e75cbdd312fc1`，没有正式 tag。

- staging：`D:/ck3-superman-qiang-20261004/builder-L0-A0004/mod_superman_qiang`。
- manifest SHA-256：`63b0bc75a4c13bfdb343d77d621617eb425c204af081f00658454b193f261aac`。
- ZIP SHA-256：`551901e384931fb5d465f0eaca3327ef357d004d4e290b7bc205c24cc40c3564`。

[完整 A0004 构建报告](build-report-2026-10-04-L0-A0004.json) 和对应 `build-evidence-2026-10-04-L0-A0004/` 保存实际 argv、起止时间、stdout/stderr、夹具语法 corpus、22 文件 manifest 和 A0003/A0004 精确字节比较。原始外置候选、ZIP 及所有前次 attempt 均保留。

本报告只认证静态合同和构建。正常界面、保存重载及新夹具结果须由后续原生 R0008 证据判断；本候选未上传到外部平台。
