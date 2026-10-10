# 2026-10-11 I4 Source11 与独立案例预检

截至 00:14 CST，新容量准入、冻结、公共 `prepare`、`plan`、`preflight` 均实际 exit 0。尚未 allocate、启动 CK3 或获得新业务结果。一期仍 **75% / NOT_GREEN**；正式 B4/B5/C3/I4 缺口保持。

## 冻结输入

- Source11：`b539d0180b66a22ec4efa2ccf5c6acd40339e621`，单父为 Source10 `b9d179bc74b69e7fc92cd82499622d224a1ab93e`；标签 `archive/ck3-common-runtime/source11-20261011-011`。导出 `C:/csr11`，运行时 `C:/workspace/ck3-common-runtime/20261010-011`。
- 仅从已发布 `120530139e409631579da7c1db7c6b2bca02a045` 投影 keeper、queue 及两个便携测试。7905 文件继承、2 文件替换、2 文件新增，共 7909 文件。未重编 native；host、MCP、DLL、injector、capabilities 沿用 O10，未引入另一执行线的 Source18。
- 修复及必要测试见[共享工具专题](../ck3-native-ai/2026-10-10-shared-acceptance-keeper-and-queue.md)。本次没有重复旧测试；冻结成功不能代替新 keeper/queue 实机场景验收。

## 新案例与实际预检

独立目录 `C:/workspace/ck3-common-runtime/cases/lyd-i4-natural-expiry-20261011-003`，沿用原 0240 存档、actor 31254、date 53144712、正式产品与配置；只改新 `state_dir`，不复用已消费 CASE2。公共入口为 `tools/ck3_mod_acceptance.py`，case 为 `i4-existing-school-cooldown`。

| 实际操作 | 完成时间（CST） | 结果 |
| --- | --- | --- |
| 容量准入 003 | 00:11:10 | exit 0 |
| Source11 冻结与导出 | 00:11:44 | exit 0，无 native build |
| 公共 prepare | 00:11:54 | exit 0 |
| 公共 plan | 00:12:06 | exit 0 |
| 公共 preflight | 00:12:07 | exit 0，blockers=[]，runtime NOT_RUN |

原始小证据共 **50,598 B**，包含实际命令回执、冻结绑定、runtime/manifest、完整 preflight stdout 与容量准入：[INDEX](acceptance/2026-10-11-i4-source11-preflight/INDEX.actual.json)。prepare/plan stdout 留外置精确引用，不复制大存档、索引或整棵运行树到 Git。

## 容量与下一门槛

预约 003 的保守已有使用量为 `132205666666 B`；加新峰值 `4294967296 B` 后为 `136500633962 B`，低于 `137438953472 B` 原配额，余 `938319510 B`。当时 C 盘实际可用 `622757015552 B`。这是容量准入，不是全项目物理占用测量；未扣减历史清理或把旧预约退还写成删除。

预约截止 `2026-10-11T06:11:10.391492+08:00`；配额复核截止仍 `2026-10-12T13:19:51.814083+08:00`。输入、缓存与 Source10 的原复核时间均不因复制而延长。详见[当日存储记录](../maintenance/storage-retention-2026-10-11.md)。

先发布本轮输入与跨日记录，保持 MAIN 干净，再由公共 allocator 分配新 run 与 a14 keeper，审阅新鲜 Steam 离线画面及精确 ready/frozen 绑定，随后只运行一次 CASE3。运行期间保持 checkout 冻结；完成或 RED 后依实际 OS/native/host/keeper 回执收尾、CAS 释放并闭账 003。完整到期、final SAVE、冷恢复与新完整 365 日循环仍各需自己的实际证据，当前预检不授予这些信用。

R51 的业务 RED、原正常关闭失败与后来行政闭场保持原结论，见[原小证据](acceptance/2026-10-10-i4-natural-r51/INDEX.actual.json)。本轮不追认旧场通过。
