# 重整河山 post-primary 赋法源码合同补正

2026-10-08，Official CI 的旧检查只允许两处 `single_heir_succession_law` 安装；已授权的 post-primary 修复使实际生产源码有三处：创建后、设为主头衔后、启动迁移。检查更新为三处，并解析验证新增安装在恢复头衔 scope 内、位于 `set_primary_title_to` 后且受缺法 guard 保护。原创建和启动迁移断言保持。

仅运行直接受影响的 `test_phase_three_title_law_and_idempotent_save_migration` 一次，实际 1 passed、0 failures、0 errors；[精确候选与回执](C:/workspace/ck3-upgrade-20261007/rmtm-ci-single-heir-contract-ccc-agent-01/DIRECT-AFFECTED-VALIDATION-02.json)保留测试和生产字节绑定。没有重跑完整 suite 或 CI。生产代码、36 文件及 14 日业务合同未改。

这只纠正源码检查与已采用生产修复之间的冲突。R10 实机头衔法 FALSE 的原业务失败仍保留，实际安装原因和生产修复继续研究；不授实机或发布通过。
