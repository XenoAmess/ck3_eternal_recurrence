# 圣物窗口 owner 角色修复：有限 MCP 资格

machine_id: `4-8e1c2f1861`。实际观察时间、逐包 SHA 和源码冻结见 [qualification.json](qualification.json)。

本次原生 focused fixture 为 reader 18 项检查 / 6 包、typed action 10 项检查 / 7 包。实际 Python Driver → Service → MCP SDK 消费全部 13 包，无跳过。最终 b03 / bui03 改正夹具构造后的包，与实际消费的 a01 输入逐字节一致；保留双方 SHA 和重新读取的等值证明，未重复旧矩阵。

规划器须保留组件的 unknown。foreign / null owner 可以只使窗口权限不可读，独立物品所有权仍可读；owner 漂移可使根结果不可用，不能把局部旧值提升为行动依据。typed dispatch 后 owner 漂移仍表示已经调用、后验未知；第二次相同意图在原生 I/O 前被持久 pending 拒绝，只产生一次原生请求。ACK 或选择状态不能作为供奉成功的证明。

`window+0x98` 是外层 jomini owner；`owner+0x10` 是 Gfx。此次资格仅证明修正后的原生 fixture → Python 公共链，未执行游戏 getter / callback，未取得新的实机业务资格。完整 DLL 未链接；typed 整包使用精确生产函数体的独立 TU。

合回后可用已具备 MCP SDK 的 Python 执行以下消费器，reader 和 typed manifest 可分别提供。manifest 必须来自新运行的对应原生 focused producer，保留可读原包和原请求；不能手工构造正例。`STATE` 和 `OUTPUT` 必须为新路径。

```text
python -B -X utf8 ck3_autonomous_player/native_bridge/research/consume_holy_site_relic_binding_focused_packets.py --base-source-root REPO --reader-manifest READER_MANIFEST --typed-manifest TYPED_MANIFEST --state-root STATE --output OUTPUT
```

消费器复用已入库的 `test_holy_site_relic_actions_12004_native_mcp.py` 建立真实 Driver 的辅助方法，不执行其历史测试矩阵。外置候选验收另传 `--source-overlay-root` 和 `--combined-hook-manifest`，先装入 SHA 冻结公共 hooks，再导入 base bridge。合回后的无 overlay 导入模式没有另行执行 SDK；本回执绑定实际执行的候选导入模式。原始 SDK 回执与临时 state 留在外置工作包，按统一存储策略限期保护复核，不作为永久入库资产。
