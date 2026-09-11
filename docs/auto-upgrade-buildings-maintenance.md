# “自动升级建筑”1.19.0.6 维护记录

状态：实现、L0 与隔离 CK3 核心实机矩阵均已完成；
`desktop-3fevhd2-1c74096080--auto-upgrade-buildings--R0013` 在 CK3 1.19.0.6 上取得 GREEN。本文记录的是维护判断和可复核证据，
不替代上游原始字节记录，也不代表已经上传 Workshop。

## 诊断结论

上游脚本可以通过基础括号检查，但运行合同已经落后于 CK3 1.19.0.6：

1. `auto_build.0004` 每轮使用 `every_province` 扫描全地图，再以 `province_owner = root` 过滤。当前原版已有
   Character scope 的 `every_directly_owned_province`；旧写法在每名启用玩家的每次轮询中承担不必要的全图成本。
2. 四个升级模板都依赖嵌套调用中的隐式 `prev` 读取付款人和文化。1.19 的原版建筑 effect 在 Province scope 明确保存
   `holder` 与 `build_owner`；维护版同时保存稳定的 `aub_payer`，不再依赖调用栈相对位置。
3. 每一级是互相独立的 `if`，因此同一建筑链能在一次轮询中连续升级多级并连续扣款。维护合同改成 `if/else_if`，每轮每链最多一级。
4. 上游四分类模板并不等于 1.19 的实际元数据。例如 `caravanserai`、`watermills`、`windmills` 与 `workshops` 当前使用
   `expensive_building_tier_*_cost`，而旧版按 normal 扣费；`hunting_grounds`、`logging_camps`、`outposts` 等按 cheap 定价，
   旧版也有多处套错。旧版经济模板在五、六级仍要求 `innovation_windmills`，而多条 1.19 普通经济链的标准路线已使用
   `innovation_guilds`。
5. 上游未排除 `has_ongoing_construction = yes` 的地产，瞬时 `add_building` 可能覆盖正常施工流程；当前原版通用 holding trigger
   还包含 `temple_citadel_holding`，不能再只靠该 trigger 实现产品的“排除曼荼罗”边界。
6. 旧循环由每名角色自行续排 `auto_build.0003`，没有单实例 seed。更新、重复排队或异常读档可能产生并行循环；维护版增加
   rootless `auto_build.0005` 和全局 seed，使旧存档中已经排队的 `.0003` 汇入唯一循环。
7. `add_all_buildings_effect` 与四个 `au_simple_*` 是无命名空间的通用名称，容易与其他 mod 冲突。它们不是存档公开 ID，维护版将
   内部 effect 全部收口到 `aub_` 前缀，同时保留 `auto_build.0001/.0003/.0004` 和 `enable_auto_build` 以兼容旧存档。

## 维护实现

- `tools/auto_upgrade_buildings_data.py` 冻结 43 条上游建筑链在 CK3 1.19.0.6 下的费用档、标准革新路线和地产等级门槛。
- `tools/gen_auto_upgrade_buildings.py` 生成 301 条逐级升级边；生成结果只允许从数据表刷新。
- 玩家启用决议建立或复用唯一全局循环；每 15 日只对启用功能的真人玩家派发执行事件。
- 执行事件只遍历玩家直接持有、未出租、无在建项目的城堡/城市/神殿 province；部落、游牧、曼荼罗、主建筑、公国建筑、
  特殊建筑和未列入 43 链的内容不会进入 dispatcher。
- 每个升级分支先验证资金、标准革新与 holding 等级，再原子执行 `add_building` 和一次扣款。国库足额时只扣国库，否则才检查并
  扣个人金钱。
- 构建器只投影 7 个运行时文件，README 不进入 staging；canonical descriptor 禁止 `remote_file_id` 和上游 item ID。

## 证据状态

- 上游字节：见 [auto-upgrade-buildings-upstream.md](auto-upgrade-buildings-upstream.md)，tree SHA-256
  `E878367B2A105CC3C9EFFA2D63543A6EB983BF13FC8557C8F5B6DF5BFEB595B7`。
- L0：生成一致性、43×8 原版 building ID、301 个升级边的费用 token、革新定义、作用域/循环约束、UTF-8/BOM、双语本地化、
  7 文件 allowlist、5 个构建器单测和 deterministic ZIP 均已通过。
- Open Kaishek：本机 `D:\workspace\open_kaishek@890b32d` 的 Java 25 启动器在 `java -version` 与 preflight 中均持续卡死；该项是
  工具环境 RED，不是产品 RED，未在无变化条件下重复运行。
- `desktop-3fevhd2-1c74096080--auto-upgrade-buildings--R0001/R0002`（legacy `R405/R406`）：隔离启动脚手架错误，
  均在 CK3 进入解析前终止并保留，分类为 harness RED。
- `desktop-3fevhd2-1c74096080--auto-upgrade-buildings--R0003`（legacy `R407`）：上游基线直接启动后持续工作，但 1800 秒内未到达
  日志/主菜单状态；只终止该轮自有 PID，分类为 environment RED。
- `desktop-3fevhd2-1c74096080--auto-upgrade-buildings--R0004`（legacy `R408`）：保护快照错误地遍历了 83 个无关 Workshop 树，
  CK3 未启动；修正 runner 后保留该轮并分类为 harness RED。
- `desktop-3fevhd2-1c74096080--auto-upgrade-buildings--R0005`（legacy `R409`）：维护版已启动，但在等待主菜单期间代码复核发现
  付款后置条件需要补强；只终止本轮自有 PID，修正后以新轮次复验，分类为
  superseded。
- `desktop-3fevhd2-1c74096080--auto-upgrade-buildings--R0006`（legacy `R410`）：最终 7 文件 production projection 与外置
  fixture 均按精确 tree hash 挂载，CK3 进程持续响应，但 1800 秒内仍停在
  “启动游戏中……”画面，未进入主菜单或 fixture 场景。`error.log` 为空，报告未发现产品诊断；产品与 fixture 前后 tree hash 不变，
  真实用户资料不变，退出后以 Get-Process/WMI 双源确认 CK3 进程数为 0。该结果只能分类为 environment RED，不能证明玩法 GREEN，
  也没有证据把它归因于本 mod。证据保存在
  `D:\workspace\ck3_auto_upgrade_runtime\R410-maintained-live\artifacts`。
- R0006 的环境 RED 根因已确认：本任务早先遗留的 `rg.exe` PID 12388（父 PowerShell PID 22848）从 21:45 起扫描整个
  `D:\workspace`，令 D 盘平均队列约 14、峰值 16、平均传输延迟约 40 ms，而吞吐仅约 7.5 MB/s。按用户指令只终止这两个
  精确进程后，D 盘平均队列降至约 0.007、延迟约 0.3 ms；R0007 在同一 D 盘本体上 11 分 48 秒到达主菜单，证明阻断来自
  I/O 竞争，不是 CK3 或本 mod 死锁。
- R0007 同时暴露并促成修复三项真实 1.19 加载问题：decision 的旧 `ai_check_frequency`、缺失 tooltip 本地化、无引用且缺少
  本地化/主题的 `auto_build.0001`。修复提交为 `92b94ecf`；此后的 R0008–R0013 产品相关诊断均为零。
- 游戏迁移到 `C:\SteamLibrary\steamapps\common\Crusader Kings III` 后，EXE SHA-256 保持
  `2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86`。R0008 首次在 C 盘以隔离 userdir 到达主菜单用时
  5 分 46 秒，较无竞争 D 盘 R0007 的 11 分 48 秒缩短约 51%；R0009–R0013 稳定在约 5 分钟至 5 分 15 秒。
- R0008/R0009、R0010/R0011 与 R0012 分别保留为资金假设、跨日被动经济假设、以及非法 fixture `remove_gold` token 导致的
  fixture/harness RED。它们均未改写产品树或真实用户资料；R0010 已取得 `has_treasury = yes`、国库下降和建筑升一级的正证据，
  R0011 已通过国库与停用场景。最终夹具在一次性环境中先切换到真实拥有国库的 `celestial_government`，再切回
  `feudal_government` 验证个人金币路径，并新增静态门拒绝已证伪的 `remove_gold` effect。
- `desktop-3fevhd2-1c74096080--auto-upgrade-buildings--R0013`：402.065 秒内完成核心 source-live 矩阵并取得 GREEN；国库优先且
  `outposts_01 → outposts_02` 每轮只升一级、停用后零建筑副作用、无国库时只走个人金币、重新启用后的循环可干净停止、两种资金
  都不足时建筑不变，五项 marker 全部 PASS；验收结果事件由 OCR 看见并关闭。产品相关诊断为 0，产品 release tree
  SHA-256 为 `E0B95B5228670633EB7DBFAFA13F2B4555C6B72BCDD12242CA208B1F7DB2224F`，运行前后产品/fixture tree 均不变，
  临时 userdir 已删除，受保护 Steam/CK3 真实资料未改变，退出后 Get-Process/WMI 均为 0。报告与截图保存在
  `C:\Users\1\AppData\Local\Temp\desktop-3fevhd2-1c74096080--auto-upgrade-buildings--R0013`。
- 最终离线构建仍为 7 文件；ZIP SHA-256 为
  `71143C1550F043CEC004EB4B6C6A7DCBBE2BCD2F62577E91E3FA9FA0BE440471`。

本轮没有 Workshop 上传、订阅缓存覆盖、tag 或正式 release；Steam 在取得上游字节后持续保持离线。R0013 完成后连接日志仍只有
`CClientJobGetClientUpdateHosts: failed to get updated list, error 3`，没有重新登录记录。
