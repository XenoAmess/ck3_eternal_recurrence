# 天朝 361 Incident X/Y/Z 原生观测口 v1

状态：`static-ready`、`shared-protocol-integrated`、`not-live`

本观测口服务于天朝二期 Incident X/Y/Z 的一次启动批量验收。它只读取暂停帧中的玩家角色，并把请求里的
`owner_character_id` 当作相等性过滤器；调用方不能指定 subject、scope 或变量名。`profile` 只能是
`x | y | z`，分别选择三份编译期固定的 50 项 allowlist，不做字符串拼接式变量读取。三份 allowlist 的
前 10 项分别读取 `zg361_ip_{x|y|z}_probe_*` 冻结回执；shared `zg361_ip_probe_*` 只留在 mod 内部 detector，
不再暴露给 provider。

权威实现与合同：

- C++ 类型/固定 allowlist：`native_bridge/include/xar_bridge/zhongguo_incident_snapshot_v1.hpp`
- C++ 原生 reader：`native_bridge/src/zhongguo_incident_snapshot_v1.cpp`
- C++ serializer：`native_bridge/src/zhongguo_incident_snapshot_v1_serializer.cpp`
- application-main mailbox：`native_bridge/include/xar_bridge/zhongguo_incident_snapshot_v1_mailbox.hpp` 与
  `native_bridge/src/zhongguo_incident_snapshot_v1_mailbox.cpp`
- C++ 离线 fixture：`native_bridge/src/zhongguo_incident_snapshot_v1_test.cpp`
- Python 严格合同：`src/xar_autoplayer/bridge/zhongguo_incident_snapshot_contract.py`
- JSON Schema：`schemas/zhongguo-incident-snapshot-v1.schema.json`
- ABI/来源 fixture：`native_bridge/research/zhongguo_incident_snapshot_v1_abi.json` 与
  `native_bridge/research/fixtures/zhongguo_incident_snapshot_v1_source_contract.json`
- normal/`-O` 测试：`tests/unit/test_zhongguo_incident_snapshot_contract.py` 与
  `tests/unit/test_zhongguo_incident_snapshot_scaffold.py`

## 查询与权限边界

能力名为 `game.command.query-zhongguo-incident-snapshot-v1`。MCP 公开参数精确为：

```text
request_nonce
expected_revision
owner_character_id
profile = x | y | z
```

禁止增加 `subject_character_id`、`case_kind`、`variable_name(s)`、`scope_character_id` 或任意透传字段。
subject 恒为 same-frame `played_character_id`；reader 只为该角色构造 kind-4 event target。probe 中实际冻结的
owner 必须等于请求 owner 且不能等于玩家自己。前后帧必须相同，50 项 raw row 必须连续读取两遍且逐项相同。
X/Y/Z 共享 played subject/expected owner ACL，不要求业务 cycle、probe serial 或资源值相同；中央 stage 分批推进
时这些字段本就可以来自不同的已冻结业务时点。

## 严格终态 union

可用帧的 `terminal.kind` 只能是两种：

1. `na`：probe 的 `result/source/consequence` 必须精确为 `0/0/0`；N/A arm 必须携带同一
   owner、subject、cycle、probe serial，`reason=1`、正 `receipt_serial`、`applicable=0`、
   `kpi_staged=0`。它是正向“不适用”证明，不是空案卷。
2. `incident`：probe 必须为真实正案，source/consequence 只能是 `(1,1)`、`(3,2)`、`(4,2)`、
   `(5,3)`；final arm 必须回连同一 owner、subject、cycle、source、consequence，并携带正 case、revision、
   incident serial、`-4..4` final score 与 `applicable=1`。X 终态 state 固定为 8，Y/Z 固定为 6。

两个 arm 严格互斥，未选 arm 必须为 JSON `null`。不存在“字段都没读到所以算 N/A”的路径。

KPI 也采用严格状态：N/A 只能是 `not_staged`；正案只能是 `pending` 或 `consumed`。pending 必须
`pending=1/consumed=0` 且没有消费回执；consumed 必须 `pending=0/consumed=1`，并携带正 receipt 及完整
owner/subject/origin/due/consumed-cycle/case/score/incident join。旧轮、错 owner、错案或 collision 后残留 tuple
都不能过 readiness。

## 管理者国库 producer 已闭合

commit `9441742` 中的 `zg361_ip_capture_real_incident_effect` 已在显式
`government_has_flag = government_has_treasury` 能力守卫下，把同一 probe 帧的三项资源冻结在受评者 scope：

- `zg361_ip_probe_subject_gold = gold`
- `zg361_ip_probe_manager_treasury = root.treasury`
- `zg361_ip_probe_capital_control = capital_county.county_control`

complete-cache guard 同时要求三项变量存在；没有零值兜底。provider 将
`zg361_ip_probe_manager_treasury` 先由每个 profile freeze effect 复制为
`zg361_ip_{profile}_probe_manager_treasury`；三份固定 allowlist 只读取各自副本，并像另外两项资源一样保留
kind-1 原始 payload、按 Q100000 解码。provenance 的 `manager_treasury_source` 仍精确记录上游 detector
variable，ABI/source fixture 另记录 provider key template 与 freeze effect template。

如果任一实际帧缺少该变量，字段必须保持：

```json
{"status":"unavailable","value":null,"unavailable_reason":"variable_absent"}
```

此时 `resource_snapshot_ready=false`、总 `ready=false`。禁止从 `source_kind=4` 推断余额为 0，禁止把缺字段补 0，
也禁止为填这个字段开放 caller-selected owner scope reader。合法的真实国库余额可以恰好为 0；是否可用由 typed
status 而不是数值本身决定。

## 共享层精确插入合同

共享层现已按下表精确接入。Incident 独占第十七个固定只读槽
`permitted_executor_septendenary`；它不复用 B2 的 sequence/result key，也没有进入 planner action space。

| 文件 | 稳定锚点 | 必须插入的内容 |
|---|---|---|
| `native_bridge/CMakeLists.txt` | `zhongguo_result_case_snapshot_v1*.cpp` / 当前最后一个 ZhongGuo provider | 把 reader、serializer、mailbox 加入 bridge target；把 fixture test 连同 `zhongguo_case_snapshot_v1.cpp` 加为 CTest；至少把 mailbox source 置于 `/W4 /WX` 编译覆盖 |
| `native_bridge/include/xar_bridge/main_thread_query_mailbox_v1.hpp` | `permitted_executor_*` 尾项，当前并行树已到 `sexdenary` | 分配合并后“下一个唯一空闲” executor 槽，在 mailbox 与 environment 两份结构中同时增加 |
| `native_bridge/src/main_thread_query_mailbox_v1.cpp` | null 环境检查、environment→mailbox 复制、permit-any 检查、executor ACL 四处 | 同一槽四处同步；遗漏任一处都必须让 mailbox 测试 RED |
| `native_bridge/src/ck3_11906_adapter.cpp` | ZhongGuo capability 数组与 result/B2/manager 项 | include incident header，数组计数加一并加入 capability |
| `native_bridge/src/game_adapter.cpp` | `ParseZhongguoResultCaseSnapshotV1Step` 邻近只读 query 分支 | include mailbox header；把 exact step 映射到 incident capability，不能加入 action steps |
| `native_bridge/src/bridge.cpp` | result/B2/manager query 的 result-frame、permit、sequence、dispatch 分支 | include mailbox；hello/query_scope 声明；新增 `ZhongguoIncidentSnapshotResultFrame`，payload key 固定 `zhongguo_incident_snapshot`；注册唯一 executor；新增独立 sequence；按 result provider 的 same-frame wait/cancel 模式接 exact request/serializer/failure；不可复用别的 query sequence |
| `src/xar_autoplayer/bridge/native_driver.py` | result/B2/manager contract imports、capabilities、dynamic query parse、execute dispatch、私有 query helper | import本合同；公开 `zhongguo_incident_snapshot_v1_query_supported`；把动态 query 排除出 action；发送的 wire 字段只能是 8 个 control fields；校验 result key、native revision/date/player/connection generation 后调用两级 normalizer |
| `src/xar_autoplayer/bridge/service.py` | `query_zhongguo_result_case_snapshot_v1` 同类只读方法 | 新增 `query_zhongguo_incident_snapshot_v1(request_nonce, *, expected_revision, owner_character_id, profile)`；查询前后都核对 snapshot id/revision/native revision/date/paused/player/connection generation |
| `src/xar_autoplayer/bridge/mcp_server.py` | result/B2/manager helper、tool、probe 列表 | 新增唯一 MCP tool；input schema 精确三个业务参数加 expected revision，不得接受 subject/variable alias |
| `tests/unit/test_repository_contracts.py` | schema/contract 精确集合与数量 | 加入本 schema/contract；显式更新计数，不能用放宽断言规避 |
| provider 专属 integration test | result provider bridge test 模式 | 覆盖 native-driver request exactness、pause/revision/capability/connection drift、service signature、MCP schema 拒绝 subject/variable alias |

ABI fixture 的 `integration_status` 已更新为 `shared_protocol_static_ready`。这仍只代表静态接线与 fixture；
没有 paused CK3 artifact 前不能写 production-live。

## 批量实机验收合同

统一 phase2 live batch 在同一 CK3 PID、同一 paused frame 中按 `x → y → z` 查询；三份响应的 terminal kind
集合必须精确包含 `{na, incident}`，每域至少冻结并保存以下原始 MCP 响应：

- exact N/A：完整 probe + 正 N/A receipt + `applicable=0/kpi_staged=0`；
- exact incident：正 final score 与 case/incident/source/consequence；
- KPI pending，并在下一正式 KPI 冻结后查询 consumed receipt；
- subject personal gold、manager treasury、capital control 三项 Q100000；
- stale owner/profile/revision、cross-arm、重复查询不改状态的负例；
- profile receipts 可以有不同 cycle/probe serial/resources，但 owner/subject ACL 必须相同，后写 shared detector
  不得改变任何已冻结 profile response。

只有 manager treasury producer 已落地、provider `readiness.ready=true`、loader error scan 无本项目归因错误，并且
上述 paused artifact 都存在，才能把 Incident 提升为 `fixture-live` 或更高。OCR 只可在 MCP 真值闭合后截展示图。

## 当前验证

- 合并 B2 PIP 与 Incident 后，从空目录生成的 MSVC 19.51 / C++20 Release 构建通过；
  全量 CTest 56/56 通过，其中包含 Incident reader、mailbox 与 source-contract 三个专项。
  最终外部构建目录为
  `C:\Users\xenoa\AppData\Local\Temp\xar-provider-integration-final-20260831T1620`；
  source fingerprint 为 `670A9E9C093EA2ACF7826724ED7BE8CC0BAE1855A64FDAA268FEB5BFA09C84A4`，
  DLL SHA-256 为 `3FBB8D2645C4C16C7AC4EA13A889990B79454FC88340891BDA0BF4E5EAAF5E73`。
- 合并后的 native driver、service、MCP、ZhongGuo case/result/B2/Incident 相关 Python 回归：
  normal 492/492、`-O` 492/492，包含公开 schema 精确集合合同。
- mailbox/B2/Incident 的 8 份 ABI、source fixture 与公开 schema 均已重新解析；
  `git diff --check -- ck3_autonomous_player docs/ck3-native-ai` 通过。
- MSVC 19.51、C++20、`/W4 /WX`：reader、serializer、mailbox 均独立编译通过。
- 离线 C++ fixture：完整资源 N/A、manager treasury 缺失 typed unavailable、Y incident-pending 均通过；
  可执行文件保存在
  `C:\Users\xenoa\AppData\Local\Temp\xar-incident-scaffold-20260831T1615Z\incident_fixture_test.exe`，
  SHA-256 `828F8628C60A3E08C9871D598DEA9A3289EBF57787827610BFE953EB49FB590A`。

2026-09-01 新增 profile-frozen fixture：同一个 paused frame 同时保存 X=N/A（cycle 6）与
Y/Z=incident-pending（cycle 7），三次 provider query 均 `readiness.ready=true`。MSVC 19.51 Release targeted
CTest 2/2 GREEN，构建目录为
`C:\Users\xenoa\AppData\Local\Temp\xar-incident-profile-receipts-20260901`；随后连 mailbox 一起复跑为
3/3 GREEN。mixed fixture 可执行文件 SHA-256 为
`DF3C3FBAF03E6D94342D6EA47E64BDA2552FC83E6C4CD352F70D4564A9C876E1`，source-contract 可执行文件为
`F6EC244F46076E7B3BB1848963EBBDDBDC557317174A8069F12744F475A8AC01`。这仍是离线 fixture，尚不是 CK3 paused artifact。

直接调用 MSVC 编译这组 standalone fixture 时必须带 `/DNOMINMAX`，否则 `windows.h` 的 `max` 宏会破坏
`std::numeric_limits<...>::max()`，并在 `/WX` 下失败。编译工作目录必须放在仓库外的 artifact 目录；早期一次误在
仓库根生成的 `zhongguo_case_snapshot_v1.obj`、`zhongguo_incident_snapshot_v1.obj`、
`zhongguo_incident_snapshot_v1_serializer.obj`、`zhongguo_incident_snapshot_v1_test.obj` 已作为过程素材保留，
不得把它们当作当前 50-key fixture 产物。

这些证据仍不包含 CK3 live，不能越级宣称 production-live 完成。
