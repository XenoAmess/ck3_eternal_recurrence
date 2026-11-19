# 三项已有现金边界修复的精确脚本回归

当前生产源码定向复核确认三项修复已经存在，因此本包没有生产修复或 runtime 清单变化，只有测试和说明。不能把此前静态风险列表当成当前漏洞，也不能把下面源码依据说成新增实机通过。

1. ensure_account 在调用前清 xfm_account 输出；旧仓导入另检查真实 beneficiary 的 typed finance_account。测试让 A 的输出引用残留，再令 B 账户工厂真实失败，执行实际 ensure 和 import，核 A 的钱／冻结／继承标记／仓位／债务引用完全未变、B 未假导入；解除工厂失败后真实导入 B，一次成功且重复导入不复制资产。
2. governance 已将 maker holder/beneficial_owner 同步到现控制人；spot submit 和 book refresh 也刷新真实受益人。测试通过实际 maker producer 建双边报价，政治实体从 A 换到 B 后执行真实 controller refresh，再用 B 私账户发可交叉买单：订单可挂起，但绝不与 B 实质控制的 maker 成交。真实独立第三方的普通订单仍可实际成交，证明不是把撮合停掉。
3. maker 退出已经按每笔最多100000000分、单次32笔分块，未清余额保 pending；每日 coin registry 分支重试，归档快路要求 pending=0。测试以3200000123分作合法大额账本前置，先执行32个真实普通 transfer，留123分，再直接执行从真实 daily registry loop 取得的原 if Entry，最后123到账且 pending=0；再执行同一原分支无新增提现或 transfer。每步现金守恒。

复用现有生产脚本 VM，仅补原生临时列表 append / list 读取及顶层效果清临时列表的语义；generic effect 计数只是观察，原函数体照常执行，没有用 stub 设置金融结果。新三 case 不修改既有期望。大额用例执行原 daily 的实际 pending 分支 AST，未执行同循环内无关的30日线写入及盘口刷新，不外推为完整日调度或游戏 SAVE 验收。工厂失败是原有可控 Story factory port，失败后的 ensure/import 分支全部执行实际源码；政治控制和转账均不 port。

作者没有编译／运行测试、Root Git 或 Game 操作。由 Root 在正常关闭当前场后采用测试叶，以相称 focused 验证和最后完整验收取得软件资格。原325项通过不能追认为这三个新增用例已运行。
