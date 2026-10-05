# R0175 B合军：只读研究包

当前正式状态由terminal-overlay.json说明：B在+38提前停止，余52日，冻结兵团/统帅条件未通过；无可比较伦敦终点。arithmetic-result.json保留先前合军sourcecut，其中formalterminal=null是当时的历史。当前补充不改写原始来源或旧结果。

所有核算输入在sources/相对路径。`replay_merge_arithmetic.py`只编译精确原helper中hash-bound的weighted_supply纯函数，绝不导入其顶层模块、调用SDK或游戏。原helper以.py.txt保存，不是操作入口。字节来源10份；正式terminal另有2份。没有图片、录像、音频、存档或凭据。

在任意机器使用标准库Python：

```text
<verified-python> -I -S -B verify_frozen_package.py --output <new-verify.json>
<verified-python> -I -S -B replay_merge_arithmetic.py --output <new-arithmetic.json>
```

输出拒绝覆盖，默认输入目录为脚本所在目录。核算结果是离线历史重放，不是新的实机采样或支付应用账。focused-checks/保留实际12项数学/负测回执；terminal-focused-checks/保留后来的6项追加核对，生产源.txt仅为历史实现凭证，不是本包消费入口。既有69段口述、配音和字幕不进入此研究scope。
