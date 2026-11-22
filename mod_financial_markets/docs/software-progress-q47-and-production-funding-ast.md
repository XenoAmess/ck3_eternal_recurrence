# Q47与生产资金费AST软件验证

2026-11-22，machine_id: 4-8e1c2f1861。Q47实际源码为 `048e8304246217b972ced8308a46ac5fe0e98c57`；Java完整验证使用该提交基线，加已采用但当时未提交的一叶测试修改，不能简称为纯048e源码。该叶从87583字节／SHA `845886ad9960fbe13132afb06f41f060fdc3910a20e0b9f67da80e3a3017d2eb` 变为95253字节／SHA `3f4e6601d0d502244a3039c5787332f4d0569e760954902a21eda6cedbb3c185`，实际SOURCE-BEFORE仅此dirty路径，完整SOURCE-WINDOW绑定运行时字节；本文不猜后继提交头。本记录不改变R64加载的f358／Q46来源或以往失败。

Q47原操作退出0，用时142.0355774秒，公开consumer为PASS。配置为238个flag，TU图为268＋593＋1＝862；实际日志只有14条CXX构建和4条链接，其中生产10条、两个新OFF target共4条CXX，不能说862全重编，也不能把112行依赖对象元数据称作112次重编。22个正式fixture按精确依赖复用，新增正式fixture执行为0；curated decisions与XQOL conversion prompt的两个默认OFF补充测试分别实际执行0。DLL引用SHA为 `4a4f30881c56e0e15445d7d7c01bb120f70ccf67ad3c310014085cd3ceba7b2f`。原日志vswhere提示及后继vcvars成功保持，原构建退出0；该NoGame资格不授新267能力或实机业务。

金融侧只新增既有Java测试叶中的三个生产AST资金费用例：双方premium方向对应实际保证金／可用分转移、同日幂等与现金守恒；真实成交量9900分低于原10000分门槛而10010分合格；合格单手资金费仍向下舍入0，不虚造递延1分。用例先执行真实submit／match脚本建仓及记录成交量，再运行position_daily，使用现有Clausewitz VM；这是软件夹具里的真实脚本链，不是引擎付款或实际市场成交。

受影响FullBook类34项实际通过，用时73.4735918秒；该阶段日志实际记载编译61个main源、52个test源，不能说整批零重编。最终未过滤、未skip的完整verify共634个distinct方法全部通过，failure／error／skip均0；外层270.1085025秒，Maven子进程268.7229122秒，最终日志两处均记载“Nothing to compile - all classes are up to date.”。捕获的423个源文件前后逐项稳定，这不表示它们均等于048e干净提交。34项和三个新方法都在634项中，不与旧631或其他批次重复相加。

正额资金费实机、全局通知实际送达、长期容量与性能、完整产品及Workshop首发仍待验；正在修订的news公共source不属于本批资格。本文不新增SAVE读取或业务信用，不改写旧失败、PARTIAL、UNKNOWN或金融日期缺口。

[原wait、完整634报告、源码窗口、Q47及两项OFF执行的精确pins](../../docs/maintenance/evidence/2026-11-22-financial-markets-q47-production-funding-ast-software.json)。
