# GitHub 每日精选 · 项目记忆

## 项目信息
- **仓库**：https://github.com/lq-tammy/github_daily
- **线上地址**：https://lq-tammy.github.io/github_daily
- **本地路径**：/Users/yanyang/Workplace/0.Daily/github_daily.py
- **Owner 署名链接**：Yanyang → https://github.com/lq-tammy/github_daily

## 功能特性
- 每日抓取 GitHub Trending：今日全榜 Top 8 + Python Top 5
- 本周新增 Star Top 10（2 列卡片网格 + 关键词标签）
- 顶部英雄卡：今日第一项目的开发者背景 / 功能特色 / 适合场景（GitHub API + Claude Haiku 生成）
- 所有项目简介批量翻译为中文（Claude Haiku，一次批量请求）
- 日榜和周榜各有一段精炼导览推荐语（文科生友好语言）

## 技术要点
- 爬取：`requests` + `BeautifulSoup`，抓 `https://github.com/trending?since=daily/weekly`
- Claude API：**直接用 `requests` 调用**，不用 anthropic SDK
  - 原因：`ANTHROPIC_BASE_URL` 指向第三方代理时，anthropic SDK 走 httpcore proxy 路径会报 `Illegal header value`
  - API 端点：`{ANTHROPIC_BASE_URL}/v1/messages`
  - 模型：`claude-haiku-4-5-20251001`
- **API Key 注意**：`ANTHROPIC_API_KEY` 末尾有一个空格，初始化时必须 `.strip()`
- 环境变量：`ANTHROPIC_BASE_URL=https://api.aicodewith.com`，key 格式 `sk-acw-...`

## 部署
- GitHub Actions：`.github/workflows/daily.yml`
- 定时：UTC 01:00（北京时间 09:00）每天自动运行
- 流程：运行脚本 → 生成 `index.html` → commit + push → GitHub Pages 自动更新
- Secrets 需配置：`ANTHROPIC_API_KEY`、`ANTHROPIC_BASE_URL`

## 视觉设计（2026-03-28 重构）
- 参考 youmind.com：白底亮色、渐变强调色（indigo `#6366f1` → purple `#8b5cf6`）
- 周榜：2 列卡片网格，悬浮上浮动效
- 日榜：升级版表格，悬浮行浅紫色
- 英雄卡：渐变背景，三列玻璃感白色信息块
- 响应式：手机端单列，`@media (max-width: 640px)`

## 标签系统
- `TAG_RULES`：22 条关键词规则，按优先级匹配
- `TAG_COLORS`：22 个标签对应颜色
- `extract_tags(repo, max_tags=3)`：合并 description + name 匹配
- 无命中时 fallback 到语言名 / "开源项目"
