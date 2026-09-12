# R522/R523 scoreboard 全局根定位 RED

## 结论

旧轮次 R522/PID `49964` 完成 authenticated Frontend warm-up 后终止；当前轮次
R523/PID `113504` 随后作为唯一 CK3 实例，以 `-loadsave=autosave` 加载产品存档。
R523 通过 exact-build loader、native readiness、paused seed、HUD 和 feature manifest
门禁，第一条只读 scoreboard query 随即返回
`unavailable/widget_not_instantiated`。runner 将其保留为
`scoreboard_visibility_provider_unavailable`，在任何游戏输入和第一段 clean span 前停止。
R522、R523 均已终止，CK3 与 FFmpeg 进程为零；P2 素材仍为 `0/8`。

R521 后新增的逐控件诊断在本轮生效。固定 allowlist 的 15 个身份全部返回
`exists={status:available,value:false}`；provider session 为
`DAD8092EFBBBB101D78C1F1B28B74CD9`，paused binding 为 native revision `3`、
date `53147016`、player `29037`。这排除了“某个深层子控件缺失”和“继续提高
fixed-window DFS 上限”两个方向：direct top-level lookup 没有返回注册的 scripted
widget，因而此前的 window 子树遍历根本没有开始。

## 最小修复

`ck3_autonomous_player/native_bridge/src/zhongguo_scoreboard_state_v1.cpp` 的
`FindFixedWidgets` 现在在 direct lookup 未命中或名字不符时，读取同一 exact-build
GUI owner 的 `+0xD0` 全局根，并复用现有固定 15 名 allowlist 的单次 bounded traversal。
这条 owner/root seam 已由 promotion provider 的 R13/R14 实机路径验证。遍历仍限制为
65,536 个节点、depth 64、单节点最多 4,096 个子项，并在 15 项全部找到时提前结束；
没有放宽名字、schema、ACL、动作能力或 readiness。

对应 native focused target 重新编译并退出 `0`；测试可执行文件为 126,976 bytes，
SHA-256 `679248B4FAFE8E19272498A4A7A455D2536D6B49AA2E79BC8609AABA5CB04632`。
第一次增量构建调用未加载 `VsDevCmd`，在标准库头 `cstdint` 前失败；随后使用显式
Visual Studio developer environment 重跑成功。该环境错误没有启动 CK3，也不是候选代码 RED。

## 冻结证据

- attempt：`Z:\ck3_mod_rewrite\_runtime\p2-capture-r522-r529-f3fe1bc-20260912`
- frozen plan：11,273 bytes，`6460FC4DCABADA483B12E1F19C45A3AEEB89E5368990850D5D0F27B41A3336D5`
- outer report：4,370,665 bytes，`4213A944C4F5C1A923A2C03F5A5D00F0F3714777224B30F97F9068F7D7FF3916`
- inner report：4,315,785 bytes，`10B1AFD87CAA09F9541E751DF110B20595A0E6C7C680503450026316C4468B89`
- driver state：39,258 bytes，`CF2243B787E6971ACF9283E20DAB4623B23DF4B32D83F057898ED2330B56B8A5`
- cleanup：30,901 bytes，`8BA4376DAFE20A822E58341E85100E1BBFCBA1C226160646AD1D5B556E17BA4A`
- failed take：3,684,736 bytes，`DB4C6A17A6EAA04D0BB9CA281FC502DC5CB27056656485D5FB9AD21489DE9C99`
- timeline：7,932 bytes，`7EEC3E5BBD5215901A257524F3258820C54DA955A7E2C170C439D63AE8A75269`

本轮从诊断 DLL 切换到下一候选 DLL 属于 DLL 变化，不能热重跑。下一次 bounded
实机需先从同步提交构建全新的 Release bridge，再启动新轮次 R524 warm-up 与
新轮次 R525 gameplay。P1 继续保持 `9/9 GREEN`；视频硬锁已解除，剪辑、导出和
发布仍等待八段 clean footage 与内容复核。此次内部根定位没有改变 MCP wire、版本、
公共字段或依赖，不触发 open_kaishek 兼容层代码同步。
