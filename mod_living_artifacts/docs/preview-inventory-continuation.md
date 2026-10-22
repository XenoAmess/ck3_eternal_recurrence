# 库存打开失败后的同进程喂养预览续行

此入口仅接续一个已知的、发生在装备和喂养 intent 之前的库存可见性失败。原 `run_case` 与 `resume_inventory_open_failure` 共用 `_preview_sequence` 和最终 `evaluate`；不新增第二套喂养动作或判定器。原公开结果保持 `BLOCKED`，独立续行报告只记录后来实际取得的证据。

当前操作卡针对 `machine_id: pc-20260924rtuf-f11af23c08`、R0013。原公开入口已记录 1 次 Save、5 次 tool 和 2 次 snapshot；Root 另一次只读库存纠正观测计为第 8 次调用。原 PID 7108 / generation 1、玩家 31254、物品 402、日期 raw 53144328 必须保持。原场次的 180 次调用和固定 7200 秒 hold 继续有效；每次动作仍执行原关闭预留守卫，不重新等待 readiness、不延长 deadline。

准备和调用必须由 Root 执行：

1. 从原 `native-report.json` 保全唯一 `root-r13-inventory-correction-readonly-a01` 完整行，另存不可变文件 `{"rows": [原行]}`。使用 Python 原始 JSON 整数域，禁止经 JavaScript Number 往返。入口将逐字段核对它与原 host 当前保留行相等，并校验全部 8 步已经结束、无额外动作、同进程/角色/日期及库存尚未装备且可见。
2. 在独立 Python 进程中先导入 **c16 原产品工具目录**及原共享 SDK，再按绝对文件路径加载主仓的维护版 `preview_acceptance_adapter.py`。其它依赖和配置继续取自 c16；入口逐一检查已加载依赖的真实 `__file__`、原部署闭包和 Pin。不要把维护文件复制覆盖 c16。
3. 复用原 `Selection` 的 runtime、products、context、prepared 路径及 opt-in。仅新建同一 live 下的一层输出目录，由 `CaseClient` 创建，不能事先创建。启动已有 Save/PNG 服务时将监听目录设为该目录；只接受 **4 次新 Save**。原 initial checkpoint 读回文件、Save 原件及原生记录都复用，不重发第一次 Save。
4. 以下是维护入口的函数组合；`selection` 必须是原分配的 `Selection`，不能重新 allocate、prepare 或启动游戏。Root 对 5 次原图审阅继续调用既有 `produce_preview_review`，提供真实捕获和审阅时间。

```python
import importlib.util
from pathlib import Path
import sys

# shared_source、original_tools 来自原 frozen-argv.json。
sys.path[:0] = [str(shared_source / "tools"), str(original_tools),
               str(shared_source / "ck3_autonomous_player/src")]
import preview_acceptance_adapter  # 先固定 c16 的所有原依赖
from acceptance_contract import pin
from ck3_mod_acceptance_client import CaseClient

spec = importlib.util.spec_from_file_location("preview_inventory_maintenance", overlay_path)
if spec is None or spec.loader is None:
    raise ValueError("Maintenance module is unavailable")
overlay = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = overlay
spec.loader.exec_module(overlay)

client = CaseClient(selection, output=live / "case-continuation-a01")
try:
    result = overlay.resume_inventory_open_failure(
        selection.adapter_context(client.output), client,
        predecessor_output=live / "case-output",
        corrected_item=pin(correction_rows_path),
        original_source_tools=original_tools,
    )
finally:
    client.close_handle()
```

入口从原记录恢复 `calls=8`、`sequence=5`、已保存观察数 1、快照序号 2，后继控制 ID 从 `xalw-core-0006`、`case-snapshot-0003` 开始，避免重放已消费 ID。先正常装备和进入管理，再审阅普通材料并取消，确认回到管理且原生库存未消费；随后依次审阅/确认四档材料，各做一次真实 Save。最终恰为 5 次 Save、5 次原图审阅、零自然日。材料消失与经验/自动升级仍由原 Save/原生消费者核对，Root 的审阅声明不代替业务结果。

输出为新目录的 `preview-evidence-journal.json` 和 `preview-inventory-continuation-result.json`，包括原失败、复用 initial checkpoint、纠正原生行、维护源的 Pin、继承调用数、原 hold 和独立判定。入口不改写原公开结果、不授全产品或发布通过。原 public run / CaseClient 仍是唯一正常关闭方；续行 client 只释放自身进程句柄，不写另一份 normal-close 响应。

离线回归运行真实原入口产生该故障，再经原 Root/Save 文件生产者和消费者接续四次 Save，最后重算完整 `evaluate`；另有跨日期纠正拒绝用例。测试只在 CK3/native/像素边界使用 authored 输入，不构成 R0013 实机通过。实际续行和正常关闭结果需由 Root 后续独立记录，旧失败及旧截图坐标保留。
