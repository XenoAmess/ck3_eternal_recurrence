# 纯原版新局的普通继承资格

机器：`xenoamess-full-tower-eb9d2c1186`。本包对应Root为1066罗贝尔干净新局准备的
SDK37 CLEAN03；[来源索引](SOURCE-PINS.json)绑定小patch及生产源码。
前批`b25c96f2`的[Official39007487520](https://github.com/XenoAmess/ck3_eternal_recurrence/actions/runs/39007487520)
与Linear39007487528已实际success，保存[终态小回执](OFFICIAL-TWELFTH-CI-FINAL.json)。
新局从主菜单起录、重新计算30年目标，不携带旧局战果／天数／Driver／goal。
这里没有启动Game、改变mod配置或操作现场。

## 不把未加载改写成关闭

原普通继承合同要求准备环境有明确`xar_off`，因此纯原版环境不含该规则时会被拒绝。
现在仅在显式fresh no-pact、准备profile明确启用列表为空，且Root已审阅实际启动日志
并给出已知空加载列表时，允许另一个合同：
`xar_enabled=None`、pact／source均为`absent_by_verified_xar_mod_not_loaded`。
旧`xar_off`与rogue-one-life行为保留，缺字段或unknown不等于关闭。

SDK核验同一profile的`dlc_load.json`原字节、大小和SHA；启动日志使用不可变审阅快照及SHA，
原日志路径必须属于该隔离profile的logs。证明还绑定环境摘要、明确审阅者和实际Game PID／
出生FILETIME。它不扫描不到XAR字符串便判未加载，不自行解释空日志，也不自动取得审阅资格。
新Game必须有其自身实际证明；本次离线fixture只生成合成文件，不能充当新Game证明。

## 普通继承消费者

公共[queue消费者](../../../../tools/g2_saved_campaign/m7_ordinary_successor_queue.py)
的两个旧`xar_off`硬编码入口改为同一无SDK依赖predicate。新None分支必须具有完整六字段、
精确pact／source及环境SHA，不能仅因None继续继承；旧xar_off准入保留。
原始完成回执、前后episode、public／Native帧、同进程、分封reconciliation、当前后继与
配对SAVE守卫不变。构造adapter不执行操作；消费已完成原回执不重发Continue。

旧ordinary seed rebinder及特定h3937研究入口仍限定其原xar_off checkpoint用途，
本包不把干净重开改成旧局carry，也没有扩大这些研究入口。owner另核新运行端不导入公共M7，
而调用私有`automatic_handoff`；其原单一off门已有两合同候选，正在对齐此公共predicate，
精确运行侧差量与部署事实另记。场次目录不作为公共API导入位置。

## 验证与边界

31项／24子例通过：正式公共binder读取临时profile／log，拒绝缺失、unknown、非空列表、
foreign profile、篡改pin及布尔伪身份；新合同完整异步queue消费及旧owner／modal／adoption／
persistence／per-title回归。新queue正例保留public6／Native42，所有传输和SAVE为显式fake，
没有真实继承、SAVE或Native调用；错误合同在第一次回调前即拒绝。
新增7项／24子例也在`-O`通过，输入资格不依赖可被优化移除的assert；Python-only检查通过。

Root准备的候选binder为`e99ab19e…`，CLEAN03 source manifest为`ef5a2dac…`；
公共source仅另纠正文档描述。新局实际启动／mod加载证明／自然死亡继承尚需Root原件，
不由这些离线测试宣称完成。稳定30年第一，随后<1秒／日、0.5秒／日，均未达。

## 静态知识可以复用，现场身份重新观察

[离线学习移交](STATIC-KNOWLEDGE-DELIVERY.json)在06:08:54Z封包时全部未arm，
worker／seed安装均为0；此后实际执行需Root另证。71个旧source entry中，59条显式
character事件去重为58组静态facts，9条letter及3条无显式type排除。`pam_*`来自原版DLC，
不能按名称归为mod；历史calculated ID只保来源身份，不作为新局当前事件实例ID。
新局仍需fresh actor／选项／exact build验证。G2原状态6/8、M6/M7缺口保持。
[原小结](STATIC-KNOWLEDGE-NOTE.md)与来源保留，没有复制0.91MB种子、旧状态或场次owner脚本。
