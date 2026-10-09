# 当前玩家方向的持久停战日期（1.20.0.4）

2026-10-09。本专题补当前 build 的只读观测口，不改变战争策略。历史 1.19 的 R459 与停战证据继续保留；它们不能证明当前 build 的绑定。Native45/46、自然一生和完整战后 Save/Load 均不由本包授予资格。

## 已闭合的原生来源

身份为 CK3 1.20.0.4、Steam build 25734779、EXE SHA-256 `98702F88A547CDE2EAF29A85F93B85F68EE4CF8148336A4F7AFAEB75319DD518`。复用已冻结 immutable03 的 PE metadata，没有重新读取 headers 或计算整个 EXE 哈希。

`has_truce` 实际字符串 RVA `47F9600` → 注册函数 `5AA350..5AA3E8` → creator `2B75170` → RTTI `CHasTruceTrigger` / vtable `47FA708` → 本类实际 slot25 evaluator `2B71AD0..2B71C47`。这个 evaluator 按 scope tag4 与完整 CharacterID 解析双方角色，再调用 `28BC250` 查找现有关系。不能套用另一 trigger 的 slot27。

lookup 的四个原始 RUNTIME_FUNCTION 片段连成 `28BC250..28BC300`。它按角色 `+1B0` 关系表、vector `+20` / count `+2C`、16 字节 row 查找 toward 完整 ID；只返回现有关系或 stock 无效对象，无 call、分配、关系创建或游戏状态写入（仅保存/恢复栈寄存器）。完整独立 predicate 为 `29131C0..2913215`（85 字节），完整日期 getter 为 `2913220..29132A6`（134 字节），ABI 均为 RCX=owner、RDX=toward。二者与命名 evaluator 使用同一 lookup、关系 `ActR` tag `+210`、owner 完整 ID `Character+18` 对照 relation `+8/+C`，以及方向日期 `+28/+58`。getter 返回该方向日期地址，provider 只复制其中的 int32。

`GetTruceEndDate` 字面字符串 `44DCF20` 没有在有限指针/xref 定位中找到引用，因此这里不声称其命名注册已闭合。日期 getter 的语义来自上述实际类型、调用和返回字段链。对应原始范围、哈希和保留的失败定位见 [ABI 记录](../../ck3_autonomous_player/native_bridge/research/ck3_12004_persisted_truce_expiry_abi.json)。完整外置采样包为 `C:/workspace/ck3-upgrade-20261009/g2-persisted-truce-current4-native-01/`；其 research plan 与生成图分别为 `research-plan-static-source-02.json` 和 `research-plan-static-graph-02.md`。

## Provider 与调用合同

新只读 MCP 为 `ck3_query_player_truce_expiry_v1(toward_character_id, expected_revision)`。当前 living played character 固定为 owner，toward 必须是显式完整正 CharacterID。沿已有 legacy 拼写的 `query-raiktor-actual-truce-expiry-v1-N` token 传输，不增加战争动作或任意 owner setter。实际调用经现有 WorkerAdapter 主线程 mailbox 到 .4 concrete provider。

新 binder 严格匹配当前 EXE SHA，复用 .4 CoreBindings 与完整代次角色 resolver。核心读取复用既有纯 callback 双 HasTruce / 双日期算法和暂停同帧比较；外层再次解析双方完整 ID，变化时拒绝。CWar 不参与身份、读取或生命周期，所以 source API 可供战后查询；实际战后持久性仍待实机。

返回保留 `status`、`native_has_truce`、`actual_expiry_observable`、`expiry_date_raw` 和 `same_frame_stable` 等已有 DTO 字段，新增显式当前 build / EXE 身份。两次原生 predicate 都为 false 是合法 `no_truce` 观测，expiry 为 null、readiness 为 false、reason 为 `native_has_truce_false`；不与读取失败混同。两次日期必须一致且晚于当前 date，才返回可观察的 expiry。无法解析角色、读失败、帧/代次变化和已过期不伪装成 absence。

## 本包的资格边界

新 Python 局部验证与实际静态源码采样只支持对应层次。未构建新的 bridge DLL，未调用现场管道，未启动或操作 CK3、Steam、桌面或 lease；当前 Source09 与既有 DLL 不变。下一步由 Root 将源码纳入共同 native/runtime 后，在一次合法暂停同 owner 帧上核对真实 present 与 absence；完整战后 Save/Load 属于后续 G2 原 scope。

采样明确读取 4,594 字节 / 220 次（含失败候选与 metadata 二分行）。命名字符串与具体 xref 搜索另计独立 coverage：唯一覆盖 96,836,786 字节，按查询累计 205,371,854 字节，部分 RIP opcode 查询含 16 次 prefix find；不能把整个定位成本写成只读 4 KB。旧入口不匹配和错误 slot 假设均永久保留。
