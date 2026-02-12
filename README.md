# Personal News Aggregator

个人新闻聚合推送工具 - 自动从多个订阅源抓取内容，处理后生成静态网页。

## 功能特性

- ✅ 多源聚合：支持RSS、Twitter List、YouTube频道、博客
- ✅ Notion管理：使用Notion数据库管理订阅源
- ✅ 自动抓取：每天3次定时抓取（12:00、15:00、20:00）
- ✅ 内容处理：自动去重、翻译英文内容
- ✅ 静态生成：生成静态HTML页面，部署到GitHub Pages
- ✅ 成本低廉：使用免费服务，月成本接近0

## 项目结构

```
qiangs_news_insight/
├── backend/              # 后端代码
│   ├── main.py          # 主入口
│   ├── config.py        # 配置
│   ├── database.py      # 数据库操作
│   ├── integrations/    # 集成模块
│   │   └── notion.py    # Notion集成
│   ├── scrapers/        # 抓取模块
│   ├── processors/      # 内容处理
│   ├── generators/      # 页面生成
│   └── utils/           # 工具函数
├── frontend/            # 前端代码
│   ├── index.html       # 主页面
│   ├── css/             # 样式
│   └── js/              # 脚本
├── data/                # 数据目录
├── logs/                # 日志目录
├── requirements.txt     # 依赖
├── .env.example         # 环境变量示例
└── README.md            # 说明文档
```

## 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 配置环境变量

复制 `.env.example` 为 `.env` 并填入你的配置：

```bash
cp .env.example .env
```

需要配置：
- `NOTION_API_KEY`: Notion集成令牌
- `NOTION_DATABASE_ID`: Notion数据库ID

### 3. 创建Notion数据库

在Notion中创建一个数据库，包含以下属性：

| 属性名 | 类型 | 说明 |
|--------|------|------|
| Name | Title | 订阅源名称 |
| Type | Select | RSS / Twitter / YouTube / Blog |
| URL | URL | 订阅源地址 |
| Active | Checkbox | 是否启用 |
| Tags | Multi-select | 标签（可选） |
| Last Fetched | Date | 最后抓取时间 |

### 4. 运行

```bash
python backend/main.py
```

## 部署到GitHub

### 1. 创建GitHub仓库

```bash
git init
git add .
git commit -m "Initial commit"
git remote add origin <your-repo-url>
git push -u origin main
```

### 2. 配置GitHub Secrets

在GitHub仓库设置中添加以下Secrets：

- `NOTION_API_KEY`
- `NOTION_DATABASE_ID`
- `TWITTER_API_KEY`（可选）
- `YOUTUBE_API_KEY`（可选）
- `DEEPL_API_KEY`（可选）

### 3. 启用GitHub Pages

Settings → Pages → Source: gh-pages branch

### 4. 配置GitHub Actions

项目包含 `.github/workflows/scrape.yml`，会自动在指定时间运行抓取任务。

## 开发

### 添加新的订阅源类型

1. 在 `backend/scrapers/` 创建新的抓取模块
2. 继承 `BaseScraper` 类
3. 实现 `fetch()` 和 `parse()` 方法

示例：

```python
from scrapers.base import BaseScraper

class MyScraper(BaseScraper):
    def fetch(self):
        # 实现抓取逻辑
        pass

    def parse(self, raw_data):
        # 实现解析逻辑
        pass
```

## 许可证

MIT