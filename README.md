# GitHub 每日简报

自动抓取 [GitHub Trending](https://github.com/trending)，生成精美 HTML 简报，一键分享。

**在线查看：** https://lq-tammy.github.io/github_daily/

---

## 功能

- 抓取每日 GitHub Trending 全榜 Top 10
- 分语言榜单：Python / TypeScript / Go / Rust Top 5
- 生成暗色主题 HTML 简报���支持浏览器直接打开
- 数据包含：项目名、描述、编程语言、总 Star 数、今日新增 Star

## 快速开始

**安装依赖**

```bash
pip install requests beautifulsoup4
```

**运行脚本**

```bash
python3 github_daily.py
```

生成文件：`github_daily_YYYY-MM-DD.html`

## 更新简报到线上

1. 运行脚本生成今日 HTML
2. 将生成的文件复制并重命名为 `index.html`
3. 上传到本仓库，覆盖旧的 `index.html`
4. 等待约 1 分钟，访问 https://lq-tammy.github.io/github_daily/ 即可看到最新简报

## 文件说明

| 文件 | 说明 |
|------|------|
| `github_daily.py` | 主脚本，抓取数据并生成 HTML |
| `index.html` | 最新一期简报（GitHub Pages 入口） |
| `github_daily_YYYY-MM-DD.html` | 历史归档简报 |

## 覆盖语言

| 榜单 | 数量 |
|------|------|
| 全部语言 | Top 10 |
| Python | Top 5 |
| TypeScript | Top 5 |
| Go | Top 5 |
| Rust | Top 5 |

## 数据来源

[GitHub Trending](https://github.com/trending) · 每日更新
