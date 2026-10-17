# R195：GUI 静态来源 owner 的补员开关已真实读回

2026-10-17，机器 `desktop-3fevhd2-1c74096080`、source `611bc985ae95f477dd7314df11f8602cd1e595f3` / a33。Root 完成 R195 R07 control 32个实际自然日后，关闭 payment/natural 实验采样门，再经唯一 a43 control opener执行三请求。该control没有拍摄 Start/Finish；没有调用补员toggle或provider，之后沿原normalSave/exit闭场。此记录不授R07付款、补员ADD或拍摄资格。

新 `static_direct_owner_switch_12004` 已在真实游戏 family 中available：可见 index220 / path `0/0/0/2/3/0/0/0` 与隐藏 index238 / path `0/0/0/3/5/0/0/0` 两处均为 owner31254、military组件非空、raw4A9=1、enabled=true、basis `raw_military_byte`，且双读稳定。这里只读**静态来源候选的 Character 开关**；`current_variable_table_observed`、`native_receiver_selected`、`provider_invoked`仍为false。

## 同帧与完整 census

实际PID29000、creation FILETIME134366728035105406、generation1、actor31254、episode `native-31254-d5ea28d864bc`；date53148960、native revision109、public revision110、snapshot `native:109`。GUI frame为pump96426/ticket65/thread29904，owner thread/frame/GUI owner均稳定。Root独立before/fence相同。本消费读取Root交接的239540B endpoint一次，用同一份bytes核SHA、parse并无损gzip保存；全部507行census经复制的实际生产strict consumer消费，未读Driver，未裁成两行伪树。

原 endpoint SHA `4327754594ed01fa69d74589cb7a49f23b0e425c2146548c687cdda010d9ecdf`，RESULT1566B/SHA `a6863011a3233e448fdaa01403bdc770d36d2b33cfecd8fae168d8d8bfdf89ac`。便携原字节在[无损gzip](acceptance/2026-10-17-r195-static-owner-switch/OPENER-ENDPOINT.actual.json.gz)；[PACKET](acceptance/2026-10-17-r195-static-owner-switch/PACKET.actual.json)保留原Root pins，展开后必须严格等于原239540字节。原展开endpoint未重复复制。

| 层次 | R195实际结果 | 不得推出 |
| --- | --- | --- |
| full candidate | 原depth8/read51/pass1 unavailable | 不能改成full成功 |
| continuation | available/stable；depth8 definition count3、first key635 index0，mode1/flag1/direct非空 | count3不是三个receiver |
| direct owner | +218为31254，经完整Character registry/ID/Char magic核对 | 不是Army18，也不是direct对象本身等于Character |
| raw开关叶 | military存在，raw4A9=1，enabled=true | 不是toggle刚执行/状态转移成功 |
| provider | **provider_present=true**，vtable/slot2 RVA均null | mode1不进入dynamic provider分支，presence不授地址解引用或执行 |
| parent | static_direct_terminal at8；parent未读，9–11未读 | 不是null_end或更深definition缺席 |

原版 `.4 3AC1C00` 的mode1复制direct值并AL1；只有mode>=2才沿provider槽分派。本场即使provider字段present，读口也没有解引用它。与R194的provider_present=false是实际来源数据差别，不能解释成新provider已运行。

## 与 R194 和实验采样门的区别

[R194](episode04-r194-r06-frontier-12004.md)已有depth8静态来源，但a32没有新开关叶，raw4A9当时unknown。R195新叶available才首次在这个GUI来源路径证明raw1；不同runtime/date/source，不能据此声称R194→R195发生0→1切换。payment/natural实验采样门OFF与这里military补员开关enabled=true是不同状态，彼此不矛盾。

当前可以复用的是：同来源可见控件的静态owner为真实Character31254，其补员开关输入在本帧为enabled。没有观察临时variables表或最终native RCX，不给正式C++类名补证；不能凭此自动执行provider/OnClick、授CanReplenish或实际ADD。后续动作仍须沿原固定source dispatch和独立新后验；本场没有做该动作。

## 运行环境边界与验证

Root报告首次直接运行封存a43默认preflight时exit1：`ModuleNotFoundError: qualification_contract`，位于 `owner_film_candidate.py config → validate_native_provenance`。失败发生在SDK请求之前，没有opener。Root随后用显式a33 `--adapter-root` 的通用runpy launcher运行，脚本原字节未改，实际live exit0及同帧RESULT如上。这里区分**裸命令失败**与**绑定导入环境后实际成功**；不能把旧裸命令写成已通过。当前launcher的具体argv/独立小回执若尚未交接，仍只作为Root运行报告引用，不伪造file pin。

独立 [verify_portable.py](acceptance/2026-10-17-r195-static-owner-switch/verify_portable.py) 以stdlib bounded解压核对原bytes/SHA，再用源提交611的原生产strict consumer消费完整507行，检查identity/before-fence/opener后验/owner join/raw字段/未执行资格。所有失败判断用显式异常，`python -O -B`有效。实际native总读次数/字节/耗时未导出，仍为null；策略预算不能替代实际消耗。未重跑旧测试矩阵，无新SDK/Driver/EXE/save读取或主树写入。

短口播：这次已经从真实军务窗口读到罗贝尔来源的补员开关值1。两处控件都在第八层找到静态直接来源，完整507行和前后帧校验通过；这里只证明当前开关读值，还没有点击切换或证明兵员补充。
