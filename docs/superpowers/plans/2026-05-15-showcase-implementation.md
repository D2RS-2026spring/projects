# D2RS 结课作品展实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 将主页项目卡片链接到各项目的静态展示页面，形成完整的 D2RS 结课作品展。

**Architecture:** 添加 28 个 git submodule 到 `showcase/` 目录，编写 `build_showcase.py` 扫描各 submodule 的已有输出（HTML/图片）并复制到 `site/showcase/`，修改 `build_site.py` 在卡片中添加作品展链接，更新 GitHub Actions 工作流。

**Tech Stack:** Python 3.12, git submodules, GitHub Actions, GitHub Pages

---

## 文件结构

| 操作 | 文件 | 职责 |
|------|------|------|
| 新建 | `build_showcase.py` | 扫描 submodule、复制输出、生成入口页 |
| 新建 | `showcase/` (目录) | git submodule 根目录 |
| 新建 | `site/` (编译输出，.gitignore) | 生成的静态站文件 |
| 修改 | `build_site.py` (行 ~372-421) | 卡片 HTML 中添加作品展链接 |
| 修改 | `.github/workflows/update-site.yml` | 添加 submodule init + showcase build 步骤 |
| 修改 | `.gitignore` | 添加 `site/` 目录忽略规则 |

---

## Task 1: 添加 git submodules

**Files:**
- Create: `showcase/` (via `git submodule add`)
- Modify: `.gitmodules` (auto-created by git)

- [ ] **Step 1: 添加所有 28 个 submitted repos 作为 submodule**

```bash
cd /Users/gaoch/GitHub/D2RS-2026spring/projects

# 批量添加 submodule
REPOS=(
  neanderthal-ecosystem-productivity
  Shifting-dominant-periods-in-extreme-climate-impacts-under-global-warming
  project68
  Global-patterns-of-16S-rRNA-diversity-at-a-depth-of-millions-of-sequences-per-sample
  citrus-nutrient-analysis-project
  Hydroponic-Soybean-Replication
  proj
  gamma-swc-reproduction
  SynCom_Assembly_Analysis
  gfss-lunwenfuxian-project
  soil-soc-repro
  rice-nitrogen-project
  DATA
  compost_wheat_reproduce
  CO2-enhanced-water-use-efficiency
  nematode-toxicology-team
  RiceSEG-Reproduction
  cropland-nitrogen-reproduction
  ammonia-fertilizer-production-team-project
  Crop-Recommendation-System-Using-Machine-Learning
  cross-scale-ecology-team-project
  litter-decomposition-hfa
  data_review_project
  iris-reproducible-project
  rsts-encoder
  "Extraction---of---Algal---Extracellular---Polymeric---Substances."
  Synthetic-Microbiome-Reproduction
  soil-cadmium-immobilized-bacteria
)

for repo in "${REPOS[@]}"; do
  echo "Adding submodule: $repo"
  git submodule add "https://github.com/D2RS-2026spring/${repo}.git" "showcase/${repo}" 2>&1 || echo "FAILED: $repo"
done
```

- [ ] **Step 2: 验证 submodule 添加结果**

```bash
# 检查有多少 submodule 成功添加
git submodule status | wc -l
# 预期: ~28

# 检查 .gitmodules 文件
cat .gitmodules | grep "\[submodule" | wc -l
# 预期: ~28
```

- [ ] **Step 3: Commit submodule changes**

```bash
git add .gitmodules showcase/
git commit -m "feat: add 28 project submodules for showcase"
```

---

## Task 2: 创建 `build_showcase.py`

**Files:**
- Create: `build_showcase.py`

- [ ] **Step 1: 创建 build_showcase.py 基础框架**

```python
#!/usr/bin/env python3
"""Build the D2RS showcase: copy project outputs to site/showcase/."""
import json, os, shutil, subprocess
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
SHOWCASE_DIR = SCRIPT_DIR / 'showcase'
SITE_DIR = SCRIPT_DIR / 'site' / 'showcase'
REPORT = []

# Image extensions to look for in output directories
IMG_EXTS = {'.png', '.jpg', '.jpeg', '.gif', '.svg', '.webp'}
```

- [ ] **Step 2: 添加 `read_readme_title` 函数**

```python
def read_readme_title(repo_path):
    """Extract title from README.md first heading, fallback to repo name."""
    readme = repo_path / 'README.md'
    if readme.exists():
        for line in readme.read_text(encoding='utf-8', errors='replace').splitlines():
            line = line.strip()
            if line.startswith('# '):
                return line[2:].strip()
    return repo_path.name
```

- [ ] **Step 3: 添加 `copy_tree` 辅助函数**

```python
def copy_tree(src, dst):
    """Copy directory tree, overwriting existing."""
    if dst.exists():
        shutil.rmtree(dst)
    shutil.copytree(src, dst)
```

- [ ] **Step 4: 添加 `find_html_files` 函数**

```python
def find_html_files(repo_path):
    """Find HTML files in repo, excluding common non-output locations."""
    exclude = {'node_modules', '.git', 'renv', 'site_libs', '.quarto'}
    html_files = []
    for f in repo_path.rglob('*.html'):
        if any(part in exclude for part in f.parts):
            continue
        html_files.append(f)
    return html_files
```

- [ ] **Step 5: 添加 `find_output_figures` 函数**

```python
def find_output_figures(repo_path):
    """Find images in output/ or figures/ directories."""
    imgs = []
    for dirname in ['output', 'figures', 'docs']:
        d = repo_path / dirname
        if d.is_dir():
            for f in d.rglob('*'):
                if f.suffix.lower() in IMG_EXTS:
                    imgs.append(f)
    return imgs
```

- [ ] **Step 6: 添加 `generate_gallery_html` 函数**

```python
def generate_gallery_html(title, images, repo_name):
    """Generate a simple image gallery HTML page."""
    imgs_html = ''
    for img in sorted(images):
        rel = img.relative_to(SITE_DIR / repo_name)
        name = img.stem.replace('_', ' ').replace('-', ' ')
        imgs_html += f'<figure><img src="{rel}" alt="{name}"><figcaption>{name}</figcaption></figure>\n'

    return f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{title}</title>
<style>
*{{box-sizing:border-box;margin:0;padding:0}}
body{{font-family:system-ui,sans-serif;background:#f8f9fa;color:#2c3e50;padding:20px;max-width:1200px;margin:0 auto}}
header{{margin-bottom:24px}}
header a{{color:#2980b9;text-decoration:none;font-size:.9rem}}
header a:hover{{text-decoration:underline}}
h1{{font-size:1.4rem;margin:12px 0 8px}}
.gallery{{display:grid;grid-template-columns:repeat(auto-fill,minmax(300px,1fr));gap:16px}}
figure{{background:#fff;border:1px solid #e0e6ed;border-radius:8px;overflow:hidden}}
figure img{{width:100%;height:auto;display:block}}
figcaption{{padding:8px 12px;font-size:.82rem;color:#636e72}}
footer{{margin-top:32px;padding-top:16px;border-top:1px solid #e0e6ed;font-size:.8rem;color:#636e72}}
footer a{{color:#2980b9;text-decoration:none}}
</style>
</head>
<body>
<header>
  <a href="/projects/">&larr; 返回作品展</a>
  <h1>{title}</h1>
</header>
<div class="gallery">
{imgs_html}
</div>
<footer>
  <a href="https://github.com/D2RS-2026spring/{repo_name}">查看源码 &rarr;</a>
</footer>
</body>
</html>'''
```

- [ ] **Step 7: 添加 `generate_wrapper_html` 函数**

```python
def generate_wrapper_html(title, repo_name):
    """Generate a minimal wrapper page that loads the project's index.html."""
    return f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{title}</title>
<style>
*{{box-sizing:border-box;margin:0;padding:0}}
body{{font-family:system-ui,sans-serif;background:#f8f9fa;color:#2c3e50}}
.bar{{padding:12px 20px;background:#fff;border-bottom:1px solid #e0e6ed;display:flex;align-items:center;gap:16px}}
.bar a{{color:#2980b9;text-decoration:none;font-size:.88rem}}.bar a:hover{{text-decoration:underline}}
.bar h1{{font-size:1rem;font-weight:600}}
.frame{{width:100%;border:none;height:calc(100vh - 50px)}}
</style>
</head>
<body>
<div class="bar">
  <a href="/projects/">&larr; 返回作品展</a>
  <h1>{title}</h1>
  <a href="https://github.com/D2RS-2026spring/{repo_name}" target="_blank" style="margin-left:auto">查看源码 &rarr;</a>
</div>
<iframe class="frame" src="content/index.html"></iframe>
</body>
</html>'''
```

- [ ] **Step 8: 添加 `build_project` 主逻辑函数**

```python
def build_project(repo_name):
    """Build showcase for a single project. Returns status dict."""
    repo_path = SHOWCASE_DIR / repo_name
    out_dir = SITE_DIR / repo_name
    title = read_readme_title(repo_path)

    if not repo_path.is_dir():
        return {'repo': repo_name, 'status': 'skipped', 'reason': 'submodule not found', 'title': title}

    # Priority 1: HTML files in repo root (e.g., citrus-nutrient-analysis-project)
    html_files = find_html_files(repo_path)
    root_html = [f for f in html_files if f.parent == repo_path]
    if root_html:
        # Copy all root HTML + assets to out_dir/content/
        content_dir = out_dir / 'content'
        if out_dir.exists():
            shutil.rmtree(out_dir)
        out_dir.mkdir(parents=True)
        content_dir.mkdir()
        for f in root_html:
            shutil.copy2(f, content_dir / f.name)
        # Copy supporting files (css, images, site_libs)
        for ext in ['*.css', '*.jpg', '*.jpeg', '*.png', '*.gif']:
            for f in repo_path.glob(ext):
                shutil.copy2(f, content_dir / f.name)
        if (repo_path / 'site_libs').is_dir():
            copy_tree(repo_path / 'site_libs', content_dir / 'site_libs')
        # Generate wrapper
        (out_dir / 'index.html').write_text(generate_wrapper_html(title, repo_name))
        return {'repo': repo_name, 'status': 'ok', 'type': 'html', 'title': title}

    # Priority 2: docs/ directory with HTML
    docs_dir = repo_path / 'docs'
    if docs_dir.is_dir():
        docs_html = list(docs_dir.glob('*.html'))
        if docs_html:
            content_dir = out_dir / 'content'
            if out_dir.exists():
                shutil.rmtree(out_dir)
            out_dir.mkdir(parents=True)
            copy_tree(docs_dir, content_dir)
            (out_dir / 'index.html').write_text(generate_wrapper_html(title, repo_name))
            return {'repo': repo_name, 'status': 'ok', 'type': 'docs', 'title': title}

    # Priority 3: output/figures with images
    imgs = find_output_figures(repo_path)
    if imgs:
        if out_dir.exists():
            shutil.rmtree(out_dir)
        out_dir.mkdir(parents=True)
        # Copy images to out_dir/images/
        img_dir = out_dir / 'images'
        img_dir.mkdir()
        copied = []
        for img in imgs:
            dst = img_dir / img.name
            if not dst.exists():
                shutil.copy2(img, dst)
            copied.append(dst)
        (out_dir / 'index.html').write_text(
            generate_gallery_html(title, copied, repo_name))
        return {'repo': repo_name, 'status': 'ok', 'type': 'gallery', 'title': title}

    # Priority 4: output/ with HTML
    output_dir = repo_path / 'output'
    if output_dir.is_dir():
        out_html = list(output_dir.glob('*.html'))
        if out_html:
            content_dir = out_dir / 'content'
            if out_dir.exists():
                shutil.rmtree(out_dir)
            out_dir.mkdir(parents=True)
            copy_tree(output_dir, content_dir)
            (out_dir / 'index.html').write_text(generate_wrapper_html(title, repo_name))
            return {'repo': repo_name, 'status': 'ok', 'type': 'output-html', 'title': title}

    # Priority 5-7: No usable output
    return {'repo': repo_name, 'status': 'skipped', 'reason': 'no output found', 'title': title}
```

- [ ] **Step 9: 添加 `generate_index` 函数（作品展首页）**

```python
def generate_index(results):
    """Generate showcase index page listing all projects."""
    ok = [r for r in results if r['status'] == 'ok']
    skipped = [r for r in results if r['status'] == 'skipped']
    failed = [r for r in results if r['status'] == 'failed']

    cards = ''
    for r in sorted(ok, key=lambda x: x['repo']):
        cards += f'''<div class="scard">
  <a href="{r['repo']}/">{r['title']}</a>
  <span class="stype">{r['type']}</span>
</div>\n'''

    skip_list = ''.join(f'<li>{r["repo"]} — {r.get("reason","")}</li>\n' for r in skipped)

    return f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>D2RS 结课作品展</title>
<style>
*{{box-sizing:border-box;margin:0;padding:0}}
body{{font-family:system-ui,sans-serif;background:#f8f9fa;color:#2c3e50;max-width:1000px;margin:0 auto;padding:20px}}
h1{{font-size:1.5rem;margin:20px 0 12px;color:#1a5276}}
.back{{color:#2980b9;text-decoration:none;font-size:.88rem}}.back:hover{{text-decoration:underline}}
.grid{{display:grid;grid-template-columns:repeat(auto-fill,minmax(280px,1fr));gap:12px;margin:16px 0}}
.scard{{background:#fff;border:1px solid #e0e6ed;border-radius:8px;padding:14px 16px}}
.scard a{{color:#1a5276;text-decoration:none;font-weight:600;font-size:.9rem}}.scard a:hover{{color:#2980b9}}
.stype{{display:block;font-size:.72rem;color:#636e72;margin-top:4px}}
.stats{{display:flex;gap:24px;margin:12px 0;font-size:.88rem;color:#636e72}}
.stats b{{color:#1a5276}}
section{{margin:24px 0}}
h2{{font-size:1.1rem;color:#1a5276;margin-bottom:8px}}
ul{{font-size:.84rem;color:#636e72;padding-left:20px}}ul li{{margin:4px 0}}
</style>
</head>
<body>
<a class="back" href="/projects/">&larr; 返回主页</a>
<h1>D2RS 结课作品展</h1>
<div class="stats">
  <span><b>{len(ok)}</b> 个项目已上线</span>
  <span><b>{len(skipped)}</b> 个项目暂不可用</span>
  <span><b>{len(failed)}</b> 个编译失败</span>
</div>
<div class="grid">
{cards}
</div>
<section>
<h2>暂不可用的项目</h2>
<ul>{skip_list}</ul>
</section>
</body>
</html>'''
```

- [ ] **Step 10: 添加 `main` 入口**

```python
def main():
    if not SHOWCASE_DIR.is_dir():
        print("showcase/ directory not found. Run 'git submodule update --init' first.")
        return

    # Clean and create site directory
    if SITE_DIR.exists():
        shutil.rmtree(SITE_DIR)
    SITE_DIR.mkdir(parents=True)

    # Find all submodule directories
    repos = sorted([d.name for d in SHOWCASE_DIR.iterdir() if d.is_dir()])
    print(f"Found {len(repos)} submodules in showcase/")

    results = []
    for repo_name in repos:
        print(f"  Building: {repo_name}...", end=' ')
        result = build_project(repo_name)
        results.append(result)
        print(f"{result['status']}" + (f" ({result['type']})" if result.get('type') else f" - {result.get('reason','')}"))

    # Generate index
    index_html = generate_index(results)
    index_path = SITE_DIR / 'index.html'
    index_path.write_text(index_html)

    # Write build report
    report_path = SCRIPT_DIR / 'showcase-build-report.json'
    report_path.write_text(json.dumps(results, indent=2, ensure_ascii=False))

    ok_count = sum(1 for r in results if r['status'] == 'ok')
    skip_count = sum(1 for r in results if r['status'] == 'skipped')
    fail_count = sum(1 for r in results if r['status'] == 'failed')
    print(f"\n✅ Showcase build complete: {ok_count} ok, {skip_count} skipped, {fail_count} failed")
    print(f"   Output: site/showcase/")
    print(f"   Report: showcase-build-report.json")

if __name__ == '__main__':
    main()
```

- [ ] **Step 11: 运行 build_showcase.py 验证**

```bash
cd /Users/gaoch/GitHub/D2RS-2026spring/projects
python3 build_showcase.py
# 预期: 扫描所有 submodule，输出每个项目的构建状态
# 预期: site/showcase/ 目录生成对应文件
```

- [ ] **Step 12: Commit**

```bash
git add build_showcase.py
git commit -m "feat: add build_showcase.py to compile project showcase"
```

---

## Task 3: 修改 `build_site.py` 添加作品展链接

**Files:**
- Modify: `build_site.py` (行 ~372-421, cards_html section)

- [ ] **Step 1: 在 `build_site.py` 开头加载 showcase 状态**

在文件开头的 imports 之后（约第 7 行后），添加 showcase 状态加载：

```python
# Load showcase build report (if exists)
showcase_ok = set()
report_path = SCRIPT_DIR / 'showcase-build-report.json'
if report_path.exists():
    try:
        with open(report_path) as f:
            for r in json.load(f):
                if r.get('status') == 'ok':
                    showcase_ok.add(r['repo'])
    except Exception:
        pass
```

- [ ] **Step 2: 在卡片 HTML 中添加作品展链接**

在 `build_site.py` 约第 401-421 行的 `cards_html += f'''` 块中，在 `card-foot` 的 `clinks` div 之后、`issue` 链接之前，添加作品展链接：

找到这一行（约第 419 行）：
```python
        <a class="clink issue" href="{issue}" target="_blank" rel="noopener">Issue #{p["num"]}</a>
```

在其前面添加：
```python
      <div class="card-foot">
        <div class="clinks">
          {doi_html}
          {showcase_html}
          <a class="clink" href="{repo}" target="_blank" rel="noopener">
```

然后在构建卡片的循环中（约第 379 行之后），添加 showcase 链接的构建：

```python
    # Showcase link
    repo_name = p['repo'].split('/', 1)[1] if p.get('repo') and '/' in p['repo'] else ''
    if repo_name and repo_name in showcase_ok:
        showcase_html = f'<a class="clink showcase" href="/projects/showcase/{repo_name}/" target="_blank">结课作品</a>'
    else:
        showcase_html = ''
```

- [ ] **Step 3: 在 CSS 中添加作品展链接样式**

在 `CSS` 字符串中（约第 500 行附近），添加：

```css
.clink.showcase{color:#27ae60;font-weight:600}.clink.showcase:hover{color:#1e8449}
```

- [ ] **Step 4: 运行 build_site.py 验证**

```bash
cd /Users/gaoch/GitHub/D2RS-2026spring/projects
python3 build_site.py
# 预期: 生成的 index.html 中，已提交项目的卡片包含 "结课作品" 链接
```

- [ ] **Step 5: 在浏览器中预览效果**

```bash
open /Users/gaoch/GitHub/D2RS-2026spring/projects/index.html
# 检查卡片是否有 "结课作品" 绿色链接
```

- [ ] **Step 6: Commit**

```bash
git add build_site.py
git commit -m "feat: add showcase link to project cards"
```

---

## Task 4: 更新 `.gitignore` 和 GitHub Actions 工作流

**Files:**
- Modify: `.gitignore`
- Modify: `.github/workflows/update-site.yml`

- [ ] **Step 1: 更新 .gitignore**

在 `.gitignore` 中添加：

```
site/
showcase-build-report.json
```

- [ ] **Step 2: 更新 GitHub Actions 工作流**

修改 `.github/workflows/update-site.yml`，在 "Build site" 步骤之前添加 submodule 初始化和 showcase 构建：

```yaml
name: Update Project Showcase

on:
  schedule:
    - cron: '0 19 * * *'
  workflow_dispatch:

permissions:
  contents: write

jobs:
  build-and-deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          submodules: recursive
          token: ${{ secrets.GITHUB_TOKEN }}

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.12'

      - name: Build site
        env:
          GH_TOKEN: ${{ secrets.GITHUB_TOKEN }}
        run: python3 build_site.py

      - name: Build showcase
        env:
          GH_TOKEN: ${{ secrets.GITHUB_TOKEN }}
        run: python3 build_showcase.py

      - name: Deploy to GitHub Pages
        uses: peaceiris/actions-gh-pages@v4
        with:
          github_token: ${{ secrets.GITHUB_TOKEN }}
          publish_dir: .
          include_files: index.html;submitted.html;pending.html;not_submitted.html;site/showcase/**
          keep_files: true
```

- [ ] **Step 3: Commit**

```bash
git add .gitignore .github/workflows/update-site.yml
git commit -m "ci: add showcase build step and update deployment config"
```

---

## Task 5: 本地测试与部署

**Files:** (none — verification only)

- [ ] **Step 1: 本地完整测试**

```bash
cd /Users/gaoch/GitHub/D2RS-2026spring/projects

# 确保 submodule 已初始化
git submodule update --init --recursive

# 运行 showcase 构建
python3 build_showcase.py
# 预期: 输出 ok/skipped 统计

# 运行主页构建
python3 build_site.py
# 预期: 生成包含作品展链接的 index.html

# 本地预览
open index.html
open site/showcase/index.html
```

- [ ] **Step 2: 检查几个项目的展示页面**

```bash
# 检查 citrus-nutrient-analysis-project（应该有 HTML 输出）
open site/showcase/citrus-nutrient-analysis-project/

# 检查 neanderthal-ecosystem-productivity（应该有 figures）
open site/showcase/neanderthal-ecosystem-productivity/
```

- [ ] **Step 3: 提交并推送**

```bash
git add -A
git commit -m "feat: D2RS 结课作品展 — submodule + showcase build pipeline"
git push origin main
```

- [ ] **Step 4: 手动触发 GitHub Actions 部署**

```bash
gh workflow run update-site.yml --repo D2RS-2026spring/projects
# 等待部署完成
gh run list --repo D2RS-2026spring/projects --limit 1
```
