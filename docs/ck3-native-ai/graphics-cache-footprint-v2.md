# 公共图形缓存候选：v2 输入投影

旧规则把所有 mod 业务文件及外层目录路由纳入缓存 key，导致只改变事件、effect 或文本也必须重新冷建缓存。v2 将图形候选的兼容比较与完整业务输入冻结分开，供公共验收准备使用；默认关闭、闭场来源、原始字节核验及产品验收规则保持。

## 版本与输入

`freeze_shader_cache_seed(origin_pin, new_output, key_version=2)` 从已实际闭场来源创建全新的 v2 seed。省略参数仍生成 v1；旧 seed、key、来源与原场次不改写。v1 继续使用完整业务 key 和原有两模组合同。

v2 按 `enabled_mods` 实际顺序比较任意非空模组集合。仅将验证后的外层 `path` 与 DLC `enabled_mods` 路由映射为有序位置；descriptor 其余字节、DLC 其余字节、四份配置及模组内 descriptor 都保留比较。图形、shader、GUI、其他 common、未知种类和嵌套路径全部保留。

仅以下三个 loader 目录的直接文件不进入图形兼容 key：

- `common/scripted_effects/*.txt`
- `events/*.txt`
- `localization/<language>/*.yml`

这是按脚本 effect、事件、文本的职责边界生成派生候选，未逆向证明所有引擎编译依赖。每个排出文件仍核对完整业务 bytes/SHA，并在独立 projection audit 记录其原始 pin、完整业务 inventory digest 和有序路由。源和目标的完整业务 digest 可以不同，图形投影必须相同；目标篡改、图形/config/未知内容变化、来源未闭场或 helper 与共享 source index 不同仍拒绝。公共输入快照继续冻结全部业务文件，投影不授业务豁免。

## 实证与边界

对现有 DX11 样本的五文件 / 20,823 B 有界读取确认：`.bin` 是 DXBC 容器，`.scache` 包含 `gfx/FX` shader 路径、effect 与编译宏。文件名 key 的构造、引擎对当前源的校验以及实际 hit/miss 仍 **UNKNOWN**。v2 的 key 是项目输入投影，不是引擎内部 key；不以 cache 被复制、mtime、文件数或启动成功证明命中，也不添加新的引擎逆向硬门槛。

旧完整业务 key 曾拒绝新的 holder/resolve overlay；v2 候选可以比较图形输入相同而业务不同的 profile。当前仍需从闭场来源新建 seed、冻结后继共享 helper、走公共 prepare/preflight 与实际诊断。此源码交付没有复制真实缓存、没有启动游戏或完成正式 I3b/C3/I4。

## 验证与期限

精确候选两文件的一次 portable suite **25 项通过**，包括原 17 项和新增 8 项；覆盖三类排出但业务篡改拒绝、图形/GUI/未知/其他 common 保留、有序路由、配置/descriptor/DLC 变化、v1 旧规则及新 v2 seed→公共 prepare→复验路径。synthetic 来源原 RED 保持。主树采用的 bytes/SHA 与已测试候选相同，未重复运行相同 suite；现有 Official CI 已包含该测试文件。[实际源码回执](acceptance/2026-10-10-graphics-cache-footprint-v2/VALIDATION.actual.json)。

缓存复制、profile 与 source export 分别计入当次峰值预算；新快照继承实际来源的原到期，不能借 v2、复制或使用续龄。当前缓存仍到 Oct17 复核，原本机配额例外仍 Oct12 到期。[统一存储策略](../storage-retention-policy.md)适用于全部执行机器。

## 16:55 本机实际生产与公共准备

源码 `5ecbb9aec` 已普通推送。新 Source09 实际 freeze exit 0，单父 Source08，commit `0239d7a14b42c24f47762985dcb9124fd9ff060a`；archive tag `archive/ck3-common-runtime/source09-20261010-008` 已普通推送。`C:/csr9` 仅替换 helper/test 两路径，7,904 项独立复制并继承原 SHA，未全树重 hash、重打 ZIP、建 hardlink 或重编 native。host、DLL、injector与旧 MCP 注册源码保持。

08:49:22 UTC 新 v2 seed 实际生成成功：3,687 文件 / 143,124,020 B，key `afe16a01871eb4908178c0c3c19180959a04cc31d95d0f7bdc9b7281dc8095ba`。实际闭场来源与 holder profile 的图形投影相同，完整业务 digest 不同；原始业务及缓存内容仍逐字节核验。旧 seed/key 未改，原 Oct17 03:03:44 UTC 到期继承。

新 holder case `lyd-holder-stage-20261010-002` 的公共 prepare、bound plan、无现场 context 的 preflight 均实际 exit 0、blockers 为空。首次 prepare 因 ROOT 错写 registry 路径，在建 profile 前退出 2；保留原回执，仅纠正为已有 `tools/ck3_mod_acceptance_products.json` 后执行成功。尚未 allocate、取得新鲜离线亲审或启动游戏。[实际来源、缓存与准备回执](acceptance/2026-10-10-graphics-cache-footprint-v2/PREPARE.actual.json)。

此次唯一 4 GiB 峰值于08:45 UTC重新登记，保守当前占用121,559,165,119 B，空闲624,803,192,832 B；配额例外 Oct12 原到期不续。新峰值尚未闭账，供本次串行 Source09/cache/profile/单场诊断，其他任务不得重复消费。首次和后继准备的 NOT_RUN 是各自记录时刻状态，不追认旧 R47 闭场。
