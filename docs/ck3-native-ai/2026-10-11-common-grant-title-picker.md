# 现代公共 host 的 stock grant Title picker

本候选为 `STATIC_READY / LIVE_NOT_RUN`，整体仍为估计 75% / NOT_GREEN。MAIN 作者基线 `ddbe2b97058b465b8a4bbe7484d658069ff43c6d`；正在运行的 O13/R54 未改变。未来共同 source/runtime/new Title/当前 NPC 资格和业务信用均未产生。

四工具复用既有 `NativeHeadlessGameplayDriver.grant_title_picker_v1` 与 `grant_title_picker_v1.execute`，保持 native provider、DTO、旧 profile21/23/24/28 不变：

| 公共工具 | 必填字段 |
| --- | --- |
| `ck3_query_grant_title_picker_v1` | recipient_id, title_full_ids, expected_revision |
| `ck3_prepare_grant_title_picker_v1` | recipient_id, title_full_ids, expected_revision |
| `ck3_select_grant_title_picker_v1` | recipient_id, title_full_id, desired_selected, expected_selected_title_full_ids, expected_revision |
| `ck3_send_grant_title_picker_v1` | recipient_id, expected_selected_title_full_ids, expected_revision |

共享 manifest 的 `host_features.stock_grant_title_picker` 是严格布尔且默认 OFF。产品不能自选该 feature；统一入口传 `--private-grant-title-picker`，公共 host 传给原 child 并显式绑定原 driver permission。MCP 注册器仅接受 permission 严格为 True；service 不提权，G4 readonly 许可不隐式开启这四工具。

参数保持 full generation-bearing ID 与严格 public revision：拒绝 bool/int 混用、未知参数、tuple/string 列表、重复/超限 ID、UINT32_MAX sentinel；Title 0 沿原合同合法，recipient 为正数，send 的完整选集必须非空。通用 query/prepare 允许空列表但不会选取 Title；C3 必须显式提供经过新 B4/B5 验收的同一新 T，NULL 不能自动挑选。

路径为 MCP→service 薄入口→原 driver→原 primitive/provider。原 claim、防未知重发、exact paused owner/frame/date/build 绑定及完整 holder 后读保持。prepare/select/发送 ACK 不证明转移；warning/158 分支不自动确认，pending/unknown Send 不能重发。局部 transfer_verified 还须实际每个目标 holder 都读回 recipient，business_full_credit 始终 False。

[永久原始回执与字节索引](acceptance/2026-10-11-common-grant-title-picker/INDEX.actual.json)保留首轮失败和单项后继；外置来源包为 `C:/workspace/ck3_lyd_runtime_20261004/c3-common-grant-public-route-sourceonly-20261011-001`。首轮 8 新 focused 中 7 PASS；唯一测试 ERROR 是 MCP 注解 Python 属性大小写误读，原 exit1/源/完整 stderr 已保留。只改为 `model_dump(by_alias=True)`，受影响 metadata/schema 单项重验 actual0；七项未改用例不重复。生产四路径字节两轮不变。检查运行实际 MCP/Pydantic schema、候选生产 AST 和既有 driver/execute，经合成 transport 覆盖路由/权限/claim/后读；无 SDK/game/native 编译。最终源码 patch 只读 `git apply --check` actual0。CI 仅新增现有公共验收 job 的测试命令，未执行未来 CI。

当前 O13 已有公共 G4；Cbr3 已启用 grant native flag，但当前 O13 并未投影本候选四工具，不能继承公共实机信用。未来共同 freeze 须将新的 host/MCP/service 放入精确 source index，并明确 feature/capabilities/source/native 各自身份。四 capability 的 source_build_ready 只能由未来实际绑定取得，actual_live_qualified 保持 False 直到实机证据。

Source09 的原两路径 producer **不适用于此变更**。不得覆盖旧 Source09/O8/O13 清单或用它遗漏 host/MCP/service 新字节。host/source/host_features 改变 runtime key，旧 v2 seed 必须重新评估精确绑定；当前没有新 freeze、runtime、case 或 seed 资格。

执行顺序仍是 [formal B4](../li-yu-dao/i3b-public-formal-b4.md) 全保护通过→独立 [B5](../li-yu-dao/2026-10-11-i3b-formal-b5-source.md) 同新 T 保存/属性/law95→实际 NPC65865 存活/同 Faith/holder 资格→显式新 T 的 query/prepare/select/send→实际 holder 后读→唯一 SAVE/G3/G4→既有 C3 单读 discovery 和无第二次存档解析的派生 qualification→正式准入/拒绝、撤回、死亡清理、重载。87/88、ordered cache45、七保护和 registry assertions 不减；不 set_independent、不执行第二 factory，不由授予推断政治独立。current holder-Faith 与旧 owner-Faith 分列，独立 native effectiveDoctrine 仍 UNKNOWN。旧 RED 不改，没有完整 C3、产品或 Workshop 发布成功信用。
