# 第 2 期原生战斗计算卡

2026-09-28。九张 **2560×1440 全屏独立插页**对应[下一期镜头表](../shot-list.md)的 E2-02/03/04/05/06/07/09；E2-05 拆成三张，防止把不同回放剪成同一次。画面底部 `y=1120..1439` 留白给字幕。它们只表现已取得的原生整数回执和说明，不是 CK3 实机截图，也不作为覆盖原生 UI 的叠层。现场画面、原速连续段和用户全片审阅仍按[追击与骑士证据索引](../pursuit-knight-evidence-audit-20260928.md)及[增援与终局证据索引](../join-terminal-evidence-index.md)另行取得。

| 卡 | 原版回放 | 说明 | 生成 SVG SHA-256 |
| --- | --- | --- | --- |
| [E2-02](e2-02-calculation.svg) | 004，从 attempt-002 接战存档冷载的独立回放；第 27 日存档由 004 自己生成 | 第 28 日 24 团软伤池 `62,528,090+19,904,137=82,432,227 raw`；追击伤害 `75,203,000 raw`、败方掩护聚合 `0`，首日软转硬 `2,070,677 raw`。非零掩护仍缺同帧样本。 | `D3EF3FA32AA96CBD2E120F950498069352B9385B5E4B02EE0EE8794C44BDF509` |
| [E2-03](e2-03-calculation.svg) | 同一次 004 回放 | 第 28→31 日逐日硬伤 `2,070,677+2,097,473+2,126,119=6,294,269 raw`，即 `62.94269` 人当量；72/72 soft、69/69 可读 hard 零差，另 3 项 hard 是每日一个 `null`，不能按零算。第 29/30 日没有重新喂入原版败方状态。 | `A5C13BB2A34974D7D01B7038AD7AB53C14F0F2966A5137BBF6D76087ECD8772D` |
| [E2-04](e2-04-calculation.svg) | 039 致残后档 → 040 逐字节复载 | 目标骑士 `34333` 独腿、轻伤后仍在 24 人名册；基础勇武 `3→3`、有效勇武 `11→7`，兵团 61 人数 `1→1`，有效伤害 `962.5→612.5`、坚韧 `192.5→122.5`。 | `06A320E1DF5EE316175F0208F06C0346330824A2F44B70C3F2707FCD76F0E0E0` |
| [E2-05A](e2-05a-calculation.svg) | 020，第 26 日独立回放 | 击杀者无权重选择器：19 名源骑士筛到 14 名；`1,400,813,912 % 14 = 8`，尾项填洞后的索引 8 是 `34120`。本次战报目标 `33437`；完整效果写集未证明。 | `A4F254D2DC0A59549BF6AC8A7F1345E1ACF1A6BF0956F509D63F137B31E5F330` |
| [E2-05B](e2-05b-calculation.svg) | 070，从同一第 26 日源档另起独立回放 | 成长列表原生运行时权重 `40/30/15`、正权重和 `85`；独立 draw `51,510,340` 得阈值 `2`，执行来源第 0 项 `no_op`。070 不提供 038 的后存档。 | `7EA7E24139AB2CCC01CF38308004DC20DB5EAD32F6ED46FB755F084B0D0615EE` |
| [E2-05C](e2-05c-calculation.svg) | 036 事件后档 → 038 逐字节复载 | 第 26 日事件前 `69` 团、`30` 骑士；第 27 日暂停输入 `68` 团、`29` 骑士，缺 `33437`/团 `65`。038 capture report 明确指向 036 后存档 `CD0648D7…08A55`，没有接到 070。 | `0A735D50E6460BBA9EF78B30B1A3A1CC24F1F92C5664F379BD707EAEF9D72150` |
| [E2-06](e2-06-calculation.svg) | 085，第 11 日源档独立回放 | 旧双方 entry/cache 差额，ArmyID 22 的 13 团起始 2570 人与实际 current 2560 人，返回双方残差归零。 | `767543A90732DC811BB9930929E4651971944CE92EE359BC9CFAB8675D866AF5` |
| [E2-07](e2-07-calculation.svg) | 同一次 085 回放 | join 前后 base/final 战宽 `1645/1480→2467/2220`，首次 side 0 出伤 `R8D=2220`。森林 `0.9` 是同版原版脚本静态值，非 085 同帧运行时地形字段。 | `91BCCA2B3B540E90C28A1FAE3117F522039312300B8C6702B779379E980CD527` |
| [E2-09](e2-09-calculation.svg) | 历史 024，第 27 日源档独立回放 | 024 的原生 writer 回执：分子 536.62042 人当量、八桶分母 996 人、整数比例 53.877%、CB 战分系数 150、未封顶 80.8155、单场封顶 50、战争进攻方相对 row `-50`。本卡没有新拍 run 的结果。 | `1A9EDC4CAEDC662F2F3AA44925CE1C8F7493A154273A78B258D8C020F2F5DE31` |

004 的 E2-02/03 可讲为同一条追击回放；004 的实际冷载源由其 `capture-report.json` 的 `checkpoint_source.save` 绑定到 attempt-002 接战存档 SHA `45CCE7E9...6245F`，第 27 日存档 SHA `F085D8AB...FEEB3` 则是在 004 运行中生成、供后续 024 等回放使用的检查点。039→040 和 036→038 各有自己的逐字节后档复载；020、070、036 是从第 26 日源档分别启动的回放，即使角色与战报一致，也不能拼成同一次。085 和 024 又是不同日期检查点的独立回放。每张卡顶部标 attempt，底部标 exact build、CombatID `16777218`、WarID `4`、原生日戳及**各自原始回执完整 SHA-256**。[数据表](calculation-cards.json)保留来源存档、原始响应、采集报告及终局文件路径与 SHA。038 外置 `ck3-output/capture-report.json` SHA-256 `2D09C0B1432B5E2D608B95ECDA75C143169C56404C138FF85EA266B8E5504D5D` 的 `checkpoint_source.save.path` 指向 `episode01-day26-random-list-type-attempt-036/d27-postevent-immutable.ck3`；完整本机路径见数据表。085 自己已有入场前、返回后、首次出伤三点，E2-07 无需把另一条 083 回放的第三点拼入。024 的 50 是历史单场 battle row，不等于整个战争总分；败方的正常败退也不是主动撤退证据。024 精确 DLL 已确认不可得，新配对仅有静态预检，详见[新配对证据](../terminal-new-pair-evidence-20260928.json)。

## 样式来源和复现

[渲染脚本](render_calculation_cards.py)只用 Python 标准库生成 SVG。背景 `#211813`、面板 `#35291F`、主字 `#F0E5CF`、金色 `#CBA56A`、弱线 `#61503C` 均来自系列已有的 [`war_ai_promo.visuals`](../../integration/src/war_ai_promo/visuals.py)；字体首选 **Microsoft YaHei**，与系列既有 [`war_ai_promo.common.font`](../../integration/src/war_ai_promo/common.py) 的 `msyh.ttc/msyhbd.ttc` 一致，其他平台回退 `Noto Sans CJK SC`。没有调用 CK3、外部图像生成或宣传工具链，也没有使用原版 UI 位图。

在仓库根目录使用已验证的 Python 执行：

```text
tools\.venv\Scripts\python.exe promo\ck3_native_war_ai\episode-02-battle-second-half\cards\render_calculation_cards.py --verify-sources
tools\.venv\Scripts\python.exe promo\ck3_native_war_ai\episode-02-battle-second-half\cards\render_calculation_cards.py --check --verify-sources
```

`--verify-sources` 对本机外置 attempt-004/020/024/036/038/039/040/070/085 的**全部列明来源文件**逐字节算 SHA，重复引用的大存档只读取一次；只有这些本地证据齐备时使用。跨机只检查 repo 内数据与生成 SVG 的确定性，可仅运行 `--check`。生成器在算式、回放身份、来源 SHA 或 SVG bytes 偏离时拒绝通过。SVG 是生成结果，调整文字与数值应改 JSON 或脚本后重建；不要手改 SVG。

2026-09-28 在独立 worktree 用主 worktree 的已验证 Python `3.14.7` 完成 `--check --verify-sources`；六张新增 SVG 以 Edge headless 渲染到外置 `D:/ck3-research-artifacts/episode02-pk-card-preview-20260928/`，逐张查看文字可读、面板间距和字幕安全区。E2-09 随历史来源标注勘误重新生成，其新 SHA 列于上表；此处的卡片预览不是成片人工审阅。004 有 100 秒原速 MKV，但不能覆盖其第 31/32 日终局；039/040/020/070/036/038 没有可用原始录像，卡片不能被剪作这些回放的原速游戏镜头。
