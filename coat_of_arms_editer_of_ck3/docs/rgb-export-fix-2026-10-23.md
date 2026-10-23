# RGB 小数导出故障：修复与实机验收

2026-10-23。修复、自动回归和 CK3 官方 UI 业务回归已通过；正式发布状态以对应 master 提交的 Pages workflow 为准。

## 根因

联合颜色细化器 `fitJointRefinement.ts` 的内部颜色是 0–1 归一化值，旧 `rgbExpression()` 却直接把它写成 CK3 的 `rgb { ... }`。网页渲染器同时接受这种归一化 RGB，校验也没有拦截，因此预览正常、粘贴进游戏失败。

反馈中的三个小数可由原始 `197 / 255` 和红通道 `+0.03` 步长精确复现：

```text
错误：rgb { 0.802549 0.772549 0.772549 }
正确：rgb { 205 197 197 }
```

这不是图章、层数或 position/scale 小数导致的语法错误。CK3 的 **RGB 颜色分量**要求 0–255 整数；其他数值字段继续保留原有语义。用户没有提供完整海贼旗源码，本次不声称验证了该完整作品。

## 修复

- 在生成颜色候选时执行 `round(clamp(channel, 0, 1) * 255)`，先量化再渲染和评分，确保评分对应最终导出的颜色，不在导出最后一刻改变已评分结果。
- RGB 校验拒绝小数、指数表示和越界分量；非法原文保留并明确报错，禁止复制，不擅自猜测用户原意。HSV 浮点语义不改。
- 渲染器统一按字节 RGB 解释，包括 `rgb { 1 0 0 }`，不再按数值大小猜测是否归一化。
- 新增生产者→序列化→解析→渲染回归、非法输入与中英文诊断、网页复制门禁，并将浏览器回归加入正式 Pages 门禁。

## 自动验证

本次机器 `machine_id: desktop-3fevhd2-1c74096080`；2026-10-23 UTC 观察，证据根目录 `C:/coa-rgb-20261023/`。

- 修改前定向测试真实失败：预期整数 `205 197 197`，实际为反馈中的三个小数；外置 `baseline-regression.txt` 保留。
- 修改后 Vitest：27 文件通过、1 文件跳过；124 测试通过、1 测试跳过（11:05 UTC 读回）。
- production build / `vue-tsc -b`、纯前端边界检查、构建后 1630 个静态 DDS 文件逐项校验通过。
- 新增生产预览 Playwright 回归通过：非法 RGB 禁止复制、修正后可复制，中英文诊断正确。
- 真实授权 DDS 与生产细化器的 19 次计算接受了整数颜色调整，样例损失 `8.027777777777779 → 0`，图章实例数仍为 1。这是确定性故障回归，**不是整体拟合质量提升百分比**。

## CK3 实机验证

仅以下机器、版本与场次有效，不能外推其他机器的安装、离线或业务资格。

- `machine_id: desktop-3fevhd2-1c74096080`
- 场次：`desktop-3fevhd2-1c74096080--vanilla--R0244`；独立中文 profile，无启用 mod。
- 实际 EXE：`C:/SteamLibrary/steamapps/common/Crusader Kings III/binaries/ck3.exe`；CK3 `1.20.0.4`，Steam build `25734779`。
- EXE SHA-256：`98702f88a547cde2eaf29a85f93b85f68ee4cf8148336a4f7afaeb75319dd518`。
- 原修复提交 `14a1c054fbd58d09f8a0b294b62e13b6890537db` 在干净冻结 checkout 验收；之后仅 rebase 到新 master（编辑器代码无上游差异）并追加本报告。
- 观察：2026-10-23 `10:57:17–11:00:36Z`；Steam 离线模式在启动前取得新鲜像素证明，退出后 `11:03:22Z` 再次实际审阅，未切换在线。

测试使用单个 `ce_block_02.dds` 图章，复用反馈颜色和 depth619，scale0.7 以便观察。操作使用官方家徽编辑器的 Paste/Copy 和受守卫的坐标换算，无 OCR。

| 操作 | 实际结果 |
| --- | --- |
| 粘贴原小数 RGB | Paste 禁用，游戏提示“你的剪贴板没有纹章设计”；复制前后原家徽逐字节相等。 |
| 粘贴生产生成的整数 RGB | 盾牌预览立即变为目标家徽。 |
| 从游戏 Copy 读回 | `color1=rgb { 205 197 197 }`，纹理、scale0.7、depth619 保留；按生产解析器核对全部根颜色、图章和实例语义相同。 |
| 原生 Copy 再 Paste 再 Copy | 两次原生输出逐字节相等。 |
| 点击 CoA“结束” | 返回角色设计器，王朝盾牌仍显示新家徽。 |

精简原始证据位于 [rgb-export-2026-10-23/](rgb-export-2026-10-23/)：

- [旧小数输入](rgb-export-2026-10-23/reported-fractional.txt)、[生产生成的修复输入](rgb-export-2026-10-23/fixed-generated.txt)、[游戏原生 Copy](rgb-export-2026-10-23/fixed-native-copy.txt)。
- [拒绝小数的实际界面](rgb-export-2026-10-23/fractional-rejected.png)、[接受整数的实际界面](rgb-export-2026-10-23/fixed-accepted.png)。
- [生产复现回执](rgb-export-2026-10-23/production-repro.json)、[业务回读回执及文件 SHA](rgb-export-2026-10-23/native-business-acceptance.json)、[精确进程退出观测](rgb-export-2026-10-23/process-exit-readonly.actual.json)。这些回执中的绝对路径指外置原件，不意味着其他机器存在同一路径。

范围止于角色设计器 Paste/Copy/Finish；未进入战役，不声称跨存档验收。本次没有添加新游戏素材，线上 DDS pack 仍是已授权的 `1.19.0.6` pack，不因实机版本扩大素材授权。

## 基础设施异常与闭场

旧 MCP CoA hook 仅绑定 1.19，未对 1.20 调用。现成 route runner 要求的五项旧导航 capability 在当前冻结 1.20 DLL 中不存在，故只轮询 capability 缓存并超时：**MCP 导航基础设施 RED；官方 UI 业务 PASS**，不能互相替代。原始报告的 `mcp_only` 描述仅属于未执行导航的旧 runner，不描述本次官方 UI 操作。

游戏由“退出到桌面”正常关闭。PID31884 的原生创建 FILETIME `134372256090884288`（规范十进制字符串）绑定本次启动；只读查询和既有 managed cleanup 均实读退出码0。退出后镜像查询 error31 原样保留，不能用该字段声称镜像已重新读回。

11:10:11Z managed cleanup 证明 `tree_gone=true`、`cleanup_proven=true`、watchdog absent、共享锁已释放，无残余 CK3。keeper 正常停止、无 failure；11:18:49Z 使用最终 sequence8424 做 CAS 屏幕释放（事件8426）。监督包装器在 cleanup 后因原 runner 已写同名报告而报 FileExistsError、进程退出1；原件未覆盖，这项收尾异常不计为产品业务失败或 MCP 成功。后续未重启或强杀游戏。

外置完整执行材料按通用存储策略有限保留：build14天、raw evidence30天、record180天，到期复核而非自动续存；本次未删除用户文件。仓库仅保存小型输入/回读、关键截图及回执，不保存重复游戏载荷、完整原生轮询导出或 dist。
