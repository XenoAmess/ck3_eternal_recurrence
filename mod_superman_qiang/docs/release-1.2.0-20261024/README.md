# 超人强 1.2.0 发布报告

状态：**COMPLETE**。Steam 与 GitHub 已实际公开，真实 Steam 下载与正式 35 文件精确一致；R37 通过实际主菜单加载的公共缓存限定边界及正常退出。R36 preGame 失败原件保留。永久记录已随 commit `6acd117ad9865807e3108e24a210dc1cf0fe1d88` 推送 master 并实际回读远端引用，release_delivery_complete=true。该状态不扩大业务验证范围。

machine_id：desktop-3fevhd2-1c74096080。整理时间：2026-10-24T03:15:34.192203+00:00。业务实机绑定 CK3 1.20.0.4 / build25734779，EXE SHA-256 98702f88a547cde2eaf29a85f93b85f68ee4cf8148336a4f7afaeb75319dd518；这些安装与实机事实只适用于该机器。

产品：超人强：越超人越强；Workshop item 3812991990；app 1158310。正式 tag superman-qiang-v1.2.0 → bcb9e9f11658519c5277e0d304a02e5028bbd760，上一公开 tag superman-qiang-v1.1.0 → f7fde816e295a62807ab636ee2d93cf307ea69cf。永久玩家说明见 [1.2.0 changelog](../../../docs/release-changelogs/superman-qiang/1.2.0.md)。

## 正式构建与已发生的发布

| 项目 | 实际结果与证据 |
| --- | --- |
| 正式包 | 35 个运行文件，共 1010859 B；[manifest](evidence/formal/manifest.json) 6404 B，SHA-256 9db0f28a9f08215ecd7747f7406acc8b379c54d87dc8964551829dccb0dad7ba |
| 正式 ZIP | 826470 B，SHA-256 d6a566f1f3f785336f33247423772d7c2a45e0fef8ea93becea8364b77818f86；归档只留摘要，避免重复大附件 |
| Steam 更新 | [原生回执](evidence/steam/native-update-receipt.json) steam_result=1，2026-10-24T02:48:35.240588+00:00；content_and_metadata；调用一次 |
| 公开 Change Notes | [匿名核对](evidence/public/verification.json)：entry 1792810119，全文 930 字符 / 28 行，SHA-256 939510478a9d23ea35a0d99721360b87fe20c3c8e6e07302ddabdc59083a68cd；[原始 HTML](evidence/public/changelog.raw.html)、[公开全文](evidence/public/change-notes.actual.txt)保留 |
| 标题与描述 | 同次匿名读取精确一致；[公开 API](evidence/public/item-api.raw.json)与[实际描述](evidence/public/description.actual.bbcode)保留 |
| Compatible Version | [侧栏核对](evidence/public/compatible-version-verification.json) HTTP 200，rightDetailsBlock 唯一 1.20 'Crozier' 与 requiredtags[] 精确一致；[原始 HTML](evidence/public/item-sidebar.raw.html)保留。实际 tags 顺序 Gameplay、Balance、Events、1.20 'Crozier' |
| GitHub | [公开 Release](https://github.com/XenoAmess/ck3_eternal_recurrence/releases/tag/superman-qiang-v1.2.0)；[实际回执](evidence/github/release.json)记录先查询不存在、仅一次创建、远端正文回读、两个附件重新下载及 SHA 精确一致 |
| 下载缓存 | [真实 SDK 下载](evidence/cache/native-download.json)成功；[35 文件比对](evidence/cache/exact-formal.json) EXACT_FORMAL_CACHE。实际目录 C:/SteamLibrary/steamapps/workshop/content/1158310/3812991990；没有把源码或 staging 复制进下载目录 |
| 上传后部署 | [外层 descriptor](evidence/deployment/outer-descriptor.json) 保留 canonical item ID，内层正式 descriptor 无 remote_file_id；上传后重建与正式包一致 |
| Steam 恢复离线 | [背景实际读回](evidence/steam/offline-restored-state.json)及[当次画面审阅](evidence/steam/root-offline-review.json)；只证明相应时刻，后续启动另取新鲜证据 |

## 已验证范围与已知缺口

[月度与冷加载原记录](../2026-10-24-monthly-and-cold-native-acceptance.md)记录 R30/R31：12 个完整角色 ID 65831..65842；最终 8 名合格角色 XP=2、3 名存活拒绝角色 XP=0、死亡角色 XP 变量缺失；双方月份与双向配偶去重列表按原始存档读取。配偶双方在显式补充事件前已 XP=2；其他合格对的最终总值已核，不把最终总值等同于每个脉冲各自归因。R31 为实际新 PID，零天冷读，未初始化、重置或重播性交，字段精确保持。

[通知原诊断](../2026-10-24-notification-diagnostic.md)保留 N0/N5 的有限样本：R33 N0 与 R35 N5 各一次可见死亡通知；R35 同日五个独立 pair 记录及 XP 增量已核。它们不构成同一存档反事实、完整 N=0/1/2/5 原版勾引矩阵，也不能定位或证明修复“勾引后后续通知累加”。该问题仍未解决。

C2 补足的 medical/pilgrimage/narrative 等分支有来源审计与离线回归，未逐分支实际引擎验收。纯工坊版不能精确观测原生引擎每次失败受孕掷骰；日常夫妻计数采用月度脚本模拟，无原生运行依赖，也不重掷真实怀孕概率。同性关系设置未独立引擎验收。其他 patch、DLC 组合、多人、铁人及成就不因本次样本获得通过。

[发布范围原审阅](evidence/source/scoped-review.original.json)与[原始门禁汇总](evidence/source/release-gates.original.json)逐字节保留。它们创建于发布之前，旧字段 published=false、tag 尚不存在等是当时事实；不可将这些旧字段改写成发布后的结果，也不可把局部接受范围改称 whole-product PASS。

## 格式、静态与类型检查

[九语言格式认证](evidence/format/certification.json)记录实际 generator --check、validate_static.py、build_release.py --check 全部退出 0：33 个生成输出，加 descriptor 与 thumbnail 共 35 正式运行文件。键、BOM、精确语言 header、占位符与引擎标记通过；保留既有九语言翻译，没有调用翻译 API，没有外语实机或语义认证。

[产品回归](evidence/ci/product-summary.original.json)五组实际退出 0，87 次测试执行，并完成两文件 [mypy](evidence/ci/product-mypy.original.json)。[共享历史汇总](evidence/ci/shared-final.verified.json)属于 f8032008c64e467701e6a26b0239a13c163c2fec 源码阶段：105 条实际命令通过、1058 次 unittest 执行、17 条 mypy 命令。它没有在后续公共修复 HEAD 全量复跑；不称作“117 个测试”，也不称整个旧仓库严格类型清零。类型边界记录保留了既有诊断，loader/core 的严格检查与所修改范围分别有实际结果。[发布 helper 回归](evidence/ci/publication-helper.json)与[原始 stderr](evidence/ci/publication-helper/unittest-all-existing-builder-publication.stderr.log)实际为 16 项 unittest（原 13 项加新增 3 项）、所修改文件 strict/普通 mypy 及 diff 检查退出 0；未改变 mod 业务运行字节。

公共 menu factory 与失败闭场修复为 commit 91295b2152ecdb469aaab349029f0e72e5d002d8；[该阶段交接](evidence/shared-repair/HANDOFF.actual.json)记录新增阶段 35 项相关测试（closure 19、support 10、menu 6），不能与旧 105 条命令混为新 HEAD 全量重跑。[修改范围类型结果](evidence/shared-repair/FINAL-TYPE-SCOPE.actual.json)：background/support 严格检查及 builder 普通检查通过；allocate 历史普通诊断仍为 18→18，按函数归属诊断集合一致，新增 menu helper 错误为 0，并未声称整个 allocate 模块通过。真实 frozen SDK factory 的[静态构造检查](evidence/shared-repair/REAL-FACTORY-STATIC.actual.json)只证明构造和工具登记；实际加载由后续 R37 另证。

## 实际缓存加载与正常闭场

R36 [原生报告](evidence/history/R0036-preGame-native-report.json)仍为 preGame factory 异常 RED。[首次](evidence/history/R0036-release-rejected-a01.json)与第二次 CAS 释放拒绝保持原样；[第三次实际释放](evidence/history/R0036-release-success-a03.json)在 sequence 8569 成功，任务 done、resources=[]。[失败闭场合同](evidence/shared-repair/R0036-FAILURE-CLOSURE.actual.json)保留该失败，不把后继成功回写到 R36。

R37 [公共 verify](evidence/cache/R0037/public-verify.json)实际退出 0，case_acceptance_pass=true、qualified_boundary_pass=true。其加载证据边界为 COMBINED_MANAGED_CACHE_PROFILE_AND_ACTUAL_MAIN_MENU_LOAD：正式 35 文件与真实下载缓存精确一致，[隔离 profile](evidence/cache/R0037/profile-preparation.json)及[启动输入](evidence/cache/R0037/startup-evidence.json)仅指向该缓存，实际 PID 16564 / EXE SHA 98702f88…dd518 的原生 route 为 main_menu。没有 campaign、业务 fixture 或业务动作；缓存验收没有重复功能测试。独立引擎 VFS 路径读回仍为 UNKNOWN，actual_cache_mount_proven_by_independent_vfs=false，不将组合加载证据冒称独立 VFS 查询结果。原始 result_boundary 名称含历史 PENDING_ORIGINAL_NORMAL0 字样；最终 normal_close 对象及 case_acceptance_pass 已实际完成，不改写该原始字段。

Root 从实际主菜单“退出到桌面”按钮只退出一次；短暂 Not Responding 后，[原进程保留句柄](evidence/cache/R0037/retained-os-exit.json)及[正常退出结果](evidence/cache/R0037/normal-close.json)证明 OS0/native0、Job before/final 均 0、cleanup_ok=true、managed_thread_finished=true、normal_close_qualified=true。没有重试、强制结束或伪造关闭。业务 PASS 不由正常退出授予。

闭场后 [Root 直接画面审阅](evidence/cache/R0037/root-closed-review.json)绑定新鲜 20 px 窗口移动与 11:29 时钟的 Steam 离线画面，[原生离线读回](evidence/cache/R0037/steam-offline-closed.json)也为 offline=true。[keeper](evidence/cache/R0037/keeper-parent-exit.json)实际退出 0；[CAS 释放](evidence/cache/R0037/screen-release.json)在 sequence 8575 成功，done、resources=[]。大图仅在 C 依通用存储策略复核，不重复入小型归档。

缓存限定验收、正常闭场及仓库交付已经完成。[实际仓库交付回执](evidence/repository/delivery.json)记录 master commit `6acd117ad9865807e3108e24a210dc1cf0fe1d88`、成功推送及新的远端引用核对；[归档逐字节检查](evidence/repository/staged-validation.json)保留原始证据与暂存区一致性。两份公开原始 HTML 保留原有空白与 SHA，格式检查仅排除这两份原始 HTML，其他新增文档与证据格式检查退出 0。

## 归档与复核

[实际缓存结果投影](cache-observed.actual.json)保留原始大 native report 与选中 common runtime 的完整 SHA-256 pin；该投影有明确来源，不冒称原始回执。新增阶段[闭场容量检查](evidence/storage/closing-admission.json)为实际预算检查，不另建额度。

[evidence-index.json](evidence-index.json)为每份字节不改的小型证据保留完整 SHA-256、字节数、原始路径及预定仓库相对路径；[release.actual.json](release.actual.json)连接当前发布事实。C 原件路径是历史来源，后续回收不应让仓库内相对副本失效。此归档不包含 SAVE、melt、游戏大日志、重复 ZIP、SDK 或 native 依赖。

本报告的 C 草稿在既有有限发布预算内制作；随后已逐字节归档到当前仓库并提交推送 master。归档及最终交付没有改变正式 mod 运行文件、Steam、游戏或屏幕状态，也未清理资产或另建额度。[仓库闭场容量检查](evidence/storage/repository-closing.json)保存目标机器实际容量与必要 stage 的有限保护。C 临时原件于 2026-11-23 按通用存储策略复核；正式发布记录和仍被引用的必要证据按用途保护，不能无限期延长全部过程素材。

最终缓存结果整理时间：2026-10-24T03:34:01.639135+00:00；machine_id：desktop-3fevhd2-1c74096080。
仓库交付最终核对时间：2026-10-24T03:45:02.122779+00:00；machine_id：desktop-3fevhd2-1c74096080。
