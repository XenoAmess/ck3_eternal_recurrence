# R499/R500 `trait_specific_interactions.0011` RED 与通用合同

日期：2026-09-12（Asia/Shanghai）

## 现场

R499 只完成 frontend warmup，并在 R500 启动前终止。当前轮次 R500/PID `181268` 是唯一 CK3；loader GREEN 后，
它从 v7 玩家经理 source `50B713F2...C7E4` 开始执行 Stage 10。已有合同依次处理
`sway_outcome.1001` 与 `stress_threshold.1011`；后者实机选择 authored6/native5 并通过事件实例推进后置条件，证明
R498 修复有效。时间线推进 13 日后在 `trait_specific_interactions.0011` instance `21` 保留新的原版事件 RED；
B1 仍 active，`.120` 未评估，没有对新事件提交选择。RED artifact SHA-256 为
`8DF21A7682E1B30258A12DB736B975E348CE434C6A2A3D0AFFF11F30424B04AA`。

live frame 绑定 root/recipient/subject 为玩家 `27181`、actor 为 distinct character `27168`；
`secondary_actor`、`secondary_recipient`、`intermediary` 为类型确定但 identity unavailable 的 Character scope，五个
`poem_theme_*` scope 均为 boolean。实际 rendered native indices 为 `0/1/2`。

## exact-build 根因与安全选项

CK3 `1.19.0.6` / EXE `2D00FF31...DB86` 的定义位于
`events/trait_specific_events/trait_specific_interaction_events.txt:128-205`，SHA-256 `2709B062...CEE55`。
调用链位于 `common/character_interactions/00_poetry_interactions.txt:7-101`，SHA-256 `324439D9...E9C7F`：
`send_poem_interaction` 在被接受且主题为 mourning 时向 adult recipient 触发 `.0011`。选项 effect 位于
`common/scripted_effects/00_poetry_effects.txt`，SHA-256 `0BF4AACF...57FB`。

- native0 进行随机 diplomacy duel，再走接受或拒绝后果；
- native1/authored2 直接接受：可能给 actor 诗人 XP，玩家获得正面 opinion、中等 stress loss，并有 25% potential-friend 判定；
- native2/authored3 直接拒绝：玩家对 actor 的 opinion 降低，并有 20% potential-rival 判定。

因此通用合同选择 authored2/native1。它避免随机决斗，也避免拒绝带来的关系恶化与潜在宿敌；合同严格绑定上述
11-scope/3-option projection，不保存本次 allocator ID 或日期。宗教域未参与。

## 通用资产与验证

共享 vanilla-event registry/source index 增至 186 个事件与 524 条 lexical caller candidate；dataset SHA-256 为
`210E785F58FE6C176F0AE7DEFCF5301AB9E63BBC41161DBBF45590D4E6FE10C9`。便携证据增至 286 个 blob，
manifest SHA-256 `3660B8AC4BAE5C457A8A15913AF56BDEF07EBD30AB8166A2AE2CE327156DA2B1`；新增的定义、调用、effect 与
R500 RED 都可供只读 MCP 离线复用。

冻结 R500 frame 通过生产解析器 `26/26` 检查，选择 authored2/native1；回放 artifact SHA-256
`FECF7A6CD7CC3105D3474A18BD98FC6DA2017B5A535AF8CEE45BD73D3FB1EE74`。相关 normal/optimized 聚焦测试均为
`50 passed, 147 subtests passed` 加独立 `8 passed`；source-index byte check 与 portable-evidence offline check 均 GREEN。
没有运行全仓测试或扩大游戏日范围。

本包只改 Python 合同与只读通用资产，不涉及 DLL、游戏文件、加载顺序或视频。P1 保持 `8/9`，P2 继续
`LOCKED`。当前轮次 R500 保留 RED，旧轮次 R499 已终止。

## ???????????

???? R500 ????????????? 1200 ??????session report ?? `exit_reason=timeout`?`elapsed_seconds=1206.281`?`restart_count=0`???????? `run-stage10`?canonical cleanup `B66D52597996FE8DE3D673D907F420FF1714319FA0DE41CB454A936152648ABD` ? managed cleanup `6AFF78CFE6A8462F462162533E2FD10C311683930B5A4A151370E22E496BA7E1` ?? GREEN??? CK3????Operator MCP ??? `12446` ?????

?????? `0494375d74a4928573cf47672b6150a0ab894ed2` ? open_kaishek ???? `ab57166a34f6a896919f88cd7d5aaac438bae2aa` ?? rebase?push ??? local/remote ???open_kaishek ???? `4/4` GREEN??? MCP tool ID?v1 schema??????DLL????????????????????? provider/data hash ??????

??? R499 ????? R500 ????????????????P1 ?? `8/9`?P2 ?????? `LOCKED`??????? R501 warmup ? R502 gameplay???? 120 ????????????????????? `.120`?
