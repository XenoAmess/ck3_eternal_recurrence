# R185 拍摄结果：十二日已完成，80秒最低录制未完成

`machine_id: desktop-3fevhd2-1c74096080`；run `desktop-3fevhd2-1c74096080--vanilla--R0185`，2026-10-16 UTC。runtime/native源 `c743520929d4f9a82c17c908b218075018598e2d`、a28构建，CK3 `1.20.0.4`／build25734779。本场从R184正常保存date53148144接续，完成 **12个自然日到53148432**。

原片正常封装为 **46.466秒／1394帧**，完整AV解码exit0、无诊断；完成正常保存、游戏exit0和屏幕释放。完成12日后，为达到80秒最低录像时长而继续hold时，新容量检查失败并正常finish，因此**未达到80秒最低要求，也没有录满120秒计划上限**。现有文件不是截断partial，但仍没有连续clean、业务正例或人工签核；合格动态 **0/11**，研究 **6/14（42.9%）**、业务 **4/11（36.4%）** 不变。

共享来源与智能体消费边界见 [R185专题](../../../docs/ck3-native-ai/episode04-r185-window-capture-12004.md)、[52份原件索引](../../../docs/ck3-native-ai/evidence/episode04-r0185-20261016/source-index.json)和[原便携事实](../../../docs/ck3-native-ai/evidence/episode04-r0185-20261016/portable-facts.actual-a01.json)。

| 项目 | 实际结果 |
| --- | --- |
| 捕获范围 | 2560×1440桌面中CK3客户区`[640,360,1920,1080]`，输出1280×720；取屏幕区域，没有录整张桌面，也不是独立HWND像素捕获 |
| 原片 | `raw-window-a01/raw.mkv`，27,208,789 bytes，H.264／30fps，无音轨 |
| 实际时间轴 | 容器46.466秒、末PTS46.433秒、1394帧，无缺失或倒退时间戳 |
| 录制闭场 | `NORMAL_TREE_EMPTY`、exit0、active0、guard error null，完整AV decode无诊断、不截断 |
| 最低时长 | 请求80秒；wall49.653296秒、编码46.466秒，两项均未达标 |
| 原生推进 | 12份完成回执，每日1 tick、overshoot0，Army18仍在2635围城、路线空 |
| 衔接 | ready→resume ACK3.272059秒 |
| 正常闭场 | 14:44:19 UTC保存date53148432；14:45:29游戏process_exit0；14:45:58屏幕seq5784 done/resources[] |

原片SHA-256 **`b15dac9e149903f116af4b16a917aba679633088f5d3be6fb477b995f49ff7b9`**；来源机器路径 `C:/ck3-e04-resume-20261015-a01/live12004-r185-window-capture-a01/raw-window-a01/raw.mkv`。raw、截图和存档没有复制到仓库。后来审计时的新容量检查通过，不改变录制hold阶段真实失败，不补发80秒素材。

Root已逐张直接审阅三张1280×720原图，回执见 [root-three-frame-review](../../../docs/ck3-native-ai/evidence/episode04-r0185-20261016/root-three-frame-review.actual-a01.json)：

| 请求时码 | 可见日期 | Army18显示人数 | 同帧 |
| --- | --- | --- | --- |
| 0秒 | 1067-02-21 | 1184 | 暂停、1%、补给300/300 |
| 23.2165秒 | 1067-03-01 | 1173 | 暂停、1%、补给300/300 |
| 46.433秒 | 1067-03-05 | 1173 | 暂停、1%、补给300/300 |

三个样本未见外来窗口、Steam或周边桌面；人数显示净变−11。但它们没有证明精确扣兵帧、物理DATA或writer来源，**不能直接称为新R03围城扣兵正例**，也不能归因为县损耗或饥饿。原audit的未审字段保持原样，后续Root审阅另附；三帧不等于连续全片观看。

这条raw可进入精确连续区间审查：检查无遮挡、无冻结、关键读数与日期可读，再将实际获准范围绑定raw SHA和帧边界。暂不批准任何clean clip，也不把原生12日回执自动转换成12天均清楚入片的结论。若以后需要80秒镜头，另按真实预算采集，不能拉长或重复本片伪装达标。

正常checkpoint为73,864,691 bytes、SHA `500ed157a401f22e8ee5433a84b6fb24850f357a964e4474c7b8af4ce67335ff`。屏幕释放回执没有同时授容量预留返还；存储闭场另记。证据包仅含选择性小原件、一份完整闭场snapshot和原逐帧PTS输出，不是完整portable closure replay。其他机器复用方法后仍须重核本机资格，全部资产期限继续按[统一存储策略](../../../docs/storage-retention-policy.md)处理。
