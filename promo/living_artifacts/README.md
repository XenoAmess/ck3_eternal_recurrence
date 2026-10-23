# 活武器：饥渴的传世之物 · 宣传片项目

**完整投稿标题：传世之物，饥渴长存｜CK3模组推荐《活武器：饥渴的传世之物》**

封面主标题为「传世之物，饥渴长存」，副标题保留正式模组名「活武器：饥渴的传世之物」。

当前交付：**完整导演稿 v1 与 promo 项目**，建议约 3 分 30 秒、八幕，气质为阴暗、冷峻、克制。以一件自然觉醒的宝物串起培养、收益、代价和玩家取舍；尚未拍摄、配音或输出成片。

- [导演稿与逐幕旁白](director.md)：LA-01–08 分镜、画面、声音、事实限制和同场截图表。
- [机器可读导演数据](director.json)：本项目专用导演稿数据，与章节和旁白对应。
- [promo 项目配置](promo-project.json)：既有工具链 v1 配置，章节 `planned`，素材引用为空。
- [工坊介绍 BBCode](../../workshop/living_artifacts_description.bbcode)：已重写并公开核对；新图将在视频拍摄过程中取得后上传并嵌入。
- [正式模组与规则](../../mod_living_artifacts/README.md)；[宣传整改记录](../../mod_living_artifacts/docs/workshop-promotion-remediation-2026-10-23.md)。

## 本轮实际工具使用

`machine_id: pc-20260924rtuf-f11af23c08`；2026-10-23。使用正式发布的 `xar-promo 0.3.0`，官方 wheel SHA-256 为 `f59c4b62b89297e2ff7bb7df4354fc88c6447fa6b1b7eade28de2bc1e6dc974c`。包安装在独立外置 target，仅该 CLI 进程显式设置 `PYTHONPATH`；未修改冻结游戏 runtime 的 venv 与依赖。

工具 `init` 于 `2026-10-23T15:28:41Z` 实际退出 0，创建本目录与 `preproduction-0001` run。原结构化 argv／进程环境／退出见 [初始化回执](D:/workspace/ck3-living-artifacts-20261022/environment/living-promo-project-init-a01.json)；[独立 CLI 资格](D:/workspace/ck3-living-artifacts-20261022/environment/living-promo-cli-v030-a01/qualification.json)记录真实工具来源。初始化与早期导演 run 保留原有配置；选定标题和冷峻稿固定在新的 run，不改旧快照。

当前导演 run 为 [director-v1-selected-title-20261024-a02](runs/director-v1-selected-title-20261024-a02/run-manifest.json)。`start-run`、当前配置 `validate --profile authoring --json`、该 run 的同项验证均实际退出 0；两次验证均为 `GREEN`、八章、零媒体 artifact，并实际核对引用文件字节与 SHA。标题及八幕旁白在 Markdown、导演 JSON 与项目配置间一致。[作者阶段验证记录](evidence/director-v1-authoring.json)保留命令、进程结果与稿件来源。

`generic/default` 是当前 authoring 占位配置，不代表实际剪辑 composer 或媒体 producer 已接入。后续 `plan/build` 必须绑定实际可用的 adapter、preset 与 composer；本次只调用项目初始化、run 固定与验证，不把这些命令当成成片。

## 一次拍摄，两类交付

按照导演稿 P01–P05 拍摄视频，关键 UI 顺手保留稳定段及原始静帧。W01 宝物详情、W02 喂养确认和结果、W03 管理取舍来自同一正式拍摄；不再为补图独立开场。旧验收夹具与两张已撤下的 R8 图片不进入本片或新图库。

当前没有登记可用原片、截图或音频。未来取得实际素材后再注册工具链 artifact，并记录原片时间码及身份；不把计划中的 P01 或 W01 填成已存在的 artifact。

正式拍摄与渲染须重新计算含原片和缓存的容量，沿 [统一存储策略](../../docs/storage-retention-policy.md)执行。创意稿不依赖某台机器的盘符；本页绝对路径仅为上述机器当时执行证据。

## 拍摄准备状态

`machine_id: pc-20260924rtuf-f11af23c08`，2026-10-23 UTC 的两次早期普通取材尝试均未进入地图、没有合格宣传素材：`PROMO0001` 在地图就绪前超时，原 host 退出 1；`PROMO0002` 的前端规则／任意选角调用因当前冻结 DLL 缺少 capability 被拒绝，原 host 保留退出 1。后者经真实主菜单 Exit to Desktop，CK3 原生进程退出 0、tree gone；两场均无游戏存档。证据为外置 [PROMO0001](D:/workspace/ck3-living-artifacts-20261022/live/pc-20260924rtuf-f11af23c08--living-artifacts--PROMO0001/host-report.json) 与 [PROMO0002](D:/workspace/ck3-living-artifacts-20261022/live/pc-20260924rtuf-f11af23c08--living-artifacts--PROMO0002/host-report.json)。keeper 原退出 0，CAS969 已释放屏幕；不把这些准备尝试计作正式视频拍摄。

同机早期配置中的 `NEVER`／`NO_AUTOSAVE` 未取得关闭自动保存的游戏读回，实际曾恢复默认；当前只保留诊断，不能据配置文件值准许下一次拍摄推进。此问题与原生 capability 缺口须在正式录像前解决或采用实际可用的合法入口，不能热改已冻结 runtime，也不能重放结果未知的动作。

2026-10-23 UTC 后续准备：普通拍摄使用公共入口的 `living-artifacts / ordinary-promotion`，startup 为 `ordinary_gui_campaign`。只复制逐文件绑定的正式 product 与四份普通配置；不创建 load carrier、fixture policy 或初始业务步骤。玩家通过正常 GUI 选角和开局，当前原生玩家、暂停地图及同一 allocation 身份闭合后进入固定 hold，结束仍走公共正常退出流程。该 case 的范围是正式游玩取材，不授产品业务验收或成片通过。

首场使用既有 v2 recorder，1920×1080、30fps、无原声，最多四段，每段最多60秒，合计240秒、全部原片及录制元数据合计512MiB。Root 审看实际游戏帧并核录制终态后才能登记取材结果；编码成功仍不授最终视频验收。`machine_id: pc-20260924rtuf-f11af23c08` 的 [正式拍摄 run](C:/codex-ck3-demos/living-artifacts-promo-20261024/promo-runs/formal-capture-a01/run-manifest.json)已创建，当前尚未登记媒体；原片与工具放在同一机器的独立 C 盘范围内。
