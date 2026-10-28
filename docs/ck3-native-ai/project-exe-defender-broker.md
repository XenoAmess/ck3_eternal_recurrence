# 已安装的本机项目 EXE 排除 broker

2026-10-28 补注：下文 2026-10-05 安装记录的 `machine_id: unknown`，所属机器尚未核实，不能证明当前机器已安装或免重复 UAC 已验收。历史原件仍按[统一存储策略](../storage-retention-policy.md)复核；文中的“永久保留”不构成无限期保留授权。

当前接续机器为 `machine_id: xenoamess-full-tower-eb9d2c1186`，观察时间 `2026-10-28T01:29:46Z`。用户要求仅进行一次 UAC。当前方案维护现有 broker：一次管理员安装固定 SYSTEM 按需任务，之后已配置项目源码/构建根下的已知 CMake/MSVC 清单由普通调用方提交，不逐 EXE 提权。受保护的小型运行组件放在 `C:/Program Files/XAR CK3 Project EXE Broker`；批量输入、冻结数据、日志和回执放在固定 `D:/ck3-state/xar-project-exe-broker`。D 盘祖先目录可由普通用户替换，不能只凭叶目录 ACL 认定保护完成；安装时须将数据根卷、文件身份、创建时间和 ACL 绑定到受保护安装清单，客户端及 worker 持有不允许删除共享的目录句柄并重验，身份变化即拒绝。

2026-10-28T02:58:28Z 更新：当前机器已成功安装并完成普通调用方验收。固定任务采用 SYSTEM、无周期触发、固定 action；安装读回包含 638 条 ACL 记录。首个真实注入器的路径排除由 SYSTEM 确认，路径数 16→17，扩展名设置的 `null` 与原进程设置均保留。首次取消记录保留；用户明确要求重试并确认后，管理员进程退出 0，后续测试未再提权。

另一个不同路径的 EXE 由真实单 TU MSVC 编译产生（2.137 秒，未执行该 EXE），普通调用方 `admin=false` 经原公共 helper→固定任务取得完整 SYSTEM 回执，路径数 17→18，仅新增该路径，`runas_calls=0`。共享修复最终原整组共 61P；九个完整模块 mypy 与精确修改前基线均为 41 项，新增诊断 0，类型检查整体尚未全绿。普通客户端曾因扫描 SYSTEM 私有区被拒，已修入共享客户端；它只检查公有 inbox，完整私有区容量点仍由 SYSTEM worker 执行，没有放开私有 ACL 或修改已安装的 C 盘图。

本机原件：`D:/ck3-state/ck3-java-g2-resume63-m0-native01/broker-install-current01/INSTALL-ACTUAL01.json`（1051099B，SHA `b9687409b4ce9fe51b87ce65f2e2b85a982e74b4479912e4ed60140ed256abf4`）；同目录 `SECOND-ORDINARY-RESULT01.json`（5173B，SHA `c88116c835b7d9a9821dac7078645cf5891cc6f1bbc61aaa7b15dc0cae4e2389`）绑定新构建、设置前后态和八份 proof。安装回执继承了准备阶段错误的 `settings_changed:false` 摘要；实际 SYSTEM 回执证明已新增路径，后继结果明确更正，原件未改写。

**当前机器、已配置项目根和两种已知清单的后续登记免重复 UAC 已实际通过。** 此结果不代表 Java 正式 REGISTER、CK3 启动或完整迁移通过。Java 原公共 `readVerified` 已用真实 CMake target 与八份 proof 完整读回，退出 0/2.433 秒，并经独核，未削弱身份或 target 检查。Root 曾因自己的诊断输出把 `before_settings` 重命名为 `before` 而误判合同；原始回执的顶层 `before/after` 实际都是路径数组，修改建议已撤销，零源码修改，原 331 源最终验收恢复。首个 Java CK3 启动仍为 0。

2026-10-05 04:56:18 UTC，固定 SYSTEM 按需任务与受保护运行时安装完成，首批两份构建清单中的四个项目 EXE 经实际 SYSTEM 设置前后读回验证。原始安装回执 `C:/ck3-war-episode04-research-20261004-a01/project-broker-root-resume-a01/installer-receipt.json` 为 1,367,505 字节，SHA-256 `4157fec4c9e66aeaae73b04dee5fcaa6f78f5f1245da188e0c331743096fe9ae`，状态 `installed_initial_outputs_verified`，`settings_status=verified`。这一结果与 Task.Run ACK、fake 测试或静态清单分别记录。

截至本源码整合时，普通 token 为第五个新构建路径登记并取得 SYSTEM 回执的验收仍待独立实际结果。固定任务可安装与初四项生效，不能代替普通调用方免重复 UAC 的验收。旧 [永久排除专题](project-exe-defender-exclusions.md) 的 238 项、六个构建入口与未覆盖旧生产器清单保留为各自阶段的事实。

## 固定任务与信任边界

本机安装根为 `C:/Program Files/XAR CK3 Project EXE Broker`，安装 UUID 为 `83b30886-8dbc-4c9c-8177-d575be46a925`。固定任务 `\XAR CK3 Project EXE Broker\RegisterDeclaredProjectExecutables` 使用 SYSTEM service account，无密码、无周期触发器、只按需运行。唯一 action 是受保护 copied Python 的 `-I -S -B` 与固定 bootstrap/config，工作目录同受保护根。普通调用方只调用 `Run(None)`，不传命令、模块、任务参数或结果路径。

所有运行时文件、stdlib、PYD/DLL、初始化器、worker 和配置均由 SYSTEM/Administrators 拥有并写入。普通 owner 对任务及 folder 仅 read/run；只有 inbox 允许该 owner 提交请求，私有冻结区与 SYSTEM receipt 区不能由普通调用方写入。创建代码/config/runtime 时即传最终 SECURITY_ATTRIBUTES；逐文件实际 owner/DACL/字节检查，不依赖父目录 ACL 或事后收紧。

SYSTEM worker 只消费严格七字段数据请求及两种已知清单 `cmake-file-api-v2`、`msvc-explicit-command-v1`，不 import/执行 repo、Git、CMake、编译器、user command 或用户可写 site/cache。已授权本机 owner/build caller 是信任边界；清单一致性不是抵抗该 owner 的独立构建认证。已配置 source/build 工作区为 D 主仓、`C:/w` 和本次 C 外置研究根。范围内已知 producer 的新 target/new bytes 无需逐 EXE 管理员 enrollment；未知 producer、其他目录、全盘或全机 EXE 扩展名不由此纳入。

客户端和 worker 分别检查 policy/seal/安装身份、实际文件/PE bytes、owner、任务 action/principal/无 triggers、原生 no-reparse/file identity 与 held leases。成功要求同一实际 SYSTEM/admin client 的 ExclusionPath/Extension/Process 三数组 before/after：请求路径全部存在、旧路径保留，Extension/Process 不变。排除设置不等于 EXE 本身运行时可信或发布签核。构建侧仍复用 [普通客户端](../../tools/project_exe_exclusion_broker_client.py) 与 [六入口公共 helper](../../tools/register_project_exe_exclusions.py)，Git-local opt-in 不自动复制到其他机器或 CI。

## 两次真实兼容故障及固定恢复

首次 UAC 的任务缺席检查遇到外层 `DISP_E_EXCEPTION`，内部 `EXCEPINFO.scode` 才是实际 file-not-found。`project-broker-root-install-a01/installer-receipt.json`（相对上述外置根）1,197 字节、SHA `fd6e25ac915ca12873a39a21e1b39d9562a74f180a45bf01810669071e865adf`，phases 为空，未写安装根、未开始设置。窄分类器只识别直接 0x80070002/03，或严格外层 0x80020009 与结构化内层相同 missing；denied/unknown 不降成 missing。

第二次 UAC 已复制全部 734 个文件并检查 ACL，设置内存任务属性时，裁剪的动态 client 缺少 stock `VARIANT`。`project-broker-root-install-a03/installer-receipt.json` 1,357,926 字节、SHA `89952704c6ead5e2b323e8cde424a87b6e89169cf96c95ecbd6a387bdafb02dc`，保留部分安装，设置未开始。修复只逐原 pywin32 source 追加 `VARIANT` 类，不恢复 gencache、registry extension、TEMP/gen_py 或 pickle 初始化。

普通权限实际探针随后设置并读回全部 16 个内存任务属性/action、SYSTEM 账户名解析为 SID18、无触发器与一项 action；同时实际生成 WMI Add 参数实例并读回字符串数组及空数组，未 Register/Run/ExecAdd/Put。恢复入口再检查了 105 个加载模块 origin 全部在新 seal。复制运行时的这些真实接口检查与纯 fake provider 结果分开保全。

实际 a06 恢复继续同一个 UUID。先验旧 734 路径、每个字节和完整保护 ACL、实际任务缺席与三个空数据目录；仅接受 missing folder，或 exact ACL 且空的 retained folder。替换前，四个旧叶及其安全证据归档到新的 protected private 目录；仅替换 `deps/win32com/client/__init__.py` 与关联 runtime-seal/policy/installation-manifest 三份配置。730 个不变文件及祖先 leases 保持，最终 734 文件再次检查，再 create-only 注册固定任务。初四项只提交两个请求，调用一次 Run(None)，共享 180 秒实际回执窗口；失败保存 TaskState/LastTaskResult/运行实例/现有受保护回执，不盲重启。

普通 source parent 曾分别遇到 pywin32 signed SECURITY_INFORMATION、目录继承与旧 lease 快照问题，失败全部保留。实际修正先对 owner nodes 做明确预硬化，再取得最终不可变 readonly leases；Root 最终持有全部 744 源文件与祖先直到 child 退出。这个 source guard 是该次固定 capsule 的父进程合同，不是通用目录 ACL 修改器。

## 入库源码与复现

[源码入口](../../tools/project_exe_broker/README.md) 保存八个运行时/安装模块、固定恢复器、ordinary assembler、source parent context、三个最小 vendor shim/class 和许可证。批量 copied Python、stdlib、PYD/DLL、原始录像/安装包与失败 attempts 仍在外部永久保留。

初始 18 文件输入的 `repo-source-final-a06-a01/SOURCE-PINS.json` 为 3,658 字节，SHA `68e6f7345e5e276d1ab0bd7396d15c395e7a1e11c3f19032e287b92fd15bb214`。入库仅适配 CLI 帮助/只读计划、测试相对路径及文档；实际执行的原脚本放在 `frozen-source`，原 `VARIANT` stock 类和动态初始化器字节保留。`assemble_fixed_a06.py` 明确追加该类，核对最终 bundle `4054437f4a6e18b8feeeab8d2ac91698e82b5006d0b5e49fb1b15afda22ca49e`、authority `4a1aac6e92801a75ae275cafe83aba7e666d93e24ce0ef3647e1e7dd308eef63` 与完整源库存 `7577eb373feb532122b429b8be09dac28e519615fc23c48128abc1f0aa0fafb9`，拒绝覆盖已有输出。

这些源码保留本机 owner SID、固定 Program Files 根和历史 UUID/hash，提供这一精确安装的可审阅复现与维护。它们未提供另一台机器的通用安装配置，也未实现实际卸载删除。仓库帮助入口可用主 venv 查看，实际管理员恢复始终使用 approved frozen capsule 内的 copied runtime/entry 与完整 parent sourceguard。

21 项仓库相对路径测试覆盖原安装/恢复 failure、archive-before-replace、ACK 不能充当 SYSTEM result 和五个 CLI 的帮助入口。`open_kaishek` 为 not-applicable：本包是 Python/Win32 TaskScheduler/Defender 合同，不读取或验收 CK3 parser、原生 ABI 或游戏行为。本次源码集成没有 SDK、桌面、TaskRun、WMI 设置或项目 EXE 执行。

官方方法依据：[Task registration](https://learn.microsoft.com/en-us/windows/win32/taskschd/taskfolder-registertaskdefinition)、[Task security contexts](https://learn.microsoft.com/en-us/windows/win32/taskschd/security-contexts-for-running-tasks)、[CreateFile SECURITY_ATTRIBUTES](https://learn.microsoft.com/en-us/windows/win32/api/fileapi/nf-fileapi-createfilew)、[COM EXCEPINFO](https://learn.microsoft.com/en-us/windows/win32/api/oaidl/ns-oaidl-excepinfo)、[Python isolated search](https://docs.python.org/3.14/using/windows.html#finding-modules)。具体兼容返回与能力完成度以上述本机实际回执为准。
