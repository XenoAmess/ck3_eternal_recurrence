# 琉焰卿的永恒轮回

## ……我将永不停歇地，一次次回到那个你还在的冬日

一个 Crusader Kings III 的轮回 roguelike mod：每次人生结算分数，纪录**跨存档全局保存**，新开局可把纪录作为点数副本购买属性强化。

订阅地址： https://steamcommunity.com/sharedfiles/filedetails/?id=3784706360

> **⚠ 必须开启教程！** 游戏设置 → 教程（reactive advice）选「完整」或「警告」均可——**切勿「禁用」**。
>
> <sub>原因：本 mod 的跨存档全局存储复用的是引擎的教程课程持久化机制（`tutorial.txt`）。教程被禁用后课程不会完成与落盘，纪录既无法写入也无法读取，mod 核心功能整体失效。</sub>

## 玩法

1. 游戏规则中启用「琉焰卿的永恒轮回」（默认启用）
2. 开局弹出「终末之契」：接受则获得特质【琉焰之视】（微小健康增益、+10% 压力）并进入商店；拒绝则本局与无 mod 无异

![终末之契](screenshots/01.jpg)

3. 「轮回当铺」（分页）：分数 = 全局最高纪录的副本。可购买六维属性、金钱/威望/虔诚/影响力/宗族威望、预期寿命、免费宗教改革（每局限一次）。每件商品每次购买后涨价 ×1.2（仅当局）。点「开始此生」时剩余分数等量转为金币

![轮回当铺](screenshots/02.jpg)

4. 琉焰卿的「垂青会」：开局及此后每 3 年，可从随机 3 项祝福中领 1 项，但每领 1 祝福必须再从随机 3 项诅咒中选 1；每场至多 3 对，每对使最终结算 +1%（加算）。池子见 [docs/blessing-curse-pools.md](docs/blessing-curse-pools.md)
5. 死亡时先写入全局纪录（教程通知），随后展示可滚动的完整结算明细；确认后本局进入观察者模式，不可继续扮演后代

![轮回终结·上](screenshots/03.jpg)

![轮回终结·下](screenshots/04.jpg)

**算分规则**：详见 [docs/scoring-rules.md](docs/scoring-rules.md)（逐条分列；游戏内死亡结算事件会展示当局逐项实况数值与完整公式）。

## 原理

利用引擎全局持久化的 `tutorial.txt` 课程完成列表作为只增位存储，分层阈值编码纪录（粒度 1→1000 递增，上限 167,600，可扩展）。课程用 `trigger_transition` 自动完成，无需玩家点击；读取经由 customizable_localization → GUI state → scripted_gui 桥接导入存档。详见 `docs/cross-save-persistence.md`。

## 要求

- 游戏设置中开启教程（reactive advice）
- 单机定位（多人下各人纪录独立）

## 开发

源码地址 https://github.com/XenoAmess/ck3_eternal_recurrence.git

```powershell
py XenoAmess_s_Eternal_Recurrence/tools/gen_highscore.py   # 重新生成位体系文件
```

测试与调试流程见 `AGENTS.md` 与 `docs/testing-workflow.md`。
