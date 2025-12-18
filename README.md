# CCF DBLP 爬虫

一个用于爬取 CCF 会议/期刊论文元信息和摘要的高效爬虫工具。

## 功能特性

- **论文元信息获取**：通过 DBLP API 获取指定 CCF 等级的会议/期刊论文元信息
- **多源摘要获取**：支持通过多种方式获取论文摘要
  - API 方式：Crossref、OpenAlex、Semantic Scholar
  - 网站爬取：针对 ACM、IEEE、arXiv、OpenReview... 等超多适配
- **代理池管理**：自动管理代理池，支持代理失效时降级到本机地址

## 环境要求

- Python 3.7+
- 依赖包见 `requirements.txt`

## 安装

```bash
# 安装依赖
pip install -r requirements.txt

# 安装 Playwright 浏览器
playwright install chromium

# 配置代理（可选）
# 复制 .env.local.example 为 .env.local，并填入代理 API 配置
```

### 代理配置

本项目使用**神龙代理**（api.shenlongip.com）作为代理服务。如需使用代理功能，请：

1. 访问 [神龙代理官网](http://www.shenlongip.com/) 注册账号并购买代理服务
2. 在控制台获取 `API Key` 和 `API Sign`
3. 创建 `.env.local` 文件，配置以下环境变量：

```bash
PROXY_API_KEY=你的API_Key
PROXY_API_SIGN=你的API_Sign
```

**注意**：如果不配置代理，程序会自动降级使用本机地址进行请求，但可能受到访问频率限制。

## 使用方法

### 基本使用

```bash
# 使用短参数（推荐）
python main.py -ccf a -c conf -m 20 -p 10
```

### 命令行参数

- `-ccf`: CCF 等级，可选值 `a`、`b`、`c`
- `-c, --classification`: 论文分类类型，可选值 `conf`（会议）或 `journal`（期刊）
- `-m, --max-concurrent`: 最大并发数
- `-p, --proxy-pool-size`: 代理池大小

### 输出说明

- 论文数据保存在 `data/paper/{classification}_{ccf}/` 目录
- 日志文件保存在 `data/logs/` 目录
- 每个会议/期刊的数据以 JSON 文件形式保存

## 项目结构

```
.
├── main.py                 # 主程序入口
├── driver.py               # Playwright 驱动和代理池管理
├── utils.py                # 工具函数
├── crawler/
│   ├── fetch_meta.py       # 论文元信息获取
│   └── fetch_abstract.py   # 论文摘要获取（异步版本）
└── config/
    ├── venue.py            # CCF 会议/期刊配置
    └── special_rules.py    # 特殊规则配置
```

## 声明

本项目仅用于学习和研究目的。本项目不存储任何论文的完整内容，仅获取公开的元信息和摘要信息。

如本项目涉及任何侵权行为，请及时通知，我们将立即删除相关内容。