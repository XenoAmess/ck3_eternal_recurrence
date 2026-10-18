# 战役评分：离线实现与证据边界

规则：[v1设计](campaign-development-scoring-v1-design-2026-10-19.md)。此实现保留该提案版本和权重，不宣称唯一客观价值标准。公式核在 `ck3_autonomous_player/src/xar_autoplayer/campaign_development_score_v1.py`；只读适配器在 `campaign_score_save_reader.py`；有界定向补提取器在 `campaign_score_target_projection.py`。

## 使用与输出

入口 `ck3_autonomous_player/tools/score_ck3_campaign.py --help`。必要参数：

- `--permanent-receipt`：独立保存的小型来源回执；核对机器及保存文件身份。
- `--baseline-save`、`--baseline-receipt`：真实开局原件及原始来源回执，不由游戏默认历史补造。
- `--decoder`：已核来源的 Rakaly 可执行文件；不自动安装依赖或更改系统配置。
- `--output`、`--metadata-admission`、`--machine-id`：本次已准入的小型输出范围及机器身份。
- `--actor`、`--founder`：当前玩家及固定开局人物；继承后不改 founder。
- `--game-dir`、可重复的 `--landed-titles-source`、`--static-title-map` 三选一：显式指定游戏定义、有效标题定义文件或已固定小映射。不会暗取上一次任务的地图。有效模组覆盖应先解析清楚；冲突省份映射拒绝静默覆盖。

普通入口对当前与开局各执行一次 SAX 流式读取，保留紧凑标量投影，同时取得省份 occupant、宗族单数 `perk` 数组及 `wars.active_wars` 关系。之后只在内存计算县集合和映射，生成本次相关县的小映射。`--interactive` 仅供有 stdin 的工具 PTY 查询，支持 `inspect/export/stop`，不需要桌面焦点；普通批处理无需它。

保存通过 WinAPI `GENERIC_READ / FILE_SHARE_READ` 持有只读锁，拒绝同时写入、删除和重解析点，读前后核对卷、文件ID、大小和mtime。保存全文不落盘，不重新计算整个保存SHA，不修改保护属性。来源SHA标明来自此前回执，不能把身份保持误写成本次重新验SHA。输出 create-only，不覆盖既有结果。

JSON schema 为 `xar.ck3.campaign-development-score/v1`。六域含原始指标、单位、范围、来源、确定值或上下界；`display_steps` 提供中文计算说明。有限十进制的六域加权和可用有理数精确复算，显示区间下界向下、上界向上舍入；不使用中值。缺项保留中文名与英文key，不重新分配权重。

`known_domains_*` 只比较两端**共同确定**的领域，按原权重报告贡献及覆盖率，不把贡献重新放大成总分。宗族传承计入D；已建立支系数只列事实，不另加分。个人属性、个人威望或缓存 `power` 均不代替战役发展或有效军力。

## 本场实际结果

`machine_id: xenoamess-full-tower-eb9d2c1186`。观察时间与每次锁定区间见结果内 sources、`source-custody-02.json`、定向03/04回执。原始开局JSON历史机器ID缺失，保留 `historical_machine_id: unknown`；当前只读观察有明确机器ID。

外置结果根为 `D:/codex-ck3-demos/2026-10-14-robert-30year/continuation42-cold-prep/p50-presentation-prepare01/scoring-draft01`。最终输入：

- `score-result-03.json`：65,583B，SHA256 `be53bcc423a0a02d167f9d79329fe2ac1435234db204483687b50ed63be01ea0`；实际生成 `59e5a5` 退出0。此前draft1与-02保留，不能混称最终输入。
- `targeted-inputs-03.json`：285,581B，SHA256 `e3e30c7e3410abea191b32f5a0de2048f5bae3c980be855e078237b64aedfe45`。取得34省、相关人物与战争/围城小记录；最初宗族selector遗漏被明确记录，未当作“无传承”。
- `targeted-dynasty-04.json`：23,602B，SHA256 `1f699727806299cd39ccfb22675f0f8b07c42b6bf7ed4e45edb1e7d6be636f3f`。修正为实际 `dynasties.dynasties.174` 路径，补足宗族完整小记录。两次定向读取的两份保存解码均退出0，未知token均0，无世界文本落盘。

真实T0为1066.9.15；严格30周年为1096.9.15。保存为1096.9.23，晚8个游戏日，采用CK3固定365日日历。结果资格为 `FINAL_STATE_ONLY`，不能替代准点A_end或完整S30。准点稀疏MET和两份保存不能补成360个月历史。

当前实际统治10→2县，现金239→251.85072金；固定宗族174，支系0→2，已解锁传承0→2级。完成地产的省份记录证明当前两县无occupant，开局十县亦无；当前玩家的唯一战争是反抗领主，不是其自身领地下的叛乱。

L=14.65704486、U=81.82743662、D=42.79127726。共同确定的L/U/D覆盖原权重50%，开局为L50/U100/D40，原权重贡献28.50→18.26569647，变化−10.23430353；这是三域贡献，**不是总分**。财政、军力及合法继承尚缺闭合合同，A_state仅能给18.26569647…68.26569647，S30不可完整计算。

尚缺项分开处理：人物保存的 `alive_data.income`、`landed_data.balance` 已取得，但与Native开局观测并不一致，不能硬当兼容的gross/expenses；完整到期债务及军费没有闭合适配。军力保存有strength/power等缓存及临时部队关系，尚未适配每支常规军的有效伤害/坚韧，不能拿集结人数代替P。保存有succession候选列表，但列表不证明玩家合法后继及备用资格。这里是适配/语义缺口，不声称所有这些信息都根本不在保存中。

## 验证与限制

实际 `02ffab` 退出0：9个聚焦单元测试，包括借债保土/丢半国算例、跨chunk词法、单扫描perk及战争角色、显式静态映射、定向选择、向外区间显示、固定权重共同贡献、重复小数有理加权。`2b8292` CLI帮助退出0。实际最终JSON通过冻结可视化的精确Fraction校验和开局三域重算（`59e5a5`）。未为新版CLI重读保存，也未启动游戏；当前实际结果来源于前述明确记录的旧投影加定向补提取。新入口的单扫描完整保存运行仍待以后获准的实际样本验证。

此线程不生成或检查媒体。评分图片、评分片段及长片头尾合成由独立媒体流程消费固定JSON；不能把JSON已完成写成视频已交付。

## 追加：源码审阅后的边界修正

以上实际03和旧验证回执保持不变。新增纯数据验证 `30b989` 退出0，16项测试通过；本段不代表再次读取真实保存。此前整体测试 `13f6f6` 因CLI导出热重载改变dataclass身份出现两项失败；移除该非必要热重载后通过，保留失败事实。

完整财政/军力/合法继承输入现在生成对应实际公式说明，只有真实缺项才显示缺项；L明示 `max(开局,1)`，现金下降不产生“+-”。日期不齐或晚到的状态不能以 `strict_endpoint_verified=True` 冒充准点A_end。

CLI核包内canonical当前机器ID、卡schema/owner/status、实际有效期和输出根；每次新写前后检查本namespace累计逻辑大小，拒绝重解析点。所有派生输出均含attempt-id，旧报告不覆盖。整体fixture直接调用CLI main，以小保存投影stub替代两次解码，验证每源一次、自动映射、导出及L/U/D确定域和原权重贡献；尚未把新版入口的真实保存运行当作通过。

重复scalar的nonunique标记保持不消失；重复occupant不被当作“无占领”；字段帽命中直接拒绝，不再静默丢尾部字段。重复角色或定向实体拒绝；定向空记录、路径、根容器和嵌套深度均有帽。支持根层active_wars，未知战争容器不能证明无本国叛乱。CRLF注释与UTF-8在1/2/17字节分块均有合法用例。实际03相关省份、战争和宗族小记录另由并行审计核对，不将通用负例冒充当前保存已发生的数据错误。

## 追加：真实历史人物重复的处理

Root在 `machine_id: xenoamess-full-tower-eb9d2c1186` 实际运行入口attempt05，当前保存首扫遇历史角色40982在dead_unprunable重复，`98853d`外层退出1，未产评分输出；观察时间以该Root回执为准。本线程没有重读保存。该失败说明“任意世界角色ID重复即中断”的旧修复不适合真实保存格式，以上拒绝规则由本段更正，不覆盖失败事实或03。

普通投影现在仅对不属于wanted的角色比较评分所需house：重复值完全一致（包括同为无house）安全合并，计入重复审计；冲突及后续第三次重复保持sticky unknown。wanted当前玩家/开局人物重复时，清掉角色正文与house，明确未知，不任选钱包或身份。定向完整记录投影仍拒绝重复。

县持有人house不确定时，宗族土地K和宗族县计数未知，不能当作宗族外0；已知title chain的领地品质仍可独立计算。H0/D0只从真实T0确定，并附baseline_save来源后注入current；当前死者记录重复不会重设或替换已知开局锚，开局本身不唯一时则保留未知。复用地理映射时清除旧场锚。上述合并、三次冲突、wanted钱包未知、县holder传播及T0锚均有小型回归；不宣称修后真实入口已运行。

本次纯数据回归 `d1d76e` 退出0，17项测试通过；源码及后续固定pins见追加最终校验回执。

## 追加：玩家当前战争范围与小缓存回放

Root实际入口06（本文件同一machine_id，`94b0c1`退出0）已对当前/T0各完整读取一次，未知token为0；L/D与03一致。U仍给41.8274…81.8274，因为当时守卫要求世界95条战争都具有CB defender，历史/空壳记录扩大了不确定范围。06较宽结果保留，不改写。

新增纯函数 `player_war_defence` 只读取明确的 `landed_data.wars`；不混用 `alive_data.wars` 计数。每个列出ID必须找到战争投影及唯一CB defender，才判断玩家是否为本国内战的被反抗者。缺失、截断、重复列表、缺war、CB冲突均未知；显式空数组必须有parser的presence证据。完全没有玩家列表时，只有独立完整世界战争清单的全部CB均可核，才保留该既有证明路径；这不是将缺列表当空，有列表但无效时不走后备。detail记录采用哪一种方法。

`50fd92`纯测试18项通过，main整体fixture包含无关世界空壳，仍能凭合法玩家范围得到确定U；缺项和冲突负例均不会被归零。

最终追加 `aa58d0` 的18项测试通过，独立世界清单后备也拒绝非数字或nonunique的CB defender，不以该后备绕开列表冲突。

小缓存实算 `0975a6`退出0：`player-war-scope-cache-replay-07.json`，4,061B，SHA256 `c9b20536977237d55e27312175c5e182877f283c1832bae1efad37af2329ff94`。回放核06与target03的current保存卷/文件ID/大小/mtime前后相同、解码退出0和未知0，再将82925唯一列表184549379与target03唯一CB defender36445绑定。只更新current rebel_share=0，baseline沿用06原先实际观测；L/U/D及A区间与03严格Decimal相等，U=81.8274366197。输入pins、步骤、窄war投影均在回执中，未写替代整份评分报告或改电影03，更未读取SAVE。以后可用该方案离线重算，无需再次整场扫描。

## Root 独立复核补注

`machine_id: xenoamess-full-tower-eb9d2c1186`；复核记录UTC 2026-10-18T20:41:41.385330+00:00。Root 实际 `068425`：18 项单元测试退出0，并重新核对缓存回放引用的五份小 JSON 的大小及 SHA。`19a3be`：通用图片/视频入口的纯检查退出0，没有生成额外媒体。真实整链读取为 session86989、`94b0c1` 退出0；最后的玩家战争列表改进另以同存档身份的小输入回放验证，未重复扫描保存。媒体合成资格和最终交付仍由各自实际回执证明。
