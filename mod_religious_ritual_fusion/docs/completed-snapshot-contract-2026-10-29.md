# 完成态冷载合同与实际验证边界（2026-10-29）

`machine_id: 4-8e1c2f1861`。观察时间：2026-10-29T03:18Z。本文记录软件验证和已取得的原始实机事实；新完成态冷载尚未执行，0.2.0尚未发布。

## 触发问题与修复

R0046实际完成同一Rite155／Faith106的免费原生编辑，并自然推进35天。完成态当前礼仪为允许离婚及宗族化密教；创建时的24项原始教义仍含禁止离婚。Faith106底层数据也保持禁止离婚及非宗族化，与礼仪覆盖分别存储。旧只读观察配方将当前礼仪与原始教义都固定为允许离婚，不能据此验证这个真实完成态，亦不能回改R0046首次冷观察失败。

现增加明确的`schemaVersion: 5`／`completed_snapshot`，从精确绑定的创建后及完成态完整RITE记录分别读取原始和当前离婚规则。两份报告须显式选择结果Rite，且selection、scope、record均证明完整读取；原始教义有序列表必须完整、无重复且跨两份报告相同。现有v3、v4保留原版本配方，没有自动升级或以Faith底层值替代礼仪值。必需的持久化PASS日志及原有来源、费用、核心与历史守卫继续保留。

钱包接受规范有符号定点字符串，包括自然月收入产生的`-0.4`。创建历史仍要求非负的before／after和精确的一次费用差。CK3实际省略已有钱包块中的零currency时读作零；缺块、重复字段、非原子值和脚本片段继续拒绝。Java生成器、FrozenFixtureReader、共享prepare入口、独立Selection及输入sidecar消费已同步。

## 实际软件验收

全部使用同一可复用V19目录与已有Maven缓存；默认`mvn`实际为3.10.0，`-T2 --offline -pl :religious-ritual-fusion-tools -am`。reactor包含SaveCore、RRF；DES未重新构建。Java编译及测试不代表游戏通过。

| 实际命令组 | 结果与范围 |
| --- | --- |
| v5局部AcceptanceFixtureTest、SavedSelectionTest | 24项，失败／错误／跳过均0；原wait0 |
| 最终完整Maven help:evaluate＋verify | SaveCore10＋RRF110，共120项，失败／错误／跳过均0，原wait0；同JVM环境诊断保留；Maven墙钟59.350秒，含外层监督62.684秒 |
| workflow完整五消费者模块 | 63项，跳过0，原wait0；56.964秒 |
| compatibility严格mypy完整模块 | 原wait0；4.269秒；修改的prepare helper另由五消费者内实际8节点strict回归覆盖 |

命令原件位于`C:/workspace/rrf-development-20261024/review-fixes-a01/review-validation-a19/metadata/final-wallet-CI-a01/`，`05`至`08`保留源码前后Pin、argv、cwd、原Popen wait与日志。首次wallet验收`03`因负例测试夹具在断言外构造非法语法而退出1，原失败JUnit保留；修复后`04`及最终v5验收独立记录，不覆盖失败。冻结Native a09未重编。

`05`局部实际重新编译RRF的21个main及17个test源码，SaveCore复用缓存；`06`最终verify全部复用编译缓存，重新执行完整测试及打包。最终应用JAR为306056 B／`9486fb2d376b0f9d9cdee28d09dcec0bc8cc97174992632c37d9b898fb487d0b`；启动器JAR仍为852 B／`88793bc997a68f734f69b19d6d26fddfc39b96bb2f256e4f9c8f5ec67b78ee56`。55文件、8308779 B的完整Quarkus图另有逐文件Pin；不能只比较启动器推断应用未改变。

## 实机原件及尚缺验证

R0046第35天检查点为`cold-R0045-retry-a01/checkpoints/day35.ck3`，69117980 B，SHA-256 `001e9f169c346037de53925b4adcfc0e28db3f4c5e038f077f1c30d1cb89a676`。精确绑定该归档路径的完整身份报告为`metadata/normal-close-a01/root-business-oracles-a01/C14/day35-archive-identity-a02/report.json`，683496 B，SHA-256 `223af8cecdcbee9957c0081ebd688771a593a520b4b2d812b84958e613473408`。

R0046已见四核心、30字符长名称、七美德／七罪恶、48名成员最终绑定Rite155／House174及35天维护后态。E1三名未绑定成员65872／65873／65874在完整存档中均为成年人；旧Root回复称其为“新生儿”不准确，原回复保留，追加更正原件为`final-Java-wallet-admission-control-a01/R46-REPLY-CLARIFICATION.actual.json`。

后续独立冷载须验证这些完成态身份、完整成员集合、原始教义和当前覆盖、对象库存与完整选定记录，并实际触发一次只读持久化观察取得日志。还需补齐禁用决议原因悬停、决议分组与顺序、列表滚动末端及返回、地图颜色的实际画面；无效组合创建按钮的真实tooltip仍是单独缺口。已经具备同Faith与跨Faith模式、无MTS三核心／有MTS四核心等代表证据，不重复融合或再等35天。R20与R42／R46不同分支的数据不能合成同一个对象通过。

R0046正常资源关闭资格成立，但公共run与Root原wait均为2，业务总case仍不完整。SDK另有保存绑定缺口，不能用原生文件存在抵扣SDK continuation。

## 存储与素材

C14原NativeSave lane及normal-close子预算实际超额，历史RED保留，后续输出停止；不提高旧帽或重新分类来追认通过。独立Java新准入04Z／256MiB累计帽与后续场次分开；新场次须重新观察容量、确认写者关闭和明确准入。

已精确回收R45的3824个可重建shader文件，分配160665680 B；另精确回收R42的3740个shader文件及R46三份与独立检查点字节相同的自动保存副本，合计3743文件、分配361857840 B。四份人工检查点、当前checkpoint、冷载输入和必要失败证据仍保留。只对精确原件执行持有句柄身份校验及删除，回收不退款历史gross／paid；后一批addback待下一次实际容量CAS记账。统一用途复核仍为2026-11-01T04Z。

两张R0046实机UI图已追加到同一Workshop3826756673，媒体总数15；原13张顺序保持。匿名页面与新CDN原图已核对，完整双语说明已回读；这是未发布版本的开发预览，公开下载仍为0.1.0-alpha。详细图片证据见[本轮媒体更新](../../../docs/workshop-metadata-revisions/religious-ritual-fusion/2026-10-29-long-name-and-DES-day35-previews.md)。
