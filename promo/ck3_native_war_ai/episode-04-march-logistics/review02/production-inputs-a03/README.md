# Review02：冻结69段双语输入和真实CN配音

这个目录保存可复用的项目输入，不包含MP3、视频或人工签核。归档内含完整双语ProjectConfig、69段原中文和新英文、逐段source/actual/conditional及镜头缺口索引，以及薄composer。

用本机已核验Python运行 `materialize_inputs.py --output <全新显式目录>`。脚本先核归档及全部成员SHA，再输出原JSON、config、composer和带原ID的中文/英文txt；不联网、不调用provider、不创建媒体。归档由独立copyplan交给主仓整合者，已有同名不同字节时拒绝替换。

正式运行沿仓库的工具链规则：每个新run先查xar_promo_toolchain最新正式release；runtime-pins.actual.json的0.2.1只记录本次。安装依赖后使用新Python进程。运行时将本仓integration/src放进已验证解释器的导入路径，composer入口为 `war_ai_promo.episode04_review02:compose`。它仍要求真实69音频和明确保留的visual bindings；归档本身不是render-ready。

Edge历史故障：7.2.8的握手403旧run保持失败；Root升级7.3.1后新pilot实际成功，再单次合成余68。中间GitHub匿名latest API403发生在provider以前，保留独立错误。现在用已登录gh查询官方release并完整比对正式状态、version、wheel SHA和directURL；不输出令牌。

69段实际语音1901.616秒，按30fps、普通段0.55秒/章末1.6秒留白生成1946.866666667秒的配音时间线。pilot C01-01语音19.848秒，独立pilot时被视为章末的21.466666667秒在合并中改为20.4秒；没有重合成pilot。实际音频地址仅按机器和外置run引用，跨机器使用规则见audio-references.actual.json。

尚需真实画面绑定、剪辑、音乐、渲染、自动审计与完整1×人工审片；研究卡仍按各自原实证门槛计数。这里的32:26.867是配音时间线，不是完整成片。
