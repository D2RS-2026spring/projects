#!/usr/bin/env python3
"""Extract structured data from GitHub issues using DeepSeek API.

Reads open issues + comments, calls LLM to extract repo URL, members, DOI,
journal, and description. Saves to data/issue_data.json for build_site.py.
"""
import json, os, subprocess, hashlib, sys, time, re
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent

# ── Load reference data ─────────────────────────────────────────────────────
students = {}
with open(SCRIPT_DIR / 'data' / 'student-list.csv', encoding='utf-8-sig') as f:
    import csv
    for row in csv.DictReader(f):
        students[row['学号']] = row['姓名']

with open(SCRIPT_DIR / 'data' / 'student_github_map.json') as f:
    id_to_github = json.load(f)

student_roster = '\n'.join(
    f"{sid} {name} @{id_to_github[sid]}"
    for sid, name in sorted(students.items()) if sid in id_to_github)

# ── Fetch open issues ───────────────────────────────────────────────────────
print("Fetching open issues...")
result = subprocess.run(
    ['gh', 'issue', 'list', '--repo', 'D2RS-2026spring/projects',
     '--state', 'open', '--limit', '200', '--json', 'number,body,title,author'],
    capture_output=True, text=True, check=True)
issues = json.loads(result.stdout)
print(f"  Found {len(issues)} open issues")

# Fetch comments for each issue
print("Fetching comments...")
for issue in issues:
    num = issue['number']
    r = subprocess.run(
        ['gh', 'api', f'repos/D2RS-2026spring/projects/issues/{num}/comments',
         '--paginate', '--jq', '.[].body'],
        capture_output=True, text=True)
    issue['_comments'] = r.stdout or ''

# ── Load existing data for incremental extraction ───────────────────────────
data_file = SCRIPT_DIR / 'data' / 'issue_data.json'
existing = {}
if data_file.exists():
    try:
        with open(data_file) as f:
            for item in json.load(f):
                existing[item['number']] = item
    except Exception:
        pass

# ── Call DeepSeek API ───────────────────────────────────────────────────────
from openai import OpenAI

api_key = os.environ.get('DEEPSEEK_API_KEY')
if not api_key:
    env_file = SCRIPT_DIR / '.env'
    if env_file.exists():
        api_key = env_file.read_text().strip()
if not api_key:
    print("ERROR: DEEPSEEK_API_KEY not set. Export it or create .env file.")
    sys.exit(1)

client = OpenAI(api_key=api_key, base_url="https://api.deepseek.com")

PROMPT_TEMPLATE = """你是项目信息提取助手。从以下 GitHub issue 正文和评论中，提取结构化信息。

## 学生花名册（用于匹配学号和 GitHub 用户名）
{roster}

## Issue 正文
{body}

## 评论
{comments}

## 提取规则
1. **repo**: 学生提交的项目仓库 URL（github.com/owner/name 格式）。
   - 优先提取标注为"仓库链接"、"仓库"的 URL
   - 排除论文原始代码仓库（如 armetcal/xxx、original paper repos）
   - 排除用户头像附件（user-attachments 开头的）
   - 如果有 D2RS-2026spring 组织的仓库，优先使用
   - 没有则留空字符串

2. **members**: 小组所有成员列表。每人包含：
   - name: 中文姓名
   - sid: 13位学号（从花名册匹配）
   - gh: GitHub 用户名（从花名册匹配 @mention）
   - leader: 是否组长（issue 作者通常是组长）

3. **doi**: 论文 DOI（10.xxxx/xxx 格式），没有则留空

4. **journal**: 期刊名称，没有则留空

5. **description**: 一句话中文描述项目内容（不超过50字）

只返回 JSON，不要其他文字。格式：
{{
  "repo": "D2RS-2026spring/repo-name",
  "members": [
    {{"name": "张三", "sid": "2025303110001", "gh": "zhangsan", "leader": true}},
    {{"name": "李四", "sid": "2025303110002", "gh": "lisi", "leader": false}}
  ],
  "doi": "10.1234/example",
  "journal": "Nature",
  "description": "复现xxx论文的核心图表分析"
}}"""

results = []
for i, issue in enumerate(issues):
    num = issue['number']
    body = issue.get('body', '') or ''
    comments = issue.get('_comments', '') or ''
    title = issue.get('title', '')
    author = issue['author']['login']

    # Skip if unchanged
    content_hash = hashlib.md5((body + comments).encode()).hexdigest()
    if num in existing and existing[num].get('_hash') == content_hash:
        results.append(existing[num])
        print(f"  [{i+1}/{len(issues)}] #{num} (cached)")
        continue

    print(f"  [{i+1}/{len(issues)}] #{num} {title[:40]}...", end=' ', flush=True)

    prompt = PROMPT_TEMPLATE.format(
        roster=student_roster, body=body, comments=comments)

    for attempt in range(3):
        try:
            resp = client.chat.completions.create(
                model="deepseek-v4-pro",
                messages=[{"role": "user", "content": prompt}],
                response_format={"type": "json_object"},
                temperature=0.1)
            raw = resp.choices[0].message.content
            data = json.loads(raw)
            break
        except Exception as e:
            if attempt < 2:
                print(f"retry({e})...", end=' ', flush=True)
                time.sleep(2 ** attempt)
            else:
                print(f"FAILED: {e}")
                data = {"repo": "", "members": [], "doi": "", "journal": "",
                        "description": title}

    results.append({
        "number": num,
        "title": title,
        "author": author,
        "repo": data.get("repo", ""),
        "members": data.get("members", []),
        "doi": data.get("doi", ""),
        "journal": data.get("journal", ""),
        "description": data.get("description", ""),
        "_hash": content_hash,
    })
    print("ok")
    time.sleep(0.5)  # rate limit

# ── Save ────────────────────────────────────────────────────────────────────
data_file.parent.mkdir(exist_ok=True)
with open(data_file, 'w', encoding='utf-8') as f:
    json.dump(results, f, ensure_ascii=False, indent=2)

print(f"\nSaved {len(results)} issues to {data_file}")
