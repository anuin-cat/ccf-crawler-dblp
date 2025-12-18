from typing import Literal

# A 类会议名称列表
PUB_CONF_A = [
    # ========== 一、计算机体系结构/并行与分布计算/存储系统 ==========
    'ppopp', # ✅
    'fast', # ✅
    'dac', # ✅
    'hpca', # ✅
    'micro', # ✅
    'sc', # 搜索结果过多
    'asplos', # ✅
    'isca', # ✅
    'usenix_atc', # ✅
    'eurosys', # ✅

    # ========== 二、计算机网络 ==========
    'sigcomm', # ✅
    'mobicom', # ✅
    'infocom', # ✅
    'nsdi', # ✅

    # ========== 三、网络与信息安全 ==========
    'ccs', # ✅
    'eurocrypt', # ✅
    'sp', # ✅
    'crypto', # ✅
    'uss', # ✅ USENIX Security (缩写)
    'ndss', # ✅

    # ========== 四、软件工程/系统软件/程序设计语言 ==========
    'pldi', # 混到了其他期刊中
    'popl', # 和 pldi 混合了
    'fse_esec', # 暂时有点问题，要调整一下检索名
    'sosp', # ✅
    'ooplsa', # 检索为空
    'ase', # ✅
    'icse', # ✅
    'issta', # ✅
    'osdi', # ✅
    'fm', # ✅

    # ========== 五、数据库/数据挖掘/内容检索 ==========
    'sigmod', # ✅
    'kdd', # ✅
    'icde', # ✅
    'sigir', # ✅
    # 'vldb', # vldb 不发布到会议中，发表于期刊中


    # ========== 六、计算机科学理论 ==========
    'stoc', # ✅
    'soda', # ✅
    'cav', # ✅
    'focs', # ✅
    'lics', # ✅

    # ========== 七、计算机图形学与多媒体 ==========
    'mm', # ✅
    'siggraph', # ✅
    'vr', # x 检索即失败
    'vis', # x 数量对不上，应该 120 结果 53 篇
    
    # ========== 八、人工智能 ==========
    'aaai', # ✅
    'nips', # ✅
    'acl', # ✅
    'cvpr', # ✅
    'iccv', # ✅
    'icml', # ✅
    'ijcai', # ✅

    # ========== 九、人机交互与普适计算 ==========
    'cscw', # 搜索数量极少，不对劲，正常接收了 2235 篇
    'chi', # ✅
    'ubicomp', # 搜索数量极少，不对劲，正常接收了 764 篇
    'uist', # ✅ 但是数量较少，可能是官方的问题

    # ========== 十、交叉/综合/新兴 ==========
    'www', # ✅
    'rtss', # ✅
    'wine', # ✅

    # ========== 十一、其他 ==========
    'iclr', # ✅
]

# B 类会议名称列表
PUB_CONF_B = [
    # ========== 一、计算机体系结构/并行与分布计算/存储系统 ==========

    # ========== 二、计算机网络 ==========

    # ========== 三、网络与信息安全 ==========

    # ========== 四、软件工程/系统软件/程序设计语言 ==========

    # ========== 五、数据库/数据挖掘/内容检索 ==========
    # 'cikm',
    # 'wsdm',
    # 'pods',
    # 'dasfaa',
    # 'ecml-pkdd',
    # 'iswc',
    # 'icdm',
    # 'icdt',
    # 'edbt',
    # 'cidr',
    # 'sdm',
    # 'recsys',

    # ========== 六、计算机科学理论 ==========

    # ========== 七、计算机图形学与多媒体 ==========
    'icmr',
    # 'i3d', # 检索不到
    # 'sca',
    # 'dcc',
    # 'eurographics',
    # 'eurovis',
    # 'sgp',
    # 'egsr',
    'icassp',
    'icme',
    # 'ismar',
    # 'pg', # 和期刊混合了
    
    # ========== 八、人工智能 ==========
    'colt',
    'emnlp',
    # 'ecai',
    'eccv',
    # 'icra',
    'icaps',
    # 'iccbr',
    'coling',
    # 'uai',
    # 'aamas',
    # 'ppsn',
    'naacl',

    # ========== 九、人机交互与普适计算 ==========

    # ========== 十、交叉/综合/新兴 ==========
]

# 期刊名称列表
PUB_JOURNALS_A = [
    # ========== 一、计算机体系结构/并行与分布计算/存储系统 ==========
    'tocs',
    'tos',
    'tcad',
    'tc',
    'tpds',
    'taco',

    # ========== 二、计算机网络 ==========
    'jsac',
    'tmc',
    'ton',

    # ========== 三、网络与信息安全 ==========
    'tdsc',
    'tifs',
    'joc',

    # ========== 四、软件工程/系统软件/程序设计语言 ==========
    'toplas',
    'tosem',
    'tse',
    'tsc',

    # ========== 五、数据库/数据挖掘/内容检索 ==========
    'tods',
    'tois',
    'tkde',
    'vldb',  # vldb 只获取期刊结果

    # ========== 六、人工智能 ==========
    'ai',
    'tpami',
    'ijcv',
    'jmlr',

    # ========== 七、计算机科学理论 ==========
    'tit',
    'iandc',
    'sicomp',

    # ========== 八、计算机图形学与多媒体 ==========
    'tog',
    'tip',
    'tvcg',

    # ========== 九、人机交互与普适计算 ==========
    'tochi',
    'ijhcs'

    # ========== 十、交叉/综合/新兴 ==========
    'jacm',
    'pieee' # 全称 Proceedings of the IEEE
    'scis'
]

# A类 DBLP venue 名称特殊映射表
CONF_A_VENUE_MAPPING = {
    # 需要特殊处理的会议名称
    'usenix_atc': 'USENIX ATC',  # USENIX Annual Technical Conference
    # 'fse_esec': 'Proc ACM Softw Eng',
    'fse_esec': 'SIGSOFT FSE',
    'esec': 'SIGSOFT FSE',  # FSE/ESEC的另一个名称
    'sp': 'SP',  # IEEE S&P的简化名称
    'uss': 'USENIX Security',  # USENIX Security的简称
    'mm': 'ACM Multimedia',  # ACM MM
    'vr': 'IEEE VR',
    'vis': 'IEEE VIS',
    'sc': 'SC$',

    # 需要特殊处理的期刊发表会议
    'pldi': 'Proc ACM Program Lang',  # PLDI论文发布在PACMPL期刊
    'popl': 'Proc ACM Program Lang',  # POPL论文发布在PACMPL期刊
    'oopsla': 'Proc ACM Program Lang',  # OOPSLA论文发布在PACMPL期刊
    'sigmod': 'Proc ACM Manag Data',  # SIGMOD主会议论文发布在PACMMOD期刊
    'vldb': 'Proc VLDB Endow',  # VLDB期刊的实际名称
    'cscw': 'Proc ACM Hum Comput Interact',  # CSCW论文发布在PACMHCI期刊
    'ubicomp': 'Proc ACM Interact Mob Wearable Ubiquitous Technol',  # UbiComp论文发布在IMWUT期刊
}

# B类 DBLP venue 名称特殊映射表
CONF_B_VENUE_MAPPING = {
    'i3d': 'SI3D',
    'pg': 'PG$'
}


def get_venue_name(conference_key: str, year: int=None) -> str:
    """
    获取会议在DBLP中的venue名称
    """
    # 特殊处理年份相关的venue名称变化
    if year is not None and conference_key.lower() == 'nips':
        return 'NIPS' if year < 2018 else 'NeurIPS'

    # 检查是否在特殊映射表中
    if conference_key.lower() in CONF_A_VENUE_MAPPING:
        return CONF_A_VENUE_MAPPING[conference_key.lower()]
    if conference_key.lower() in CONF_B_VENUE_MAPPING:
        return CONF_B_VENUE_MAPPING[conference_key.lower()]

    return conference_key.upper()

def get_all_venue_by_rule(ccf: Literal['a', 'b', 'c'], classification: Literal['conf', 'journal']) -> str:
    """
    根据 CCF等级 和 期刊/会议类型 获取对应的所有 venue 的名称
    """
    if ccf == 'a' and classification == 'conf':
        return PUB_CONF_A
    elif ccf == 'a' and classification == 'journal':
        return PUB_JOURNALS_A
    elif ccf == 'b' and classification == 'conf':
        return PUB_CONF_B
    else:
        raise NotImplementedError(f"CCF {ccf} {classification} not implemented")