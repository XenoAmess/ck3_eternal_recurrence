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

## Copy 再导入像素闭环

r12 在 r11 之后新增 7/7 的 Copy 回读文本再次 Apply，并把首次 CK3 UV 对齐截图作为哈希绑定
reference。第二阶段使用更严格的 MAE 0.01、MSE 0.001、edge 0.02、最坏空间块 0.03 门禁。
7/7 全部通过；最大实测值分别为 0.0000771、0.000000303、0.000345 和 0.000523。

因此 picture-02/05/07 的 fractional rotation 文本取整是 CK3 Copy 的原生规范化事实，但在当前
家徽表面实际输出中像素等价。原始输入到首次 Copy 的字段序列仍诚实报告为 4/7；r12 证明的是
规范化文本自身可稳定二次往返且重绘等价，不是把字段变化忽略掉。完整证据在
`docs/coat-of-arms-fit-artifacts/user-picture-corpus-v8-native-r12/`。

## v11 高分辨率候选原生复验

`user-picture-corpus-v11-native-r13` 在 commit `b3bd10b4` 上重新运行全部 7 例，未把 v8 的结果外推给
发生变化的 picture-02/05/07。9 点校准最大重投影误差为 0.334 px；网页 canonical → 首次 CK3
Apply 的 7 例全部通过既有 0.10 / 0.03 / 0.16 / 0.25 门禁。最坏实测值分别为 MAE 0.033104、
MSE 0.005396、edge 0.098117 和最坏空间块 0.108654。

原生 Copy 全文再次分块 Apply 的 7 例也全部通过严格像素门禁；最坏 MAE 为 0.0000793，最坏 MSE
为 0.000000311，最坏 edge 为 0.000379，最坏空间块为 0.000236。02/05/07 的首次 source → Copy
仍因 rotation 取整而只取得 4/7 严格字段序列通过；计数完整，Copy 文本自身的再次 round-trip 为
7/7。runner 按严格聚合合同返回 RED，这一状态与“两个像素一致性门禁 7/7 通过”同时保留，不能互相
替代。完整证据见
`docs/coat-of-arms-fit-artifacts/user-picture-corpus-v11-native-r13/`。

## v12 混合形状与同会话 A/B

`user-picture-corpus-v12-native-r14` 对 v12 全部 7 个用户案例重跑：网页 canonical → CK3 和 Copy
再次 Apply 都是 7/7 像素门禁通过；最坏首次 MAE/MSE/edge/空间块为
`0.041775 / 0.009702 / 0.139285 / 0.225221`。严格 source → Copy 字段序列仍因 02/05/07 的
rotation 取整为 4/7。

然而，未变代码案例在 r13/r14 间也表现出不可忽略的跨会话采样差异，所以这些绝对值不能证明 v12
形状替换优于 v11。r15 将 v11/v12 的 picture-05/07 放入同一 CK3 会话并加入重复样本：picture-05
的 v12 MAE 比 v11 高约 `0.000250`，而 v11 重复漂移约 `0.000003`；MSE/edge 同向退化。
picture-07 的差异则落在重复漂移量级。结论是 v12 绝对兼容，但没有通过原生相对收益门禁，不能晋级。
证据见 `user-picture-corpus-v11-v12-native-ab-r15/`。
