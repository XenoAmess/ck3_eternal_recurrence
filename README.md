# XenoAmess's Eternal Recurrence

一个 Crusader Kings III 的轮回 roguelike mod：每次人生结算分数，纪录**跨存档全局保存**，新开局可把纪录作为点数副本购买属性强化。

## 玩法

1. 游戏规则中启用「XenoAmess 的永恒轮回」（默认启用）
2. 开局弹出「终末之契」：接受则获得特质【琉焰之视】（微小健康增益、+10% 压力）并进入商店；拒绝则本局与无 mod 无异
3. 「轮回当铺」（分页）：分数 = 全局最高纪录的副本。可购买六维属性、金钱/威望/虔诚/影响力/宗族威望、预期寿命、免费宗教改革（每局限一次）。每件商品每次购买后涨价 ×1.2（仅当局）。点「开始此生」时剩余分数等量转为金币
4. 死亡时先写入全局纪录（教程通知），随后展示可滚动的完整结算明细；确认后本局进入观察者模式，不可继续扮演后代

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
