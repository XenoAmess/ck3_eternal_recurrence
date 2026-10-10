# 下一次共同 native 资格：只读结论

SOURCE_ONLY；ROOT 提供的 MAIN 基线为 4112d13，诊断002仍由 ROOT 采用。未操作 Git、导出、构建、游戏、SDK、存档、PE，也未重跑 B5 测试。以下实现存在性不代表新 DLL 或实机资格。

G2/G4 已有真实实现，可与诊断002放进同一次共享构建。不能仅向 O11 metadata 添加名字：C:/csr11 冻结的 MCP 注册目前只有 G3；MAIN 已有 G2/G3/G4 注册。O11 继承的 Cbr2 构建输入实际上早已启用三项 native 开关，因此缺口同时涉及冻结 Python 注册、全局 host feature 和新实际构建证据。

## 已核对的源链

| 层 | 实际文件与位置 | 结论 |
| --- | --- | --- |
| O11 | C:/workspace/ck3-common-runtime/20261010-011/runtime.local.json、manifest.json | source=C:/csr11，native=C:/cbr2；capabilities 无 G2/G4，succession_title_readonly=true，无 challenger feature |
| 旧注册 | C:/csr11/ck3_autonomous_player/src/xar_autoplayer/bridge/mcp_server.py:1337 | readonly 分支仅 G3，没有 G2/G4 注册 |
| 新注册 | ck3_autonomous_player/src/xar_autoplayer/bridge/mcp_server.py:1345 | G2 ck3_query_confucian_assembly_predicates_v1 与 G3 同一 readonly 分支；1360 G4 ck3_query_confucian_challenger_graph_v1 |
| host | ck3_autonomous_player/native_bridge/research/run_ck3_12002_mcp_live.py:1000、3539、3812 | succession flag 给 driver readonly 权限；challenger flag 单独给权限，并传给原 server 子进程 |
| public entry | tools/ck3_mod_acceptance.py:249–259 | 全局 host_features 允许 succession_title_readonly 与 confucian_challenger_readonly；转为真实 host CLI，产品不得选择这些政策（134） |
| G2 native | native_bridge/src/ck3_12003_confucian_assembly_mailbox.cpp:148–160；ck3_12004_confucian_assembly_bindings.cpp:22–30 | actual .4 descriptor 分支绑定 .4 provider，精确 EXE SHA；实际 Enter/Submit mailbox 路径存在 |
| G4 native | native_bridge/src/ck3_12003_confucian_challenger_graph_mailbox.cpp:167；ck3_12003_challenger_graph_readback.cpp:360–369、414–438 | descriptor EXE 传进 BindImage；只接受已知 .3/.4，使用对应 Title provider，按 actual4 输出实际版本/EXE/index |
| executor | native_bridge/src/bridge.cpp:11499–11513、11912–11924 | assembly/challenger 宏下实际注册 executor；14879/14886 admission 和 15080/15092 revision 分支存在 |

上述 native_bridge 路径均在 ck3_autonomous_player/ 下。函数名中的12003是既有软件 namespace，不能据此把 .4 分支判为缺失，也不能据此省略 .4 验证。

## 最小共同 source/export/build 路径

1. 等 ROOT 最终提交诊断002及选定 Python 注册，冻结同一个完整实际 source commit。Source11 原 producer 位于 B/i4-source11-four-path-sourceonly-20261011-001/produce_source11.py；它只接受固定 keeper/queue/两个 test 的四路径投影（75–81 参数、147/155 independent index/commit-tree），不能原样充当这次 native 变化的 producer。沿其已用的独立 index、单父来源、create-only export/index流程，ROOT必须给这次真实选定路径/依赖闭包；新 commit、export、source/native index、输出目录均待实际选择。没有现成公共 acceptance 的 export/build 子命令可冒名调用。
2. 使用真实公共 native 包装器：`<PY> -B -X utf8 <NEW_SOURCE>/tools/run_native_msvc.py --source-dir <NEW_SOURCE>/ck3_autonomous_player/native_bridge --build-dir <FRESH_BUILD> --configure --build --jobs 32 --defender-external-candidate <ROOT_LABEL> ...`。`--cmake-define NAME=VALUE` 可重复；`--target` 接一个或多个实际 target（源码31–44、137–140）。不使用产品私有 DLL/host，不复用 Cbr2 的 SHA 作为新构建结果。
3. 从已实际执行的 O2/BUILD-INPUTS.actual.json（3608B，manifest pin 70ae3c7f…bab36）复用完整定义表与真实 argv 结构，保留已有 frontend/decision/normal-exit 等能力；至少三项必须显式 ON：

```text
XAR_CK3_ENABLE_CONFUCIAN_ASSEMBLY_PREDICATES_PRIVATE_QUERY_V1=ON
XAR_CK3_ENABLE_CONFUCIAN_RELIGIOUS_TITLE_PRIVATE_QUERY_V1=ON
XAR_CK3_ENABLE_CONFUCIAN_CHALLENGER_GRAPH_PRIVATE_QUERY_V1=ON
BUILD_TESTING=ON
XAR_CK3_EXECUTABLE_PATH=C:/Program Files (x86)/Steam/steamapps/common/Crusader Kings III/binaries/ck3.exe
```

生产 target 为 xar_ck3_bridge、xar_ck3_bridge_injector。CMakeLists.txt:983–997 纳入 G2/G3 sources，9305–9318 纳入 G4 sources/宏，均为显式开关。新版 MAIN 的全部其它 feature 默认值不可用旧13项清单推定相同；ROOT最终配置须保留已审共享配置，而非开启全部当前 feature。

4. 同一构建树可增建这些已有 focused targets：xar_confucian_assembly_predicates_v1_test（9266）、xar_confucian_religious_title_readback_v1_test（9281）、xar_confucian_challenger_graph_v1_test（9321）、xar_ck3_main_thread_query_mailbox_v1_test。最后一个的既有 CTest 名 xar_ck3_native_bridge_confucian_executor_registration_v1（7318）带 `--confucian-registration-only <bridge.cpp>`。这是待执行集合，没有声称这些新源码现已编译或通过。
5. Python 既有相关测试入口：ck3_autonomous_player/tests/test_confucian_readonly_private_v1.py、test_confucian_challenger_graph_v1.py、test_lyd_private_build_12004.py。最后文件的 Actual4PrivateContractTests 覆盖三域 outer/inner/build/static-map 关联与错配拒绝（39、72）。诊断002自己的新增 focused target 需由其作者给出，本包不猜名字、不代替其测试。

## 全局 metadata 与下一次 public 消费

新 manifest 必须绑定真正 new source/native indices、MCP source ref、host ref、实际 DLL/injector ref、实际 build input/result；保留精确 game 1.20.0.4 / EXE98702f88…dd518。host_features 保留 succession_title_readonly=true，并显式加 confucian_challenger_readonly=true；entry据此传 `--private-succession-title-readonly`、`--private-confucian-challenger-readonly`。不是产品自行选 host flag。

capabilities 补 G2 `ck3_query_confucian_assembly_predicates_v1` 和 G4 `ck3_query_confucian_challenger_graph_v1`，source_build_ready 只能在新 source/注册/实际构建证据齐全后写 true，actual_live_qualified 仍 false。已有 public preflight（385）只据 build-ready 逐项准入，不能替代后续 list_tools 与实际查询。G2参数为 expected_revision；G4另需 faith_full_ids（真实校验1–8项完整 ID）。按当前 snapshot revision/PID/session/gen/date 请求，同帧资格依旧严格。

接下来仍走 MAIN tools/ck3_mod_acceptance.py 的 prepare → plan → no-context preflight → 原 allocate/直接 review/run/verify 路由；新 case/prepared/lease/输入 pins 待 ROOT 实际生成。新 native/source 会改变 graphics runtime key，不能把 O11/旧 derivative shader seed 的接受外推到新 runtime；应由正式 prepare 合同决定冷 cache 或新的已授权 derivative。没有新增 cache/build/容量权限。

## 容量与未决事实

Source11-NATIVE-REUSE记录原复制 source payload 141,059,781 B；O2已封 ZIP为53,534,946 B，合计194,594,727 B，仅说明旧 source+ZIP低于192MiB。旧产物 DLL9,459,712 B/injector39,936 B不能估算新OBJ/PDB/Ninja/TEMP峰值。新MAIN source增量、编译工作目录上界、诊断 target 增量均NULL；应由ROOT在新容量准入里补实际有界build预算，不能用旧source-only192MiB批准nativebuild。可省重复ZIP/历史大证据与旧测试重跑；不省新native实际编译/来源与所需focused验证。

本机实际可用根是 C:/csr11、C:/cbr2、C:/workspace/ck3-common-runtime/20261010-011；没有依赖旧升级目录。新共同 source/native/runtime/hello/live qualification 全部待实际，B4/B5/C3仍无新增业务信用。
