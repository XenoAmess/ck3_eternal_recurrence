# 公共 stock grant picker 接线候选

状态：`STATIC_READY / LIVE_NOT_RUN`。作者基线 `ddbe2b97058b465b8a4bbe7484d658069ff43c6d`；MAIN、O13 与正在运行的 R54 均未改变。整体仍为估计 75% / NOT_GREEN。新共同 source、runtime key、Title、NPC 当前资格、实机业务信用均未产生。

本次补足现代公共 host 尚缺的四工具接线。原 driver、native provider、四操作 DTO、旧 profile21/23/24/28 均不改。最终增量见 `candidate-002/PUBLIC-GRANT.incremental.patch`，四现有路径及一条新测试路径的 before/after 精确字节 pins 见同目录 `INTEGRATION-MANIFEST.json`。未复制完整源树。

## 准入与现有 driver 路由

全局 manifest 的显式布尔 `host_features.stock_grant_title_picker` 默认 OFF；产品配置不能自行设置 host feature。统一入口沿既有 `Selection.build_argv` 传一次 `--private-grant-title-picker`；公共 host 将它传给原 child，并在创建原 `RecordingDriver` 后绑定既有 `_grant_title_picker_private_enabled_v1`。MCP registrar 仅在该 permission **严格为 True** 时注册；service 不开启或扩大权限。G4 许可不能隐式开启 grant。

| 新公共工具名 | 必填参数 | 现有操作 |
| --- | --- | --- |
| `ck3_query_grant_title_picker_v1` | `recipient_id, title_full_ids, expected_revision` | query |
| `ck3_prepare_grant_title_picker_v1` | 同 query | prepare |
| `ck3_select_grant_title_picker_v1` | `recipient_id, title_full_id, desired_selected, expected_selected_title_full_ids, expected_revision` | select |
| `ck3_send_grant_title_picker_v1` | `recipient_id, expected_selected_title_full_ids, expected_revision` | send |

路径为 MCP → 新 service 薄入口 → 原 `NativeHeadlessGameplayDriver.grant_title_picker_v1` → 原 `grant_title_picker_v1.execute` → 原 primitive transport/provider。保留严格 public revision、完整 generation-bearing IDs、recipient/actor/PID/gen/date/episode 绑定、capability 检查、claim 落盘、防未知重发及实际 holder 后读；不选取默认 Title 或替代 NULL 输入。query/prepare 的通用列表沿旧合同允许空列表，但它不选择任何 Title；C3 操作卡必须显式提供新验收 Title。

MCP 拒绝 extra arguments、混类型 bool/int/revision、tuple/string 列表、重复 ID、超过 64 项和 UINT32_MAX sentinel；Title 0 按原 full-ID 合同合法，recipient 必须正数。send 必须非空完整选集。prepare/select 的 destructiveHint 保留 `None`，query 为 False，send 为 True。现有 provider 的 warning/158 分支仍不能自动确认或绕过；只有 send 原生完成且目标每个 Title 的 holder 实际读回 NPC 才有局部 transfer_verified，business_full_credit 始终 False。pending/unknown claim 禁止再发 Send。

## 实际新检查

`focused-001`：8 项首轮，7 PASS；唯一 ERROR 是测试误读当前 MCP `ToolAnnotations` 的 camelCase Python 属性。原 exit1、完整 stderr 和原测试字节保留，不重写。仅将该测试改为 `model_dump(by_alias=True)`；`focused-002` 只执行这一受影响 metadata/schema 用例，actual exit0。七项未改变用例不重跑。生产候选四路径在两轮间逐字节不变。

检查使用候选生产 AST 的实际注册器/service/统一入口/host parser，以及安装的 MCP/Pydantic 参数模型；经原 NativeHeadlessGameplayDriver 方法和 execute 流程接到惰性 synthetic transport。覆盖默认 OFF/独立权限、严格 schema、四真实原 driver 路由、stale revision 和后帧变更拒绝、pending claim 禁重发、warning 虚假成功拒绝、实际完整 holder 后读必要性。仅替身原语返回值是合成数据，不授 native、NPC 或业务资格。

两轮前后 HEAD 均为作者基线；无 SDK、pipe、CK3、native 编译或 MAIN 写入。最终补丁 `git apply --check --whitespace=nowarn` actual0（tool chunk `2ec3b7`，0.3403299s；该只读检查时间戳未单独取得）。完整 argv/cwd/start/end/exit/stdout/stderr pins 在两份 RESULT。

## 下一共同 freeze 的必要输入

当前 O13 `manifest.json` 已声明 G4 readonly route，但没有这四个新公共工具；当前 Cbr3 cache 已 `XAR_CK3_ENABLE_GRANT_TITLE_PICKER_PRIVATE_V1=ON`。本包只说明既有 native 源资格可供后继评估，不把未调用的公共接线标成实机已验。

`FUTURE-MANIFEST.fragment.json` 是默认关闭的审阅片段，不是可分配 runtime。将来 ROOT 采用源码并冻结时必须明确选定 hostfeature True、同一 source index 中新的 host/MCP/service bytes、入口版本及四 capability 声明。`source_build_ready` 只能在该实际冻结绑定完成后据证据设置；`actual_live_qualified` 仍 False，直到新实机取得相应证据。source/native build 身份须分别如实记录；未改变 native 的复用资格也须由既有 producer/gate 明确接受，不能假作新编译。

Source09 原两路径 successor producer **不能用于本包**：它不会投影新 host/MCP/service。不得改旧 Source09/O8/O13 清单，或把本包套成已运行源。新 host/source/host_features 会影响 runtime key，必须重新评估旧 v2 seed 的精确绑定；不能默认继承。未来 source/runtime/seed/head 字段保留 NULL，当前没有新 freeze、case 或 launch。

## C3 顺序与业务屏障

1. 先完成既有 formal B4 全保护验收（87/88 门槛与 ordered cache 45 均不减），再独立 B5 的同一新 Title/四属性/law95/SAVE/G2/G3 资格；失败世界不能作为 C3 输入。
2. 读取新场同 Faith NPC65865 的存活、Faith/holder 资格及该新 Title 当前归属，保持 HoF169/actor31254、政治七 AST 与其他身份保护。新 T 仍 NULL 时禁止发 grant；不 set_independent、不执行第二 factory，不由标题授予推断政治独立。
3. 对显式新 T 和 NPC 调 query→prepare→query→select→query→send；每次用当时实际 public revision 与完整实际选集。prepare/selection/ACK 不是转移成功。warning/158 停在原拒绝边界；unknown/pending 不重发。
4. 只有实际 holder 后读确认转移，再唯一 SAVE 与完整 G3/G4 collection，绑定当前 holder-Faith 与旧 owner-Faith 各自事实。C3 discovery/qualification 使用已有单读入口；未知映射不造 PASS，同一保全 projection 可派生资格，无需第二次解析存档。
5. 按既有 C3 合同逐项进行准入/合法拒绝、撤回、死亡清理和重载。空集合省略只能用已封 empty-before/nonempty-after+完整 native collection 证据闭合，不能把字段缺失当 empty；不得降低七保护/registry assertions。

已完成的 saved discovery/adapter 源及 19+7 负例不重跑；其旧 R26 binding 不自动获得当前资格。本包不重造 saved reader/provider，也不开始新 T/注册/撤回/死亡/重载实机。独立 native effectiveDoctrine 仍 UNKNOWN；授予不证明 mandate、完整 C3 或产品成功。旧 R14/R15/R27/R49 等 RED 保持原样。

ROOT 闭场采用后可用统一命令验证新接线：

```text
<verified-python> -B -X utf8 tools/test_ck3_mod_acceptance_grant_title_picker.py -v
```

当前外置检查与未来 MAIN 采用后的检查不可混称；未要求重复原 native/profile 套件。
