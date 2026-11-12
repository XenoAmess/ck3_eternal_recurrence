# 用本次私有原字节证明 Driver 文本无需重复 surrogate 遍历

已有严格 Driver 解码在每个 history／slot 子树上重复遍历文本与字段名，确认 surrogate 的 encode／parse 行为可安全复用。现在两处根解码入口先取得本次一致私有原字节副本，用原严格 UTF-8／JSON parser 解码，再作一次保守字节证明：原字节没有任何 backslash-u 序列，也没有大于等于 F0 的字节时，严格解析的字符串不可能包含 UTF-16 surrogate，私有解析子树可跳过这次重复检查。

所有不确定输入继续原 stableParserTree 和原构造器路径，包括真实四字节 UTF-8、escaped unicode、pair／unpaired surrogate、字段名和 literal backslash-u。原 bytes(node) 完整验证和编码、全部预算、callback／null／size 错误先序、公开 Value／History／Complete 构造器、精确身份一次消费及 finally 均保留；没有改变 parser、hash、编码或增加跨调用缓存。

生产单 TU 完整9类与独立测试单类首次编译通过，完整四项实际4P／0F／0E／0skip。输入由合法完整 public Complete 的全部 slots 与有序三项 history 构造，覆盖大整数、原数字 token、BMP、12个 Unicode 不确定域，并以原 public Value／History 构造路径作 oracle；另测 caller 原数组、返回数组和 verifier row 修改、nested decode、异常同对象、错误后再合法调用与公有伪 index 仍拒。不使用扫描器镜像或遍历计数。模型提供的裸 JSON／错误签名测试未采用，测试由 owner13 独立完成。

正式 HEAD 的完整 BASE 为9991B／`6ee9ba914fad5654c6b03c23762ca56f5738e79714716ef61c0b4cde83571779`，与实际已资格 BASE 逐字相同；正式发表的候选10911B／`0307feefd2f675eec8af3577452779a5b02fe3af28eb1173e0aa9076cfd64404`及测试15245B／`7d8979f02a25df99bdd4da9bcbe5db5eb5bb35a8aa76124dd7a94ca0f7ee5942`也直接同源复用，没有额外重编旧绿。生产 ACTUAL1594B／`716d712dceec8df1c0fee60473671aca3c0d4cce179bc439e90745b0f08b3907`；whole4 ACTUAL1433B／`92d0e1472328131c1fcf4f40173e1d9b6a8601e98540b9b42163fceea2726b37`、CLOSE204B／`9de1f5f8f1046e34fd00169203d691b56f2e374fcf1c113f59f0410e71a7a5a3`。原件在 `D:/ck3-state/resume91-native-integration/life-postcondition-p0-20261112-01/driver-snapshot54-{compile01,test13-junit01}/actual/prod`。机器 `xenoamess-full-tower-eb9d2c1186`，2026-11-12离线资格。

九处生产核心来自本地模型完整候选；owner仅机械适配两个旧锚点的嵌套缩进与接口 implicit-public 声明。正确性资格不代表实际装载、总墙钟或新增保存日改善。Runtime 正常运行，候选只在后续真实必要边界评估，不为这次发表重启或中断原命令。
