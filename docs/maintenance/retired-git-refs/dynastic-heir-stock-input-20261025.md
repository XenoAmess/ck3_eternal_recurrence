# Dynastic Esotericism 旧分支归档

原远端分支 `work/dynastic-heir-stock-input-20261025` 的最终提交为
`c3e46759b397f2f1950b6b46066a67c2df631dcb`，源码树为
`2cd50aca5b7accb6a316213cf84f7bfed7fd618c`。
[Git bundle](dynastic-heir-stock-input-20261025.bundle) 保存从主线已有的
`eda55b5f7dc3d32a06179345bf232c012afe739b` 以来的原始 28 个提交。
SHA-256 为 `e4484e5d103a4c3d77682c82ce2d44831d86cd67f595ba53e30fa8ab53c0ddd5`。

主线已接入存档读取、拜占庭两阶段罪行夹具、Root 协作停止、
campaign-root 能力和 Decisions 可见性读取。相应源码和验证记录见
[分支台账](../../branch-management.md#2026-11-26-主线收口)。

公开帝国恢复目前缺已执行的玩家操作、后继 S1 物理存档和同时点的头衔持有者证据。
原分支中两条公开恢复 case 的旧就绪标记随历史保留。容量与执行工具还依赖冻结场次中的
仓库外 Java 类型。这些实验源码保存在归档内，现行产品入口仍采用已经验证的离线合同。

## 恢复原始提交

在包含完整 `master` 历史的 Git 仓库根目录执行。恢复引用保存在本地归档命名空间内。

```text
git bundle verify docs/maintenance/retired-git-refs/dynastic-heir-stock-input-20261025.bundle
git fetch docs/maintenance/retired-git-refs/dynastic-heir-stock-input-20261025.bundle refs/remotes/origin/work/dynastic-heir-stock-input-20261025:refs/archive/dynastic-heir-stock-input-20261025
git rev-parse refs/archive/dynastic-heir-stock-input-20261025
```

2026-11-26 在 `machine_id: xenoamess-full-tower-eb9d2c1186` 的独立 bare
仓库中从 GitHub 获取唯一前置提交后解包，通过了原 tip、源码树、提交数量与执行工具原始 blob 的读回。
本次归档没有运行 CK3 或发布产品。
