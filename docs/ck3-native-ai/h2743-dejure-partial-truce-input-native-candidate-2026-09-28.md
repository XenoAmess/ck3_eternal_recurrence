# H2743 守方投降：部分休战输入的原生只读候选

本候选扩展现有 `query-defender-de-jure-exit-terms-v1-16777231` 的 V1 只读 payload，增加 `truce_inputs_v1`；旧 attempt-11、旧 DLL SHA `6689ED3B3EB40F33157B028BD7067FF859F1C6ACDCFC02EDEB92A7D0F271B17E` 和 OneDrive WAR 请求均未改写。新增字段只代表在同一暂停战争基线中**尝试读取的条件输入**，不代表 `add_truce` 已执行、期限已知或终战代价已比较。来源 ACK 的独立边界见 [记录](h2743-title-prestate-source-ack-2026-09-28.md)。

## 精确取数路径

此 DLL 仍由 bridge 的精确 CK3 `1.19.0.6-steam23530548` EXE SHA-256 `2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86` 门禁限定。[磁盘 RVA/脚本审计](h2743-dejure-next-readonly-getter-candidate-2026-09-28.md)是设计来源；源码实现只复制已存在的容器或调用经该审计的纯读取 getter：

- `FLEX` 输入读攻方角色 `+0x1A8` 非空对象 `+0x220` 的 owned-perk span，逐项回读 `Perk+0x18` stable key，检查容量、字符集和唯一性，并找 `flexible_truces_perk`。这是 span 命中观测；非玩家攻方是否与原版 `has_perk` 完全等价，仍需新 live 候选验证。
- `NOMAD_BOTH` 输入先经 lookup-only `0x3B588E0` 和 name `0x3B58970` 精确往返回读 `government_is_nomadic` ID；对双方仅走存活、landed 的 `CharacterGovernment` RVA `0x26165B0` 返回路径，并比对 landed `+0x3F0`，再严格读取 `Government+0x48` 有序 flag span。`nomad_both` 只在双方 individually observed 时作布尔合取。
- 三个原始输入在同一现有 V1 战争/双方/CB/目标/资源/暂停快照门下各自双读；容器读取失败、角色路径不符或样本漂移均 typed unavailable。V1 `material_complete=false`、title/vassal/resource/truce delta 均保持 null，正式退出守卫仍拒绝无授权终战。

`short`、`long`、`border_raid_pair` 固定 typed unavailable；`evaluated_days` 与 `persisted_expiry_date_raw` 固定 null。部分读数不能代入公式生成 H2743 期限。旧 V1 payload 缺新增字段时 Python 投影仍接收，但 `truce_inputs_v1=null`，绝不补零或倒填旧 evidence。

新的静态候选 DLL 在 `D:/ck3-research-artifacts/war31-h2743-20260928/build-truce-inputs-002/xar_ck3_bridge.dll`，3,148,800 bytes，SHA-256 `1361FC0991D1FA09CB7272112D73F7F50736B7BBAD6A3656C33F9FB200CA1BAA`；同目录保存 fresh MSVC/Ninja configure/build argv 与 stdout/stderr，build stderr 为空。`build-truce-inputs-001` 在最终源码补丁之前开始编译，仅保留为历史构建，不作新候选。聚焦 Python wire/负例测试普通模式及 `-O` 模式各 10/10 通过；EXE/脚本/RVA 校验通过。**尚未运行 CK3 实机**，三个新布尔均无 H2743 live 值。下次实机须另开 exact asset/hash pin、no-launch 和只读 live attempt，屏幕与 Steam 离线门由执行者新鲜取得；不得复用 attempt-11 清场回执作为新 DLL 准入。不得提交投降、推进日期、调用 setup/resolve、广义 loaded-effect preview 或旧 G2 休战求值器。
