# 公共入口与 allocator/unrun 的同目录来源

2026-10-21；machine_id: `desktop-3fevhd2-1c74096080`。本页描述源码修复与纯 Python 检查，不授予新场游戏、Steam 离线或 R08 业务资格。

R227 的原始 frozen metadata 带 `launch_requires_fresh_owned_cas_and_offline_direct_review: true`，随后 C 入口实际拒绝 `Allocated background offline gate is missing`。这是旧门闸字段，不是 argv 中观察到的同名命令行参数。原进程没有记录 allocator 的 `__file__`；“晚导入可能选入冻结 D allocator”的归因来自原字段与 Python 导入路径机制，不能写成当时已经实测该模块来源。[原件引用与更正投影](evidence/episode04-public-control-peer-imports-20261021/CONTROL-IMPORT-CAUSE.actual-a02.json)

入口原来在 `native_dispatch` 分配分支中才导入 allocator；unrun 的三个控制调用也晚导入它。适配器曾改变搜索路径，且 Python 会复用 `sys.modules`，因此 C、D 同名模块共存时，入口路径本身不足以确定晚导入来源。场次 a05/a06 的临时入口先加载同 C allocator/unrun 并核 `__file__`；本次 canonical 修复把这条约束放回共享入口。

共享入口在 allocate 调用之前，要求 allocator 和 unrun 都来自自己的同一目录；unrun 的三个 allocator 控制调用复用这一规则。已有缓存若来自外目录就明确拒绝，不重载或替换该模块；临时搜索路径在成功或异常时均恢复。它只约束这两个控制 peer，完整运行依赖仍须由实际 frozen files 闭包逐项绑定。`ModuleType` 仅描述真实的模块导入边界。

实际定向检查用文件模块构造两个目录，在真实 `native_dispatch` 和 unrun release 路径边界运行。61b 原入口选中外目录的反例实际失败；修复后同目录选择、外目录 allocator 缓存、外目录 unrun 缓存、导入异常恢复及 unrun release 共 5 项通过。只有 Selection 构造和无害 allocator 回调使用夹具，未调用 SDK、任务总线分配器或游戏。新测试 strict 通过；补齐受改 `native_dispatch` 注解后，相同两生产文件的 strict 诊断从 134 到 129，新增 0，仍不表示旧生产源码整体 strict 通过。[最终源码冻结](evidence/episode04-public-control-peer-imports-20261021/CONTROL-PEER-SOURCE-FREEZE.actual-a02.json)

下一运行窗口应由新进程使用已冻结的同目录文件闭包。不得把此修复热换进活动场次，也不能凭源码修复追认 R227 已启动游戏或旧尝试已成功。
