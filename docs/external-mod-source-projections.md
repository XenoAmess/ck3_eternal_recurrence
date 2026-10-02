# 独立 mod 的原版覆盖迁移与可逆投影

2026-10-02，从 [More Tenets Slots(XA) 迁移](https://github.com/XenoAmess/ck3_mod_more_tenant_slots/blob/master/docs/migration-plan.md) 提炼。产品源码、配置和实机报告留在独立仓库。

游戏大版本升级时，先冻结 launcher/build/EXE 和依赖原版文件。覆盖审查必须同时比较文件路径、数据库目录、顶层定义及 scope，不能只检查原文件是否还存在或 supported_version。不同文件名仍可能覆盖同名定义；原版删除一个文件或将 ID 移到另一数据库时，旧 mod 的完整副本可能重新引入已退役类型。

本次 CK3 1.20.0.3 磁盘实例：核心教义从 `common/religion/doctrine_types` 移到 `tenet_types`；创建窗口从 `window_faith_creation.gui` 换成 `window_rite_creation.gui`；信仰创建钩子的 root 由角色改为信仰。这些事实要求重新选择产品扩展入口，不能简单复制新版原版全文进旧目录。具体哈希和产品修复由独立项目报告绑定，不构成所有 mod 的兼容结论。

`tools/ck3_text_projection.py` 提供不依赖 CK3 进程的通用原语：忽略注释和字符串内花括号的结构扫描、唯一命名块定位、SHA 绑定的最小文本替换，以及反向恢复校验。使用者显式传入原版内容、规范化 SHA 和替换集合；工具没有游戏路径、产品 ID、宗教行为或操作者配置。

生成器先检查原版 SHA，再只替换已审阅锚点；验收时逆向移除产品变更，恢复内容必须仍匹配原版 SHA。源文件变更、锚点重复、缺失和额外修改均拒绝，需要重新审阅。SHA 定义为移除 BOM、规范化 LF 后 UTF-8 的摘要，原始文件 SHA 应另记入输入账本。

该结构扫描仅证明引号/花括号与投影一致性，不验证 CK3 语法、scope、费用、UI 布局或原生执行，也不能替代 `open_kaishek` 预验和真实 CK3 验收。调用方自行维护产品合同、发布 allowlist 和实际通过边界。

实际反例见独立项目 [R0001 原生日志](https://github.com/XenoAmess/ck3_mod_more_tenant_slots/blob/master/docs/evidence/live-R0001.json)：将 GUI `spacing` 写成向量 `{ 20 25 }`，结构扫描和投影恢复均通过，CK3 原生读取器仍报 `Malformed token`。该字段在此控件上接受标量。修改控件类型或属性值时，原版相邻控件只能帮助建立假设，最终须由真实加载日志验证属性类型；不能把可逆文本投影称为引擎语法验收。

另一个实际反例见 [R0003 原生状态读回](https://github.com/XenoAmess/ck3_mod_more_tenant_slots/blob/master/docs/evidence/live-R0003.json)：产品源文件中 define 和同名 script value 都写成 100，原生执行 `GetDefine` 却返回 100，`ScriptValue` 返回 3。产品 `mts_*.txt` 排在原版 `pam_values.txt` 前面，后者覆盖同名 ID。修复为排在原版后面的文件名，同时检查原版该 ID 的定义所有者。这个单模组实例不能推出所有数据库的统一加载规则；其他 mod 的同名覆盖仍须独立审阅。

验收关键配置时，除了源文件和冻结哈希，还应记录真实加载后的有效值。对有镜像 script value 的 define 分别读回两者；对列表、槽位和创建结果再检查原生 UI、费用变化与存档实体。源内容相同不等于有效运行值相同。原生调试日志是本次实例的读回通道，不能将控制台文本已粘贴、按键已发送或命令 ACK 当作效果成功。

受管桌面运行的屏幕所有者心跳必须使用当前任务的 `last_sequence` 做 CAS，并保持租约新鲜。首次失败后仅添加序号不能续约已经过期的租约；先按合同释放自己的旧 claim，再注册新任务。运行器须在续约失败等异常路径中关闭自己启动的进程，并写出退出回执，避免 Python 已结束而游戏继续占用桌面。产品冻结输入变化应分配新 run，保留旧 RED。

槽位验收还必须区分生产列表、可达布局与消费者索引。独立项目 [R0004](https://github.com/XenoAmess/ck3_mod_more_tenant_slots/blob/43765b0ffa53ea84e398e02e64086915be387624/docs/evidence/live-R0004.json) 在 CK3 1.20.0.3 实际读取到 100 个原生教义槽，拖动纵向滚动条也能到达第 100 槽；点击该槽却发生原生访问异常。冻结 EXE 的只读调用链显示，打开窗口的消费者使用教义槽号索引另一组教条条目，未在读取前检查该数组范围。不能把 producer 的数量、同名的索引 getter、可滚动显示或前几槽成功，直接外推成全部槽位可操作。

因此，扩容控件的验收应分别记录：实际列表数量、首尾及跨页可达、首尾实际选择、费用与条件、创建结果，以及保存和重载。空槽可保存也不能代替空槽打开/选择安全。优先操作已经审阅的滚动条；鼠标滚轮产生输入或页面移动，不能单独证明末端已经到达。按钮按住期间的坐标换算工具可能拒绝移动以避免意外拖拽；显式拖拽须在输入前将两个端点都按同一原始画面和实际桌面尺寸校验映射，并保留拖拽后的业务画面。

当 GUI 方法名似乎可复用时，可由隔离 debug userdir 的原生 `dump_data_types` 取得当前注册接口。独立项目 [R0005](https://github.com/XenoAmess/ck3_mod_more_tenant_slots/blob/eb27c6ba47e44b298382e4fd4c337b9d2e505311/docs/live-R0005-selector-investigation.md) 保存了实际导出的接口文件摘要和调查边界。方法名或 getter 的存在不证明参数语义兼容；缺少某个导出也不能证明所有内部方法都不存在。发生原生崩溃时同时保留进程退出码、崩溃日志和 dump，不能只依据没有 GUI 解析错误判 GREEN。该反例是测试方法的富化，不构成新的宗教 MCP 能力或产品修复验收。

独立项目 [R0006](https://github.com/XenoAmess/ck3_mod_more_tenant_slots/blob/99e78c6/docs/live-R0006-empty-slots.md) 还复现了编辑控件容量和追加粘贴的问题：1.20.0.3 控制台长命令被截断，保存名称未先全选时则插入旧内容中。剪贴板写入成功不等于目标文本完整。输入后应先用不同的哨兵覆盖剪贴板，再从目标控件复制全文；全文不一致时必须停止后续 Enter/保存，而不是仅抛出错误后继续动作序列。按 exact-build 和具体控件记录已实测容量，不能将控制台长度上限外推给所有编辑框。保留输入失败和修复回执。

独立项目 [R0007](https://github.com/XenoAmess/ck3_mod_more_tenant_slots/blob/3fbeed4/docs/live-R0007-cold-reload-culture.md) 分别读取了基础文化 cap 和原生 UI 的时代加成上限。基础 define 是输入，实际可用上限还可能包含时代、修正或其他原版条件。验收应读回有效值，并以超过默认上限的真实入口、费用支付和业务状态验证扩容。通过原生 effect 准备夹具可能触发原版冷却；应先核对权威定义，区分冷却阻断与容量阻断，记录夹具解除条件，而不能削弱产品原生限制或把开始建立称为多年后已完成。

2026-10-03 的独立项目 [R0008](https://github.com/XenoAmess/ck3_mod_more_tenant_slots/blob/master/docs/live-R0008-selector.md) 进一步区分了尾部空槽与中间空洞：该实例实际读取到 100 个信条槽和 128 个教条条目，第 100 槽可以打开原生候选并选择，真实已选索引为 `[0,1,99]`，虔诚费用从 4837 变为 5587；原生合法性检查仍报告 `Absent is not allowed`。R0006 的两个真实信条加尾部 98 个空槽可创建保存，不能据此外推有空洞的选择序列也能创建。扩容测试应分别覆盖尾部空槽、中间空洞、连续选择和最终保存；末端选择与费用变化成功只证明对应操作，不代替创建合法性通过。这个 exact-build 反例不能推出其他列表或版本的统一空槽规则。

R0008 同时仍为加载检查 RED：`visible=no` 的隐藏教条也会解析默认 `_name`/`_desc` 本地化，隐藏性不能省略加载所需元数据；教条组按原版合同解析 `_name`。GUI 通过 `AddScope` 传入的 scope，应按原版 ScriptedGui 合同用 `saved_scopes` 声明。产品已依据原版 `doctrine_types`、`doctrine_group_types` 的 `.info` 和 `pam_scripted_guis.txt` 修正声明并补齐两种语言的空白本地化，具体生成源码和收据见独立项目 [候选说明](https://github.com/XenoAmess/ck3_mod_more_tenant_slots/blob/master/docs/selector-repair-candidate.md)。此修正目前只有静态检查通过，须以新源码冷启动确认原生日志，不能用 R0008 的旧冻结输入或静态 BOM/结构检查冒充实机修复。框架只提炼加载合同和验收边界，不搬入产品教条、存档或专有夹具，也不将本产品结果外推为所有 mod 通过。

验证入口：`python tools/test_ck3_text_projection.py`，覆盖真实生产投影/恢复路径、原生 controls 保留、变更拒绝、歧义锚点及注释/字符串扫描。

磁盘空间不足时，先区分可再下载的软件缓存与必须保留的研究材料。源码、冻结构建输入、存档、mod/Workshop 资产、夹具、原始及中间素材、dump 和失败 attempt 都不能作为垃圾；目录名含 `Temp`、`runtime` 或 `cache` 也不构成删除依据。已安装依赖和本地构建 wheel 继续保留，删除下载缓存不能改变 venv 或依赖版本。只对已确认可再生的具体缓存范围盘点，校验解析后的绝对目标仍位于该范围，拒绝符号链接、junction 与其他 reparse 路径；逐文件取得独占删除句柄并读回删除结果，锁定、近期或用途不明的内容跳过，不停止游戏或其他任务。

2026-10-03，本机在用户授权的并行 C 盘清理中删除了 443 个老于七天的 pip HTTP、npm 下载、NuGet HTTP 缓存及未使用的 NVIDIA App 下载安装包，共 `2,064,770,145` 逻辑字节，失败为零；项目、冻结输入和全部运行证据未删除。逐文件计划、删除回执和原始容量盘点留在本机外置 `_runtime/c-disk-cleanup-20261003-a01/`，公开文档只提炼方法。报告分别记录删除文件量、句柄返回的文件分配量和开始/结束空闲容量；并发验收写入及无损压缩会改变空闲量，不能将空闲容量差值全部归因于垃圾清理，也不能把分配量简单当作实际回收量。

更换上游 Workshop 主包时，保留旧上游、旧维护版本和新上游三份输入，逐项重评维护差异。每项修复应记录旧提交、文件和对象、原故障、新上游代码依据，以及保留、重写、上游已修复或不再适用的决定；新增兼容遮挡和完整原版文件投影同样纳入。补丁无冲突只能证明文本可应用，不能证明新 scope、数据库提供方或运行语义仍兼容。迁移应从新上游构造候选，保全其新增逻辑，避免旧维护整文件覆盖；源码、工具、存档派生器和未合入候选分别记录实际去向。

组件关系以用户指定来源和当前物品页核对，不能因主包 ID 改变而沿用或自行删掉依赖。匿名页面或接口不可见时，保留失败回执，再用已授权的登录态客户端核对；不能据匿名失败认定物品不存在。下载结束立即恢复 Steam 离线，随后以客户端下载结果、installed/latest manifest 相等、完整文件清单与 SHA-256 冻结精确输入。网页加载成功、订阅按钮状态或下载命令 ACK 均不能代替此闭合。

原包的 embedded `.git`、编辑器目录和 authoring 素材保全为本机 raw 证据，运行树与 GitHub 提交使用显式资源投影。空间不足时，可对关闭的旧快照做无损 NTFS 压缩，记录逻辑 bytes、文件集合、mtime、file ID 与哈希检查的实际覆盖。相同内容也可在已冻结且不可变的 raw 快照之间核验后硬链接，逐文件记录来源与身份；禁止链接会被 Steam 更新的缓存。硬链接共享内容及属性，不能原地编辑、重编码或设置只读来改变旧证据；修改前复制到独立工作树。物理空间变化与逻辑内容校验应分开报告。

Windows 上核验冻结文件身份时，前后都使用 `Path.stat(follow_symlinks=False)` 或 `os.stat(..., follow_symlinks=False)`。本机一次压缩前的只读准入把 `DirEntry.stat()` 与 `Path.stat()` 混比，前者的 `st_ino/st_dev` 实际返回零，后者则返回真实非零身份；内容哈希、大小和 mtime 均未变，这次拒绝发生在任何压缩之前。保留拒绝回执，在新的 attempt 中改用同一种真实身份采样，随后完成全文件哈希、身份、大小、mtime 和文件/目录集合核验。零值不能冒充身份保全，也不能仅凭这种 API 差异认定文件被修改。Python 官方文档明确说明 Windows `DirEntry.stat()` 的 `st_ino/st_dev/st_nlink` 为零，应调用 `os.stat()` 获取。[Python 3.14 文档](https://docs.python.org/3.14/library/os.html#os.DirEntry.stat)

关闭 Windows 休眠属于系统功能变更，不能由“清理垃圾”自动推定授权。已有明确授权时，由该操作的 owner 调用原生 `powercfg.exe /hibernate off`，保留执行前后的 `powercfg.exe /a`、命令退出码、休眠文件原始逻辑大小及操作后是否存在；恢复命令为 `powercfg.exe /hibernate on`。这些是命令说明，本轮文档与收尾线程不再次执行该操作。文件消失、功能状态和磁盘净空闲变化分别报告；并行写入或其他压缩存在时，不能把整盘空闲差值全部归因于关闭休眠。开启/关闭及可用睡眠状态查询的语义以官方文档为准。[Microsoft powercfg 文档](https://learn.microsoft.com/en-us/windows-hardware/design/device-experiences/powercfg-command-line-options#hibernate-or-h)
