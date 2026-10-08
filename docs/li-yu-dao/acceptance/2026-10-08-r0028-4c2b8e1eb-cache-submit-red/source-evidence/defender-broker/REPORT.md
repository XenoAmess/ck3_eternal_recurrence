# R28 精确 EXE 普通 broker 请求准备：实际阻点

来源 HEAD `4c2b8e1eb496ae9167dd23b88fbff3ec9a84b60c`。本轮 producer 实际编译及六项 focused 通过；outer exit 1 与 `built_defender_registration_failed/settings_failed` 保留为独立登记失败。

原 CMake producer 声明 8 个 target，其中 `xar_ck3_bridge` 是 DLL。原 manifest 的 **7 个 EXE** 当前实际文件大小、SHA-256、PE EXE/非 DLL 标记全部匹配；CMake index/codemodel/7 target 来源共 9 项 SHA 也匹配。完整精确路径、哈希及 producer/source 绑定见 `SEVEN-EXE-PINS.actual.json`。没有扫描其他输出、纳入第三方 EXE、目录或扩展名。

2026-10-08T03:26:29Z 固定 `C:/Program Files/XAR CK3 Project EXE Broker/policy.json` 实际 exists=false，见 `INSTALLED-POLICY.readonly.json`。现有客户端 `dispatch_manifest` 在固定 policy 缺席时直接返回 None。因此当前 installation/policy pins、有效七字段请求及普通请求 ROOT argv 均 NULL；没有编造可调用 broker 或安装事实。专题中的历史 SYSTEM 成功回执不能外推到本次固定安装可用。

原失败 receipt 实际 `admin_token=true`、`error_stage=Add-invocation`，WMI 内层 `0x80041001`。原 before/after 空数组与 calls/error 均原样保留，不据此额外推断设置状态。公共 helper 只对非 admin 走 broker；当前 admin 分支会直接 WMI，所以不能把原 CLI 重发称为 ordinary broker 请求。此包只记录阻点，不重试设置。

读取合同、源码、来源 JSON 与精确 EXE 字节之外，TaskRun/WMI Add/UAC/install/service/MAIN/Git/build/export/CI/SDK/game 操作均为 0。后续如 ROOT 选择不同已存在的管理员原生 COM 调用入口，应另立准备及实际结果层，不改本包或旧失败。登记仍 NOT_VERIFIED，whole mod NOT_GREEN。
