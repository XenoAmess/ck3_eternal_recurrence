# 财政战争优先级只解析本次拥有的输入一次

实际采样调用链 OrdinaryFinanceCollector.current → new OrdinaryWarPriority.Input → observe(Input) 对同份 snapshot／root 连续完整解析两遍：Input 构造器校验后丢弃树，observe 马上再解码。本单元增加严格 byte[] 入口，使此唯一实际 caller 在克隆本次两份原输入、完成相同 parser／shape 校验后直接执行原私有算法；不会缓存下一调用／下一轮或接受 trusted AST。

新入口仍先 snapshot 非空并 clone，再 root 非空并 clone，之后才 parse snapshot 与 root。因此 malformed snapshot 加 null root 仍先是原 NPE，snapshot 解析／对象错误仍先于 root 错误。原 Input 构造器／getters、observe(Input)、FinanceRequest／finance API 保留，原算法、完整原件、未知字段／数值 token／Unicode、Observation 的防御性复制均保。Collector 只去掉 new Input，两个 DriverJson.encode 参数的左到右求值、真实 reads、current proposal 和异常边界不变。

实际与正式两个变体分别必要编译两 TU／16类，各首0。正式只在已有 Input 私字段读取优化上移同一入口和私算法委托，保原 null getter 失败表达式、finance／Saved差异，没有抄 active 全叶。没有新增类型；新增方法及现有 synthetic 变动不授整组 HCR。

独立新 Test 一 TU／3类、无 Helper／resource／props。实际和正式产物分别运行原完整四项，各首次4P／0F／0E／0skip、POST输入不变、CLOSE释放。真实非空 war／own与enemy armies／同帧root／strength cache 对旧新公开入口逐字比较完整输出与 sourceSnapshot，检查 member counts、full UInt32、大整数、小数 token 和 Unicode；另测 caller／getters／返回数组所有权、旧 finance 路径、NPE／双错误先序以及13类 malformed UTF8／JSON／shape。未以计数镜像或修改旧 Golden 当验证，不宣称整个 Golden 语义域已重跑。

actual whole4 ACTUAL1392B／`d319dea923093a822bbfc0547db71ee67f2634a4ac44ae80d1038d0afa4bf839`，CLOSE204B／`1f10017436dfda59060f35852e9cc8b4ba73923138ec57dc9a93c7e1fbc6e486`。formal whole4 ACTUAL1420B／`ee32766daef405b9ca92cf8ff2bfedda69314c54e2523011b3475091fe71d2e6`，CLOSE204B／`38b3a8b3e50a2076ea4eebb1091b8e0386c0a322b3f4be6c92ad49dbd0ed6084`。原件 D:/ck3-state/resume91-native-integration/life-postcondition-p0-20261112-01/war-priority60-{compile01,test-compile01,junit01,formal-compile01,formal-junit01}，机器 xenoamess-full-tower-eb9d2c1186，2026-11-12。

两处生产 edit 来自本地模型一次完整响应，owner只机械适配 CRLF 与正式既有字段访问；独立 helper实现上述真 DATA 测试，模型没有提供可采用 Test。软件与正式发表不授实际 Collector 分支已命中、墙钟收益或10秒目标；运行只在后继真正必要清洁边界由唯一 owner采用，不打断已经 BEGIN 的原动作。
