# 天朝制允许经商&贪腐框架（XenoAmess维护版）

面向 CK3 1.20.0.3 的独立维护版，基于 Steam Workshop 物品 `3596263413`
（`Corruption & Trading under the Celestial government`）的玩法与素材继续开发。

核心内容：

- 为原版 `celestial_government` 增加 `barter = yes`，使天朝制角色进入原版易货与商旅系统；
- 为天朝属官提供四档贪腐策略，分别少缴 5%、10%、15%、25% 的天朝税赋；
- 贪腐特质提供易货产出，并同步施加功绩、民望、压力与治理代价；
- AI 按性格权重选择策略，角色也可暂时收手或永久退出该框架。

维护版不会覆盖原版 `feast.txt` 或 `window_county_view.gui`。当前原版 CK3 已原生支持宴会的
易货货物成本；旧 GUI 整文件覆盖会回退当前原版的快捷键与特殊建筑界面。

上游出处、精确提交、兼容性差分和授权确认记录见
[`docs/compatibility-audit.md`](docs/compatibility-audit.md)。

## 验收与发布状态

- `1.0.0` 已发布到维护版 Workshop 物品 [`3804807463`](https://steamcommunity.com/sharedfiles/filedetails/?id=3804807463)；上游物品 `3596263413` 未被修改。
- CK3 `1.19.0.6` 简体中文隔离实机验收及全新订阅缓存复验均 GREEN：正式决议与事件完成 UI 往返，天朝易货规则、第四档特质和 `0.75 - 0.25 = 0.50` 税率计算均由引擎确认。实机验收只使用简体中文。
- 正式 staging 由 `py tools/build_celestial_commerce_corruption_release.py` 生成，共 22 个运行文件；不要直接上传源码目录。
- 简中、英语及法、德、日、韩、波、俄、西九语已纳入正式 staging；后续实机验收只用简体中文，英语及其他非简中语言仅检查键集、编码/BOM、header、保护 token、转义与可解析格式，不要求数字语义、术语、文字种类或游戏内签核。1.0.0 的旧审阅过程保留为历史记录。
- 工坊标题、主描述（含 `1.0.0` 更新日志段）和完整 Steam Change Notes 已匿名精确回读；正式发布记录见 [`docs/release-changelogs/celestial-commerce-corruption/1.0.0.md`](../docs/release-changelogs/celestial-commerce-corruption/1.0.0.md)。
- 上游下载未附许可证；仓库所有者已于 2026-09-20 明确确认取得原作者对维护版再分发与发布的许可，并指示据此执行。授权原件仍待所有者方便时补档。

## 1.20.0.3 维护候选

拟定版本 1.0.1，尚未发布。相对公开版 1.0.0，天朝政府迁移为完整原版 1.20 定义，保留新行政机制、属官发展、东亚庄园、天朝官僚、俸禄、军事与部院预算、AI 传奇与可授予神权政府的能力，仅额外启用 barter。
四档特质、税率、事件、决议、三年冷却及九语本地化没有玩法改动。1.20.0.2 的核心与代表生产 UI 记录只作历史，不代替 1.20.0.3 验收。

## 2026-10-07（上海）CCC25 / R0011 / a84：本轮源业务与正常退出已验

CK3 1.20.0.3 简中源场复用 Source18/runtime31/原 f150 DLL；D0–D3 及生产 GUI Confirm、真实 `xccc.1001` 新事件 `.f` 一次选择后独立 eventgone 已完成，D1 的 `date_raw +24` 为24小时/1天。既有核心11标记各1、XCA/XCA120两族FAIL0复用 R0003 原件，不重新计入本场。Root于 UTC17:39:36 亲审本场原图，确认角色29959的 `xccc_corruption_1` 至 `_4` 全部缺失，实际 Confirm 日1066-09-18、禁用决议/确认按钮的冷却日1069-09-18；没有再推进三年。保留进程句柄独立读得OS0，native退出0、job0/treegone、cleanup及managed thread完成；最终报告27步全ok、GREEN/error=null，于UTC17:27:31.305704结束（27,243,296B，SHA `c3d880f42e7b18e6ccd04fa17a0004d37ee0f34fc7b3280cb3f9003ba3765c32`）。Keeper真实exit0/thread_exited、末序4532后CAS4533 done/resources=[]。事实与原件pins见[当次事实索引](C:/workspace/ck3-upgrade-20261006/ccc-source-acceptance-text-write-diagnostic-01/actual-source-R0011-01/actual-facts-draft.json)及[Root最终亲审](C:/workspace/ck3-upgrade-20261006/resume-root-01/a84-root-actual-business-and-normal-exit-review-01.json)（7732B，SHA `fd6f1e756bbca7c17d4d52f8548c8a5cbb5642406f19cb6a4bf161502ba65bfb`）；Root已确认本轮有界源验收通过。

GUI25外层exit1及原 `route-error-no-replay.json` 保留，business_error=null：真实managed结束后磁盘 `session.report` 仍旧为null，Root一次提交原finish17使真实状态落盘，caller随后对同一finish的提交被原queue拒绝；没有重播业务或改旧失败。此边界不写成full caller0。1.0.1仍未发布，正式tag构建、公开Notes、fresh cache代表业务及发布闭环待实际完成；不外推九语实机、全档位、永久退出、独立存读或最终国库转账量已穷举。
