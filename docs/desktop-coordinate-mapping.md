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

```text
"tools\.venv\Scripts\python.exe" "tools\desktop_coordinate_map.py" --source-image "D:\artifacts\before.png" --preview-left 0 --preview-top 0 --preview-width 1600 --preview-height 900 --observed-x 800 --observed-y 450 --click --receipt "D:\artifacts\after.png"
```

脚本输出 machine-readable JSON，包括预览内容矩形、观察点、源图尺寸、当前桌面尺寸和最终桌面点位。

右键点击使用 `--click --button right --receipt <path>`；`--button` 默认为 `left`，`right` 只允许用于点击。右键仍须提供本轮原始截图、实际预览内容矩形和点击后回执，并遵守相同的尺寸与越界拒绝条件。

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

```text
"tools\.venv\Scripts\python.exe" "tools\test_desktop_coordinate_map.py"
```

测试覆盖 X/Y 独立换算、不同宽高比、带偏移的预览内容矩形和所有越界/非法尺寸拒绝分支。

## 只移动指针 / hover

`--move` 只把指针立即移到换算后的点，不点击、不按按钮、不拖动、不切换窗口。
仍须使用本轮原始 PNG、当前实际桌面尺寸和显式预览内容矩形；不得复用历史分辨率或倍率。
另外必须提供同一预览坐标系内已直接审阅的安全区域
`--reviewed-left/top/width/height`。区域须完全位于图像内容矩形内，观察点与舍入后的实际桌面点
都须落在该区域内，否则拒绝输入。由执行者根据本轮实际原图确认区域，工具不推断画面已经审阅。

以下数字只演示接口形状，不能直接用于实际桌面：

```text
"tools\.venv\Scripts\python.exe" "tools\desktop_coordinate_map.py" --source-image "D:\artifacts\before.png" --preview-left 100 --preview-top 50 --preview-width 800 --preview-height 600 --observed-x 500 --observed-y 350 --reviewed-left 300 --reviewed-top 200 --reviewed-width 400 --reviewed-height 300 --move --receipt "D:\artifacts\after-move.png"
```

移动前重新读取桌面尺寸、指针与前台窗口/控件焦点；移动后保存实际指针、当前桌面尺寸、前台窗口/焦点、
原尺寸 PNG 和 `after-move.png.json`。JSON 绑定原图与回执图 SHA-256、原始坐标和 X/Y 换算结果。
可加 `--expected-foreground-hwnd <本轮实际HWND>`，前台不匹配时拒绝移动。指针未到达目标、
屏幕或回执尺寸改变、前台窗口/焦点改变时保留失败回执并返回非零，不能凭输入 ACK 称移动已验。
移动前读取五种鼠标按钮状态；任一仍按下时拒绝位移，避免把 pointer-only 动作变成拖动；回执也记录移动后按钮状态。
已有 PNG 或 JSON 回执拒绝覆盖；重新尝试须用新路径。

在相同命令加 `--dry-run` 可只验证尺寸、几何与区域，输出计划 JSON；不发指针输入、不读焦点、
不生成截图或回执。dry-run 仍读取当前 `pyautogui.size()` 作实际尺寸核对；它不证明实际移动完成。
`--move` 与 `--click` 互斥，原有点击与回执流程保持原样。
