# 信仰与权力第一期：本地审阅与游玩智能体研究入口

第一期本地审阅版已完成：[观看MP4](C:/workspace/ck3-faith-and-power-20261017/episode01/production-candidate/formal-full-review-build-a01/native-run/derived/direct/episode01-review.mp4)，约19分25秒，2560×1440／30fps，中英双语字幕。[文稿、三套字幕、11章时间和来源索引](C:/workspace/ck3-faith-and-power-20261017/episode01/production-candidate/formal-full-review-build-a01/local-delivery/README.md)齐备，精确元数据见[交付索引](faith-and-power-episode01-review-delivery.json)。用户已授权本地先交，本次没有上传。

machine_id: **4-8e1c2f1861**；实际成片于2026-10-17T17:37:10.826053+00:00收口，Root小回执读回时间2026-10-17T17:42:03.547494+00:00。制作代码d4d049561266cbabd8b4c0cc31e38f9ce6fa6be0，实际作者输入SHA b675ecff0a84cacdbeefb257aa86ed5645ffd61c201e9a470822ca967913da80。MP4为73,514,400 B、容器1164.821354秒；34944帧视频时钟1164.8秒。成片SHA-256 `92e3c83641f57fb2e60eed09c583856813149b18a28813bf75c46ba7617f7071`。

| 研究/实证 | 帮助规划的已知结果与范围 |
|---|---|
| [R5采用](faith-and-power-episode01-r0005-adoption.md) | 旧额外2000准备分支；采用已有32实付1000，2250→1250，普通成员和空库存独立读回。 |
| [R6准备](faith-and-power-episode01-r0006-observations.md) | 从原F另开准备，累计额外5000；钱包2250→5250、奉献3000→6000/level3→4、个人rite13→15，采用后C2钱包4250。 |
| [R7重规划](faith-and-power-episode01-replanning-r7-12004.md) | 从C2独立恢复；Emax拒绝后降26再升32，各1000，4250→3250→2250，各决议冷却独立。 |
| [R7圣物](faith-and-power-episode01-relic-r7-12004.md) | 237供奉/撤回使32 Active false→true→false、有效稀有度0→4→0；钱包2250→2250→1750。 |
| [R8弃用](faith-and-power-episode01-r8-abandon-12004.md) | 从原C2另恢复；退出32实付1000，T/E/R6/3/3→5/3/2，Faith51仍保留主要关系。 |
| [R8新建](faith-and-power-episode01-r8-create-12004.md) | 接W后3250钱包；一件237/rarity4合法，新建326智慧普通圣地，实付2000至1250，Active/库存/owner后验完成。 |
| [R8保存闭场](faith-and-power-episode01-r8-closure.md) | D3保存/冻结和正常GUI OS0/CAS已验；Driver绑定仍mismatch、restore未验，public verify2/research holder。 |

R7、R8分别从原C2恢复；R7撤回后的1750不能接成R8起点，只有R8 Create接W后的3250。实验准备已明确获准并披露；其资源与结果不增加普通罗贝尔成绩。

最新版本化知识入口ck3_query_holy_site_planning_knowledge_v1支持adopt/create/promote/demote/abandon/enshrine_relic/remove_relic七类。它提供源码条件和带范围的历史证据，当前state未观察、native legality未知、action_ready=false。早期[能力审计](faith-and-power-mcp-capabilities-12004.md)是历史截点，后续原生观察与动作边界见R5–R8专题及索引中的guarded action合同，当前运行权限和默认关闭守卫继续生效。

智能体按以下顺序消费：

1. 当前context与snapshot先读actor/run、个人Rite、Faith/main Rite、完整成员及每Faith等级、县主、artifact owner/库存/槽/认可。有效ID0不能当缺失。
2. 保留全部正常Can失败条件，记录可得报价及新鲜度、钱包/整链预算，分别查询free与decision/creation冷却；未知不转false。Create缓存报价不冒充最终新鲜成本。
3. 绑定当前选择元组、预览和未消费意图，只提交一次。ACK、窗口reset或accepted字段均不单独证明结果；dispatch后pending时继续查询，不盲目重试。
4. 独立读付款、成员差集、明确目标或新实例、等级、owner/槽、冷却与Active，再重新规划。普通Active与主要全Faith效果分开，具体受益者修正另验。

D3已保存/冻结，但Driver save_binding_mismatch未修验、restore未验；保存文件不等于完整恢复链通过。奉献后态、创建冷却、王国数、全部受益者及净收益仍有未测项。research holder闭场不等于whole-product PASS，原片QA不等于正式影片人审。

全片严格音视频解码、34944帧PTS、105句的三套SRT精确文本/时序及声轨信号检查通过；制作源双CI成功（Official109步、Linear）。原片278.2秒／23.884%，源码静图190.5秒、原生读回214.5秒、动态源码图解481.6秒；后者有明确标注，不算实机。原片区间没有循环，包含原始暂停UI。Root已读105句稿并直接看11张实际帧，关键W/Create结果字幕在后态出现；完整1倍速人工观看、听审和clean-span签核仍待审。00:32三账图的首步与“信仰名单”旁白有时序润色项，列入审片说明。旧29:24研究讲解版与3:34短段保留各自历史，本次入口指向新正式审阅版。
