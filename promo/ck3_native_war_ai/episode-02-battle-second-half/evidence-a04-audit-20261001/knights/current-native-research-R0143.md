# R0143 原版骑士研究：三项 UI 闭合，三项机制仍待证

本轮只使用私有冻结源 `419cac1a956c7be356d886256c7bc689cda5327d`、桌面 run `desktop-3fevhd2-1c74096080--vanilla--R0143`、原生 episode `native-29829-a5224cf6dfcc`、实际 PID17420。actor29829 / War4 / Army18 / Combat16777218 / 33437 / 34120 均与原生 full-ID、snapshot/session/revision、原图 SHA 对照。暂停原日期53146848→53146872（1066.12.29→12.30），只推进一次。

十张 R0143 原图经独立直接审阅：33437 alive→dead、显示勇武4→2；34120 保持 alive、显示勇武7，威望301→451。左侧战斗名单完整11→10且移除33437，右侧完整19→19且保留34120；原版 breakdown CHARACTER full-ID 标记与像素对应。前后完整 battle panel 边界、两指挥官、中央读数和所有下部组成行均在2560×1440原图内且无遮挡，前后 fresh query/暂停身份与稳定 geometry/tree 亦相符。角色 UI、名单 UI、完整战斗窗三项 closed。

当前 UI 数量11→10/19→19不能替代 native ordered active14→13完整运行时原序链。四份实际主保存与preUI保存、四次真实 Rakaly 过程及三窗口全差分已由独立线程核对并归档，权威终件为 R0143-actual-endpoint-semantic-facts-a01.json。所有角色、团、威望、kills/weapon 等保存读数属于本轮端点证据；不得以显示或保存变化推定唯一执行路径。

原生 typed诊断明确 failure_gate=managed_wire_cap：assembled_output_bytes=1217950 超过 managed_cap_bytes=921600。ring7/drain_flags0 与 scoped184/scoped_flags0 是有效片段诊断，完整 DTO 仍未导出。monitor 实际 failure_flags8/truncatedtrue，已卸钩；其128条部分记录不能证明完整覆盖。骑士选择器、受害者唯一实际死亡执行路径、13域完整可变状态链仍 pending，global_mutable_bundle_complete=false，严格完整机制 verifier 未运行。

本轮 consumer 在真正+24后错误检查 requested_days，而原版 response 字段实际为 requested_horizon_days=1，导致原计划即时 FINISH 延迟。原失败、真实请求/响应、随后唯一 fresh FINISH continuation、wire-cap RED与monitor overflow全部原样保留；未重发推进或额外一天。完整诊断保全的是原 parsed return，wire_bytes_preserved=false也明确记录。

本轮未调用 native hover，因此不制造一次 R0143 hover RED。冻结UI源码仍有此前已实证的派生 CPdxGuiTextbox RTTI 限制；当前真实 tooltip 图通过每次原图/独立轴坐标换算、前景 PID/HWND 和同暂停 snapshot 绑定的 mapper 悬停取得。eligible军役名单不代替战斗名单。

ROOT07/LIVE143正式停止写入；私有源冻结、构建、初始错误草稿、SDK/stdio、原截图/请求、主前后及额外 preUI 存档、日推进/FINISH失败、清理、显示恢复和CAS过程完整入索引。SDK实际job exit0、游戏已清理、Steam离线与1024×768恢复由根直接审阅新原图，屏幕任务done/resources[]/CAS3490。清理通过不升级机制RED。

索引 6626 项原资产，3820 份小文件 binary exact copy，2806 项永久外置原件完整路径/bytes/SHA。raw范围 `.gitattributes` 为 `* -text -diff`，逐项源/副本字节相等，停写源 file set/mtime 前后相同；preview和伪LFS指针均不替代原图/存档。

仅新建 R0143 研究归档与事实文件；未改旧R0140/R0141/R0142、master、冻结源码、影片/config/composer/字幕/素材，未render/export/upload/signoff。Git仅以当次core.longpaths=true作只读branch/HEAD/status确认，未改配置、未提交或push；等待根审阅本次精确handoff后另授权canonical私有提交。

- [原资产索引](R0143-current-research-originals/assets-index.json)
- [逐项精确复制验证](R0143-current-research-originals/copy-verification.json)
- [事实记录](current-native-research-R0143.json)
