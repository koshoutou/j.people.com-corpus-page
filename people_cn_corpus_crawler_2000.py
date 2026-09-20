# -*- coding: UTF-8 -*-
"""
人民网日文版「中国語教室」栏目 中日对译语料 · 全量爬取脚本

整合能力：
  1. 网页解析：新格式（2023-07-27 后，段对段 1:1）、旧格式、早期格式（奇偶索引）；
  2. 分页：写 data/pages/corpus_page_*.json + metadata.json；
  3. 数据统计：写 data/pages/stats.json（总语句数 / 来源文章 / 不同标题）；
  4. 格式导出：TMX / JSONL / JSON / TXT / XML / XLSX -> data/export/。

用法：python people_cn_corpus_crawler_2000.py [页数] [延迟秒]

本脚本同时作为共享库，供 update_latest_corpus.py 复用解析、分页、统计、导出能力。
"""
import os
import re
import sys
import time
import json
import logging
from datetime import datetime
from urllib.parse import urljoin
from typing import List, Optional, Tuple

import requests
from lxml import etree

# 保证同目录模块可导入（export_formats）
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from export_formats import export_all

# ====================== 常量 ======================
BASE_URL = "https://j.people.com.cn"
INDEX_BASE = "https://j.people.com.cn/95961/index{}.html"
INDEX_URL = INDEX_BASE.format(1)
STOP_URL = "https://j.people.com.cn/n3/2018/0301/c95961-9431381.html"
NEW_FORMAT_CUTOFF = 20230727            # 新格式生效日期（YYYYMMDD）
SRC_LANG = "zh-CN"
TRG_LANG = "ja"

REPO_DIR = os.path.dirname(os.path.abspath(__file__))
CORPUS_FILE = os.path.join(REPO_DIR, "data", "corpus.json")
PAGES_DIR = os.path.join(REPO_DIR, "data", "pages")
EXPORT_DIR = os.path.join(REPO_DIR, "data", "export")

# 日志仅输出到控制台，不写仓库（避免产生爬取日志记录）
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler()],
)
logger = logging.getLogger(__name__)

session = requests.Session()
session.headers.update({
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Accept": "text/html,application/xhtml+xml;q=0.9",
    "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
    "Accept-Encoding": "gzip, deflate, br",
    "Connection": "keep-alive",
    "Upgrade-Insecure-Requests": "1",
})


# ====================== 文本清洗 ======================

_KEEP_RE = re.compile(
    r"[^\u4e00-\u9fff\u3040-\u309f\u30a0-\u30ff"
    r"\uac00-\ud7af\u3131-\u318f\u1100-\u11ff"
    r"\u0030-\u0039\u0041-\u005a\u0061-\u007a\u0020"
    r"\u3000-\u303f\uff00-\uffef"
    r"\u2000-\u206f\u2e80-\u2eff\u31c0-\u31ef"
    r"\u3200-\u32ff\u3300-\u33ff\ufe30-\ufe4f"
    r"\uf900-\ufaff\u2f800-\u2fa1f"
    r"\u0021-\u002f\u003a-\u0040\u005b-\u0060\u007b-\u007e]"
)
_HIRA_RE = re.compile(r"[\u3040-\u309f]")
_KATA_RE = re.compile(r"[\u30a0-\u30ff]")
_KANJI_RE = re.compile(r"[\u4e00-\u9fff]")


def clean_text(text: str) -> str:
    """统一清洗：去多余空白 + 仅保留中日韩英数与基本标点。"""
    if not text:
        return ""
    text = text.strip()
    text = re.sub(r"\s+", " ", text)
    text = _KEEP_RE.sub("", text)
    return text.strip()


def detect_lang(text: str) -> str:
    """按平/片假名比例返回 'ja' / 'zh' / 'other'。日文含假名，纯中文则无假名。"""
    if not text:
        return "other"
    hira = len(_HIRA_RE.findall(text))
    kata = len(_KATA_RE.findall(text))
    if hira + kata >= 2:
        return "ja"
    if len(_KANJI_RE.findall(text)) >= 2:
        return "zh"
    return "other"


def robust_split_sentences(text: str) -> List[str]:
    """旧/早期格式使用的健壮分句（按。！？；切分）。"""
    sentences = re.split(r"([。！？；])", text)
    merged: List[str] = []
    for i in range(0, len(sentences) - 1, 2):
        s = sentences[i] + (sentences[i + 1] if i + 1 < len(sentences) else "")
        if s.strip():
            merged.append(s.strip())
    if len(sentences) % 2 == 1 and sentences[-1].strip():
        merged.append(sentences[-1].strip())
    return merged


def extract_yyyymmdd(url: str) -> Optional[int]:
    """从 URL 提取文章发布日期 YYYYMMDD（int），失败返回 None。"""
    m = re.search(r"/n3/(\d{4})/(\d{2})(\d{2})/", url)
    if not m:
        return None
    try:
        return int(m.group(1) + m.group(2) + m.group(3))
    except ValueError:
        return None


def extract_title(html: etree._Element) -> str:
    """提取标题：优先 h1/h2，其次 <title>。"""
    title = clean_text("".join(html.xpath("//h1/text() | //h2/text()")))
    if title:
        return title
    return clean_text("".join(html.xpath("//title/text()"))) or "N/A"


# ====================== 解析：新格式（段对段 1:1） ======================

_SELECTOR_NEW = '//div[contains(@class, "j-d2txt-fanyi")]'


def _extract_paragraphs(content_div) -> List[Tuple[str, str]]:
    """提取容器内非空段落，返回 [(lang, text), ...]。"""
    paragraphs = content_div.xpath("./p") or content_div.xpath(".//p")
    items: List[Tuple[str, str]] = []
    for p in paragraphs:
        text = "".join(p.xpath(".//text()")).strip()
        if text:
            items.append((detect_lang(text), text))
    return items


def _split_into_zh_ja(items: List[Tuple[str, str]]):
    """把 [(lang, text), ...] 按交替规则拆成 zh / ja 两桶，截断到最短。"""
    items = [(l, t) for l, t in items if l in ("zh", "ja")]
    if not items:
        return [], []
    expected = items[0][0]
    zh: List[str] = []
    ja: List[str] = []
    for lang, text in items:
        if lang == expected:
            (zh if lang == "zh" else ja).append(text)
            expected = "ja" if lang == "zh" else "zh"
        else:
            # 漏空段导致错位：合并进当前语种，期望翻转但指向相反语种
            (zh if lang == "zh" else ja).append(text)
            expected = "ja" if lang == "zh" else "zh"
    n = min(len(zh), len(ja))
    return zh[:n], ja[:n]


def parse_new_format(html, url: str) -> Optional[List[Tuple[str, str, dict]]]:
    """新格式（2023-07-27 后）：整段 1:1 对齐，内部不再按句号切分。"""
    nodes = html.xpath(_SELECTOR_NEW)
    if not nodes:
        return None
    zh_paras, ja_paras = _split_into_zh_ja(_extract_paragraphs(nodes[0]))
    if not zh_paras or not ja_paras:
        return None
    title = extract_title(html)
    pairs: List[Tuple[str, str, dict]] = []
    for zh_para, ja_para in zip(zh_paras, ja_paras):
        zh_clean = clean_text(zh_para)
        ja_clean = clean_text(ja_para)
        if zh_clean and ja_clean:
            pairs.append((zh_clean, ja_clean, {"source_url": url, "title": title}))
    return pairs or None


# ====================== 解析：旧格式 / 早期格式（奇偶索引，原逻辑） ======================

_SELECTOR_OLD = '//div[contains(@class, "txt_con3")]'
_SELECTOR_EARLY = '//div[contains(@class, "wb_31") and contains(@class, "wb_51")]'


def _parse_by_odd_even(html, selector: str):
    """旧/早期格式共用：按奇偶索引分离中日文段落（原脚本逻辑，不改动）。"""
    content_div = html.xpath(selector)
    if not content_div:
        return None
    paragraphs = content_div[0].xpath(".//p")
    if len(paragraphs) < 2:
        return None
    zh_paragraphs: List[str] = []
    ja_paragraphs: List[str] = []
    for i, p in enumerate(paragraphs):
        text = "".join(p.xpath(".//text()")).strip()
        if text:
            if i % 2 == 0:
                zh_paragraphs.append(clean_text(text))
            else:
                ja_paragraphs.append(clean_text(text))
    if not zh_paragraphs or not ja_paragraphs:
        return None
    return zh_paragraphs, ja_paragraphs


def parse_old_format(html, url: str):
    """旧格式（2023-07-27 前）：txt_con3，原奇偶索引逻辑。"""
    return _parse_by_odd_even(html, _SELECTOR_OLD)


def parse_early_format(html, url: str):
    """早期格式（2019 及更早）：wb_31 wb_51，原奇偶索引逻辑。"""
    return _parse_by_odd_even(html, _SELECTOR_EARLY)


def parse_article(url: str) -> List[Tuple[str, str, dict]]:
    """解析详情页，按 URL 发布日期分流三种格式，返回 [(zh, ja, props), ...]。"""
    logger.info(f"解析文章: {url}")
    try:
        resp = session.get(url, timeout=15)
        resp.raise_for_status()
        resp.encoding = "utf-8"
        html = etree.HTML(resp.text)

        yyyymmdd = extract_yyyymmdd(url)
        if yyyymmdd is not None and yyyymmdd >= NEW_FORMAT_CUTOFF:
            pairs = parse_new_format(html, url) or []
            logger.info(f"  [新格式] 提取 {len(pairs)} 对")
            return pairs

        # 旧 / 早期格式
        result = parse_old_format(html, url) or parse_early_format(html, url)
        if not result:
            logger.warning(f"  旧/早期格式解析失败: {url}")
            return []
        zh_paras, ja_paras = result
        title = extract_title(html)
        pairs: List[Tuple[str, str, dict]] = []
        for zh_para, ja_para in zip(zh_paras, ja_paras):
            zh_sents = robust_split_sentences(zh_para)
            ja_sents = robust_split_sentences(ja_para)
            for zh_sent, ja_sent in zip(zh_sents, ja_sents):
                zc, jc = clean_text(zh_sent), clean_text(ja_sent)
                if zc and jc:
                    pairs.append((zc, jc, {"source_url": url, "title": title}))
        logger.info(f"  [旧/早期格式] 提取 {len(pairs)} 对")
        return pairs
    except Exception as e:
        logger.error(f"  解析文章失败 {url}: {e}")
        return []


# ====================== 分页 + 数据统计（整合自 split_data.py） ======================

def compute_stats(records: List[dict]) -> dict:
    """统计：总语句数 / 来源文章 / 不同标题。"""
    return {
        "total_sentences": len(records),
        "unique_sources": len({r.get("source_url") for r in records if r.get("source_url")}),
        "unique_titles": len({r.get("title") for r in records if r.get("title")}),
        "last_updated": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }


def rebuild_pages_and_stats(corpus_file: str, pages_dir: str, items_per_page: int = 10) -> dict:
    """读取 corpus.json，写分页 page 文件 + metadata.json + stats.json。"""
    os.makedirs(pages_dir, exist_ok=True)
    with open(corpus_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    # 清理旧分页文件，避免数量变化时残留
    for old in os.listdir(pages_dir):
        if old.startswith("corpus_page_"):
            try:
                os.remove(os.path.join(pages_dir, old))
            except OSError:
                pass

    total = len(data)
    total_pages = (total + items_per_page - 1) // items_per_page
    for page in range(total_pages):
        start = page * items_per_page
        end = min(start + items_per_page, total)
        with open(os.path.join(pages_dir, f"corpus_page_{page + 1}.json"), "w", encoding="utf-8") as f:
            json.dump(data[start:end], f, ensure_ascii=False, indent=2)

    meta = {"total_items": total, "items_per_page": items_per_page, "total_pages": total_pages}
    with open(os.path.join(pages_dir, "metadata.json"), "w", encoding="utf-8") as f:
        json.dump(meta, f, ensure_ascii=False, indent=2)

    stats = compute_stats(data)
    with open(os.path.join(pages_dir, "stats.json"), "w", encoding="utf-8") as f:
        json.dump(stats, f, ensure_ascii=False, indent=2)

    logger.info(f"分页 {total_pages} 页 + 统计已生成（总语句 {stats['total_sentences']}）")
    return stats


def finalize_and_save(records: List[dict]) -> List[dict]:
    """去重 + 编号 + 写 corpus.json + 分页/统计 + 导出全部格式。返回最终记录。"""
    seen = set()
    deduped: List[dict] = []
    removed = 0
    for r in records:
        key = (r.get("zh"), r.get("ja"))
        if key in seen:
            removed += 1
            continue
        seen.add(key)
        deduped.append(r)
    if removed:
        logger.info(f"去重：移除 {removed} 条，剩余 {len(deduped)} 条")

    for i, r in enumerate(deduped, 1):
        r["id"] = f"sent_{i:06d}"

    os.makedirs(os.path.dirname(CORPUS_FILE), exist_ok=True)
    with open(CORPUS_FILE, "w", encoding="utf-8") as f:
        json.dump(deduped, f, ensure_ascii=False, indent=2)
    logger.info(f"已保存语料库: {CORPUS_FILE}（{len(deduped)} 条）")

    rebuild_pages_and_stats(CORPUS_FILE, PAGES_DIR)
    try:
        export_all(deduped, EXPORT_DIR, prefix="zh_ja_corpus")
    except Exception as e:
        logger.error(f"导出格式文件失败: {e}")
    return deduped


# ====================== 全量爬取 ======================

def get_article_links(max_pages: int, delay: float) -> List[str]:
    """从列表页提取文章链接，直到遇到 STOP_URL 或爬完 max_pages 页。"""
    links: List[str] = []
    logger.info(f"开始抓取 {max_pages} 页列表...")
    for page in range(1, max_pages + 1):
        url = INDEX_BASE.format(page)
        logger.info(f"抓取列表页: {url}")
        try:
            resp = session.get(url, timeout=15)
            resp.raise_for_status()
            resp.encoding = "utf-8"
            html = etree.HTML(resp.text)
            hrefs = html.xpath(
                '//div[contains(@class, "w1280") and contains(@class, "j-d2tuwen")]'
                '//div[contains(@class, "left") or contains(@class, "fl")]/div/h3/a/@href'
            ) or html.xpath("/html/body/div/div[6]/div[1]/div/h3/a/@href")
            for href in hrefs:
                full_url = urljoin(BASE_URL, href)
                if full_url == STOP_URL:
                    logger.info(f"到达停止 URL: {STOP_URL}")
                    return links
                links.append(full_url)
            time.sleep(delay)
        except Exception as e:
            logger.error(f"抓取列表页失败 {url}: {e}")
    logger.info(f"共获取 {len(links)} 个文章链接")
    return links


def crawl_articles(max_pages: int, delay: float) -> List[Tuple[str, str, dict]]:
    """爬取所有文章并提取句子对。"""
    article_links = get_article_links(max_pages, delay)
    all_pairs: List[Tuple[str, str, dict]] = []
    logger.info(f"开始爬取 {len(article_links)} 篇文章...")
    for i, url in enumerate(article_links, 1):
        logger.info(f"[{i}/{len(article_links)}] 处理: {url}")
        pairs = parse_article(url)
        if pairs:
            all_pairs.extend(pairs)
            logger.info(f"  累计 {len(all_pairs)} 对")
        else:
            logger.warning(f"  解析失败: {url}")
        time.sleep(delay)
    logger.info(f"爬取完成，共提取 {len(all_pairs)} 对句子")
    return all_pairs


def _parse_args():
    max_pages = 100
    delay = 1.0
    if len(sys.argv) > 1:
        try:
            max_pages = int(sys.argv[1])
        except ValueError:
            pass
    if len(sys.argv) > 2:
        try:
            delay = float(sys.argv[2])
        except ValueError:
            pass
    return max_pages, delay


def main():
    max_pages, delay = _parse_args()
    logger.info("人民网日文版双语爬虫启动（全量）")
    sentence_pairs = crawl_articles(max_pages, delay)
    if not sentence_pairs:
        logger.warning("未提取到任何句子对")
        return
    records = [
        {"zh": zh, "ja": ja, "source_url": props.get("source_url", ""), "title": props.get("title", "")}
        for zh, ja, props in sentence_pairs
    ]
    finalize_and_save(records)
    logger.info("所有文件生成完成")


if __name__ == "__main__":
    main()