# 公共 allocator 的 CI 测试夹具修复（2026-10-10）

精确提交 `00b88fc4df0b8b4cea8b15ff85de8f244825a329` 的
[Official Runner CI 37979055544](https://github.com/XenoAmess/ck3_eternal_recurrence/actions/runs/37979055544)
在 `Test shared CK3 acceptance without installed CK3` 失败：
`test_mocked_allocation_register_immediately_starts_original_keeper` 仍用旧 `SimpleNamespace`
模拟 ID 工具，缺少真实 `actual_machine_binding` 所需的 `MACHINE_ENV`。
同一提交的 Linear history 成功；Li Yu Dao static checks 为 **NOT_TRIGGERED**，不计作成功。
本机修复前的单项测试复现同一异常，退出码为 1。

本次只修改该测试。它使用真实 ID 工具的机器 ID 派生、当前机器绑定与文件锁，
仅模拟 OS token、临时 ID state 路径及 ID 分配返回；在 `TemporaryDirectory` 内提供
前场 frozen identity、原生闭场报告、CAS 释放、总线历史与最新 machine admission。
生产 `actual_machine_binding`、regular predecessor 闭场检查和 `claim_machine_admission`
实际执行，并检查临时链由 `000001` 推进至 `000002`。
总线/进程 provider 继续模拟，断言 fresh bus list 后 `REGISTER → KEEPER_POPEN` 紧邻执行。
生产 allocator 与 ID 工具字节未改，不读写真实机器 ID/admission，不启动 CK3、keeper 或 Steam。

本地回归共 **34 项通过**：

| 命令（Python 3.13，`-B -X utf8`） | 结果 |
| --- | --- |
| `-m unittest discover -s tools -p test_ck3_mod_acceptance_adapters.py -v` | 9 / 9 |
| `-m unittest discover -s tools -p test_ck3_mod_acceptance_bootstrap.py -v` | 10 / 10 |
| `-m unittest discover -s tools -p test_ck3_mod_acceptance.py -v` | 15 / 15 |

原始 API、terminal jobs、失败日志完整 ZIP、修复前后测试回执与脚本保存在
[证据索引](acceptance/2026-10-10-common-allocator-ci-fixture/INDEX.json)；
[实际结果](acceptance/2026-10-10-common-allocator-ci-fixture/RESULT.actual.json) 记录源码 pins 与边界。
原始字节封存为 `raw-evidence.zip`（228173 bytes，SHA-256
`dcd9179c6825ff0f02e2b47b8400af24ffe7455b92acb0c5fce4fd44af9d7d5e`），
[读回复验](acceptance/2026-10-10-common-allocator-ci-fixture/ARCHIVE-VALIDATION.actual.json)
确认全部 327 项 byte-exact、ZIP CRC 正常，避免 Git 文本换行归一化改变原日志。

这是 Python 测试 provider 的修复；没有 CK3 脚本/解析/有限玩法运行时语义，
`open_kaishek` 预验为 not-applicable。未触发 workflow dispatch；本地通过不追认原提交官方 CI
成功，也不授予公共 runtime 或产品实机 GREEN。后续以新精确 master 的官方 CI 终态为准。
