# CK3 1.19.0.6 `bp1_house_feud.0014` 家族受辱决策树

## 状态与入口

- [static-confirmed] 本专题绑定 CK3 `1.19.0.6` 与 EXE SHA-256
  `2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86`。
- [paused live RED] R414 attempt 2 在原 PID `202268` / generation `1` 命中 instance `1066`，三项均
  shown/enabled，动作未提交。该 RED 表示 harness 缺少事件合同，未证明天朝二期产品失败。
- [paused live RED] R416 attempt 1 在冷恢复 PID `174656` / generation `1` 命中 instance `1076`；
  原版 immediate 这次还发布了 `relation: house_relation`。三项仍均 shown/enabled，动作未提交；这是
  已有事件合同缺少 source-authored scope 变体，不是产品失败。
- [counter-policy static-ready, live action pending] 恢复路线固定 authored `3` / native `2`；旧 instance
  消失或前进前不能标成 production-live primitive。

恋人秘密公开后，`house_feud_lover_exposure_effect` 检查 BP1、婚姻和 feud 目标；满足条件时，以 75% 基础
概率让有关 house head 在 5–15 天后收到事件。vengeful 增加 25，forgiving、已有坏关系各减少 25。
事件本身有五年 cooldown，并要求当前 house relation 不带 `house_feud_cooldown`。

```mermaid
flowchart TD
    A[lover secret 被公开] --> B{BP1 + 已婚 + 合法 feud target?}
    B -->|否| Z[不调度事件]
    B -->|是| C{75% 基础随机；性格/关系修正}
    C -->|失败| Z
    C -->|成功且 victim 是 house head 配偶| D[bp1_house_feud.0013]
    C -->|成功且 victim 是 house head 近亲| E[5–15 天后 bp1_house_feud.0014]
    E --> F{ROOT 与 attacker 仍可 feud 且无 relation cooldown?}
    F -->|否| Z
    F -->|是| G[保留 ongoing relation；呈现三项]
    G --> H[0 开始 family_cuckolded house feud]
    G --> I[1 与 attacker 建立个人 rival]
    G --> J[2 原谅：不建 feud/rival]
    H --> K[feud/rival-or-nemesis/25 年 relation cooldown 等]
    I --> L[个人 rival + victim opinion]
    J --> M[victim -15 可衰减好感/5 年 + 性格压力]
```

## R414 scope 合同

实机继承了 birth/adultery 链的 15 个 saved scope。它们归并为三组不同且均非 ROOT 的人物别名：

- `mother = adulterer_check = house_feud_spouse`；
- `father = spouse = adultery_spouse = assumed_father = secret_exposer = house_feud_victim`；
- `real_father = sex_partner = house_feud_rival = house_feud_attacker`；
- `is_child_of_concubine`、`matrilineal` 为 boolean。

合同冻结这些关系与三项 native `0/1/2` 投影，不冻结 R414 的人物 ID、日期或 instance。

R416 补出了同一原版定义的第二种合法形状：`save_ongoing_house_relation_effect` 找到已有 house relation 时，
事件 immediate 会额外保存 `relation`，而描述第 2317 行也仅在该 scope 存在时显示 feud reason。该 scope 的
原生类型是 `house_relation`；通用 scope 查询尚未解析它的内部 identity，因此合同只绑定类型与完整名称集合，
不把 unavailable 的 generic payload 当作失败。15 个 scope 的 R414 形状和 16 个 scope 的 R416 形状均保持
严格枚举，其他未知 scope 仍 fail closed。

## 原生 AI 与我方路线

三项 `ai_chance` base 都是 25。native 0 偏向 bold/vengeful，文化参数可乘 1.25；native 1 使用
boldness `-0.5`、vengefulness `+0.5`；native 2 对两者都用 `-1`。这说明原生 AI 会按性格偏好复仇，
但不决定当前产品恢复的目标。

native 2 是唯一不创建 house feud 或个人 rival 的路线。它让 victim 对 ROOT 获得 `-15`、五年衰减的
Ignored Plight opinion；vengeful/arbitrary/wrathful/brave/ambitious/arrogant ROOT 会获得从 major 到 minor
不等的压力。当前有界终态验收接受这项明确代价，以避免启动跨家族长期冲突。

## 证据

- `events/dlc/bp1/bp1_house_feud.txt:2310-2433`，SHA-256
  `37B6E662C4FC388E51D5B8EBC6F0FBCE7AE3FDCB825BFE121D23B971966469DA`。
- `common/scripted_effects/03_bp1_scripted_effects.txt:6-120,411-420,467-529`，SHA-256
  `30F4823A7A77C3FF6D96C5E43F3F4FC3F531D4A8584EDC8E99177A2BFE468ADB`。
- R414 RED：`_runtime/p1-post-chaos-terminal-r414-20260911/live-artifacts/terminal-stages-red-attempt-02.json`，
  SHA-256 `A0837453C72CB67300AE07EB76EB2B53A75CB511838543696F2891BD2AF80346`。
- R416 relation-scope RED：`_runtime/p1-terminal-resume-r416-20260911/live-artifacts/terminal-stages-red-attempt-01.json`，
  213,056 bytes，SHA-256 `8F1B7C8D055A0EDC4508454D161DD5B15677536DB0404A60F57463EDE38BB3E6`。
