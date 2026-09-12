# R518/R519：scoreboard 单次遍历候选

## 结论

旧轮次 R518/PID `176532` 完成 authenticated Frontend warm-up 并终止；当前轮次
R519/PID `214004` 随后作为唯一 CK3 加载 product save。loader、native readiness、
paused seed、HUD 与 feature manifest 均为 GREEN，FFmpeg 只在这些门禁通过后启动。

首个 scoreboard source query 绑定 `snapshot_revision=3`、`date_raw=53147016`、
player `29037`、provider session `8B4CE6D385672CD1F6EEDD8E098C91E9`，仍返回
`widget_not_instantiated`。这证明 R517 后把逐名字 DFS 上限从 4,096 调到 8,192
并不足以覆盖真实 runtime widget tree；此次失败在任何游戏输入和 clean span 之前结束。

## 根因收敛与最小修复

`zg361_scoreboard.gui` 有 7,604 行、4,782 个源码 block，并包含 2,110 次 `using`
template expansion。源码 block 数不能直接充当 runtime node 数；旧实现还会为窗口内的
14 个 descendant 名字分别从 root 重跑一次 DFS，因此既重复读取同一批节点，也让固定
上限对每个名字的遍历顺序敏感。

候选实现改为从已验证的 `zg361_scoreboard_window` 做一次有界遍历；每个 runtime name
只读一次，并在同一趟中收集 15 项编译期固定 allowlist。全部名字找到后立即停止；总节点
上限为 65,536，depth 64、单节点 child count 4,096、window root、名字集合、ACL、动作和
schema 均不变。内存使用为一次约 1 MiB 的 heap reserve，并在读失败或分配失败时保持
fail closed。原生 scoreboard 定向测试对该候选为 GREEN；真实 paused query 仍必须在新
DLL、新轮次中验证。

这是实现层性能与覆盖范围修复，没有接口、架构、协议、数据格式、版本或依赖变化，因而
不触发 open_kaishek 同步。DLL 有变化，不能原位热重跑。

## 证据

- attempt：`Z:\\ck3_mod_rewrite\\_runtime\\p2-capture-r518-r525-28cc064-20260912`
- outer report：4,370,632 bytes，`F12CB1FD4383F1D5420656C02DA7C48E5B3026523FB3956A5CA7EC4DAEB0888F`
- inner report：4,315,752 bytes，`E132A51D9EBF5D5687837F68038E4D80150661653152693955ECB59772C0ED75`
- driver state：38,193 bytes，`DB695AAC3EAE41F8DCC561CA093BB6F69479C3BD4C8F810066903020446EBA4B`
- cleanup：30,902 bytes，`D2647E11FB5402FEF7D621DD2B1829C25DF112D00878454514A2AD11A24A303C`
- failed take：3,684,505 bytes，`DE9806B562F3357CB0404A46C726165DBEF91028569B7C44BC8D1656317BB635`
- timeline：7,930 bytes，`EE8502A014D13580F457805FB81BEDE4C4BBD072E7883AFE91C49E6A7C43A56E`

失败 take 无 clean span，P2 素材仍为 `0/8`。当前轮次 R519 与旧轮次 R518 均已
终止，CK3/FFmpeg 为零。下一次实际启动为新轮次 R520 Frontend warm-up、R521
gameplay，只复验 scoreboard source/open/visible 首链；若仍失败，先把缺失 widget
identity 写入证据，再决定下一项修改，不再扩大遍历上限或长跑重试。

## 同步构建

根仓候选以 commit `95dcc005efddc6d9ef6defa42e98682c31f539fc` 推送并确认与
`origin/master` 相等。随后从该 commit 建立全新 Release 构建：

- build：`Z:\\ck3_mod_rewrite\\_runtime\\native-builds\\p2-r520-r521-scoreboard-single-pass-95dcc00-v2-20260912`
- bridge：2,599,936 bytes，`C6F2B132D3A854353126BBA278355B8D833366CD96E7F4885821496484808F16`
- injector：39,936 bytes，`D3A3641E854B07BFBC097E4515E175C14535E5ADEC87878BF26B6C8F3E429474`
- focused test：125,952 bytes，`E2B9FDEC545703855640DFD3D84238CA7A6498787F813AB96D6D29F73A80BD92`，exit `0`
- build receipt：5,383 bytes，`51A9CF3F6195632F79E4A28638D1A44004B8E8A9751A9DC4FB48C3E2CBE1B874`
- 27 个 `XAR_CK3_ENABLE_*` 均为 `OFF`

receipt 保留了两个编译前 operator RED：首次 shell 外层引号错误；其次 helper 选择了
ambient Cygwin CMake。两者均未启动 CK3；最终 `v2` 使用 VS 自带 CMake/Ninja 绝对路径，
完成 124 个 compile/link step 和唯一的 scoreboard 定向测试。构建未消耗轮次。
