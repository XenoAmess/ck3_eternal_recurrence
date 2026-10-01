# 离线 runner 单测的依赖与安装路径修复

2026-10-01，新增逐命令退出检查后，精确主线 `9e37d3df4227578fb754d71278810c9492ca948b` 的
[Official Runner CI 36823839237](https://github.com/XenoAmess/ck3_eternal_recurrence/actions/runs/36823839237)
实际 `completed / failure`，首个失败步骤为 TED release tooling。原始日志显示 TED 单测经 Ox runner
导入 `run_acceptance.py`，缺少其直接导入的 `numpy`。这是离线测试环境问题，尚未运行 CK3。

静态依赖补齐现有 runtime 文件中的精确版本：`numpy==2.5.2`、`opencv-python==5.0.0.93`、
`pywin32==312`；最后一项只在 Windows 安装。加上前包 PyAutoGUI 与 jsonschema，这些包服务既有
离线单测的导入链，没有在官方 CI 增加游戏或桌面验收。RapidOCR 仍为可选，本组测试没有 OCR 操作。

隔离环境首次真实运行 5 项 TED 单测后，暴露另一个旧问题：bootstrap 测试读固定的
`C:/SteamLibrary/steamapps/common/Crusader Kings III`，而本机实际安装在 Program Files，官方 CI
则没有游戏。正式 runner 的默认 EXE 现使用项目已有的 `ck3_installation.configured_game_executable`，
保留显式环境配置与共享安装选择逻辑。没有更改 EXE 哈希准入或 native ABI。

bootstrap 单测只替换外部游戏规则声明的读取结果，实际运行生产文件投影、外层 descriptor、加载列表和
规则渲染，并断言输入默认值写入 presets。它不再依赖 CI 上不存在的 CK3；真实引擎规则仍由实机验收读取。

必要验证使用此前新建的独立依赖 venv，安装完整 static requirements 后运行受影响的 5 项单测，全部通过。
失败 attempt 与修复后结果分别在
`C:/workspace/ck3-upgrade-20261001/audits/ci-runner-import-closure-r1/`、`ci-runner-import-closure-r2/`，
保存解释器、argv、stdout/stderr、退出码和源码 SHA。未启动游戏，未重复产品 L0，也未把遗留 361 审阅失败改为通过。

此次 GitHub API 与失败日志保存在 `audits/github-ci-command-guards-r2/`；原始失败日志 SHA-256
为 `100da4e787cbb5280074a9dde5ff08f61fc0325ccc8cb919d0880974bbffb40d`。

本包验证通过后提交推送；新的官方 run 必须另行记录，不能用本机单测结果代替正式 runner 终态。
