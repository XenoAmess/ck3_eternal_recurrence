# 共享 CK3 存档读取核心

Java 21 叶模块，供宗教礼仪融合与宗族化密教的 Quarkus CLI 共用。唯一的 Clausewitz lexer、AST、流式选择器和 Rakaly 进程生命周期在此维护；叶模块不启动服务，不进入游戏载荷。默认命令行 Maven 要求不低于3.10.0。

在仓库根目录执行，先按当前机器存储策略批准输出根及默认 localrepo 中本模块的安装占用：

```text
mvn -f java/ck3-save-core/pom.xml -Dsave.build.root=<approved-shared-build-root> install
```

两款工具各自的完整 `verify` 随后消费 `org.xar.ck3:ck3-save-core:0.1.0`。三条现有产品 CI 均先实际安装叶模块；没有 Python fallback。编译使用 `-Xlint:all -Werror`。

两款 CLI 的 `inspect-save-v4 --inputs <request> --output <report>` 使用严格 Request4 和 `ck3-save-inspection-v4` 报告；未知字段、错误整数类型、旧 shared v3 请求与命令均拒绝。选择项采用显式实体种类、表路径和规范十进制 ID；支持 Actor、Rite、Faith、Religion、Dynasty、House、Coat of Arms，以及有界命名路径投影和重复出现记录。结构目录检查必须显式指定 `structureRoots`；启用时非空，关闭时为空，只遍历所选命名根的有限相对深度。不得通过扩大节点／键限额转为全世界转储。

RRF既有 `inspect-save` Request2／Report2和fixture Request3合同继续由薄适配器提供；v2原子字段为 `raw`，v4为 `token`，比较时须尊重版本。DES原来的预置信仰校验也使用同一parser。

工具校验实际加载的JAR或classes与内嵌producer源码，并分别报告仓库源码和加载代码身份。实际decoder的退出、流SHA和原保存身份另行核对；报告不产生游戏业务通过结论。真实验证及已知边界见[产品续工记录](../../mod_religious_ritual_fusion/docs/live-review-resume-2026-10-26.md)。

DES 另提供两条共享读取入口，均采用 `--inputs <request> --output <unused-report>`，请求上限64KiB、报告上限1MiB，失败不截断记录、不覆盖输出：

- `inspect-save-selected-v1` 消费同一 Request4，但要求关闭结构 census。`ck3-save-selected-v1` 保留全部所选 Scope／RecordObservation／显式投影、原完整记录 AST、metadata 原有 DIRECT_SCALARS 语义及原生词元摘要；报告不包含 inventory，明确标记 `OMITTED_NOT_QUALIFIED`。旧 `inspect-save-v4`／Report4 和其 inventory 字段不变。此入口不授予全部人物、全部 House 或 scalar-skipping census 资格。
- `inspect-save-opinions-v1` 消费 `OpinionInspection.Request` 版本1。请求显式给出匿名意见表路径、命名 modifier、原始 `value`／`modify` 期望字符串，以及唯一有向 owner→target 对和 `EXACT_ONE`／`ABSENT` 枚举；没有产品或场次 ID 默认值。每行上限512KiB，匹配行合计上限256KiB／64行，方向上限64。完整流遍历到 EOF 后，返回全部匹配方向的原完整行 AST及命名 modifier AST；反向意见、其他 modifier 不计为目标来源。缺失、重复或错误类型的 owner／target／modifier／value／modify 拒绝，重复命名来源无法满足 `EXACT_ONE`。

两种新报告记录实际 decoder 原进程等待、原退出码、时间、stderr、完整流字节数／SHA及前后相等的加载代码／源码绑定。共用原 decoder 的 unknown-key=error、512MiB／120秒／64KiB stderr 限额；非零退出、unknown 诊断、截断、超限不形成成功报告。`SelectedInspection.readReport`／`OpinionInspection.readReport` 是有界严格消费者，重新校验所选覆盖、方向、原 AST 与来源计数，不信任附带数量声明。

显式选中表的直接 scalar 子项只接受规范 NativeId 键和精确原始 token `none`。它表示空槽，不进入旧 inventory 的完整 block ID 集合；可选选择返回 NOT_FOUND，required 选择仍拒绝缺失。其他 scalar／非法 ID／重复空槽或 block 与空槽冲突均拒绝。该守卫不扩张为成员 census 或全部历史角色资格。

共享 Java 21 核心的 FileLock／文件 Pin 前后核对不等于 Win32 deny-write、retained Save custody 或 SDK 来源资格。现有限 operator 必须继续持有自己的已核 OS 句柄，并在调用 API 前后执行同一 runtime／SDK pin／custody／decoder／源码身份检查；可在外部已持有句柄期间调用这两个 API。这里不复制 Windows FFM、不修改 SDK，不把离线读取授为游戏业务 PASS。
