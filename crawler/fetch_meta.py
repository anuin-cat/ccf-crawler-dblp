#!/usr/bin/env python3
"""
DBLP API 论文获取模块
通过DBLP API获取指定会议或期刊的论文信息

新增异步处理功能：
1. AsyncAbstractFetcher: 异步摘要获取器
2. 支持高并发异步请求
3. 更高效的I/O处理
"""

import os
import re
import sys
import json
import requests
import logging
import time
import asyncio
import aiohttp
import ssl

from typing import Dict, List, Optional, Tuple
from datetime import datetime
from pathlib import Path
from tqdm import tqdm
from fake_useragent import UserAgent
from bs4 import BeautifulSoup
from typing import Literal


# 添加项目根目录到路径
ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(ROOT_DIR)

# 导入CCF A类会议规则
from config.special_rules import get_special_rules
from config.venue import get_venue_name

class DBLPMetaFetcher:
    """DBLP论文获取器"""

    def __init__(self, data_dir: str):
        self.base_url = 'https://dblp.org/search/publ/api'
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'DBLP-Paper-Fetcher/1.0'
        })

        # 创建保存目录
        self.data_dir = data_dir
        if not os.path.exists(data_dir):
            os.makedirs(data_dir, exist_ok=True)

    def _send_request(self, query: str, max_hits: int = 1000, start_from: int = 0) -> Optional[Dict]:
        """
        发送DBLP API请求，带有重试机制

        Args:
            query: 查询字符串
            max_hits: 最大返回结果数
            start_from: 起始位置

        Returns:
            API响应的JSON数据
        """
        params = {
            'q': query,
            'format': 'json',
            'h': min(max_hits, 1000),  # DBLP API限制最大1000
            'f': start_from,
            'c': 0  # 不需要自动补全
        }

        # 重试配置：延迟时间（秒）
        retry_delays = [10, 30, 60, 120, 300]  # 10s, 30s, 1min, 2min, 5min
        max_retries = len(retry_delays)

        for attempt in range(max_retries + 1):  # +1 是因为第一次不算重试
            try:
                response = self.session.get(self.base_url, params=params, timeout=30)
                response.raise_for_status()
                return response.json()
            except Exception as e:
                if attempt < max_retries:
                    delay = retry_delays[attempt]
                    logging.warning(f"⚠️ DBLP API请求失败 (尝试 {attempt + 1}/{max_retries + 1}): {e}")
                    logging.info(f"🔄 等待 {delay} 秒后重试...")
                    time.sleep(delay)
                else:
                    logging.error(f"❌ DBLP API请求最终失败，已重试 {max_retries} 次: {e}")
                    return None

    def _extract_paper_info(self, hit: Dict) -> Dict:
        """
        从DBLP API响应中提取论文信息

        Args:
            hit: DBLP API返回的单篇论文数据

        Returns:
            标准化的论文信息字典
        """
        info = hit.get('info', {})

        # 添加DBLP特有的字段
        paper_info = info.copy()
        paper_info['key'] = hit.get('@id', '')  # DBLP key
        paper_info['dblp_url'] = f"https://dblp.org/rec/{hit.get('@id', '')}" if hit.get('@id') else ''

        # 确保ee字段是列表格式
        if 'ee' in paper_info and isinstance(paper_info['ee'], str):
            paper_info['ee'] = [paper_info['ee']]

        return paper_info

    def _get_all_papers_by_page(self, query: str) -> List[Dict]:
        """
        分页获取所有论文数据

        Args:
            query: 查询字符串

        Returns:
            所有论文信息列表
        """
        all_papers = []
        start_from = 0
        page_size = 1000

        while True:
            result = self._send_request(query, max_hits=page_size, start_from=start_from)

            if not result or 'result' not in result:
                break

            hits_data = result['result'].get('hits', {})
            total = int(hits_data.get('@total', 0))
            hits = hits_data.get('hit', [])
            
            if not hits:
                break

            # 处理当前页的论文
            for hit in hits:
                paper_info = self._extract_paper_info(hit)
                all_papers.append(paper_info)

            # 检查是否还有更多数据
            if len(all_papers) >= total or len(hits) < page_size:
                break

            start_from += page_size
            time.sleep(0.5)  # 避免请求过快

        return all_papers

    def _replace_special_characters(self, text: any) -> str:
        if not text: return ''
        text = str(text)
        # 使用正则表达式替换所有非字母字符为空格
        text = re.sub(r'[^a-zA-Z\s]', ' ', text)
        # 将多个连续空格替换为单个空格
        text = re.sub(r'\s+', ' ', text)
        # 去除首尾空格
        text = text.strip()
        # 转换为小写
        text = text.lower()

        return text

    def fetch_papers(self, venue_name: str, year: int) -> List[Dict]:
        """
        获取指定会议/期刊和年份的所有论文

        Args:
            venue_name: 会议或期刊名称 (如 'tocs', 'sigmod', 'vldb')
            year: 年份

        Returns:
            论文信息列表
        """
        # 1. 获取正确的venue名称
        dblp_venue_name = get_venue_name(venue_name, year)
        query = f"venue:{dblp_venue_name} year:{year}"

        # 2. 获取论文
        papers = self._get_all_papers_by_page(query)

        # 3. 过滤论文，只保留精确匹配的venue（DBLP API查询和返回结果的venue名称格式可能不一致）
        filtered_papers = []

        # 确定要匹配的venue名称列表
        target_venues = [self._replace_special_characters(dblp_venue_name)] # 原始 venue 名称
        special_rules = get_special_rules(venue_name) # 特殊规则（有些名称多）
        if 'filter_venues' in special_rules:
            target_venues.extend([self._replace_special_characters(venue) for venue in special_rules['filter_venues']])

        for paper in papers:
            paper_venue = paper.get('venue', '')
            # 将 paper_venue 转换为一个字符串列表
            if isinstance(paper_venue, list):
                paper_venue = [self._replace_special_characters(venue) for venue in paper_venue]
            else:
                paper_venue = [self._replace_special_characters(paper_venue)]

            # 检查是否匹配任何目标venue名称（查看是否有交集）
            if set(paper_venue).intersection(target_venues):
                filtered_papers.append(paper)

        # 4. 过滤前信息统计
        type_counts_before = {}
        venue_counts_before = {}
        for p in papers:
            # 4.1 类型分布
            paper_type = p.get('type', 'unknown')
            type_counts_before[paper_type] = type_counts_before.get(paper_type, 0) + 1

            # 4.2 来源分布
            paper_venue = p.get('venue', 'unknown')
            if isinstance(paper_venue, list):
                paper_venue = ', '.join(paper_venue) if paper_venue else 'unknown'
            elif not isinstance(paper_venue, str):
                paper_venue = str(paper_venue) if paper_venue else 'unknown'
            venue_counts_before[paper_venue] = venue_counts_before.get(paper_venue, 0) + 1

        logging.info(f"✅ {dblp_venue_name}'{year}: 过滤前 {len(papers)} -> 过滤后 {len(filtered_papers)}")

        # 5. 过滤后信息统计
        type_counts = {}
        venue_counts = {}
        for p in filtered_papers:
            # 5.1 类型分布
            paper_type = p.get('type', 'unknown')
            type_counts[paper_type] = type_counts.get(paper_type, 0) + 1

            # 5.2 来源分布
            paper_venue = p.get('venue', 'unknown')
            if isinstance(paper_venue, list):
                paper_venue = ', '.join(paper_venue) if paper_venue else 'unknown'
            elif not isinstance(paper_venue, str):
                paper_venue = str(paper_venue) if paper_venue else 'unknown'
            venue_counts[paper_venue] = venue_counts.get(paper_venue, 0) + 1

        return filtered_papers, type_counts, venue_counts, type_counts_before, venue_counts_before

    def check_paper_exists(self, venue_name: str, year: int) -> bool:
        """
        检查指定会议/期刊和年份的论文数据是否已经存在

        Args:
            venue_name: 会议或期刊名称
            year: 年份

        Returns:
            如果数据文件已存在则返回True，否则返回False
        """
        clean_venue_name = venue_name.replace(' ', '_').replace('.', '').replace('/', '_')
        filename = f"{clean_venue_name}_{year}.json"
        filepath = os.path.join(self.data_dir, filename)
        return os.path.exists(filepath)

    def save_papers_to_json(self, papers: List[Dict], venue_name: str, year: int,
                           type_counts: Dict, venue_counts: Dict,
                           type_counts_before: Dict, venue_counts_before: Dict,
                           total_papers_before: int) -> str:
        """
        保存论文数据到JSON文件
        Args:
            papers: 过滤后的论文数据列表
            venue_name: 会议/期刊名称
            year: 年份
            type_counts: 过滤后论文类型分布统计
            venue_counts: 过滤后论文来源分布统计
            type_counts_before: 过滤前论文类型分布统计
            venue_counts_before: 过滤前论文来源分布统计
            total_papers_before: 过滤前论文总数
        Returns:
            保存的文件路径
        """
        # 1. 清理文件名中的特殊字符
        clean_venue_name = venue_name.replace(' ', '_').replace('.', '').replace('/', '_')
        filename = f"{clean_venue_name}_{year}.json"
        filepath = os.path.join(self.data_dir, filename)

        # 2. 添加元数据和统计信息
        data_to_save = {
            'metadata': {
                'venue_name': venue_name,
                'year': year,
                'total_papers': len(papers),
                'fetch_time': datetime.now().isoformat(),
                'source': 'DBLP API',
                'type_distribution': type_counts,
                'venue_distribution': venue_counts
            },
            'metadata_before_filtered': {
                'total_papers': total_papers_before,
                'type_distribution': type_counts_before,
                'venue_distribution': venue_counts_before
            },
            'papers': papers
        }

        # 3. 保存到JSON文件
        if total_papers_before == 0:
            return None
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data_to_save, f, ensure_ascii=False, indent=2)

        return filepath

    def get_papers_by_venue_and_year(self, venue_name: str, year: int) -> str:
        """
        根据会议/期刊名称和年份获取论文，并保存为JSON格式

        Args:
            venue_name: 会议或期刊名称
            year: 年份

        Returns:
            保存的文件路径
        """
        # 1. 查看论文数据是否已经存在（已经存在对应的 save 的文件的话就跳过即可）
        if self.check_paper_exists(venue_name, year):
            logging.info(f"ℹ️ 论文数据已存在，跳过获取: {venue_name} {year}")
            return None
        
        # 2. 获取论文数据
        papers, type_counts, venue_counts, type_counts_before, venue_counts_before = self.fetch_papers(venue_name, year)
        total_papers_before = sum(type_counts_before.values())

        # 3. 保存论文数据
        return self.save_papers_to_json(papers, venue_name, year, type_counts, venue_counts,
                                       type_counts_before, venue_counts_before, total_papers_before)

