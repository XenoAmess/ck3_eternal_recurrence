# 五项 Workshop Mod 的本机移除与禁回装

`machine_id: desktop-3fevhd2-1c74096080`。以下结果仅属于这台机器；Root 最终核验时间为 **2026-10-19T04:59:17Z**，闭场新图于 **05:00:43Z** 直接审阅，Steam 仍显示“当前处于离线模式”。其他机器的订阅、安装和权限未作修改。

本机以下五项 Mod 的旧载荷已移除：

| Workshop ID | Mod |
| --- | --- |
| 2291024373 | 《魔戒》正式版 |
| 2993056101 | 《魔戒》Open Beta |
| 2962333032 | 《冰与火之歌》 |
| 3192256710 | After the End |
| 2224124758 | 幻萌入侵角色包 |

本轮删除 **86,062** 个文件、**8,459** 个空目录，回收最后链接分配量 **56,401,892,912 B（52.53 GiB）**，0 失败。Root 独立复核了 87 个文件批次和 9 个空目录批次；没有把卷空闲差额全部归因于此操作。[最终结果与原件索引](evidence/2026-10-19-steam-five-local-control-desktop-3fevhd2-1c74096080/ROOT-FINAL.actual.json)

本机 `C:/SteamLibrary/steamapps/workshop/` 下的 `content/1158310`、`downloads/1158310`、`temp/1158310` 三根现各保留五个受 ACL 保护的 **0 B 普通文件占位**。当前同名路径存在是保护措施，不是重新下载的 Mod 目录。安装后 123 项拒绝探针和 3 组普通兄弟项操作均符合预期；独立新进程复核同样通过。后续只读核对确认 15 个占位及三个父 ACL 精确匹配，77 个其余目录名称保留，其 DELETE、ADD_FILE、ADD_DIR 访问检查均允许。它是持久文件系统屏障，没有启动守护进程或自动删除调度。[安装](evidence/2026-10-19-steam-five-local-control-desktop-3fevhd2-1c74096080/LOCAL-ACL-APPLY.actual.json) · [独立复核](evidence/2026-10-19-steam-five-local-control-desktop-3fevhd2-1c74096080/LOCAL-ACL-VERIFY.actual.json) · [只读后验](evidence/2026-10-19-steam-five-local-control-desktop-3fevhd2-1c74096080/POSTAPPLY-READONLY.actual-a01.json)

账号订阅未修改：本轮没有 Steam API 初始化、退订、切换在线模式或在线下载测试。本地 `appworkshop_1158310.acf` 前后均为 28,041 B，SHA-256 相同。当前客户端 `11.12.30.7` 的静态链支持上述三根的 `appid/itemID/<file>` 布局；共享 `state_1158310_*.patch` 保持可写。本次不证明未来零 CDN 流量；首次自然需要上线及客户端或库路径改变时，应检查共享 patch 与实际落盘路径。[静态来源](evidence/2026-10-19-steam-five-local-control-desktop-3fevhd2-1c74096080/STATIC-LAYOUT-PROOF.actual.json)

[本机长期偏好](machine-preferences/desktop-3fevhd2-1c74096080.steam-workshop.json)持续到用户明确撤销，不随审计材料到期而失效。[原 DACL 备份](evidence/2026-10-19-steam-five-local-control-desktop-3fevhd2-1c74096080/LOCAL-ACL-ORIGINAL-DACL-BACKUP.actual.json)是当前必要的撤销资料，已精确保存在 Git；**2027-10-19** 作用途与可恢复性复核，复核日期不授权删除唯一可恢复副本，也不撤销禁回装偏好。它不被登记为用户明确要求永久保留的独立资产。

[维护工具](../../tools/maintenance/steam_workshop_local_block.py)仍只允许此机器、五个 ID 和上述精确本地库。只恢复父 DACL 的旧撤销尝试留下了 15 个子项拒删，已保留失败；修正后的自有临时目录试验使用预先持有的 WRITE_DAC 句柄恢复子项后再恢复父项，15 项均可删除。管理员启用 SeBackupPrivilege、SeRestorePrivilege 后重新打开句柄的分支尚未提权实测。未来仅在用户明确撤销后恢复精确原权限，不重置整个 Steam 树。[撤销修正范围](evidence/2026-10-19-steam-five-local-control-desktop-3fevhd2-1c74096080/ROOT-DELIVERY.actual-a04.json)

仓库版仅调整相对导入、selftest 子脚本名称及其入口身份守卫；语法、真实身份 helper 导入和错误机器拒绝检查通过，未以此追授一套新的 ACL 实测。完整来源、历史失败和精确 SHA 见[来源索引](evidence/2026-10-19-steam-five-local-control-desktop-3fevhd2-1c74096080/source-index.json)。
