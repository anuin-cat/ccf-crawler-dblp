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