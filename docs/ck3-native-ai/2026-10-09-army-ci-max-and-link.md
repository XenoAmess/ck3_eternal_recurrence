# 2026-10-09 isolated army CI 的 Windows 编译与链接修复

Official Runner CI [run 37949901557](https://github.com/XenoAmess/ck3_eternal_recurrence/actions/runs/37949901557) 对提交 `6af52ba2dbe4888f28e8e1f109b644d42273383c` 的 army fixture 编译失败。`windows.h` 的函数式 `max` 宏展开了 `std::numeric_limits<std::int32_t>::max()`。测试改为 `(std::numeric_limits<std::int32_t>::max)()`，仍向相同 overflow 分支输入相同极值，原断言保留。

本机 `C:/lci39max1` 在该修复后继续编译，实际暴露 `LNK2019`：生产 `AppendArmyStrengthV1` serializer 已引用 `xar::ck3_12004::ReadActualLossWriterObservations12004(std::span<const std::int32_t>)`，isolated CI 的翻译单元清单却未包含定义它的 `ck3_12004_actual_loss_writer_journal.cpp`。公共 CI builder 现加入这个生产翻译单元，并冻结 serializer、journal、observations 类型及 1.20.0.4 版本头的 SHA-256。未使用占位实现，也未删除 serializer 行为或测试断言。

验证命令：

```text
C:/Users/Administrator/AppData/Local/Programs/Python/Python313/python.exe -X utf8 tools/check_native_army_routes_ci.py --build-dir C:/lci39maxlink1
```

该命令的 compile/link 为 **exit 0**。随后本机永久 EXE 排除登记的 WMI `Add` 返回常规故障，helper 因 `settings_failed` 停止，原 `army-reader-ci-result.json` 保持 **failed**，请求路径未取得实际登记读回。没有修改登记工具、关闭 hook 或重编译。

另一次显式 fixture 运行绑定这个已链接 EXE 的 SHA-256 `d85132366874044524eaee6b07431bc6bcfdcf41877fabd711eebd5fe7725243`，于 `2026-10-09T15:48:29Z` 返回 **exit 0**、`CK3 1.20.0.2 army offline fixtures passed`。续跑回执绑定原 helper 结果 SHA，并确认原结果字节未变。fixture 测试通过与 Defender 登记未完成分别记录，不能将原 helper 改写为通过。

原 linker RED、本次 build stdout/stderr、fixture stdout/stderr、Defender manifest/receipt 和结果 JSON 保存于 [证据索引](acceptance/2026-10-09-army-ci-max-and-link/INDEX.actual.json)，压缩包按每个源文件字节复验。该 fixture 不初始化或安装 writer journal，不启动、读取或连接 CK3/Steam；未配置 journal 的查询返回 `nullopt`。本次只验收 Windows 上孤立 army fixture 的可编译、可链接及既有测试通过，不授予 live runtime 或任何 mod 业务通过结论。修复提交的完整 Official Runner CI 仍须单独读取终态。
