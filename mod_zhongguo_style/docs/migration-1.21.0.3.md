# 天朝特色 361：Florin 1.21.0.3 迁移候选

`machine_id: desktop-3fevhd2-1c74096080`。本次目标为本机已安装的 CK3 1.21.0.3 Florin／Steam build 26785313，EXE SHA-256 `859f0d380098adcb130eb9d453458222749fcdf6d46126ad0ed99d78f9a0aa28`。PE FileVersion 为 1.0.0.0，与 launcher/display 版本分别记录。版本号为候选 0.4.2；canonical Workshop 物品仍为 **3792585972**，没有创建或移动 tag、生成正式发布资格或更新工坊。

## 源码范围

这是完整的官僚考核产品：直属官员考核和严格 7/14/2 配额、新人保护、361 政策卡及其已实现案卷、80 槽冻结考核榜、京察召集与活动、额外薪酬和申诉。没有将它缩为外观更新，也没有把研究中的 361 套独立状态机或全部 1083 分支追认为已实现、已实测或本次新增发布门槛。

运行投影仍为 1034 文件。现有 `common`、`events`、`gfx`、`gui` 和九语言本地化均不覆写原版文件；它们不直接引用 1.21 重建后的 holding/building 键。本次保留这些运行正文的全部原字节。运行改动为 descriptor 的 0.4.2／1.21.*；维护工具的实质改动是将本次已审依赖接入现有静态校验链，校验真实消费者、严格字段类型、重复字段、路径、源码 SHA 和锚点，缺少或漂移时明确失败。

`tools/stock_compatibility_1_21.json` 记录实际 14 份原版源文件的 SHA 与消费者。它是有限的已审源码集合，并非完整引擎 API 或所有传递依赖的证明。

| 依赖 | 本次核对 |
| --- | --- |
| `common/governments/00_government_types.txt` | `celestial_government` 的 `government_is_celestial`、`government_has_merit`、`government_has_treasury`、salary budget 标志仍存在；保留公爵以上考核者、全部直属在任官员的原产品谓词。 |
| `common/modifiers/10_tgp_modifiers.txt` | 原版仍使用 `monthly_merit_mult` 与 `monthly_treasury_from_salary_budget_mult`；末位俸禄扣减保留 -25%。 |
| `common/script_values/10_dlc_tgp_china_values.txt` | 现有六种 merit gain/loss 值仍定义；不更改奖惩值或资源语义。 |
| `common/on_action/_on_actions.info`、`yearly_on_actions.txt` | playable pulse 仍为 count+ 且日期依角色；everyone pulse 仍覆盖所有角色。保留失地玩家恢复入口，未把 global flag 当作排队基数证明。 |
| `common/activities/activity_types/feast.txt` | 原版仍有 host/participant、phase active、进度、完成及 header 路径调用形式；京察仅 host 帧结算的原守卫不变。1.20→1.21 feast 的商人邀请和地产评分变化不属于京察依赖，不复制这些无关玩法。 |
| `common/activities/guest_invite_rules/activity_invite_rules.txt`、`intents/shared_intents.txt` | vassals 邀请规则及两个意图仍存在；京察仍只允许实际合格直属官员。 |
| `events/activities/activity_system_events.txt` | 失能取消事件 .0330/.0331 仍存在；不把 stock 事件 ID 存在当作实际取消已经通过。 |
| `gui/shared/buttons.gui`、`portraits.gui`、`windows.gui`、`cooltip.gui`、`coa_designer.gui` | 原控件和 `GetScriptedGui`／`GetVariableSystem` 调用仍有原版定义或真实调用者；不授旧 named-widget ABI 或真实布局通过。 |

本机保留的 1.20.0.4 比对源有 feast，但没有上述 government、modifier、pulse 原件，因此这些项不能宣称逐字节跨版无变化。292 文件的 1.21.0/build26622941 选集中 feast、government_on_actions 与本次安装同 SHA；292 选集不是完整旧安装。其余按当前定义与实际调用者核对，不补造旧原文。

## 软件与发布边界

复用原生成器、`validate_local.py` 与共享 release builder。可选已审原版检查：

```text
python -B mod_zhongguo_style/tools/validate_local.py --game-dir <CK3>/game
```

未提供 `--game-dir` 时仍验证源码合同的严格形状与产品消费者；提供后才额外验证安装目录的已审 14 份源字节。该工具不查询 Game、不验证 EXE 运行映射，也不接受新 Native 能力。具体软件命令、失败、退出码、source/candidate binding 和双构建状态由本轮外置机器回执记录，不能用旧 source commit 充当未提交候选的正式 tag 来源。

0.4.0 的启动、1066 入场及一年兼容窗口，0.4.1 的真实工资说明/即时支付，以及 0.3/phase2 的历史覆盖均保留原版本和机器范围。新增校验不能把旧 405 日、旧 AE2 钱包读回或旧工坊缓存复核转为新版实机通过。新年审、7/14/2、考核榜 ACL/几何、京察 planner/承办/完成或拒绝、薪酬三 hover/25 金真实支付、延期 90/180 日、申诉、保存重载、多人及旧存档状态须逐项按实际结果记账；未执行的全部仍为 NOT_RUN，且未覆盖的旧研究范围不会自动变为本次硬门。

现有 `source-original-core-and-jingcha` case 保留原 398 marker／361 配置断言与 14 自然日上界，不能只以 dispatcher marker 代替活动 UI；`ae2-ui-payment` case 保留同暂停日实际资源收据和原选项身份。旧 Native 987/Full/Actor/named-widget 资格不适用于本机 859F；当前 engine registry 允许制备元数据不等于这些接口可用。实际执行若缺后台 Native 或经授权的 GUI 通道，必须报告缺口，不改 case 谓词、种旗或用效果预览假冒付款/画面。

最终发布仍需正常 Git/tag source、真实完整 builder/manifest/ZIP/cache 验证及本次实际业务验收；本候选没有工坊、GUI、SAVE 或完整产品通过资格。
