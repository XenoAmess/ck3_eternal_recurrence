# R0027 c791914b8 exact CI：两项成功、Official失败；实机待验

归档对象是已存在的精确源码提交 `c791914b84b9eb7cf0a83b94d55c25fb24175157`，不引用未来文档提交，也不将旧574c结果用于本提交。官方API原件及完整三项job日志见原INDEX/FINAL/raw-evidence.zip。

Li Yu Dao static checks [37704098239](https://github.com/XenoAmess/ck3_eternal_recurrence/actions/runs/37704098239) SUCCESS；Linear history [37704098241](https://github.com/XenoAmess/ck3_eternal_recurrence/actions/runs/37704098241) SUCCESS；Official Runner CI [37704098208](https://github.com/XenoAmess/ck3_eternal_recurrence/actions/runs/37704098208) FAIL。具体失败是Reclaim the Motherland release tooling：`tools/test_reclaim_the_motherland_contract.py:579`，`test_phase_three_title_law_and_idempotent_save_migration`断言`3 != 2`。本提交没有RMTM变化路径；失败仍保留为该exact HEAD的Official CI失败，不因此改成全CI成功。

CI owner已对31份原件、23组去重内容核过原SHA；原ZIP89586B，SHA `8a884baa682ac4bebae3a9077d075152d67327dd1011864b1de7c1c6cf56859a`。本预备包直接引用，不重复解包或测试，不strip原日志。

这是永久入库准备清单，ROOT可在R27报告交付时create-only导入。当前native build完成结果、R27 runtime、newT/C3/I4均NULL；两项静态CI成功不授本轮实机或整体GREEN。MAIN/Git/SDK/游戏/进程/屏幕/总线动作0。
