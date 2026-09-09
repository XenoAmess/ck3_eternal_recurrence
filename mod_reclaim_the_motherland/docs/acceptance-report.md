# 重整河山 0.1.0 验收报告

状态：**L0 GREEN；源码树 L1 GREEN；Workshop fresh-cache L3 待首次上传后执行。**

验收日期：2026-09-09  
目标游戏：CK3 `1.19.0.6`  
产品：`mod_reclaim_the_motherland`

## 1. 结论

源码树已经通过独立构建、静态合同与真实 CK3 全链验收。MCP-first 实机 run 从 1066 年宋帝出发，实际切入群雄割据、触发原版 `tgp_dynastic_cycle.0081`，证明后宋的动态名称与空法理头衔、旧天子的个人领地、尊王派直属封臣及其下级 realm tree 均被保留；非尊王派直属封臣脱离。随后在精确 50%/51% 控制边界验证“宣称复辟”，并由真实决议 UI 证明“宣称复辟”可用而原“宣称天命”不可见。执行决议后完整原版天命效果生效，且复辟者持有的后朝霸权被额外销毁。

首次 Workshop 上传、fresh subscribed cache 严格核对及同矩阵 L3 尚未发生，因此本报告此时不把发布状态写成 complete。上传后的 item ID、tag、正式 manifest/ZIP 和 L3 证据将在同一文件追加，不覆盖本节历史结论。

## 2. L0：静态、合同与可复现构建

执行结果：

- `py tools/test_reclaim_the_motherland_contract.py`：12/12 GREEN。
- `py tools/validate_reclaim_the_motherland_static.py`：GREEN；28 个 release 运行时文件、9 种语言、每种 102 个 key、8 个玩法脚本。
- `py tools/test_build_reclaim_the_motherland_release.py`：10/10 GREEN。
- `py tools/build_reclaim_the_motherland_release.py --check`：双构建可复现。开发快照 manifest SHA-256 为 `41ac174812e65725846bceeea084fcccf70b938aed3cbd3aeb4e4ab6e42388d8`，ZIP SHA-256 为 `cdbd601c44d578c39c2ba8a34c2fe372292f90b812ffb5af5acf8a2425282de1`。正式 tag 构建会因 manifest 内嵌 Git identity 而取得新的正式哈希。
- 640×640 `thumbnail.png` 为源图的确定性投影，803,154 bytes，SHA-256 `564a558d5dc280e9049fb6907db36418a9a29085802da2ce8bed0f1dff6e1c38`。

九语发布审阅记录见 `docs/reclaim-release-localization-review-2026-09-09.md`。七种新增语言以 MiniMax-M3 最小 key-value 候选为起点，并由当前执行者逐条修正语义、术语、格式和保护 token；这不冒充母语译者认证。

## 3. open_kaishek 离线预验边界

- open_kaishek commit：`33d690234d8217422978ee642055ab1b13e44c76`
- CLI JAR SHA-256：`cc42a0bbd4991095deb4c8af4142a4657d46d07d616b89643a9f2d7a1e4a3cd7`
- profile：`ck3-1.19.0.6`
- CK3 EXE SHA-256：`2d00ff3101ef70b566f2fcbae292f09263199c80e9dc8f139b82d7d96f83db86`
- 产品 root scan：parser GREEN，8 文件、41,347 bytes，root SHA-256 `92b0c6c4eb6f6fe6cf62006b9630e070339dd4a3dbdf6f0f7c5141d63f9982a0`。
- 外置验收夹具 root scan：parser GREEN，8 文件、17,820 bytes，root SHA-256 `dc36c2fd401dff03f959edf5b1fd3aca33c230d226556f64db58930e0a5197f5`。
- 命名 fixture 尚不被当前 CLI 识别；validator/IR/finite-runtime 也没有覆盖本 mod 动态头衔、封臣转移和决议语义的 profile。因此这些项诚实记录为 `not-applicable / cli-red`，没有被当成产品 RED，也没有替代 CK3 实机。

## 4. L1：源码树 MCP-first 实机

GREEN run：

`D:\workspace\ck3_reclaim_the_motherland_design_process_assets\reclaim\runs\rqa_20260909_114834_32f85232`

主要身份与完整性：

- 有效 cell 报告：`cell/report.json`，SHA-256 `9594029df6b161329e820bd98dfbc2d54fc6964d0252c44538b423f1f1dbeda6`。
- run wrapper：`report.json`，SHA-256 `5ae712be7131f80729fe0a5a487e63d776332f33840eb1f6e04e3875c893d3c3`。
- CK3 `1.19.0.6`；EXE SHA-256 `2d00ff3101ef70b566f2fcbae292f09263199c80e9dc8f139b82d7d96f83db86`。
- 原生 bridge DLL SHA-256 `a71f38dfc26c8aa8e9f442f549e38973cb71049329710d1bae1e7aca87c26e03`；injector SHA-256 `41230bf1a081a034897fd18fac33acdf74a0107cedc3d67f5cc6eb53c846577e`。
- 运行时 product tree SHA-256 `ae439d58f417d96480d89ca9d85c464ea8aa48c76eda0f08edb8c5ced4e82a67`；fixture tree SHA-256 `6e470d8e1595aae26005cfb8506cd9a6a3e9bbd1274e92598469ed25d7453fea`。
- 总时长 723.141 秒；CK3 排他槽等待 0.131 秒。
- MCP readiness GREEN；关键事件均以 MCP 暂停快照与语义化 event-option selection 操作，不依赖坐标点击猜测。
- 19/19 fixture markers 通过；项目相关 diagnostics 为 0。
- source/runtime 在运行中均未改写；保护存储未变化；原生进程树回收已证明；隔离 userdir 已删除。

19 个标记覆盖：精确宋帝、真实封臣树、规则启用、真实阶段切换、原运动身份冻结、原版群雄事件分派、后朝空法理与个人领地保留、尊王派直属与下级树保留、非尊王派直属脱离、50% 不足、51% 达标、复辟决议就绪、完整原版效果与后朝销毁。

关键屏幕与机器可读证据：

- `cell/08_later_dynasty_name.png`：SHA-256 `1e23206436ed1c6ef23eab7c39e99a0cb7c0d54461822aa0f9f479506bb879e6`；配套 JSON SHA-256 `50e6118052fdeafd510fa2f1a6b5de765b7d0c8f8269d428ffdb7fa4dfd6b956`，断言实际渲染为“后宋”。
- `cell/09_decision_visibility.png`：SHA-256 `09f43902c795417569314321de14d58904fd15c2ee3f5b09f9e7ebcbabbf141c`；配套 JSON SHA-256 `9fe5d9a3ef902c02a0f6852fb1d215bffdec99b067ec149c20a23d059dc39ee5`，断言复辟可见、天命不可见。
- `cell/11_acceptance_complete.png`：SHA-256 `f845d347a1fcdac4739ec0708ad085710811c1819afba02b2dde9386df542120`，证明决议后的中华霸权复归与后朝销毁。

## 5. 保留的 RED 证据与修正

失败 attempt 均保留在相同 `runs` 根目录，没有覆盖成 GREEN。代表性问题包括：动态头衔曾只显示前缀或夹具按旧乱码字面量判断；修正为 89 个原版标准朝号的确定性组合 key，并让夹具断言 Unicode“后宋”。另一次 `non_pro_hegemon_direct_released` RED 来自夹具随机抽到男爵，而产品设计本就让结构性男爵跟随伯爵领主；夹具现只选择伯爵及以上的真实直属参与者。上述修正后获得本报告的 19/19 GREEN。

## 6. Workshop L3（待执行）

首次上传后必须补齐：

- item ID、公开 URL、tag 与正式 commit；
- 正式 28 文件 manifest/ZIP SHA-256；
- 全新订阅缓存路径、ID-bearing sidecar manifest 与 28/28 严格核对；
- 对该 fresh cache 执行相同 MCP-first 矩阵所得 L3 run、报告哈希和 19/19 结果；
- 640×640 preview、三张真实游戏截图的顺序与公开页面复核；
- 上传后重建无 `remote_file_id` 的正式 staging。

完成这些项目并把 initial-baseline changelog 提交、推送后，方可将本报告状态更新为 complete。
