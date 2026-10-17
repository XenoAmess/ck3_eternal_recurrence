# 2026-10-17：增量源覆盖保留旧 mtime 导致旧 OBJ 被复用

本次为 `machine_id: 4-8e1c2f1861` 的实际离线构建故障，不能外推为别的机器已出现。
观察区间为 `2026-10-17T08:07:32Z–08:12:52Z`；没有启动、注入 CK3 或录制。

本期 HolySite a02 候选源码已增加完整生产 command_result 包装。执行者用
`shutil.copy2` 将四个更新文件覆盖到同一 Ninja source tree，保留了候选较早的 mtime。
increment01 刚生成的 OBJ 时间比这些文件更晚。increment02 实际 build/fixture 虽返回 0，
原生输出仍是旧内层 DTO；生产 MCP 消费因缺少 `result` 键真实 RED。这不是新 wrapper
已经执行，也不能由 Python 再套一层 envelope 来冒充原生结果。

实际诊断在 `runtime/increment-03/timestamp-correction.json`：新 JSON serializer、fixture
和 religion mailbox 的源 SHA 与已冻结 a02 完全相同，但源 mtime 均早于对应现存 OBJ。
header 没有同名 OBJ，其变更通过真实头文件依赖触发消费者重编。该 JSON 位于外置
`C:/workspace/ck3-faith-and-power-20261017/episode01/`，记录完整原数值、来源及更新后时间。

纠正只刷新实际更换文件的 mtime，保持源码字节与 a02 SHA 不变，再调用同一
`tools/run_native_msvc.py`、同一 build、同一四个 target 与八个 job。
increment03 日志真实出现 16 个必要编译／链接步骤，包括 serializer、fixture、mailbox 和
bridge；没有全量冷建。精确项目 EXE 的实际管理员排除回执 verified 后，才运行新 fixture。
新 frontend fixture exit0；HolySite fixture exit0／14 checks，输出写入全新的
`runtime/increment-03/holy-site-12004-wire`。生产 Driver/MCP 消费及 live 资格另计。

后续向已存在的增量构建树投影不同字节时，不保留一个可能早于现有 OBJ 的源 mtime；
可使用 `copyfile`，或在逐文件 SHA 验明后对更换文件 `os.utime`。
同时保存前后源 pin、实际编译日志与新输出，不以 build ACK 或一个旧 fixture 的成功
替代新代码已进入产物。这个处理针对本次有实际后果的源覆盖方式，不要求扩为全仓审计。

原 increment01 的 frontend 测试 C2660、increment02 的旧 DTO 原件及 MCP RED 保持；
新结果不追改它们。baseline DLL/source、各次改变前的文件和每轮 input-freeze 也已分开保全，
按统一存储策略于 2026-10-24 复核当前基线用途。
