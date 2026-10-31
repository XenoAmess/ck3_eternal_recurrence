# 第一期完整续拍：190.5.1至191.6.1

`machine_id: 4-8e1c2f1861`。本次从shooting-02的真实May1保存继续，Game2008，同一董卓人物5048；没有为补结尾开第二局、改日期、手工触事件或改战果。续拍396游戏日，合前段120日，全故事516日。用户已否定约470秒初版，要求继续拍清战争与人物结局；旧版保留过程记录，新版交付及人工签核另记。

## 已拍故事

| 日期／阶段 | 实际结果 | 口播边界 |
| --- | --- | --- |
| 190.5.1续载 | 原May1存档，董卓5048、战争31仍在 | 不把加载、编译或SDK新session计游戏日。 |
| 190.6.14消息 | 孙坚退出战争与洪水袭击敌方同屏 | 两通知没有已证因果，不说洪水逼退孙坚。 |
| 190.7.2 | 刘协来信，已命王弘助战；0015第一显示“好消息”原生确认，旧实例消失 | 来信确认援助安排，不由点击再次入战；不凭信推兵已到场。 |
| 190.7.31→8.5 | 省2430一场小战：我方20,027→20,024，对方初始488，结果winning_side0/wipedyes | 地名、5674名字未核，不猜；结果winner/leader哨兵不当真实人物ID。 |
| 190.9.5→10.16 | 伊阙省774守战，乐进领我方30,417→30,214，袁术一方35,949→14,810，我方胜；战后war31分数19 | 只称伊阙之战，旧tongguan/yiqiu文件名是早期误猜别名；不称全歼、不冒称整场战争胜利，袁术主参战者与6224实际统帅分开。 |
| 191.1.2画面 | WJ_peer.100食邑岁禄5金，原生确认旧实例消失 | 款项在通知前由年度脚本发放，知悉不再发钱、不改领地持有。 |
| Native raw45474576／191.3.3画面 | hd190.0001张鲁据汉中，唯一选项“汉中自此另立门户”原生确认 | 原生上下文与截图时点分别记录；不能将截图日期反填成精确触发日。消息选项无effect，不由董卓点出割据。 |
| 191.6.1 raw45476784 | 事件21“未央之约”，原生选“照常入朝”，旧实例消失 | 实际选第一项，不沿用旧稿称病设想；没有拍称病延后分支。 |
| 同日终局 | 玩家5048→7261，董卓51岁被谋杀，董璜34继承；War31从存在到`active_wars=[]` | 原生列表变化与主要守方死亡失效规则吻合，没有军事胜利／强制议和／typed winner回执。 |
| 同日后态 | 原版GUI继续继承、显示“国贼伏诛”后唯一按钮关闭；再原生打开并独立读取5048及7261 | 两次GUI fallback另计，原生读树不等于死亡窗提交能力；同campaign继承，不是另开一局。 |
| 最终人物／领主 | 董璜实拍500兵、1头衔；root read直属领主7227、最高8928，家族头衔c_hd_nf_longxi_dong | 不把500兵等同旧军队全死，不说仍直接隶属刘协，不猜7227姓名。 |

年中陌生请求`celestial_request_elders_support_interaction`、冬春`find_elder_interaction`及已知婚约请求均保原生context／合法拒绝／独立后态。新知识离线核定义，不把研究文档写成已注册生产策略。对主片没有影响的弹窗处理不逐条塞入成片。

## 新增来源与原件

本机外置根为`C:/workspace/hanjin-spring-autumn-20261031/shooting-03`。详细原件不入Git；共享库仅收精简机器记录、源码pins及必要摘录。

- `research/july-event-16/`：刘协来信0015的原版定义、最终交互覆盖、局部读取及来源SHA。
- `research/october-battles/`：October保存流式读到EOF的精简battle_result16777223／16777226原文、既有解析器结果、角色名字交叉来源及SHA；没有保完整世界melt。
- `research/winter-events/`：年禄、汉中消息、长老邀请与婚约拒绝定义及13source/28evidencepins。
- `research/final-death/`：入朝至死亡、全局死讯、继承读取与来源边界，11source/30evidencepins；`machine-record.json`保同日前后绑定。
- `research/sentinel-entry-notes.md`：DLL宣告／源码能力与本局实际不可用分别记录。两次`life-advance-one-day`均明确`tactical daily sentinel is unavailable`、无新增日；本局采用既有普通`life-advance`逐日推进，不把失败授成功。

总共三次Native SAVE：前段May1一次，本段October和未央前各一次；SDK episode seed不另计。May1原件40,181,838B、SHA`46ead77a194e755e247fc0ad3777df59f0bc487765463bf67dc6c677a957c1b6`仍在shooting-02。October保存42,980,005B、SHA`e54896d943a3abca322d6584ef8a58932253825d7179d051c1c2aa284fa90857`已完成只读解析后释放，原checkpoint路径随后覆盖；保精简解析，不制造同名旧原件。未央前保存44,261,446B、SHA`a6d2f7d607bad165b93389970e1e6caaa2b58c46d442948c502177295aa88f49`，日期191.6.1，尚未选择入朝。

新保存的SDK seed元数据仍引用October SHA，但文档未独立重新检查seed文件，不由元数据推保存副本仍可读。legacy lifecycle默认值`rogue_one_life/xar_on`也不证明本局加载永恒轮回；四包profile的第四包仅纯董卓书签入口。

## 终局源码边界

“国贼伏诛”是`hd_world_news.0009`。董卓on_death→`hd_handle_dong_regent_death_effect`保存人物scope、全局发通报；若吕布动手且本谋杀链有效，广播把王允设为主谋，显示王允与吕布合谋。唯一按钮“天下又要变了”没有effect。实际killer具体Native字段未读出，不用广播文案填该字段。

入朝第一项当天直接执行隐藏诛董事件；死亡后`hd_dong_aftermath.0002`向汉帝排期一日后处理郿国／官职／势力落位。本局停在191.6.1，因此不宣称0002、全部吕布王允李傕安排或其后新战争已实机完成。董卓的死亡和这场战争退出是本片结尾，不继续机制预告或别人人物篇。

旧episode因played_character_changed进入terminal，不能消费原版死后通报。root保留原生读取诊断，再用原版GUI继续／关闭；不假称已有MCP死亡提交API，不通过改SDK账本伪造终态。

## 收场与交付

`launcher/exit.json`实际Game2008于2026-10-31T20:13:54.882511500Z正常exit0。root另确认keeper无failure且线程退出，最终keeperseq14916，新鲜CAS14917释放成功；显示于20:17:48Z恢复1024×768，Steam20:20:34Z仍后台离线。后四项应连同root的独立原始闭场文件入最终机器记录，不把exit0或旧launch的Steam凭证代替闭场实读，也不拿闭场回填新启动资格。

本段原片`take-01.mkv`、`take-02.mkv`、`take-03.mkv`已由root封存。大原片、大保存、全部中间JSON和第三方全文不入Git。保留期限与容量继续按项目通用存储策略复核，活跃剪辑输入仍受保护。

用户六点返工在[新版导演稿](../../episode-01-dong-zhuo.md)逐项对应：无下一期；玩家自然口吻；结尾模组宣传与工坊搜索；战斗精简；无未拍机制预告；补齐真实人物结局。新片8分24.757秒，41,625,420B，SHA256 `a023cc2dd16f5fdbe66421cab149e6fbd696f9a7c067c2f05faa6df7d0e23b9b`。成片为本机根目录下`episode01-dongzhuo-reworked-review.mp4`，同名前缀字幕与封面另存；[交付快照](delivery-snapshot.json)、[制作元数据](edit-metadata.json)、[最终旁白](narration.txt)已绑定新字节。正式run005的plan/build、18帧自动audit、17帧待审包、全片解码及最终validate均完成；人工签核仍null，不沿用旧片审查或冒称人工完整1倍速批准。旁白继续Edge TTS7.3.1 Yunjian，rate−12%、pitch−8Hz。

[存储闭场](storage-close.json)实际整包8,163,221,929B，edit03为846,613,154B，均在共享8GiB及0.8GiB剪辑预算内；复核期限2026-11-02T19:00:00Z。原片未重复复制、未删除，旧470秒视频SHA仍不变。新片只本地交付，未上传外部平台。
