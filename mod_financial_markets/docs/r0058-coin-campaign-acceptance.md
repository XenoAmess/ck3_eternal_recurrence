# R0058：宣发实付已核，双币后态与正常退出未通过

2026-11-21，machine_id: `4-8e1c2f1861`。R58沿`independent-seed19`的R57真实终档启动`coin-campaign-gui`；零新增自然日，已确认基线和付费后两份独立物理SAVE，均为raw53150352／金融日247。没有完成第三份terminal SAVE，本文不授双币成交、完整case、全产品或Workshop首发通过。

## 两份保存证明的宣发现金

基线17,256条完整记录与声明来源相符。输入声明A为coin87/native67122003、entity_type3，B为coin72/native17012、entity_type4；App17已经投影实体类型及绑定对象的原始namespace／身份，但独立具名实体来源仍未完成，不能仅凭输入、数字或币名授宗族／政治绑定格。

正常charter宣发后的同日保存与基线完成12项有限对账：

| 项目 | 保存前→后 |
| --- | --- |
| PRIMARY永久2/native54可用 | 8341→8241分，实际减少100分 |
| PRIMARY冻结 | 335→335分，旧预留未被宣传占用 |
| 交易所费用 | 实际增加100分；全部账户现金减少100分，合并费用后存量保持 |
| A广告累计 | 100→200分；B完整记录及其他投影金融记录保持 |
| 原义务 | 没有新增／缺失投影记录，旧whole义务无变化，未见负余额或负簿字段 |
| 真实角色字段 | 付费后存在charter nonce及带tick7的广告冷却；保留原typed值，不由字段计数推断实名触达或气泡送达 |

12项均为true，证明这次真实100分支付及相应有限状态变化；不等于完整宣发case／受众传播／宗族绑定通过。原比较的正常差异及各自退出码仍保留，不能把付费图变化当作应当全图不变，或将`all_original_steps_exit0=false`改写成全部原子步骤0。两份pipeline和原对账均保留，不为本文重复读取SAVE。

## 两笔BUY之后没有已保存后态

A、B两次BUY的后台GUI callback确有处理记录，但没有终点物理SAVE或可核订单后态。是否实际创建、冻结、成交、拒绝均为UNKNOWN；callback handled不等于金融成功，也不等于NoDispatch。SELL提交为0，因此双币四笔真实买卖格未通过。旧BUY／原命令及未知动作不得重放，不能以现有paid档早于BUY为由把它们视为“从未发生”。本文不授恢复、回滚或重试权限。

## 退出失败及行政释放

normalQuit在原在途状态下失败，原case还保留退出预留到达／pending Root phase GAP错误。公共run2、verify2保持。Native报告CK3 exit1；原retained同步句柄未signaled、OS退出码为null，没有原OS0证明。Host和keeper的0不能补成Game正常退出；`normal_close_qualified=false`、`typed_normal_exit_proven=false`。

CAS15973的resources[]是失败场的行政资源释放，不是正常闭场、业务或发布通过。原释放文件当时保留了公共allocator参数格式尚未正式消费的事实。后继公开argv校验修复已采用，40项检查通过；既有正式资源消费者随后实际成功，返回`actual_public_resource_closed=true`，该行政资源边界现已解决。原options-first argv及失败bundle没有重排或改写，也未重复allocate、STOP或release。`normal_close_qualified`、`typed_normal_exit_proven`、`business_pass`和`release_pass`仍为false，不能据此补授正常退出或新业务。两个已保存档、原报告、失败与UNKNOWN均保留。

## 本次输入资格与信用边界

Q42实际操作0，约138.77秒；profile233个开关、FileAPI范围845个TU、22个有限fixture。复用原缓存完成17个增量步骤，不能写成845个TU全部重编。App17、完整631项软件及原来源资格是已存在成果，本场没有重跑或追加测试数。它们不补本次正常退出、具名实体、订单保存或完整产品验收。期货零日GUI累计仍4/6；R57跨日真实SHORT／减仓事实继续保留，不混入本次虚拟币格。

## 原件索引

下列路径均为本机TASK根`C:/workspace/ck3-market-task-20261118`内的已完成元数据；表内哈希是对应JSON原字节，不是新SAVE读取或对原报告的改写。

| 原件 | 字节／SHA-256 |
| --- | --- |
| `coin22-paid01-financial-reconciliation.actual.json` | 7912／`2476bd44ea6c6d38a5135ffec9ec46ef87586bb500ffd83767b6d31851abcb02` |
| `coin22-baseline01-PIPELINE.actual.json` | 15845／`01da6cff5d6ff218004a571d1ba2918365f657d3fadf92d9c6cd0f3adb265376` |
| `coin22-paid01-PIPELINE.actual.json` | 15810／`e62088603fc9e9cc5751b9000765f7f99cbbc6a79387bf8ef9a0ed141dfaece4` |
| `R0058-closure-before-release.actual.json` | 7536／`c70ab9765ebe7de075866bc4fe7f2dbd679933a2f8b3a95307beaf12feffdc5a` |
| `R0058-closure-released.actual.json` | 2244／`81f582620efbb763201b97c446cdd088a319b6e47bf7af48b823bd69e93321bb` |
| `R0058-official-failed-resource-consumption01.actual.json` | 12370／`44334f40a86f7607742d355c4927552d9da45242abe40f44eb75e60d3db6a008` |
| `native-common-qualification42/Q.actual.json` | 16599／`adb1c3f8b37ea6d6e572c813337bb321c628daf688c51aead79b285cac282d1c` |

同一reconciliation关联原archive／App17 audit／Raw／whole；闭场文件关联原run／verify、normal-close及失败资源文件。具体合同见[双币宣发验收](coin-campaign-gui-acceptance.md)，后续仍按真实新结果增量推进，不给虚假总完成百分比。
