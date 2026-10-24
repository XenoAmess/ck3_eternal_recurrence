# 重复角色通知：2026-10-24 诊断记录

当前结论：选中的 N0/N5 死亡通知帧各可见一张卡片；尚未复现玩家原报告，也未证明根因或修复。未完成全部 32 格，N5 只覆盖五个独立可见结算事件实例，不代表五套完整勾引 scheme。逐类型通知设置未得到实际读回，两次已执行场都保留负向公共验收结果。

机器 `desktop-3fevhd2-1c74096080`；本记录时间 `2026-10-24T00:05:17.981628+00:00`。本轮源码固定 `9ab8e9b14ecadb15ce47035bc2ea02b4cf335464`，运行时 SHA `2afce59cd300fa7ecdb30e076e28c361c307810a4e583d6198a4139a548223f6`。CK3 实际样本为 1.20.0.4；Steam appmanifest 实际 build 为 25734779，EXE 来源绑定 SHA `98702f88a547cde2eaf29a85f93b85f68ee4cf8148336a4f7afaeb75319dd518`。35 文件业务投影原 manifest 的来源提交仍为 26ee285，不将它改写成 9ab；这几场使用同一份已核对的业务字节。产品未发布到工坊。

原报告来自 [3812991990 的评论](https://steamcommunity.com/sharedfiles/filedetails/?id=3812991990#comment_581684714275963017)，作者 1668788452，2026-10-10 21:35 北京时间：勾引后，关于同一角色的右侧消息随勾引次数累加。评论没有指出消息类型，也没有玩家存档或截图。本次自行选择原版情人死亡 feed 探针，不把该类型外推为原评论实际类型。

## 实际场次

| 场次 | 实际范围 | 结果与限制 |
| --- | --- | --- |
| R0032 | actor 31254 / subject 65837；仅基线 SAVE | Root 调用注册但未 advertised 的角色窗工具，被 SDK 拒绝。case action/death 均 0；native 强退码 1，run/verify 各 2，cleanup 证明清理，CAS 8523。不能给 N0 或通知结论。 |
| R0033 | subject 65869；case 9、N0 | actor XP=5，stage=3，dead=1。repetitions 是存在的 type=value，但省略 identity；confirmed counter 不存在，不补造显式整数 0。subject 死亡压缩后 XP 消失，未保留 predeath SAVE，不能把源码 seed1 当作实测 XP1。phase 3/4 保守失败。 |
| R0034 | subject 65868；仅基线 SAVE | 因观察到计划重启提示，Root 正常关闭。未执行 mode/N5/死亡，不能冒充 N5；不声称实际已重启。CAS 8545。 |
| R0035 | subject 65860；case 12、N5 | 实际 sxant.1201–1205 的 event instances 为 3–7、native revisions 10–14，各确认一次。predeath SAVE 直接读回 actor 5→10、subject 1→6、counter=5、repetitions=5、stage=2。postdeath actor=10、stage=3、dead=1。phase 3 通知设置仍失败；实际正常闭场，case 验收失败保留。 |

R0033 和 R0035 各使用自己的真实基线，不是同一 SAVE 的反事实分支。两场基线双向 lover 各一条；R0035 五次结算结束仍各一条，没有同方向关系累加。R0035 死亡前 actor/subject 的外交、军事、管理、勇武账本分别为 ±1，健康为 ±0.00075；谋略和学识变量不存在，不能将缺失变成显式零。双方各五个对应 gain/loss 修正，未见同名重复。死亡后 subject 转入 level2 dead_prunable，其变量被引擎压缩移除；XP6 的证据明确来自真实 predeath 样本。

两场都只提交一次原版 `death_natural_causes` 探针。暂停等待未见卡片后，各探索推进额外一天，才观察到原版死亡 feed；保留零天夹具合同偏离，未宣称严格 32 格通过。R0033 frame-07 和 R0035 frame-07 均经离线原图直接审阅，各可见一张情人死亡卡片、30 压力；Root 另审 R0035 frame-00/07 也各一张。跨帧同一张卡不重计，单帧计数也不等于完整消息实例数。

postdeath SAVE 的 played_character 实际 pinned_characters 分别含 65869、65860，支持关注关系；逐类型消息设置没有原生读口或明确序列化记录。实际 pdx_settings 只保存 notifications.banner_timeout=2。原生 HUD type、subject ID、message instance ID 均不可用，不能把事件窗口的 instance ID 当成 HUD 通知实例。

## 公开 1.1.0 与关系累加假设

公开 tag `superman-qiang-v1.1.0` 指向 `f7fde816e295a62807ab636ee2d93cf307ea69cf`。已有外置补查证明：paired/unknown 性行为主体只差投影版本注释；转移、探针、特质和经验查询交互相同；当前记录 helper 只多两条跳过记录的 scope 守卫。公开版没有直接 set_relation 调用，唯一直接 toast 在主动查看经验交互。该差异检查的当时源码 HEAD 为 2d810e，未伪装成新一轮重新比较。

当前原版勾引脚本在添加 lover 前检查已有关系。当前精确 EXE 的正常 set_relation 路径按完整目标角色 ID 查 pair，并在追加前检查同一 relation-definition 指针；已存在时返回 false。双向各一条是 corresponding 关系，不是两个重复订阅。这些证据削弱“每次行为直接新增同向 lover 记录”这一具体猜测，但没有测量 HUD 下游订阅，不能覆盖所有调用方、旧存档损坏或历史 1.20.0.3 引擎。

现成 R29 基线有 14 条有向 lover、无重复，但不是重复勾引证据。旧 R21/R22 真实继承 SAVE 在 1.20.0.3 下含 118 条有向 lover、无重复；31254/32535 的真实一次勾引关系各向一条。相关六份核心文件逐字等于后来公开 tag，仍只称 1.1 核心候选，不追认为正式缓存，也未覆盖反复勾引。原始反汇编和摘录继续保留在已有 C 补查目录，本次只索引其 SHA。

## 闭场事实

R0035 原始 OS handle 在 2026-10-24T00:01:25.241967Z 实测 exit 0，birth FILETIME 为规范十进制字符串 `134372724270891329`。native host 最终 GREEN（00:05:32.769298Z），session process/CK3 均 exit 0，Job before/final 均 0、tree gone、inventory empty、cleanup=true。keeper 原分配器实测 exit 0、thread exited、最后序号 8558；CAS 8559 释放现场，新的 Steam 原生离线读回为 offline。R0033/R0034 也已有正常退出、native0、Job0 和 cleanup 的独立回执。

这些正常闭场事实不覆盖业务失败：R0035 原公共 run/verify 均实际 exit 2，`normal_close_qualified=true`，`case_acceptance_pass=false`。实际 Root 断言仅第 3 项“关系和通知设置”是 false，其余八项 true；normal-close 说明模板遗留的 false3/false4 字样不覆盖实际断言对象。原始回执保留，没有为取得通过而更改设置门槛或补造通知 ID。

公开 1.1 补查的文件比较、旧真实勾引摘录、R29 摘录，以及精确 EXE 的 RVA/跨度 SHA 已嵌入同名 JSON 的 compact_source_index。原始七份“current”比较文件已再次核实等于这几场实际加载的 35 文件业务投影；145 KB 原始反汇编仍只以外置 SHA 索引，不复制大原件。闭场后的 rebase 不改变本轮事实所绑定的 9ab 源提交。

## 证据与后续边界

同名 JSON 保存每场 assessment、decoder、原始 SAVE/melt、闭场记录及源码补查的路径、字节数和 SHA。大原件均未复制；存档 driver binding 的 unconfirmed/save_binding_mismatch 原样保留，字节和实际角色域核验不替代该身份绑定资格。

本轮没有因命名就断言 saved scope 污染，也没有把五次同一 helper 的观测外推成完整勾引流程已排除。后续仍需要覆盖公开 1.1.0 的重复完整勾引及其他角色消息类型；现有实际样本不能关闭原 bug report。

按共同存储策略 1.0.0：原始证据 720 小时复核，小型结论 180 天复核；不重置既有原件期限，引用 raw 最早复核边界保守保留为 2026-11-22T00:00:00Z，小型结论复核为 `2027-04-22T00:05:17.981628+00:00`。当前必要基线和唯一来源依实际用途保护；到期不授权自动删除。定稿时间为 2026-10-24T00:17:50.414685+00:00；本轮所有实机与 keeper 均已闭场。文档由 C 盘原始证据离线汇总后复制入库，没有为编写文档重新启动游戏、调用原生接口或再次解码。

容量操作保留两项偏差：R0030 同月 SAVE 在新鲜检查命令失败后提交；R0033 postdeath 检查超有限额度后，Root 编排未按非零退出码停止而继续 SAVE/copy/melt。原提交没有重放，后续重新核容量，不追认检查发生在写入之前。原回执为同机器外置证据根下 `ops/R0030-samemonth-capacity-admission.actual.json`、`ops/R0033-postdeath-cap-owner-reconciliation.actual.json`。有限任务估算按实时整卷占用显式重算至 464000000000 B；4 GiB 系统预留、20 GiB 物理底线和 2026-10-24T15:45Z 复核期限未变，没有清理或扩展其他资产权限。最后实际闭场容量检查为 `ops/R0035-closed-capacity-admission.actual.json`；这些估算不能代表其他机器状态。
