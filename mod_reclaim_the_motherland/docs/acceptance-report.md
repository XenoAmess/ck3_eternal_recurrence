# 重整河山 0.1.1 验收报告

状态：**COMPLETE；L0 GREEN、源码树 L1 GREEN、Workshop fresh-cache L3 GREEN，公开发布后复核通过。**

验收日期：2026-09-09  
目标游戏：CK3 `1.19.0.6`  
产品：`mod_reclaim_the_motherland`

## 1. 结论

源码树已经通过独立构建、静态合同与真实 CK3 全链验收。MCP-first 实机 run 从 1066 年宋帝出发，实际切入群雄割据、触发原版 `tgp_dynastic_cycle.0081`，证明后宋的动态名称与空法理头衔、旧天子的个人领地、尊王派直属封臣及其下级 realm tree 均被保留；非尊王派直属封臣脱离。随后在精确 50%/51% 控制边界验证“宣称复辟”，并由真实决议 UI 证明“宣称复辟”可用而原“宣称天命”不可见。执行决议后完整原版天命效果生效，且复辟者持有的后朝霸权被额外销毁。

版本 `0.1.1` 已上传到独立 Workshop item `3798404599`，全新订阅缓存完成 28/28 严格核对，并从该缓存执行相同的 MCP-first 实机矩阵取得 19/19 GREEN。三张宣传截图来自这次 GREEN run；地图镜头由原生 MCP 精确定位到大宋首都开封，而非意大利或其他错误区域。Workshop 页面已经公开、登记《溥天之下 / All Under Heaven》为必需 DLC，并通过 Steam 匿名接口复核可见性。

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

## 6. Workshop fresh-cache L3

发布身份：

- Workshop item ID：`3798404599`
- 公开页面：`https://steamcommunity.com/sharedfiles/filedetails/?id=3798404599`
- 公开版本：`0.1.1`
- 上传包 ID-bearing manifest SHA-256：`f1d4f19816650267ad2ca181d9e18295c910623b88fe4b56ffd6bbc3cb5b6946`
- 上传包 deterministic ZIP SHA-256：`b7096953d96ff2c5542fa7b18fc9a9a02536750969f9f5ef57a08bc65b96e962`
- Workshop 缓存：`D:\Program Files (x86)\Steam\steamapps\workshop\content\1158310\3798404599`
- 缓存按 ID-bearing manifest 严格核对：28/28 GREEN。
- 上传成功日志：`C:\Users\1\AppData\Local\Paradox Interactive\launcher-v2\logs\launcher-2026-09-09.log`；2026-09-09 10:30:57 开始、10:31:05 成功。
- 上传后正式 staging 已重建；内层 `descriptor.mod` 不含 `remote_file_id`，item ID 只保留在外层 launcher descriptor 与发布记录中。

最终 GREEN run：

`D:\workspace\ck3_reclaim_the_motherland_design_process_assets\reclaim\runs\rqa_workshop_20260909_1952_capital_3798404599_v011`

- Wrapper `report.json` SHA-256：`6d5ad36cd296f61a83573b501a566c90ec918e9d811ab5b38eb41ade3513c6ab`。
- Cell `cell/report.json` SHA-256：`5859e13cdf06f8287cb2a28aa1f3d72669d4d33ff2cb50fb4ab691dee4938e30`。
- 结果：wrapper/cell 均为 `GREEN`；19/19 markers；项目 diagnostics 为 0；总时长 878.326 秒；CK3 槽位等待 0.165 秒。
- runtime product tree SHA-256：`9313dbd44116241f7bd4f22000068033778ad3c584a5933599915e5472dfe947`。
- source/runtime、受保护存储均未改写；CK3 进程树已受控回收；隔离 userdir 已清理。
- “保留个人领地”不是宽松的 top-liege 推断：fixture 对原直辖伯爵领逐个执行 `holder = root` 严格断言。产品分支只销毁 `h_china`、不执行 `force_step_down_landed_titles`，并把旧天子排除在弱势王/帝头衔裁剪之外。

大宋首都镜头证据：

- 原生 MCP `ck3_center_map_on_landed_title_v1` 以 `b_kaifeng` 为目标；title ID `13949`、capital province `9822`。
- 相机 target/current 均为 `[6836.0, 0.0, 2619.0, 174.0, 1.082104..., 0.0]`；`settled=true`、`postcondition_verified=true`、`target_write_blocked=false`。
- `cell/08_song_capital_navigation.json` SHA-256：`cc280aaadd48a2ab4fc3d8f193f3edcfe6e0afbb92042c1a832077e1e92acdde`。
- `cell/08_song_capital_map.png` SHA-256：`772defc92ca9846758a5e42da554d5b5ec021b1e290c747d9736491a4cdc150a`；视觉辅证命中开封周边“管城县”，并排除“教宗 / 教宗国 / 意大利 / 罗马 / 那波利 / 萨莱诺”以及测试字样。
- 保留的 RED attempt `rqa_workshop_20260909_1940_capital_3798404599_v011` 是 OCR 词表未接纳“管城县”的 harness RED；它没有被覆盖，也没有被用作商店素材。

Workshop 页面复核：

- 640×640 thumbnail：803,154 bytes，SHA-256 `564a558d5dc280e9049fb6907db36418a9a29085802da2ce8bed0f1dff6e1c38`。
- 三张 media strip 均来自上述 GREEN run，按“后宋立于开封 → 宣称复辟就绪 → 复辟诏告与效果”上传；文件和来源哈希见 `workshop/reclaim_the_motherland_screenshots.md`。
- Steam 匿名 `GetPublishedFileDetails` 在 2026-09-09 21:54（Asia/Shanghai）返回 `result=1`、`visibility=0`、标题 `Reclaim the Motherland — 重整河山`、consumer app `1158310`。
- 页面公开与三张缩略图证据：`reclaim/steam/public_page_final.png`，SHA-256 `f532f793a59fa9988823a97fa23c83f7258b6adbbcab6e4e9c81e27b3446405c`。
- 必需 DLC 已勾选 `Crusader Kings III: All Under Heaven`；证据 `reclaim/steam/required_dlc_saved.png`，SHA-256 `642bc89e737550eebb095c64dad2ad57cbace8326160d06891a780be899509c6`。

正式 tag、exact-tag 构建哈希和永久 initial-baseline changelog 在发布记录提交中回填；它们不改变上述已经上传并经 fresh-cache 验证的 28 个运行时文件。
