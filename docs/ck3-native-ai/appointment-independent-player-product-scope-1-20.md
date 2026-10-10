# QOL 百万分逻辑与原 government 合同：一次文本核对

**结论：独立条件是正式产品条件，必须保留；不只是fixture选角便利。** 实际逻辑是减分1000000，不是给所有human候选加分。将玩家换成非独立human不能保持现有产品的正向百万差分验收。

## 玩家可见产品及生产来源

权威生成器 `tools/gen_xqol_appointments.py:14,18–29` 为行政1处、贤能2处、天朝2处分数插入。最小语义原文：

```text
admin: top_liege = this
merit/celestial: is_independent_ruler = yes
is_ai = no
has_variable = xqol_auto_appoint_successors_enabled
subtract = { value = 1000000 ... }
```

这些条件位于 `candidate_score.value`；官方 `_succession_appointment.info:8–10` 定义该处root为appointment candidate。所以检查的是被计分候选自身，不是“任意human候选只要其上级玩家开关开启就减分”。行政保留其实际代码 `top_liege=this` 表述，不把它悄悄改写成另一个trigger。

| 当前生产文件 | 精确条件和减分行号 |
| --- | --- |
| `mod_xenoamess_quality_of_life/common/succession_appointment/admin_governor.txt` | :59–71；:62 top_liege=this，:63非AI，:64开关变量，:66–68减1000000 |
| 同目录 `meritocratic_governor.txt` | civic:61–73 / military:117–129；独立条件:64/:120，减分:68–70/:124–126 |
| 同目录 `celestial_governor.txt` | civic:101–113 / military:133–145；独立条件:104/:136，减分:108–110/:140–142 |

产品开关本身也限定相同玩家范围：`common/scripted_triggers/xqol_triggers.txt:1–9` 的 xqol_supported_player_trigger要求is_ai=no、is_ruler=yes、top_liege=this，并属于administrative/meritocratic/celestial。`common/decisions/xqol_decisions.txt:9–16,30–37` 的正式启用/停用决议使用该trigger并设置/移除开关变量。

玩家说明 `workshop/xenoamess_quality_of_life_description.bbcode:20` 保留原版候选池/资格/分数并使其他最高分合资格候选继任；`:43–45` 的明确范围是“非AI、独立的行政制、贤能制或天朝制玩家”。这与生产代码一致，不支持将适用范围扩大成全部human候选。

## 原验收合同与harness具体前提

`tools/ck3_mod_acceptance_cases/xqol_administrative_appointments.json:13–16` 与 `xqol_meritocratic_appointments.json:13–16` 同时要求政府类型、empire tier、independent=true。`xqol_government_adapter.py:97–105` 以实际root证明政府与独立身份；`:49–50` 要求该人类自然在合法完整池且independent_human_candidate=true；`:51–61,81–84` 要求准确百万off/on/off、原开关恢复、实际AI任命/继任。

独立与正向百万差分对应产品真实条件，不能删。**固定e_byzantium/e_goryeo、1066.9.15及empire tier则是当前harness具体选角约束**：分别写在两份 `xqol_followup_cases/<government-case>/fixture/events/zqagov_events.txt:9–16,27` 和上述post_start，产品trigger/分数代码不写固定头衔、日期或empire tier。若Root未来评审替换固定选角，应继续保留自然独立受支持玩家、实际完整池中的人类与AI、原GUI/真实分项、百万差分、原switch恢复和真实任命继任；不是改成dependent human或脚本制造候选。现有原合同明确empire，任何这种harness输入调整仍须Root单独评审授权，本包不落实。

这次核对不能证明有另一个自然独立角色满足全部原前提，也没有证明R57/R58唯一排除机制。下一轮不应将“独立只是无关harness假设”作为再次cold的依据；必须先取得原规则下人类真实自然入池的事实，才有正向分数差分可验。现有两个RED/所有GAP保留，不将候选缺席改判通过。

仅产品/合同文本读取和外置薄卡。未live/native ABI/build/prepare/test、未修改MAIN/Git/fixture/helper，也未新增预算、采样或callback。
