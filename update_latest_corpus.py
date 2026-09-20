# -*- coding: UTF-8 -*-
"""
人民网日文版「中国語教室」栏目 中日对译语料 · 增量更新脚本

复用全量爬虫 people_cn_corpus_crawler_2000.py 的解析 / 分页 / 统计 / 格式导出能力。
流程：抓取首页最新文章 -> 解析新文章直到命中语料库已有首篇 -> 合并去重
      -> 写 corpus.json -> 重新分页 + 统计 -> 重新导出全部格式。

用法：python update_latest_corpus.py
"""
import sys
import json
import time
import logging
from pathlib import Path
from urllib.parse import urljoin

from lxml import etree

# 保证同目录模块可导入
sys.path.insert(0, str(Path(__file__).parent))

from people_cn_corpus_crawler_2000 import (
    parse_article,
    session,
    BASE_URL,
    INDEX_URL,
    CORPUS_FILE,
    finalize_and_save,
    compute_stats,
)

DELAY = 1.0

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler()],
)
logger = logging.getLogger(__name__)


def load_corpus(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def get_latest_article_links():
    """抓取首页，返回最新文章链接列表。"""
    logger.info(f"抓取首页: {INDEX_URL}")
    try:
        resp = session.get(INDEX_URL, timeout=15)
        resp.raise_for_status()
        resp.encoding = "utf-8"
        html = etree.HTML(resp.text)
        hrefs = html.xpath(
            '//div[contains(@class, "w1280") and contains(@class, "j-d2tuwen")]'
            '//div[contains(@class, "left") or contains(@class, "fl")]/div/h3/a/@href'
        ) or html.xpath("/html/body/div/div[6]/div[1]/div/h3/a/@href")
        return [urljoin(BASE_URL, href) for href in hrefs]
    except Exception as e:
        logger.error(f"抓取首页失败: {e}")
        return []


def update_all():
    print("=" * 50)
    print("  人民网中日对译语料库 - 增量更新")
    print("=" * 50)

    if not Path(CORPUS_FILE).exists():
        logger.error("语料库不存在，请先运行全量爬虫 people_cn_corpus_crawler_2000.py")
        return False

    existing = load_corpus(CORPUS_FILE)
    first_url = existing[0].get("source_url") if existing else None
    if not first_url:
        logger.error("语料库异常：缺少 source_url，无法定位增量起点")
        return False

    latest_links = get_latest_article_links()
    if not latest_links:
        logger.warning("首页未获取到文章链接")
        return False

    new_records = []
    stopped = False
    logger.info(f"开始解析 {len(latest_links)} 篇最新文章，直到命中已有首篇为止...")
    for i, url in enumerate(latest_links, 1):
        if url == first_url:
            logger.info(f"命中已有首篇，停止: {url}")
            stopped = True
            break
        logger.info(f"[{i}/{len(latest_links)}] {url}")
        for zh, ja, props in parse_article(url):
            new_records.append({
                "zh": zh,
                "ja": ja,
                "source_url": props.get("source_url", ""),
                "title": props.get("title", ""),
            })
        time.sleep(DELAY)

    if not stopped:
        logger.warning("未命中已有首篇，本次新增可能不完整，请检查首页结构")

    if not new_records:
        logger.info("语料库已是最新，无需更新")
        return False

    # 合并：新文章在前，旧语料在后（finalize_and_save 内部去重 + 重新编号）
    updated = new_records + [dict(rec) for rec in existing]
    logger.info(f"合并完成：新增 {len(new_records)} 对 + 原有 {len(existing)} 对")
    records = finalize_and_save(updated)

    stats = compute_stats(records)
    print("\n" + "=" * 50)
    print("  增量更新完成")
    print("=" * 50)
    print(f"  新增句对（去重后并入总数）：{len(records)} 对")
    print(f"  总语句数：{stats['total_sentences']}")
    print(f"  来源文章数：{stats['unique_sources']}")
    print(f"  不同标题数：{stats['unique_titles']}")
    print("=" * 50)
    return True


def main():
    update_all()


if __name__ == "__main__":
    main()