# R0216 资源接续与旧 76d CI 读回

本目录回执均属于 `machine_id: desktop-3fevhd2-1c74096080`，记录自身 UTC 观察时间和原件路径／大小／SHA。`integration.json` 将已验候选及复制证据逐字节绑定；35 项 focused 与真实资源检查通过，不授正常闭场或业务资格。

2026-10-20T03:22:34Z 官方 exact `76dcbf7fe4526117fc25f0c892593b570f0a8b68` 的 [Official Runner CI](https://github.com/XenoAmess/ck3_eternal_recurrence/actions/runs/39361392848) 完成为 failure，Linear history 成功。失败 job 为 [static / 118428157093](https://github.com/XenoAmess/ck3_eternal_recurrence/actions/runs/39361392848/job/118428157093)，step 为 `Test shared CK3 acceptance without installed CK3`。源日志 2026-10-20T03:23:09Z 从官方读取，140,004 B，SHA `9ab1d3b008b20589cb60f9359f73e8d17bbb560d704d2b48c03520bfb66944b8`；本机原件 `C:/ck3-e04-resume-20261020-a01/ci-final-76d-a01/FAILED-STEP-LOG.actual.txt`，完整小终态回执 `TERMINAL.actual.json` 为 12,946 B / `da1c9d5e79bafd726cc73cb1d255f33e05f767edc414ab10c443fca41a244b36`。这条 CI 不包含随后 R0216 的新增 missing-normal 资源分支。

官方错误为测试夹具遗漏新 `Selection` opt-in 字段，以及全源码 SHA 守卫拒绝两份产品证据 adapter 中的精确 EXE 来源常量。仅更新夹具三项 false 字段，并对两份精确模块／唯一赋值名／完整 SHA 做 AST 核对后屏蔽该赋值，其余源码继续受机器路径与 SHA 守卫约束。

2026-10-20T03:25:09Z 的 25 项本地复验已消除上述两项，但路径守卫进一步检出真实未便携依赖：`faith_e02_first_four_integrated_adapter.py` 从固定 `C:/workspace/.../candidate/tools` 导入未随仓库携带的 scout。此时为 24 pass / 1 fail；保留 RED，不整文件跳过，不将该缺口计入已闭。原件 `ADAPTER-FOCUSED.stderr.txt` 为 30,556 B / `30fb23de77f9fbe696639e035ffa6f93f401db86f98c053a33e14ad306854345`；测试源为 54,244 B / `4ae0887478f9be0e301b9c94030ce9291e9028db7517ca4e078df3fa711b251d`。

本页只保存小摘要与精确来源，未复制整份日志。上述外置 CI 小证据最迟 2026-10-27T03:25:09Z 复核；原件不可读时应如实标记，不能另造同名证据。
