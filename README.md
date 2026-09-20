# 人民网中日对译语料库

[![License: GPL v3](https://img.shields.io/badge/License-GPL%20v3-blue.svg)](https://www.gnu.org/licenses/gpl-3.0)
[![Python 3.6+](https://img.shields.io/badge/python-3.6+-blue.svg)](https://www.python.org/downloads/)
[![Auto Update](https://img.shields.io/badge/auto--update-every%203%20days-green.svg)](https://github.com/koshoutou/j.people.com-corpus-page/actions)

从人民网日文版「中国語教室」栏目自动采集的中日双语平行语料库，适用于机器翻译训练、双语词典构建、翻译评估与语言学研究。

---

## 项目简介

本项目是一个自动化的中日双语语料库采集系统，从人民网日文版「中国語教室」栏目爬取中日对照翻译语料。系统支持完整爬取和增量更新两种模式，每 3 天自动更新一次，确保语料库始终保持最新状态。

**当前数据统计**（自动更新）：
- 总句对数：**9,947**
- 来源文章：**1,513 篇**
- 不同标题：**1,512 个**
- 时间跨度：2018-03-01 至今
- 支持格式：JSON、JSONL、TMX、TXT、XML、XLSX

---

## 项目动机

中日双语平行语料在机器翻译、语言学研究等领域具有重要价值，但高质量、持续更新的中日平行语料资源相对稀缺。人民网日文版「中国語教室」栏目提供了丰富的中日对照翻译内容，是构建平行语料库的理想来源。

本项目的目标是：
1. **自动化采集**：通过爬虫系统自动提取中日对译句对
2. **持续更新**：通过 GitHub Actions 每 3 天自动增量更新
3. **多格式导出**：支持 JSON、TMX、TXT、XML、XLSX 等多种格式
4. **在线浏览**：提供现代化的 Web 界面，支持搜索和分页浏览

---

## 作者介绍

| 项目 | 信息 |
|------|------|
| **作者** | koshoutou（Inkcoo） |
| **院校** | 湖南农业大学 |
| **方向** | 自学 AI 全栈开发，关注 AI 应用工程与 Web 产品设计 |
| **GitHub** | [@koshoutou](https://github.com/koshoutou) |

---

## 功能特性

### 核心功能
- **完整爬取**：支持爬取约 2000 篇文章，生成完整语料库
- **增量更新**：智能识别新增内容，仅爬取最新文章
- **多格式导出**：JSON、JSONL、TMX、TXT、XML、XLSX
- **自动更新**：GitHub Actions 每 3 天自动运行增量更新

### 网页功能
- **现代化界面**：响应式设计，支持桌面和移动端
- **搜索功能**：支持按中文、日文、标题关键词搜索
- **分页浏览**：按需加载，提升浏览性能
- **实时统计**：显示语料库总量、来源数等关键指标

### 技术特点
- **多格式解析**：支持 2018-2026 年不同网页布局
- **智能分句**：中日文混合分句算法
- **数据清洗**：自动去除 HTML 残留和特殊符号
- **错误处理**：完善的异常处理和日志记录

---

## 语料下载

### 直接下载（GitHub 直链）

| 格式 | 下载链接 | 说明 |
|------|----------|------|
| **JSON** | [corpus.json](https://raw.githubusercontent.com/koshoutou/j.people.com-corpus-page/main/data/corpus.json) | 完整语料库（推荐） |
| **JSONL** | [zh_ja_corpus.jsonl](https://raw.githubusercontent.com/koshoutou/j.people.com-corpus-page/main/data/export/zh_ja_corpus.jsonl) | 每行一个句对（流式/大模型友好） |
| **TMX** | [zh_ja_corpus.tmx](https://raw.githubusercontent.com/koshoutou/j.people.com-corpus-page/main/data/export/zh_ja_corpus.tmx) | 翻译记忆交换格式 |
| **TXT** | [zh_ja_corpus.txt](https://raw.githubusercontent.com/koshoutou/j.people.com-corpus-page/main/data/export/zh_ja_corpus.txt) | 人类可读文本 |
| **XML** | [zh_ja_corpus.xml](https://raw.githubusercontent.com/koshoutou/j.people.com-corpus-page/main/data/export/zh_ja_corpus.xml) | 结构化 XML |
| **XLSX** | [zh_ja_corpus.xlsx](https://raw.githubusercontent.com/koshoutou/j.people.com-corpus-page/main/data/export/zh_ja_corpus.xlsx) | Excel 表格 |
| **分页数据** | [data/pages/](https://github.com/koshoutou/j.people.com-corpus-page/tree/main/data/pages) | 分页 JSON 文件 |

> **更新时间**：语料库通过 GitHub Actions 每 3 天自动更新一次，并同步重导全部导出格式，最新数据可查看 [Actions 运行记录](https://github.com/koshoutou/j.people.com-corpus-page/actions)。

### 重新生成导出格式

仓库内 `data/export/` 已包含 6 种格式，也可用独立脚本重新生成：

```bash
# 安装依赖
pip install requests lxml pandas openpyxl

# 从 data/corpus.json 重新生成全部格式到 data/export/
python export_formats.py
```

如需从网络重新全量爬取并重建语料库，运行完整爬虫（会自动写 `data/corpus.json`、分页并导出全部格式）：

```bash
python people_cn_corpus_crawler_2000.py
```

---

## 数据格式示例

### JSON 格式
```json
[
  {
    "id": "sent_000001",
    "zh": "中国近年来在环境保护方面取得了显著成就。",
    "ja": "中国は近年、環境保護面で顕著な成果を上げている。",
    "source_url": "https://j.people.com.cn/n3/2023/0512/c95961-20001234.html",
    "title": "中国的环境保护政策"
  }
]
```

### TMX 格式（翻译记忆交换格式）
```xml
<?xml version="1.0" encoding="UTF-8"?>
<tmx version="1.4">
  <header creationtool="PeopleCN_Bilingual_Crawler" 
          creationtoolversion="2.3"
          datatype="PlainText" 
          segtype="sentence" 
          adminlang="en-US" 
          srclang="zh"/>
  <body>
    <tu tuid="sent_000001">
      <prop type="source_url">https://j.people.com.cn/n3/2023/0512/c95961-20001234.html</prop>
      <prop type="title">中国的环境保护政策</prop>
      <tuv xml:lang="zh"><seg>中国近年来在环境保护方面取得了显著成就。</seg></tuv>
      <tuv xml:lang="ja"><seg>中国は近年、環境保護面で顕著な成果を上げている。</seg></tuv>
    </tu>
  </body>
</tmx>
```

---

## 快速开始

### 环境要求
- Python 3.6+
- pip 包管理器

### 安装依赖
```bash
pip install requests lxml pandas
```

### 使用方式

#### 1. 完整爬取（首次使用）
```bash
python people_cn_corpus_crawler_2000.py
```
爬取约 2000 篇文章，生成完整语料库，输出到带时间戳的目录。

#### 2. 增量更新（日常维护）
```bash
python update_latest_corpus.py
```
自动获取最新文章，更新 `data/corpus.json` 和分页文件。

#### 3. 本地浏览
```bash
# Linux/Mac
bash deploy.sh

# Windows
powershell -ExecutionPolicy Bypass -File deploy.ps1
```
启动本地服务器，访问 `http://localhost:8000` 浏览语料库。

---

## 项目结构

```
.
├── index.html                          # 主页面
├── css/style.css                       # 样式文件
├── js/main.js                          # JavaScript 逻辑
├── worker.js                           # Cloudflare Workers 优化脚本
├── wrangler.toml                       # Cloudflare Workers 配置
│
├── data/                               # 数据目录
│   ├── corpus.json                     # 完整语料库
│   └── pages/                          # 分页数据
│       ├── corpus_page_1.json
│       ├── corpus_page_2.json
│       ├── ...
│       ├── metadata.json               # 元数据
│       └── stats.json                  # 统计信息
│
├── people_cn_corpus_crawler_2000.py   # 全量爬取脚本（整合解析/分页/统计/导出，并作共享库）
├── update_latest_corpus.py             # 增量更新脚本（复用全量爬虫的解析/分页/统计/导出）
├── export_formats.py                   # 格式输出脚本（TMX/JSONL/JSON/TXT/XML/XLSX）
│
├── .github/workflows/                  # GitHub Actions
│   └── update-corpus.yml               # 自动更新工作流
│
├── deploy.sh / deploy.ps1              # 部署脚本
└── README.md                           # 项目说明
```

---

## 部署指南

### GitHub Pages 部署

1. Fork 本仓库到你的 GitHub 账号
2. 进入仓库 Settings → Pages
3. Source 选择 `main` 分支，目录选择 `/ (root)`
4. 保存后等待部署完成
5. 访问 `https://<your-username>.github.io/j.people.com-corpus-page/`

### Cloudflare Pages 部署

1. 登录 [Cloudflare Dashboard](https://dash.cloudflare.com/)
2. 进入 Workers & Pages → Pages → Create a project
3. 选择 "Connect to Git"，选择本仓库
4. Build settings：
   - Build command: 留空
   - Build output directory: `/`
5. 点击 "Save and Deploy"
6. 部署完成后访问分配的域名

### Cloudflare Workers 部署（可选）

```bash
# 安装 Wrangler CLI
npm install -g wrangler

# 登录 Cloudflare
wrangler login

# 部署 Worker
wrangler deploy
```

---

## 技术栈

- **前端**：HTML5 + CSS3 + Vanilla JavaScript
- **后端爬虫**：Python 3 + requests + lxml
- **数据处理**：pandas（可选，用于 Excel 导出）
- **部署**：GitHub Pages / Cloudflare Pages / Cloudflare Workers
- **自动化**：GitHub Actions（定时任务）

---

## 自动更新机制

本项目通过 GitHub Actions 实现自动更新：

- **触发条件**：每 3 天 UTC 00:00 自动运行
- **更新流程**：
  1. 检出最新代码
  2. 安装 Python 依赖
  3. 运行 `update_latest_corpus.py`
  4. 检查是否有数据变更
  5. 如有更新，自动提交并推送

- **手动触发**：可在 Actions 页面手动运行 "自动更新语料库" 工作流

---

## 使用说明

### 数据加载示例（Python）
```python
import json

# 加载 JSON 语料库
with open("data/corpus.json", "r", encoding="utf-8") as f:
    data = json.load(f)

# data 为句对列表，每项包含 id、zh、ja、source_url、title 等字段
print(f"总句对数: {len(data)}")
print(f"第一条: {data[0]['zh']}")
```

### 数据清洗建议
1. **去重**：根据 `source_url` 和 `zh` 字段去除重复句对
2. **清洗标点**：去除多余空白和特殊符号
3. **质量过滤**：过滤过短或异常的句对

---

## 注意事项

1. **数据来源**：本项目数据来源于人民网日文版公开内容，仅供学术研究与非商业用途
2. **使用规范**：请遵守目标站点的 robots.txt 和使用条款
3. **爬虫频率**：如需自行爬取，建议保持适当的请求间隔（默认 1 秒）
4. **版权说明**：数据版权归原作者/人民网所有，本项目仅提供技术整理

---

## 许可证

本项目代码采用 [GNU GPL v3](https://www.gnu.org/licenses/gpl-3.0) 许可证。  
数据内容版权归原作者人民网所有，仅供学术研究和非商业用途使用。

---

## 在线演示

访问示例网站：[https://j-people-com-corpus-page.pages.dev/](https://j-people-com-corpus-page.pages.dev/)

---

## 联系方式

- **作者**：koshoutou（Inkcoo）
- **邮箱**：koshoutou@foxmail.com
- **GitHub**：[https://github.com/koshoutou](https://github.com/koshoutou)

如有问题或建议，欢迎通过 GitHub Issues 反馈。

---

## 致谢

感谢人民网日文版提供的公开内容，以及所有为本项目提出建议的同仁。
