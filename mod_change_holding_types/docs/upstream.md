# 来源冻结记录

日期：2026-10-03。状态：已取得并冻结完整上游字节；维护适配与原始快照分离。

- 上游标题：`Change the holding types`
- 原作者：白绮
- 上游 Workshop ID：`3337428403`
- [公开页面](https://steamcommunity.com/sharedfiles/filedetails/?id=3337428403)
- 页面显示最后更新日期：2025-11-13
- 页面显示上传包大小：232.740 KB；这是页面元数据，不能作为本地文件字节验收结果。
- 下载方式：父任务经本机原生 Steam Workshop download 路线获取；callback `3406`、`EResult=1`，下载后 `Subscribed=false`。
- 下载日期：2026-10-03（Asia/Shanghai）。
- 原始只读快照：`C:/workspace/two-mod-maintenance-20261003/upstream-3337428403-original/`。
- 文件数：10；总字节：232740。
- tree SHA-256：`904700D881F7997CBC09DC1E86EFACEBDC37058F45C8790F06CC55CBB75D15E4`。
- [逐文件 manifest](upstream-manifest-2026-10-03.json)，文件 SHA-256 `d66aa92d6c7d5db5d6df0ac668359d7cb76bdbf4f34218cf9baf4247935813b8`。
- 维护版 Workshop ID：尚未创建。

`3337428403` 只作来源身份，禁止作为维护版发布目标或写入维护版内层 `descriptor.mod`。canonical descriptor 不保留 `remote_file_id`。

沿用 [自动升级建筑来源冻结方法](../../docs/auto-upgrade-buildings-upstream.md)：下载后立即复制到外置只读原始快照，按相对路径排序，以 UTF-8 `<path>\0<size>\0<SHA256>\n` 计算 tree hash。所有维护改动与原始快照分离，原片和失败 attempt 保留。

上游十文件未携带 LICENSE。仓库所有者于 2026-10-03 明确要求把本 item 独立第三方维护、适配最新 CK3 并创建新 mod 发布，本任务按该明确指令执行；记录没有原作者单独授权原件，不能用 `mod_auto_upgrade_buildings` 的作者授权替代本 item 的来源事实。保持白绮作者署名、上游链接与维护版身份。

`thumbnail.sai2` 是上游过程原片（174516 字节），保存在原始快照中，不导入正式运行树；`thumbnail.png` 作为原始主视觉保留。九个上游运行文件导入后，内层 descriptor 删除 `remote_file_id`，维护版本改 `1.0.0`、名称与 `supported_version="1.20.*"`。脚本／GUI／本地化统一 UTF-8 BOM；游戏适配 diff 和新 `cht_` effect 与原片分离。
