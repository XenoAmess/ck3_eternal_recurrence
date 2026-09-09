# 重整河山 0.1.1 验收方案

状态：执行版

目标游戏：CK3 `1.19.0.6`；正式产品：`mod_reclaim_the_motherland`。

## 1. 验收原则

- 每次 CK3 步骤先执行 `open_kaishek` 离线预验，并在同一 run 记录 commit、profile、游戏版本、EXE SHA-256、语料 SHA-256、实际命令、结果和不支持项。
- 游戏控制采用原生 MCP bridge 取得 readiness、paused snapshot、恢复/暂停和最终状态；当前 MCP 未暴露王朝循环 participant group、动态头衔变量和决议可用性，因此这些字段由外置、不会进入 release staging 的引擎夹具断言，决议 UI 只用于触发真实产品入口。
- CK3 排他槽使用 `xar_autoplayer.locking.exclusive_launch_lock`；若槽位已占用，runner 等待，不抢占、不终止别人的进程。
- L0/L1/L3 各自只证明其声明的边界。脚本解析、夹具 PASS 或上传成功都不能替代 fresh Workshop cache 的完整复核。
- 正式 staging 只能由 `tools/build_reclaim_the_motherland_release.py` 生成；仓库与正式 staging 的内层 `descriptor.mod` 不含 `remote_file_id`。

## 2. L0 静态与构建

执行：

```powershell
& tools/.venv/Scripts/python.exe tools/compose_reclaim_the_motherland_key_art.py --check
& tools/.venv/Scripts/python.exe tools/test_reclaim_the_motherland_contract.py
& tools/.venv/Scripts/python.exe tools/test_build_reclaim_the_motherland_release.py
& tools/.venv/Scripts/python.exe tools/validate_reclaim_the_motherland_static.py
& tools/.venv/Scripts/python.exe tools/build_reclaim_the_motherland_release.py --check
```

通过条件：

- 原版两个覆写点仍与 CK3 1.19.0.6 锁定基线一致；自定义路径与完整原版回退路径均存在。
- 28 文件 release allowlist 精确成立；九语均为 UTF-8 BOM、102/102 key 对称（13 个产品文案 key 与 89 个确定性朝号组合 key）、格式 token 不漂移、七语无英文占位。
- 640×640 PNG thumbnail 小于 1,000,000 bytes，且逐字节等于源图的确定性投影。
- 两次 staging 的 manifest 与 ZIP 逐字节一致。

## 3. L1 源码实机

外置夹具在 1066 年宋帝真实角色与真实封臣树上执行：

1. 把一名直属有地封臣固定到尊王派，把其余直属有地封臣固定到非尊王派，记录一名尊王派下级封臣和一名非尊王派直属封臣。
2. 先确认两个对照封臣分别处于尊王派与扩张派。精确存档书签可能从不带原版运动冻结 `on_end` 的阶段被测试夹具强制跳入群雄割据，因此夹具先按原版合同把当下真实 participant-group scope 写入 `former_movement_member`，再通过真实 `situation:dynastic_cycle.situation_top_sub_region.change_phase` 切换阶段；地图推进离开书签首日后显式触发原版 `tgp_dynastic_cycle.0081`，由该事件调用产品覆盖的 `tgp_chaos_shattering_effect`。
3. 引擎断言旧天子失去 `h_china`，但仍有地、仍持有原个人伯爵领，获得一个 marker 正确、空法理、由本人持有的动态霸权；尊王派直属封臣及其下级 realm tree 保留，非尊王派直属封臣脱离。
4. 在实机事件中显示动态后朝全名，保存截图，验证简中“后＋原朝号”的渲染结果。
5. 关闭所有验收专用窗口后，通过原生 MCP `ck3_center_map_on_landed_title_v1` 将地图镜头定位到大宋首都 `b_kaifeng`（开封），并以相机 settled 回读为权威证据；随后保存无面板地图画面。详细地图层级可能以相邻的“管城县”标示这一区域，因此 OCR 辅证接受“开封”“汴州”或“管城县”，但不允许出现“教宗”“意大利”“罗马”“那波利”“萨莱诺”等意大利地名，也不允许出现“验收”字样。
6. 把中华法理伯爵领隔离转移到控制角色，再逐郡转回：先证明控制比例 `>=50%` 且 `<` 原版 `claim_mandate_china_county_percentage_value` 时“宣称复辟”不满足；再转移到刚好首次满足原版门槛。
7. 决议面板确认“宣称复辟”可见且可执行，并确认“宣称天命”对后朝持有者不可见；点击真实产品决议。
8. 引擎断言完整原版复辟结果至少包含：玩家重新持有 `h_china`、三日 `claimed_the_mandate_of_heaven` flag 已写入；产品额外结果为全部本人后朝霸权销毁。
9. 收集项目相关 `error.log`、`gui_warnings.log`、`database_conflicts.log`；项目解析/运行错误、重复 key、进程清理未证明、runtime/source 被改写任一项均为 RED。

## 4. L3 Workshop fresh-cache

首次上传后：

1. 用新 item ID 重建 ID-bearing sidecar manifest；不得把 ID 写进 canonical descriptor。
2. 删除本地订阅缓存后由 Steam 重新下载，确认是 fresh cache，而非上传 staging 的残留副本。
3. `--verify --workshop-cache` 精确核对 28/28 文件；仅允许缓存内层 descriptor 追加一行正确的 `remote_file_id`。
4. 对 strict-verified 的数字 cache leaf 再执行与 L1 相同的 MCP-first 实机矩阵。
5. 核对公开 item 的标题、可见性、Gameplay 标签、640×640 preview 与仓库 BBCode；把最终 GREEN artifact 投影出的三张真实游戏截图按跟踪清单上传、排序并写入 BBCode。第一张画面的地图背景必须由上述 `b_kaifeng` MCP 定位证据约束在开封，不得出现意大利地名；禁止用生成插画冒充实机证据。
6. 从精确 tag 重建正式 staging，恢复无 ID 的内层 descriptor；写入并 push initial-baseline changelog 后才可标记发布完成。

## 5. 报告与证据

最终结果写入 `docs/acceptance-report.md`，至少记录：

- 源码/tag/Workshop item 身份；
- L0 命令与结果；
- L1、L3 artifact 绝对路径及 `report.json` SHA-256；
- open_kaishek provenance、MCP readiness、slot 等待时间、关键截图与 fixture markers；
- manifest/ZIP/thumbnail/fresh-cache 哈希；
- 发布本地化审阅边界；
- 已知限制与任何保留的 RED attempt。
