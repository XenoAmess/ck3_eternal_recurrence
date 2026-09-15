# CK3 家徽 framebuffer 对照 MCP v3

## v2 为什么不足

v2 已经去除了“用待验证网页图搜索最像区域”的循环依赖，但只从红/绿两帧取得一个动态表面矩形和
不规则 mask。CK3 角色设计器会随会话把同一家徽呈现在圆框、盾框等不同原生框体中；把这个包围盒
直接缩放成 canonical 正方形会混入框体几何，导致同一正确内容在不同会话得到不可比的误差。

v3 保留红/绿定位，另加入原生 UV 标定：

1. Apply 纯黑 `pattern_solid.dds` 并捕获 anchor base。
2. Apply 9 个白色 `ce_block_02.dds`，canonical 位置固定为
   `(0.3/0.5/0.7, 0.3/0.5/0.7)` 的笛卡尔积。
3. 对 complete 与 base 做差，结构化识别 9 个连通域中心，并拟合 canonical UV 到 framebuffer 的
   2×3 仿射矩阵。
4. 后续比较把 framebuffer 反采样回 canonical 230×230 空间，只在由标定得到的原生内容 mask 与
   reference alpha 交集内评分。网页 reference 不参与定位、尺度或仿射求解。

所有阶段绑定同一 bridge PID、连接代次、页面 route 和 calibration id；缺标记、标记数量错误、最大
重投影误差超过 2.5 px、窗口/路由变化或前台身份不符均 fail closed。捕获仍是只读 framebuffer；
Apply 由既有分块原生 MCP 完成。合同明确 `usesOcr=false`、`usesKeyboard=false`、`usesMouse=false`、
`fixedScreenCoordinatesUsed=false`。

## 前台准备的结构化修复

r9 暴露 `SetForegroundWindow` 在 Windows 前台限制下会直接抛错；r10 又证明只把当前线程附着到
既有前台线程不足以稳定激活 CK3。当前实现同时附着当前线程到既有前台线程和目标 CK3 窗口线程，
在附着期调用 Show/BringToTop/Activate/SetForeground，随后解附着并按 exact root HWND 复核。
framebuffer 捕获入口还会在“准备完成到实际捕获”之间焦点变化时原子地重新准备，避免 TOCTOU。
直接激活错误与附着激活错误分别进入收据，不会被 ACK 掩盖。

## 7 图 live 结果

`user-picture-corpus-v8-native-r11` 在 commit `e4a3caa7` 上完成：一次校准服务 7 个案例，9 点最大
重投影误差 0 px；7/7 均完成 Apply、Copy 与 UV 对齐截图，7/7 通过预先冻结的 MAE/MSE/edge/空间
门禁。最高 MAE 为 picture-04 的 0.043774（阈值 0.10），最高 edge 为 picture-04 的 0.132857
（阈值 0.16），最高局部块误差为 picture-05 的 0.140578（阈值 0.25）。

严格文本 round-trip 仍是 4/7：picture-02/05/07 的 CK3 Copy 把小数 rotation 规范化为整数；核心
实例/块/层计数不丢失，且当前 Apply 后三例像素门禁均通过。原生像素结论与 Copy 再导入结论必须分开，
不能据此声明 fractional rotation 已完整往返。

完整证据见
`docs/coat-of-arms-fit-artifacts/user-picture-corpus-v8-native-r11/`。v1/v2 文档和 r5-r10 收据继续作为
定位历史保留，不原地覆盖。
