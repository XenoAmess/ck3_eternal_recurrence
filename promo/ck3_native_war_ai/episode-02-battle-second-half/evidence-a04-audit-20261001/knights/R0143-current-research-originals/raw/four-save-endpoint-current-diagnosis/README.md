# R0143 原版四存档端点核对

本目录只读取 R0143：runtime 419cac1a956c7be356d886256c7bc689cda5327d，PID17420，native-29829-a5224cf6dfcc。四份原版 immutable 存档逐 SHA 对原 native checkpoint 绑定，实际使用 Rakaly0.8.19 解码；raw exact copies、解码全文、角色/战斗/家族/荣誉全块差分和实际 argv/stdout/stderr 均保留。

新增端点证据：33437 在 1066.12.30 保存为死亡，reason death_battle、killer34120，军团65脱离；34120 的 prestige currency 和 accumulated 各+150、kills新增33437、signature_weapon新增axe。Army18 defender regiment14→13；原版UI getter left11→10只移除33437/right19不变。两个UI窗口的保存态顶层 RNG 端点相等，推进日 random_count +948。

UI 原图与前后 paused snapshot/subject/PID/GUI thread/context/owner 已核 SHA 和原件绑定；root 人工审图回执原样保留，本报告不制造新的视觉审批。上述存档及 getter 是端点证据：daily trace export容量失败，DTO未发布；monitor accepted=false/status failed/flags8/truncated128/uninstalledtrue，仅部分诊断。未运行严格 causal/selector/monitor 成功验收，13域完整可变链及机制后三项仍 pending，global_bundle_complete=false。相同端点不证明日内无写入/分支未执行/唯一因果。

权威事实为 R0143-actual-endpoint-semantic-facts-a01.json；完整过程主回执 R0143-final-readonly-endpoint-receipt-a01.json。较早 semantic-facts.json 是本轮派生中间件，保留历史，不作为最终13域状态。全过程未改源码、原件、Git、屏幕、游戏或视频；没有加载 R0142 的存档或读数。
