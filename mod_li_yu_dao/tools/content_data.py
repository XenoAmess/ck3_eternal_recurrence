"""Authored Confucian content catalogue; generation is not gameplay acceptance.

R01--R36 and T01--T36 retain the design catalogue. Only SAMPLE_RITES and
their SAMPLE_TENETS are emitted as native definitions in the first package.
The first package is an explicitly free chronology mode: no historical
persons, institutions, or chronology are instantiated by these definitions.
"""

from __future__ import annotations

from dataclasses import dataclass

GAME_VERSION = "1.20.0.3"
NAMESPACE = "lyd"
PARENT_RELIGION = "confucianism_religion"
PARENT_FAITH = "lyd_common_faith"
MAIN_RITE_ID = "lyd_rite_kongmen"
DESIGN_DOCUMENT = "docs/ck3-confucian-rites-and-tenets-design-list.md"
SAMPLE_RITE_CODES = ("R01", "R02", "R03", "R06", "R07", "R10", "R20", "R21")

SOURCE_LINKS = {
    "confucius": "https://plato.stanford.edu/entries/confucius/",
    "mencius": "https://plato.stanford.edu/entries/mencius/",
    "xunzi": "https://plato.stanford.edu/entries/xunzi/",
    "dong": "https://www.shidianguji.com/mingju/7621669398360915994",
    "han_classics": "https://zxyj.cbpt.cnki.net/portal/journal/portal/client/paper/9511dbcdd722bd91723bc52843db1a7f",
    "zheng_wang": "https://ruzang.pku.edu.cn/info/1107/1746.htm",
    "xuanxue": "https://plato.stanford.edu/entries/neo-daoism/",
    "jingshu": "https://www.cp.com.cn/book/275bde04-e.html",
    "han_li": "https://journal.scu.edu.cn/info/1109/13243.htm",
    "li_ao": "https://www1.ihp.sinica.edu.tw/Publications/Bulletin/981/Article/388",
    "song_ming": "https://plato.stanford.edu/entries/song-ming-confucianism/",
    "song_classics": "https://www.litphil.sinica.edu.tw/newsletter/86/157-172.pdf",
    "guan_luo": "https://jijian.snnu.edu.cn/info/1005/1072.htm",
    "wanganshi": "https://ah.lib.nccu.edu.tw/item?item_id=58658",
    "su_school": "https://soyj.cbpt.cnki.net/portal/journal/portal/client/paper/56d8388f043644ae6bb0098fc96d5861",
    "yongjia": "https://zsbwg.zjgsu.edu.cn/2023/1201/c4095a168508/page.htm",
    "wucheng": "https://www.shidianguji.com/book/RZ1932/chapter/1lw8yn3q9caa1",
    "baisha_ganquan": "https://wyds.cbpt.cnki.net/portal/journal/portal/client/paper/0b898c5bf8642b9e2d4be773301b6336",
    "ganquan": "https://journal.bit.edu.cn/sk/article/id/20140423",
    "yangming": "https://plato.stanford.edu/entries/wang-yangming/",
    "jiangyou": "https://ruzang.pku.edu.cn/info/1107/1757.htm",
    "taizhou_donglin": "https://sxsyj.nju.edu.cn/d5/5d/c12464a251229/page.htm",
    "jishan": "https://www.phil.tsinghua.edu.cn/info/1036/1123.htm",
    "chuanshan": "https://zhouyi.sdu.edu.cn/info/1034/1042.htm",
    "yan_li": "https://ruzang.pku.edu.cn/rzen/info/1017/1255.htm",
    "qianjia": "https://qsyj.ruc.edu.cn/EN/abstract/abstract1662.shtml",
    "changzhou": "https://sxsyj.nju.edu.cn/d5/45/c12461a251205/page.htm",
    "huangzongxi": "https://zh.wikisource.org/zh-hans/明夷待訪錄",
    "xiaojing": "https://ctext.org/xiao-jing/zh",
    "jifa": "https://zh.wikisource.org/wiki/禮記/祭法",
    "martial_rites": "https://www.shidianguji.com/mid-page/7620561956860100646",
}


@dataclass(frozen=True)
class Rite:
    code: str
    slug: str
    name_zh: str
    name_en: str
    history_zh: str
    history_en: str
    tenet_codes: tuple[str, str, str]
    era: str
    kind: str
    source_keys: tuple[str, ...]
    color: tuple[int, int, int] = (236, 190, 85)

    @property
    def script_id(self) -> str:
        return f"lyd_rite_{self.slug}"

    @property
    def is_sample(self) -> bool:
        return self.code in SAMPLE_RITE_CODES

    @property
    def icon(self) -> str:
        return "daoxue" if self.code in {"R20", "R21"} else "jingxue"

    @property
    def sources(self) -> tuple[str, ...]:
        return tuple(SOURCE_LINKS[key] for key in self.source_keys)


@dataclass(frozen=True)
class Tenet:
    code: str
    slug: str
    name_zh: str
    name_en: str
    belief_zh: str
    belief_en: str
    practice_zh: str
    practice_en: str
    source_keys: tuple[str, ...]
    icon: str = "tenet_ritual_hospitality"

    @property
    def script_id(self) -> str:
        return f"lyd_tenet_{self.slug}"

    @property
    def parameter_id(self) -> str:
        return f"lyd_{self.slug}_practice"

    @property
    def sources(self) -> tuple[str, ...]:
        return tuple(SOURCE_LINKS[key] for key in self.source_keys)


RITES = (
    Rite("R01", "kongmen", "孔门经礼", "The Kongmen Tradition",
         "以孔门的仁、礼与敬为本，学诗习礼，尊圣传道。祭礼的敬与哀须出于内心；贵重礼物不能代替诚意。此名概括经典中的共同传统，不声称古代存在同名独立教会。",
         "Rooted in the Confucian classics, this tradition joins humaneness, ritual and reverence. Study, music and sincere offerings cultivate character; lavish gifts cannot replace a reverent heart. Its name describes a shared tradition, rather than an ancient separate church.",
         ("T03", "T06", "T08"), "pre_qin", "reconstructed", ("confucius", "jifa")),
    Rite("R02", "mengzi", "孟氏之学", "The Learning of Mengzi",
         "恻隐、羞恶、辞让与是非之心是成德的萌芽，须由行义扩充。养气依靠持续实践，礼义冲突则须辨经权；性善不意味着无需努力便已成圣。",
         "Compassion, shame, deference and moral discernment are sprouts to be extended through practice. Righteous conduct nourishes moral courage; difficult cases require judgment. Good human nature does not make anyone a sage without cultivation.",
         ("T09", "T11", "T06"), "pre_qin", "historical", ("mencius",), (210, 174, 76)),
    Rite("R03", "xunzi", "荀氏之学", "The Learning of Xunzi",
         "成德有赖师法、习礼与人为努力。丧祭与礼乐安顿情感和欲望；天的运行有常，祈雨不直接改变天时。起伪之伪指有意识的作为，绝非以欺诈为德。",
         "Moral cultivation requires teachers, ritual and deliberate effort. Mourning and music give proper form to emotions and desires. Heaven follows its regular course; rain rites do not control the weather. Deliberate effort here means cultivation, not deceit.",
         ("T10", "T03", "T22"), "pre_qin", "historical", ("xunzi",), (189, 143, 67)),
    Rite("R04", "dongzhongshu", "公羊春秋·董氏传承", "Dong's Gongyang Tradition",
         "以董仲舒相关公羊经说为重点，借春秋褒贬明义，将灾异理解为省过的谴告。它不代表所有今文家；灾异的解释可以争论，不能证明天神按人的请求施罚。",
         "This route emphasizes Dong Zhongshu's Gongyang learning, moral judgments in the Spring and Autumn Annals and portents interpreted as calls to reform. It does not represent all New Text scholars, nor prove that Heaven punishes on command.",
         ("T21", "T12", "T01"), "han", "historical", ("dong", "han_classics")),
    Rite("R05", "guwen", "古文经传", "Old Text Learning",
         "依据经传、旧注与可考的名物辨礼明义。汉代今古文之分不等于两套整齐神学，考证也不预设拒绝一切鬼神与祭祀。",
         "Inherited texts, commentaries and historical evidence guide the interpretation of rites. Han Old and New Text traditions were not two uniform theologies; textual inquiry need not reject spirits or sacrifice.",
         ("T19", "T20", "T08"), "han", "historical", ("han_classics",)),
    Rite("R06", "zhengxuan", "郑氏礼学", "Zheng Xuan's Ritual Learning",
         "会通今古文的郑氏礼学区分昊天与五帝、圜丘与郊祭，并以感生与祖先配享解释祭礼。经师理论与各朝实际采用的祀典仍须分别考察。",
         "Zheng Xuan's synthesis distinguishes Highest Heaven from the Five Emperors, and the Round Mound from the suburban sacrifice. Accounts of ancestral origin and paired offerings shape ritual interpretation. A commentator's theory is not automatically a dynasty's actual practice.",
         ("T19", "T01", "T04"), "eastern_han", "historical", ("zheng_wang",), (224, 178, 110)),
    Rite("R07", "wangsu", "王氏礼学", "Wang Su's Ritual Learning",
         "王肃主张天惟一体、丘郊一祭，将禘礼解释为追享祖源。它与郑氏有实际礼学分歧，仍共同重视经据、报本与诚敬；王肃不是王弼。",
         "Wang Su maintains one Heaven, understands mound and suburban offerings as one sacrifice, and interprets di rites through ancestral origins. This is a substantive disagreement with Zheng Xuan within shared ritual learning. Wang Su is distinct from Wang Bi.",
         ("T19", "T04", "T20"), "cao_wei", "historical", ("zheng_wang",), (182, 153, 107)),
    Rite("R08", "wangbi", "王弼玄儒", "Wang Bi's Classical Interpretation",
         "以王弼的贵无、崇本与得意忘象为素材，追问经典的根本义。玄儒为跨儒道的概括标签，不将所有玄学划成儒家宗派。",
         "Wang Bi's interpretation seeks the root of things and meaning beyond images. This is a deliberately cross-traditional route drawing on Confucian and Daoist concerns, rather than a claim that all xuanxue formed a Confucian denomination.",
         ("T32", "T20", "T03"), "wei_jin", "cross_tradition", ("xuanxue",)),
    Rite("R09", "guoxiang", "郭象玄儒", "Guo Xiang's Classical Interpretation",
         "从独化、性分与自得理解万物及名教自然。此跨界路线保留与王弼贵无论的差异，不另造同名古代教会。",
         "Self-transformation, individual capacities and self-realization inform Guo Xiang's account of nature and moral roles. This cross-traditional route remains distinct from Wang Bi's emphasis on nonbeing.",
         ("T32", "T03", "T06"), "western_jin", "cross_tradition", ("xuanxue",)),
    Rite("R10", "jingshu", "经疏正义", "The Classical Commentaries",
         "以南北经学及唐代经疏为基础，兼习诸经，尊重传注又辨其义理。祭序、礼器与丧服须据经说明，不将后世四书中心体系提前置入。",
         "Drawing on northern and southern learning and Tang commentaries, this route studies several classics and examines their explanations of ritual. Offerings, vessels and mourning require textual grounds; a later Four Books curriculum is not projected backward.",
         ("T20", "T19", "T08"), "sui_tang", "historical", ("jingshu",), (229, 204, 137)),
    Rite("R11", "hanyu", "韩氏原道", "Han Yu's Recovery of the Way",
         "以仁义人伦论道，尊孔孟、师道与圣道承传，并批评出世主张。论辩不自动成为对所有佛道人物的永久敌视。",
         "Humaneness and righteousness define the Way, transmitted through sages and teachers. Han Yu's criticisms of withdrawal from human obligations do not require permanent personal hostility toward every Buddhist or Daoist.",
         ("T06", "T08", "T07"), "late_tang", "historical", ("han_li",)),
    Rite("R12", "liao", "李氏复性", "Li Ao's Return to Nature",
         "通过澄心静养恢复被邪妄之情遮蔽的本性，论诚与成圣。此说与佛道思想有复杂联系，不能与韩愈合成一种单纯反佛的学说。",
         "Calming the heart reveals a good nature obscured by turbulent feelings. Sincerity and becoming a sage guide cultivation. Its complex relations with Buddhist and Daoist thought distinguish Li Ao from a simple anti-Buddhist reading of Han Yu.",
         ("T23", "T02", "T08"), "late_tang", "historical", ("li_ao", "han_li")),
    Rite("R13", "zhoudunyi", "濂溪之学", "Zhou Dunyi's Learning",
         "以诚、阴阳生化与静养探讨成圣之道。周敦颐是北宋先驱，后世学统整理不能直接当作其时代的统一教会。",
         "Sincerity, the transformations of yin and yang, and cultivation in stillness inform Zhou Dunyi's learning. Later accounts of lineage must be distinguished from institutions of his own lifetime.",
         ("T34", "T02", "T15"), "northern_song", "historical", ("song_ming",)),
    Rite("R14", "chengbrothers", "二程洛学", "The Cheng Brothers' Learning",
         "论天理、仁与持敬，以学问和道德实践互相贯通；程颢、程颐之间仍有不同侧重。",
         "Heavenly principle, humaneness and reverent attention unite study and moral practice. Cheng Hao and Cheng Yi nevertheless have distinct emphases.",
         ("T15", "T14", "T06"), "northern_song", "historical", ("song_ming", "guan_luo")),
    Rite("R15", "zhangzai", "横渠关学", "Zhang Zai's Guan Learning",
         "以气化、天人联系和民胞物与论道，强调通过礼与实践变化气质。关学与洛学相互影响并有批评，不应全部折叠为同一说法。",
         "Transformations of qi connect humanity, Heaven and the world. Ritual and practice change one's dispositions. Guan and Luo learning influenced and criticized each other rather than forming an identical theory.",
         ("T13", "T03", "T07"), "northern_song", "historical", ("guan_luo", "song_ming")),
    Rite("R16", "shaoyong", "先天象数之学", "Shao Yong's Image and Number Learning",
         "借象数、观物与天道运行理解天地。推演表达解释与信念，不提供必然准确的未来预言。",
         "Images, numbers and contemplation of things illuminate the workings of Heaven and Earth. Such interpretation expresses a worldview rather than guaranteed knowledge of future events.",
         ("T31", "T20", "T01"), "northern_song", "historical", ("song_ming",)),
    Rite("R17", "wanganshi", "荆公新学", "Wang Anshi's New Learning",
         "重新解释诗、书、周礼等经典，以经义回应当时处境。此路不等于公羊春秋学，也不将全部变法政策当成宗教工夫。",
         "New readings of the Odes, Documents and Rites of Zhou respond to contemporary circumstances. This is distinct from Gongyang learning and is not simply a religious label for every New Policy.",
         ("T30", "T20", "T06"), "northern_song", "historical", ("wanganshi", "song_classics")),
    Rite("R18", "sushi", "苏氏之学", "The Su Family's Learning",
         "以三苏及后学的经义、人情与礼义讨论为素材。学派边界有后世整理，不把所有蜀地学人或政治同党合为教会。",
         "The Su family's interpretations explore the classics, human feelings and ritual. Later definitions of the school should not turn every Sichuan scholar or political ally into one denomination.",
         ("T20", "T06", "T03"), "northern_song", "historical", ("su_school",)),
    Rite("R19", "huxiang", "湖湘之学", "Huxiang Learning",
         "以胡宏、张栻等人的仁、性与成德讨论为基础，察识与涵养有不同解释。湖湘有自己的学统，并非朱学的附庸。",
         "Hu Hong, Zhang Shi and their lineage examine humaneness, nature and cultivation, including the relation between recognition and nourishment. Huxiang learning has its own history and is not merely an appendix to Zhu Xi.",
         ("T06", "T15", "T02"), "southern_song", "historical", ("song_classics",)),
    Rite("R20", "zhuxi", "朱子之学", "Zhu Xi's Learning",
         "以四书、理气及居敬穷理论成德，家礼将诚敬落实于日用丧祭。问学必须落实于行；其南宋形成过程与后世官方正统地位不能混为一谈。",
         "The Four Books, principle and qi, reverent attention and inquiry guide cultivation. Family rites bring sincerity into mourning and offerings. Study must inform conduct; the school's Southern Song development is distinct from its later official status.",
         ("T14", "T15", "T04"), "southern_song", "historical", ("song_ming", "song_classics"), (150, 211, 198)),
    Rite("R21", "lujiuyuan", "象山之学", "Lu Jiuyuan's Learning",
         "发明本心、辨明大本，以立志改过和实践检验自得。它不主张任性便是道，也不废弃经典；陆学不等于后世成熟的阳明学。",
         "Illuminating the original heart requires moral resolve, correction and practice. Personal whims are not the Way, and the classics remain relevant. Lu Jiuyuan's learning is distinct from the later mature teachings of Wang Yangming.",
         ("T16", "T02", "T06"), "southern_song", "historical", ("song_ming", "song_classics"), (113, 185, 180)),
    Rite("R22", "yongjia", "永嘉之学", "Yongjia Learning",
         "义理须在具体事务与实践效果中检验，义利关系需要辨析。事功不是以财富或胜利直接证明德性。",
         "Moral principles must be tested in concrete affairs and their consequences. Practical achievement is not a license to equate wealth or victory with virtue.",
         ("T27", "T06", "T19"), "southern_song", "historical", ("yongjia",)),
    Rite("R23", "yongkang", "永康之学", "Yongkang Learning",
         "陈亮相关传承从历史、道义与事功中论学。它与永嘉有联系，仍保留不同的思想来源。",
         "Chen Liang's learning examines history, moral purpose and achievement. Its connections with Yongjia do not erase their different intellectual origins.",
         ("T27", "T11", "T07"), "southern_song", "historical", ("song_ming", "yongjia")),
    Rite("R24", "wucheng", "草庐会通", "Wu Cheng's Synthesis",
         "以元代吴澄的经籍整理、朱陆会通及德性工夫为基础。会通不是另造一套神谱，也不是元朝建立当天自动出现的统一学说。",
         "Wu Cheng's Yuan learning joins textual work, cultivation and engagement with Zhu and Lu. Synthesis does not create a new pantheon or a doctrine that arose fully formed when the dynasty began.",
         ("T20", "T14", "T16"), "yuan", "historical", ("wucheng", "song_classics")),
    Rite("R25", "chenxianzhang", "白沙之学", "Chen Xianzhang's Learning",
         "陈献章以静养、自得及自身道德体认论学，主要发展于十五世纪后半。不将白沙直接并入后来的阳明学。",
         "Chen Xianzhang emphasizes quiet cultivation and personally attained moral understanding. Developing chiefly in the later fifteenth century, this route is not simply an early name for Yangming learning.",
         ("T35", "T02", "T08"), "late_fifteenth_century", "historical", ("baisha_ganquan",)),
    Rite("R26", "zhanruoshui", "甘泉之学", "Zhan Ruoshui's Learning",
         "在动静、内外及具体处境中随处体认天理。湛若水与王阳明论辩，不能简化为王门附属。",
         "Heavenly principle is recognized throughout movement, stillness and concrete situations. Zhan Ruoshui debated with Wang Yangming rather than merely belonging to his school.",
         ("T36", "T15", "T20"), "sixteenth_century", "historical", ("baisha_ganquan", "ganquan")),
    Rite("R27", "wangyangming", "阳明学", "Wang Yangming's Learning",
         "致良知、知行合一与事上磨炼相互贯通，须持续去除自欺。成熟学说主要在十六世纪，不提前冒称早期开局已有同名学派。",
         "Extending moral knowledge, the unity of knowing and acting, and cultivation in affairs oppose self-deception. The mature teaching belongs chiefly to the sixteenth century, not to an already existing early medieval school.",
         ("T17", "T18", "T06"), "sixteenth_century", "historical", ("yangming",)),
    Rite("R28", "jiangyou", "江右王门", "The Jiangyou Wang School",
         "以戒惧、慎独与良知持守为重点，成员在静养和实践上仍有差异。不以一个统一公式抹平王门内部讨论。",
         "Vigilance, sincerity in solitude and maintaining moral knowledge characterize this branch. Its members still differ over quiet cultivation and practice.",
         ("T17", "T02", "T15"), "sixteenth_century", "historical", ("jiangyou", "yangming")),
    Rite("R29", "taizhou", "泰州之学", "Taizhou Learning",
         "普通人的日用生活亦可成圣，尊身与会讲成为学习内容。此路不将所有王艮后学视为同一思想，也不因出身直接判德性。",
         "Ordinary daily life can become a path to sagehood, with care for oneself and shared teaching. Followers of Wang Gen are not all identical, and social birth alone does not determine virtue.",
         ("T24", "T17", "T08"), "sixteenth_seventeenth_centuries", "historical", ("taizhou_donglin", "yangming")),
    Rite("R30", "liuzongzhou", "蕺山之学", "Liu Zongzhou's Learning",
         "慎独诚意、检点微意与迁善改过是持续工夫。公开认错或做一场善事，不能替代隐微处的自省。",
         "Sincerity in solitude, attention to subtle intentions and correcting faults require sustained cultivation. Public confession or a single good deed cannot replace honest inward examination.",
         ("T02", "T29", "T15"), "late_ming", "historical", ("jishan",)),
    Rite("R31", "donglin", "东林之学", "Donglin Learning",
         "讲学、躬行义理及公共责任共同构成修养。学统与政治阵营须区别，不把全部东林同党改为教会。",
         "Teaching, practicing moral principles and public responsibility shape cultivation. An intellectual lineage must be distinguished from a political alliance.",
         ("T07", "T06", "T15"), "late_ming", "historical", ("taizhou_donglin",)),
    Rite("R32", "wangfuzhi", "船山气学", "Wang Fuzhi's Qi Learning",
         "以气化生生、人的判断和实践、知行相资论道。此学主要属于明清之际，不能套用现代无神论教会的标签。",
         "The ongoing transformations of qi, human judgment and mutually supporting knowing and acting shape this late Ming and early Qing learning. A modern atheist denomination is not its historical counterpart.",
         ("T34", "T33", "T04"), "ming_qing_transition", "historical", ("chuanshan",)),
    Rite("R33", "yanli", "颜李之学", "Yan-Li Practical Learning",
         "礼乐射御书数须亲身习行，躬行而非空谈成德。六艺的实践不是现代教育产业，也不是仅有兵种增益。",
         "Ritual, music, archery, charioteering, writing and calculation require personal exercise. Moral cultivation through these arts is neither a modern educational industry nor simply a military bonus.",
         ("T25", "T03", "T06"), "early_qing", "historical", ("yan_li",)),
    Rite("R34", "qianjia", "乾嘉汉学", "Qianjia Classical Learning",
         "以故训、文献和名物明圣贤之道，考据不取消义理。惠栋、戴震等人仍有差异，情欲与义理的争论不能全部折叠为程朱旧说。",
         "Philology, evidence and historical particulars illuminate the sages' Way. Textual work does not eliminate ethics, and figures such as Hui Dong and Dai Zhen retain significant differences.",
         ("T26", "T19", "T20"), "eighteenth_century", "historical", ("qianjia",)),
    Rite("R35", "changzhou", "常州今文经学", "Changzhou New Text Learning",
         "据公羊经义、微言大义及时代处境解释经典。后学不断分化，不将康有为全部晚期主张回填到庄存与、刘逢禄。",
         "Gongyang interpretation and the subtle meaning of the classics respond to changing circumstances. Later branches differ; Kang Youwei's later proposals should not be projected onto Zhuang Cunyu or Liu Fenglu.",
         ("T21", "T30", "T26"), "late_eighteenth_nineteenth_centuries", "historical", ("changzhou",)),
    Rite("R36", "jingshi", "经世实学", "Practical Learning for the World",
         "此为以明清道义、历史与现实事务之学组合的综合路线。亭林、梨洲等可有不同配置，不冒称顾、黄、王曾同属一个统一宗派。",
         "This is a designed synthesis of Ming and Qing learning about moral purpose, history and concrete affairs. Gu Yanwu, Huang Zongxi and Wang Fuzhi are not presented as members of a single historical denomination.",
         ("T06", "T07", "T27"), "ming_qing", "synthesis", ("huangzongxi", "chuanshan")),
)


TENETS = (
    Tenet("T01", "reverent_heaven", "敬天明命", "Revere Heaven and Its Charge",
          "敬天意味着承认受命者的道德责任；天的解释可以因学统而异。", "Reverence for Heaven entails moral responsibility; schools may understand Heaven differently.",
          "斋戒告天，省察失德与祭祀资格。", "Prepare reverently for offerings and examine faults and ritual standing.", ("jifa", "dong")),
    Tenet("T02", "sincerity_solitude", "诚敬慎独", "Sincerity in Solitude",
          "无人知晓时也须不自欺，诚敬须贯通意念和行为。", "Sincerity joins intention and conduct even when no one is watching.",
          "祭前整肃与私下改过；献金不能替代补过。", "Prepare honestly and correct private faults; donations cannot substitute for repair.", ("confucius", "song_ming"), "tenet_inner_journey"),
    Tenet("T03", "ritual_music", "礼乐成德", "Cultivation through Ritual and Music",
          "礼与乐给敬、哀和欲望以合宜形式，使实践成为成德之路。", "Ritual and music give reverence, grief and desire fitting forms and cultivate character.",
          "在释奠、丧祭与雅乐中辨诚敬、节制和炫耀。", "Distinguish sincerity, restraint and ostentation in offerings, mourning and music.", ("confucius", "xunzi")),
    Tenet("T04", "ancestral_reverence", "报本敬祖", "Honor Ancestral Origins",
          "祖先追念、丧祭与生者责任互相联系。", "Remembering ancestors connects mourning, offerings and duties to the living.",
          "以告祖与丧祭表达哀敬，并承担费用和照料之责。", "Express grief and reverence through ancestral rites while accepting costs and duties of care.", ("jifa", "zheng_wang")),
    Tenet("T05", "names_duties", "正名践分", "Names and Responsibilities",
          "名号与身份须与实际履行的责任相称。", "Titles and roles must correspond to fulfilled responsibilities.",
          "说明或纠正僭号、失职与失礼。", "Explain or correct improper titles, neglected duties and ritual failures.", ("confucius", "xunzi")),
    Tenet("T06", "humaneness_righteousness", "仁义为道", "Humaneness and Righteousness",
          "仁义不能被财富、权势与一时便利取代。", "Wealth, power and convenience cannot replace humaneness and righteousness.",
          "救助、恤孤与宽俘须接受资源代价；见利忘义损害修养。", "Aid and mercy require real resources; sacrificing rightness for gain undermines cultivation.", ("mencius", "han_li")),
    Tenet("T07", "righteous_remonstrance", "以义匡谏", "Righteous Remonstrance",
          "对亲长和君主的责任也包含劝止不义。", "Responsibility toward elders and rulers includes urging them away from wrongdoing.",
          "承担进谏的关系代价，不以此制造无限牵制。", "Accept the relational costs of remonstrance without treating it as unlimited coercion.", ("xiaojing",)),
    Tenet("T08", "sage_transmission", "尊圣传道", "Honor Sages and Transmit the Way",
          "传承成德之道须以经典、教学与德行相互印证。", "Transmission of moral learning requires texts, teaching and exemplary conduct.",
          "受业、传书与谒圣；真传之说须接受问学和德行检验。", "Study with teachers, transmit books and honor sages; claims of true transmission invite scrutiny.", ("confucius", "han_li"), "tenet_literalism"),
    Tenet("T09", "extend_sprouts", "扩充四端", "Extend the Four Sprouts",
          "恻隐、羞恶、辞让与是非之心是善的萌芽，仍须扩充。", "Compassion, shame, deference and discernment are moral beginnings that require extension.",
          "在连续抉择中践行善端，不能只自称心善。", "Cultivate these beginnings through repeated choices rather than merely claiming goodness.", ("mencius",)),
    Tenet("T10", "deliberate_cultivation", "化性起伪", "Deliberate Moral Cultivation",
          "师法、习礼和有意识的努力改变未经养成的欲望。", "Teachers, ritual and conscious effort reshape uncultivated desires.",
          "反复学习并约束争夺；人为之伪不是欺骗。", "Learn repeatedly and restrain rivalry; deliberate action here does not mean deception.", ("xunzi",)),
    Tenet("T11", "righteous_qi", "集义养气", "Nourish Qi through Righteousness",
          "浩然之气由持续行义积累，不能由一次表演获得。", "Moral courage grows through sustained righteous conduct rather than a single performance.",
          "守已承担的义务，临事违义损害积累。", "Fulfill accepted duties; betraying rightness weakens accumulated cultivation.", ("mencius",)),
    Tenet("T12", "portent_reflection", "灾异省身", "Reflect upon Portents",
          "灾异可被解释为省过之警，但解释需要论辩。", "Portents may be understood as warnings to reform, but their interpretation is contestable.",
          "灾后问礼、告祭和省过；不能召唤灾害。", "Consult, offer and reflect after disasters without claiming power to summon them.", ("dong",)),
    Tenet("T13", "qi_kinship", "气化同体", "Kinship within the Transformations of Qi",
          "气化连接天地万物，民胞物与带来道德责任。", "Transformations of qi connect the world and ground moral responsibilities toward others.",
          "在丧祭与照料中思索生死，承担实际责任。", "Consider life and death through rites and care while accepting concrete duties.", ("guan_luo", "song_ming")),
    Tenet("T14", "investigate_principle", "格物穷理", "Investigate Things and Principle",
          "经书、礼仪和日用人伦皆可成为探求理的对象。", "Classics, rites and everyday relationships are fields for investigating principle.",
          "考察伦理疑案并践行所得，不止积累章句。", "Examine moral cases and act upon understanding rather than accumulating phrases alone.", ("song_ming", "song_classics"), "tenet_literalism"),
    Tenet("T15", "reverent_attention", "居敬涵养", "Reverent Attention and Cultivation",
          "敬须贯通动静与日用，省察骄矜及私欲。", "Reverent attention extends through stillness, movement and daily life.",
          "持续约束自欺与骄矜，不禁止正常情感。", "Restrain self-deception and arrogance without denying ordinary emotions.", ("song_ming",), "tenet_inner_journey"),
    Tenet("T16", "original_heart", "发明本心", "Illuminate the Original Heart",
          "本心的道德根据不能与任性的欲求等同。", "The moral ground of the original heart is not identical to personal whim.",
          "在权势与良心冲突中辨大本，改过和行动检验自得。", "Discern moral purpose amid power and conscience; correction and action test insight.", ("song_ming", "song_classics"), "tenet_inner_journey"),
    Tenet("T17", "innate_knowing", "致良知", "Extend Moral Knowledge",
          "落实良知须持续去除自欺。", "Extending moral knowledge requires sustained resistance to self-deception.",
          "联系意念与处境，向不同出身者问道。", "Join intention to circumstances and learn from people of different backgrounds.", ("yangming",)),
    Tenet("T18", "knowing_acting", "知行合一", "The Unity of Knowing and Acting",
          "真知与践行不可被空谈割裂。", "Genuine moral knowing cannot be severed from acting.",
          "用明确承担的行动验证许诺，失约须补过。", "Test promises through accepted actions and repair broken commitments.", ("yangming",)),
    Tenet("T19", "textual_ritual", "据经考礼", "Ground Rites in the Classics",
          "礼器、祭序及配享须能说明其经据。", "Ritual vessels, sequences and paired offerings require intelligible textual grounds.",
          "论礼与诚敬共同决定实践，贵重器物不自动正确。", "Evidence and reverence guide practice; expensive vessels do not make a rite correct.", ("zheng_wang", "jingshu"), "tenet_literalism"),
    Tenet("T20", "classical_synthesis", "诸经会通", "Interpret Classics Together",
          "多部经传可相互阐发，同时须辨异同。", "Several classics illuminate each other without erasing their differences.",
          "比较传注与跨经义案，不以一本书包办所有真义。", "Compare commentaries and cases across texts rather than treating one book as every answer.", ("jingshu", "song_classics"), "tenet_literalism"),
    Tenet("T21", "annals_judgment", "春秋明义", "Moral Judgment in the Annals",
          "春秋褒贬与经义解释关乎行为之义。", "Praise, blame and interpretation of the Annals illuminate moral action.",
          "以论经辨现实伦理，不将史论无限转成处罚。", "Relate textual debate to ethical cases without converting every judgment into punishment.", ("dong", "changzhou")),
    Tenet("T22", "constant_heaven", "天行有常", "Heaven Follows Its Course",
          "自然运行有常，道德责任应在人事中求。", "Nature follows regular patterns; moral responsibility belongs to human conduct.",
          "祈雨和灾异可依礼文解释，拒绝天谴不取消祭礼。", "Rites and portents can be interpreted as ritual expression without abandoning sacrifice.", ("xunzi",)),
    Tenet("T23", "restore_nature", "澄心复性", "Calm the Heart and Restore Nature",
          "善性可能被邪妄之情遮蔽，静养有助复性。", "Disturbing feelings may obscure good nature; quiet cultivation helps reveal it.",
          "澄心返观，避免以静养为逃避人伦责任。", "Calm and examine the heart without using retreat to evade human responsibilities.", ("li_ao",), "tenet_inner_journey"),
    Tenet("T24", "ordinary_life", "百姓日用", "Cultivation in Ordinary Life",
          "普通人的日用也有成圣可能。", "Ordinary daily life also offers a path toward sagehood.",
          "会讲、日用伦理与跨身份问学。", "Teach together, examine daily obligations and learn across social ranks.", ("taizhou_donglin",)),
    Tenet("T25", "six_arts", "六艺习行", "Practice the Six Arts",
          "六艺须亲身习行，不能仅凭书本空谈。", "The Six Arts require bodily practice rather than words alone.",
          "持续习礼、雅乐与射礼，承担训练成本。", "Practice ritual, music and archery with the costs of sustained training.", ("yan_li",)),
    Tenet("T26", "philological_way", "循文见道", "Find the Way through Texts",
          "故训和文献证据可通向圣贤之道。", "Philology and documentary evidence can illuminate the sages' Way.",
          "校勘辨伪后说明伦理意义，也接受依据动摇。", "Explain ethical significance after textual inquiry and accept challenges to inherited evidence.", ("qianjia",), "tenet_literalism"),
    Tenet("T27", "moral_achievement", "道义事功", "Moral Purpose and Practical Achievement",
          "道义须面对实践与后果，逐利不因此成为德性。", "Moral purpose must face practice and consequences without making greed a virtue.",
          "检验救助和礼义抉择的实际结果。", "Examine the consequences of assistance and ritual choices.", ("yongjia", "song_ming")),
    Tenet("T28", "restrain_violence", "制暴安民", "Restrain Violence and Protect the People",
          "义战须受禁暴救民之义约束。", "Righteous warfare is constrained by duties to restrain violence and protect people.",
          "祭告与誓约约束私利、滥杀和抢掠；常设修会须另建制度。", "Offerings and vows constrain private gain, slaughter and plunder; permanent orders require separate institutions.", ("martial_rites",)),
    Tenet("T29", "subtle_intentions", "微意改过", "Examine Subtle Intentions",
          "极微意念亦须检点，改过不能靠公开表演。", "Even subtle intentions require scrutiny; correction is not a public performance.",
          "私下省察并具体补过，避免反复刷认错。", "Examine oneself privately and repair actual faults rather than repeating empty confession.", ("jishan",), "tenet_inner_journey"),
    Tenet("T30", "responsive_interpretation", "义理通变", "Interpret Principles for Changing Times",
          "可依据经义回应时代处境，各家传承仍有不同。", "Classical principles can respond to changing circumstances while schools remain distinct.",
          "提出有经据的变通，承受旧说争论。", "Propose grounded interpretation and accept debate with inherited readings.", ("wanganshi", "changzhou")),
    Tenet("T31", "images_numbers", "观象体易", "Contemplate Images and Change",
          "象数、运行与观物可表达对天道的理解。", "Images, numbers and contemplation express understanding of Heaven's patterns.",
          "论易解象，不保证预言或操控未来。", "Discuss images and change without guaranteed prophecy or control over future events.", ("song_ming",)),
    Tenet("T32", "profound_interpretation", "会通玄理", "Explore Profound Interpretation",
          "贵无、独化与名教自然有不同解释。", "Nonbeing, self-transformation and moral roles admit distinct interpretations.",
          "通过解经与论辩辨根本，不将王弼郭象宇宙论合一。", "Examine roots through debate without merging Wang Bi's and Guo Xiang's cosmologies.", ("xuanxue",)),
    Tenet("T33", "knowing_acting_support", "知行相资", "Knowing and Acting Support Each Other",
          "知与行各有功用并相互支持。", "Knowing and acting have distinct functions and support each other.",
          "问学与实践交互推进，不等同阳明的全部命题。", "Develop inquiry and practice together without treating every view as Yangming's formula.", ("chuanshan",)),
    Tenet("T34", "ongoing_generation", "万物生生", "The Ongoing Generation of Things",
          "天地生成与阴阳变化进入生命与道德的解释。", "Generation and transformation inform understandings of life and moral responsibility.",
          "在祭仪、养性与生死问题中保留各家的理气差异。", "Consider rites, cultivation and mortality while preserving differences about principle and qi.", ("song_ming", "chuanshan")),
    Tenet("T35", "quiet_self_attainment", "静养自得", "Quiet Cultivation and Self-Attainment",
          "静养与自身体认可助于得道。", "Quiet cultivation and personally attained understanding can illuminate the Way.",
          "辨静养、读经与自得，不因独处自动成圣。", "Examine quiet cultivation, study and insight without equating solitude with sagehood.", ("baisha_ganquan",), "tenet_inner_journey"),
    Tenet("T36", "recognition_everywhere", "随处体认", "Recognize Principle in Every Situation",
          "天理须在动静内外及具体处境中体认。", "Heavenly principle is recognized through movement, stillness and concrete situations.",
          "在祭仪和日用中求理，不预设天理与良知完全同义。", "Seek principle in rites and daily life without assuming identity with every account of moral knowledge.", ("ganquan", "baisha_ganquan")),
)

RITES_BY_CODE = {item.code: item for item in RITES}
TENETS_BY_CODE = {item.code: item for item in TENETS}
SAMPLE_RITES = tuple(RITES_BY_CODE[code] for code in SAMPLE_RITE_CODES)
SAMPLE_TENET_CODES = tuple(sorted({code for rite in SAMPLE_RITES for code in rite.tenet_codes}))
SAMPLE_TENETS = tuple(TENETS_BY_CODE[code] for code in SAMPLE_TENET_CODES)


@dataclass(frozen=True)
class PracticeOption:
    key: str
    label_zh: str
    label_en: str
    tooltip_zh: str
    tooltip_en: str
    gold_cost: int = 0
    piety_change: int = 0
    prestige_change: int = 0
    stress_change: int = 0
    learning_xp: int = 0


@dataclass(frozen=True)
class Practice:
    rite_code: str
    title_zh: str
    title_en: str
    desc_zh: str
    desc_en: str
    options: tuple[PracticeOption, PracticeOption, PracticeOption]
    historical_boundary_zh: str
    historical_boundary_en: str
    source_keys: tuple[str, ...]

    @property
    def slug(self) -> str:
        return RITES_BY_CODE[self.rite_code].slug

    @property
    def script_id(self) -> str:
        return f"lyd_practice_{self.slug}"

    @property
    def rite_id(self) -> str:
        return RITES_BY_CODE[self.rite_code].script_id

    @property
    def completion_flag(self) -> str:
        return f"{self.script_id}_completed"

    @property
    def sources(self) -> tuple[str, ...]:
        return tuple(SOURCE_LINKS[key] for key in self.source_keys)


# These are event INPUTS, not implemented events. Resource outcomes apply only
# to the player actor when the integration layer validates and executes them.
# Integration must check affordability, record which option was chosen, and
# implement its player/rite/faith gates and cooldown before exposing a choice.
PRACTICES = (
    Practice("R01", "祭礼中的诚敬", "Reverence within the Offering",
             "谒圣祭礼将近，礼生呈来器物与雅乐的安排。有人主张以华丽陈设显扬你的敬意，但你知道，若心不在礼，繁华也只是摆设。该如何准备这次祭礼？",
             "An offering in honor of the sages approaches. The attendants present vessels and music; some urge a lavish display of your reverence. Yet magnificence alone cannot make an inattentive heart sincere. How will you prepare?",
             (
                 PracticeOption("a", "减去浮饰，亲自习礼。", "Set aside display and rehearse the rite myself.",
                                "用合宜的器物与亲身准备表达敬意。", "Fitting vessels and personal preparation give form to reverence.",
                                gold_cost=10, piety_change=35, stress_change=5, learning_xp=25),
                 PracticeOption("b", "备齐乐舞，也给礼生留足准备。", "Prepare the music and give the attendants time to learn.",
                                "礼乐可相助，筹备与授业也有代价。", "Music and ritual support each other, with real costs of preparation and teaching.",
                                gold_cost=25, piety_change=25, prestige_change=15, learning_xp=15),
                 PracticeOption("c", "让贵重礼物替我说明诚意。", "Let costly gifts speak for my sincerity.",
                                "陈设足以引人注目，却不能代替内在诚敬。", "Display may attract attention but cannot replace inward reverence.",
                                gold_cost=40, piety_change=-15, prestige_change=25),
             ),
             "个人谒圣与习礼，不以此授予天子国礼资格。", "Personal reverence and rehearsal do not grant imperial ritual standing.",
             ("confucius", "jifa")),
    Practice("R02", "善端与眼前之人", "A Moral Sprout and the Person Before Me",
             "祭礼筹备时，一名送来器物的人受伤倒下。你的礼生担心误了时辰，劝你先把祝辞读完。此刻的恻隐之心，应怎样成为真正的行动？",
             "During preparations, a person carrying ritual vessels is injured. An attendant worries about the appointed time and urges you to finish the words first. How will compassion become action?",
             (
                 PracticeOption("a", "先安排救护，我承担误时之责。", "Arrange care first; I will answer for the delay.",
                                "在经权抉择中扩充恻隐，承担费用与议论。", "Extend compassion through judgment, accepting expense and criticism.",
                                gold_cost=20, piety_change=40, prestige_change=-10, stress_change=5, learning_xp=25),
                 PracticeOption("b", "由我另遣人照料，祭礼从简举行。", "Send help and conduct a simpler offering.",
                                "兼顾照料与礼仪，仍须实际出资。", "Care and ritual can both be honored, but assistance requires resources.",
                                gold_cost=15, piety_change=25, learning_xp=15),
                 PracticeOption("c", "我心中已有恻隐，照旧诵礼便是。", "Feeling compassion is enough; continue as before.",
                                "善端若不扩充到行动，不能只凭自称心善成德。", "An unextended moral beginning does not become virtue by assertion alone.",
                                piety_change=-20, stress_change=5),
             ),
             "匿名伦理案例为游戏情境，非冒称孟子原典记载此事。", "This anonymous moral case is a designed situation, not an episode attributed to the Mengzi.",
             ("mencius",)),
    Practice("R03", "给哀伤以礼", "Give Grief a Fitting Form",
             "丧祭习礼中，礼生只顾催促每一步仪节，哀者反而愈加慌乱。礼既非任情失序，也不该成为空洞的动作。你决定如何重新准备？",
             "During rehearsal for mourning, hurried instructions leave the mourners distressed. Ritual is neither unrestrained emotion nor an empty sequence of movements. How will you prepare anew?",
             (
                 PracticeOption("a", "依师法重习，让仪节安顿哀情。", "Rehearse with guidance so the forms can hold grief.",
                                "反复习礼，以人为努力使情感得到合宜表达。", "Repeated guided practice gives emotion fitting expression through deliberate effort.",
                                gold_cost=10, piety_change=35, stress_change=-10, learning_xp=35),
                 PracticeOption("b", "先安顿众人，再删去不合宜的铺陈。", "Settle the mourners and remove unsuitable display.",
                                "礼须养情，节制铺陈并非取消祭祀。", "Ritual nurtures feeling; restraint does not abolish the offering.",
                                gold_cost=15, piety_change=25, stress_change=-5, learning_xp=20),
                 PracticeOption("c", "动作整齐就够了，不必管心中如何。", "Correct movements suffice; their feelings do not matter.",
                                "失去养情之实，仪节易成为空文。", "Without cultivation of feeling, formal observance becomes hollow.",
                                piety_change=-20, stress_change=10),
             ),
             "情感安顿与师法取自荀学；不将礼仪结果写成祈雨改变自然。", "Guided ritual and emotional cultivation draw on Xunzi; rites do not control the weather.",
             ("xunzi",)),
    Practice("R06", "丘郊与配享之辨", "Distinguish Mound, Suburb and Paired Offerings",
             "祖祭之前，礼生拿来一份用于讲礼的祭图，竟把昊天与感生帝、圜丘与郊祭的说明混在一起。祖先配享的依据也因此含混。你不愿僭行国礼，但须决定如何澄清这份解说。",
             "Before an ancestral offering, an attendant brings a diagram for ritual instruction. It confuses Highest Heaven with the generating emperor, the Round Mound with the suburban sacrifice, and the grounds for ancestral paired offerings. You will not claim imperial rites, but the explanation needs examination.",
             (
                 PracticeOption("a", "据郑氏之说，分别考定祭者与配享。", "Use Zheng's distinctions to examine recipients and paired offerings.",
                                "先辨祭祀对象与资格，再说明丘郊之别。", "Distinguish recipients and standing before explaining the separate sacrifices.",
                                gold_cost=15, piety_change=30, learning_xp=40),
                 PracticeOption("b", "请礼生保存异说，祖祭只用已明之礼。", "Preserve the competing accounts and use established ancestral forms.",
                                "保留论礼证据，同时不将疑案变成僭祀。", "Preserve evidence for debate without turning uncertainty into an unauthorized sacrifice.",
                                gold_cost=10, piety_change=20, learning_xp=25),
                 PracticeOption("c", "只要祝辞气派，何必分得这样细？", "If the words impress, why distinguish so much?",
                                "忽略对象与配享，铺张无法弥补礼据不足。", "Display cannot remedy confusion about recipients and paired offerings.",
                                gold_cost=30, piety_change=-20, prestige_change=15),
             ),
             "事件为礼学问答与合资格祖祭，不让普通领主举行天子郊祀。", "This is ritual inquiry and an appropriate ancestral offering, not imperial suburban sacrifice by an ordinary lord.",
             ("zheng_wang",)),
    Practice("R07", "禘礼与祖源", "Di Rites and Ancestral Origins",
             "祖祭筹备时，礼生据一份旧解，把追享祖源写成向感生帝祈福。你所学的王氏礼说却不这样解释禘。如何面对这份有分歧的解说？",
             "An old interpretation used in preparation explains honoring ancestral origins as seeking favor from a generating emperor. The learning of Wang Su interprets di rites differently. How will you address this disagreement?",
             (
                 PracticeOption("a", "考明祖源，重写解说中的祭祀对象。", "Examine the ancestral origins and revise the explanation.",
                                "依王氏之义辨禘享祖源，不混同感生与祖先。", "Follow Wang's ancestral interpretation without conflating origins and a generating deity.",
                                gold_cost=15, piety_change=30, learning_xp=40),
                 PracticeOption("b", "并列郑王异说，先守合资格的家祭。", "Compare Zheng and Wang while keeping our family offering within its standing.",
                                "论礼可以容纳异说，实际祭礼仍须守其资格。", "Debate can preserve disagreement while actual observance respects ritual standing.",
                                gold_cost=10, piety_change=20, learning_xp=25),
                 PracticeOption("c", "把所有称谓都添上，总会有一个受享。", "Include every name; surely one will receive it.",
                                "不辨名实的堆砌，与据经考礼相背。", "Accumulating names without distinction abandons grounded ritual inquiry.",
                                gold_cost=25, piety_change=-20, prestige_change=10),
             ),
             "禘与郊丘为礼议对象，不授予玩家超出身份的祭祀资格。", "Di and mound-suburb relations are subjects of inquiry, not grants of ritual standing beyond the player's role.",
             ("zheng_wang",)),
    Practice("R10", "传注之间的问礼", "Ask about Rites between Commentaries",
             "一件丧服疑案摆在眼前。两种传注的用语相近，适用的亲属关系却不同。有人建议只用最贵的服饰，以免显得失礼；你仍须说明此礼为何合宜。",
             "A mourning case is before you. Two commentaries use similar words for different kinship relations. An attendant suggests choosing the most expensive garment to avoid seeming irreverent. Yet cost alone cannot explain the proper rite.",
             (
                 PracticeOption("a", "核对经文与旧注，再说明适用关系。", "Compare text and commentary, then explain the relevant relationship.",
                                "在具体名物与亲属关系中据经辨礼。", "Ground the rite in the text, particulars and kinship relation.",
                                gold_cost=15, piety_change=30, learning_xp=45),
                 PracticeOption("b", "向师长问明异同，也保留尚未解开的疑义。", "Consult a teacher and preserve what remains uncertain.",
                                "问学允许存疑，不能假装已通尽诸经。", "Inquiry allows uncertainty rather than claiming complete mastery.",
                                gold_cost=20, piety_change=25, stress_change=-5, learning_xp=30),
                 PracticeOption("c", "购置最贵的服饰，免去查考。", "Buy the finest garment and skip the inquiry.",
                                "贵重不能替代礼据和诚敬。", "Expense cannot replace grounds for the rite and sincere reverence.",
                                gold_cost=35, piety_change=-15, prestige_change=15),
             ),
             "匿名疑案不声称某一具体丧服条文已经考定；脚本不改原生亲属等级。", "The anonymous case does not pretend to settle a specific historical mourning rule or alter native kinship ranks.",
             ("jingshu", "zheng_wang")),
    Practice("R20", "问理而后行礼", "Inquire into Principle, Then Practice the Rite",
             "祖祭的礼文已誊清，但你发现自己只会复述步骤，未能说明为何如此。礼生问你，是先把经义和实际礼事相对照，还是只求在众人面前完成一次漂亮的祭礼？",
             "The ancestral forms are copied, yet you can repeat the sequence without explaining it. Will you relate the classical teaching to the actual rite, or merely seek an impressive performance before everyone?",
             (
                 PracticeOption("a", "问明此礼之理，再亲身习行。", "Examine the principle and practice the rite myself.",
                                "把穷理、持敬与报本连在实际行动中。", "Join inquiry, reverent attention and ancestral obligation through action.",
                                gold_cost=15, piety_change=35, stress_change=5, learning_xp=40),
                 PracticeOption("b", "先从简持敬，将疑处记下继续问学。", "Observe reverently and modestly, recording questions for further study.",
                                "承认理解未足，持续涵养而不废祭礼。", "Acknowledge incomplete understanding and continue cultivation without abandoning the offering.",
                                gold_cost=10, piety_change=25, learning_xp=25),
                 PracticeOption("c", "多添供物，别人看不出我未明其理。", "Add offerings so no one notices my lack of understanding.",
                                "炫示会遮蔽问学，礼物不能代替成德工夫。", "Display conceals neglected inquiry; gifts cannot replace cultivation.",
                                gold_cost=35, piety_change=-20, prestige_change=20),
             ),
             "家礼场景为玩法抽象，不预设朱学在南宋已是全儒家唯一正统。", "The family-rite scene does not presume exclusive Zhu orthodoxy in the Southern Song.",
             ("song_ming", "song_classics")),
    Practice("R21", "祝辞与本心", "The Offering Text and the Original Heart",
             "祭礼前读祝时，你发现其中赞扬自身德行的话，远过于自己真正做过的事。众人也许不会察觉，但你知道这份夸饰。发明本心，该如何落实在眼前？",
             "Reading the offering text, you notice praise of your virtue far beyond what you have actually done. Others may not notice, but you know the exaggeration. How will illuminating the heart take shape here?",
             (
                 PracticeOption("a", "删去自饰之辞，承认我仍须改过。", "Remove the self-flattery and admit that I still need correction.",
                                "显明本心须去自欺，承担名声和意念中的代价。", "Illuminating the heart requires resisting self-deception, even at a cost to reputation.",
                                piety_change=40, prestige_change=-15, stress_change=10, learning_xp=25),
                 PracticeOption("b", "据经问师，使祝辞与实际行为相称。", "Consult the text and a teacher so the words fit my conduct.",
                                "本心与问学可以相助，陆学不等于拒绝经典。", "The heart and study can support each other; Lu's learning does not reject the classics.",
                                gold_cost=15, piety_change=25, learning_xp=30),
                 PracticeOption("c", "既然我自认为有德，照旧读下去。", "If I believe myself virtuous, the words can stand.",
                                "自信不能把任性或夸饰变成道德根据。", "Confidence cannot turn whim or self-flattery into moral grounds.",
                                piety_change=-25, prestige_change=25, stress_change=-5),
             ),
             "本心之学仍有经书与礼仪，不回填阳明的成熟良知体系。", "Learning of the heart retains texts and rites without importing mature Yangming teaching.",
             ("song_ming", "song_classics")),
)

PRACTICES_BY_RITE_CODE = {item.rite_code: item for item in PRACTICES}


def validate_catalogue() -> None:
    """Reject broken catalogue references using runtime checks, not asserts."""
    if len(RITES) != 36 or len(TENETS) != 36:
        raise ValueError("The authored catalogue must preserve 36 rites and 36 tenets")
    if len(RITES_BY_CODE) != len(RITES) or len(TENETS_BY_CODE) != len(TENETS):
        raise ValueError("Duplicate catalogue code")
    for collection in (RITES, TENETS):
        if len({item.script_id for item in collection}) != len(collection):
            raise ValueError("Duplicate native definition ID")
        for item in collection:
            for key in item.source_keys:
                if key not in SOURCE_LINKS:
                    raise ValueError(f"Unknown historical source {key}: {item.code}")
    for rite in RITES:
        if len(set(rite.tenet_codes)) != 3:
            raise ValueError(f"Rite must have three distinct core tenets: {rite.code}")
        if any(code not in TENETS_BY_CODE for code in rite.tenet_codes):
            raise ValueError(f"Unknown core tenet: {rite.code}")
        if any(not 0 <= channel <= 255 for channel in rite.color):
            raise ValueError(f"Invalid map color: {rite.code}")
    if MAIN_RITE_ID not in {rite.script_id for rite in SAMPLE_RITES}:
        raise ValueError("Main rite must be part of the emitted sample package")
    if set(PRACTICES_BY_RITE_CODE) != set(SAMPLE_RITE_CODES):
        raise ValueError("Each emitted sample rite must have exactly one practice input")
    for practice in PRACTICES:
        if tuple(option.key for option in practice.options) != ("a", "b", "c"):
            raise ValueError(f"Practice options must use stable a/b/c keys: {practice.rite_code}")
        if any(option.gold_cost < 0 or option.learning_xp < 0 for option in practice.options):
            raise ValueError(f"Invalid practice costs: {practice.rite_code}")
        for key in practice.source_keys:
            if key not in SOURCE_LINKS:
                raise ValueError(f"Unknown practice source: {key}")
