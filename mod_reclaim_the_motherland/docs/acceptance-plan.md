# 重整河山 0.2.0（二期）验收方案

状态：执行版

目标游戏：CK3 `1.19.0.6`

正式产品：`mod_reclaim_the_motherland`

Workshop item：`3798404599`

## 1. 验收目标

在不削弱一期“后朝—复辟”闭环的前提下，证明二期同时满足两项目标：

1. 最终留下的忠臣不会经过原版弱势王国/帝国裁剪及改国号入口；其主头衔对象、title key、显示/自定义名称、直属关系和下级封臣树保持不变。
2. 默认“人心离散”规则会对每名直属、有地、伯爵级以上尊王派候选人结算一次忠诚：公开决裂者必叛，强羁绊者必留，其余 AI 按冻结后的 5%–95% 概率掷一次；兼容规则“誓死尊王”仍保留一期全员留守行为。

所有验收保持 MCP-first。`open_kaishek` 先覆盖可确定解析的部分；它不支持的动态头衔、关系、概率与封臣树语义必须进入真实 CK3 paused artifact，不能用静态 PASS 替代。

## 2. L0 静态、原版合同与正式构建

使用已验证的项目虚拟环境解释器执行：

```powershell
& tools/.venv/Scripts/python.exe tools/compose_reclaim_the_motherland_key_art.py --check
& tools/.venv/Scripts/python.exe tools/test_reclaim_the_motherland_contract.py
& tools/.venv/Scripts/python.exe tools/test_build_reclaim_the_motherland_release.py
& tools/.venv/Scripts/python.exe tools/validate_reclaim_the_motherland_static.py
& tools/.venv/Scripts/python.exe tools/build_reclaim_the_motherland_release.py --check
```

通过条件：

- CK3 1.19.0.6 的两个原版覆写点及所用 trigger/effect 合同哈希仍与锁定基线一致。
- 两个游戏规则分别只有一个默认项；原版群雄割据分支完全绕过二期判定。
- 硬叛、硬留、分数修正、5/95 钳制、AI 单次随机、玩家确定性 50 分界、结果持久变量和忠/叛名单均有静态合同覆盖。
- 忠臣同时从独立处理、弱势王/帝头衔销毁和国号重组入口中排除；产品逻辑不对忠臣调用 `reset_title_name`。
- 正式 allowlist 恰为 32 个运行时文件；九语均为 UTF-8 BOM、每语 112 个产品 key，无七语英文占位；`descriptor.mod` 为 0.2.0 且不含 `remote_file_id`。
- 两次 staging 的 manifest 与 ZIP 逐字节可复现；640×640 thumbnail 小于 1 MB，并与已提交源图的确定性投影一致。

## 3. `open_kaishek` 离线预验

每次 CK3 启动前保存：`open_kaishek` exact commit、profile/version、CLI/JAR SHA-256、CK3 build 与 EXE SHA-256、产品/fixture corpus ID 与 SHA-256、实际命令、解析结果和不支持项。

预期边界：root parser 应为 GREEN；当前 validator 对 CK3 大量合法 opcode 仍可能返回 `UNKNOWN_OPCODE`，fixture 目录也可能不在 profile 中。此类结果记录为 tool limitation / not-applicable，不冒充产品 GREEN 或产品 RED，随后继续真实 CK3。

## 4. L1 源码树真实 CK3 矩阵

### 4.1 默认“人心离散”受控场景

外置夹具在 1066 年大宋真实统治者与真实封臣树中准备至少三名直属有地角色：

- 忠臣：尊王派，设置可解释的硬留事实；记录其角色 ID、主头衔对象、title key、显示/自定义名称、直属领主和至少一名下级封臣。
- 叛臣：尊王派，设置可解释的硬叛事实。
- 对照：非尊王派直属封臣。

通过原生 situation phase API 切入群雄割据，并由真实 `tgp_dynastic_cycle.0081` 调用产品覆写。必须在 paused snapshot / fixture marker / 日志中证明：

- 忠臣的 `rmtm_loyalty_outcome=stay` 与原因已保存；叛臣为 `defect`；每人只结算一次。
- 忠臣仍以旧天子为直属/最高领主，原下级封臣仍在其树下；其主头衔对象、title key、显示名称与夹具设置的自定义名称前后一致。
- 忠臣即使被压到原版弱势王国阈值以下，王国头衔也没有被销毁或换号。
- 叛臣和非尊王派对照脱离旧天子并继续原版割据重组；没有被忠臣领袖意外拉回。
- 旧天子只失去 `h_china`，保留个人领地、其他头衔与“后＋原朝号”空法理霸权；一期 50%/51%、决议可见性、宣称复辟及后朝销毁断言继续 GREEN。
- 一天后的“人心向背”总结事件可见，文案与实际忠/叛结果一致。

### 4.2 规则回归

- “誓死尊王”：受控硬叛候选人也必须留守，证明该规则是一期兼容模式。
- “原版群雄割据”：不创建后朝、不写二期忠诚结果，角色/头衔/封臣关系与锁定的原版兼容副本一致。
- 非 AI 候选人：以相同冻结输入验证公开的 50 分确定性分界；报告明确这不是多人交互选择界面。

### 4.3 自然分布与极端场景

在不人为设置忠叛条件的自然大宋候选人上记录候选人数、硬叛/硬留/概率池人数、每人分数与最终结果。15%–40% 的叛离率是平衡观察目标，不是硬编码门禁；若样本过小，只报告原始人数，不伪造统计显著性。

另执行两个受控极端：高好感/高合法性/低相对军力应显著偏向留守；低好感/低合法性/高相对军力应显著偏向叛离。硬叛必须始终优先于硬留。

### 4.4 MCP、画面与清理

- CK3 排他槽通过仓库借用机制获取；若被占用则等待，不抢占、不终止他人进程。
- 所有交互先取 MCP readiness 和 paused snapshot；UI 只用于 MCP 无法直接触达的真实产品入口。
- 宣传/工坊实机图在关闭验收专用窗口后拍摄。地图镜头必须由原生 MCP 定位到大宋首都 `b_kaifeng`（开封），并保存 camera settled 回读；不得出现意大利地名或验收字样。
- 结束时 CK3 进程树、隔离 userdir 和独占槽均清理；源码/runtime 字节、真实用户存档与保护存储不被改写。
- `error.log`、`gui_warnings.log`、`database_conflicts.log` 中任何产品解析/运行错误、重复 key 或未清理进程均为 RED。

## 5. 发布与 L3 fresh-cache

1. 在 exact `master` commit/tag 上生成正式 staging，冻结 manifest、ZIP、thumbnail、BBCode 与 Steam Change Notes 的字节和 SHA-256。
2. 只使用 staging 上传同一 Workshop item `3798404599`；`remote_file_id` 只写外层 launcher descriptor/sidecar。
3. 匿名读取公开 changelog 页面，找到本次条目并在 HTML 解码、换行归一后逐字复核 Change Notes 的字符数、行数与 SHA-256。仅 `EResult=1` 不算完成。
4. 删除旧订阅缓存并由 Steam 重新下载；对 strict-verified 数字 cache leaf 执行 32/32 精确核对，只允许内层 descriptor 多出正确 `remote_file_id`。
5. 对 fresh cache 重跑与 4.1 相同的 MCP-first 核心矩阵。公开页面复核标题、版本、可见性、Gameplay 标签、thumbnail、BBCode 和代表性真实游戏截图。
6. 上传后从 exact tag 重建 staging，恢复无 ID 的 canonical release tree；新增 `docs/release-changelogs/reclaim-the-motherland/0.2.0.md` 并提交、推送到 `master`。
7. 把 Steam 恢复到项目规定的离线状态，释放 CK3 槽和任务登记。

## 6. 最终报告字段

`docs/acceptance-report.md` 至少记录：源码/tag/Workshop 身份，全部 L0 命令与结果，`open_kaishek` provenance，L1/L3 artifact 绝对路径及 `report.json` SHA-256，MCP readiness 和 slot 等待，二期三角色前后快照与自然分布，32 文件 manifest/ZIP/thumbnail/fresh-cache 哈希，九语审核边界，Change Notes 冻结值与匿名精确回读，公开页面/截图复核，以及所有保留 RED attempt 与已知限制。
