# 验收报告

执行日期：2026-09-09（Asia/Shanghai）
目标：XenoAmess的体验优化 1.0.2 / CK3 1.19.0.6

## 结论

| 层级 | 结果 | 证据 |
|---|---|---|
| L0 静态、发布本地化、exact-byte、可复现构建 | GREEN | 发布本地化 validator、builder 单测、双构建 SHA、exact-tag 官方 CI |
| L1 隔离加载、MCP readiness | GREEN | Workshop fresh-cache 最终 artifact 的 `04_mcp_readiness.json` |
| L2 开关、死亡、卸任、禁转 flag | GREEN | 14 个必需引擎 PASS/DONE marker 各一次，另记录死亡继任观察项 |
| L3 Steam fresh-cache | GREEN | item `3798133925`，19/19 strict verify，fresh-cache 实机矩阵 GREEN |

## 发布身份与 L0

- Git tag：`xqol-v1.0.2`
- Git commit：`a8acdc19c36a94e807c11f047f3d4bc85f7ff941`
- GitHub Release：<https://github.com/XenoAmess/ck3_eternal_recurrence/releases/tag/xqol-v1.0.2>
- 正式 manifest SHA-256：`d1618abc1ffe6b3f2e611799001b72793ac99676f8fd5b28061f724d07538ce3`
- deterministic ZIP SHA-256：`edf50efd2d64044c1ea62f9c9177759d375324dabf2e08aea56d1acb124e95c7`
- thumbnail SHA-256：`832e36c9394e6ed74aa8669507d55486ceacc0403f49daa8b456fc3cb1067fe3`
- exact-tag 官方 CI：runs `34251618381`、`34251655995` 均 GREEN。

L0 确认 19 个 runtime 文件、五种 appointment type、三份受控原版覆盖、九种本地化结构、七语发布翻译门禁与 640×640 thumbnail。法、德、日、韩、波、俄、西均为 22/22 key，格式 token 与英文基准一致；未获得七语母语者签核。三份 appointment 文件移除五个 `XQOL_AUTO_APPOINTMENT` 块后逐字节等于本机 CK3 1.19.0.6 原版。

## Workshop fresh-cache

- Workshop item：[`3798133925`](https://steamcommunity.com/sharedfiles/filedetails/?id=3798133925)
- Launcher 上传成功：2026-09-09 01:20:02（Asia/Shanghai），日志为 `C:\Users\1\AppData\Local\Paradox Interactive\launcher-v2\logs\launcher-2026-09-09.log` 第 1784 行 `Publishing mod succeeded`。
- 空路径下载缓存：`D:\Program Files (x86)\Steam\steamapps\workshop\content\1158310\3798133925`
- ID-bearing sidecar manifest SHA-256：`a896600926a79d31ff3bc53e9d162c47666547d1965be407d2269734d916ed7b`
- sidecar ZIP SHA-256：`edf50efd2d64044c1ea62f9c9177759d375324dabf2e08aea56d1acb124e95c7`
- `--workshop-cache` 严格核验：19/19 GREEN；只接受 Launcher 注入的 item ID 与允许的换行规范化。
- 匿名 Steam API 回读：`visibility=0`、标题 `XenoAmess的体验优化`、`Gameplay` 标签；描述仅规范化末尾换行后逐字符等于 `workshop/xenoamess_quality_of_life_description.bbcode`。
- 远端 preview：640×640 PNG，768,568 字节，SHA-256 `832e36c9394e6ed74aa8669507d55486ceacc0403f49daa8b456fc3cb1067fe3`；commit-pinned GitHub raw 主图 HTTP 200。

## L1 / L2 / L3 最终实机

命令：

```powershell
& tools/.venv/Scripts/python.exe tools/run_xenoamess_quality_of_life_acceptance.py `
  --source 'D:\Program Files (x86)\Steam\steamapps\workshop\content\1158310\3798133925' `
  --bridge-dll 'ck3_autonomous_player/build-fresh-xqol-1.0.1/xar_ck3_bridge.dll' `
  --bridge-injector 'ck3_autonomous_player/build-fresh-xqol-1.0.1/xar_ck3_bridge_injector.exe'
```

最终 artifact：`D:\workspace\ck3_xqol_publication_process_assets\xqol\runs\zqa_20260909_043524_3fe57500`

- 结果：GREEN；耗时 623.051 秒。
- exact build：CK3 `1.19.0.6`；`ck3.exe` SHA-256 `2d00ff3101ef70b566f2fcbae292f09263199c80e9dc8f139b82d7d96f83db86`。
- MCP：`native-headless`；paused、map-ready、semantic state、transport 与 PID binding 全部 GREEN。
- 产品开启/关闭决议、原版 baseline heir、启用态最高非玩家 heir、真实卸任、真实自然死亡、禁转 flag 所有权、关闭恢复与既有 flag 保留全部 PASS。
- 死亡路径先由 MCP 短暂推进暂停的模拟队列，再重新暂停；本次明确记录 `death_used_predeath_current_heir`，并通过 `death_transferred_to_non_player_successor`。
- runtime product tree SHA-256：`5d224abfe224c291a34f7f425a25bc8a8d9f5f5af84a67bb5dd3592cfef45b5d`；fixture tree SHA-256：`e95f099289dc58ffc5975af244f24425885339499f353e40874edd50b6b53399`。
- runtime/source 树未被 CK3 改写；原生进程树清理证明 GREEN；一次性 state dir 已删除；受保护 Steam/真实用户目录未变化。

关键哈希：

| 文件 | SHA-256 |
|---|---|
| `report.json` | `b01a7ee987ca591aee4e2abffcbf9b81f2c833743490830cd123ed8730a5b19a` |
| `cell/report.json` | `2d01847d7dfeb913806376f56010627260da6ea855fea132188319d0d8454264` |
| `cell/04_mcp_readiness.json` | `679e5406bb6a0a17eedb5695f83846bad293c281daaed5a328239597cb8cb938` |
| `cell/09_death_settlement_tick.json` | `dfeb9eb738461ad11bf86cc40c20629eb723d6105bc26b65c6da16657fecd746` |

MCP 当前不发布 appointment score、角色变量或角色 flag，故这些字段由仓库外部 fixture 在 CK3 引擎内断言；暂停、地图 readiness、模拟推进、前后 paused snapshot 与进程绑定均由 MCP 完成。简体中文正式名、四个决议标题及确认按钮已在本次正式 fresh-cache 会话中由 OCR 实读。

## open_kaishek 预验

预验使用 checkout commit `33d690234d8217422978ee642055ab1b13e44c76`、CLI JAR SHA-256 `cc42a0bbd4991095deb4c8af4142a4657d46d07d616b89643a9f2d7a1e4a3cd7`、profile `ck3-1.19.0.6` 与 exact CK3 EXE hash。产品 fresh-cache 与最终 fixture 均 parser GREEN；validator 因尚未覆盖 XQOL 目录/opcode 返回独立 tool-coverage RED，IR/runtime 跳过。该 RED 未被冒充 CK3 capability RED，也不替代最终实机 GREEN。

## 保留的 RED 尝试

历史 1.0.0 夹具 RED 与本次发布尝试均原样保留，没有覆盖或冒充最终 GREEN。本次主要路径如下：

1. `zqa_20260909_013538_0ba0e296`：runner 尚不接受 fresh-cache 内层 Launcher ID。
2. `zqa_20260909_014730_cbbdd753`：五分钟超时且 Windows Update 弹窗遮挡启动画面。
3. `zqa_20260909_020023_4e9229ba`、`zqa_20260909_021613_da3eaae8`：本机冷启动超过旧五分钟预算。
4. `zqa_20260909_032959_be5a64a5`：死亡 holder 在同一 GUI 帧被提前读取。
5. `zqa_20260909_040040_458e6fd8`：修复同帧竞态后证明暂停地图不会自行处理排队死亡继承。
6. `zqa_20260909_041836_9447142e`：MCP 已推进日期，但随机样本的预死亡 `current_heir` 身份不是稳定门禁；由精确产品合同修正为“title 离开死者且绝不落到玩家”，同时保留候选身份观察。
7. `zqa_20260909_043524_3fe57500`：最终 GREEN。

正式 staging 已从 `xqol-v1.0.2` tag 重建；内层 `descriptor.mod` 不含 `remote_file_id`。item ID 只保留在用户目录外层 descriptor、Steam cache 与发布 sidecar。
