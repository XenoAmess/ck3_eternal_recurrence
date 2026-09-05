# 361 机制实现映射

> GENERATED FILE — edit the numbered design document, reviewed choice JSON, acceptance-contract JSON, domain data, or `tools/zg361_readiness_data.py`.

状态口径：361 项目录文案为 `complete`；参考政策配置和共享账本投影为 `fixture-live`；
361/361 已有 `contract-complete` 的领域/状态/操作/期限/事务/反馈设计合同；这不等于游戏实现。
当前累计门为 Python L0 `361/361`、CK3 static `361/361`、central-wired `361/361`、bounded fixture-live `4/361`。
`central-wired` 只表示中央产品 hook 可达，不表示逐号语义完整；#018 只有 receipt/refund 为 fixture-live，`.53` 重开仍为 static-ready。
旧 361 政策卡与共享账本 fixture 只证明配置投影，不得提升领域运行时。完整分层见 `361-phase2-coverage-ledger.md`。

| ID | 机制 | 组 | P | Profile | 玩家入口 | AI 入口 | 同批逻辑组 | 目录 | 配置 | 账本 | 运行设计 | 领域 | 玩家闭环 | 最高证据 |
|---:|---|---|---|---|---|---|---:|---|---|---|---|---|---|---|
| 001 | KPI 分项证据单 | A | P0 | `assessment` | `zg361m.1` | `zg361_mechanism_001_ai_effect` | 1 | complete | fixture-live | fixture-live | contract-complete | partial | partial | `ck3-live` |
| 002 | 年度目标责任书：OKR 方向 + KPI 结果 | A | P0 | `assessment` | `zg361m.2` | `zg361_mechanism_002_ai_effect` | 1 | complete | fixture-live | fixture-live | contract-complete | partial | partial | `central-wired` |
| 003 | 期中 Check-in 与目标重置 | A | P1 | `assessment` | `zg361m.3` | `zg361_mechanism_003_ai_effect` | 1 | complete | fixture-live | fixture-live | contract-complete | partial | partial | `central-wired` |
| 004 | 自评与认知差 | A | P1 | `assessment` | `zg361m.4` | `zg361_mechanism_004_ai_effect` | 1 | complete | fixture-live | fixture-live | contract-complete | partial | partial | `central-wired` |
| 005 | 岗位化记分卡 | A | P1 | `assessment` | `zg361m.5` | `zg361_mechanism_005_ai_effect` | 1 | complete | fixture-live | fixture-live | contract-complete | partial | partial | `central-wired` |
| 006 | 起点与难度校正 | A | P2 | `assessment` | `zg361m.6` | `zg361_mechanism_006_ai_effect` | 1 | complete | fixture-live | fixture-live | contract-complete | partial | partial | `central-wired` |
| 007 | 背靠背 360 邀评 | B | P0 | `calibration` | `zg361m.7` | `zg361_mechanism_007_ai_effect` | 1 | complete | fixture-live | fixture-live | contract-complete | partial | partial | `central-wired` |
| 008 | 评价者“手松手紧”与同侪信用 | B | P1 | `calibration` | `zg361m.8` | `zg361_mechanism_008_ai_effect` | 1 | complete | fixture-live | fixture-live | contract-complete | partial | partial | `central-wired` |
| 009 | 校准会驾驶舱 | B | P0 | `calibration` | `zg361m.9` | `zg361_mechanism_009_ai_effect` | 1 | complete | fixture-live | fixture-live | contract-complete | partial | partial | `central-wired` |
| 010 | “背 C”与护人 | B | P0 | `calibration` | `zg361m.10` | `zg361_mechanism_010_ai_effect` | 1 | complete | fixture-live | fixture-live | contract-complete | partial | partial | `central-wired` |
| 011 | 隔级校准 / HR 政委席 | B | P1 | `governance` | `zg361m.11` | `zg361_mechanism_011_ai_effect` | 1 | complete | fixture-live | fixture-live | contract-complete | partial | partial | `central-wired` |
| 012 | 利益冲突与回避 | B | P1 | `calibration` | `zg361m.12` | `zg361_mechanism_012_ai_effect` | 1 | complete | fixture-live | fixture-live | contract-complete | partial | partial | `central-wired` |
| 013 | 透明 / 半透明 / 黑箱公示制度 | B | P2 | `governance` | `zg361m.13` | `zg361_mechanism_013_ai_effect` | 1 | complete | fixture-live | fixture-live | contract-complete | partial | partial | `central-wired` |
| 014 | 绩效申诉案卷 | C | P0 | `governance` | `zg361m.14` | `zg361_mechanism_014_ai_effect` | 1 | complete | fixture-live | fixture-live | contract-complete | partial | partial | `central-wired` |
| 015 | PIP 改进任务书 | C | P0 | `pip` | `zg361m.15` | `zg361_mechanism_015_ai_effect` | 1 | complete | fixture-live | fixture-live | contract-complete | partial | partial | `central-wired` |
| 016 | PIP 支持预算与“只给指标不给资源” | C | P1 | `pip` | `zg361m.16` | `zg361_mechanism_016_ai_effect` | 1 | complete | fixture-live | fixture-live | contract-complete | partial | partial | `central-wired` |
| 017 | 末位处置阶梯 | C | P0 | `pip` | `zg361m.17` | `zg361_mechanism_017_ai_effect` | 1 | complete | fixture-live | fixture-live | contract-complete | partial | partial | `central-wired` |
| 018 | 个人告身与四重后果清算单 | C | P0 | `assessment` | `zg361m.18` | `zg361_mechanism_018_ai_effect` | 1 | complete | fixture-live | fixture-live | contract-complete | partial | partial | `ck3-live` |
| 019 | 晋升资格门槛 | D | P0 | `promotion` | `zg361m.19` | `zg361_mechanism_019_ai_effect` | 2 | complete | fixture-live | fixture-live | contract-complete | partial | partial | `central-wired` |
| 020 | 晋升包与跨部门答辩 | D | P1 | `promotion` | `zg361m.20` | `zg361_mechanism_020_ai_effect` | 2 | complete | fixture-live | fixture-live | contract-complete | partial | partial | `central-wired` |
| 021 | 奖金—调薪矩阵 | D | P1 | `compensation` | `zg361m.21` | `zg361_mechanism_021_ai_effect` | 2 | complete | fixture-live | fixture-live | contract-complete | partial | partial | `central-wired` |
| 022 | 软 HC / 编制预算 | D | P1 | `hc` | `zg361m.22` | `zg361_mechanism_022_ai_effect` | 2 | complete | fixture-live | fixture-live | contract-complete | partial | partial | `central-wired` |
| 023 | HC 答辩与团队投入产出 | D | P1 | `hc` | `zg361m.23` | `zg361_mechanism_023_ai_effect` | 2 | complete | fixture-live | fixture-live | contract-complete | partial | partial | `central-wired` |
| 024 | 内部活水与转岗博弈 | D | P1 | `organization` | `zg361m.24` | `zg361_mechanism_024_ai_effect` | 2 | complete | fixture-live | fixture-live | contract-complete | partial | partial | `central-wired` |
| 025 | 高绩效人才被挖与反 offer | D | P2 | `promotion` | `zg361m.25` | `zg361_mechanism_025_ai_effect` | 2 | complete | fixture-live | fixture-live | contract-complete | partial | partial | `central-wired` |
| 026 | 真实贡献 / 上司可见度双账 | E | P0 | `assessment` | `zg361m.26` | `zg361_mechanism_026_ai_effect` | 3 | complete | fixture-live | fixture-live | contract-complete | partial | partial | `central-wired` |
| 027 | 跨部门贡献账本 | E | P1 | `governance` | `zg361m.27` | `zg361_mechanism_027_ai_effect` | 3 | complete | fixture-live | fixture-live | contract-complete | partial | partial | `central-wired` |
| 028 | 抢功仲裁 / 甩锅复盘 | E | P1 | `governance` | `zg361m.28` | `zg361_mechanism_028_ai_effect` | 3 | complete | fixture-live | fixture-live | contract-complete | partial | partial | `central-wired` |
| 029 | 指标包装、造假与京察审计 | E | P1 | `data` | `zg361m.29` | `zg361_mechanism_029_ai_effect` | 3 | complete | fixture-live | fixture-live | contract-complete | partial | partial | `central-wired` |
| 030 | 资源赛马与抢预算 | E | P2 | `hc` | `zg361m.30` | `zg361_mechanism_030_ai_effect` | 3 | complete | fixture-live | fixture-live | contract-complete | partial | partial | `central-wired` |
| 031 | 恩主 / Sponsor 网络 | E | P2 | `promotion` | `zg361m.31` | `zg361_mechanism_031_ai_effect` | 3 | complete | fixture-live | fixture-live | contract-complete | partial | partial | `central-wired` |
| 032 | 管理者自己的团队绩效 | F | P0 | `assessment` | `zg361m.32` | `zg361_mechanism_032_ai_effect` | 4 | complete | fixture-live | fixture-live | contract-complete | partial | partial | `central-wired` |
| 033 | 管理者画像与可解释理由码 | F | P0 | `governance` | `zg361m.33` | `zg361_mechanism_033_ai_effect` | 4 | complete | fixture-live | fixture-live | contract-complete | partial | partial | `central-wired` |
| 034 | 绩效×潜力九宫格 | F | P1 | `promotion` | `zg361m.34` | `zg361_mechanism_034_ai_effect` | 2 | complete | fixture-live | fixture-live | contract-complete | partial | partial | `central-wired` |
| 035 | 严格 361 / 松绑 361 / 混合门槛 | F | P2 | `calibration` | `zg361m.35` | `zg361_mechanism_035_ai_effect` | 4 | complete | fixture-live | fixture-live | contract-complete | partial | partial | `central-wired` |
| 036 | 十年制度报告 | F | P2 | `governance` | `zg361m.36` | `zg361_mechanism_036_ai_effect` | 4 | complete | fixture-live | fixture-live | contract-complete | partial | partial | `central-wired` |
| 037 | 跨团队配额互换 | G | P1 | `calibration` | `zg361m.37` | `zg361_mechanism_037_ai_effect` | 1 | complete | fixture-live | fixture-live | contract-complete | partial | partial | `central-wired` |
| 038 | 小样本合池校准 | G | P1 | `calibration` | `zg361m.38` | `zg361_mechanism_038_ai_effect` | 1 | complete | fixture-live | fixture-live | contract-complete | partial | partial | `central-wired` |
| 039 | 分母管理与名单锁定 | G | P1 | `calibration` | `zg361m.39` | `zg361_mechanism_039_ai_effect` | 1 | complete | fixture-live | fixture-live | contract-complete | partial | partial | `central-wired` |
| 040 | “离职者背 C”灰色操作 | G | P1 | `calibration` | `zg361m.40` | `zg361_mechanism_040_ai_effect` | 1 | complete | fixture-live | fixture-live | contract-complete | partial | partial | `central-wired` |
| 041 | 新人保护、参评与献祭三路线 | G | P1 | `calibration` | `zg361m.41` | `zg361_mechanism_041_ai_effect` | 1 | complete | fixture-live | fixture-live | contract-complete | partial | partial | `central-wired` |
| 042 | 轮流背 C 的跨周期合谋 | G | P2 | `calibration` | `zg361m.42` | `zg361_mechanism_042_ai_effect` | 1 | complete | fixture-live | fixture-live | contract-complete | partial | partial | `central-wired` |
| 043 | 校准会发言席与注意力预算 | G | P1 | `calibration` | `zg361m.43` | `zg361_mechanism_043_ai_effect` | 1 | complete | fixture-live | fixture-live | contract-complete | partial | partial | `central-wired` |
| 044 | 盲审初排、实名复议 | G | P2 | `calibration` | `zg361m.44` | `zg361_mechanism_044_ai_effect` | 1 | complete | fixture-live | fixture-live | contract-complete | partial | partial | `central-wired` |
| 045 | “不得惊讶”反馈债 | G | P1 | `assessment` | `zg361m.45` | `zg361_mechanism_045_ai_effect` | 1 | complete | fixture-live | fixture-live | contract-complete | partial | partial | `central-wired` |
| 046 | 机会分配审计 | G | P1 | `governance` | `zg361m.46` | `zg361_mechanism_046_ai_effect` | 1 | complete | fixture-live | fixture-live | contract-complete | partial | partial | `central-wired` |
| 047 | 近因偏差与证据时间窗 | G | P2 | `assessment` | `zg361m.47` | `zg361_mechanism_047_ai_effect` | 1 | complete | fixture-live | fixture-live | contract-complete | partial | partial | `central-wired` |
| 048 | 评价者工时与邀评额度 | H | P1 | `workload` | `zg361m.48` | `zg361_mechanism_048_ai_effect` | 1 | complete | fixture-live | fixture-live | contract-complete | partial | partial | `central-wired` |
| 049 | 封存提交与截止时点 | H | P1 | `calibration` | `zg361m.49` | `zg361_mechanism_049_ai_effect` | 1 | complete | fixture-live | fixture-live | contract-complete | partial | partial | `central-wired` |
| 050 | 互相抬轿契约与背叛 | H | P1 | `calibration` | `zg361m.50` | `zg361_mechanism_050_ai_effect` | 1 | complete | fixture-live | fixture-live | contract-complete | partial | partial | `central-wired` |
| 051 | 可推断匿名与最小样本阈值 | H | P1 | `governance` | `zg361m.51` | `zg361_mechanism_051_ai_effect` | 1 | complete | fixture-live | fixture-live | contract-complete | partial | partial | `central-wired` |
| 052 | 保留评价形状，不只看均分 | H | P1 | `assessment` | `zg361m.52` | `zg361_mechanism_052_ai_effect` | 1 | complete | fixture-live | fixture-live | contract-complete | partial | partial | `central-wired` |
| 053 | 360 只作发展、不入奖金的制度路线 | H | P2 | `calibration` | `zg361m.53` | `zg361_mechanism_053_ai_effect` | 1 | complete | fixture-live | fixture-live | contract-complete | partial | partial | `central-wired` |
| 054 | 汇报工时挤占真实产出 | I | P1 | `workload` | `zg361m.54` | `zg361_mechanism_054_ai_effect` | 3 | complete | fixture-live | fixture-live | contract-complete | partial | partial | `central-wired` |
| 055 | 上司注意力席位 | I | P1 | `governance` | `zg361m.55` | `zg361_mechanism_055_ai_effect` | 3 | complete | fixture-live | fixture-live | contract-complete | partial | partial | `central-wired` |
| 056 | 逐级汇报中的截功 | I | P1 | `organization` | `zg361m.56` | `zg361_mechanism_056_ai_effect` | 3 | complete | fixture-live | fixture-live | contract-complete | partial | partial | `central-wired` |
| 057 | 贡献留痕与版本签名 | I | P1 | `data` | `zg361m.57` | `zg361_mechanism_057_ai_effect` | 3 | complete | fixture-live | fixture-live | contract-complete | partial | partial | `central-wired` |
| 058 | 越级抄送（CC）与信息政治 | I | P1 | `governance` | `zg361m.58` | `zg361_mechanism_058_ai_effect` | 3 | complete | fixture-live | fixture-live | contract-complete | partial | partial | `central-wired` |
| 059 | 坏消息早报、迟报与隐瞒 | I | P1 | `incident` | `zg361m.59` | `zg361_mechanism_059_ai_effect` | 3 | complete | fixture-live | fixture-live | contract-complete | partial | partial | `central-wired` |
| 060 | 材料泄露与创意窃取 | I | P2 | `governance` | `zg361m.60` | `zg361_mechanism_060_ai_effect` | 3 | complete | fixture-live | fixture-live | contract-complete | partial | partial | `central-wired` |
| 061 | 短文档 / 长叙事汇报制度 | I | P2 | `workload` | `zg361m.61` | `zg361_mechanism_061_ai_effect` | 3 | complete | fixture-live | fixture-live | contract-complete | partial | partial | `central-wired` |
| 062 | 实线与虚线目标冲突 | J | P1 | `organization` | `zg361m.62` | `zg361_mechanism_062_ai_effect` | 3 | complete | fixture-live | fixture-live | contract-complete | partial | partial | `central-wired` |
| 063 | 周期初权重契约 | J | P1 | `governance` | `zg361m.63` | `zg361_mechanism_063_ai_effect` | 3 | complete | fixture-live | fixture-live | contract-complete | partial | partial | `central-wired` |
| 064 | 换老板交接双签 | J | P1 | `organization` | `zg361m.64` | `zg361_mechanism_064_ai_effect` | 3 | complete | fixture-live | fixture-live | contract-complete | partial | partial | `central-wired` |
| 065 | 空降主管与旧部包 | J | P2 | `organization` | `zg361m.65` | `zg361_mechanism_065_ai_effect` | 3 | complete | fixture-live | fixture-live | contract-complete | partial | partial | `central-wired` |
| 066 | 项目取消：业务失败与个人失败分离 | J | P1 | `assessment` | `zg361m.66` | `zg361_mechanism_066_ai_effect` | 3 | complete | fixture-live | fixture-live | contract-complete | partial | partial | `central-wired` |
| 067 | 合并后“一岗两人” | J | P2 | `organization` | `zg361m.67` | `zg361_mechanism_067_ai_effect` | 3 | complete | fixture-live | fixture-live | contract-complete | partial | partial | `central-wired` |
| 068 | 可携带履历与本地重新证明 | J | P1 | `organization` | `zg361m.68` | `zg361_mechanism_068_ai_effect` | 3 | complete | fixture-live | fixture-live | contract-complete | partial | partial | `central-wired` |
| 069 | 正式送达与申诉时钟 | K | P0 | `governance` | `zg361m.69` | `zg361_mechanism_069_ai_effect` | 1 | complete | fixture-live | fixture-live | contract-complete | partial | partial | `ck3-live` |
| 070 | 申诉后的反报复观察期 | K | P1 | `governance` | `zg361m.70` | `zg361_mechanism_070_ai_effect` | 1 | complete | fixture-live | fixture-live | contract-complete | partial | partial | `central-wired` |
| 071 | 内部论坛长文与公开升级 | K | P2 | `governance` | `zg361m.71` | `zg361_mechanism_071_ai_effect` | 1 | complete | fixture-live | fixture-live | contract-complete | partial | partial | `central-wired` |
| 072 | 提前泄露绩效档位 | K | P1 | `governance` | `zg361m.72` | `zg361_mechanism_072_ai_effect` | 1 | complete | fixture-live | fixture-live | contract-complete | partial | partial | `central-wired` |
| 073 | 恶意泄密与善意吹哨分流 | K | P1 | `governance` | `zg361m.73` | `zg361_mechanism_073_ai_effect` | 1 | complete | fixture-live | fixture-live | contract-complete | partial | partial | `central-wired` |
| 074 | 诚实裁撤与“洗成绩裁人” | K | P1 | `compensation` | `zg361m.74` | `zg361_mechanism_074_ai_effect` | 1 | complete | fixture-live | fixture-live | contract-complete | partial | partial | `central-wired` |
| 075 | 保履历自愿离开包 | K | P2 | `compensation` | `zg361m.75` | `zg361_mechanism_075_ai_effect` | 1 | complete | fixture-live | fixture-live | contract-complete | partial | partial | `central-wired` |
| 076 | 程序失败的多级责任 | K | P1 | `governance` | `zg361m.76` | `zg361_mechanism_076_ai_effect` | 1 | complete | fixture-live | fixture-live | contract-complete | partial | partial | `central-wired` |
| 077 | 独立复核人轮换 | K | P1 | `governance` | `zg361m.77` | `zg361_mechanism_077_ai_effect` | 1 | complete | fixture-live | fixture-live | contract-complete | partial | partial | `central-wired` |
| 078 | 分布公平性仪表盘 | K | P2 | `data` | `zg361m.78` | `zg361_mechanism_078_ai_effect` | 1 | complete | fixture-live | fixture-live | contract-complete | partial | partial | `central-wired` |
| 079 | 隔级接待日 | K | P2 | `governance` | `zg361m.79` | `zg361_mechanism_079_ai_effect` | 1 | complete | fixture-live | fixture-live | contract-complete | partial | partial | `central-wired` |
| 080 | 公开指标缺陷单 | K | P1 | `data` | `zg361m.80` | `zg361_mechanism_080_ai_effect` | 1 | complete | fixture-live | fixture-live | contract-complete | partial | partial | `central-wired` |
| 081 | 绩效信息层级压缩 | K | P2 | `governance` | `zg361m.81` | `zg361_mechanism_081_ai_effect` | 1 | complete | fixture-live | fixture-live | contract-complete | partial | partial | `central-wired` |
| 082 | 总回报配方 | L | P1 | `compensation` | `zg361m.82` | `zg361_mechanism_082_ai_effect` | 2 | complete | fixture-live | fixture-live | contract-complete | partial | partial | `central-wired` |
| 083 | 公司—团队—个人三层奖金系数 | L | P1 | `compensation` | `zg361m.83` | `zg361_mechanism_083_ai_effect` | 2 | complete | fixture-live | fixture-live | contract-complete | partial | partial | `central-wired` |
| 084 | 递延奖金与分期归属 | L | P2 | `compensation` | `zg361m.84` | `zg361_mechanism_084_ai_effect` | 2 | complete | fixture-live | fixture-live | contract-complete | partial | partial | `central-wired` |
| 085 | 续期激励断崖 | L | P2 | `compensation` | `zg361m.85` | `zg361_mechanism_085_ai_effect` | 2 | complete | fixture-live | fixture-live | contract-complete | partial | partial | `central-wired` |
| 086 | 奖金暂扣与追索 | L | P1 | `compensation` | `zg361m.86` | `zg361_mechanism_086_ai_effect` | 2 | complete | fixture-live | fixture-live | contract-complete | partial | partial | `central-wired` |
| 087 | 薪酬带宽与带内位置 | L | P1 | `compensation` | `zg361m.87` | `zg361_mechanism_087_ai_effect` | 2 | complete | fixture-live | fixture-live | contract-complete | partial | partial | `central-wired` |
| 088 | 市场调薪与绩效调薪争预算 | L | P1 | `compensation` | `zg361m.88` | `zg361_mechanism_088_ai_effect` | 2 | complete | fixture-live | fixture-live | contract-complete | partial | partial | `central-wired` |
| 089 | 职级、任命、权力与现金解耦 | L | P1 | `promotion` | `zg361m.89` | `zg361_mechanism_089_ai_effect` | 2 | complete | fixture-live | fixture-live | contract-complete | partial | partial | `central-wired` |
| 090 | 专项即时奖 | L | P1 | `compensation` | `zg361m.90` | `zg361_mechanism_090_ai_effect` | 2 | complete | fixture-live | fixture-live | contract-complete | partial | partial | `central-wired` |
| 091 | 年功奖与绩效奖分账 | L | P2 | `compensation` | `zg361m.91` | `zg361_mechanism_091_ai_effect` | 2 | complete | fixture-live | fixture-live | contract-complete | partial | partial | `central-wired` |
| 092 | 专业 / 管理双通道 | M | P1 | `promotion` | `zg361m.92` | `zg361_mechanism_092_ai_effect` | 2 | complete | fixture-live | fixture-live | contract-complete | partial | partial | `central-wired` |
| 093 | 失败经理回归专家岗 | M | P1 | `promotion` | `zg361m.93` | `zg361_mechanism_093_ai_effect` | 2 | complete | fixture-live | fixture-live | contract-complete | partial | partial | `central-wired` |
| 094 | 微职级与“升半级”缓冲 | M | P2 | `promotion` | `zg361m.94` | `zg361_mechanism_094_ai_effect` | 2 | complete | fixture-live | fixture-live | contract-complete | partial | partial | `central-wired` |
| 095 | 高级管理任命年度复审 | M | P1 | `governance` | `zg361m.95` | `zg361_mechanism_095_ai_effect` | 2 | complete | fixture-live | fixture-live | contract-complete | partial | partial | `central-wired` |
| 096 | 破格晋升包 | M | P2 | `promotion` | `zg361m.96` | `zg361_mechanism_096_ai_effect` | 2 | complete | fixture-live | fixture-live | contract-complete | partial | partial | `central-wired` |
| 097 | 跨团队晋升校准 | M | P1 | `promotion` | `zg361m.97` | `zg361_mechanism_097_ai_effect` | 2 | complete | fixture-live | fixture-live | contract-complete | partial | partial | `central-wired` |
| 098 | 增长、补缺、项目三类 HC | N | P1 | `hc` | `zg361m.98` | `zg361_mechanism_098_ai_effect` | 2 | complete | fixture-live | fixture-live | contract-complete | partial | partial | `central-wired` |
| 099 | HC 到期、结转与年底突击招募 | N | P1 | `hc` | `zg361m.99` | `zg361_mechanism_099_ai_effect` | 2 | complete | fixture-live | fixture-live | contract-complete | partial | partial | `central-wired` |
| 100 | 冻结期与关键岗位特批 | N | P1 | `hc` | `zg361m.100` | `zg361_mechanism_100_ai_effect` | 2 | complete | fixture-live | fixture-live | contract-complete | partial | partial | `central-wired` |
| 101 | 一个资深 / 两个普通 / 学徒梯队 | N | P1 | `hc` | `zg361m.101` | `zg361_mechanism_101_ai_effect` | 2 | complete | fixture-live | fixture-live | contract-complete | partial | partial | `central-wired` |
| 102 | 零基编制重审 | N | P2 | `hc` | `zg361m.102` | `zg361_mechanism_102_ai_effect` | 2 | complete | fixture-live | fixture-live | contract-complete | partial | partial | `central-wired` |
| 103 | 空编占坑审计 | N | P1 | `hc` | `zg361m.103` | `zg361_mechanism_103_ai_effect` | 2 | complete | fixture-live | fixture-live | contract-complete | partial | partial | `central-wired` |
| 104 | 新人池 / 成熟人才池之争 | N | P2 | `hc` | `zg361m.104` | `zg361_mechanism_104_ai_effect` | 2 | complete | fixture-live | fixture-live | contract-complete | partial | partial | `central-wired` |
| 105 | 离任后的 backfill 归属 | N | P1 | `hc` | `zg361m.105` | `zg361_mechanism_105_ai_effect` | 2 | complete | fixture-live | fixture-live | contract-complete | partial | partial | `central-wired` |
| 106 | 关键岗位与关键人才分离 | O | P1 | `organization` | `zg361m.106` | `zg361_mechanism_106_ai_effect` | 2 | complete | fixture-live | fixture-live | contract-complete | partial | partial | `central-wired` |
| 107 | 继任准备度阶梯 | O | P1 | `learning` | `zg361m.107` | `zg361_mechanism_107_ai_effect` | 2 | complete | fixture-live | fixture-live | contract-complete | partial | partial | `central-wired` |
| 108 | 代理任职试炼 | O | P1 | `learning` | `zg361m.108` | `zg361_mechanism_108_ai_effect` | 2 | complete | fixture-live | fixture-live | contract-complete | partial | partial | `central-wired` |
| 109 | 高潜标签的公开层级 | O | P2 | `promotion` | `zg361m.109` | `zg361_mechanism_109_ai_effect` | 2 | complete | fixture-live | fixture-live | contract-complete | partial | partial | `central-wired` |
| 110 | 潜力校准与绩效校准分会 | O | P1 | `promotion` | `zg361m.110` | `zg361_mechanism_110_ai_effect` | 2 | complete | fixture-live | fixture-live | contract-complete | partial | partial | `central-wired` |
| 111 | 遗憾流失与健康流失分类 | O | P1 | `organization` | `zg361m.111` | `zg361_mechanism_111_ai_effect` | 2 | complete | fixture-live | fixture-live | contract-complete | partial | partial | `central-wired` |
| 112 | 留任访谈（Stay Interview） | O | P1 | `organization` | `zg361m.112` | `zg361_mechanism_112_ai_effect` | 2 | complete | fixture-live | fixture-live | contract-complete | partial | partial | `central-wired` |
| 113 | 关键人依赖与知识移交 | O | P1 | `learning` | `zg361m.113` | `zg361_mechanism_113_ai_effect` | 2 | complete | fixture-live | fixture-live | contract-complete | partial | partial | `central-wired` |
| 114 | 经理“人才输出”积分 | P | P1 | `organization` | `zg361m.114` | `zg361_mechanism_114_ai_effect` | 2 | complete | fixture-live | fixture-live | contract-complete | partial | partial | `central-wired` |
| 115 | 匿名内部应聘 | P | P1 | `organization` | `zg361m.115` | `zg361_mechanism_115_ai_effect` | 2 | complete | fixture-live | fixture-live | contract-complete | partial | partial | `central-wired` |
| 116 | 放人时限与一次交接延期 | P | P1 | `organization` | `zg361m.116` | `zg361_mechanism_116_ai_effect` | 2 | complete | fixture-live | fixture-live | contract-complete | partial | partial | `central-wired` |
| 117 | 转岗爬坡保护期 | P | P1 | `learning` | `zg361m.117` | `zg361_mechanism_117_ai_effect` | 2 | complete | fixture-live | fixture-live | contract-complete | partial | partial | `central-wired` |
| 118 | 试用期绝对门槛，不占末位配额 | P | P1 | `assessment` | `zg361m.118` | `zg361_mechanism_118_ai_effect` | 2 | complete | fixture-live | fixture-live | contract-complete | partial | partial | `central-wired` |
| 119 | 招聘质量回写 | P | P1 | `hc` | `zg361m.119` | `zg361_mechanism_119_ai_effect` | 2 | complete | fixture-live | fixture-live | contract-complete | partial | partial | `central-wired` |
| 120 | 导师与 onboarding 绩效 | P | P1 | `learning` | `zg361m.120` | `zg361_mechanism_120_ai_effect` | 2 | complete | fixture-live | fixture-live | contract-complete | partial | partial | `central-wired` |
| 121 | 首次任经理试运行 | Q | P1 | `learning` | `zg361m.121` | `zg361_mechanism_121_ai_effect` | 3 | complete | fixture-live | fixture-live | contract-complete | partial | partial | `central-wired` |
| 122 | 管理者 4-3-3 记分卡 | Q | P1 | `assessment` | `zg361m.122` | `zg361_mechanism_122_ai_effect` | 3 | complete | fixture-live | fixture-live | contract-complete | partial | partial | `central-wired` |
| 123 | 下属评经理专表 | Q | P1 | `assessment` | `zg361m.123` | `zg361_mechanism_123_ai_effect` | 3 | complete | fixture-live | fixture-live | contract-complete | partial | partial | `central-wired` |
| 124 | “先有接班人，才升经理” | Q | P1 | `promotion` | `zg361m.124` | `zg361_mechanism_124_ai_effect` | 3 | complete | fixture-live | fixture-live | contract-complete | partial | partial | `central-wired` |
| 125 | 亲自救火与授权取舍 | Q | P1 | `organization` | `zg361m.125` | `zg361_mechanism_125_ai_effect` | 3 | complete | fixture-live | fixture-live | contract-complete | partial | partial | `central-wired` |
| 126 | 绩效 × 价值观处置矩阵 | Q | P1 | `assessment` | `zg361m.126` | `zg361_mechanism_126_ai_effect` | 3 | complete | fixture-live | fixture-live | contract-complete | partial | partial | `central-wired` |
| 127 | 管理幅度与评分失真 | Q | P2 | `organization` | `zg361m.127` | `zg361_mechanism_127_ai_effect` | 3 | complete | fixture-live | fixture-live | contract-complete | partial | partial | `central-wired` |
| 128 | 强制分布气候指标 | Q | P2 | `organization` | `zg361m.128` | `zg361_mechanism_128_ai_effect` | 3 | complete | fixture-live | fixture-live | contract-complete | partial | partial | `central-wired` |
| 129 | 晋升排队与职业平台期 | R | P1 | `promotion` | `zg361m.129` | `zg361_mechanism_129_ai_effect` | 2 | complete | fixture-live | fixture-live | contract-complete | partial | partial | `central-wired` |
| 130 | 把低绩效“倾倒”给别组 | R | P1 | `organization` | `zg361m.130` | `zg361_mechanism_130_ai_effect` | 2 | complete | fixture-live | fixture-live | contract-complete | partial | partial | `central-wired` |
| 131 | 探索型 OKR 与承诺型 KPI 双赛道 | R | P1 | `delivery` | `zg361m.131` | `zg361_mechanism_131_ai_effect` | 3 | complete | fixture-live | fixture-live | contract-complete | partial | partial | `central-wired` |
| 132 | 及时砍项目也算功 | R | P1 | `delivery` | `zg361m.132` | `zg361_mechanism_132_ai_effect` | 3 | complete | fixture-live | fixture-live | contract-complete | partial | partial | `central-wired` |
| 133 | 无责复盘与有责追究分轨 | R | P1 | `incident` | `zg361m.133` | `zg361_mechanism_133_ai_effect` | 3 | complete | fixture-live | fixture-live | contract-complete | partial | partial | `central-wired` |
| 134 | 共享指标的唯一 owner 与仲裁 | R | P1 | `governance` | `zg361m.134` | `zg361_mechanism_134_ai_effect` | 3 | complete | fixture-live | fixture-live | contract-complete | partial | partial | `central-wired` |
| 135 | 影子初评与预期窗口 | S | P1 | `assessment` | `zg361m.135` | `zg361_mechanism_135_ai_effect` | 1 | complete | fixture-live | fixture-live | contract-complete | partial | partial | `central-wired` |
| 136 | 跨经理预校准小会 | S | P1 | `calibration` | `zg361m.136` | `zg361_mechanism_136_ai_effect` | 1 | complete | fixture-live | fixture-live | contract-complete | partial | partial | `central-wired` |
| 137 | 议程顺序与锚定效应 | S | P2 | `calibration` | `zg361m.137` | `zg361_mechanism_137_ai_effect` | 1 | complete | fixture-live | fixture-live | contract-complete | partial | partial | `central-wired` |
| 138 | 人数取整与尾差归属 | S | P1 | `calibration` | `zg361m.138` | `zg361_mechanism_138_ai_effect` | 1 | complete | fixture-live | fixture-live | contract-complete | partial | partial | `central-wired` |
| 139 | 跨周期配额债 | S | P2 | `calibration` | `zg361m.139` | `zg361_mechanism_139_ai_effect` | 1 | complete | fixture-live | fixture-live | contract-complete | partial | partial | `central-wired` |
| 140 | 重组中的配额归属日 | S | P1 | `calibration` | `zg361m.140` | `zg361_mechanism_140_ai_effect` | 1 | complete | fixture-live | fixture-live | contract-complete | partial | partial | `central-wired` |
| 141 | 高层“保送 / 必杀”名单 | S | P2 | `governance` | `zg361m.141` | `zg361_mechanism_141_ai_effect` | 1 | complete | fixture-live | fixture-live | contract-complete | partial | partial | `central-wired` |
| 142 | 里程碑待定档 | S | P2 | `assessment` | `zg361m.142` | `zg361_mechanism_142_ai_effect` | 1 | complete | fixture-live | fixture-live | contract-complete | partial | partial | `central-wired` |
| 143 | 截止后重大事故对称处理 | S | P1 | `governance` | `zg361m.143` | `zg361_mechanism_143_ai_effect` | 1 | complete | fixture-live | fixture-live | contract-complete | partial | partial | `central-wired` |
| 144 | 校准异议票与少数意见 | S | P1 | `calibration` | `zg361m.144` | `zg361_mechanism_144_ai_effect` | 1 | complete | fixture-live | fixture-live | contract-complete | partial | partial | `central-wired` |
| 145 | 三档之内的影子排序 | S | P2 | `assessment` | `zg361m.145` | `zg361_mechanism_145_ai_effect` | 1 | complete | fixture-live | fixture-live | contract-complete | partial | partial | `central-wired` |
| 146 | 直白档位 / 委婉话术制度 | T | P1 | `assessment` | `zg361m.146` | `zg361_mechanism_146_ai_effect` | 1 | complete | fixture-live | fixture-live | contract-complete | partial | partial | `central-wired` |
| 147 | 强制“一扬一抑”反馈模板 | T | P2 | `assessment` | `zg361m.147` | `zg361_mechanism_147_ai_effect` | 1 | complete | fixture-live | fixture-live | contract-complete | partial | partial | `central-wired` |
| 148 | 先讲证据还是先报结果 | T | P1 | `assessment` | `zg361m.148` | `zg361_mechanism_148_ai_effect` | 1 | complete | fixture-live | fixture-live | contract-complete | partial | partial | `central-wired` |
| 149 | 绩效结果谈判包 | T | P2 | `compensation` | `zg361m.149` | `zg361_mechanism_149_ai_effect` | 1 | complete | fixture-live | fixture-live | contract-complete | partial | partial | `central-wired` |
| 150 | “这次先委屈你”的补偿承诺 | T | P1 | `compensation` | `zg361m.150` | `zg361_mechanism_150_ai_effect` | 1 | complete | fixture-live | fixture-live | contract-complete | partial | partial | `central-wired` |
| 151 | 签收不等于认同 | T | P1 | `governance` | `zg361m.151` | `zg361_mechanism_151_ai_effect` | 1 | complete | fixture-live | fixture-live | contract-complete | partial | partial | `central-wired` |
| 152 | 反馈可行动性评分 | T | P1 | `assessment` | `zg361m.152` | `zg361_mechanism_152_ai_effect` | 1 | complete | fixture-live | fixture-live | contract-complete | partial | partial | `central-wired` |
| 153 | 反馈后行动项闭环 | T | P1 | `assessment` | `zg361m.153` | `zg361_mechanism_153_ai_effect` | 1 | complete | fixture-live | fixture-live | contract-complete | partial | partial | `central-wired` |
| 154 | 录音式完整纪要 / 摘要纪要 | T | P2 | `governance` | `zg361m.154` | `zg361_mechanism_154_ai_effect` | 1 | complete | fixture-live | fixture-live | contract-complete | partial | partial | `central-wired` |
| 155 | 公开表扬与私下批评边界 | T | P2 | `organization` | `zg361m.155` | `zg361_mechanism_155_ai_effect` | 1 | complete | fixture-live | fixture-live | contract-complete | partial | partial | `central-wired` |
| 156 | 团队结果说明会 | T | P1 | `governance` | `zg361m.156` | `zg361_mechanism_156_ai_effect` | 1 | complete | fixture-live | fixture-live | contract-complete | partial | partial | `central-wired` |
| 157 | 自荐权与主管提名权 | U | P1 | `promotion` | `zg361m.157` | `zg361_mechanism_157_ai_effect` | 1 | complete | fixture-live | fixture-live | contract-complete | partial | partial | `central-wired` |
| 158 | 主管提名额度 | U | P1 | `promotion` | `zg361m.158` | `zg361_mechanism_158_ai_effect` | 1 | complete | fixture-live | fixture-live | contract-complete | partial | partial | `central-wired` |
| 159 | 雪藏明星不提名 | U | P1 | `promotion` | `zg361m.159` | `zg361_mechanism_159_ai_effect` | 1 | complete | fixture-live | fixture-live | contract-complete | partial | partial | `central-wired` |
| 160 | 部门预审淘汰赛 | U | P1 | `promotion` | `zg361m.160` | `zg361_mechanism_160_ai_effect` | 1 | complete | fixture-live | fixture-live | contract-complete | partial | partial | `central-wired` |
| 161 | “陪跑包”与虚假竞争 | U | P2 | `promotion` | `zg361m.161` | `zg361_mechanism_161_ai_effect` | 1 | complete | fixture-live | fixture-live | contract-complete | partial | partial | `central-wired` |
| 162 | 资历门槛例外申请 | U | P2 | `promotion` | `zg361m.162` | `zg361_mechanism_162_ai_effect` | 1 | complete | fixture-live | fixture-live | contract-complete | partial | partial | `central-wired` |
| 163 | 晋升绩效观察窗 | U | P1 | `promotion` | `zg361m.163` | `zg361_mechanism_163_ai_effect` | 1 | complete | fixture-live | fixture-live | contract-complete | partial | partial | `central-wired` |
| 164 | 跨团队成果进入晋升包 | U | P1 | `promotion` | `zg361m.164` | `zg361_mechanism_164_ai_effect` | 1 | complete | fixture-live | fixture-live | contract-complete | partial | partial | `central-wired` |
| 165 | “先干到下一级”试岗证据 | U | P1 | `promotion` | `zg361m.165` | `zg361_mechanism_165_ai_effect` | 1 | complete | fixture-live | fixture-live | contract-complete | partial | partial | `central-wired` |
| 166 | 候选主动撤包 | U | P2 | `promotion` | `zg361m.166` | `zg361_mechanism_166_ai_effect` | 1 | complete | fixture-live | fixture-live | contract-complete | partial | partial | `central-wired` |
| 167 | Sponsor 的晋升信用债 | U | P1 | `promotion` | `zg361m.167` | `zg361_mechanism_167_ai_effect` | 1 | complete | fixture-live | fixture-live | contract-complete | partial | partial | `central-wired` |
| 168 | 经理提名命中率 | U | P1 | `promotion` | `zg361m.168` | `zg361_mechanism_168_ai_effect` | 1 | complete | fixture-live | fixture-live | contract-complete | partial | partial | `central-wired` |
| 169 | 评委专业匹配 | V | P1 | `promotion` | `zg361m.169` | `zg361_mechanism_169_ai_effect` | 1 | complete | fixture-live | fixture-live | contract-complete | partial | partial | `central-wired` |
| 170 | 随机评委与熟人评委 | V | P2 | `promotion` | `zg361m.170` | `zg361_mechanism_170_ai_effect` | 1 | complete | fixture-live | fixture-live | contract-complete | partial | partial | `central-wired` |
| 171 | 答辩评委利益回避 | V | P1 | `governance` | `zg361m.171` | `zg361_mechanism_171_ai_effect` | 1 | complete | fixture-live | fixture-live | contract-complete | partial | partial | `central-wired` |
| 172 | 一票否决 / 多数票 / 平均分 | V | P2 | `governance` | `zg361m.172` | `zg361_mechanism_172_ai_effect` | 1 | complete | fixture-live | fixture-live | contract-complete | partial | partial | `central-wired` |
| 173 | 盲材料审查与现场答辩 | V | P2 | `promotion` | `zg361m.173` | `zg361_mechanism_173_ai_effect` | 1 | complete | fixture-live | fixture-live | contract-complete | partial | partial | `central-wired` |
| 174 | 答辩时间预算 | V | P1 | `promotion` | `zg361m.174` | `zg361_mechanism_174_ai_effect` | 1 | complete | fixture-live | fixture-live | contract-complete | partial | partial | `central-wired` |
| 175 | 模拟答辩与辅导资源 | V | P1 | `learning` | `zg361m.175` | `zg361_mechanism_175_ai_effect` | 1 | complete | fixture-live | fixture-live | contract-complete | partial | partial | `central-wired` |
| 176 | 团队成绩的个人归因质询 | V | P1 | `promotion` | `zg361m.176` | `zg361_mechanism_176_ai_effect` | 1 | complete | fixture-live | fixture-live | contract-complete | partial | partial | `central-wired` |
| 177 | 项目规模与个人杠杆分离 | V | P1 | `promotion` | `zg361m.177` | `zg361_mechanism_177_ai_effect` | 1 | complete | fixture-live | fixture-live | contract-complete | partial | partial | `central-wired` |
| 178 | 可复核工件与故事表达双证据 | V | P1 | `promotion` | `zg361m.178` | `zg361_mechanism_178_ai_effect` | 1 | complete | fixture-live | fixture-live | contract-complete | partial | partial | `central-wired` |
| 179 | 失败答辩的具体反馈 owner | V | P1 | `promotion` | `zg361m.179` | `zg361_mechanism_179_ai_effect` | 1 | complete | fixture-live | fixture-live | contract-complete | partial | partial | `central-wired` |
| 180 | 晋升冷却与材料刷新 | V | P1 | `promotion` | `zg361m.180` | `zg361_mechanism_180_ai_effect` | 1 | complete | fixture-live | fixture-live | contract-complete | partial | partial | `central-wired` |
| 181 | 能力、意愿、错岗三分诊 | W | P1 | `pip` | `zg361m.181` | `zg361_mechanism_181_ai_effect` | 1 | complete | fixture-live | fixture-live | contract-complete | partial | partial | `central-wired` |
| 182 | PIP 启动证据门槛 | W | P1 | `pip` | `zg361m.182` | `zg361_mechanism_182_ai_effect` | 1 | complete | fixture-live | fixture-live | contract-complete | partial | partial | `central-wired` |
| 183 | PIP 目标双签与拒签理由 | W | P1 | `pip` | `zg361m.183` | `zg361_mechanism_183_ai_effect` | 1 | complete | fixture-live | fixture-live | contract-complete | partial | partial | `central-wired` |
| 184 | 经理的 PIP 承载量 | W | P1 | `pip` | `zg361m.184` | `zg361_mechanism_184_ai_effect` | 1 | complete | fixture-live | fixture-live | contract-complete | partial | partial | `central-wired` |
| 185 | PIP 中期检查 | W | P1 | `pip` | `zg361m.185` | `zg361_mechanism_185_ai_effect` | 1 | complete | fixture-live | fixture-live | contract-complete | partial | partial | `central-wired` |
| 186 | PIP 目标膨胀锁 | W | P1 | `pip` | `zg361m.186` | `zg361_mechanism_186_ai_effect` | 1 | complete | fixture-live | fixture-live | contract-complete | partial | partial | `central-wired` |
| 187 | PIP 毕业标准 | W | P1 | `pip` | `zg361m.187` | `zg361_mechanism_187_ai_effect` | 1 | complete | fixture-live | fixture-live | contract-complete | partial | partial | `central-wired` |
| 188 | 毕业后的复发观察期 | W | P1 | `pip` | `zg361m.188` | `zg361_mechanism_188_ai_effect` | 1 | complete | fixture-live | fixture-live | contract-complete | partial | partial | `central-wired` |
| 189 | 二次 PIP / 调岗 / 退出三岔口 | W | P1 | `pip` | `zg361m.189` | `zg361_mechanism_189_ai_effect` | 1 | complete | fixture-live | fixture-live | contract-complete | partial | partial | `central-wired` |
| 190 | PIP 随转岗披露的最小范围 | W | P1 | `pip` | `zg361m.190` | `zg361_mechanism_190_ai_effect` | 1 | complete | fixture-live | fixture-live | contract-complete | partial | partial | `central-wired` |
| 191 | PIP 退出后的团队成本单 | W | P1 | `organization` | `zg361m.191` | `zg361_mechanism_191_ai_effect` | 1 | complete | fixture-live | fixture-live | contract-complete | partial | partial | `central-wired` |
| 192 | 急务值守轮盘 | X | P1 | `incident` | `zg361m.192` | `zg361_mechanism_192_ai_effect` | 1 | complete | fixture-live | fixture-live | contract-complete | partial | partial | `central-wired` |
| 193 | 值守津贴 / 调休二选一 | X | P1 | `compensation` | `zg361m.193` | `zg361_mechanism_193_ai_effect` | 1 | complete | fixture-live | fixture-live | contract-complete | partial | partial | `central-wired` |
| 194 | 值守对项目目标的等量减免 | X | P1 | `workload` | `zg361m.194` | `zg361_mechanism_194_ai_effect` | 1 | complete | fixture-live | fixture-live | contract-complete | partial | partial | `central-wired` |
| 195 | 假警报与告警质量 | X | P1 | `incident` | `zg361m.195` | `zg361_mechanism_195_ai_effect` | 1 | complete | fixture-live | fixture-live | contract-complete | partial | partial | `central-wired` |
| 196 | 事故等级申报博弈 | X | P1 | `incident` | `zg361m.196` | `zg361_mechanism_196_ai_effect` | 1 | complete | fixture-live | fixture-live | contract-complete | partial | partial | `central-wired` |
| 197 | 事故指挥官与技术救火者分功 | X | P1 | `incident` | `zg361m.197` | `zg361_mechanism_197_ai_effect` | 1 | complete | fixture-live | fixture-live | contract-complete | partial | partial | `central-wired` |
| 198 | “纵火者拿救火奖”识别 | X | P1 | `incident` | `zg361m.198` | `zg361_mechanism_198_ai_effect` | 1 | complete | fixture-live | fixture-live | contract-complete | partial | partial | `central-wired` |
| 199 | 未发生事故的预防功 | X | P2 | `incident` | `zg361m.199` | `zg361_mechanism_199_ai_effect` | 1 | complete | fixture-live | fixture-live | contract-complete | partial | partial | `central-wired` |
| 200 | 紧急处置临时授权 | X | P1 | `incident` | `zg361m.200` | `zg361_mechanism_200_ai_effect` | 1 | complete | fixture-live | fixture-live | contract-complete | partial | partial | `central-wired` |
| 201 | 不可改写的事故时间线 | X | P1 | `incident` | `zg361m.201` | `zg361_mechanism_201_ai_effect` | 1 | complete | fixture-live | fixture-live | contract-complete | partial | partial | `central-wired` |
| 202 | 复盘行动项 owner | X | P1 | `incident` | `zg361m.202` | `zg361_mechanism_202_ai_effect` | 1 | complete | fixture-live | fixture-live | contract-complete | partial | partial | `central-wired` |
| 203 | 重复事故升级到管理责任 | X | P1 | `incident` | `zg361m.203` | `zg361_mechanism_203_ai_effect` | 1 | complete | fixture-live | fixture-live | contract-complete | partial | partial | `central-wired` |
| 204 | 可靠性预算与停止上线 | X | P2 | `incident` | `zg361m.204` | `zg361_mechanism_204_ai_effect` | 1 | complete | fixture-live | fixture-live | contract-complete | partial | partial | `central-wired` |
| 205 | 重复运维（toil）比例上限 | Y | P1 | `technology` | `zg361m.205` | `zg361_mechanism_205_ai_effect` | 3 | complete | fixture-live | fixture-live | contract-complete | partial | partial | `central-wired` |
| 206 | 积弊本金与利息账 | Y | P1 | `technology` | `zg361m.206` | `zg361_mechanism_206_ai_effect` | 3 | complete | fixture-live | fixture-live | contract-complete | partial | partial | `central-wired` |
| 207 | 固定还债预算 | Y | P1 | `technology` | `zg361m.207` | `zg361_mechanism_207_ai_effect` | 3 | complete | fixture-live | fixture-live | contract-complete | partial | partial | `central-wired` |
| 208 | 渐进修补 / 全面重做 | Y | P2 | `technology` | `zg361m.208` | `zg361_mechanism_208_ai_effect` | 3 | complete | fixture-live | fixture-live | contract-complete | partial | partial | `central-wired` |
| 209 | 旧系统危险津贴 | Y | P1 | `compensation` | `zg361m.209` | `zg361_mechanism_209_ai_effect` | 3 | complete | fixture-live | fixture-live | contract-complete | partial | partial | `central-wired` |
| 210 | 维护 owner 轮换 | Y | P1 | `technology` | `zg361m.210` | `zg361_mechanism_210_ai_effect` | 3 | complete | fixture-live | fixture-live | contract-complete | partial | partial | `central-wired` |
| 211 | 文档与操作手册功劳 | Y | P1 | `learning` | `zg361m.211` | `zg361_mechanism_211_ai_effect` | 3 | complete | fixture-live | fixture-live | contract-complete | partial | partial | `central-wired` |
| 212 | 自动化“做完就看不见”悖论 | Y | P1 | `technology` | `zg361m.212` | `zg361_mechanism_212_ai_effect` | 3 | complete | fixture-live | fixture-live | contract-complete | partial | partial | `central-wired` |
| 213 | 审阅与质量把关贡献 | Y | P1 | `technology` | `zg361m.213` | `zg361_mechanism_213_ai_effect` | 3 | complete | fixture-live | fixture-live | contract-complete | partial | partial | `central-wired` |
| 214 | 覆盖率数字与真实质量 | Y | P1 | `technology` | `zg361m.214` | `zg361_mechanism_214_ai_effect` | 3 | complete | fixture-live | fixture-live | contract-complete | partial | partial | `central-wired` |
| 215 | 退役旧制度也算交付 | Y | P1 | `technology` | `zg361m.215` | `zg361_mechanism_215_ai_effect` | 3 | complete | fixture-live | fixture-live | contract-complete | partial | partial | `central-wired` |
| 216 | 离岗交接完整度 | Y | P1 | `organization` | `zg361m.216` | `zg361_mechanism_216_ai_effect` | 3 | complete | fixture-live | fixture-live | contract-complete | partial | partial | `central-wired` |
| 217 | 共享平台强制采用 / 自愿采用 | Z | P1 | `platform` | `zg361m.217` | `zg361_mechanism_217_ai_effect` | 3 | complete | fixture-live | fixture-live | contract-complete | partial | partial | `central-wired` |
| 218 | 内部客户满意与战略底座双评分 | Z | P1 | `platform` | `zg361m.218` | `zg361_mechanism_218_ai_effect` | 3 | complete | fixture-live | fixture-live | contract-complete | partial | partial | `central-wired` |
| 219 | 采用数量 / 使用深度 / 节省成本 | Z | P1 | `platform` | `zg361m.219` | `zg361_mechanism_219_ai_effect` | 3 | complete | fixture-live | fixture-live | contract-complete | partial | partial | `central-wired` |
| 220 | 共享成本展示与内部结算 | Z | P2 | `platform` | `zg361m.220` | `zg361_mechanism_220_ai_effect` | 3 | complete | fixture-live | fixture-live | contract-complete | partial | partial | `central-wired` |
| 221 | 迁移成本谁来付 | Z | P1 | `platform` | `zg361m.221` | `zg361_mechanism_221_ai_effect` | 3 | complete | fixture-live | fixture-live | contract-complete | partial | partial | `central-wired` |
| 222 | 新旧双跑过渡期 | Z | P1 | `platform` | `zg361m.222` | `zg361_mechanism_222_ai_effect` | 3 | complete | fixture-live | fixture-live | contract-complete | partial | partial | `central-wired` |
| 223 | 重复造轮子扫描 | Z | P1 | `platform` | `zg361m.223` | `zg361_mechanism_223_ai_effect` | 3 | complete | fixture-live | fixture-live | contract-complete | partial | partial | `central-wired` |
| 224 | 重复方案合并赛 | Z | P2 | `platform` | `zg361m.224` | `zg361_mechanism_224_ai_effect` | 3 | complete | fixture-live | fixture-live | contract-complete | partial | partial | `central-wired` |
| 225 | “不是我造的不用”与合法分叉 | Z | P1 | `platform` | `zg361m.225` | `zg361_mechanism_225_ai_effect` | 3 | complete | fixture-live | fixture-live | contract-complete | partial | partial | `central-wired` |
| 226 | 内部开源贡献归因 | Z | P1 | `platform` | `zg361m.226` | `zg361_mechanism_226_ai_effect` | 3 | complete | fixture-live | fixture-live | contract-complete | partial | partial | `central-wired` |
| 227 | 创始人、贡献者与维护者分账 | Z | P1 | `platform` | `zg361m.227` | `zg361_mechanism_227_ai_effect` | 3 | complete | fixture-live | fixture-live | contract-complete | partial | partial | `central-wired` |
| 228 | 中台事故的爆炸半径责任 | Z | P1 | `platform` | `zg361m.228` | `zg361_mechanism_228_ai_effect` | 3 | complete | fixture-live | fixture-live | contract-complete | partial | partial | `central-wired` |
| 229 | 指标字典与口径 owner | AA | P1 | `data` | `zg361m.229` | `zg361_mechanism_229_ai_effect` | 3 | complete | fixture-live | fixture-live | contract-complete | partial | partial | `central-wired` |
| 230 | 多数据源对账 | AA | P1 | `data` | `zg361m.230` | `zg361_mechanism_230_ai_effect` | 3 | complete | fixture-live | fixture-live | contract-complete | partial | partial | `central-wired` |
| 231 | 业务指标分母变更 | AA | P1 | `data` | `zg361m.231` | `zg361_mechanism_231_ai_effect` | 3 | complete | fixture-live | fixture-live | contract-complete | partial | partial | `central-wired` |
| 232 | 缺失数据与人工回填 | AA | P1 | `data` | `zg361m.232` | `zg361_mechanism_232_ai_effect` | 3 | complete | fixture-live | fixture-live | contract-complete | partial | partial | `central-wired` |
| 233 | 看板访问权不对称 | AA | P2 | `data` | `zg361m.233` | `zg361_mechanism_233_ai_effect` | 3 | complete | fixture-live | fixture-live | contract-complete | partial | partial | `central-wired` |
| 234 | 领先指标与滞后结果分账 | AA | P1 | `data` | `zg361m.234` | `zg361_mechanism_234_ai_effect` | 3 | complete | fixture-live | fixture-live | contract-complete | partial | partial | `central-wired` |
| 235 | 主指标与护栏指标 | AA | P1 | `data` | `zg361m.235` | `zg361_mechanism_235_ai_effect` | 3 | complete | fixture-live | fixture-live | contract-complete | partial | partial | `central-wired` |
| 236 | KPI 达标悬崖 | AA | P2 | `data` | `zg361m.236` | `zg361_mechanism_236_ai_effect` | 3 | complete | fixture-live | fixture-live | contract-complete | partial | partial | `central-wired` |
| 237 | 时间窗挑选与“截最美一段” | AA | P1 | `data` | `zg361m.237` | `zg361_mechanism_237_ai_effect` | 3 | complete | fixture-live | fixture-live | contract-complete | partial | partial | `central-wired` |
| 238 | 虚荣指标与最终价值 | AA | P1 | `data` | `zg361m.238` | `zg361_mechanism_238_ai_effect` | 3 | complete | fixture-live | fixture-live | contract-complete | partial | partial | `central-wired` |
| 239 | 失败实验的学习收益 | AA | P1 | `learning` | `zg361m.239` | `zg361_mechanism_239_ai_effect` | 3 | complete | fixture-live | fixture-live | contract-complete | partial | partial | `central-wired` |
| 240 | 实验污染与多团队抢样本 | AA | P2 | `data` | `zg361m.240` | `zg361_mechanism_240_ai_effect` | 3 | complete | fixture-live | fixture-live | contract-complete | partial | partial | `central-wired` |
| 241 | 长尾效果归属期 | AA | P1 | `assessment` | `zg361m.241` | `zg361_mechanism_241_ai_effect` | 3 | complete | fixture-live | fixture-live | contract-complete | partial | partial | `central-wired` |
| 242 | 在场时长 / 真实成果双账 | AB | P1 | `workload` | `zg361m.242` | `zg361_mechanism_242_ai_effect` | 3 | complete | fixture-live | fixture-live | contract-complete | partial | partial | `central-wired` |
| 243 | 非工作时段回复规则 | AB | P1 | `workload` | `zg361m.243` | `zg361_mechanism_243_ai_effect` | 3 | complete | fixture-live | fixture-live | contract-complete | partial | partial | `central-wired` |
| 244 | “自愿奋斗”与隐性强制 | AB | P1 | `workload` | `zg361m.244` | `zg361_mechanism_244_ai_effect` | 3 | complete | fixture-live | fixture-live | contract-complete | partial | partial | `central-wired` |
| 245 | 审批加班 / 影子加班 | AB | P1 | `workload` | `zg361m.245` | `zg361_mechanism_245_ai_effect` | 3 | complete | fixture-live | fixture-live | contract-complete | partial | partial | `central-wired` |
| 246 | 加班金币 / 调休 / 目标减免 | AB | P1 | `compensation` | `zg361m.246` | `zg361_mechanism_246_ai_effect` | 3 | complete | fixture-live | fixture-live | contract-complete | partial | partial | `central-wired` |
| 247 | 战时冲刺的起止令 | AB | P1 | `workload` | `zg361m.247` | `zg361_mechanism_247_ai_effect` | 3 | complete | fixture-live | fixture-live | contract-complete | partial | partial | `central-wired` |
| 248 | 长期缺编反噬经理 | AB | P1 | `hc` | `zg361m.248` | `zg361_mechanism_248_ai_effect` | 3 | complete | fixture-live | fixture-live | contract-complete | partial | partial | `central-wired` |
| 249 | 会议工时预算 | AB | P1 | `workload` | `zg361m.249` | `zg361_mechanism_249_ai_effect` | 3 | complete | fixture-live | fixture-live | contract-complete | partial | partial | `central-wired` |
| 250 | 出席人数 / 决策贡献分离 | AB | P1 | `workload` | `zg361m.250` | `zg361_mechanism_250_ai_effect` | 3 | complete | fixture-live | fixture-live | contract-complete | partial | partial | `central-wired` |
| 251 | 拒绝无效会议的政治成本 | AB | P2 | `workload` | `zg361m.251` | `zg361_mechanism_251_ai_effect` | 3 | complete | fixture-live | fixture-live | contract-complete | partial | partial | `central-wired` |
| 252 | 休假与缺勤的目标归一化 | AB | P1 | `assessment` | `zg361m.252` | `zg361_mechanism_252_ai_effect` | 3 | complete | fixture-live | fixture-live | contract-complete | partial | partial | `central-wired` |
| 253 | 低绩效后的躺平反应 | AB | P2 | `pip` | `zg361m.253` | `zg361_mechanism_253_ai_effect` | 3 | complete | fixture-live | fixture-live | contract-complete | partial | partial | `central-wired` |
| 254 | 外包绕 HC | AC | P1 | `external` | `zg361m.254` | `zg361_mechanism_254_ai_effect` | 2 | complete | fixture-live | fixture-live | contract-complete | partial | partial | `central-wired` |
| 255 | 正式 HC / 外包总成本比较 | AC | P1 | `external` | `zg361m.255` | `zg361_mechanism_255_ai_effect` | 2 | complete | fixture-live | fixture-live | contract-complete | partial | partial | `central-wired` |
| 256 | 外部团队独立绩效池 | AC | P1 | `external` | `zg361m.256` | `zg361_mechanism_256_ai_effect` | 2 | complete | fixture-live | fixture-live | contract-complete | partial | partial | `central-wired` |
| 257 | 外包转正式的有限通道 | AC | P1 | `hc` | `zg361m.257` | `zg361_mechanism_257_ai_effect` | 2 | complete | fixture-live | fixture-live | contract-complete | partial | partial | `central-wired` |
| 258 | 权限差导致的绩效校正 | AC | P1 | `external` | `zg361m.258` | `zg361_mechanism_258_ai_effect` | 2 | complete | fixture-live | fixture-live | contract-complete | partial | partial | `central-wired` |
| 259 | 供应商 SLA 与个体责任分开 | AC | P1 | `external` | `zg361m.259` | `zg361_mechanism_259_ai_effect` | 2 | complete | fixture-live | fixture-live | contract-complete | partial | partial | `central-wired` |
| 260 | 人力补位 / 结果承包二种合同 | AC | P2 | `external` | `zg361m.260` | `zg361_mechanism_260_ai_effect` | 2 | complete | fixture-live | fixture-live | contract-complete | partial | partial | `central-wired` |
| 261 | 多层转包与真实执行者披露 | AC | P1 | `external` | `zg361m.261` | `zg361_mechanism_261_ai_effect` | 2 | complete | fixture-live | fixture-live | contract-complete | partial | partial | `central-wired` |
| 262 | 借调人员双线评价 | AC | P1 | `assessment` | `zg361m.262` | `zg361_mechanism_262_ai_effect` | 2 | complete | fixture-live | fixture-live | contract-complete | partial | partial | `central-wired` |
| 263 | 借调结束的返岗权 | AC | P1 | `organization` | `zg361m.263` | `zg361_mechanism_263_ai_effect` | 2 | complete | fixture-live | fixture-live | contract-complete | partial | partial | `central-wired` |
| 264 | 供应商退出的知识移交 | AC | P1 | `external` | `zg361m.264` | `zg361_mechanism_264_ai_effect` | 2 | complete | fixture-live | fixture-live | contract-complete | partial | partial | `central-wired` |
| 265 | 外包招聘舞弊与管理连责 | AC | P1 | `governance` | `zg361m.265` | `zg361_mechanism_265_ai_effect` | 2 | complete | fixture-live | fixture-live | contract-complete | partial | partial | `central-wired` |
| 266 | 招人门槛 / 空岗紧急度 | AD | P1 | `hc` | `zg361m.266` | `zg361_mechanism_266_ai_effect` | 2 | complete | fixture-live | fixture-live | contract-complete | partial | partial | `central-wired` |
| 267 | 面试官先独立投票 | AD | P1 | `assessment` | `zg361m.267` | `zg361_mechanism_267_ai_effect` | 2 | complete | fixture-live | fixture-live | contract-complete | partial | partial | `central-wired` |
| 268 | 面试官手松手紧校准 | AD | P1 | `calibration` | `zg361m.268` | `zg361_mechanism_268_ai_effect` | 2 | complete | fixture-live | fixture-live | contract-complete | partial | partial | `central-wired` |
| 269 | 面试判断的延迟回写 | AD | P1 | `learning` | `zg361m.269` | `zg361_mechanism_269_ai_effect` | 2 | complete | fixture-live | fixture-live | contract-complete | partial | partial | `central-wired` |
| 270 | 误招 / 漏招成本偏好 | AD | P2 | `assessment` | `zg361m.270` | `zg361_mechanism_270_ai_effect` | 2 | complete | fixture-live | fixture-live | contract-complete | partial | partial | `central-wired` |
| 271 | 内推奖励与利益回避 | AD | P1 | `hc` | `zg361m.271` | `zg361_mechanism_271_ai_effect` | 2 | complete | fixture-live | fixture-live | contract-complete | partial | partial | `central-wired` |
| 272 | Offer 职级特批 | AD | P1 | `promotion` | `zg361m.272` | `zg361_mechanism_272_ai_effect` | 2 | complete | fixture-live | fixture-live | contract-complete | partial | partial | `central-wired` |
| 273 | 候选人归属与“抢简历” | AD | P2 | `hc` | `zg361m.273` | `zg361_mechanism_273_ai_effect` | 2 | complete | fixture-live | fixture-live | contract-complete | partial | partial | `central-wired` |
| 274 | 反 Offer 竞价上限 | AD | P1 | `compensation` | `zg361m.274` | `zg361_mechanism_274_ai_effect` | 2 | complete | fixture-live | fixture-live | contract-complete | partial | partial | `central-wired` |
| 275 | Offer 拒绝与 HC 保留期 | AD | P1 | `hc` | `zg361m.275` | `zg361_mechanism_275_ai_effect` | 2 | complete | fixture-live | fixture-live | contract-complete | partial | partial | `central-wired` |
| 276 | 离职人才回聘 | AD | P1 | `hc` | `zg361m.276` | `zg361_mechanism_276_ai_effect` | 2 | complete | fixture-live | fixture-live | contract-complete | partial | partial | `central-wired` |
| 277 | PIP 退出不自动补 HC | AD | P1 | `hc` | `zg361m.277` | `zg361_mechanism_277_ai_effect` | 2 | complete | fixture-live | fixture-live | contract-complete | partial | partial | `central-wired` |
| 278 | 年度总包实得对账单 | AE | P1 | `compensation` | `zg361m.278` | `zg361_mechanism_278_ai_effect` | 2 | complete | fixture-live | fixture-live | contract-complete | partial | partial | `central-wired` |
| 279 | 额外月份俸禄的契约属性 | AE | P1 | `compensation` | `zg361m.279` | `zg361_mechanism_279_ai_effect` | 2 | complete | fixture-live | fixture-live | contract-complete | partial | partial | `central-wired` |
| 280 | 年中入离职奖金折算 | AE | P1 | `compensation` | `zg361m.280` | `zg361_mechanism_280_ai_effect` | 2 | complete | fixture-live | fixture-live | contract-complete | partial | partial | `central-wired` |
| 281 | 奖金发放日与延期信用 | AE | P1 | `compensation` | `zg361m.281` | `zg361_mechanism_281_ai_effect` | 2 | complete | fixture-live | fixture-live | contract-complete | partial | partial | `central-wired` |
| 282 | 调薪生效日与追溯补发 | AE | P1 | `compensation` | `zg361m.282` | `zg361_mechanism_282_ai_effect` | 2 | complete | fixture-live | fixture-live | contract-complete | partial | partial | `central-wired` |
| 283 | “干升职”兑现期限 | AE | P1 | `compensation` | `zg361m.283` | `zg361_mechanism_283_ai_effect` | 2 | complete | fixture-live | fixture-live | contract-complete | partial | partial | `central-wired` |
| 284 | 降级薪俸缓冲坡 | AE | P1 | `compensation` | `zg361m.284` | `zg361_mechanism_284_ai_effect` | 2 | complete | fixture-live | fixture-live | contract-complete | partial | partial | `central-wired` |
| 285 | 同档调薪二次校准 | AE | P1 | `compensation` | `zg361m.285` | `zg361_mechanism_285_ai_effect` | 2 | complete | fixture-live | fixture-live | contract-complete | partial | partial | `central-wired` |
| 286 | 超带冻结与低带追赶 | AE | P1 | `compensation` | `zg361m.286` | `zg361_mechanism_286_ai_effect` | 2 | complete | fixture-live | fixture-live | contract-complete | partial | partial | `central-wired` |
| 287 | 密薪 / 带宽公开 / 匿名分布 | AE | P2 | `governance` | `zg361m.287` | `zg361_mechanism_287_ai_effect` | 2 | complete | fixture-live | fixture-live | contract-complete | partial | partial | `central-wired` |
| 288 | 新老薪酬倒挂修复 | AE | P1 | `compensation` | `zg361m.288` | `zg361_mechanism_288_ai_effect` | 2 | complete | fixture-live | fixture-live | contract-complete | partial | partial | `central-wired` |
| 289 | 薪酬申诉与绩效申诉分轨 | AE | P1 | `compensation` | `zg361m.289` | `zg361_mechanism_289_ai_effect` | 2 | complete | fixture-live | fixture-live | contract-complete | partial | partial | `central-wired` |
| 290 | 长期功赏提名池 | AF | P1 | `compensation` | `zg361m.290` | `zg361_mechanism_290_ai_effect` | 2 | complete | fixture-live | fixture-live | contract-complete | partial | partial | `central-wired` |
| 291 | 定份额 / 定授予价值 | AF | P2 | `compensation` | `zg361m.291` | `zg361_mechanism_291_ai_effect` | 2 | complete | fixture-live | fixture-live | contract-complete | partial | partial | `central-wired` |
| 292 | 高风险期权式 / 保底份额式 | AF | P2 | `compensation` | `zg361m.292` | `zg361_mechanism_292_ai_effect` | 2 | complete | fixture-live | fixture-live | contract-complete | partial | partial | `central-wired` |
| 293 | 当期奖金自愿换长期份额 | AF | P2 | `compensation` | `zg361m.293` | `zg361_mechanism_293_ai_effect` | 2 | complete | fixture-live | fixture-live | contract-complete | partial | partial | `central-wired` |
| 294 | 授予价、当前估值与可变现值三栏 | AF | P1 | `data` | `zg361m.294` | `zg361_mechanism_294_ai_effect` | 2 | complete | fixture-live | fixture-live | contract-complete | partial | partial | `central-wired` |
| 295 | 首授 Cliff 长短 | AF | P2 | `compensation` | `zg361m.295` | `zg361_mechanism_295_ai_effect` | 2 | complete | fixture-live | fixture-live | contract-complete | partial | partial | `central-wired` |
| 296 | 月度 / 季度 / 年度归属节奏 | AF | P2 | `compensation` | `zg361m.296` | `zg361_mechanism_296_ai_effect` | 2 | complete | fixture-live | fixture-live | contract-complete | partial | partial | `central-wired` |
| 297 | 服务归属与绩效归属分轨 | AF | P1 | `compensation` | `zg361m.297` | `zg361_mechanism_297_ai_effect` | 2 | complete | fixture-live | fixture-live | contract-complete | partial | partial | `central-wired` |
| 298 | 组织门槛 × 个人门槛双闸 | AF | P1 | `compensation` | `zg361m.298` | `zg361_mechanism_298_ai_effect` | 2 | complete | fixture-live | fixture-live | contract-complete | partial | partial | `central-wired` |
| 299 | Good Leaver / Bad Leaver 分类 | AF | P1 | `compensation` | `zg361m.299` | `zg361_mechanism_299_ai_effect` | 2 | complete | fixture-live | fixture-live | contract-complete | partial | partial | `central-wired` |
| 300 | 回购窗口与流动性队列 | AF | P1 | `compensation` | `zg361m.300` | `zg361_mechanism_300_ai_effect` | 2 | complete | fixture-live | fixture-live | contract-complete | partial | partial | `central-wired` |
| 301 | 核心业务光环折算 | AG | P1 | `assessment` | `zg361m.301` | `zg361_mechanism_301_ai_effect` | 2 | complete | fixture-live | fixture-live | contract-complete | partial | partial | `central-wired` |
| 302 | 衰退业务的逆风责任 | AG | P1 | `assessment` | `zg361m.302` | `zg361_mechanism_302_ai_effect` | 2 | complete | fixture-live | fixture-live | contract-complete | partial | partial | `central-wired` |
| 303 | 孵化团队的限期分布保护 | AG | P1 | `assessment` | `zg361m.303` | `zg361_mechanism_303_ai_effect` | 2 | complete | fixture-live | fixture-live | contract-complete | partial | partial | `central-wired` |
| 304 | 项目归属与职能归属双家长 | AG | P1 | `organization` | `zg361m.304` | `zg361_mechanism_304_ai_effect` | 2 | complete | fixture-live | fixture-live | contract-complete | partial | partial | `central-wired` |
| 305 | 校准前重组静默期 | AG | P1 | `calibration` | `zg361m.305` | `zg361_mechanism_305_ai_effect` | 2 | complete | fixture-live | fixture-live | contract-complete | partial | partial | `central-wired` |
| 306 | 双帽临时负责人容量拆分 | AG | P1 | `organization` | `zg361m.306` | `zg361_mechanism_306_ai_effect` | 2 | complete | fixture-live | fixture-live | contract-complete | partial | partial | `central-wired` |
| 307 | 利润中心 / 成本中心记分卡 | AG | P1 | `assessment` | `zg361m.307` | `zg361_mechanism_307_ai_effect` | 2 | complete | fixture-live | fixture-live | contract-complete | partial | partial | `central-wired` |
| 308 | 管理岗与专业岗比例 | AG | P2 | `organization` | `zg361m.308` | `zg361_mechanism_308_ai_effect` | 2 | complete | fixture-live | fixture-live | contract-complete | partial | partial | `central-wired` |
| 309 | 边远团队的可见度折损 | AG | P1 | `organization` | `zg361m.309` | `zg361_mechanism_309_ai_effect` | 2 | complete | fixture-live | fixture-live | contract-complete | partial | partial | `central-wired` |
| 310 | 并入团队的旧档映射 | AG | P1 | `governance` | `zg361m.310` | `zg361_mechanism_310_ai_effect` | 2 | complete | fixture-live | fixture-live | contract-complete | partial | partial | `central-wired` |
| 311 | 战略转向不得倒改旧目标 | AG | P1 | `governance` | `zg361m.311` | `zg361_mechanism_311_ai_effect` | 2 | complete | fixture-live | fixture-live | contract-complete | partial | partial | `central-wired` |
| 312 | 内部岗位全量挂牌 | AH | P1 | `organization` | `zg361m.312` | `zg361_mechanism_312_ai_effect` | 2 | complete | fixture-live | fixture-live | contract-complete | partial | partial | `central-wired` |
| 313 | 原经理推荐信标准化 | AH | P1 | `governance` | `zg361m.313` | `zg361_mechanism_313_ai_effect` | 2 | complete | fixture-live | fixture-live | contract-complete | partial | partial | `central-wired` |
| 314 | 跨地域调任包 | AH | P2 | `compensation` | `zg361m.314` | `zg361_mechanism_314_ai_effect` | 2 | complete | fixture-live | fixture-live | contract-complete | partial | partial | `central-wired` |
| 315 | 转岗试运行与双向退出 | AH | P1 | `organization` | `zg361m.315` | `zg361_mechanism_315_ai_effect` | 2 | complete | fixture-live | fixture-live | contract-complete | partial | partial | `central-wired` |
| 316 | 转岗薪酬带映射 | AH | P1 | `compensation` | `zg361m.316` | `zg361_mechanism_316_ai_effect` | 2 | complete | fixture-live | fixture-live | contract-complete | partial | partial | `central-wired` |
| 317 | 未录用转岗申请的保密 | AH | P1 | `governance` | `zg361m.317` | `zg361_mechanism_317_ai_effect` | 2 | complete | fixture-live | fixture-live | contract-complete | partial | partial | `central-wired` |
| 318 | 转岗申请频率与占位费 | AH | P2 | `organization` | `zg361m.318` | `zg361_mechanism_318_ai_effect` | 2 | complete | fixture-live | fixture-live | contract-complete | partial | partial | `central-wired` |
| 319 | 原团队一次反 Offer 后必须放人 | AH | P1 | `organization` | `zg361m.319` | `zg361_mechanism_319_ai_effect` | 2 | complete | fixture-live | fixture-live | contract-complete | partial | partial | `central-wired` |
| 320 | 离职访谈的聚合信号 | AH | P1 | `data` | `zg361m.320` | `zg361_mechanism_320_ai_effect` | 2 | complete | fixture-live | fixture-live | contract-complete | partial | partial | `central-wired` |
| 321 | 离职人才库与回流关系 | AH | P2 | `organization` | `zg361m.321` | `zg361_mechanism_321_ai_effect` | 2 | complete | fixture-live | fixture-live | contract-complete | partial | partial | `central-wired` |
| 322 | 回流人才的旧账与新证据 | AH | P1 | `assessment` | `zg361m.322` | `zg361_mechanism_322_ai_effect` | 2 | complete | fixture-live | fixture-live | contract-complete | partial | partial | `central-wired` |
| 323 | 学习预算争夺 | AI | P1 | `learning` | `zg361m.323` | `zg361_mechanism_323_ai_effect` | 2 | complete | fixture-live | fixture-live | contract-complete | partial | partial | `central-wired` |
| 324 | 结课 / 应用 / 业务结果三阶段 | AI | P1 | `learning` | `zg361m.324` | `zg361_mechanism_324_ai_effect` | 2 | complete | fixture-live | fixture-live | contract-complete | partial | partial | `central-wired` |
| 325 | 证书 KPI 与能力抽测 | AI | P1 | `learning` | `zg361m.325` | `zg361_mechanism_325_ai_effect` | 2 | complete | fixture-live | fixture-live | contract-complete | partial | partial | `central-wired` |
| 326 | 外部会议与行业曝光 | AI | P2 | `learning` | `zg361m.326` | `zg361_mechanism_326_ai_effect` | 2 | complete | fixture-live | fixture-live | contract-complete | partial | partial | `central-wired` |
| 327 | 内部授课分账 | AI | P1 | `learning` | `zg361m.327` | `zg361_mechanism_327_ai_effect` | 2 | complete | fixture-live | fixture-live | contract-complete | partial | partial | `central-wired` |
| 328 | 专业共同体贡献 | AI | P2 | `learning` | `zg361m.328` | `zg361_mechanism_328_ai_effect` | 2 | complete | fixture-live | fixture-live | contract-complete | partial | partial | `central-wired` |
| 329 | 跨团队导师匹配 | AI | P1 | `learning` | `zg361m.329` | `zg361_mechanism_329_ai_effect` | 2 | complete | fixture-live | fixture-live | contract-complete | partial | partial | `central-wired` |
| 330 | 衰退业务再技能化 | AI | P1 | `learning` | `zg361m.330` | `zg361_mechanism_330_ai_effect` | 2 | complete | fixture-live | fixture-live | contract-complete | partial | partial | `central-wired` |
| 331 | 受保护的学习时间 | AI | P1 | `learning` | `zg361m.331` | `zg361_mechanism_331_ai_effect` | 2 | complete | fixture-live | fixture-live | contract-complete | partial | partial | `central-wired` |
| 332 | 继任演练与灾备替岗 | AI | P1 | `learning` | `zg361m.332` | `zg361_mechanism_332_ai_effect` | 2 | complete | fixture-live | fixture-live | contract-complete | partial | partial | `central-wired` |
| 333 | 高价培训服务承诺 | AI | P2 | `learning` | `zg361m.333` | `zg361_mechanism_333_ai_effect` | 2 | complete | fixture-live | fixture-live | contract-complete | partial | partial | `central-wired` |
| 334 | 统一需求入口与来源标签 | AJ | P1 | `delivery` | `zg361m.334` | `zg361_mechanism_334_ai_effect` | 3 | complete | fixture-live | fixture-live | contract-complete | partial | partial | `central-wired` |
| 335 | 紧急插单预算 | AJ | P1 | `delivery` | `zg361m.335` | `zg361_mechanism_335_ai_effect` | 3 | complete | fixture-live | fixture-live | contract-complete | partial | partial | `central-wired` |
| 336 | 需求准入完成定义 | AJ | P1 | `delivery` | `zg361m.336` | `zg361_mechanism_336_ai_effect` | 3 | complete | fixture-live | fixture-live | contract-complete | partial | partial | `central-wired` |
| 337 | 需求变更税 | AJ | P1 | `delivery` | `zg361m.337` | `zg361_mechanism_337_ai_effect` | 3 | complete | fixture-live | fixture-live | contract-complete | partial | partial | `central-wired` |
| 338 | 范围—期限—质量三角签字 | AJ | P1 | `delivery` | `zg361m.338` | `zg361_mechanism_338_ai_effect` | 3 | complete | fixture-live | fixture-live | contract-complete | partial | partial | `central-wired` |
| 339 | 估算校准而非只奖准时 | AJ | P1 | `data` | `zg361m.339` | `zg361_mechanism_339_ai_effect` | 3 | complete | fixture-live | fixture-live | contract-complete | partial | partial | `central-wired` |
| 340 | 在制品上限（WIP） | AJ | P1 | `workload` | `zg361m.340` | `zg361_mechanism_340_ai_effect` | 3 | complete | fixture-live | fixture-live | contract-complete | partial | partial | `central-wired` |
| 341 | 跨周期未完工债 | AJ | P1 | `delivery` | `zg361m.341` | `zg361_mechanism_341_ai_effect` | 3 | complete | fixture-live | fixture-live | contract-complete | partial | partial | `central-wired` |
| 342 | 阻塞时间归因 | AJ | P1 | `delivery` | `zg361m.342` | `zg361_mechanism_342_ai_effect` | 3 | complete | fixture-live | fixture-live | contract-complete | partial | partial | `central-wired` |
| 343 | 提出、执行、验收三方签收 | AJ | P1 | `delivery` | `zg361m.343` | `zg361_mechanism_343_ai_effect` | 3 | complete | fixture-live | fixture-live | contract-complete | partial | partial | `central-wired` |
| 344 | 上线 / 采用 / 价值三阶段结算 | AJ | P1 | `delivery` | `zg361m.344` | `zg361_mechanism_344_ai_effect` | 3 | complete | fixture-live | fixture-live | contract-complete | partial | partial | `central-wired` |
| 345 | 年度 / 半年度 / 季度周期 | AK | P2 | `governance` | `zg361m.345` | `zg361_mechanism_345_ai_effect` | 3 | complete | fixture-live | fixture-live | contract-complete | partial | partial | `central-wired` |
| 346 | 周期外重大表现信号 | AK | P1 | `assessment` | `zg361m.346` | `zg361_mechanism_346_ai_effect` | 3 | complete | fixture-live | fixture-live | contract-complete | partial | partial | `central-wired` |
| 347 | 经理人工 Override 预算 | AK | P1 | `calibration` | `zg361m.347` | `zg361_mechanism_347_ai_effect` | 3 | complete | fixture-live | fixture-live | contract-complete | partial | partial | `central-wired` |
| 348 | 制度例外自动到期 | AK | P1 | `governance` | `zg361m.348` | `zg361_mechanism_348_ai_effect` | 3 | complete | fixture-live | fixture-live | contract-complete | partial | partial | `central-wired` |
| 349 | 抽查率与审计成本 | AK | P2 | `governance` | `zg361m.349` | `zg361_mechanism_349_ai_effect` | 3 | complete | fixture-live | fixture-live | contract-complete | partial | partial | `central-wired` |
| 350 | 档位通胀与跨年标杆漂移 | AK | P1 | `data` | `zg361m.350` | `zg361_mechanism_350_ai_effect` | 3 | complete | fixture-live | fixture-live | contract-complete | partial | partial | `central-wired` |
| 351 | 分区域制度试点 | AK | P2 | `governance` | `zg361m.351` | `zg361_mechanism_351_ai_effect` | 3 | complete | fixture-live | fixture-live | contract-complete | partial | partial | `central-wired` |
| 352 | 制度改版的旧记录映射 | AK | P1 | `governance` | `zg361m.352` | `zg361_mechanism_352_ai_effect` | 3 | complete | fixture-live | fixture-live | contract-complete | partial | partial | `central-wired` |
| 353 | 绩效行政成本进入经理报表 | AK | P1 | `governance` | `zg361m.353` | `zg361_mechanism_353_ai_effect` | 3 | complete | fixture-live | fixture-live | contract-complete | partial | partial | `central-wired` |
| 354 | “公平指标”也会被刷 | AK | P2 | `governance` | `zg361m.354` | `zg361_mechanism_354_ai_effect` | 3 | complete | fixture-live | fixture-live | contract-complete | partial | partial | `central-wired` |
| 355 | 高绩效目标棘轮 | AL | P1 | `endgame` | `zg361m.355` | `zg361_mechanism_355_ai_effect` | 4 | complete | fixture-live | fixture-live | contract-complete | partial | partial | `central-wired` |
| 356 | 好消息雪藏与截止日套利 | AL | P1 | `endgame` | `zg361m.356` | `zg361_mechanism_356_ai_effect` | 4 | complete | fixture-live | fixture-live | contract-complete | partial | partial | `central-wired` |
| 357 | 先锁事实、再套 361 配额 | AL | P1 | `calibration` | `zg361m.357` | `zg361_mechanism_357_ai_effect` | 4 | complete | fixture-live | fixture-live | contract-complete | partial | partial | `ck3-live` |
| 358 | 申诉不加重原则 | AL | P1 | `governance` | `zg361m.358` | `zg361_mechanism_358_ai_effect` | 4 | complete | fixture-live | fixture-live | contract-complete | partial | partial | `central-wired` |
| 359 | 翻案后的配额回流与连环送达 | AL | P1 | `calibration` | `zg361m.359` | `zg361_mechanism_359_ai_effect` | 4 | complete | fixture-live | fixture-live | contract-complete | partial | partial | `central-wired` |
| 360 | 经理集体拒绝“硬背 C” | AL | P2 | `endgame` | `zg361m.360` | `zg361_mechanism_360_ai_effect` | 4 | complete | fixture-live | fixture-live | contract-complete | partial | partial | `central-wired` |
| 361 | 《三六一绩效宪章》 | AL | P2 | `endgame` | `zg361m.361` | `zg361_mechanism_361_ai_effect` | 4 | complete | fixture-live | fixture-live | contract-complete | partial | partial | `central-wired` |

Manifest semantic SHA-256: `dea593ac8a86a800b20fa0c23903b33554f46a41327ada31c564a53ca01f1cbd`
