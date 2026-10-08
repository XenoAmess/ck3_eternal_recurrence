# R28 管理员 COM 实际结果追加：七个 EXE 登记未完成

来源 HEAD `4c2b8e1eb496ae9167dd23b88fbff3ec9a84b60c`。ROOT 于 `2026-10-08T03:40:15.766483+00:00` 至 `2026-10-08T03:40:16.369624+00:00` 实际执行已准备候选一次，原 wrapper **exit 1**。此追加使用原 JSON/stdout，原候选包、固定 broker 缺席报告与 CI 包均保持原样；没有重新执行设置。

调用前后实际 SID/admin 标记相同，`admin_token=true`。现有 SameAdminDefenderClient 在首个路径 `C:\lr28b1\xar_ck3_12002_event_window_context_test.exe` 的 **一次 Add** 阶段失败，外层 COM `0x80020009`、内层 WMI `0x80041001`，ReturnValue NULL。原错误与阶段 `Add-invocation` 保留；后续六个 EXE 未调用 Add，没有重发。

同一 client 的实际 before_settings/after_settings 三数组均为空；原 `verified_requested_paths=[]`、`missing_requested_paths` 为全部七项，`partial_mutation=false`。只据此记录本次登记未完成，不把空数组扩大解释为全机排除状态改变，也不把 admin client 写成 SYSTEM/broker 成功。具体原字节、caller、manifest/producer/source pins 与 STDOUT hash 对照见 `ACTUAL-RESULT.source-facts.json` 和 `INDEX.json`。

本轮 actual compilation 与六项 focused PASS 仍是独立的原构建事实，此环境设置失败不能改写成编译失败。七个精确 EXE 尚未取得排除验收；不以旧路径、ACK、候选源码或编译通过替代实际设置读回。ROOT 后续 qualified DLL 实机由另一证据层记录，本包没有添加 runtime/business/newT/C3/I4/GREEN 信用；whole mod NOT_GREEN。

归档者本次 WMI/系统 probe/设置/service/install/MAIN/build/export/CI/SDK/game 动作为 0。原 actual receipt、原 execution/stdout/stderr、原 manifest/argv 与旧失败 receipt 按 bytes/SHA 冻结入新 ZIP，一次归档字节核验；没有复制 EXE/DLL 或重读存档。
