# 墨西拿正常战斗终局：败方正统性同角色读回合同

日期：2026-09-27。本页接续[冻结存档缺口](normal-result-loser-legitimacy-pair-gap-2026-09-27.md)，只审计现有 CK3 1.19.0.6 EXE、NativeBridge 源码与公开响应合同；没有运行 CK3，也没有改变 DLL。精确 EXE SHA-256 为 `2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86`。目标是原生败方 CharacterID `29829`，不是当前玩家的泛称。

## 可用读口与身份边界

| 读口 | 静态事实 | 对本场的结论 |
| --- | --- | --- |
| `query-campaign-root-context-v1.player_legitimacy_v1` | `ReadPlayerIdentity` 先从 local-player manager 唯一解析当前玩家的 full CharacterID，再从世代安全的 Character storage 解析指针；`CampaignRootContextRequestV1` 只带 `expected_snapshot_revision`，没有目标角色参数。[实现](../../ck3_autonomous_player/native_bridge/src/campaign_root_context_v1.cpp) `550–616, 2039–2108`；[请求定义](../../ck3_autonomous_player/native_bridge/include/xar_bridge/campaign_root_context_v1.hpp) `357–359`。 | 仅当暂停帧的 `played_character_id` 和响应 `player_character_id` 都是 `29829` 时，可把该字段当败方读数。`072/074` 控制胜方 `31549`，现有读口不能代读败方。 |
| 原生当前值内存链 | EXE 既有静态 getter 分析记录 wrapper RVA `0x2625280`、condition RVA `0x2871150`、`CCharacter+0x1C0 → legitimacy data+0x28`、signed Q100000；[战争终局专题](war-termination.md) `348–369`。Bridge 的独立原生资源读取器也按这个 offset 取值；[实现](../../ck3_autonomous_player/native_bridge/src/ck3_11906.cpp) `5025–5066`。 | 是特定角色读口的已知取值链，不等于当前公开 RPC 能输入任意 CharacterID。旧资源读取器在空指针时发布合法零、负值 clamp 零；campaign-root 字段则对空指针、失败或负值返回 `unavailable`，两者的缺失语义不能混用。 |
| `query-war-termination-exit-terms` 的 primary resource rows | 源码中 `ResolveTermsCharacter` 经 `module+0x570C130` 的存储槽解析任意 full CharacterID，核对 `CCharacter+0x18`，可为战争双方读资源；但公开 `ReadWarTerminationExitTerms` 目前固定返回 `unavailable`，理由为既往 loaded-effect preview 崩溃；[实现](../../ck3_autonomous_player/native_bridge/src/ck3_11906.cpp) `1827–1853, 2870–2885, 18161–18167`。 | 不得复活该预览来补 29829 后值；战斗结束也不保证 War/CB 查询上下文仍存在。 |

campaign-root 的正统性字段从 `player_character+0x1C0` 读取指针再从 `+0x28` 读 signed `int64`；缺指针、读取失败或负值对应明确 unavailable reason，只有非负值发布 `{raw,scale:100000}`。[原生实现](../../ck3_autonomous_player/native_bridge/src/campaign_root_context_v1.cpp) `1835–1854`、[序列化](../../ck3_autonomous_player/native_bridge/src/campaign_root_context_v1_serializer.cpp) `403–415, 856–870` 与 [Python 合同](../../ck3_autonomous_player/src/xar_autoplayer/bridge/campaign_root_context_contract.py) `277–294` 三层一致。查询要求 application-main、已暂停、map/玩家 ready、精确 build 和预期 native revision；读取整个 root 两次，前后帧必须相等，且 full CharacterID 的 storage 指针不变 (`campaign_root_context_v1.cpp:2047–2100`)。但 root 的其他字段也可能导致整体 unavailable；不能在此时把某个局部正统性叶子强读出来。

## 下一次自然终局的最小取证

1. 从冻结源档启动一个**新**的独立败方控制 attempt。校验 EXE/DLL SHA、Steam 离线与 CK3 独占资源；在首次原生暂停帧先核 `played_character_id=29829`，并冻结实际 CombatID、WarID 与双方身份。若以 `072/074` 的墨西拿同场 tuple 作对照，其既有值是 CombatID `16777218`、WarID `4`；新 attempt 出现不同 ID 时只能先建立独立配对，不可冒充旧场。不要把存档 `321` 当作临终前读数。
2. 在终局前最近的稳定暂停帧，通过唯一 owner driver 调一次现有 `query-campaign-root-context-v1`；保全原始 command response、相邻 snapshot、日期、native/public revision、query_sequence、root `player_character_id=29829` 与 `player_legitimacy_v1.raw/scale` 及各文件 SHA。若 root 或该字段 unavailable，记录未知并终止本配对，不补零。
3. 让原版自然推进至 `normal_result`，保全同场 terminal journal 的 CombatID/WarID、winner/loser、sequence/date 和原始响应。在终局已写回后的**首个**稳定暂停帧再次按相同合同读 root；两次均需 full ID `29829`，明确记录中间经过的日期/小时、命令和其他事件。若角色切换、死亡、世代变化、root readiness 失败、查询跨帧或同场身份不能绑定，整组标 RED。
4. 可以计算 `(post.raw-pre.raw)/100000`，只标为这段时间内 `29829` 的**净变化**。要证明它由败方脚本的 `warscore_value >= 15`、`is_valid_for_legitimacy_change` 与 `minor_legitimacy_loss=-50` 所写，仍需独立绑定 loaded 节点父链/RHS 与该次 effect 写入的角色和时点，排除同窗口其他正统性写者。单凭净差等于 `-50` 不升级为因果证据。

若必须在胜方控制的 `072/074` 型回放观察败方，当前公开 root 合同不适用。将来的**独立私有、默认关闭、只读**定向字段才可考虑沿已知 storage/full-ID 解析链取 `29829`：只在精确 EXE/DLL、application-main 暂停帧和预期 revision 下执行；限制唯一目标 ID、容量与 fallback 检查、完整 ID 复核、前后帧及指针世代复核；空指针返回 unavailable，原始 raw/scale 与查询时点一起输出。不得调用 effect、mutator 或已停用的战后预览。这是设计门禁，不是本轮已实现能力。
