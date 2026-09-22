# 战争影片拍摄：失败后保留同一 MCP 现场

本次修正对应 `desktop-3fevhd2-1c74096080--vanilla--R0003`。该次实机在约 448 秒读回主菜单，`New Game` 验证到 bookmarks，随后 StartGame 的 post-ready pump 检查报错。原脚本在 Python 异常后关闭 driver 并设置 session stop，游戏随之退出，失去同局诊断机会。

R0003 仍是 RED。其原录像末尾前 8 秒仍显示“载入：100%”，没有可见 HUD；已发布 map-ready 语义快照不等于画面加载完成，也不证明整个 1066 身份后置通过。不能把本轮当作可用实机镜头或原生 AI 因果案例。

- 原资产：`D:/workspace/ck3_war_film_research_20260923/capture-live-live-r3/`。
- 原录像 SHA-256：`1c16fc235bfc2b22c6a17edafc8824596474db88f21bc40245ccaf2c3d2498ba`。
- 末尾帧及抽取 argv：`D:/workspace/ck3_war_film_research_20260923/capture-r3-postready-inspection/`。
- 原 attempt 已完整 `preserve` 到 `promo-runs/map-capture-live-r3` 并通过实际 xar-promo 0.2.1 validate；没有改变 RED 状态。

## 当前行为

[`capture_session.py`](../../promo/ck3_native_war_ai/integration/capture_session.py) 在初始流程失败后保存异常、driver 诊断、语义快照和桌面截图。只要 owning session 仍有效，保持**同一个 driver、官方 MCP Client 和游戏进程**，默认提供 1800 秒的 `recovery-requests/` 服务。成功加载后也提供 `interactive-requests/`，方便继续采样和保存检查点，避免每次独立 Python 操作都冷启动。

操作者在对应目录写入临时文件，写完后原子改名为新的 `.json` 文件。例如：

```json
{"action":"mcp","tool":"ck3_take_snapshot","arguments":{}}
```

每个请求只执行一次，原文件和对应 `*-responses/` 中的 SHA 绑定、结果、时间与 driver 诊断都保留。一个失败请求不终止后续诊断。结束请求为 `{"action":"finish"}`；到期或 owner 已停止也结束服务。该入口不自动重发 StartGame 或其他修改游戏状态的调用。操作者必须读取返回状态；请求完成不等于业务后置通过。

初始流程已经失败时，后续请求成功也不会把原 attempt 改写为 GREEN。新截图、录像或实验须另立证据并解释和失败现场的关系。此服务只延长已有会话，不绕过 native session 的唯一 owner、排他锁与清理规则。

`--shader-cache-source` 可显式复用同 build 旧 profile 的 `shadercache`。逐文件记录来源和目标 hash，只复制渲染缓存，仍生成新的纯原版设置、规则和空 mod 列表；不复制旧存档或其它用户设置。旧缓存不删除、不修改。

## 验证与边界

`test_capture_hot_service.py` 的两项离线测试通过：修改类调用失败后仍可在同 owner 查询快照且不自动重试；owner 停止后不执行请求。测试不启动 CK3、不证明真实 IPC 后置。本次新流程的实机验证放在后续独立 run，不能借旧录像声称通过。

启动前开始的 `raw-desktop.mkv` 是全流程诊断录像。它仍不能直接作为 adapter 要求的“进入 HUD 后开始”的正式实机包；后续在 HUD 和对应语义状态均确认后另开录像。
