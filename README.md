# XenoAmess's Eternal Recurrence

一个 Crusader Kings III 的轮回 roguelike mod：每次人生结算分数，纪录**跨存档全局保存**，新开局可把纪录作为点数副本购买属性强化。

## 玩法

1. 游戏规则中启用「XenoAmess 的永恒轮回」（默认启用）
2. 开局弹出「永恒轮回」商店：分数 = 全局最高纪录的副本，每 25 分购买 1 点属性（外交/军事/管理/谋略/学识/勇武）
3. 死亡时结算当局分数，破纪录则写入全局纪录（弹出教程通知），随后展示结算（当局分数/此前纪录/差值）

**算分规则**（log₂ 均向下取整）：六维属性每点 1 分；每个在世且为你后代的宗族成员 0.1 分、家族成员额外 0.1 分；金钱 log₂×5；威望/虔诚/影响力 各 log₂×3；死时持有头衔 伯1/公2.5/王5/帝10/霸20；在世后代按最高头衔 伯0.25/公1/王2.5/帝5/霸10；有地时领地规模（含封臣伯爵领数）log₂×10。

## 原理

利用引擎全局持久化的 `tutorial.txt` 课程完成列表作为只增位存储，分层阈值编码纪录（粒度 1→1000 递增，上限 167,600，可扩展）。课程用 `trigger_transition` 自动完成，无需玩家点击；读取经由 customizable_localization → GUI state → scripted_gui 桥接导入存档。详见 `docs/cross-save-persistence.md`。

## 要求

- 游戏设置中开启教程（reactive advice）
- 单机定位（多人下各人纪录独立）

## 开发

```powershell
py XenoAmess_s_Eternal_Recurrence/tools/gen_highscore.py   # 重新生成位体系文件
```

测试与调试流程见 `AGENTS.md` 与 `docs/testing-workflow.md`。
