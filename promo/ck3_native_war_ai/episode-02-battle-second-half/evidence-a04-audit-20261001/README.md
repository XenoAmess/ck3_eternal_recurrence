# a04 逐句机制证据

对象为旧 a04 六章、167 句的实际旁白与画面。新 a06 只修包装和引用，不能补写旧 a04 证据。证据层级分别记录：原版静态实现、公式或投影、历史原生读数、历史存档、实际 UI、同帧绑定；目录内的支持结论只适用于该句声明的范围。

| 内容 | 文件 |
| --- | --- |
| 骑士 38 句 | [逐句表](knights/sentence-audit.md) / [结构化原件](knights/sentence-audit.json) |
| 骑士次日最小配方 | [capture-nextday-plan.json](knights/capture-nextday-plan.json) |
| 新保存态验收入口 | [check_nextday_saved_status.py](knights/check_nextday_saved_status.py) |
| 增援 42 句 | [utterance-audit.json](reinforcement/utterance-audit.json) / [REVIEW.md](reinforcement/REVIEW.md) |
| 增援同帧最小配方 | [minimum-supplement.json](reinforcement/minimum-supplement.json) |
| 七处定位修复 | [locator-corrections.json](locator-corrections.json) |
| 聚合入口 | [assemble_audit.py](assemble_audit.py) |
| 开场/追击/终局/收束 87 句 | [utterance-audit.json](other/utterance-audit.json) |
| 全 167 句精确覆盖 | [audit-index.json](audit-index.json) |

聚合必须验证实际 timeline 的 key 精确集合、六章分母、无重复、中文逐字匹配，才写新 `audit-index.json`。有缺口的句子也入表，不能靠漏句获得通过。聚合与机器审计不构成人工视频签核。

实际聚合已通过：167/167、六章分母10/30/38/42/37/10，missing/duplicate均为空，中文与原a04逐字一致，共218项主张。索引 SHA-256 为 `68ADEDC0040666A45CC7873556CA28DE79C5DA94700A53F606DB49E276BC8992`。164句在声明边界内支持，另3句机制有据但原a04存在图注、缺字或放大承诺问题；新a06修复不重写旧表。

## 优先仍缺的证据

1. 当前 a02 人物 **33437 次日状态**。最终 trace 失败且没有 d27 生命行或冻结存档，名单减少及旧 020 的死亡不能代替。新 run 从冻结 d26（1066-12-30）开始，推进一天到 d27（12-31），绑定暂停原生帧后保存一次 checkpoint，严格核对该 CharacterID 的 alive/dead/death_date/reason/killer；缺失或歧义保持 UNKNOWN。保存态核验与 targeted live query 分开。
2. **增援同帧画面**。原 A01 入场 2560、旧行九字段不变及宽度1480→2220有原始读数；现有日期及人数截图缺战宽 tooltip，也未绑定 hook 瞬间。新 run 仅需推进前后两组暂停原图、snapshot/control 和人数/宽度 tooltip，绑定 run/date/native frame/revision/CombatID。暂停后人数不能冒充 join 返回时刻读数。

当前两项都是 `NOT_RUN_ENVIRONMENT_RED`。本次屏幕独占期间 Steam 原始图全黑、桌面旧时钟确认 stale，ToDesk 恢复返回错误5；新挑战码像素不证明 Steam 离线。没有启动 CK3或生成新实采 run ID；租约已释放。详见 [停止事实与机制记录](../../../../docs/ck3-native-ai/a04-mechanism-evidence-audit-2026-10-01.md)。

其他未覆盖部分也逐句列明：追击每tick一项hard不可读、UI内部人数getter未证、非零败方screen缺自然实机对拍、战分分子与硬账差10的原因未闭合、特殊部队/其他CB容器边界及普通AI主动撤退/完整概率未验证。旁白已排除或保留这些边界；不要求把未声称的机制包装成已证明。

## 原 a04 制作问题与 a06 修订

原 `reinforcement-r038` 主图日期/人数图注错误，`pursuit-p028` 箭头缺字，`knights-k035` 放大通告承诺未兑现。新 a06 已修，不改旧审计事实。七处引用只改定位，不增添观测。

[a06 成片与实测回执](../series-color-a06-20261001.md)：棕金包装与前两期一致；媒体检查通过，单视频客户端 InSync。完整真人 1× 观看、听审及 signoff 仍待完成。

独立分支 `codex/war-series-brown-gold-20261001`，工作树 `C:/w/e2gold1001`，固定底座 `d81b91be1ae6bf818f38c3c5af0d595dd4ea4752`。没有拉取、合入或接收新的 master 内容，所有旧过程资产保留。
