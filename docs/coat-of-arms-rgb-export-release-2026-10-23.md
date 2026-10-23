# 家徽编辑器 RGB 导出修复：正式发布回执

- 日期：2026-10-23；回读机器 `machine_id: desktop-3fevhd2-1c74096080`。
- 公开站点：[CK3 家徽编辑器](https://xenoamess.github.io/ck3_eternal_recurrence/coat_of_arms_editer_of_ck3/)。
- 部署提交：`a9cdef91833294eb94aab70ce270ca61d7f488eb`；产品代码修复提交为 `417bd1b6d`（实机冻结原提交 `14a1c054f` 的无冲突 rebase）。
- [正式 Pages workflow 39946754790](https://github.com/XenoAmess/ck3_eternal_recurrence/actions/runs/39946754790)：build、deploy 均实际 `success`；未绕过任何测试门禁，未手工提交 dist 或部署分支。
- 2026-10-23 `12:43:01.978Z` 使用独立、禁用 Service Worker 的无头 Edge 浏览器实际读取公开 URL，HTTP200，页面版本为 `2026-10-23T12:33:02.715Z · a9cdef91`。
- 同一公开页面输入反馈的小数 RGB 时，出现整数范围诊断且复制按钮禁用；改为 `rgb { 205 197 197 }` 后可复制，所得 RGB 三分量均为0–255整数字符串，页面脚本错误0。此项读取隔离浏览器 clipboard callback，并非 OS 剪贴板；游戏原生 OS Copy 验收另见下述实机报告。
- 精简机器可读原始回执：[public-readback.json](coat-of-arms-rgb-export-2026-10-23-public-readback.json)。截图原件 `C:/coa-rgb-20261023/public-release.png`，SHA256 `c4648a7211f1e83e6940bcb78da72274e5b41f344f66093846a7f14b643f5a56`，按 raw evidence30天到期复核，不无限续存。

根因、生产回归、CK3 `1.20.0.4` 实机 Paste/Copy/Finish、正常退出与旧 MCP 基础设施 RED 边界见[子项目修复与实机报告](../coat_of_arms_editer_of_ck3/docs/rgb-export-fix-2026-10-23.md)。正式站点仍为纯前端，不依赖 CK3、MCP 或 Java；授权 DDS pack 未改变。

玩家处理：刷新页面确认版本 `a9cdef91` 或更新版本后重新生成。修复不会追改已经保存或复制出去的旧错误代码；不要把归一化小数直接取整为0/1。

本记录仅追加发布与回读事实，不覆盖旧失败/超时回执。最终本机容量闭场回执由任务结束时外置生成在 `C:/coa-rgb-20261023/CAPACITY-CLOSED-r*.actual.json`，不以本段提前证明已释放预留。
