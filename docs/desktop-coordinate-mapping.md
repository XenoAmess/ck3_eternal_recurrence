# 桌面截图坐标换算合同

## 问题

桌面截图文件、聊天中的图片预览、远程查看器和桌面输入 API 可能分别使用不同尺寸。即使原图以原始质量读取，展示层也可能单独缩放、裁切或加留白。预览坐标不能直接作为桌面点击坐标，历史上观察到的固定倍率也不能外推到其他屏幕或图片。

## 强制流程

1. 用 `pyautogui.screenshot(...)` 保存点击前的原始桌面截图。
2. 读取截图文件的真实宽高；点击时重新读取 `pyautogui.size()`。两者不一致视为截图陈旧或来自其他桌面，拒绝点击。
3. 对当前一次预览显式记录实际图像内容矩形：`left`、`top`、`width`、`height`。不得把查看器窗口、留白或裁切区误算进图像内容矩形。
4. 在同一预览坐标系内记录目标点 `x`、`y`。
5. 运行 `tools/desktop_coordinate_map.py`。脚本先扣除内容矩形原点，再分别按宽度和高度映射 X/Y；它不假定屏幕或图片宽高比相同。
6. 真正点击必须加 `--click --receipt <path>`。回执图必须是点击后的当前桌面原尺寸截图。
7. 用回执图验证焦点或界面状态，再决定下一次动作。不同点击必须分别换算，不沿用前一次的裸桌面坐标。

## 命令

下面的数字仅演示参数形状，不是默认分辨率或默认倍率：

```powershell
& "tools\.venv\Scripts\python.exe" "tools\desktop_coordinate_map.py" `
  --source-image "D:\artifacts\before.png" `
  --preview-left 0 --preview-top 0 `
  --preview-width 1600 --preview-height 900 `
  --observed-x 800 --observed-y 450 `
  --click --receipt "D:\artifacts\after.png"
```

脚本输出 machine-readable JSON，包括预览内容矩形、观察点、源图尺寸、当前桌面尺寸和最终桌面点位。

## 拒绝条件

- 未提供当前预览的内容矩形；
- 把历史预览尺寸或倍率当作当前值；
- 目标点不在显式内容矩形内；
- 原始截图尺寸与当前桌面尺寸不一致；
- 无法判断预览是否裁切、旋转、加透视或非线性变形；
- 点击模式未提供回执路径；
- 点击后回执尺寸与点击时桌面尺寸不一致。

若预览存在无法精确定位的裁切或非线性变形，应回到原始 PNG 上用 PIL/OpenCV/OCR 定位，不能猜坐标。

## 键盘和语义控件

键盘输入前切换并验证目标窗口 `LANGID=0x0409`，确认前台窗口和控件焦点。
文本优先使用剪贴板，随后通过 UIA ValuePattern 读回；必要时用 `SetValue` 后再读回。
UIA 通过精确 HWND、Name、AutomationId 定位的语义动作不经过截图坐标，但必须验证业务结果。
2026-09-12 实测 React Select 的 `Invoke`/`Select` 可以返回成功却未选中；通过聚焦组合框、导航键选中后，必须读取显示的选中名称。

## 验证命令

```powershell
& "tools\.venv\Scripts\python.exe" "tools\test_desktop_coordinate_map.py"
```

测试覆盖 X/Y 独立换算、不同宽高比、带偏移的预览内容矩形和所有越界/非法尺寸拒绝分支。
