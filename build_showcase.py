#!/usr/bin/env python3
"""Build the D2RS showcase: copy project outputs to public/showcase/."""
import json, os, shutil
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
SHOWCASE_DIR = SCRIPT_DIR / 'showcase'
SITE_DIR = SCRIPT_DIR / 'public' / 'showcase'

IMG_EXTS = {'.png', '.jpg', '.jpeg', '.gif', '.svg', '.webp'}


def read_readme_title(repo_path):
    readme = repo_path / 'README.md'
    if readme.exists():
        for line in readme.read_text(encoding='utf-8', errors='replace').splitlines():
            line = line.strip()
            if line.startswith('# '):
                return line[2:].strip()
    return repo_path.name


def copy_tree(src, dst):
    if dst.exists():
        shutil.rmtree(dst)
    shutil.copytree(src, dst)


def find_html_files(repo_path):
    exclude = {'node_modules', '.git', 'renv', 'site_libs', '.quarto'}
    html_files = []
    for f in repo_path.rglob('*.html'):
        if any(part in exclude for part in f.parts):
            continue
        html_files.append(f)
    return html_files


def find_output_figures(repo_path):
    imgs = []
    for dirname in ['output', 'figures', 'docs']:
        d = repo_path / dirname
        if d.is_dir():
            for f in d.rglob('*'):
                if f.suffix.lower() in IMG_EXTS:
                    imgs.append(f)
    return imgs


GALLERY_CSS = """*{box-sizing:border-box;margin:0;padding:0}
body{font-family:system-ui,sans-serif;background:#f8f9fa;color:#2c3e50;padding:20px;max-width:1200px;margin:0 auto}
header{margin-bottom:24px}
header a{color:#2980b9;text-decoration:none;font-size:.9rem}
header a:hover{text-decoration:underline}
h1{font-size:1.4rem;margin:12px 0 8px}
.gallery{display:grid;grid-template-columns:repeat(auto-fill,minmax(300px,1fr));gap:16px}
figure{background:#fff;border:1px solid #e0e6ed;border-radius:8px;overflow:hidden}
figure img{width:100%;height:auto;display:block}
figcaption{padding:8px 12px;font-size:.82rem;color:#636e72}
footer{margin-top:32px;padding-top:16px;border-top:1px solid #e0e6ed;font-size:.8rem;color:#636e72}
footer a{color:#2980b9;text-decoration:none}"""


def generate_gallery_html(title, images, repo_name):
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
{GALLERY_CSS}
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


WRAPPER_CSS = """*{box-sizing:border-box;margin:0;padding:0}
body{font-family:system-ui,sans-serif;background:#f8f9fa;color:#2c3e50}
.bar{padding:12px 20px;background:#fff;border-bottom:1px solid #e0e6ed;display:flex;align-items:center;gap:16px}
.bar a{color:#2980b9;text-decoration:none;font-size:.88rem}.bar a:hover{text-decoration:underline}
.bar h1{font-size:1rem;font-weight:600}
.frame{width:100%;border:none;height:calc(100vh - 50px)}"""


def generate_wrapper_html(title, repo_name):
    return f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{title}</title>
<style>
{WRAPPER_CSS}
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


def build_project(repo_name):
    repo_path = SHOWCASE_DIR / repo_name
    out_dir = SITE_DIR / repo_name
    title = read_readme_title(repo_path)

    if not repo_path.is_dir():
        return {'repo': repo_name, 'status': 'skipped', 'reason': 'submodule not found', 'title': title}

    # Priority 1: HTML files in repo root
    html_files = find_html_files(repo_path)
    root_html = [f for f in html_files if f.parent == repo_path]
    if root_html:
        content_dir = out_dir / 'content'
        if out_dir.exists():
            shutil.rmtree(out_dir)
        out_dir.mkdir(parents=True)
        content_dir.mkdir()
        for f in root_html:
            shutil.copy2(f, content_dir / f.name)
        for ext in ['*.css', '*.jpg', '*.jpeg', '*.png', '*.gif']:
            for f in repo_path.glob(ext):
                shutil.copy2(f, content_dir / f.name)
        if (repo_path / 'site_libs').is_dir():
            copy_tree(repo_path / 'site_libs', content_dir / 'site_libs')
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


INDEX_CSS = """*{box-sizing:border-box;margin:0;padding:0}
body{font-family:system-ui,sans-serif;background:#f8f9fa;color:#2c3e50;max-width:1000px;margin:0 auto;padding:20px}
h1{font-size:1.5rem;margin:20px 0 12px;color:#1a5276}
.back{color:#2980b9;text-decoration:none;font-size:.88rem}.back:hover{text-decoration:underline}
.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(280px,1fr));gap:12px;margin:16px 0}
.scard{background:#fff;border:1px solid #e0e6ed;border-radius:8px;padding:14px 16px}
.scard a{color:#1a5276;text-decoration:none;font-weight:600;font-size:.9rem}.scard a:hover{color:#2980b9}
.stype{display:block;font-size:.72rem;color:#636e72;margin-top:4px}
.stats{display:flex;gap:24px;margin:12px 0;font-size:.88rem;color:#636e72}
.stats b{color:#1a5276}
section{margin:24px 0}
h2{font-size:1.1rem;color:#1a5276;margin-bottom:8px}
ul{font-size:.84rem;color:#636e72;padding-left:20px}ul li{margin:4px 0}"""


def generate_index(results):
    ok = [r for r in results if r['status'] == 'ok']
    skipped = [r for r in results if r['status'] == 'skipped']

    cards = ''
    for r in sorted(ok, key=lambda x: x['repo']):
        cards += f'<div class="scard"><a href="{r["repo"]}/">{r["title"]}</a><span class="stype">{r["type"]}</span></div>\n'

    skip_list = ''.join(f'<li>{r["repo"]} — {r.get("reason","")}</li>\n' for r in skipped)

    return f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>D2RS 结课作品展</title>
<style>
{INDEX_CSS}
</style>
</head>
<body>
<a class="back" href="/projects/">&larr; 返回主页</a>
<h1>D2RS 结课作品展</h1>
<div class="stats">
  <span><b>{len(ok)}</b> 个项目已上线</span>
  <span><b>{len(skipped)}</b> 个项目暂不可用</span>
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


def main():
    if not SHOWCASE_DIR.is_dir():
        print("showcase/ directory not found. Run 'git submodule update --init' first.")
        return

    if SITE_DIR.exists():
        shutil.rmtree(SITE_DIR)
    SITE_DIR.mkdir(parents=True)

    repos = sorted([d.name for d in SHOWCASE_DIR.iterdir() if d.is_dir()])
    print(f"Found {len(repos)} submodules in showcase/")

    results = []
    for repo_name in repos:
        print(f"  Building: {repo_name}...", end=' ')
        result = build_project(repo_name)
        results.append(result)
        status_str = result['status']
        if result.get('type'):
            status_str += f" ({result['type']})"
        elif result.get('reason'):
            status_str += f" - {result['reason']}"
        print(status_str)

    index_html = generate_index(results)
    (SITE_DIR / 'index.html').write_text(index_html)

    report_path = SCRIPT_DIR / 'showcase-build-report.json'
    report_path.write_text(json.dumps(results, indent=2, ensure_ascii=False))

    ok_count = sum(1 for r in results if r['status'] == 'ok')
    skip_count = sum(1 for r in results if r['status'] == 'skipped')
    print(f"\n✅ Showcase build complete: {ok_count} ok, {skip_count} skipped")
    print(f"   Output: site/showcase/")
    print(f"   Report: showcase-build-report.json")


if __name__ == '__main__':
    main()
