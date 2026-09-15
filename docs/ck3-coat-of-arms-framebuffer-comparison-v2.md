# CK3 家徽 framebuffer 对照 MCP v2

## 为什么需要 v2

首轮 7 图原生运行证明 v1 存在循环依赖：定位器使用待验证的网页图片，在完整 CK3 framebuffer
中逐案例搜索“最像”的区域，并继续优化 0.82–1.0 的局部缩放。视觉复核可直接看到一些输出混入
角色设计器的棕色圆框；相同页面上的不同案例还会得到不同 crop 比例。由这种裁剪算出的色差同时
混合了 UI 装饰、错误缩放和真实 renderer 差异，不能用来判定浏览器预览是否忠于 CK3。

v2 改成 reference-independent 两阶段校准：

1. 调用方通过既有原生 Apply MCP 应用纯红 `pattern_solid.dds`，调用
   `ck3_calibrate_frontend_coat_of_arms_framebuffer_v2(calibration_id, "begin")`。
2. 调用方应用纯绿的同一 pattern，再以 `phase="complete"` 捕获第二帧。
3. MCP 对两张完整客户区 framebuffer 做固定阈值差分、形态学去噪和连通域分析，选择面积最大的
   CoA 尺寸动态表面；输出矩形、mask、两帧像素哈希和 mask 哈希。
4. 后续 `ck3_compare_frontend_coat_of_arms_framebuffer_v2` 只能使用该固定矩形与 mask。reference
   只参与该矩形内的像素评分，绝不参与位置、尺度或候选选择。

这样既不依赖 OCR、鼠标坐标链或截图猜控件，也不会按案例寻找有利裁剪。校准和比较都绑定同一
原生 bridge PID、连接代次、`coat_of_arms_designer` 路由和可见页面根；窗口改变、路由漂移、ID
复用、尺寸变化或差分不足均 fail closed。校准 store 最多保留 4 个会话，ID 最长 64 个 ASCII
字符，避免无界状态增长。

## 当前合同

- 校准差分阈值：任一 sRGB8 通道绝对差 `>= 48`。
- 去噪：3×3 opening；选定连通域后 5×5 closing。
- 候选下界：宽、高至少 32 px，面积至少 512 px，宽高比 0.55–1.8，填充率至少 0.12。
- 选择顺序：面积降序、包围盒面积降序、X/Y 稳定序。
- 比较区域：校准 mask 映射到 reference 尺寸后向内腐蚀 reference 宽度的 2%，并与 reference
  alpha 相交。
- 可视证据：`cropPngBase64` 保留原始校准包围盒；runner 默认落盘的
  `alignedContentPngBase64` 使用未腐蚀校准 mask 作为 alpha，因此不会把 mask 外的棕色 UI
  装饰误呈现为家徽内容。
- 像素指标继续使用 `masked-srgb8-mae-mse-gradient-l1-spatial-8x8-v1`；定位损失和
  `distinctMargin` 不再适用。

两张纯色状态必须由调用方保存 Apply receipt；校准工具本身只读 framebuffer，不能证明调用方
确实应用了指定颜色。7 图 runner 已把红/绿 Apply、两次前台准备、begin/complete、固定校准和
逐例比较串成同一官方 MCP 会话。

## 状态与证据边界

截至 2026-09-16，v2 的合成夹具、service 绑定和官方 MCP 闭合 schema 已通过 26 项相关测试；
真实 CK3 v2 corpus 仍待下一轮共享槽位运行。在该 live run 完成前：

- `r4` 的 7/7 Apply/Copy 和小数 rotation 被原生 Copy 整数化是有效原生证据；
- `r4` 的像素门禁与 crop 仅为 v1 失效诊断，不是产品 renderer 的失败清单；
- 不得把 v2 static-ready 写成网页/CK3 像素一致性已经通过。

复现静态合同：

```bat
set PYTHONPATH=ck3_autonomous_player\src&& tools\.venv\Scripts\python.exe -m pytest ck3_autonomous_player\tests\unit\test_coat_of_arms_framebuffer.py ck3_autonomous_player\tests\unit\test_coat_of_arms_framebuffer_service.py ck3_autonomous_player\tests\unit\test_frontend_gui_route_v1_bridge.py -q
```
