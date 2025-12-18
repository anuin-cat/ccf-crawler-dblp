import os
import sys

# 添加项目根目录到路径
ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(ROOT_DIR)

import logging
import time
import asyncio
import argparse

from crawler.fetch_meta import main_papers_meta
from crawler.fetch_abstract import main_papers_abstract
from utils import info_by_dir

if __name__ == "__main__":
    # 解析命令行参数
    parser = argparse.ArgumentParser(description='CCF DBLP 爬虫程序')
    parser.add_argument('-ccf', type=str, default='b', help='CCF 等级 (默认: b)')
    parser.add_argument('-c', '--classification', type=str, default='conf', help='论文分类类型, 可选值: conf, journal')
    parser.add_argument('-m', '--max-concurrent', type=int, default=20, help='最大并发数 (默认: 20)')
    parser.add_argument('-p', '--proxy-pool-size', type=int, default=10, help='代理池大小 (默认: 10)')
    
    args = parser.parse_args()
    
    classification = args.classification
    ccf = args.ccf

    # 1. 定义保存目录
    data_dir = os.path.join(ROOT_DIR, 'data', 'paper', f'{classification}_{ccf}')
    log_dir = os.path.join(ROOT_DIR, 'data', 'logs')
    
    # 确保目录存在
    os.makedirs(data_dir, exist_ok=True)
    os.makedirs(log_dir, exist_ok=True)

    # 2. 配置日志
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler(os.path.join(log_dir, f'log_{int(time.time())}.txt'), mode='w', encoding='utf-8')
        ]
    )
    
    logging.info("=" * 60)
    logging.info("🚀 开始运行 CCF DBLP 爬虫程序")
    logging.info(f"📁 数据保存目录: {data_dir}")
    logging.info(f"📝 日志保存目录: {log_dir}")
    logging.info(f"📋 分类: {classification}, CCF等级: {ccf}")
    logging.info(f"⚙️ 最大并发数: {args.max_concurrent}, 代理池大小: {args.proxy_pool_size}")
    logging.info("=" * 60)
    
    # 3. 获取论文元信息
    logging.info("\n📊 步骤 1/2: 获取论文元信息...")
    main_papers_meta(data_dir, ccf=ccf, classification=classification)
    info_by_dir(data_dir)

    # 4. 获取论文摘要（异步版本）
    logging.info("\n📄 步骤 2/2: 获取论文摘要...")
    asyncio.run(main_papers_abstract(data_dir, max_concurrent=args.max_concurrent, proxy_pool_size=args.proxy_pool_size))
    info_by_dir(data_dir)
