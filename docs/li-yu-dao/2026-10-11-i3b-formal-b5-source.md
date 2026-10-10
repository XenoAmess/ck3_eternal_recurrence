# 2026-10-11 正式 I3b B5 公共冷载入口

正式 B5 已接入公共验收入口，源码状态为 STATIC_READY，实机仍为 NOT_RUN。一期保持 **75% / NOT_GREEN**；B4、B5、C3及完整I4仍须取得各自实际证据。

`i3b-formal-b5` 仅接受同一公共运行时下已实际 verify exit0、正常闭场的正式 B4。prepare 核验原始 verify 回执、B4 新 SAVE、完整87项前置/88项后置保护、全部45项继承缓存和动态生成头衔。缺少 B4 PASS、只完成行政清理、保护失败、种子/manifest 不一致均拒绝。R26 失败世界只提供字段映射研究证据，不是合法基线。

新场冷载原 B4 checkpoint，核对持久事件身份及动态 Title。在同一暂停帧取得一次 SAVE 和 G2/G3/继承缓存，验证四项显式 yes 字段与精确 law95、完整88项保护和有序45项缓存；未知值拒绝。此场没有工厂、选项点击或自然推进，沿用公共预算及90秒正常关闭预留。

2026-10-11 04:01:15–04:01:21 CST，MAIN 的新增8项针对性测试实际 exit0，6.077秒。覆盖合法合成管线、B4前提失败、运行时/存档不一致、动态头衔、严格字段和法例、UNKNOWN及额外法例拒绝、单次SAVE与零工厂/选择/推进。SAVE reader 在这些测试中使用替身，不能据此声称真实存档或游戏业务通过。原外置 provider 的7项测试仅引用已有结果，没有重跑。新增测试已接入官方 CI。

[小型原始证据索引](acceptance/2026-10-11-i3b-formal-b5-source/INDEX.actual.json)绑定采用补丁、独立审阅、源检查、原 git apply 和实际测试回执。`open_kaishek` 为 not-applicable：本包覆盖 Python 公共入口、来源绑定及合成验收拒绝，没有新 CK3 script 语义。未启动 CK3，未改变 Steam，未复制大存档、旧场景或缓存。

下一门槛仍是正式 B4 合格世界；不得为取得该前提重复执行没有新判别/修复的旧失败工厂。B5 路由可随下一次共同 Python source 冻结，当前 Source12/native 构建固定在05717072b，不能把这次 MAIN 修改追认到已冻结输入。

## 04:26 CST：官方CI发现的公共选择约束修正

源码提交afbb255398的[官方CI](https://github.com/XenoAmess/ck3_eternal_recurrence/actions/runs/38082794054)实际失败：通用adapter检查拒绝B5重复写死游戏EXE哈希。原8项合成测试通过仍有效，不能据此把整个CI写成通过。后继queue提交也携带这一未修正版本。

最小修复删除B5重复的版本/EXE常量，从现有精确bytes/SHA绑定的字段证据读取两项，只核查询与字段映射的兼容性；公共runtime仍唯一选择host/source/native。两份JSON、reader/source/evidence绑定和通用检查保持。04:26:02 CST，两个直接受影响B5检查及原失败通用检查共3项实际exit0；旧8项未全量重跑。[原失败与修正小证据](acceptance/2026-10-11-i3b-formal-b5-source/build-binding-fix/INDEX.actual.json)分别保留。新HEAD官方CI另行确认，B4/B5实机仍待。
