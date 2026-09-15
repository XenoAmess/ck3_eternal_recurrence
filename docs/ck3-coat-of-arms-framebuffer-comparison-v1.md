# CK3 家徽 framebuffer 对照 MCP v1

> 2026-09-16 状态：v1 的真实 CK3 运行暴露了 reference-driven 定位偏差。它会用待验证图片选择
> 每个案例自己的位置和缩放，部分 crop 实际包含角色设计器的棕色装饰框。因此 v1 只保留为历史
> 诊断合同，不能再作为网页/CK3 像素一致性结论。替代合同见
> [CK3 家徽 framebuffer 对照 MCP v2](ck3-coat-of-arms-framebuffer-comparison-v2.md)。

## 用途与边界

`ck3_compare_frontend_coat_of_arms_framebuffer_v1` 是开发验收工具，用来回答“网页 canonical
预览与 CK3 当前实际显示是否相差过大”。配套的
`ck3_prepare_frontend_coat_of_arms_framebuffer_v1` 会先把精确 PID/HWND 绑定的 CK3 客户区切到
前台。两者都不进入 GitHub Pages 或编辑器生产运行链路。

工具接收一张 32–512 px 的正方形 PNG、PNG 的 SHA-256，并执行以下只读流程：

1. 验证 base64、格式、尺寸、512 KiB 载荷上限和完整哈希；在解码像素前先拒绝超尺寸图像。
2. 通过原生语义 MCP 确认当前路由为 `coat_of_arms_designer`，且
   `coat_of_arms_page` 可见。
3. 显式 preparation 工具用 Win32 窗口 API 请求前台并验证结果；它不合成键盘/鼠标输入、不改
   游戏数据。随后把窗口绑定到 native bridge 报告的精确 CK3 PID 和连接代次；compare 只接受
   前台、未最小化、无遮挡、`2560×1440` 的完整客户区。
4. 在完整 framebuffer 上按多个尺度全局搜索盾形区域，不使用固定屏幕坐标。定位同时比较盾形
   mask 内的 sRGB8 色差和梯度；记录最佳位置、各尺度候选、与空间上另一个独立候选的差距。
5. 返回原生 crop、crop SHA-256、framebuffer RGB 像素 SHA-256、mask 内 MAE/MSE/边缘损失及
   8×8 空间误差矩阵。
6. 捕获后再次检查路由、页面根、PID 和连接代次；任一状态变化即 fail closed。

两项工具均不做 OCR、不发送键盘或鼠标输入，也不上传 framebuffer。preparation 会改变窗口前台
状态，因此明确标为 presentation-only，不能被称为只读桌面操作；compare 本身保持只读。返回的
原生 crop 只写入本地 append-only 验收 artifact。网页正式版本仍只在浏览器内处理用户图片。

## v1 比较合同

- 定位：`full-client-global-shield-mask-color72-edge28-v1`
- 像素指标：`masked-srgb8-mae-mse-gradient-l1-spatial-8x8-v1`
- 搜索边长：128、160、192、224、230、256、288、320、384、448、512 px
- 几何 mask：与网页盾形 clip-path 相同的七点多边形，再与 PNG alpha 相交
- 原生观察统一缩放到 reference 尺寸，使用 bilinear；指标只统计 mask 内像素

不同 renderer、mask、缩放、色彩空间或指标版本之间的数字不得直接宣称不劣化。crop 可以证明
空间差异；单独的全帧均值或哈希只能证明身份，不能证明两幅图一致。

## 7 图首次原生验收的预冻结门禁

以下阈值在第一次查看 CK3 结果前冻结，不根据结果事后放宽。每张图须分别报告，不以平均值掩盖
失败用例：

| 门禁 | 通过条件 |
|---|---:|
| 原生语义状态 | 路由、页面根、PID、连接代次前后完全稳定 |
| 定位损失 | `locatorLoss <= 0.45` |
| 独立空间候选间隔 | `distinctMargin >= 0.005` |
| mask 内平均绝对误差 | `meanAbsoluteError <= 0.18` |
| mask 内颜色 MSE | `colorMse <= 0.06` |
| mask 内边缘损失 | `edgeLoss <= 0.18` |
| 8×8 最坏有效格 MAE | `<= 0.35` |

阈值通过表示“在 v1 合同下未发现过大的网页/CK3 空间像素偏差”，不表示像素完全一致，也不表示
拟合结果忠实于用户原图。原图→拟合质量仍使用独立的拟合评分合同。定位门禁失败时，本轮像素值
只作诊断数据，不可据此声明网页/原生一致或不一致。

## 当前证据

2026-09-16 的浏览器外单元夹具证明：工具能在任意插入位置全局定位合成盾形图，不依赖固定
坐标；hash、载荷、尺寸、路由漂移和 bridge 绑定均会 fail closed。随后 7 图 live run `r4` 完成
7/7 Apply、Copy 与 crop，但视觉复核发现 `picture-02/04/05/06` 等 crop 包含装饰框，且
`contentToOuterRatio` 会按待验证 reference 在 0.82–1.0 间变化。该证据仍可支持传输、原生 Apply/Copy
与“v1 定位器不适合作为验收口径”，不能支持网页与 CK3 的像素差异大小。

复现命令：

```bat
cd ck3_autonomous_player
set PYTHONPATH=src&& ..\tools\.venv\Scripts\python.exe -m pytest tests\unit\test_coat_of_arms_framebuffer.py tests\unit\test_coat_of_arms_framebuffer_service.py tests\unit\test_frontend_gui_route_v1_bridge.py -q
```
