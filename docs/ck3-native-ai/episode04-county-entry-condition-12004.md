# R04：原生县进入条件24E2230的完整结构（1.20.0.4）

R0180的2635→2645已经真实提交，双definition1B为1，native B100，但同帧
`condition.passes=false`。这不能用“敌方抬军点2645”解释成县损耗正例；
也不能直接确定是哪一个内部谓词拒绝。本专题把该条件完整body的结构闭合，
不把未知callee命名为敌友、县所有权或补给连通。

来源机器desktop-3fevhd2-1c74096080，exact1.20.0.4/Steam25734779，
EXE SHA98702f88a547cde2eaf29a85f93b85f68ee4cf8148336a4f7afaeb75319dd518。
本次实际读取24E2230..24E23D4，420B/115指令，SHA
d011c6bb38172950e99324f1fa7157d0083cbe5316587b7945ed5b168f80370c。
先通过native_research_plan check，再有限21reads/240Bmetadata/420Bcode；
唯一unchained exactentry，28个内部jump全部落在本体指令边界。没有callee读取、
新EXE整hash、SDK、游戏、桌面、构建或主仓写入。历史.3偏移没有用于定位本体。

## actual mode1必须依次满足什么

现有reader从同一CArmy→CUnit+174解析完整Character，CCharacter+18核FullID；
source为Unit+20，target为完整stored route.front()解析的Province。
mode由CArmy+1D4==0取1，否则取0。现R0180为mode1。

| 本体位置 | 必须通过的条件 | 现有wire是否发布 |
| --- | --- | --- |
|24E2257..2269|source和target的definition+1B都非0|已发布；本次1/1|
|24E226F..2289|source+848和target+848对象指针不同；source对象非null|未发布；不是省份ID不同就足够|
|24E22AE..22B5|2C09DF0以actor/source县对象为显式参数，AL必须true|只有最终bool，没有此子结果|
|24E22C2..22F3|target对象非null；2C09DF0(actor,target县对象)第一次为true|未发布|
|24E22F9..2303|target县对象+3E0为0x436F4461|未发布|
|24E2343..234A|2C09DF0(actor,target县对象)第二次也为true|未发布；不把两调用合并成一次观测|
|24E234C..23B1|遍历target对象+40数组、+4C计数。每个非null邻接N经24D4ED0(N)后，2C097F0(actor,返回值)都必须false|未发布；任一true拒绝|

全通过才在24E23B3返回AL1；false汇流于24E23B7。这里的县身份是Province+848
原始对象指针，函数没有读取county FullTitleID。占领查询的county_title_id来自
holding的de_jure_parent，不是这两个指针的直接观测，不能替代该相等比较。

mode1下target+88/+8A无论是否非0，都走第二次2C09DF0调用；不能把这两字节当
mode1独立拒绝条件。mode0另要求两字节都0，并用28BFD80(actor)返回对象+18与
各县+3C8所指对象+30比较：源/目标要求不等，邻接存在相等或null则拒绝。
比较的正式游戏语义仍未知。

最小唯一未闭callee是**actual4 2C09DF0**，调用点24E22AE/22EC/2343，
显式RCX=actor、RDX=县对象、AL被测试。其formal语义、内部字段及sideeffects未读，
不能自行将true改名为“敌方县”。邻接链24D4ED0→2C097F0同样未展开。
本包不自动跟进这些callee。

## Root现在可用的精确只读顺序

先用新的暂停snapshot取得actual revision、actor、Army18当前位置及完整route。
当前到达2645的后态必须重新取值，禁止把本页旧revision5写入未来请求。

```python
{"tool":"ck3_query_army_strengths","arguments":{
 "army_ids":[18],"expected_revision":fresh_revision,
 "profile":"ordinary_core_v1"}}
```

上述现有口只读**stored第一边**；若已到达且route为空，condition应为
unavailable/no_stored_route，不能理解成false或继续沿用2635→2645。

接着以实际仍active的War4查询具备来源的候选集合：

```python
{"tool":"ck3_query_war_occupation_targets_v1","arguments":{
 "war_id":4,"expected_revision":fresh_revision}}
```

只从available且collection_complete的实际holding行取province_id、county_title_id、
legal_holder/occupier及war-side；若该场口返回unavailable，不补成空集。
这些字段用于缩小正常军事候选，不证明24E2230通过。尤其同县内换Province可能在
指针相等处直接拒绝，值得优先比较已观测不同county_title_id的合法候选，但它仅为
筛选线索，不是对24E2230的充分证明，也不指定尚未读到的ProvinceID。

只使用当前capabilities已经广告的preview步骤：

```python
{"tool":"ck3_execute_step","arguments":{
 "step":f"preview-move-army-18-to-{observed_candidate_province_id}",
 "expected_revision":fresh_revision}}
```

步骤未广告就保留接口缺口，不能伪造任意target支持。available合法preview必须绑定
当前Army、起点/目标、日期和revision，真正firsthop是去掉可选起点前缀后的route[0]。
现有preview没有任意候选firsthop的countyboolean；因此**当前MCP纯只读不能保证
提交新Move前筛出true**。本次已实际Move的false边不再重复Move/Resume试运气。

要最小补这个确实阻塞的观测，下一版可在既有合法preview结果加可选的
preview-firsthop县条件child：复用现有四参数24E2230与同一actor/mode，绑定真实
preview firsthop，保持owning-thread、FullID和frame校验，不调用执行器、不改stored
route、不新增MCP端点。其source必须与current_stored_route_first_province区分，
不能把假设路线混入现有strict字段。本包只提出此窄seam，没有实现或授当前a09能力。
若目标是解释false原因而非只筛出true，先展开唯一已知2C09DF0比加大范围试走更有信息。

## 实际拍摄和验收边界

当前一边可保留为真实“有B100但条件false”的控制素材；未观察countywriter时，
只说没有取得R04 positive，不能说整个县损耗0。新positive仍需真实到达时正常准入、
实际特殊flag、完整writer窗口及同一writer unique physical DATA槽正减；预算、
地图标识、敌方抬军和Army净少人都不补因果。

完整28分支分组与actual source在同名evidence目录。verify_source.py仅复验归档
字节、指令拼接、rel32/短分支目标和结构合同，不运行CK3，不重审live raw，
不授R04 positive、全县总额、clean、动态镜头或人工签核。
