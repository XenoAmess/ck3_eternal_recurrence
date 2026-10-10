# 缓存验收 reviewer 的 CI 夹具勘误（2026-10-10）

精确提交 `0c0e36e21164d55cd9f47d2d8ab9ae7a5cbf3f63` 的
[Official CI 38006953109](https://github.com/XenoAmess/ck3_eternal_recurrence/actions/runs/38006953109)
在共享 acceptance 步骤失败：缓存套件 9 项中仅
`test_original_normal_close_remains_mandatory_and_no_business_pass` 报
`AttributeError: 'Selection' object has no attribute 'context_path'`。
同一提交 [Linear history 38006953137](https://github.com/XenoAmess/ck3_eternal_recurrence/actions/runs/38006953137)
通过；Li Yu Dao static checks **NOT_TRIGGERED**，不计成功。远端 master 的实际 API 已核对为该 SHA。

该测试绕过 `Selection.__init__` 构造旧夹具，未提供 verifier 新调用的真实 reviewer resolver 所需绑定。
本次只补此测试的 `context_path`、`run_dir`、argv/environment、持久化 reviewer/context 与真实 frozen-argv pin。
`Selection.verify()` 继续执行实际 resolver 和 `check_pin`，并断言派生的 reviewer 来自该 context。
原有 normal-close 必需、未闭场/不合格闭场拒绝、合格闭场后仍无 business/product PASS 的断言保留。

在 debug 提交 `3704561725e583d9c9fc10f4c47c1523bb1d9643` 上应用此单项夹具修复后，实际运行一次
`python -B -X utf8 tools/test_ck3_mod_acceptance_workshop_cache.py`：**9/9 通过，exit 0**。
生产 client 与原 CI 字节相同；entry 使用已提交 debug 基线，本工作包未改任何生产代码或添加 resolver fallback。

原 CI API/终态 jobs/双 workflow 完整日志及唯一 traceback、原/新源码 pins 和本地命令回执见
[结果](acceptance/2026-10-10-common-cache-reviewer-ci-fixture/RESULT.actual.json) 与 [索引](acceptance/2026-10-10-common-cache-reviewer-ci-fixture/INDEX.json)。
原始证据 ZIP 共 135 项、364600 bytes，SHA-256 `e8c347978fcc07a3834be8e1d5b5af7d1323895c3e9cbe7e9be58cc3f6ce8614`；
[读回复验](acceptance/2026-10-10-common-cache-reviewer-ci-fixture/ARCHIVE-VALIDATION.actual.json)确认 byte-exact / CRC PASS，全部 33 组原查询回执校验通过。

本次无 CK3/Steam/屏幕或 run ID 操作，`open_kaishek` 预验 not-applicable。
旧 `6a3` 日志与报告保持原样；本地 9 PASS 不追认 `0c0e` 官方 CI 成功，不授实机 GREEN。
后续以新精确 master 的官方 CI 终态为准。
