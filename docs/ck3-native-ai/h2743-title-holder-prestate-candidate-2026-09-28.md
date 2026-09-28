# H2743 目标头衔持有人前态候选（2026-09-28）

状态：**静态候选；未在 CK3 实机读取，未取得终战条款。** 此分支从 H2743 v3 已提交的读口独立派生，绝不运行 `setup_de_jure_cb`、`resolve_title_and_vassal_change` 或投降动作。

新的 MSVC/Ninja Release DLL 在仓库外 `D:/ck3-research-artifacts/war31-h2743-20260928/build-title-prestate-001/xar_ck3_bridge.dll`，3,141,632 bytes，SHA-256 `6689ED3B3EB40F33157B028BD7067FF859F1C6ACDCFC02EDEB92A7D0F271B17E`。独立构建脚本与 configure/build 命令、stdout/stderr 均保留在同一个目录。旧候选 DLL `FD8B…21470` 与其已准备 attempts 必须保留历史原样；此新 DLL 的字节、路径、SHA 应写入**新的** no-launch 配对和运行单后才能受管实机读取。Python 聚焦单测 7/7 GREEN，尚无实机 GREEN。

## 可复用的精确原生来源

- 既有 v3 读口直接从 WarID `16777231` 的活动战争对象读取 `target_title_ids`，与当前暂停快照比较，并通过完整世代的 `ResolveLandedTitle` 核对每个目标。H2743 运行单要求目标列表精确为 `[2128]`。
- 已有 [`campaign_root_context_v1_abi.json`](../../ck3_autonomous_player/native_bridge/research/campaign_root_context_v1_abi.json) 将 `CLandedTitle+0x258` 证实为完整世代持有人 CharacterID；正式 `campaign_root_context_v1.cpp` 已使用该字段并要求持有人与人物存储对应。此候选直接从**目标头衔对象**读取，不能改用省份持有人代替。
- 同一精确 EXE 构建已绑定人物即时领主只读函数 `0x2613480`，由现有 campaign-root 与围城归属读口使用。本候选对持有人及非空领主做完整世代人物存储回环。
- 每个目标得到 `{title_id,holder_character_id,holder_immediate_liege_character_id}` 前态行；人物独立时领主为 `null`。查询在同一暂停帧读取两次整组关系并比较，继续检查原有 WarID、CB、双方、目标列表、14 项余额、2 项收入以及前后快照。缺少 binding、头衔／人物身份不匹配、关系改变均返回 `unavailable`，不填零、不发布半行。

这些是行动**之前**的原生关系输入。H2743 存档投影已有 Title `2128` 持有人 `33435`、该持有人的个人领主 `29829` 和保存层直属契约封臣 `43755/43703`；候选实机读数尚未取得，不能将这些存档值当作本候选结果。

## 尚未闭合

`target_title_holder_prestate` 不包括标题自身的法理／事实领主 ID，也不包含持有人完整直属**契约**封臣。已有 campaign-root 扫描只枚举“直属且有地”的人物子集，不能充当契约集合。原版 `individual_county_de_jure_cb` 的 `target_titles` 循环仅把目标保存为临时 scope，`setup_de_jure_cb` 在循环外执行；声明目标 `[2128]` 和本候选的头衔前态均不证明执行时 `scope:target` 的真实 referent。

原版 `resolve_title_and_vassal_change` 预览槽 `0x7E9220` 只返回 true，执行槽会进入写入全局变更队列的路径。不得为预览最终迁移而调用执行槽。`title_vassal_delta`、双方有符号资源差、定向停战与继续作战风险继续为 `null`；本候选不提供退出动作。

下一步是在屏幕空闲且取得新鲜 Steam 离线画面后，用新 candidate DLL、新独立 attempt 读取 H2743 v3 两次，检验该前态在同一 paused native revision 的实际值。若需完整的现时契约集合，应先另建同帧、受界、只读的契约数据库 reader，明确覆盖无地／已死亡记录和世代校验；不能把保存层历史值或直接有地封臣子集冒充完整集合。最终迁移仍需不写队列的确切 producer，或在另行授权的真实终战动作中记录前后状态；不能为取证单独提交投降。

本机已向固定 `C:/Users/1/OneDrive/WAR/H2743-EXIT-READONLY-V3-20260928/` **追加**新命名 `REQUEST-TITLE-PRESTATE-ADDENDUM-v1.json`；本机读回 SHA-256 `E6D567D5F9A4C4ADABFD9CB6DBA5AA717C55249578F03C2CB765D313A0364A84`，2762 bytes。同目录 `.issued.json` 发送回执 SHA-256 `02B1C53AD1660D185C2CE8DACBF4A326346D3EC313F9AEEC735EA1E83FDBEDA3`。这只证明本机精确字节落入同步目录并回读，尚无来源机 ACK、响应或云端同步完成证明；原 `REQUEST.json` 和旧资产未覆盖。
