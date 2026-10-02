# E2-02/03：A05 追击镜头与 004 数值重绑审计（2026-09-28）

结论：**A05 可作为第 28–31 日同一新回放的镜头候选，004 的追击数字已用 A05 原生响应独立重算并得到相同结果。** 这不把 A05 说成 004 的同一次录像。A05 原速片尚未完成 clean spans 与人工 1× 审阅，当前只能建立拍摄/剪辑候选和卡片重绑依据。

## 来源与逐叶核对

004 的研究回放始于接战 save SHA-256 `45CCE7E9A7E505C878F661333DE30D6B459DA638259A9E99990A226CE564245F`；A05 从 004 第 27 日另存的**精确相同字节** `trace-d27-immutable.ck3` 冷启，SHA-256 `F085D8ABB89A354FA1004DBE8800505BC952AA8A68C0EA21AAB788F9875FEEB3`。A05 `ck3-output/capture-report.json` SHA-256 `4071162AE68C384CF5AFDAAC3D9D33A3DF264E44D87CF49662383513DEFCD504` 明确绑定这个 save，且受管清场完成。两次运行保有不同的原生 response 和 media SHA。

| 日 | date_raw | A05 原生 control SHA-256 | 004 原生 control SHA-256 | A05 a02 可见 mark 截图 SHA-256 | 录像 PTS 导航点* |
| --- | ---: | --- | --- | --- | ---: |
| 28 | 53146896 | `5693FDBED5B6EDDC077729A5C4C8E9AF68DDE5C5D5E1E59D4B3DF12426D059C7` | `098BD65D68ED7FBE3B16A004A50D3520F49C94B6506A31FF53C78C69E98D94C8` | `13E6137542D6D38B557373989CCA33624B74DAD2E3E896DCF07B4F22F9CC414B` | 73.467 s |
| 29 | 53146920 | `5DB5FECEB82644F6B9917960612EF9802E8D6BD97504FB03B7DD6C28BE392725` | `05166B050CBB89E430384A199ABC537575ADFCDB0707A83B4B277FA3122A2907` | `E022D1D650C1F54B7F74667AB7212F0B5129D497249521455BA9570DE5AF0523` | 154.133 s |
| 30 | 53146944 | `2C44360FCABE4854767AAD71F7E633ED258D4E9C9ABFA0207DD97A2D51C8E13C` | `EA17AF92EFEDB8DBD0E55D4ADC77852126561CF23EC18D107E91441C515104C9` | `837D6C4194E7F3C21C0F1502B2F81ECC24AF2E3B06520F812C880997531FB137` | 226.200 s |
| 31 | 53146968 | `85269149AB826FEFAD52D7397892F28180F0195655CE7B7D2DD9B8A6EF2AA20D` | `90AF370ADCC38FC82F48D6E66D89ADB215F830BA4AB5A79ECA1B9D69F59CEC0B` | `B12C570A10A13678045B26C408E29E5970005539D55695E1E345ED452503ACE2` | 328.900 s |

*PTS 只供寻找镜头；mark 的墙钟偏移不是视频 PTS。A05 原件位于 `D:/workspace/ck3_native_war_ai_promo_work/episode02-terminal-pair-20260928-a05-live/ck3-output/interactive-requests-responses/e2t-s02-d{28..31}-control.json`，旧 004 原件为 `episode01-full-edge-attempt-004/ck3-output/interactive-requests-responses/term-d{28..31}-control.json`。

可重跑的只读脚本 `audit_a05_pursuit_against_004.py` SHA-256 `B40548ECA4DE4262AE5A032346A9054F3EB5BB85F2C9BEE03FED06DBBF508275`；外置 append-only 回执 `episode02-a05-vs-004-pursuit-20260928-a02.json` SHA-256 `29DAFCB16C34A994C41A1E950F4F46A5F39A73F97DDE7043BD2D41F339E03CD6`。四日 `battle_control_snapshot` 排除只随会话变化的 revision 后，各有**两处**差异：A05 新 DLL 在进攻、守备侧新增 `stored_terminal_loss_baseline_raw`，004 旧响应没有该字段。再排除这两个新增终局字段，原生追击控制的所有其他叶子四日均 **0 差**：日期、CombatID、phase day、胜者、参战军队、逐团人数/软硬伤、有效属性、追击修正与其他原生读数都由逐叶比较覆盖。新增字段不得从旧 004 凭空补回；A05 终局 writer 自己提供其终战账输入。

## 用 A05 自有原件重新计算

`build_a05_pursuit_parity_adapter.py` SHA-256 `188B76C912A44F731EF17EEAFF2FF8C2262C619A04BB3FD7246BD57F08E49097` 把 A05 五份原生响应**逐字节复制**到旧比较器要求的 `term-dXX` 输入布局，并写明每份 A05 原路径/哈希；它不是 004 的副本或连续录像。外置适配目录 `episode02-a05-pursuit-parity-adapter-20260928-a01/` 的 `a05-adapter-provenance.json` SHA-256 `D5C5FA070F761A1B5A2B668777380B9C98443FC05632A981B8B96080BC6CCCAE`、索引 SHA-256 `E4D5019B67A285AD3AD28E01065C4F4D02199C230E884A0EFBECEB8D4FB5B52F`。复用正式只读比较器 `ck3_autonomous_player/tools/compare_native_pursuit_receipts.py` SHA-256 `336490161FE30300639B4F2B19B86E9575890ACC75C61C185E82B59D955AFF39` 重算得到 `episode02-a05-pursuit-parity-20260928-a01.json` SHA-256 `66E257FB4E9963AF8BFD68B68501E9D2E67536E538B16DA34A901D10624353E5`；其 `source_index_sha256` 指向上述 **A05** 索引，`terminal_source_sha256` 指向 A05 新 writer `3CAC1F8F89545C299A957EB49C1B8636BB9A14C2707680A458FA8104EF9B1782`。

| A05 三次追击写回 | 28→29 | 29→30 | 30→31 | 合计 |
| --- | ---: | ---: | ---: | ---: |
| 追击伤害原始 Q100000 | 75,203,000 | 75,203,000 | 75,203,000 | 按日重算 |
| 软伤转硬伤原始 Q100000 | 2,070,677 | 2,097,473 | 2,126,119 | 6,294,269 |
| 等价人数 | 20.70677 | 20.97473 | 21.26119 | 62.94269 |
| 原生/模型软伤逐团零差 | 24/24 | 24/24 | 24/24 | 72/72 |
| 原生可读硬伤账零差 | 23/23 | 23/23 | 23/23 | 69/69 |

A05 链式推演 72/72、当前战斗人数稳定 72/72；三日坚韧软伤预算分别为 `1,489,459,979 / 1,452,047,877 / 1,414,150,820` 原始 Q100000。以上与 004 正式 v4 卡中的数字相同，但上表的证据来源是 **A05 自己的五份原生响应和这次重算**，而非借用 004 的结果哈希。旧 v4 报告 SHA-256 `0804F89A4F2F1007CBDCF49123EB6882FD667E283BA04ACDE9A35988A97425EC` 仅供对照。

## 画面与口播准入

A05 a02 原速 `e2-09-terminal-a02.mkv` SHA-256 `25A13691259215848D77EAAB8AED9C0E281AF59A8AEB126E5D726EC6FE73A9BC`，四张既有原生 mark 截图目视均可见追击战斗面板上部、逐日日期与双方人数；第 31 日（1067-01-03）画面已覆盖旧 004 的 100 秒录像所缺的日期。面板底部逐团条目在 1920×1080 被画面边沿截去，逐团数值应由明确来源的独立研究卡显示，不能当作游戏画面已直接展示。A05 逐帧 PTS 审计 `episode02-terminal-pair-a05-pts-audit-20260928-a03.json` SHA-256 `6FDE20151A6E51EC760BB6CFFAA0B30DC21413363A74149100D949681FC16391` 报告 a02 有 **271.267–278.833 秒的 7.566 秒缺帧间隙**，在第 30 日与第 31 日 mark 之间。正式 clean-span 不能直接跨过此缺帧区；各暂停镜头也仍须从 raw 逐帧定位并 1× 审阅。

当前 `cards/calculation-cards.json` 的 E2-02/03 仍标 `replay: 004`，旁白第 28、32、116 行及 `[^pursuit]` 仍明确称 004（本轮所核字节 SHA：卡 JSON `BA8989D92CAD1FD4F4772429B37E3E0290D00B67AC1671D9F3BED81D155A49EC`；旁白 `0E179F8A40FE36BFDFE251A551B68CA002B774BFB2E2123EF7A3D3297212CD15`）。若选用 A05 第 28–31 日画面，应制作 **A05 来源卡与回执绑定的 E2-02/03 卡版**，并调整说“第 004 次独立回放”的口播/字幕来源；数字可沿用本次 A05 重算结果。不得把旧 004 的第 28–30 日录像与 A05 第 31 日片段无分轨地接成一条连续实况。是否用 A05 仍取决于正式 raw clean spans 与人工审片。

复核命令（`<verified-python>` 为已核验解释器，各次 `--output` / `--output-dir` 取新的 append-only 路径）：

```text
<verified-python> audit_a05_pursuit_against_004.py --a05-root <A05-live-root> --004-root <004-root> --output <new-comparison.json>
<verified-python> build_a05_pursuit_parity_adapter.py --a05-root <A05-live-root> --output-dir <new-adapter-dir>
<verified-python> ck3_autonomous_player/tools/compare_native_pursuit_receipts.py --attempt <new-adapter-dir> --output <new-A05-parity.json>
```
