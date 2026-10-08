# 《礼与道》R0032：宗教头衔授予前加法诊断（RED）

**结论：候选无效，正式 I3b/C3/I4 仍未验收。** 在固定 R29 B3 已签署冷存档上，仅给 R31 D2a 的未授予 `new_title` 增加一条 `add_title_law = temporal_head_of_faith_succession_law`，其余诊断文件保持原样。CK3 1.20.0.4 实机中，玩家 31254 的原生完整继承人缓存在 D0、D1、D2a 均为 45 项；执行不变的 D2b 授予阶段后、保存前立即成为 40 项，保存后仍为 40 项。丢失的五个 ID 是 `38561, 39045, 39171, 39352, 39527`，没有新增项。这与 [R0031](../2026-10-09-r0031-06159b964-finer-d2-diagnostic-red/REPORT.md) 的断点一致，不能将该候选合入生产。

本次唯一新候选是外置诊断 overlay 的一行增量。静态校验通过，六个 overlay 文件中另外五个逐字节等同 R31，71 个 production 文件未修改。`live-attempt-032` 使用一次性分配的 `bf-202609141645-5434332d4d--li-yu-dao--R0032`，载入生产源 commit `06159b964d859d30f2f07f4b183284df7d6dac47`；屏幕任务在当时干净的 `9f410bc81740de82465adfd1ee6be7b31ea2040e` 工作树上取得。CK3 EXE SHA-256 为 `98702f88a547cde2eaf29a85f93b85f68ee4cf8148336a4f7afaeb75319dd518`，起始 B3 存档 SHA-256 为 `c8601e7ba08406a551dcddd2a19e454423db2be6b559fad9985c6d1121b537c9`。

| 阶段 | 原生缓存：保存前 / 保存后 | 独立保存状态 |
| --- | ---: | --- |
| D0 已签署起点 | 45 / 45 | 原始 R29 B3 固定输入；D0 自动保存被后续阶段覆盖，未单独复制，故不声称保有其保存体 |
| D1 教义投影 | 45 / 45 | T18373 尚不存在；七个政治头衔的完整 AST 成为本次对照 |
| D2a 创建未授予 T，含授予前加法 | 45 / 45 | T18373 holder 为空；七个政治头衔与 D1 完整 AST 相同 |
| D2b 执行原有授予原子组 | 40 / 40 | T18373 holder 为 31254；政治头衔 2230、2231、2235、2262、2264 的完整 AST 变化，2232、2263 不变 |

D2a 保存体中的 T18373 完整 Title AST 没有名称含 `law` 的顶层字段；D2b 也没有。当前尚无经过原生类型映射验证的头衔法序列化路径，因此这只说明**当前精确 AST 未显示顶层法律字段**，不能单凭此断言该 effect 没有执行或法律绝对不存在。无论法律内部状态为何，本次候选没有阻止五项缓存丢失。`R32-CACHE-COMPARISON.actual.json` 和 `R32-SAVED-TITLE-COMPARISON.actual.json` 在归档中保留所有逐项原生 ID、保存体完整 Title AST、SHA-256 与两阶段差异。

启动前新鲜 Steam 原图 SHA-256 为 `ce34d6881b451adec5d88c2aea6a9f5066d1e3fe8ecd734d580a91501c64c843`，我直接看见资料库底栏“离线模式”；客户端始终未切在线。首份原生 profile 只读冻结因 CK3 非前台而 RED，保留失败回执；用绑定 PID 27352/HWND 459884 的 UI Automation 聚焦后，新 profile 冻结成功。首个 MCP 接入仍因前台被抢占而返回 `isError=true`，该会话关闭；第二个新会话再次聚焦后接入成功，原生返回 `attached_snapshot_verified`。没有重放失败接入请求。完成 D2b 保存与回读后，经原生正常退出路径，原始 CK3 句柄回报 PID 27352 退出码 0，退出观察器报告 `process_exit_observed_zero`；其 `autosave_verified=false` 保持原样，不扩大为自动保存验收。最终新鲜 Steam 原图 SHA-256 `491d7a5241dd11d44e4112ec10e313da6e85e44466e342977a513d6586890e28` 再次由我直接读到“离线模式”。屏幕 CAS 在 keeper 正常停止后以序号 4050→4051 释放，CK3、录制及屏幕占用均清空。

[INDEX.json](INDEX.json) 列出 322 份逐字节核验的原始请求、SDK/原生回执、候选源码、profile、屏幕图片和操作收据；[raw-evidence.zip](raw-evidence.zip) SHA-256 为 `04148562b36f17e38d48488907f9bc32b6955c6f873d7e7391fdae47ae63fba4`，[归档校验](ARCHIVE-VALIDATION.actual.json) 已逐项解压核验。三个约 91.7 MB 的阶段 CK3 存档与原始 B3 存档继续保留在仓库外 `C:/workspace/ck3_lyd_runtime_20261004/live-attempt-032/`，INDEX 保存各自精确路径、字节数和 SHA-256；不以 ZIP 缺少保存体冒充完整可搬迁备份。所有失败 attempt、首份 profile、首次接入会话和旧 R31 证据均保留。

下一轮应只拆开 D2b 的 `create_title_and_vassal_change`、`change_title_holder` 与 `resolve`，在各原子动作后立即读缓存并独立保存，以找出 45→40 的第一个动作。该计划尚未实机执行。正式 I3b 新 T 冷重载、C3、I4、官方 CI 均仍为 **NOT_RUN/RED**，不能用本次诊断替代。
