# 1.0.0 候选源码适配记录

状态：2026-10-03，源码／日常 L0 完成，实机 **NOT_RUN**。来源和 exact-build 输入见 [upstream.md](upstream.md)。

| 冻结源码现象 | 候选修改 | 依据／边界 |
| --- | --- | --- |
| 重复 icon 字段 | 各保留一个 | 重复键检查通过 |
| 大圣战标记与自有防守方收集并存 | 普通战争模式，自有 hook 继续收集防守者 | 原版大圣战单独定义；自动军队恢复尚未实证 |
| War scope 遍历 CB-local `target_titles` | 进入 `scope:war.casus_belli` 再读列表 | 当前原版 `war_on_actions.txt` 使用这一作用域 |
| 每县 holder 加入防守方 | 改取 top liege，排除攻击者／自有封臣／已参战者 | 独立领主集合待实机读回 |
| hook 没有玩家资格闸 | 外层战争存在性与主攻击者 `is_ai=no` | 三个 CB 同时保留 `is_ai=no` 并新增 `ai=no` |
| 无 liege 的独立角色仍访问 liege | 用不同 top-liege 条件 | 避免不存在的关系读取 |
| 失效只检查主防守方是否持地 | 检查本场任一防守方目标县 | 用 `root.war` 存在性分支；实际时序待验 |
| 胜利过滤漏掉攻击者本人／中立县 | 排除攻击者、自有封臣，限定本次防守方 realm 的目标县 | 法理外与盟友／中立县不进入列表 |
| 三档重复转移代码 | 两个专属 helper，传精确当前 WAR，一次原生头衔事务 | 保留 create／resolve 原生交易；不寻找其他战争 |
| 空 `vassals_taken` 无生产者 | 删除空循环 | 保留直接取得县／男爵领，未改为自动封臣化 |
| 战败显示白和平描述、王国 war_name 指向 CB 名称 | 新双语结果说明及已有战争名称 key | 三类结算 effect 保护战争存在性，预览不读不存在的战争 |
| 旧压力处理入口 | 对照 1.20 使用 `stress_and_fulfillment_impact` | 原角色权重保留 |
| descriptor 含上游 ID／旧版本 | 维护版 1.0.0／`1.20.*`，无 remote ID，原图保留 | 新 Workshop 目标未创建 |

保留三档公开 `*_de_jure_greatwar` CB key、`de_jure_greatwar_start` 子 hook、十二个上游本地化 key、威望等级／实际费用、相邻陆海候选、法理目标、0.8 占领阈值、胜利／白和／战败附加效果、死亡继承与停战政策。`on_war_started` 只声明子钩子，没有替换原版 effect。

公开 CB ID 相同，玩家只应启用原作或维护版其中一个。进行中的旧大圣战会读新定义；保存重载尚未验收，不能声称已有战争无缝迁移。首版建议开始新战争，旧战争另列矩阵。

正式 16 文件：3 CB、1 hook、1 effect 文件（2 helper）、9 yml、descriptor、thumbnail。`tools/product.py` 冻结合同；自身 builder 复用公共原语，拒绝覆盖旧 staging，正式 build 要求产品 clean 与 `de-jure-conquest-v1.0.0` HEAD tag。docs／tools／原始 bytes 不入包。

`tools/gen_acceptance_fixture.py` 只生成外置 attempt，并先 parse 源码；`tools/verify_fixture_log.py` 只核精确 marker。夹具不进 production，不启动游戏、上传或制造人工签核。
