# 公共验收继承缓存与宗教头衔只读接线（2026-10-10）

公共 host 原先没有开放已实现的 actor cached-succession 与 religious-title 查询，无法让《礼与道》的事务对照通过公共入口消费现有 observer。现在唯一公共 manifest 可显式声明 `host_features.succession_title_readonly=true`；入口传递同一 host flag，父进程向原 MCP 子进程原样传递，driver 使用既有两个 default-off permission。产品及 case 不允许覆盖该 feature，也不选择另一份 host/source/native。

新增 MCP facade 只调用既有 service 方法，沿用 exact-build、暂停 actor/frame、前后 identity 和完整 DTO 校验；不改变继承资格、缓存、头衔、业务数值或正式产品文件。两项工具声明 readOnly、non-destructive；真实 MCP 参数模型拒绝 bool、字符串、零、溢出 revision 及额外字段。默认服务器 inventory 保持不变。

实际离线验证：公共选择器12项、真实 MCP 参数模型及委派4项、既有 actor-cache14项、既有宗教只读17项均通过。新增回归已接入 Official Runner CI；本地首次回归因测试读取 MCP 2 的旧属性名失败，改为读取 `model_dump(by_alias=True)` 后通过。上述结果只授源码接线，不授新公共运行时或产品实机资格。

用户已明确当前机器不存在 `C:/workspace/ck3-upgrade-20261008`，并要求不要依赖它。公共运行时正在从本机当前主线建立，旧外置目录仅保留历史引用；本机唯一 manifest 与实际构建结果另行登记。既有 R38 RED、修后事务对照未运行、I3b/C3/I4 未完成的事实保持。
