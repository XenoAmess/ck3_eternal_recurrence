# R0023 normal-exit source inventory 精确 descriptor 绑定修复

本场实际 .4 normal-exit query 的 exact build、owner、process 与 GUI source pins 已 true，但 stock/source 检查停在 `source_inventory_executable_binding_changed`，context/frame/dispatch 均未授验。原 inventory 真实绑定当前 .4 SHA `98702f88…19dd518`；native source verifier 却硬编码唯一 .3 SHA `94b55397…de02a6`。Python builder/verifier已核实际 EXE及guard，库存正确，不能通过伪改库存作热修。

最小源码改变让两个 provider 调用把当前 `ctx.game` 的 descriptor 传入 verifier。新增纯 join 只接受精确 adapter/version/EXE 相互关联的 .3/.4 identity，复用已存在 `IngamePrivateGuiIdentityAdmittedV1`，再核 inventory canonical lowercase digest等于该已验证 descriptor digest。未知版本、adapter/hash错配与跨版本库存均拒绝；不增加 SDK caller输入、任意hash白名单或跳过门禁。

实际module image path、inventory bytes/SHA、settings/DLC、五mount文件、stock六GUI检查保持；后续整个settings/mod/stock verifier源码片段精确相同。Gui/Pins、owner/frame、signature/stage/once、正常exit schemas及动作均未改变，当前实际profile/inventory/DLL完全不动。

在 e728独立branch，仅编译实际 production source与原已有 launch-arguments test TU。新 `--executable-identity-only` 模式只运行7个必要identity用例：.3/.4正例、双向crossed库存、未知版本、混合adapter、混合EXE拒绝，均通过。该模式不执行原历史argv/Win32 decoder测试，也不调用source verifier的文件/进程分支，SDK/CK3/存档/body操作0，未构建 runtime DLL。

第一次编译因新增main参数与原局部argc/argv重名返回C2082，源码及raw完整保留；只修测试参数名后focused002 compile/run0。Defender登记准备沿真实成功MSVC argv调用既有helper，却因 `/Fe:` 参数解析报 `MSVC output operand must be an explicit absolute file path`；未调用WMI/broker，未声称该EXE排除成功。本次不扩大修复其登记harness，失败与纯fixture通过分列。

本source包仍是本地已验证候选；ROOT当前live e728与主树冻结，不由此取得typed正常退出或业务GREEN。ROOT实际闭场后才按fetch→rebase→必要复测→普通push整合，继而新HEAD导出/实际native资格/新cold验证。不能将本次源码修复回填为旧R23正常退出成功。

[原native/inventory、最小patch、首次失败与focused通过小归档](acceptance/2026-10-07-r0023-normal-exit-exact-descriptor-source-fix/INDEX.json)。
