import os
import re
import sys
import asyncio
import logging
import random
import time
import requests
from dotenv import load_dotenv

from typing import Dict, List, Optional
from urllib.parse import urlparse
from playwright.async_api import async_playwright, BrowserContext

# 加载环境变量
load_dotenv('.env.local')

# 添加项目根目录到路径
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(ROOT_DIR)

class ProxyPool:
    """代理池管理器 - 支持代理失效时自动降级到本机地址"""
    def __init__(self, pool_size: int=10):
        '''
        每个 proxy item 都是一个 map:
        {"ip":"112.250.135.134", "port":40025, start_time: time.time(), expire_time: time.time() + ttl}
        '''

        self.pool_size = pool_size

        # 每个 item_map {} 包含 ip, port, start_time, expire_time
        self.cur_proxys = []
        self.cur_index = 0

        # 构建请求参数（需要在检查配置之前初始化）
        self.ttl = 180 - 10 # 代理有效期 (10s 预留)
        self.url = 'http://api.shenlongip.com/ip'
        self.params = {
            'key': os.getenv('PROXY_API_KEY'),
            'protocol': 2,
            'mr': 1,
            'pattern': 'json',
            'need': 1000,
            'count': 1,
            'sign': os.getenv('PROXY_API_SIGN')
        }

        # 检查代理配置是否可用（在 params 初始化之后）
        self.proxy_enabled = self._check_proxy_config()
        
        if not self.proxy_enabled:
            logging.warning("⚠️  代理配置不可用（环境变量缺失或无效），将使用本机地址进行请求")
        else:
            logging.info("✅ 代理配置已启用，将使用代理池进行请求")
    
    def _check_proxy_config(self) -> bool:
        """检查代理配置是否可用"""
        try:
            # 检查必要的环境变量
            api_key = os.getenv('PROXY_API_KEY')
            api_sign = os.getenv('PROXY_API_SIGN')
            
            if not api_key or not api_sign:
                return False
            
            # 尝试获取一个代理来验证配置是否有效
            test_proxy = self._get_new_proxy_silent()
            return test_proxy is not None
        except Exception as e:
            logging.debug(f"代理配置检查失败: {e}")
            return False
    
    def _get_new_proxy_silent(self, depth: int = 0) -> Optional[Dict[str, str]]:
        """静默获取新代理（不输出警告日志，用于配置检查）"""
        try:
            response = requests.get(
                self.url,
                params=self.params,
                timeout=5  # 配置检查时使用更短的超时
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get('code') == 200 and data.get('data'):
                    proxy_info = data['data'][0]
                    proxy_info['start_time'] = time.time()
                    proxy_info['expire_time'] = proxy_info['start_time'] + self.ttl
                    return proxy_info
        except Exception:
            pass
        
        return None

    def _get_new_proxy(self, depth: int = 0) -> Optional[Dict[str, str]]:
        '''从神龙代理获取新的代理'''
        # 如果代理未启用，直接返回 None
        if not self.proxy_enabled:
            return None
            
        try:
            # 1. 获取代理 API 请求
            response = requests.get(
                self.url,
                params=self.params,
                timeout=10
            )

            # 2. 解析代理信息
            if response.status_code == 200:
                data = response.json()
                if data.get('code') == 200 and data.get('data'):
                    proxy_info = data['data'][0]
                    proxy_info['start_time'] = time.time()
                    proxy_info['expire_time'] = proxy_info['start_time'] + self.ttl # 180s 后失效
                    return proxy_info # {ip:xx, port:xx, start_time: time.time(), expire_time: time.time() + 180}
            
            # 3. 获取失败
            if depth == 0:  # 只在第一次失败时记录警告
                logging.warning(f"获取新 proxy 失败，将使用本机地址: {response.status_code}")
            if depth < 2:  # 减少重试次数
                time.sleep(1)
                return self._get_new_proxy(depth + 1)
        except Exception as e:
            if depth == 0:
                logging.warning(f"获取代理时发生异常，将使用本机地址: {e}")
        
        return None

    def _refresh_proxys(self):
        '''刷新所有代理（先判断是否需要刷新）'''
        # 如果代理未启用，直接返回
        if not self.proxy_enabled:
            return
            
        # 1. 当代理池为空时，直接获取最大数量的代理
        if len(self.cur_proxys) == 0:
            self.cur_proxys = [self._get_new_proxy() for _ in range(self.pool_size)]
            self.cur_proxys = [proxy for proxy in self.cur_proxys if proxy]
            return

        # 2. 当代理池不为空时，检查每个代理是否过期（expire_time < time.time()）
        expired_proxies = []
        for proxy in self.cur_proxys:
            if proxy['expire_time'] < time.time():
                expired_proxies.append(proxy)
        
        for proxy in expired_proxies:
            self.cur_proxys.remove(proxy)
            new_proxy = self._get_new_proxy()
            if new_proxy: # 只添加有效的代理
                self.cur_proxys.append(new_proxy)

        # 3. 如果代理池中有效数量不足，补充代理
        self.cur_proxys = [proxy for proxy in self.cur_proxys if proxy]
        if len(self.cur_proxys) < self.pool_size:
            needed = self.pool_size - len(self.cur_proxys)
            new_proxys = [self._get_new_proxy() for _ in range(needed)]
            new_proxys = [proxy for proxy in new_proxys if proxy]

            self.cur_proxys.extend(new_proxys)

    def get_proxy(self) -> Optional[Dict[str, str]]:
        """从代理池顺序获取一个 ip，如果代理不可用则返回 None（表示使用本机地址）"""
        # 如果代理未启用，直接返回 None
        if not self.proxy_enabled:
            return None
            
        # 1. 刷新代理池
        self._refresh_proxys()
        if len(self.cur_proxys) == 0: 
            return None

        # 2. 获取代理
        self.cur_index = self.cur_index % len(self.cur_proxys)
        proxy = self.cur_proxys[self.cur_index]
        self.cur_index += 1

        return proxy

    def get_proxy_url(self, with_auth: bool = True) -> Optional[str]:
        '''
        获取代理 url
        
        如果代理不可用或获取失败，返回 None（表示使用本机地址）
        这对于 aiohttp 和 Playwright 都是有效的，它们会将 None 视为不使用代理
        '''
        proxy = self.get_proxy()
        if proxy:
            # 从环境变量获取代理认证信息
            proxy_username = os.getenv('PROXY_USERNAME')
            proxy_password = os.getenv('PROXY_PASSWORD')

            if proxy_username and proxy_password and with_auth:
                # 带认证的代理格式，统一使用HTTP协议
                proxy_url = f"http://{proxy_username}:{proxy_password}@{proxy['ip']}:{proxy['port']}"
            else:
                # 不带认证的代理格式
                proxy_url = f"http://{proxy['ip']}:{proxy['port']}"

            return proxy_url

        # 返回 None 表示使用本机地址
        return None
    
    def remove_proxy(self, ip: str):
        '''
        删除代理，并根据 ip 池上限重新补充

        Args:
            ip: 代理 ip（也有可能是 url，所以要使用包含来判断）
        '''
        # 如果代理未启用或 ip 为 None，直接返回
        if not self.proxy_enabled or not ip:
            return

        # 1. 删除代理
        self.cur_proxys = [proxy for proxy in self.cur_proxys if proxy['ip'] not in ip]

        # 2. 刷新代理池
        self._refresh_proxys()

class PlaywrightDriver:
    """基于 Playwright 的异步驱动管理器 - 支持真正的并发和自定义代理"""
    
    def __init__(self, max_concurrent: int = 5, proxy_pool_size: int = 5, headless: bool = False, timeout: int = 30000):
        """
        初始化 Playwright 驱动管理器
        
        Args:
            max_concurrent: 最大并发数
            headless: 是否无头模式
            timeout: 页面超时时间（毫秒）
        """
        self.max_concurrent = max_concurrent
        self.headless = headless
        self.timeout = timeout
        
        # 并发控制 (作为 async with 的上下文管理器)
        self.semaphore = asyncio.Semaphore(max_concurrent)

        # proxy 控制池
        self.proxy_pool = ProxyPool(pool_size=proxy_pool_size)
        
        # Playwright 实例 (使用 start 和 close 管理生命周期)
        self.playwright = None
        self.browser = None
        self._is_initialized = False
        
    async def __aenter__(self):
        """异步上下文管理器入口"""
        await self.start()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """异步上下文管理器出口"""
        await self.close()
        
    async def start(self):
        """启动 Playwright 浏览器"""
        if not self._is_initialized:
            self.playwright = await async_playwright().start()
            self.browser = await self.playwright.chromium.launch(
                headless=self.headless,
                args=[
                    '--disable-blink-features=AutomationControlled',
                    '--disable-dev-shm-usage',
                    '--no-sandbox',
                    '--disable-gpu',
                    '--disable-images',  # 禁用图片加载以提高速度
                    '--disable-javascript',  # 如果不需要JS可以禁用
                    '--disable-extensions',       # 禁用扩展
                    '--disable-plugins',          # 禁用插件
                    '--disable-web-security',     # 禁用web安全检查
                    '--disable-features=TranslateUI',  # 禁用翻译
                    '--no-first-run',             # 跳过首次运行
                    '--no-default-browser-check', # 跳过默认浏览器检查
                    '--disable-default-apps',     # 禁用默认应用
                    '--disable-logging',             # 禁用日志
                    '--log-level=3',                 # 只显示致命错误
                    '--silent',                      # 静默模式
                ]
            )
            self._is_initialized = True
            logging.info("Playwright 浏览器已启动")

    async def close(self):
        """关闭 Playwright 浏览器"""
        if self.browser:
            await self.browser.close()
            self.browser = None
            
        if self.playwright:
            await self.playwright.stop()
            self.playwright = None
            
        self._is_initialized = False
        logging.info("Playwright 浏览器已关闭")
        
    def _parse_proxy_url(self, proxy_url: str) -> Dict:
        """
        解析代理 URL，支持带认证的代理
        
        Args:
            proxy_url: 代理URL，格式如 'http://user:pass@host:port' 或 'host:port'
            
        Returns:
            解析后的代理配置字典
        """
        if not proxy_url:
            return None
            
        proxy_config = {}
        
        # 处理不同格式的代理URL
        if '://' in proxy_url:
            parsed = urlparse(proxy_url)
            proxy_config['server'] = f"{parsed.scheme}://{parsed.hostname}:{parsed.port}"
            if parsed.username and parsed.password:
                proxy_config['username'] = parsed.username
                proxy_config['password'] = parsed.password
        else:
            # 处理 user:pass@host:port 或 host:port 格式
            if '@' in proxy_url:
                auth_part, host_part = proxy_url.split('@', 1)
                if ':' in auth_part:
                    username, password = auth_part.split(':', 1)
                    proxy_config['username'] = username
                    proxy_config['password'] = password
                    
                if ':' in host_part:
                    host, port = host_part.split(':', 1)
                else:
                    host, port = host_part, '80'
                    
                proxy_config['server'] = f"http://{host}:{port}"
            else:
                # 简单的 host:port 格式
                if ':' in proxy_url:
                    host, port = proxy_url.split(':', 1)
                else:
                    host, port = proxy_url, '80'
                proxy_config['server'] = f"http://{host}:{port}"
                
        return proxy_config
        
    async def _create_context(self, proxy_url: str = None) -> BrowserContext:
        """
        创建浏览器上下文，支持自定义代理
        
        Args:
            proxy_url: 代理URL
            
        Returns:
            BrowserContext 实例
        """
        context_options = {
            'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'viewport': {'width': 1024, 'height': 768},
            'ignore_https_errors': True,
        }
        
        # 配置代理
        proxy_config = self._parse_proxy_url(proxy_url)
        if proxy_config:
            context_options['proxy'] = proxy_config
            
        return await self.browser.new_context(**context_options)
        
    async def wait_for_any_selector(self, page, selectors: List[str], timeout: int = 30000) -> Optional[str]:
        """
        简化版本：等待多个选择器中的任何一个出现，返回触发的选择器名称
        
        Args:
            page: Playwright 页面对象
            selectors: 选择器列表
            timeout: 超时时间（毫秒）
            
        Returns:
            触发的选择器名称，如果超时或出错则返回 None
        """
        async def wait_task(selector, index):
            try:
                await page.wait_for_selector(selector, timeout=timeout)
                return (selector, index)  # 返回选择器和索引
            except:
                return None
        
        # 创建 Task 对象
        tasks = [
            asyncio.create_task(wait_task(selector, i))
            for i, selector in enumerate(selectors)
        ]
        
        try:
            # 等待第一个完成
            done, pending = await asyncio.wait(
                tasks,
                return_when=asyncio.FIRST_COMPLETED,
                timeout=timeout / 1000
            )
            
            # 取消未完成的任务
            for task in pending:
                task.cancel()
            
            # 获取结果
            for task in done:
                result = task.result()
                if result:  # 如果不是 None
                    selector, index = result
                    logging.info(f"选择器 '{selector}' (索引 {index}) 被触发")
                    return selector
                    
        except asyncio.TimeoutError:
            logging.warning(f"等待选择器超时: {selectors}")
        except Exception as e:
            logging.error(f"等待选择器出错: {e}")
        finally:
            # 确保所有任务都被取消
            for task in tasks:
                if not task.done():
                    task.cancel()
        
        return None

    async def safe_get(self, url: str, wait_ids: list[str], max_retries: int = 5, sleep_time: int = 0) -> Optional[str]:
        """
        安全地访问单个URL - 选择器等待（更快）
        """
        if not self._is_initialized:
            print("Playwright 浏览器未启动，使用 self.start() 启动")
            
        async with self.semaphore:
            for attempt in range(max_retries):
                context = None
                page = None
                try:
                    cur_proxy_url = self.proxy_pool.get_proxy_url(with_auth=True)
                    context = await self._create_context(cur_proxy_url)
                    page = await context.new_page()

                    
                    if wait_ids:
                        # 提供了触发元素
                        await page.goto(url, wait_until='commit', timeout=self.timeout)
                        selectors = [
                            'text=cloudflare',
                            'text=Cloudflare', 
                            'text=Checking your browser',
                            *wait_ids
                        ]
                        
                        # 使用简化版本
                        triggered = await self.wait_for_any_selector(page, selectors, self.timeout)

                        # 休眠2s
                        await asyncio.sleep(sleep_time)
                        
                        if triggered:
                            # 检查是否是 Cloudflare 相关
                            if any(keyword in triggered.lower() for keyword in ['cloudflare', 'checking']):
                                if cur_proxy_url:  # 只有在使用代理时才移除
                                    self.proxy_pool.remove_proxy(cur_proxy_url)
                                logging.warning(f"检测到反爬保护: {triggered}，{'更换代理' if cur_proxy_url else '使用本机地址重试'} (尝试 {attempt + 1}/{max_retries}): {url}")
                                continue
                            
                            # 如果是目标选择器
                            if triggered in wait_ids:
                                try:
                                    # text = await page.inner_text(wait_id)
                                    # logging.info(f"成功获取指定元素内容: {url}")
                                    # return text
                                    return await page.content()
                                except Exception as e:
                                    logging.warning(f"获取元素内容失败: {url} - {e}")
                                    return await page.content()
                        else:
                            logging.warning(f"未找到任何目标元素 (尝试 {attempt + 1}/{max_retries}): {url}")
                    else:
                        # 没有提供触发元素
                        # 等待 domcontentloaded 后，检查是否是 Cloudflare 相关
                        await page.goto(url, wait_until='domcontentloaded', timeout=self.timeout)
                        selectors = [
                            'text=cloudflare',
                            'text=Cloudflare', 
                            'text=Checking your browser',
                        ]

                        try:
                            page_content = await page.content()
                            # 查看是否有任何 selectors 中的 item 在 page 中（是否是 Cloudflare 相关）
                            if any(selector in page_content for selector in selectors):
                                if cur_proxy_url:  # 只有在使用代理时才移除
                                    self.proxy_pool.remove_proxy(cur_proxy_url)
                                logging.warning(f"检测到反爬保护，{'更换代理' if cur_proxy_url else '使用本机地址重试'} (尝试 {attempt + 1}/{max_retries}): {url}")
                                continue
                            else:
                                return page_content
                        except Exception as e:
                            logging.warning(f"获取元素内容失败: {url} - {e}")
                            return await page.content()

                except Exception as top_e:
                    logging.warning(f"访问URL失败 (尝试 {attempt + 1}/{max_retries}): {url} - {top_e}")
                    if attempt < max_retries - 1:
                        await asyncio.sleep(random.uniform(1, 3))
                finally:
                    if page and not page.is_closed(): await page.close()
                    if context: await context.close()
            
            return None

    async def safe_get_batch(self, urls: List[str], wait_id: str, max_retries: int = 3) -> List[Optional[str]]:
        """
        批量并发访问多个URL
        
        Args:
            urls: URL列表
            wait_id: 等待的选择器ID
            max_retries: 最大重试次数

        Returns:
            页面内容列表，与输入URL顺序对应
        """
        if not self._is_initialized:
            await self.start()

        # 创建异步任务
        tasks = [self.safe_get(url, '#abstract', max_retries) for url in urls]
        
        # 执行所有任务
        results = await asyncio.gather(*tasks)
        
        # 处理异常结果
        processed_results = []
        for result in results:
            processed_results.append(result)

        success_count = sum(1 for r in processed_results if r)
        logging.info(f"批量访问完成: {success_count}/{len(urls)} 成功")
        
        return processed_results

async def main():
    # 测试URL列表
    test_urls = [
        "https://dl.acm.org/citation.cfm?id=2093503",
        "https://dl.acm.org/citation.cfm?id=2093490",
        "https://dl.acm.org/citation.cfm?id=2093510",
        "https://dl.acm.org/citation.cfm?id=2093505",
        "https://dl.acm.org/citation.cfm?id=2093483",
        "https://dl.acm.org/citation.cfm?id=2093502",
        "https://dl.acm.org/citation.cfm?id=2093515",
        "https://dl.acm.org/citation.cfm?id=2093495",
        "https://dl.acm.org/citation.cfm?id=2093479",
        "https://dl.acm.org/citation.cfm?id=2093499",
        "https://dl.acm.org/citation.cfm?id=2093513",
        "https://dl.acm.org/citation.cfm?id=2093480",
        "https://dl.acm.org/citation.cfm?id=2093478",
        "https://dl.acm.org/citation.cfm?id=2093487",
        "https://dl.acm.org/citation.cfm?id=2093506",
        "https://dl.acm.org/citation.cfm?id=2093482",
        "https://dl.acm.org/citation.cfm?id=2093484",
        "https://dl.acm.org/citation.cfm?id=2046780",
        "https://dl.acm.org/citation.cfm?id=2093500",
        "https://dl.acm.org/citation.cfm?id=2093493",
        "https://dl.acm.org/citation.cfm?id=2093479",
        "https://dl.acm.org/citation.cfm?id=2093499",
        "https://dl.acm.org/citation.cfm?id=2093513",
        "https://dl.acm.org/citation.cfm?id=2093478",
        "https://dl.acm.org/citation.cfm?id=2093501",
    ]

    # 使用类实例请求
    print("\n=== 使用类实例 ===")
    time_start = time.time()
    async with PlaywrightDriver(max_concurrent=10, proxy_pool_size=10, timeout=30000) as driver:
        results = await driver.safe_get_batch(test_urls, '#abstract', max_retries=10)
        for i, result in enumerate(results):
            print(f"URL {i+1}: {'成功' if result else '失败'}")
            # 去除掉 result 中的所有标签
            result = re.sub(r'<[^>]*>', '', result).replace('\n', '')

            print(result)
    time_end = time.time()
    print(f"总耗时: {time_end - time_start} 秒")

if __name__ == "__main__":
    # 运行示例
    asyncio.run(main())
