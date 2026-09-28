# 第 2 期增援与战分计算卡

2026-09-28。三张 **2560×1440 全屏独立插页**对应[下一期镜头表](../shot-list.md)的 E2-06、E2-07、E2-09；画面底部 `y=1120..1439` 留白给字幕。它们只表现已取得的原生整数回执和说明，不是 CK3 实机截图，也不作为覆盖原生 UI 的叠层。现场画面、原速连续段和用户全片审阅仍按[证据索引](../join-terminal-evidence-index.md)另行取得。

| 卡 | 原版回放 | 说明 | 生成 SVG SHA-256 |
| --- | --- | --- | --- |
| [E2-06](e2-06-calculation.svg) | 085，第 11 日源档独立回放 | 旧双方 entry/cache 差额，ArmyID 22 的 13 团起始 2570 人与实际 current 2560 人，返回双方残差归零。 | `767543A90732DC811BB9930929E4651971944CE92EE359BC9CFAB8675D866AF5` |
| [E2-07](e2-07-calculation.svg) | 同一次 085 回放 | join 前后 base/final 战宽 `1645/1480→2467/2220`，首次 side 0 出伤 `R8D=2220`。森林 `0.9` 是同版原版脚本静态值，非 085 同帧运行时地形字段。 | `91BCCA2B3B540E90C28A1FAE3117F522039312300B8C6702B779379E980CD527` |
| [E2-09](e2-09-calculation.svg) | 024，第 27 日源档独立回放 | 分子 536.62042 人当量、八桶分母 996 人、整数比例 53.877%、CB 战分倍率 150、未封顶 80.8155、单场封顶 50、战争进攻方相对 `-50`。 | `24EE5070E34E5804E7AD2CC813747B235DF5EB7129D3D5EF1E6902310A2E97F2` |

085 和 024 是不同日期检查点、不同独立回放；这三张卡不能串成同一条原速轨迹。每张卡顶部标 attempt，底部标 exact build、CombatID `16777218`、WarID `4`、原生日戳及**各自原始回执完整 SHA-256**。[数据表](calculation-cards.json)还保留双方来源存档、原始终局/采集回执及清场文件的路径与 SHA。085 自己已有入场前、返回后、首次出伤三点，E2-07 无需把另一条 083 回放的第三点拼入。024 的 50 是一条 battle row，不等于整个战争总分；败方的正常败退也不是主动撤退证据。

## 样式来源和复现

[渲染脚本](render_calculation_cards.py)只用 Python 标准库生成 SVG。背景 `#211813`、面板 `#35291F`、主字 `#F0E5CF`、金色 `#CBA56A`、弱线 `#61503C` 均来自系列已有的 [`war_ai_promo.visuals`](../../integration/src/war_ai_promo/visuals.py)；字体首选 **Microsoft YaHei**，与系列既有 [`war_ai_promo.common.font`](../../integration/src/war_ai_promo/common.py) 的 `msyh.ttc/msyhbd.ttc` 一致，其他平台回退 `Noto Sans CJK SC`。没有调用 CK3、外部图像生成或宣传工具链，也没有使用原版 UI 位图。

在仓库根目录使用已验证的 Python 执行：

```text
tools\.venv\Scripts\python.exe promo\ck3_native_war_ai\episode-02-battle-second-half\cards\render_calculation_cards.py --verify-sources
tools\.venv\Scripts\python.exe promo\ck3_native_war_ai\episode-02-battle-second-half\cards\render_calculation_cards.py --check --verify-sources
```

`--verify-sources` 对本机外置 attempt-004/085/024 的**两份冻结存档、两份原始响应和两份清场回执**逐字节算 SHA；只有这些本地证据齐备时使用。跨机只检查 repo 内数据与生成 SVG 的确定性，可仅运行 `--check`。生成器在算式不成立、085/024 被混作同一回放、来源 SHA 不符或 SVG bytes 偏离时拒绝通过。SVG 是生成结果，调整文字与数值应改 JSON 或脚本后重建；不要手改 SVG。

2026-09-28 在独立 worktree 用主 worktree 的已验证 Python `3.14.7` 完成 `--check --verify-sources`；三张 SVG 又以 Edge headless 渲染成外置预览并逐张人工查看版式。预览仅用于检查文字可读、面板间距和字幕安全区，不是成片人工审阅。
