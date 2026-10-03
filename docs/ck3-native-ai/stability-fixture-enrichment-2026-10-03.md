# 2026-10-03：百年夹具与结果窗口处理富化

用户于本日明确要求将结果窗口处理和外部 mod 百年稳定性夹具富化到 `ck3_eternal_recurrence`。本包在独立 detached worktree 开发，
不改变正在执行百年游戏的冻结 checkout、配置、mod 内容、native bridge 或原 operator；所有开发验证均无 UI/Steam/CK3/SDK 操作。

公开交付为 [通用夹具和 CLI](../ck3-stability-fixture.md)，外部项目保留产品配置、模板、截图、具体事件文本、角色、存档和运行结果。
本包没有搬入第三方 mod 源码或素材，也没有公开私有存档。现有 AGENTS 的跨 mod 富化原则继续有效。

## 来源与实际证据层次

本机外部项目原生会话 `4-8e1c2f1861--uuii--R0006` 在 native current-event query timeout 后保持同一监督会话。
零 native action 的 consumer 失败与 root 后续正常 UI 游玩分别保留，不能把图像辅助当成 native query 的修复。
关键来源采用外置 evidence ID 和 hash 引用，实际截图及私人产品数据不进入本公共仓库：

| 来源 | 本包提炼内容与边界 |
| --- | --- |
| `r6-gui-century-assist-agent-a02` | 完整 ROI 包含动画时，输入前无法保持精确像素一致，会错误停机；RED 原样保留。改为文本连通分量 mask 的容差身份，但不识别字符或日期。 |
| `r6-gui-century-assist-agent-a03/attempts/20261003T025329-5652ef19fe` | 战争 shell 模板包含窗外变化地图，实际输入前被拒；不把它描述为 mod crash 或已关闭结果窗。 |
| `r6-gui-century-assist-agent-a03/attempts/20261003T031401-18403d4a0c`，result SHA `a0a359e700364989933eb0030bc8ca3abf90c7d76da454416176d8c51d4eaa52` | root 实际直接审阅同一 PID 的四选项普通事件输入前/后：195.2.18 → 普通地图195.3.3；一次 Shift+1 正常 UI 变更。这个外置 helper 的成功不等于本公共包已经实机执行。 |
| `r6-gui-century-assist-agent-a04` 的闭合 war characterization | 从窗内边框和 paper/dark 静态正文取得身份；扫描实际唯一按钮位置，比较四边模板；战争正文必须参与重复动作判定。只读闭合图分析不等于执行 Escape。 |
| R0004 普通保存/退出及后续 R0005 prelaunch RED → R0006 冷载 | 普通保存、全 CRC、唯一精确父档与原进程/keeper/CAS 释放要分层记录。prelaunch 失败没有新 gameplay 日期，不能建立虚假普通存档父链。 |

原生 MCP/SDK 仍是默认路径，桌面辅助需绑定当前失败证据和实际停止 consumer 的交接。公共包没有研究或绕过 native caller，
没有第二个 native consumer，没有改变游戏速度、角色、战争意愿或任何产品策略。

## 本公共包的验证

开发路径为本机 `C:/s100fx`（基于最新 `origin/master` 的 detached worktree）；显式选用主 worktree 既有 `.venv` 的 Python 3.14.7，
Pillow 12.3.0、psutil 7.2.2。解释器位置只是本次重现记录，不是可复用协议前提。

本公共包的 22 项必要合成回归通过；顶层及 `route`、`assist`、`verify-chain` 四项真实 CLI help 均 exit 0。
只读闭合回放共 16 帧（6 个战争结果、9 个普通事件及 1 个旧 a03 实际拒绝帧），正确进入相应视觉路由；闭合 R0004
普通 ZIP 存档全 CRC/UTF-8 metadata/player 扫描通过。只读匹配不证明 Escape/Shift+1 被执行，也不证明自然100年。
永久摘要和精确代码 hash 在 [verification.json](evidence/stability-fixture-enrichment-20261003/verification.json)，合成测试原始输出在
[test-stderr.txt](evidence/stability-fixture-enrichment-20261003/test-stderr.txt)。私有图片、模板、存档和全部 stdio 留在原外置 attempt。

初始20项回归通过；增加实际按钮位置扫描与 production guard 检查后，a01 的22项回归有1项 RED：程序画的测试按钮 `r-g=55`
超出已观察 gold 谓词，导致扫描无匹配。该失败输出保留原样，a02 仅把合成按钮改为 `r-g=30` 后22项通过；没有放宽生产谓词、
重复输入或执行实机。外置最终 verification SHA 为 `208218458934dadd597d39f90b7a1796fa494689809d613b872c174e7d8293dd`，
closed-replay SHA 为 `cef069dd660bdcec3e26c8950f18512418b9f54438006a4f3712ee97c8ae187f`。

状态分层：

- 可配置公共代码：fixture-ready；必要合成回归和闭合图回放的结果分别记录。
- 当前公共版本的 Windows SendInput、现有 SCREEN/PID guard 现场消费：未执行，无公共版本实机通过声明。
- 原外置 a03 helper 的一项 Shift+1：root 已取得实际 UI 前后证据；不外推为公共包或所有窗口已通过。
- 当前产品完整100年、自然继承链及最终日志结论：由独立产品报告负责，本富化包不标记完成。

## 遗留边界

不同分辨率、GUI scale、主题、mod 窗口和新死亡/继承变体需要产品自己的外置已审阅布局配置；本包不携带默认游戏模板。
无 native enabled/date/actor/window-instance 真值，未知模板或输入不确定时交还原操作者；不会自动重发。
map-like 匹配只用于无输入等待，不证明时间前进或 actor 正确。闭合存档扫描只支持唯一 UTF-8 ZIP `gamestate`，raw/二进制格式需以后按实际需求适配。
存档 SHA、CRC 和引用文件存在不证明自然玩法；原 operator 仍必须审阅原始动作、普通保存和自然继承证据，再作正式验收结论。

## 12:30 后的最小窗口衔接修正

后续实际 a04 attempt 在一次普通输入后频繁停止。闭合原图分析证实四个具体原因：

- `20261003T034858-94f87dcbe7`、`20261003T040712-79bcde2957` 的两帧 post 跨地图与下一事件。前次输入之后不必等待同一窗口的两帧，下一次输入仍独立稳定前置。
- `20261003T040337-43a5c3691b` 的两帧都为 root 已审阅普通地图，右侧通知栏竖边被项目 map classifier 误当中心弹窗。项目适配缩至中心窗口区，未删除未知窗口拒绝，也未把地图作为时间真值。
- `20261003T034310-69d50cfa5b/step-03/map-wait-001` 的按钮实际为中性灰连续边框，旧 gold-only 谓词误拒；物理首项亮字仍独立核对。
- 同批标准窗口的标题亮字 mask 为零，正文图示落在旧“第六项仅亮字”区域。标题缺席精确保持，正文图示按成对按钮边框排除；不让正文变化释放相同不确定首项。

外置 `r6-gui-century-assist-agent-a05/assist-v2.py` 为本次最小候选，SHA
`de54e9d90fac581cb4bb3635d77f203d9575dd020031ee9d8401fe725847e3d0`，pins SHA
`a1f217b0bbdf11012e154f84e30911fbe82f672381dcdbd302fa69ebe4683819`。
三项实际 post 闭合回放分别得到两项 `UNCONFIRMED_PENDING_NEXT_STABLE_ROUTE` 和一项普通 UI 消失；未知 post 仍拒绝。
a03、a04 的完整闭合 ledger 按精确字节继承，不能靠更换辅助目录清空历史。a04 原件和 a05 初稿（标题亮字不足拒绝）均保留；
本代理未执行任何实机输入，候选是否实机消费继续以 root 的独立产品报告为准。

公共代码只同步通用中性边框/标题缺席/成对槽识别、混合后置重新前置和旧 ledger 继承；不携带本机通知栏坐标或私人图像。
新增五项必要合成回归后，27 项全部通过（11.271 秒）；混合后置之后重新取得稳定前置、未知后置停止、跨目录历史防重均有回归覆盖。
首次 27 项运行因旧测试断言的错误消息措辞不匹配而有一项 RED，保留原运行记录；只统一错误消息后最终通过，未改变判定规则。
最终摘要、公共源码 SHA 与外置闭合 handoff SHA 在
[verification.json](evidence/stability-window-handoff-20261003/verification.json)，测试输出在
[test-stderr.txt](evidence/stability-window-handoff-20261003/test-stderr.txt)。这些结果仅证明必要夹具回归及闭合像素匹配，不是实机业务通过或百年验收结论。
