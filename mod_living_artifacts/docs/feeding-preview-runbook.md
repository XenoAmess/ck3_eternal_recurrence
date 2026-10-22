# 喂养预览实机操作说明

2026-10-22。`feeding_preview` 已接入[公共产品入口](../../tools/ck3_mod_acceptance_products.json)，本文是下一独立场次的操作说明，**不是实机通过记录**。规范来自[当前 adapter](../tools/preview_acceptance_adapter.py)与[固定合同](../tools/feeding_preview.contract.json)。此前 R8 的预览显示0、实际仍到账，以及镇压 tooltip 缺序号错误，见[R8记录](runtime-r8-continuous-growth-and-feeding.md)；不能用离线修复直接追认界面通过。

## 场次与自动流程

按[公共执行合同](acceptance-execution-contract.md)准备并选择 `product=living-artifacts`、`case=feeding_preview`。当场绑定实际机器、run、运行时 manifest、冻结产品源码、正式 staging 与初始 fixture。不要改正在运行的 NPC 场次或借用它的通过事实；同机 CK3 继续排他。普通开发和测试保持 Steam 离线，实际启动前使用当场新鲜的后台离线回执。

该 case 固定 **0个自然日、最多180次公共调用、5次实际 Save、5次 Root 原图审阅**；注册预算为 `hold_seconds=2700`、`timeout=4500`、`readiness_timeout=1200`，正常退出保留180秒。沿用已有 core 初始输入：1066.9.15，目标未装备、1级/92经验、`pending=0`、`growth_sequence=0`，食性为盔甲，四件材料均为剑，因此本场没有食性加成。物品和人物 ID 从本场实际读回取得，不能填写旧场次 ID。

adapter 使用共享 Session 自动完成：初始 Save/严格 melt 读回 → 原生装备 → 普通管理决议 → `xalw.12` → `xalw.10` → `xalw.11`。Root 审阅期间只取得并直视当前原始 PNG，然后写审阅回执；**不要替 adapter 点击喂养、取消或确认**。

| Root 请求序号 | 当前确认页 | 目视基础经验／本次经验期望 | 回执后由 adapter 执行 | 随后的实际 Save 期望 |
| --- | --- | --- | --- | --- |
| 01 | 普通材料，第一次进入 | 80／80 | 取消，回管理；原生读回整份库存未变，普通原件仍在 | 不另存一次；初始 Save 为1级/92、序号0 |
| 02 | 重新选择普通材料，新的事件实例 | 80／80 | 确认消费 | checkpoint02：2级/72、序号1 |
| 03 | 大师材料（`masterwork`） | 200／200 | 确认消费 | checkpoint03：3级/72、序号2 |
| 04 | 名作材料（`famed`） | 500／500 | 确认消费 | checkpoint04：4级/272、序号3 |
| 05 | 卓越材料 | 1200／1200 | 确认消费 | checkpoint05：6级/572、序号5 |

所有 Save 都须保持同一暂停日期、同一主人和同一目标原件，结算后 `pending=0`。升级按每级 `100×当前等级` 自动连续结算，玩家只决定是否消费材料，没有升级许可或停级按钮。第01次取消没有单独增加 Save；取消不消费由前后原生库存及返回管理页证明，其经验约束还由第02次喂养后的精确72经验共同核对，不能声称另有一次原生动态经验查询。

## Root 五次审阅的实际调用

每次等待 `case-output/feeding-preview-review-01-awaiting.json`，随后依次处理 `02`至`05`。中间还会出现 `checkpoint-readback-01`至`05` 的请求，继续交给既有 Save/Root 严格读回生产者；它们不是截图审阅请求。

每个截图请求到达后重新取得原始 PNG 和 capture JSON，直视图像中的材料名、材料基础经验、顶部本次经验。参数必须填写**实际看到的数字**；如果顶部仍显示0，就填0，让消费方记录真实失败，不得把请求中的期望值抄成观察值。无需 OCR。

下面是可放在场次外置控制脚本中的调用。`product_tools` 必须来自该场次冻结的产品执行树，`runtime_manifest` 是该场次实际 manifest 文件；截图和 capture 必须在本次请求之后取得。代码只封装已有证据，不负责截图或操作游戏。

```python
from pathlib import Path
import sys

# 以下值均从当前场次和刚完成的原图审阅填写。
product_tools = Path("<frozen-product-root>/mod_living_artifacts/tools")
awaiting = Path("<run>/case-output/feeding-preview-review-01-awaiting.json")
runtime_manifest = Path("<actual-runtime-manifest.json>")
original_png = Path("<this-request-original.png>")
capture_json = Path("<this-request-capture.json>")
actual_reviewer = "<operator_reviewer>"
observed_base = 80       # 填目视结果，不能从 expected_base_xp 自动代填。
observed_preview = 80    # 看见0就填0。
observed_material = "<目视材料名称>"

sys.path.insert(0, str(product_tools.resolve()))
from acceptance_contract import read, write_once
from preview_acceptance_adapter import produce_preview_review

response = produce_preview_review(
    awaiting.resolve(),
    manifest=read(runtime_manifest.resolve()),
    reviewer=actual_reviewer,
    screenshot=original_png.resolve(),
    capture=capture_json.resolve(),
    displayed_base_xp=observed_base,
    displayed_preview_xp=observed_preview,
    displayed_material_name=observed_material,
    direct_reviewed=True,
)
destination = awaiting.with_name(
    awaiting.name.removesuffix("-awaiting.json") + "-root-result.json"
)
write_once(destination, response)
```

对01至05各执行一次，使用各自的新 PNG/capture 和实际目视值。首次普通页审阅后会先取消，再生成第二个普通页请求；不要把它当成重复请求合并。已有 `*-root-result.json` 不覆盖、不重复提交。生产函数直接读取真实 awaiting 文件，不能给它裁掉公共字段后的裸 request body。

## 输入与回执字段

所有字段的定义以 `PreviewRequest`、`RootPreviewRequest`、`PreviewResponse` 为准；下表按用途分组，不创建另一套别名。

| 位置 | 字段与实际含义 |
| --- | --- |
| 请求类型 | `schema=living-artifacts-feeding-preview-request-v1`；`event_definition_key=xalw.11`；`review_method=direct-original-png-no-ocr`；`business_pass=false` |
| 场次身份 | `run_id`、`machine_id`、`pid`、十进制字符串 `connection_generation`、`actor_character_id`、`date_raw` |
| 原生页面与物品 | `event_instance_id`、十进制字符串 `target_artifact_id`和`material_artifact_id`、共享原生稀有度 `rarity`、`native_event_record` Pin |
| 数值与时刻 | `expected_base_xp`、`expected_preview_xp`、`requested_at_utc` |
| 公共 awaiting 附加项 | `original_hold_deadline`、`reserve_seconds`、`operator_reviewer`；reviewer 必须与其一致，审阅后仍须留下原来的退出预留 |
| 审阅响应 | 保留共同身份/物品/期望字段，`schema=living-artifacts-feeding-preview-review-v1`，新增 `reviewer`、`status=reviewed`、`reviewed_at_utc`、`direct_reviewed=true` |
| 原图与目视结果 | `screenshot`、`capture`、`root_request`三个 Pin；`displayed_base_xp`、`displayed_preview_xp`、`displayed_material_name` |

Pin 使用规范绝对路径、实际字节数和 SHA-256。数值 ID/序号拒绝 `bool`及相等的浮点数。`capture`沿用原图采集回执字段：

- `machine_id`、`observed_at_utc`；`gameplay_pass_claimed=false`。
- `image.path/bytes/sha256/width/height`，以及 `desktop.width/height`；宽高从原 PNG 和实际桌面取得，彼此一致，不预设分辨率或缩放比例。
- `foreground.pid`对应请求中的实际 CK3 PID。

时间须满足 `requested_at_utc ≤ capture.observed_at_utc ≤ reviewed_at_utc`，一次审阅最多180秒。producer 校验图像、capture与请求，消费方再次校验，并通过原生查询确认**同一个事件实例、人物与日期仍在显示**。同一张旧截图不能用于后续新请求。Root 的声明仅证明目视内容，不证明材料已消失或经验已到账。

## 结束与排除面

结果在 `living-artifacts-preview-result.json`，证据入口为 `preview-evidence-journal.json`。成功完成时有五份 `preview-review-*.json`、五份 `preview-checkpoint-*.json`、`preview-cancellation.json`及完整 `preview-error-full.log`/`preview-error-scan.json`。`verify_case`会重读证据，重新核对严格 melt、原生库存/装备、经验和图像回执。若前置或审阅提前失败，保留实际已产生的文件与 `state/profile/logs/error.log`，不补造五份成功记录；未走到最终扫描也不能据此宣称无错误。

四个本场检查为 `PREVIEW-FOUR-RARITIES`、`PREVIEW-CANCEL-01`、`PREVIEW-TRANSACTIONS-01`、`PREVIEW-MOD-SCRIPT-LOG-01`。完整扫描当场 error.log，模组脚本/UI运行错误须为0，包含此前缺失镇压序号的错误；静态未使用变量/目标告警和无归因诊断分列，不能把它们合称“全日志无错误”。

本场不覆盖：匹配食性的1.25倍预览、其他语言实机、实际镇压扣费/续期/到期、NPC 获取/装备/培养、全部内容、冷载、多人和 Workshop 发布。结果里的 `business_pass`、`product_release_pass`始终为false；即使本场 `PASS`，`normal_close_pending=true`仍要由公共入口完成正常退出并分别取得实际退出证据，不能把图片审阅回执当成正常闭场或完整产品验收。
