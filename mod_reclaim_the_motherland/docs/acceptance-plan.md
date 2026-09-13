# 重整河山 0.4.0 验收方案

状态：**执行中。运行时实现、L0 与 `open_kaishek` parser 预验已完成；源码树 L1、正式发布与 fresh-cache L3 尚待最终证据。**

目标游戏：CK3 `1.19.0.6`

产品：`mod_reclaim_the_motherland`

Workshop item：`3798404599`

## 1. 本期验收目标

0.4.0 合并交付三期与四期，但四类结论必须分别成立：

1. 动态后朝具有明确单继承人顺位，随主继承人跨过一次真实死亡；同一后朝 title object、空法理、marker、留朝直属诸侯及其封臣树不裂解。其他个人头衔仍按角色原有继承规则处理。
2. 最近失去天命的后朝延续三省六部九席。仍在旧朝且合资格的 incumbent 保持同一人物、同一 council position 与同一 `e_minister_*` 头衔；实际离朝者才离任，只补真实空缺。正式中书门下权力分享、天命和 `h_china` 专属特权不得随之延续。
3. 后朝在【提议附庸】中不再冒领现任中华霸权的身份优惠；只有本轮实际释放的直属诸侯主头衔获得五年、精确引用该后朝 title object 的【新近自立】`-50`，双方换君不能绕过，期满自然消失。
4. 0.2.0 的【人心离散】、忠臣国号与封臣树、个人直辖领地保留、50%/51% 边界、【宣称天命】封锁和【宣称复辟】全链不得回归。

发布退出条件是 L0、源码树 L1、正式 staging、Workshop 上传、全新订阅缓存严格复核和 fresh-cache L3 全部 GREEN；任何自动报告都不替代实际公开页面与 Change Notes 回读。

## 2. L0：静态合同、原版身份与构建

### 2.1 exact upstream 与生成投影

- 从本机已安装 CK3 `1.19.0.6` 读取本期依赖的原版文件并校验锁定 SHA-256，不以仓库内忽略副本缺失作为跳过理由。
- `tools/gen_reclaim_vassalization_override.py` 必须从 exact upstream 的完整 `offer_vassalization_interaction` 生成发布投影；除后朝身份分支和【新近自立】项外，其余对象字节／结构保持一致。
- 对同名 interaction、`tgp_has_access_to_ministry_trigger`、单继承法、on_action 迁移、定时 title variable 和 release allowlist 建立静态合同。
- 至少 12 个表驱动接受度向量覆盖王国／公国／伯国、法理、合法性、好感和军力组合；每个向量同时保存原版与 0.4.0 差值来源。

### 2.2 内容与发布树

- `descriptor.mod` 为 `0.4.0`，不含 `remote_file_id`。
- 九种发布语言 key 集一致、UTF-8 BOM 正确，无七语英文占位；【溥天之下 / All Under Heaven】术语对应不得漂移。
- 正式 allowlist 恰为 35 个运行时文件；源码 README、验收 fixture、日志和其他 development-only 内容不得进入 staging。
- `tools/test_reclaim_the_motherland_contract.py`、`tools/validate_reclaim_the_motherland_static.py`、`tools/test_build_reclaim_the_motherland_release.py` 与 `tools/build_reclaim_the_motherland_release.py --check` 全部 GREEN。

## 3. `open_kaishek` 离线预验

任何 CK3 启动前，先运行产品树与外置 fixture 的 parser-only root scan，并冻结：

- `open_kaishek` exact commit、CLI contract、profile/version 与 JAR SHA-256；
- CK3 exact build、EXE 路径与 SHA-256；
- product/fixture corpus ID、文件数、bytes、root SHA-256、命令和 diagnostics；
- validator/IR 对动态头衔、继承、council position、interaction AI 接受度和定时变量不支持的部分必须明确记录 `not-applicable`，不得把 parser GREEN 冒充玩法 GREEN。

## 4. L1：源码树 MCP-first 实机

### 4.1 槽位与受保护运行

- 启动前在任务总线 `poll --ack`；若 CK3、主屏幕或 Steam 在线会话被其他任务占用，只按 10 分钟间隔轮询，不启动 CK3。
- 使用排他 launch lock、隔离 `-userdir`、固定源码树 runtime copy、外置 fixture 和仓库既有 bridge DLL/injector。
- 原生 MCP snapshot/command 是状态与动作的首选证据；OCR 只用于玩家可见窗口、按钮和地图画面，不用来猜内部 title/council/variable 状态。
- 每次 attempt 使用新的 append-only run 目录；RED 不覆盖、不删除。退出时回收 CK3 进程树、释放槽位并证明真实 source/runtime 与保护存储未改写。

### 4.2 单次严格链

同一条真实 CK3 链必须按顺序出现 31 个严格 marker，并完成：

1. 确认 1066 大宋天子、`h_china`、王朝循环和九席原班大臣 exact identity。
2. 进入群雄割据，确认旧天子只失去 `h_china`，仍亲自持有受控伯爵领并取得唯一空法理后朝霸权。
3. 证明必留忠臣仍直属旧天子、一次性留朝原因正确、主头衔／显示名称不变、间接封臣树完整；必叛尊王诸侯和普通对照诸侯独立。
4. 证明后朝具有 `single_heir_succession_law` 与 `current_heir`；九席仍为群雄割据前的 exact incumbents，唯一官署 entitlement 指向该后朝。
5. 证明只有两名本轮实际释放者的主头衔绑定确切后朝；通过实际 `offer_vassalization_interaction` 引擎路径向二人提议并确认二人即时拒绝、保持独立。
6. 切换为后朝主继承人并让旧君真实死亡；确认同一后朝、忠臣主头衔与封臣树、受控个人伯爵领、唯一官署 entitlement 和九名原班大臣全部由新君体系承接。
7. fixture 只把正式 1825 日 script value 覆写为 1 日；原生 MCP 以速度 1 推进并证明两项 title-bound 变量自然到期，随后重新暂停。
8. 继续回归 50% 不足、51% 达标、【宣称天命】不可用、【宣称复辟】可用、原版天命效果完成及后朝销毁。

### 4.3 四期平衡证据边界

- L0 的 12 个向量负责精确证明被删除的身份优惠和未改变的原版项目；L1 的两个真实目标负责证明 engine 实际拒绝，而非只验证自造脚本条件。
- 本版本不把 fixture 的两个受控目标冒充“三个自然局首年宏观统计”。若另行执行自然样本，人数、中华法理领土百分点、兵力与复辟状态须独立列入报告；缺少这类样本时，公开结论只能是“修复即时批量归附的已定位公式与受控复现”，不能宣称所有随机地图首年都不超过某一百分比。
- 五年机制是软性 `-50`，不是硬禁。静态极端向量必须保留堆叠好感、法理、军力和外交经营后仍可接受的路线。

## 5. 正式构建、发布与 L3

1. 源码树 L1 GREEN 后更新 README、Workshop BBCode、0.4.0 Change Notes 与验收报告；真实游戏截图必须来自 GREEN CK3 run，生成图不得冒充实机。
2. 同步最新 `origin/master` 时只允许 `fetch` + `rebase`；复测后把实现普通 fast-forward push 到 `master`，禁止 merge、force-push。
3. 从 exact `master` 建立 `reclaim-motherland-v0.4.0` tag，再从 tag 生成 deterministic staging/ZIP；canonical 内层 descriptor 保持无 `remote_file_id`。
4. 上传同一 Workshop item `3798404599`，整段替换入库 BBCode，并使用入库 `workshop/reclaim_the_motherland_change_notes_0.4.0.txt` 作为 Change Notes。
5. 通过匿名公开 API/页面逐项回读 item ID、标题、可见性、描述正文和最新 Change Notes；成功上传回执本身不算完成。
6. 把旧订阅缓存移动到可恢复发布证据目录，重新下载全新缓存并按正式 manifest 逐文件严格核对；不得把本地 staging 当 fresh cache。
7. 从全新缓存重跑同一关键 31-marker MCP-first L3；关闭 CK3，把 Steam 恢复 Offline Mode，并再次证明资源释放。
8. 实际上传成功后才写 `docs/release-changelogs/reclaim-motherland/0.4.0.md` 的最终发布事实，提交、推送 tag/changelog，并等待 exact master SHA 官方 CI 终态。

## 6. 验收报告必填字段

`acceptance-report.md` 至少记录：

- source/master/tag/Workshop 四重身份、当前与上一公开版本；
- 全部 L0 命令、结果、用例数、35 文件 manifest/ZIP/thumbnail SHA-256；
- `open_kaishek` 与 CK3 exact provenance、适用与不支持边界；
- 每个保留 RED attempt 的路径、报告哈希、失败标记、根因与修复；
- 最终 source L1 与 fresh-cache L3 的绝对路径、execution ID、wrapper/cell report SHA-256、时长、slot wait、MCP readiness、31 marker 与 diagnostics；
- 后朝 title object／law／heir、忠臣封臣树、个人伯爵领、官署 entitlement、九席 exact incumbents、两个真实拒绝、定时到期、50%/51% 与复辟断言；
- 九语审核边界、四个 override key、旧割据存档无法追溯补标的限制；
- 上传回执、公开 item/Change Notes 精确回读、全新缓存严格核对、Steam Offline Mode 与最终任务总线释放证据。

## 7. 当前执行记录

- 已完成：运行时与 fixture 实现；18 项静态合同、九语/35 文件静态校验、10 项构建测试与 deterministic 双构建 GREEN；产品/fixture `open_kaishek` parser root scan GREEN。
- 已保留：`R0008-source` 为 RED。MCP readiness 与四期 title binding 已通过；失败暴露 title law 在无持有者时过早添加、销毁 `h_china` 后才补官导致原版 liege 无 holder，以及 ministry trigger 嵌套 scope 错误。三项根因均已作窄修复，RED 目录没有覆盖。
- 已保留：`R0009-source` 为 RED。继承法／继承人、个人伯爵领、四期 title binding 与两次真实附庸拒绝均已通过；九席和忠臣主头衔／封臣树失败。日志证明九个 landless ministry title 被误当普通弱势帝国头衔释放、裁剪，随后原版官职继承把同一宰相连续塞入多个席位；批量补缺又把忠臣诸侯选为大臣并按原版规则上收其封臣树。当前窄修复显式保护未叛现任、只清退明确叛离者并把真实空缺交回正常任免。
- 待完成：修复后的源码树 L1、新真实截图（若可清晰表现三/四期）、正式构建、Workshop 上传、公开回读、全新缓存 L3、changelog/tag/master push 与官方 CI。
