# 本机项目 EXE broker 源码与固定安装复现

此目录保存 2026-10-05 已实际安装的 broker 源码、原生文件权限适配器、固定任务安装器与 a06 恢复过程。完整合同、实际设置回执与限制见 [专题](../../docs/ck3-native-ai/project-exe-defender-broker.md)。普通构建调用方使用既有 [客户端](../project_exe_exclusion_broker_client.py) 与 [登记 helper](../register_project_exe_exclusions.py)，不会从本目录自动安装服务。

Python 3.14.7、stdlib、PYD/DLL 运行时批量资产保留在外置已批准包，未进入 Git。本目录的 `vendor-shims` 保存删去 registry/gen_py/cache 路径的两个动态 COM 初始化器、实际 pywin32 stock `VARIANT` 类及其许可证。

从仓库约定的解释器可只读查看入口；帮助路径不会初始化 COM、改变 DLL 搜索或读取系统设置：

```text
tools\.venv\Scripts\python.exe -B tools\project_exe_broker\install_project_exe_broker.py --help
tools\.venv\Scripts\python.exe -B tools\project_exe_broker\resume_project_exe_broker.py --help
tools\.venv\Scripts\python.exe -B tools\project_exe_broker\assemble_fixed_a06.py --help
tools\.venv\Scripts\python.exe -B tools\project_exe_broker\uninstall_project_exe_broker.py
```

以下是当前本机已封存 a06 的只读计划，不注册或运行任务：

```text
tools\.venv\Scripts\python.exe -B tools\project_exe_broker\resume_project_exe_broker.py --expected-authority-sha256 4a1aac6e92801a75ae275cafe83aba7e666d93e24ce0ef3647e1e7dd308eef63
```

`assemble_fixed_a06.py --approved-a05-package <preserved-a05-package> --output <new-directory>` 只作普通离线组装。它以 native leases 读取旧包 734 项字节，明确追加 stock `VARIANT`，复现相同安装 UUID、新 bundle、authority 与完整源库存 SHA。`frozen-source/resume_project_exe_broker.py` 保留实际管理员执行的原 entry 字节；仓库外层 entry 仅增加可从主 venv 调用的帮助/只读计划，不代替已批准源包中的执行入口。

这些工具绑定本机固定 Program Files 根、owner SID、历史安装 UUID 与 a05/a06 哈希，服务于该次安装的复现与维护。它们没有通用重装、自动提权或任意管理员命令入口。实际恢复仅使用已批准 capsule 内的 copied Python/entry，并由普通 owner parent 持有完整源文件和祖先 leases。`source_guard_a05.py` 保留这一固定 capsule 的 parent context；不能把它视为任意目录的权限修改器。卸载入口只输出准确的保全/移除计划，执行删除未实现。

[tests](tests/) 的 21 项检查使用仓库相对模块路径，覆盖既有安装/恢复失败、归档先于替换、任务 ACK 与真实 SYSTEM receipt 的区别和 CLI 帮助。`frozen-tests` 保留原测试 source；其原绝对证据路径由 [TEST-EVIDENCE.json](TEST-EVIDENCE.json) 记录。冻结 18 文件输入库存在 [candidate-source-pins.json](candidate-source-pins.json)，入库适配差异见 [integration-provenance.json](integration-provenance.json)。所有历史失败均继续保留。
