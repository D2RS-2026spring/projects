# D2RS 结课作品展设计

## 目标

将主页 (`index.html`) 中每个项目卡片链接到各项目的静态展示页面，形成完整的结课作品展。

## 架构

```
projects/
├── showcase/                    # git submodule 目录（28 个子模块）
│   ├── neanderthal-ecosystem-productivity/
│   ├── citrus-nutrient-analysis-project/
│   └── ...
├── site/                        # 编译输出（.gitignore）
│   └── showcase/
│       ├── neanderthal-ecosystem-productivity/
│       │   └── index.html
│       └── ...
├── build_showcase.py            # 新增：作品展编译脚本
├── build_site.py                # 现有：主页生成（需修改：添加作品展链接）
└── .github/workflows/
    └── update-site.yml          # 更新：加入作品展编译步骤
```

## 工作流程

### 1. 添加 Submodule

对每个已提交且仓库在 `D2RS-2026spring` 组织下的项目，添加为 submodule：

```bash
git submodule add https://github.com/D2RS-2026spring/<repo-name>.git showcase/<repo-name>
```

已识别的 28 个待添加仓库（去重后）：

```
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
Extraction---of---Algal---Extracellular---Polymeric---Substances.
Synthetic-Microbiome-Reproduction
soil-cadmium-immobilized-bacteria
```

### 2. build_showcase.py 编译逻辑

**直接使用已有输出**，不重新编译。脚本流程：

```
对每个 submodule：
  1. 检测仓库中的可用输出（按优先级）
  2. 复制到 site/showcase/<repo-name>/
  3. 生成 index.html 入口页
  4. 记录状态（ok / skipped / failed）
```

**输出检测优先级：**

| 优先级 | 检测到的文件 | 处理方式 |
|--------|------------|---------|
| 1 | `*.html`（非 README 渲染） | 直接复制（如 citrus-nutrient-analysis-project 的 Rmd 渲染结果） |
| 2 | `docs/*.html` | 复制 `docs/` 目录 |
| 3 | `output/figures/*.png/jpg` | 生成图片画廊页 |
| 4 | `output/*.html` | 直接复制 |
| 5 | `*.qmd` 或 `*.Rmd` | 尝试 `quarto render`（标记为"编译生成"） |
| 6 | `.zip` 文件 | 解压后重新检测 |
| 7 | 无可用内容 | 标记为 `skipped` |

**index.html 入口页模板（每个项目）：**

```html
<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="UTF-8">
  <title>{project_title}</title>
  <style>/* 简洁样式 */</style>
</head>
<body>
  <header>
    <a href="/projects/">← 返回作品展</a>
    <h1>{project_title}</h1>
    <p>{description}</p>
  </header>
  <main>
    <!-- 项目内容：HTML / 图片画廊 / README 渲染 -->
  </main>
  <footer>
    <a href="https://github.com/D2RS-2026spring/{repo}">查看源码</a>
  </footer>
</body>
</html>
```

### 3. build_site.py 修改

在项目卡片中添加"作品展"链接：

```python
# 新增字段
showcase_url = f'/projects/showcase/{repo_name}/' if repo_name in showcase_projects else None
```

卡片 HTML 中添加：

```html
<a href="{showcase_url}" class="showcase-link">结课作品</a>
```

### 4. GitHub Actions 更新

在 `update-site.yml` 中增加编译步骤：

```yaml
- name: Build showcase
  run: |
    git submodule update --init --recursive
    python build_showcase.py
- name: Deploy
  uses: peaceiris/actions-gh-pages@v4
  with:
    publish_dir: .
    # 部署整个目录（包括 site/showcase/）
    # 或只部署特定文件：keep_files: true
```

## 编译失败处理

- 失败的项目不阻塞其他项目
- `build_showcase.py` 输出编译报告（成功/跳过/失败数量）
- 失败项目在卡片上标记为"作品展暂不可用"
- 失败原因记录到 `showcase-build-report.json`

## 约束

- 不重新编译学生项目，直接使用已有 output
- 动态站（Streamlit/Shiny）跳过，标记为 `skipped`
- GitHub Pages 部署路径：`/projects/showcase/<repo-name>/`
- 主页路径：`/projects/`（保持不变）
