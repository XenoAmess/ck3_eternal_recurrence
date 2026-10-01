# R0142 原版骑士研究：UI 端点与机制失败分别保全

本轮使用私有冻结源 `4ad477ee33e15a93e412f711c7b05b216a2e6651`，桌面 run `desktop-3fevhd2-1c74096080--vanilla--R0142`，原生 episode `native-29829-a892e2bcf200`，实际 CK3 PID 14700。actor 29829 / War4 / Army18 / Combat16777218 全程绑定；暂停原日期 53146848→53146872（1066.12.29→12.30），只实际推进一次。

独立核对前后三项 UI 证据后，次日角色界面、战斗骑士名单变化、完整战斗窗三项 UI 缺口 closed。33437 原版角色界面 alive→dead、显示勇武4→2；34120 保持 alive、显示勇武7，威望301→451。以上均为同轮角色 UI 读数，不能据此归因死亡执行、武器或威望生产者。

本轮完整原版战斗名单左11→10且移除33437，右19→19且保留34120；原生 UI breakdown 的完整 CHARACTER 标记与原图相互对照。它不是 native ordered active14→13 完整原序名单的证明。原图边界、两位指挥官、中央读数及所有下部组成行完整可见；暂停原生 geometry/tree 及前后 fresh query 支持同窗身份，真正完整可见仍由原图直接审阅判断。原 native hover 因 CPdxGuiTextbox 派生 RTTI 门禁拒绝且未 dispatch，真实名单画面来自有原图绑定的 coordinate-map 悬停兜底。

骑士选择器、受害者唯一实际死亡执行路径、13域完整可变状态链三项仍 pending，global_mutable_bundle_complete=false。daily FINISH 是 RED_MANAGED_DTO_UNAVAILABLE；monitor FINISH 是实际 failure_flags=8/truncated=true 的原生 overflow RED，detours_uninstalled=true。严格机制 verifier 未运行，不能把 schema 修复、UI PASS 或 SDK 清理 PASS 改称机制闭合。军役 eligible 名单 owner 门禁失败保留，也不代替战斗名单。

失败 a09/a10、一次实际推进 a11 及保存/trace RED、wrong-prefix preflight、私有源冻结、完整构建、SDK、请求/响应、stdout/stderr、原截图、主前后与额外 preUI 保存、恢复和 CAS 过程均入资产索引。主前后 immutable 原件 SHA 分别为 4562E87AB45115C5B60350DEAC4FC75DD58945436B8BE80D47A8E5F58625E40E 和 48182193DB2E78E7B3CCF00BBE9EBE7A4F7E500CADE0F12784E6146770D82267；旧 checkpoint 是输入来源，不填本轮缺失字段。

实际 SDK job 全 exit0，CK3 受控清理 exit1 且进程树消失；原模式1024×768与 Steam 离线已由根直接审阅新图，屏幕任务 done/resources[]/CAS3461。生命周期清理通过与机制 RED 分开记录。

永久索引原资产 6666 项；小文件 exact copy 3839 项，外置完整原件 2827 项。原图/存档/大文件保留完整绝对路径、bytes 与 SHA；preview 不替代原图，不写伪 LFS 指针。raw 子树 `.gitattributes` 为 `* -text -diff`，逐项二进制 bytes/SHA 相同，原件停写后 file set/mtime 均未变化。

本次仅创建研究归档与新事实记录，未操作 Git/master、游戏/屏幕、研究源码、视频配置/字幕/素材、render/export/upload 或人工成片 signoff。等待根安排私有 canonical 提交。

- [完整资产索引](R0142-current-research-originals/assets-index.json)
- [逐项复制验证](R0142-current-research-originals/copy-verification.json)
- [事实记录](current-native-research-R0142.json)
