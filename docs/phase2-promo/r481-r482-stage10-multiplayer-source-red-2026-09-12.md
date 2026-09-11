# R481/R482 Stage 10 多玩家来源准入 RED

## 结论

T0-P1 保持 **`8/9 = 88.9%`**，唯一未签收项仍是玩家可见的 `zg361mg.120`，P2 最终宣传视频继续
`LOCKED`。旧轮次 R481 完成 frontend warmup 后退出；当前轮次 R482 是唯一 gameplay 实例，完成 loader 日志门后在
native readiness 停止。Stage 10 action 没有开始，真实 B1、公示回调、`.90` 和 `.120` 均未执行，因此本轮不能推翻
`58e8cc9` 的产品修复，也没有形成新的 B1 产品 RED。

R482 暴露的是输入准入缺陷：候选文件虽为 `SAV0101`，内部仍声明 `meta_number_of_players=5`，并含五组
`played_character`。旧 v2 receipt 只检查 header、离线角色拓扑和 hash，没有执行仓库已有的单玩家/live provenance
准入规则，错误地把多人 lineage 送进了 CK3。

## 运行事实

- frozen code：`c1d43ba385d50bbd3ac5dc47cdbdadc4f1d15873`；production tree：
  `B5C0ED99F0C87507E1B8D5DF7E48B96EDDD69DCD57908C0A2CF5D057404B5404`。
- 输入：`112339684` bytes，SHA-256
  `80030146765A960EABAA1E38E90FF88CDEB8FBBBB2442E30E695FDFBFD64687D`。
- 旧轮次 R481 warmup PID `130504`；当前轮次 R482 gameplay PID `201932`，connection generation `1`；两者没有重叠。
- loader append-only 门在 `119.075 s` 到达 `load_save / GREEN`，fatal count `0`。CK3 日志随后进入 `Setting idler 'In Game'`。
- native snapshot 为 `map_ready=true / paused=true / date_raw=51841680`，但 `played_character=null`；mailbox 未安装，
  executor、pump epoch、application-state pointers 和 date binding 均未建立。300 秒门限后按合同返回 RED。
- action 没有收到业务控制，游戏时间没有为 Stage 10 推进；没有进行第二次尝试，也没有延长门限。

这与 R410/R412 的多人来源准入失败同类。新的 source SHA 不改变同类因果结论；后续不得再用该文件及同组
`autosave_1.ck3`、`autosave_2.ck3` 占用 CK3 串行槽。三份文件离线均为五玩家内容。

## 最小准入修复

Stage 10 operator 的目标自有 receipt 升为 `zg361_stage10_player_publication_source_v3`。除原有 exact-build、产品树、
checkpoint 和玩家经理拓扑绑定外，现在还强制要求：

1. 离线 `meta_number_of_players=1`；唯一 `played_character` 必须是目标 manager/local player `1`；
   `currently_played_characters` 也只能含该 manager。
2. receipt 必须引用一份 hash-verified 的 `zg361_stage10_player_source_capture_v1` 实机来源证明。
3. 该证明必须绑定同一个 checkpoint 与产品树，记录 paused/map-ready 的目标玩家、直属上级、非独立、公爵及以上、
   `government_is_celestial`，并证明 checkpoint 由 MCP 原生保存。

聚焦 operator 测试在 normal/optimized 下各 `4/4` GREEN，新增反例锁定五玩家 receipt 的启动前拒绝。实现与测试通过
`py_compile`，`git diff --check` GREEN；没有扩大到全量 L0，也没有为该 Python 准入修复启动 CK3。

## 清理与后继

canonical cleanup SHA-256 为 `AA245F4B249ADB32C20EC547F43053B8BCDA084435F893D61F0E131B7950C54F`，
managed cleanup SHA-256 为 `A87F9EE46B47723A40928C56D2AA9BB94B4D11C7049FBD04242955D61F2E9D87`，均为
GREEN。当前轮次 R482 与旧轮次 R481 均已终止；CK3、Operator 作业、Operator MCP 服务和监听端口均为零。

下一步先从已有 live-admitted 单玩家 checkpoint 生成玩家经理 source，再执行一次新的 30 游戏日 Stage 10 尝试。离线
候选扫描已在 R159 单玩家世界中找到玩家 `32904` 的多名合格天朝直属经理；该临时扫描逻辑必须先迁成无固定账号、路径
或轮次的通用工具，再允许新 CK3 启动。新来源需经过 v3 receipt，不能再次依赖文件名或 `SAV0101` header 放行。

## 证据索引

| 证据 | SHA-256 |
|---|---|
| loader progress | `D5356E302F0C3E254AC24B0F3F6E260C7E802E6CB88946A7B803236656B59FC6` |
| native readiness RED | `73437AF4F4C721C1B13DD1B442844B3239E3D03AE0E2DF4321FD1041A48CEBC9` |
| loader gate RED | `34B7CAAC0A18C0355D10EC6F1853C1313686A1B5AB88E4558A1FF112CAEB9D48` |
| Stage 10 operator RED | `BB2B04658CC5F1975AFB0429E33ADFB53F60E1D02CA38F3CAA0A8EA38313D545` |
| canonical cleanup GREEN | `AA245F4B249ADB32C20EC547F43053B8BCDA084435F893D61F0E131B7950C54F` |
| managed cleanup GREEN | `A87F9EE46B47723A40928C56D2AA9BB94B4D11C7049FBD04242955D61F2E9D87` |

所有运行证据位于
`Z:\ck3_mod_rewrite\_runtime\p1-stage10-player-publication-r481-r482-c1d43ba-20260912\live-artifacts`。
本轮没有触碰宣传工具或视频文件，也没有改变公共 Operator MCP 1.1、DLL、游戏文件、启动参数或加载顺序。目标自有
receipt schema 发生 v2→v3 变化，根仓提交后必须同步 open_kaishek 兼容说明。
