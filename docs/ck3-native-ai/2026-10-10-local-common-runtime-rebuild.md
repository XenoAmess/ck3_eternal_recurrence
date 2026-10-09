# 2026-10-10：当前机器自行重建公共运行时

用户确认 `C:/workspace/ck3-upgrade-20261008` 不存在，并要求不依赖它。本次从本机已跟踪源码构建、固定一份供全部产品共用的 manifest，没有等待该目录，也没有回退产品专属 host/native。历史缺件和失败报告保留。

本机 CK3 为 1.20.0.4，EXE SHA-256 `98702f88a547cde2eaf29a85f93b85f68ee4cf8148336a4f7afaeb75319dd518`。正式入口仍为 `tools/ck3_mod_acceptance.py` 的六种模式。

28项实际输入、输出、索引和生产器已逐字节归档：[INDEX](acceptance/2026-10-10-local-common-runtime-rebuild/INDEX.actual.json)、[归档复验](acceptance/2026-10-10-local-common-runtime-rebuild/ARCHIVE-VALIDATION.actual.json)。完整源码 ZIP 和二进制保留外置，仓库保存它们的字节/SHA。

## 实际构建与共享源码

第一次冻结 Source01 `5e2f65740a28dd5df34ffa59862a47030048a1b3` 的构建失败于 MSVC C2712；[共享修复](2026-10-10-religious-title-seh-compile.md)将纯 SEH 调用与含 RAII 的逻辑分开。Source01、失败日志和输入保留。

Source02 `af20455212ed75000ba6136b3be308a9288cb06e` 在 `C:/csr2`，实际 build 在 `C:/cbr2`，公共 DLL/injector 编译链接返回0。特性开关从本机已知真实基线取得并加入公共 frontend rules；完整定义、编译工具和索引位于外置证据，不据此宣称所有产品能力已通过。

| 产物 | 字节 | SHA-256 |
| --- | ---: | --- |
| `xar_ck3_bridge.dll` | 9459712 | `390506e486f5b19e298070523360d420de255a7811b5e79a5b279d5f9331dbbe` |
| `xar_ck3_bridge_injector.exe` | 39936 | `2e22a985ba3166ce50ca1732901f0bac0629e8ff0f068de73330fdd5d09c86a8` |

Source03 `13d063c81ff706d8bc3f9a8bf81f60c283338042` 在 `C:/csr3`，增加[固定保存中已有事件的只读启动检查](2026-10-10-saved-startup-event-admission.md)。与 Source02 全文件比较共有6项变化；native_bridge 下只有 host `.py` 改变，所有其他 native 目录文件逐字节相同。因此沿用已编译 Source02 产物，保留两份完整 source/native 索引和实际比较，不宣称重新编译 Source03。共同运行时固定这些显式输入，不随其他 master 工作包自动改版。

`C:/workspace/ck3-common-runtime/20261010-002/manifest.json` 的 SHA 为 `275bd7bdb8b44e72340e4fb77cc238f43a50dabd532d64f93916d3d0380be51c`；本机映射 `runtime.local.json` 的 SHA 为 `36e880a0784458fd54c3740c0cf69fcccb66cc3e1ca87a82571dba852482660f`。公共 host、source、DLL/injector、Python imports、launcher、队列、keeper 和已安装 task-bus 均绑定精确字节。能力表只授 source/build-ready，`actual_live_qualified=false`。

## 首次本机准入与事务对照输入

[首次本机 bootstrap](../ck3-mod-acceptance-first-machine-bootstrap.md)实际 bundle 已固定。真实只读检查通过：绑定当前 OS MachineGuid 派生 machine ID、canonical ID 历史、八份 R38 原始闭场证据、归档 INDEX、当前实际 bus list 和 durable 4188→4189 释放链。没有借此将 R38 追认为公共运行时或完整事务对照。该检查未分配 ID、创建 ledger 或领取屏幕。

《礼与道》新增 `transaction-only-control` 产品 case，只有 fixture/data/adapter；host/native 选择仍在全局 manifest。正式71文件与原固定 `06159b964d859d30f2f07f4b183284df7d6dac47` 的正式 staging 逐字节相同，诊断覆盖6文件单独挂载。外置 seed 是原 R34 D2a，91711686字节、SHA `a6db85e38ba0648eca4b7e835c79d867b96ca26099698f4d4ee5269b818d822c`。actor/root31254、date_raw53144712、原事件121均固定；真实 typed saved scope 名是 `new_title`，title18373。

四份配置中 `pdx_settings.txt`、`tutorial.txt` 使用 R38 原字节；旧现场和当前 Windows Documents CK3 目录均没有两份 presets。新 fixture 明确创建两份零字节“无自定义预设”输入并保存来源说明，不伪称历史复制，不改变存档及其中的游戏规则。seed 留在外置输入路径，准备 profile 的 saves/logs/run 保持空。

新 case 仍使用既有公共预算 command300/readiness400/timeout2100/hold900/poll0.5；没有延长旧 held 会话。只选择原 D2b 选项一次，以真实终点事件、完整有序45人缓存、resolve 后持久化数值标记、未授封18373和七个政治头衔完整 AST 为证。此对照不授正式 I3b/C3/I4 或整体验收通过。

## 已知边界

构建原始回执的 Defender hook 为 `disabled`：冻结源码没有主仓 Git-local opt-in。随后从已成功构建的真实 CMake codemodel 仅登记新增 injector 精确路径；实际管理员 WMI Add 返回常规故障，读回仍缺该路径，终态 `settings_failed`。未重新 build，DLL/injector 字节保持固定。原 disabled、dry-run仅需CMake glob regeneration的保守停止和实际失败回执分别保留；不能外推旧238路径或称新路径已永久排除。

`af2045521` 的 Official CI 失败于新增无害子进程测试缺少可选 `psutil`；[原失败及修复证据](acceptance/2026-10-10-shared-local-launch-static-dependency/REPORT.md)保留。修复只隔离可选创建时间查询，真实 Popen/wait/退出码7检查仍执行。Linear 通过，LiYu 未触发；不把未触发写为通过。

公共 `prepare` 实际 exit0，完整 profile 为84文件（79项 mod/outer 加四配置、dlc_load），seed未写进 profile。公共 `preflight` 实际 exit0，状态 `READY_FOR_EXISTING_REVIEWED_LAUNCH`；包括安装游戏 SHA、共同 host CLI、固定保存、startup handler/data、adapter 和 native pins。[12项准备和预检原件](acceptance/2026-10-10-local-common-runtime-rebuild/PREPARE-PREFLIGHT.actual.json)另行归档，前28项历史归档不覆盖。原未准备 `plan` 的6项 unbound 阻点及 exit2 也保留，不改写旧结果。

截至此版记录，公共运行时为 **BUILD_READY / LIVE_NOT_RUN**。新实机仍需当次实际无占用检查、唯一 ID/屏幕租约及新鲜 Steam 离线原图亲审；不能由 manifest、bootstrap 或 preflight 推导 live GREEN。事务对照和正式 I3b/C3/I4/整体验收未通过。
