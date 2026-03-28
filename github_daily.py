#!/usr/bin/env python3
"""
GitHub 每日精选生成器
自动抓取 GitHub Trending，生成 HTML 简报
"""

import json
import os
import requests
from bs4 import BeautifulSoup
from collections import Counter
from datetime import date

try:
    _AI_KEY = os.environ.get("ANTHROPIC_API_KEY", "").strip()
    _AI_BASE = os.environ.get("ANTHROPIC_BASE_URL", "https://api.anthropic.com").rstrip("/")
    _AI_HEADERS = {
        "x-api-key": _AI_KEY,
        "anthropic-version": "2023-06-01",
        "content-type": "application/json",
    }
    _AI_MODEL = "claude-haiku-4-5-20251001"
    HAS_AI = bool(_AI_KEY)
except Exception:
    HAS_AI = False


def _ai_call(prompt: str, max_tokens: int = 600) -> str:
    """向 Claude API 发送请求，返回文本；失败时返回空字符串。"""
    r = requests.post(
        f"{_AI_BASE}/v1/messages",
        headers=_AI_HEADERS,
        json={
            "model": _AI_MODEL,
            "max_tokens": max_tokens,
            "messages": [{"role": "user", "content": prompt}],
        },
        timeout=30,
    )
    r.raise_for_status()
    return r.json()["content"][0]["text"].strip()

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
}
GH_API_HEADERS = {**HEADERS, "Accept": "application/vnd.github.v3+json"}

OWNER_URL = "https://github.com/lq-tammy/github_daily"

LANG_COLORS = {
    "Python": "#3572A5",
    "TypeScript": "#2b7489",
    "Go": "#00ADD8",
    "Rust": "#dea584",
    "JavaScript": "#f1e05a",
    "Shell": "#89e051",
    "C": "#555555",
    "C++": "#f34b7d",
    "Java": "#b07219",
    "—": "#888",
}

TAG_COLORS = {
    "AI Agent":   "#7c3aed",
    "LLM":        "#6d28d9",
    "MCP":        "#5b21b6",
    "机器学习":   "#4f46e5",
    "AI":         "#2563eb",
    "前端":       "#0891b2",
    "后端":       "#0369a1",
    "CLI工具":    "#065f46",
    "安全":       "#b91c1c",
    "数据库":     "#92400e",
    "DevOps":     "#1d4ed8",
    "区块链":     "#d97706",
    "游戏":       "#7e22ce",
    "移动端":     "#be185d",
    "数据分析":   "#047857",
    "机器人":     "#0f766e",
    "开发工具":   "#4b5563",
    "多媒体":     "#b45309",
    "自动化":     "#15803d",
    "知识管理":   "#6b7280",
    "金融":       "#a16207",
    "本地优先":   "#374151",
}

TAG_RULES = [
    (["agent", "agents", "multi-agent", "agentic"],          "AI Agent"),
    (["llm", "large language model", "language model",
      "openai", "gpt", "gemini", "claude", "mistral",
      "ollama", "vllm", "llama"],                            "LLM"),
    (["mcp", "model context protocol"],                      "MCP"),
    (["machine learning", "deep learning", "neural",
      "pytorch", "tensorflow", "training", "finetune",
      "diffusion", "stable diffusion"],                      "机器学习"),
    (["ai", "artificial intelligence", "chatbot",
      "rag", "embedding", "vector"],                         "AI"),
    (["react", "vue", "svelte", "next.js", "nextjs",
      "nuxt", "frontend", "front-end", "css", "tailwind",
      "ui", "component", "dashboard", "web app"],            "前端"),
    (["api", "backend", "server", "microservice",
      "grpc", "rest", "graphql", "django", "fastapi",
      "flask", "express", "spring"],                         "后端"),
    (["cli", "command-line", "command line", "terminal",
      "shell", "tui", "ncurses", "readline"],                "CLI工具"),
    (["security", "vulnerability", "exploit", "pentest",
      "ctf", "reverse", "malware", "firewall",
      "encryption", "crypto", "auth", "oauth"],              "安全"),
    (["database", "sql", "nosql", "postgres", "mysql",
      "sqlite", "redis", "mongodb", "clickhouse",
      "duckdb", "olap", "oltp"],                             "数据库"),
    (["docker", "kubernetes", "k8s", "ci/cd", "devops",
      "terraform", "ansible", "helm", "infra",
      "deployment", "container"],                            "DevOps"),
    (["blockchain", "web3", "solidity", "ethereum",
      "bitcoin", "defi", "nft", "smart contract"],           "区块链"),
    (["game", "games", "gaming", "unity", "unreal",
      "godot", "opengl", "vulkan", "renderer"],              "游戏"),
    (["android", "ios", "mobile", "flutter", "swift",
      "kotlin", "react native", "xamarin"],                  "移动端"),
    (["data science", "analytics", "pandas", "spark",
      "etl", "pipeline", "notebook", "visualization",
      "plot", "chart", "tableau"],                           "数据分析"),
    (["robot", "robotics", "ros", "drone",
      "autonomous", "simulation"],                           "机器人"),
    (["developer tool", "devtool", "ide", "debugger",
      "linter", "formatter", "sdk", "compiler",
      "parser", "ast", "language server"],                   "开发工具"),
    (["video", "audio", "image", "ffmpeg", "media",
      "streaming", "podcast", "music", "photo"],             "多媒体"),
    (["automation", "workflow", "scraping", "crawler",
      "rpa", "scheduler", "cron", "bot"],                    "自动化"),
    (["knowledge", "wiki", "note", "obsidian", "notion",
      "zettelkasten", "pkm", "second brain"],                "知识管理"),
    (["finance", "trading", "quant", "stock",
      "forex", "portfolio", "accounting"],                   "金融"),
    (["local", "offline", "self-hosted", "privacy",
      "local-first", "on-premise"],                          "本地优先"),
]

# ─── Fetch ────────────────────────────────────────────────────────────────────

def fetch_trending(language: str = "", since: str = "daily") -> list[dict]:
    url = f"https://github.com/trending/{language}?since={since}"
    resp = requests.get(url, headers=HEADERS, timeout=10)
    resp.raise_for_status()

    soup = BeautifulSoup(resp.text, "html.parser")
    repos = []

    for article in soup.select("article.Box-row"):
        name_tag = article.select_one("h2 a")
        if not name_tag:
            continue
        full_name = name_tag.get("href", "").strip("/")

        desc_tag = article.select_one("p")
        description = desc_tag.get_text(strip=True) if desc_tag else "—"

        lang_tag = article.select_one("[itemprop='programmingLanguage']")
        lang = lang_tag.get_text(strip=True) if lang_tag else "—"

        stars_tags = article.select("span.d-inline-block.float-sm-right")
        today_stars = stars_tags[0].get_text(strip=True) if stars_tags else "—"

        star_tag = article.select_one("a[href$='/stargazers']")
        total_stars = star_tag.get_text(strip=True) if star_tag else "—"

        repos.append({
            "name": full_name,
            "url": f"https://github.com/{full_name}",
            "description": description,
            "language": lang,
            "total_stars": total_stars,
            "today_stars": today_stars,
        })

    return repos


def fetch_github_extra_info(full_name: str) -> dict:
    """从 GitHub API 获取仓库及作者的额外信息。"""
    owner = full_name.split("/")[0]
    info = {"repo": {}, "owner": {}}
    try:
        r = requests.get(f"https://api.github.com/repos/{full_name}",
                         headers=GH_API_HEADERS, timeout=8)
        if r.ok:
            info["repo"] = r.json()
    except Exception:
        pass
    try:
        r = requests.get(f"https://api.github.com/users/{owner}",
                         headers=GH_API_HEADERS, timeout=8)
        if r.ok:
            info["owner"] = r.json()
    except Exception:
        pass
    return info

# ─── AI helpers ───────────────────────────────────────────────────────────────

def batch_translate_descriptions(all_repos: dict) -> dict[str, str]:
    """批量将英文描述翻译成中文，返回 {原文: 译文}。无 AI 时返回空 dict。"""
    if not HAS_AI:
        return {}

    seen: dict[str, None] = {}
    for repos in all_repos.values():
        for r in repos:
            desc = r.get("description", "")
            if desc and desc != "—" and desc not in seen:
                en_ratio = sum(1 for c in desc if c.isascii() and c.isalpha()) / max(len(desc), 1)
                if en_ratio > 0.35:
                    seen[desc] = None

    if not seen:
        return {}

    descs = list(seen)
    numbered = "\n".join(f"{i + 1}. {d}" for i, d in enumerate(descs))

    try:
        text = _ai_call(
            "请将以下 GitHub 项目简介逐条翻译成中文。要求：\n"
            "- 每条不超过 40 字\n"
            "- 用非技术读者也能看懂的通俗语言\n"
            "- 保留英文专有名词（AI、API、LLM 等）\n"
            "- 只输出译文，格式为「序号. 译文」，不加任何额外内容\n\n"
            f"{numbered}",
            max_tokens=2500,
        )
        result: dict[str, str] = {}
        for line in text.splitlines():
            line = line.strip()
            if not line:
                continue
            dot = line.find(".")
            if dot < 1:
                continue
            try:
                idx = int(line[:dot]) - 1
                trans = line[dot + 1:].strip()
                if 0 <= idx < len(descs) and trans:
                    result[descs[idx]] = trans
            except ValueError:
                continue
        return result
    except Exception as e:
        print(f"    翻译失败: {e}")
        return {}


def generate_hero_content(repo: dict, github_info: dict) -> dict:
    """调用 Claude 生成英雄卡片的三段中文介绍。"""
    fallback = {
        "developer_bg": f"由 {repo['name'].split('/')[0]} 开发的开源项目。",
        "features": repo.get("description", "—"),
        "use_cases": "适合开发者及技术爱好者探索使用。",
    }
    if not HAS_AI:
        return fallback

    repo_info = github_info.get("repo", {})
    owner_info = github_info.get("owner", {})

    fields = [
        ("项目全名", repo["name"]),
        ("项目描述", repo.get("description", "")),
        ("编程语言", repo.get("language", "")),
        ("总 Star 数", repo.get("total_stars", "")),
        ("今日新增 Star", repo.get("today_stars", "")),
        ("主题标签", ", ".join(repo_info.get("topics", []))),
        ("开发者 ID", owner_info.get("login", "")),
        ("开发者简介", owner_info.get("bio", "")),
        ("开发者公司", owner_info.get("company", "")),
        ("开发者所在地", owner_info.get("location", "")),
        ("开发者粉丝数", str(owner_info.get("followers", ""))),
        ("公开仓库数", str(owner_info.get("public_repos", ""))),
    ]
    context = "\n".join(f"{k}：{v}" for k, v in fields if v and v.strip())

    try:
        text = _ai_call(
            "你是一位科技媒体编辑，擅长把技术项目介绍给普通读者。\n"
            "基于以下 GitHub 项目信息，用中文写三段介绍，每段 30-60 字，"
            "语言通俗、有温度，文科生也能看懂。\n\n"
            f"{context}\n\n"
            "请严格输出以下 JSON（不要 markdown 包裹）：\n"
            '{"developer_bg":"开发者背景","features":"项目功能与特色","use_cases":"适合什么人或场景"}',
            max_tokens=600,
        )
        if "```" in text:
            text = text.split("```")[1]
            if text.lower().startswith("json"):
                text = text[4:]
            text = text.split("```")[0]
        return json.loads(text.strip())
    except Exception as e:
        print(f"    英雄卡片生成失败: {e}")
        return fallback

# ─── Badges & tags ────────────────────────────────────────────────────────────

def lang_badge(lang: str) -> str:
    color = LANG_COLORS.get(lang, "#888")
    return f'<span class="badge" style="background:{color}">{lang}</span>'


def extract_tags(repo: dict, max_tags: int = 3) -> list[str]:
    text = (repo.get("description", "") + " " + repo.get("name", "")).lower()
    tags = []
    for keywords, tag_name in TAG_RULES:
        if tag_name in tags:
            continue
        if any(kw in text for kw in keywords):
            tags.append(tag_name)
        if len(tags) >= max_tags:
            break
    if not tags:
        lang = repo.get("language", "—")
        tags = [lang] if lang and lang != "—" else ["开源项目"]
    return tags


def tag_badges(tags: list[str]) -> str:
    return "".join(
        f'<span class="topic-tag" style="background:{TAG_COLORS.get(t, "#4b5563")}">{t}</span>'
        for t in tags
    )

# ─── Hero card ────────────────────────────────────────────────────────────────

def section_hero_card(repo: dict, content: dict) -> str:
    tags = extract_tags(repo, max_tags=3)
    return f"""
    <section class="hero-section">
      <div class="hero-card">
        <div class="hero-eyebrow">今日之星 · 开发者聚焦</div>
        <div class="hero-name-row">
          <a class="hero-name" href="{repo['url']}" target="_blank">{repo['name']}</a>
          {lang_badge(repo['language'])}
        </div>
        <div class="hero-meta">
          <span class="hero-stars">⭐ {repo['total_stars']}</span>
          <span class="hero-today">今日 +{repo['today_stars']}</span>
          <span class="hero-tags">{tag_badges(tags)}</span>
        </div>
        <div class="hero-grid">
          <div class="hero-item">
            <div class="hero-item-label">👤 开发者背景</div>
            <div class="hero-item-body">{content.get('developer_bg', '—')}</div>
          </div>
          <div class="hero-item">
            <div class="hero-item-label">✨ 项目功能与特色</div>
            <div class="hero-item-body">{content.get('features', '—')}</div>
          </div>
          <div class="hero-item">
            <div class="hero-item-label">🎯 适合场景</div>
            <div class="hero-item-body">{content.get('use_cases', '—')}</div>
          </div>
        </div>
      </div>
    </section>"""

# ─── Digest ───────────────────────────────────────────────────────────────────

def _build_digest(repos: list[dict], limit: int, time_word: str) -> str:
    top = repos[:limit]
    if not top:
        return ""

    tag_counter: Counter = Counter()
    for r in top:
        for t in extract_tags(r, max_tags=3):
            tag_counter[t] += 1
    top_tags = [t for t, _ in tag_counter.most_common(4)]

    lang_counter: Counter = Counter(
        r["language"] for r in top if r["language"] not in ("—", "")
    )
    top_langs = [l for l, _ in lang_counter.most_common(2)]

    ai_tags = {"AI Agent", "LLM", "MCP", "机器学习", "AI"}
    ai_count = sum(
        1 for r in top
        if any(t in ai_tags for t in extract_tags(r, max_tags=3))
    )

    leader = top[0]
    leader_short = leader["name"].split("/")[-1]
    leader_tag_str = "／".join(extract_tags(leader, max_tags=2))

    parts = []
    if top_tags:
        theme = "、".join(top_tags[:2])
        s1 = f"{time_word}精选聚焦 {theme} 方向"
        if ai_count >= 3:
            s1 += f"，{ai_count} 个项目与 AI 生态直接相关"
        parts.append(s1 + "。")

    parts.append(f"人气最高的 {leader_short}（{leader_tag_str}）势头最旺，值得重点关注。")

    if top_langs:
        lang_str = " 与 ".join(top_langs)
        parts.append(f"语言层面以 {lang_str} 为主；")
    if len(top_tags) >= 3:
        tail = "、".join(top_tags[2:4])
        parts.append(f"{tail} 等细分方向亦有亮眼作品入榜，整体热度持续走高。")
    else:
        parts.append("整体开发者热情持续高涨，值得持续跟踪。")

    return "".join(parts)[:300]


def daily_digest(repos: list[dict], limit: int = 8) -> str:
    return _build_digest(repos, limit, "今日")


def weekly_digest(repos: list[dict], limit: int = 10) -> str:
    return _build_digest(repos, limit, "本周")

# ─── Table / card HTML ────────────────────────────────────────────────────────

def repo_rows(repos: list[dict], limit: int, show_lang: bool = True) -> str:
    rows = ""
    for i, r in enumerate(repos[:limit], 1):
        lang_col = f"<td>{lang_badge(r['language'])}</td>" if show_lang else ""
        rows += f"""
        <tr>
          <td class="rank">{i}</td>
          <td><a href="{r['url']}" target="_blank">{r['name']}</a>
              <div class="desc">{r['description']}</div></td>
          {lang_col}
          <td class="stars">{r['total_stars']}</td>
          <td class="stars today">{r['today_stars']}</td>
        </tr>"""
    return rows


def section_table(title: str, repos: list[dict], limit: int,
                  show_lang: bool = True, digest: str = "") -> str:
    lang_th = "<th>语言</th>" if show_lang else ""
    digest_html = f'\n      <p class="section-digest">{digest}</p>' if digest else ""
    return f"""
    <section>
      <h2>{title}</h2>{digest_html}
      <table>
        <thead><tr><th>#</th><th>项目</th>{lang_th}<th>⭐ 总计</th><th>今日 ⭐</th></tr></thead>
        <tbody>{repo_rows(repos, limit, show_lang)}</tbody>
      </table>
    </section>"""


def repo_cards_weekly(repos: list[dict], limit: int) -> str:
    cards = ""
    for i, r in enumerate(repos[:limit], 1):
        tags = extract_tags(r)
        cards += f"""
      <div class="card">
        <div class="card-header">
          <span class="card-rank">{i}</span>
          <div style="flex:1;min-width:0">
            <a class="card-name" href="{r['url']}" target="_blank">{r['name']}</a>
          </div>
          {lang_badge(r['language'])}
        </div>
        <div class="card-desc">{r['description']}</div>
        <div class="tags">{tag_badges(tags)}</div>
        <div class="card-footer">
          <span class="card-stars">⭐ {r['total_stars']}</span>
          <span class="card-week-stars">+{r['today_stars']}</span>
        </div>
      </div>"""
    return cards


def section_table_weekly(repos: list[dict], limit: int = 10) -> str:
    digest = weekly_digest(repos, limit)
    digest_html = f'\n      <p class="section-digest">{digest}</p>' if digest else ""
    return f"""
    <section>
      <h2 class="weekly">本周新增 Star Top 10</h2>{digest_html}
      <div class="card-grid">{repo_cards_weekly(repos, limit)}
      </div>
    </section>"""

# ─── HTML builder ─────────────────────────────────────────────────────────────

def build_html(all_repos: dict[str, list], weekly_repos: list[dict],
               hero_html: str = "") -> str:
    today = date.today().strftime("%Y-%m-%d")

    daily_top = all_repos.get("", [])
    d_digest = daily_digest(daily_top, 8)
    sections = section_table("今日全榜 Top 8", daily_top, 8,
                             show_lang=True, digest=d_digest)
    sections += section_table_weekly(weekly_repos, 10)
    py_repos = all_repos.get("python", [])
    if py_repos:
        sections += section_table("Python Top 5", py_repos, 5, show_lang=False)

    return f"""<!DOCTYPE html>
<html lang="zh">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Github每日精选 · {today}</title>
  <style>
    * {{ box-sizing: border-box; margin: 0; padding: 0; }}
    body {{ font-family: -apple-system, BlinkMacSystemFont, "Inter", "Segoe UI", sans-serif;
            background: #f8fafc; color: #0f172a; padding: 36px 24px; line-height: 1.6; }}
    .container {{ max-width: 1000px; margin: 0 auto; }}

    /* ── Header ── */
    header {{ margin-bottom: 44px; padding-bottom: 24px; border-bottom: 1px solid #e2e8f0; }}
    header h1 {{ font-size: 28px; font-weight: 800; letter-spacing: -0.5px;
                 background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%);
                 -webkit-background-clip: text; -webkit-text-fill-color: transparent;
                 background-clip: text; }}
    header .meta {{ color: #94a3b8; font-size: 13px; margin-top: 6px;
                    display: flex; align-items: center; gap: 6px; }}
    header .meta a {{ color: #6366f1; text-decoration: none; font-weight: 600; }}
    header .meta a:hover {{ text-decoration: underline; }}
    header .meta .sep {{ color: #d1d5db; }}

    /* ── Section headings ── */
    section {{ margin-bottom: 52px; }}
    h2 {{ font-size: 17px; font-weight: 700; color: #0f172a;
          margin-bottom: 18px; display: flex; align-items: center; gap: 10px; }}
    h2::before {{ content: ""; display: inline-block; width: 4px; height: 20px;
                  border-radius: 2px;
                  background: linear-gradient(180deg, #6366f1, #8b5cf6); flex-shrink: 0; }}
    h2.weekly::before {{ background: linear-gradient(180deg, #f59e0b, #ef4444); }}

    /* ── Section digest ── */
    .section-digest {{ font-size: 13px; color: #4b5563; line-height: 1.85;
                       background: linear-gradient(135deg, #fefce8 0%, #faf5ff 100%);
                       border: 1px solid #e9d5ff; border-radius: 12px;
                       padding: 13px 18px; margin-bottom: 18px; }}

    /* ── Table ── */
    table {{ width: 100%; border-collapse: separate; border-spacing: 0;
             background: #fff; border-radius: 14px; overflow: hidden;
             box-shadow: 0 1px 4px rgba(0,0,0,.06), 0 6px 16px rgba(0,0,0,.04);
             border: 1px solid #e8ecf0; font-size: 14px; }}
    th {{ text-align: left; padding: 11px 16px; color: #94a3b8; font-weight: 600;
          font-size: 11px; text-transform: uppercase; letter-spacing: .06em;
          background: #f8fafc; border-bottom: 1px solid #e8ecf0; }}
    td {{ padding: 13px 16px; border-bottom: 1px solid #f1f5f9; vertical-align: top; }}
    tr:last-child td {{ border-bottom: none; }}
    tr:hover td {{ background: #f5f3ff; }}
    td a {{ color: #4f46e5; text-decoration: none; font-weight: 600; font-size: 14px; }}
    td a:hover {{ color: #7c3aed; text-decoration: underline; }}
    .desc {{ color: #94a3b8; font-size: 12px; margin-top: 4px; line-height: 1.5; }}
    .rank {{ color: #d1d5db; width: 36px; text-align: center;
             font-weight: 800; font-size: 15px; }}
    .stars {{ color: #f59e0b; text-align: right; white-space: nowrap;
              font-weight: 600; font-size: 13px; }}
    .today {{ color: #10b981; }}

    /* ── Language badge ── */
    .badge {{ display: inline-block; padding: 2px 10px; border-radius: 20px;
              font-size: 11px; color: #fff; font-weight: 600; white-space: nowrap; }}

    /* ── Hero card ── */
    .hero-section {{ margin-bottom: 52px; }}
    .hero-card {{ background: linear-gradient(135deg, #eef2ff 0%, #faf5ff 100%);
                  border: 1px solid #c7d2fe; border-radius: 16px; padding: 24px 28px; }}
    .hero-eyebrow {{ font-size: 11px; font-weight: 700; text-transform: uppercase;
                     letter-spacing: .08em; color: #6366f1; margin-bottom: 12px; }}
    .hero-name-row {{ display: flex; align-items: center; gap: 10px;
                      flex-wrap: wrap; margin-bottom: 8px; }}
    .hero-name {{ font-size: 22px; font-weight: 800; color: #4f46e5;
                  text-decoration: none; letter-spacing: -0.3px; }}
    .hero-name:hover {{ color: #7c3aed; text-decoration: underline; }}
    .hero-meta {{ display: flex; align-items: center; gap: 12px;
                  flex-wrap: wrap; font-size: 13px; margin-bottom: 20px; }}
    .hero-stars {{ color: #f59e0b; font-weight: 700; }}
    .hero-today {{ color: #10b981; font-weight: 600; }}
    .hero-tags {{ display: flex; gap: 4px; flex-wrap: wrap; }}
    .hero-grid {{ display: grid; grid-template-columns: repeat(3, 1fr); gap: 14px; }}
    .hero-item {{ background: rgba(255,255,255,.75); border-radius: 10px;
                  padding: 14px 16px; }}
    .hero-item-label {{ font-size: 11px; font-weight: 700; color: #6366f1;
                        text-transform: uppercase; letter-spacing: .05em;
                        margin-bottom: 6px; }}
    .hero-item-body {{ font-size: 13px; color: #374151; line-height: 1.65; }}

    /* ── Weekly card grid ── */
    .card-grid {{ display: grid; grid-template-columns: repeat(2, 1fr); gap: 16px; }}
    .card {{ background: #fff; border-radius: 14px; padding: 18px 20px;
             box-shadow: 0 1px 4px rgba(0,0,0,.06), 0 6px 16px rgba(0,0,0,.04);
             border: 1px solid #e8ecf0;
             transition: box-shadow .2s ease, transform .2s ease; }}
    .card:hover {{ box-shadow: 0 4px 14px rgba(99,102,241,.12), 0 10px 28px rgba(0,0,0,.08);
                   transform: translateY(-3px); }}
    .card-header {{ display: flex; align-items: flex-start; gap: 10px; margin-bottom: 8px; }}
    .card-rank {{ font-size: 22px; font-weight: 900; color: #e2e8f0;
                  min-width: 30px; line-height: 1.2; }}
    .card-name {{ color: #4f46e5; font-weight: 700; font-size: 14px;
                  text-decoration: none; line-height: 1.4; word-break: break-all; }}
    .card-name:hover {{ color: #7c3aed; text-decoration: underline; }}
    .card-desc {{ color: #94a3b8; font-size: 12px; line-height: 1.55; margin: 6px 0 8px; }}
    .card-footer {{ display: flex; align-items: center; justify-content: space-between;
                    margin-top: 12px; padding-top: 10px; border-top: 1px solid #f1f5f9; }}
    .card-stars {{ font-size: 13px; color: #f59e0b; font-weight: 700; }}
    .card-week-stars {{ font-size: 12px; color: #10b981; font-weight: 600; }}

    /* ── Topic tags ── */
    .tags {{ display: flex; flex-wrap: wrap; gap: 5px; }}
    .topic-tag {{ display: inline-block; padding: 2px 8px; border-radius: 5px;
                  font-size: 11px; color: #fff; font-weight: 600; }}

    /* ── Footer ── */
    footer {{ text-align: center; color: #94a3b8; font-size: 12px;
              margin-top: 48px; padding-top: 20px; border-top: 1px solid #e2e8f0; }}
    footer a {{ color: #6366f1; text-decoration: none; font-weight: 500; }}
    footer a:hover {{ text-decoration: underline; }}

    @media (max-width: 640px) {{
      .card-grid {{ grid-template-columns: 1fr; }}
      .hero-grid {{ grid-template-columns: 1fr; }}
      body {{ padding: 20px 16px; }}
    }}
  </style>
</head>
<body>
  <div class="container">
    <header>
      <h1>Github每日精选</h1>
      <div class="meta">
        <span>{today}</span>
        <span class="sep">·</span>
        <span>by <a href="{OWNER_URL}" target="_blank">Yanyang</a></span>
      </div>
    </header>
    {hero_html}
    {sections}
    <footer>
      数据来源：<a href="https://github.com/trending" target="_blank">GitHub Trending</a>
      &nbsp;·&nbsp; 生成时间：{today}
    </footer>
  </div>
</body>
</html>"""

# ─── Main ─────────────────────────────────────────────────────────────────────

def main():
    print("正在抓取 GitHub Trending...")

    all_repos: dict[str, list] = {}
    for lang, label in [("", "全部"), ("python", "Python")]:
        print(f"  → {label}")
        try:
            all_repos[lang] = fetch_trending(lang)
        except Exception as e:
            print(f"    抓取失败: {e}")
            all_repos[lang] = []

    print("  → 本周全榜（weekly）")
    try:
        weekly_repos = fetch_trending("", since="weekly")
    except Exception as e:
        print(f"    抓取失败: {e}")
        weekly_repos = []

    # ── 批量翻译描述 ──
    print("  → 翻译项目简介（Claude Haiku）...")
    all_for_translate = {**all_repos, "_weekly": weekly_repos}
    translations = batch_translate_descriptions(all_for_translate)
    if translations:
        for repos in [*all_repos.values(), weekly_repos]:
            for r in repos:
                if r["description"] in translations:
                    r["description"] = translations[r["description"]]
        print(f"    已翻译 {len(translations)} 条描述")

    # ── 英雄卡 ──
    hero_html = ""
    top_daily = all_repos.get("", [])
    if top_daily:
        leader = top_daily[0]
        print(f"  → 生成今日精选介绍：{leader['name']}")
        github_info = fetch_github_extra_info(leader["name"])
        content = generate_hero_content(leader, github_info)
        hero_html = section_hero_card(leader, content)

    html = build_html(all_repos, weekly_repos, hero_html)

    today = date.today().strftime("%Y-%m-%d")
    output_dir = os.path.dirname(os.path.abspath(__file__))
    output_path = os.path.join(output_dir, f"github_daily_{today}.html")

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html)

    index_path = os.path.join(output_dir, "index.html")
    with open(index_path, "w", encoding="utf-8") as f:
        f.write(html)

    print(f"\n简报已生成：{output_path}")
    print(f"已同步：{index_path}")


if __name__ == "__main__":
    main()
