# Official Runner CI：保留 cmd 中途失败（2026-10-01）

此前 [CI 审计](ck3-1.20.0.2-github-ci-audit-2026-10-01.md) 证明，GitHub run 的 API success
可与原始日志中的失败同时存在：cmd 多命令 block 不会因前一 Python 命令非零退出而自动停止，后面的成功覆盖步骤结果。
本包只修复错误传播，并补齐原有离线测试实际导入的依赖；不修改 361 内容、计数、审阅批准或 native/promo 机制。

## 候选变更

`.github/workflows/static-ci.yml` 的 19 个多命令 `run: |` block、85 条命令后，逐条追加：

```text
if not "%errorlevel%"=="0" exit /b %errorlevel%
```

第一条失败会立即退出当前步骤，保留该命令的实际非零码；正数及负数退出码均覆盖。
REM 注释不算命令。单命令步骤已有直接退出结果，无需追加其他操作。
去除新增 guard 与一行解释注释后，工作流与变更前逐字一致：原有测试、构建命令、顺序、条件与上传配置未变。

`tools/requirements-static.txt` 新增两个精确依赖：

- [PyAutoGUI 0.9.54](https://pypi.org/project/PyAutoGUI/0.9.54/)：与既有 `tools/requirements.txt` 版本一致，
  供 TED/361 原有离线单测导入 runner 使用。
- [jsonschema 4.26.0](https://pypi.org/project/jsonschema/4.26.0/)：供原有 schema fixture 的 `Draft202012Validator` 使用；
  官方 metadata 支持 Python 3.13。

没有添加整套桌面依赖，也没有新增桌面验收、CK3 启动或 native 注入步骤。安装包与模块 import 不能视为实机验收。

## 必要验证

验证目录：`C:/workspace/ck3-upgrade-20261001/audits/ci-cmd-guards-r1/`。
由外置 Python 驱动提取**候选工作流中的实际 guard**，在有限的新目录生成小型 `.cmd`，通过真实
`cmd.exe /d /c <probe.cmd>` 执行；每项 timeout 15 秒，原脚本、stdout、stderr 与生成文件保留。

| 黑盒用例 | 实际 cmd 退出码 | 第二命令的文件 | 结果 |
| --- | --- | --- | --- |
| 第一命令 `SystemExit(17)` | 17 | 没有创建 | GREEN |
| 第一命令 `SystemExit(-1)` | 4294967295（Windows 的无符号 -1） | 没有创建 | GREEN |
| 第一命令成功，第二命令写文件 | 0 | 成功创建，第一命令文件也存在 | GREEN |

完整 guard inventory 检查确认 19 block / 85 command，无遗漏、重复或孤立 guard。
独立的新 Windows venv 安装新增两包，再真实 import PyAutoGUI、导入 `Draft202012Validator` 并检查最小 schema，
安装与 import 均 exit 0。该本机解释器为 3.14.7；GitHub 配置仍为 3.13，正式 runner 结果待 push 后新 run。
验证没有桌面输入或游戏启动，也没有重复产品 L0。`git diff --check` 针对两份源码配置通过。

| 证据 | SHA-256 |
| --- | --- |
| `report.json`（cmd 黑盒与 guard inventory） | `faff18f2007ce983c1b749a65656f66e1cfe651022bf0f3d471e1db4133940f2` |
| `workflow-and-requirements.diff` | `7ad3b3c196f3b6155ec547d9773a26b9eafb98acd0b8e4cffe40317aaab7e2cc` |
| 候选 workflow bytes | `d083229f3396c5916b24e1f5f3d91d6b5e50f6bd5360462843325179928c7bb2` |
| 候选 static requirements bytes | `f1671948f42e10b6ffd6f90c0bfe61432fa2c1f50082430bfd950152a527cc3d` |

`dependency-report.json` 保存隔离安装/import 的 argv、解释器和实际版本；`diff-report.json` 保存原命令完全一致检查。
外置 handoff 保存上述文件的精确 SHA。

## 仍需诚实保留的旧 RED

本包不把既有失败改为通过。加 guard 后，361 的旧 career 计数、文案/审阅 ledger、native preflight 与 promo 证据
漂移可能成为正式 runner 的第一处 failure；后续步骤因失败停止则保持未运行，不能借未运行声称通过。
它们在升级前 `c69260e65` 的官方原始日志中已存在，归因见审计文档；禁止为清空 CI 红色刷新人工审批或七语签核。
两个新增依赖只处理已证缺模块的 environment 边界，不能预先保证其他测试通过。
