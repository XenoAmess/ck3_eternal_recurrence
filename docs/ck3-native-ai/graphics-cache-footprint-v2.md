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
