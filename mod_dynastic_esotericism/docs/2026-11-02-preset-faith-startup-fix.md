# 两项预置信仰开局创建修复

`machine_id: desktop-3fevhd2-1c74096080`。观察日期：UTC 2026-11-01／本地2026-11-02。本说明记录修复行为与本地验证范围；尚无新的实机通过结果。

## 症状与确定的配置缺口

用户在自定义统治者中选择白绮或繁育，进入战役后信仰被换掉；进入信仰列表也找不到两项预置。用户同时明确要求繁育默认宗族化。

已发布0.2的相关定义与本轮Root读取的远端master一致。`common/religion/faith_types/des_faiths.txt`定义了`des_procreation_faith`及`des_vivhite_faith`，分别绑定同名main Rite，两项均为`historical = no`。旧发布树没有`history`目录，也没有初始信徒；未给这两Faith显式开局创建历史。Rite自身的`create = yes`、`convert = yes`不等于它所属Faith已经created。

本轮读取的原版依据：

- `game/history/faiths/_faith_history.info:7–11`说明，没有信徒且未created的Faith不能转入。
- `game/history/faiths/00_abrahimic.txt`中karaism、malabarism在`867.1.1`设置`created = yes`；原注释明确，否则早期书签的信仰列表会隐藏该Faith。
- 原版GUI通过`Faith.IsVisibleInGui`过滤信仰列表。

这些依据确认旧配置缺少Faith创建状态，并支持列表缺失的原因判断。自定义统治者开局替换的具体引擎分支、替换时点及修复后的实际结果仍待实机读回，不能写成已经跟踪或通过。教义中的`can_pick`是选择条件，也不能仅凭该条件认定“开局自动改信”已被证明。

## 最小修复行为

新增`history/faiths/des_faiths.txt`，两Faith根分别设置：

```text
des_procreation_faith = {
    867.1.1 = { created = yes }
}
des_vivhite_faith = {
    867.1.1 = { created = yes }
}
```

该历史文件自867.1.1起标记两Faith为created；保留`historical = no`、原main Rite及原生开局机制。无需强改玩家、制造信徒或指定NPC改信。

本轮静态核对34个教义键存在，同一Rite内没有重复group。两项Rite原本均有`des_doctrine_dynastic`，其中繁育的默认宗族化已经在原定义中，不应另改用户教义。`common/scripted_effects/des_initialization_effects.txt:60–71`仅在None及Dynastic都缺失时补None，已有Dynastic不会被这段初始化覆写。本修复只补Faith创建历史，不借机改动这些教义或选择条件。

显式构建清单与校验需同步包含新历史文件：预期开发树35→36文件，正式发布staging 56→57文件。Root已同步四份活跃验收JSON中的产品文件数断言名56→57；最终数量和消费闭环仍以实际构建/回归输出为准。

## 测试真实状态

| 范围 | 实际结果 |
| --- | --- |
| 本地release包四类回归及Quarkus verify | 最终源字节a03：原0、未超时，31.127177953720093秒；22/22，failure/error/skip均0 |
| 严格编译及打包 | 所构建模块使用javac `-Xlint:all -Werror`；Quarkus package实际成功 |
| 显式清单、开发树及正式staging | 开发36文件；正式57文件、1,945,617 B；真实build→staging→manifest/ZIP→既有独立AST consumer原0 |
| 历史文件及语义回归 | 两Faith created、原main Rite Dynastic及初始化NOR不覆写均已核；缺history、created=no、缺created、错Faith、晚日期及重算manifest后篡改均拒绝 |
| 四份活跃JSON消费者及更广回归 | 已与Java消费者同步；完整模块及公共消费者范围仍待远端DES CI，不由本地四类选择外推 |
| 自定义统治者及信仰列表实机路径 | **未执行，不能声明通过** |

实际命令使用默认`mvn -o`，根reactor选择`-pl :dynastic-esotericism-tools -am verify`，并明确限定`-Dtest=ReleaseBuilderTest,ReleaseLocalizationTest,SectPresetValidationTest,DefaultMavenTest`及`-Dsurefire.failIfNoSpecifiedTests=false`。最终原回执为本轮源测试包`logs/FIXED-RELEASE-a03.original-wait.actual.json`，开始于2026-11-01T19:39:06.579153Z；a03保留上游LF最终源字节。

修前`BASELINE-REACTOR`真实原1：新增实际staging断言指出两Faith缺少创建history。首个单模块GAV环境原1单独保留，不记为产品断言失败；首轮修后history漏BOM也真实原1，补齐BOM后再通过，未降低原规范。原日志及XML均保留；本地包实测峰12,719,820 B。

本轮只获准不超过128 MiB的例行源测试包，没有Game准入。旧C36的期限不能复活，也不能用本次编译或staging成功追认旧场或新实机通过。

## 手动复核建议（均尚未执行）

1. 自定义统治者选择白绮，进入正常新战役后核对仍为`des_vivhite_faith`及`des_vivhite_rite`。
2. 自定义统治者选择繁育，进入正常新战役后核对仍为`des_procreation_faith`及`des_procreation_rite`。
3. 打开信仰列表，分别确认白绮、繁育可见，并可打开各自信仰详情。
4. 繁育开局完成正常初始化后，确认默认仍为`des_doctrine_dynastic`，未被补成`des_doctrine_none`。

这四项记录用户症状的复核范围，不新增验收门禁；执行后据真实读回填写结果，失败原件保留。
