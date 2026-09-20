# -*- coding: UTF-8 -*-
"""
人民网日文版「中国語教室」语料库多格式导出模块

从规范化的双语句对列表生成 6 种格式：
  - TMX    翻译记忆交换格式（翻译工具通用）
  - JSONL  每行一个 JSON 对象（流式/大模型友好）
  - JSON   完整数组（默认逗号分隔、无缩进压缩；可通过参数开启缩进）
  - TXT    人类可读文本（成对列出）
  - XML    结构化 XML（<corpus>/<sentence>/<chinese>…）
  - XLSX   Excel 表格（依赖可选的 pandas + openpyxl）

规范句对两种输入均可：
  1) 列表元素为 dict，含字段：zh, ja, source_url, title（id 可选，缺省自动生成）
  2) 列表元素为三元组 (zh, ja, props)

用法：
  作为模块调用：
      from export_formats import export_all
      export_all(corpus_list, output_dir="data/export", prefix="zh_ja_corpus")

  命令行（默认读取 data/corpus.json 生成到 data/export/）：
      python export_formats.py [corpus.json 路径] [输出目录]
"""

import os
import json
import sys
import logging
from datetime import datetime
from typing import List, Dict, Tuple, Union, Optional

import xml.sax.saxutils as saxutils

try:
    import pandas as pd
    PANDAS_AVAILABLE = True
except ImportError:  # pragma: no cover
    PANDAS_AVAILABLE = False

logger = logging.getLogger(__name__)

# 每个句子对内可导出的属性
_PROP_KEYS = ["source_url", "title"]


def normalize_pairs(items: List[Union[dict, Tuple]]) -> List[dict]:
    """把不同输入统一成 dict 列表，补全 id / zh / ja / source_url / title。"""
    out: List[dict] = []
    for i, item in enumerate(items, 1):
        if isinstance(item, dict):
            rec = dict(item)
            zh = str(rec.get("zh", "")).strip()
            ja = str(rec.get("ja", "")).strip()
            if zh and ja:
                rec["id"] = rec.get("id") or f"sent_{i:06d}"
                out.append(rec)
        else:
            zh, ja, props = item[0], item[1], (item[2] if len(item) > 2 else {})
            zh = str(zh).strip()
            ja = str(ja).strip()
            if zh and ja:
                rec = {"id": f"sent_{i:06d}", "zh": zh, "ja": ja}
                for k in _PROP_KEYS:
                    v = props.get(k) if isinstance(props, dict) else None
                    if v:
                        rec[k] = v
                out.append(rec)
    return out


def load_corpus(path: str) -> List[dict]:
    """从语料库 JSON 文件读取句对列表（兼容 dict 或三元组）。"""
    with open(path, "r", encoding="utf-8") as f:
        raw = json.load(f)
    return normalize_pairs(raw)


# ---------------------- 单格式写入 ----------------------

def write_tmx(items: List[dict], filepath: str, src="zh-CN", tgt="ja"):
    with open(filepath, "w", encoding="utf-8") as f:
        f.write('<?xml version="1.0" encoding="UTF-8"?>\n')
        f.write('<tmx version="1.4">\n')
        f.write("  <header\n")
        f.write('    creationtool="PeopleCN_Bilingual_Crawler"\n')
        f.write('    creationtoolversion="2.3"\n')
        f.write('    datatype="PlainText"\n')
        f.write('    segtype="sentence"\n')
        f.write('    adminlang="en-US"\n')
        f.write(f'    srclang="{src}"\n')
        f.write('    o-tmf="UTF-8"\n')
        f.write(f'    creationdate="{datetime.now().strftime("%Y%m%dT%H%M%SZ")}"\n')
        f.write("  />\n")
        f.write("  <body>\n")
        for i, rec in enumerate(items, 1):
            tuid = rec.get("id") or f"sent_{i:06d}"
            f.write(f'    <tu tuid="{tuid}" creationdate="{datetime.now().strftime("%Y%m%dT%H%M%SZ")}">\n')
            for k in _PROP_KEYS:
                if rec.get(k):
                    f.write(f'      <prop type="{k}">{saxutils.escape(str(rec[k]))}</prop>\n')
            f.write(f"      <tuv xml:lang=\"{src}\">\n")
            f.write(f"        <seg>{saxutils.escape(str(rec['zh']))}</seg>\n")
            f.write("      </tuv>\n")
            f.write(f"      <tuv xml:lang=\"{tgt}\">\n")
            f.write(f"        <seg>{saxutils.escape(str(rec['ja']))}</seg>\n")
            f.write("      </tuv>\n")
            f.write("    </tu>\n")
        f.write("  </body>\n")
        f.write("</tmx>\n")


def write_jsonl(items: List[dict], filepath: str):
    with open(filepath, "w", encoding="utf-8") as f:
        for rec in items:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")


def write_json(items: List[dict], filepath: str, indent: Optional[int] = 2):
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(items, f, ensure_ascii=False, indent=indent)


def write_txt(items: List[dict], filepath: str):
    with open(filepath, "w", encoding="utf-8") as f:
        f.write("人民网中日对译语料库\n")
        f.write("=" * 50 + "\n")
        f.write(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write("=" * 50 + "\n\n")
        for i, rec in enumerate(items, 1):
            f.write(f"[{i}]\n")
            f.write(f"中文: {rec['zh']}\n")
            f.write(f"日文: {rec['ja']}\n")
            f.write(f"来源: {rec.get('source_url', 'N/A')}\n")
            f.write(f"标题: {rec.get('title', 'N/A')}\n")
            f.write("-" * 30 + "\n")


def write_xml(items: List[dict], filepath: str):
    with open(filepath, "w", encoding="utf-8") as f:
        f.write('<?xml version="1.0" encoding="UTF-8"?>\n')
        f.write("<corpus>\n")
        f.write("  <metadata>\n")
        f.write(f"    <generated>{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</generated>\n")
        f.write(f"    <total_sentences>{len(items)}</total_sentences>\n")
        f.write("  </metadata>\n")
        for i, rec in enumerate(items, 1):
            f.write(f'  <sentence id="{rec.get("id") or f"sent_{i:06d}"}">\n')
            f.write(f"    <chinese>{saxutils.escape(str(rec['zh']))}</chinese>\n")
            f.write(f"    <japanese>{saxutils.escape(str(rec['ja']))}</japanese>\n")
            f.write(f"    <source_url>{saxutils.escape(str(rec.get('source_url', '')))}</source_url>\n")
            f.write(f"    <title>{saxutils.escape(str(rec.get('title', '')))}</title>\n")
            f.write("  </sentence>\n")
        f.write("</corpus>\n")


def write_xlsx(items: List[dict], filepath: str) -> bool:
    if not PANDAS_AVAILABLE:
        logger.warning("未安装 pandas/openpyxl，跳过 XLSX 生成")
        return False
    df = pd.DataFrame([{
        "ID": rec.get("id", f"sent_{i:06d}"),
        "中文": rec["zh"],
        "日文": rec["ja"],
        "来源URL": rec.get("source_url", ""),
        "文章标题": rec.get("title", ""),
    } for i, rec in enumerate(items, 1)])
    df.to_excel(filepath, index=False, engine="openpyxl")
    return True


# ---------------------- 导出入口 ----------------------

def export_all(items: List[Union[dict, Tuple]],
               output_dir: str,
               prefix: str = "zh_ja_corpus") -> Dict[str, str]:
    """把语料导出为 6 种格式到指定目录。返回 {格式: 文件路径}。"""
    os.makedirs(output_dir, exist_ok=True)
    data = normalize_pairs(items)
    paths = {
        "tmx": os.path.join(output_dir, f"{prefix}.tmx"),
        "jsonl": os.path.join(output_dir, f"{prefix}.jsonl"),
        "json": os.path.join(output_dir, f"{prefix}.json"),
        "txt": os.path.join(output_dir, f"{prefix}.txt"),
        "xml": os.path.join(output_dir, f"{prefix}.xml"),
        "xlsx": os.path.join(output_dir, f"{prefix}.xlsx"),
    }
    write_tmx(data, paths["tmx"])
    write_jsonl(data, paths["jsonl"])
    write_json(data, paths["json"])
    write_txt(data, paths["txt"])
    write_xml(data, paths["xml"])
    ok_xlsx = write_xlsx(data, paths["xlsx"])
    if not ok_xlsx:
        paths.pop("xlsx", None)
    logger.info(f"导出完成：{len(data)} 对句子 -> {output_dir}（{list(paths.keys())}）")
    return paths


def main():
    corpus_path = sys.argv[1] if len(sys.argv) > 1 else "data/corpus.json"
    output_dir = sys.argv[2] if len(sys.argv) > 2 else "data/export"
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    if not os.path.exists(corpus_path):
        print(f"错误：语料库文件不存在：{corpus_path}")
        print("请先用完整爬虫（people_cn_corpus_crawler_2000.py）生成 data/corpus.json，再运行本脚本导出格式。")
        return 1
    try:
        data = load_corpus(corpus_path)
    except Exception as e:
        print(f"错误：读取语料库失败：{e}")
        return 1
    if not data:
        print(f"错误：{corpus_path} 中没有可导出的句对")
        return 1
    export_all(data, output_dir)
    return 0


if __name__ == "__main__":
    sys.exit(main())