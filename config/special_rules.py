#!/usr/bin/env python3
"""
CCF A类会议的DBLP查询规则和特殊处理规则
用于统一管理各个会议在DBLP中的venue名称映射和特殊处理逻辑

⚠️ 重要踩坑记录：

1. 【DBLP API点号问题】
   - 查询时使用无点号版本：'Proc ACM Program Lang'
   - 过滤时使用带点号版本：'Proc. ACM Program. Lang.'
   - 原因：DBLP API查询和返回结果的venue名称格式不一致

2. 【期刊发布模式】
   - OOPSLA/PLDI/POPL等会议从2017年开始论文发布在PACMPL期刊中
   - 不能直接查询会议名，需要查询期刊名然后过滤
   - 需要在DBLP网站确认具体的发布模式

3. 【Venue名称精确匹配】
   - 很多会议有companion、workshop等相关论文
   - 必须使用精确的venue名称过滤，避免获取到非主会议论文
   - 例如：CSCW vs CSCW Companion, FSE vs SIGSOFT FSE Companion

4. 【简化名称优于全名】
   - IEEE S&P: 使用'SP'而不是'IEEE Symposium on Security and Privacy'
   - IEEE VIS: 使用'IEEE VIS'而不是'IEEE Visualization'
   - 原因：DBLP中实际使用的是简化名称

5. 【年份相关的venue变化】
   - 有些会议的venue名称在不同年份可能有变化
   - 需要通过DBLP网站确认具体年份的venue名称
   - 建议先在DBLP网站手动搜索确认再配置
"""

# 特殊处理规则：某些会议需要特殊的查询或过滤逻辑
CONF_CCF_A_SPECIAL_RULES = {
    # 规则说明
    'default' : {
        'query_venue': str,  # 查询 venue 名称
        'filter_venues': list,  # 过滤 venue 名称
    },

    # SIGMOD: 主会议论文发布在PACMMOD期刊，需要特殊处理
    'sigmod': {
        'query_venue': 'Proc ACM Manag Data',  # 查询时使用无点号
        'filter_venues': ['Proc. ACM Manag. Data'],  # 过滤时匹配带点号
    },

    # VLDB: 期刊形式，venue名称包含点号
    'vldb': {
        'query_venue': 'Proc VLDB Endow',  # 查询时使用无点号
        'filter_venues': ['Proc. VLDB Endow.'],  # 过滤时匹配带点号
    },

    # OOPSLA: 论文从 2017 年开始发布在PACMPL期刊中
    'oopsla': {
        'query_venue': 'Proc ACM Program Lang',  # 查询PACMPL期刊（无点号）
        'filter_venues': ['Proc. ACM Program. Lang.'],  # 过滤时匹配带点号版本
    },

    # PLDI: 论文发布在PACMPL期刊中
    'pldi': {
        'query_venue': 'Proc ACM Program Lang',  # 查询PACMPL期刊
        'filter_venues': ['Proc. ACM Program. Lang.'],  # 过滤时匹配带点号
    },

    # POPL: 论文发布在PACMPL期刊中
    'popl': {
        'query_venue': 'Proc ACM Program Lang',  # 查询PACMPL期刊
        'filter_venues': ['Proc. ACM Program. Lang.'],  # 过滤时匹配带点号
    },

    # CSCW: 论文发布在PACMHCI期刊中
    'cscw': {
        'query_venue': 'Proc ACM Hum Comput Interact',  # 查询PACMHCI期刊（无点号）
        'filter_venues': ['Proc. ACM Hum. Comput. Interact.'],  # 过滤时匹配带点号版本
    },

    # UbiComp: 论文发布在IMWUT期刊中
    'ubicomp': {
        'query_venue': 'Proc ACM Interact Mob Wearable Ubiquitous Technol',  # 查询IMWUT期刊（无点号）
        'filter_venues': ['Proc. ACM Interact. Mob. Wearable Ubiquitous Technol.'],  # 过滤时匹配带点号版本
    },

    # USS: 与USENIX Security相同
    'usenix_atc': {
        'query_venue': 'USENIX ATC',  # 查询USENIX Security
        'filter_venues': ['USENIX ATC'],  # 只保留主会议论文
    },

    # USS: 与USENIX Security相同
    'uss': {
        'query_venue': 'USENIX Security',  # 查询USENIX Security
        'filter_venues': ['USENIX Security Symposium'],  # 只保留主会议论文
    },

    # fse_esec: 论文发布在PACMSE期刊中
    'fse_esec': {
        'query_venue': 'Proc ACM Softw Eng',  # 查询PACMSE期刊（无点号）
        'filter_venues': ['ESEC/SIGSOFT FSE'],  # 过滤时匹配带点号版本
    }
}

CONF_CCF_B_SPECIAL_RULES = {
    'default': {
        'query_venue': str,
        'filter_venues': list,
    },
    'naacl': {
        'query_venue': 'NAACL',
        'filter_venues': ['NAACL-HLT', 'NAACL-HTL', 'HLT-NAACL', 'NAACL'],
    }
}


def get_special_rules(conference_key: str) -> dict:
    """
        获取会议的特殊处理规则
    """
    conference_key = conference_key.lower()
    if conference_key in CONF_CCF_A_SPECIAL_RULES:
        return CONF_CCF_A_SPECIAL_RULES[conference_key]
    elif conference_key in CONF_CCF_B_SPECIAL_RULES:
        return CONF_CCF_B_SPECIAL_RULES[conference_key]
    else:
        return {}