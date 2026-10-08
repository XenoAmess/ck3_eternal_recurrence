# fa0 Official Runner 第41步原因与最小测试候选（追加）

本补充绑定 **fa0f5e1ee098ab6fab4635bedce939eab857610a**，Official run [37756034825](https://github.com/XenoAmess/ck3_eternal_recurrence/actions/runs/37756034825/job/113240689583) / job 113240689583。原官方 **FAILURE** 保留；原终态包的 log/cause NULL 是首次封存时的边界，不改写原 INDEX、REPORT、ZIP 或六选candidate。

新取得完整原 joblog 188521B，SHA256 `0ca9a4a544acc54ad8e3442a6ea29460c10c0cb02e52c60f1595c12b31435928`。第一次 gh API 因终端escape输出保护 exit1；按原stderr要求增加 `--allow-escape-sequences` 后一次 actual exit0，原错误亦保全，没有改认证或网络设置。第41步实际命令 `python tools/test_fixture_engine_prepare.py`，原3tests均ERROR：receipt/identity两用例读已不存在的 `prep.REVIEWED_BUILDS`；unknown用例构造的临时repo缺少 `version_identity.py`，在 helper checked_output81→engine_identity35 加载时 FileNotFoundError。原行2055–2114逐字节excerpt和全log均保留。

官方 commit `57ee1192ce932782a3ae19732db35cba3fe14971` 的原patch移除helper副注册表，统一从 supplied repo 加载 canonical registry 和共享 Steam parser；该提交没有同步这份旧测试。其helper blob与fa0相同。真实MAIN路径的helper/registry/parser三文件与exactfa0官方源字节一致；调用真实repo helper、以模拟EXE摘要与fake ACF成功得到1.20.0.4。没有观察到真实repo依赖路径故障；这项证明只覆盖源依赖加载，不能代替真实EXE/native/SDK/live验证。

最小源码候选只有 `tools/test_fixture_engine_prepare.py`：从单一 `NATIVE_BUILD_IDENTITIES` 取1.20构建；临时fixture复制canonical registry和共享Steam parser，设置显式fake ACF、mock digest，保持unknown SHA在创建输出前拒绝，并保留receipt NOT_RUN/native_abi_loaded=false/gui_callbacks_mounted=false。没有恢复重复的 REVIEWED_BUILDS 表。

此候选三个回归一次实际exit0，原stdout/stderr及argv在 `FOCUSED-RESULT.actual.json`；unittest为3tests、9.419s、OK。没有运行其他旧测试或CI。实际官方fa0仍FAILURE，本地候选通过不补写其结论；本次RMTM步骤31原SUCCESS，LiYu/Linear原SUCCESS独立保留。whole mod **NOT_GREEN**，native/live/formal/newT/C3/I4信用NULL。

candidate源码及 `COPY-MANIFEST.actual.json` 供ROOT现场正常闭合后review/import；本轮 MAIN/HEAD/Git/runtime/system设置0写，未commit/push。小raw ZIP按来源/SHA保原字节；不含游戏、存档正文或构建binary。
