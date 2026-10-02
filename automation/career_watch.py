#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
career_watch.py —— 高校就业网宣讲会/招聘会/招聘公告监控（config 驱动，仅用标准库）

用法：
    python career_watch.py                  # 默认读同目录 config.json
    python career_watch.py config.xxx.json  # 指定配置
    python career_watch.py --check          # 只抓取并打印 JSON（调试选择器用，不写文件）

适配其他学校：见同目录《适配其他学校.md》。
输出：config.output_md 指向的 Markdown（默认 ../applications/宣讲会监控-latest.md），
      原始 JSON 快照写入 capture_dir。
"""

import json
import re
import sys
import gzip
import os
import html
import time
from urllib.parse import urljoin
import urllib.request
from datetime import datetime, timedelta

HERE = os.path.dirname(os.path.abspath(__file__))
DATE_RE = re.compile(r"(20\d{2})[-/](\d{1,2})[-/](\d{1,2})")


def load_config(path):
    with open(path, "r", encoding="utf-8") as f:
        raw = json.load(f)
    cfg = {k: v for k, v in raw.items() if not k.startswith("_")}
    if not cfg.get("base_url", "").startswith(("https://", "http://")) or not cfg.get("list_pages"):
        raise ValueError("配置需要有效 base_url 和至少一个 list_pages 条目")
    for key in ("max_pages", "days", "future_days"):
        if key in cfg and (type(cfg[key]) is not int or cfg[key] < (1 if key == "max_pages" else 0)):
            raise ValueError("无效的窗口/页数配置：" + key)
    if not isinstance(cfg.get("request_interval", 1), (int, float)) or cfg.get("request_interval", 1) < 0:
        raise ValueError("request_interval 必须非负")
    keys = set()
    for page in cfg["list_pages"]:
        for key in ("name", "key", "path", "block_pattern", "link_pattern"):
            if not page.get(key):
                raise ValueError("列表配置缺少 " + key)
        re.compile(page["block_pattern"])
        re.compile(page["link_pattern"])
        if page["key"] in keys:
            raise ValueError("列表 key 重复")
        keys.add(page["key"])
        for key in ("max_pages", "max_items"):
            if key in page and (type(page[key]) is not int or page[key] < 1):
                raise ValueError("列表页数/展示上限必须是正整数")
        if page.get("date_mode", "publish") not in {"event", "publish"}:
            raise ValueError("date_mode 必须为 event/publish")
        if page.get("empty_pattern"):
            re.compile(page["empty_pattern"])
    return cfg


def resolve_path(cfg_path, p):
    if os.path.isabs(p):
        return p
    return os.path.normpath(os.path.join(os.path.dirname(cfg_path), p))


def http_get(url, cfg):
    http_cfg = cfg.get("http", {})
    headers = {
        "User-Agent": http_cfg.get(
            "user_agent",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
        ),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "zh-CN,zh;q=0.9",
        "Referer": http_cfg.get("referer", cfg.get("base_url", "")),
        "Accept-Encoding": "gzip",
    }
    req = urllib.request.Request(url, headers=headers)
    timeout = http_cfg.get("timeout", 20)
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        data = resp.read()
        if resp.headers.get("Content-Encoding") == "gzip":
            data = gzip.decompress(data)
    for enc in ("utf-8", "gbk", "gb2312"):
        try:
            return data.decode(enc)
        except UnicodeDecodeError:
            continue
    return data.decode("utf-8", errors="replace")


def strip_tags(s):
    return html.unescape(re.sub(r"<[^>]+>", "", s))


def parse_blocks(page_html, block_pattern):
    """按 <ul class="infoList ...">...</ul> 之类的块切分列表页。"""
    return re.findall(block_pattern, page_html, re.S | re.I)


def parse_block(block, page_cfg):
    """从一个条目块提取 id/title/url/date/extra。"""
    link_re = re.compile(page_cfg["link_pattern"], re.I)
    m = link_re.search(block)
    if not m:
        return None
    item_id = m.group(1) if m.groups() else m.group(0)
    href = m.group(0)
    # 标题：优先 title 属性，其次锚文本
    tm = re.search(r"title=[\"']([^\"']+)[\"']", block)
    if tm:
        title = html.unescape(tm.group(1)).strip()
    else:
        am = re.search(r">(.*?)</a>", block, re.S)
        title = re.sub(r"\s+", " ", strip_tags(am.group(1))).strip() if am else ""
    title = re.sub(r"^(【置顶】|\s)+", "", title).strip()
    if not title:
        return None
    dm = DATE_RE.search(block)
    date_str = f"{dm.group(1)}-{int(dm.group(2)):02d}-{int(dm.group(3)):02d}" if dm else None
    extra = {}
    for field, pat in page_cfg.get("extra_patterns", {}).items():
        fm = re.search(pat, block, re.S)
        if fm:
            extra[field] = re.sub(r"\s+", " ", strip_tags(fm.group(1))).strip()
    return {"id": item_id, "title": title, "href": href, "date": date_str, "extra": extra}


def title_matches(title, cfg):
    for kw in cfg.get("exclude", []):
        if kw and kw in title:
            return False, f"排除词「{kw}」"
    for kw in cfg.get("keywords", []):
        if kw and kw in title:
            return True, f"关键词「{kw}」"
    for name, reason in cfg.get("whitelist", {}).items():
        if name and name in title:
            return True, f"白名单 {name}（{reason}）"
    return False, ""


def in_window(date_str, mode, cfg):
    """event 模式：未来 future_days 天 + 过去 1 天；publish 模式：过去 days 天。"""
    if not date_str:
        return False
    try:
        d = datetime.strptime(date_str, "%Y-%m-%d")
    except ValueError:
        return False
    today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    if mode == "event":
        return today - timedelta(days=1) <= d <= today + timedelta(days=cfg.get("future_days", 7))
    return today - timedelta(days=cfg.get("days", 3)) <= d <= today


def fetch_list(page_cfg, cfg):
    """读取有界列表；空页需明确标记，分页或覆盖异常显式返回。"""
    base = cfg["base_url"].rstrip("/")
    items, seen = [], set()
    max_pages = page_cfg.get("max_pages", cfg.get("max_pages", 5))
    previous_blocks = None
    coverage_error = None
    for page_no in range(1, max_pages + 1):
        path = page_cfg["path"] if page_no == 1 else page_cfg.get("page_path", page_cfg["path"] + "?page={n}").format(n=page_no)
        if page_no > 1:
            time.sleep(cfg.get("request_interval", 1))
        try:
            page_html = http_get(urljoin(base + "/", path), cfg)
        except Exception as e:  # noqa: BLE001
            return items, f"第 {page_no} 页抓取失败（{type(e).__name__}）；检查网络与官方入口"
        blocks = parse_blocks(page_html, page_cfg["block_pattern"])
        if not blocks:
            empty_pattern = page_cfg.get("empty_pattern")
            if empty_pattern and re.search(empty_pattern, page_html, re.I):
                break
            return items, f"第 {page_no} 页未识别到条目：可能页面结构变化、登录页或访问受限；不能认定无招聘"
        if blocks == previous_blocks:
            return items, f"第 {page_no} 页与上一页相同：分页可能失效，结果不完整"
        previous_blocks = blocks
        parsed_count = 0
        dated_count = 0
        for block in blocks:
            it = parse_block(block, page_cfg)
            if not it:
                coverage_error = "部分条目链接或标题未识别，结果不完整"
                continue
            parsed_count += 1
            it["url"] = urljoin(urljoin(base + "/", path), it["href"])
            try:
                datetime.strptime(it["date"] or "", "%Y-%m-%d")
                dated_count += 1
            except ValueError:
                coverage_error = "部分条目日期无效，结果不完整"
                continue
            if it["id"] in seen:
                continue
            seen.add(it["id"])
            mode = page_cfg.get("date_mode", "publish")
            if not in_window(it["date"], mode, cfg):
                continue
            if page_cfg.get("filter_by_keywords", False):
                ok, reason = title_matches(it["title"], cfg)
                if not ok:
                    continue
                it["reason"] = reason
            items.append(it)
        if not parsed_count or not dated_count:
            return items, f"第 {page_no} 页链接或日期未识别，结果不完整"
        # 列表可能含置顶或按举办时间升序；不从最旧日期推断后续页无效。
        if page_no == max_pages:
            coverage_error = (coverage_error + "；" if coverage_error else "") + f"已达 max_pages={max_pages}；只覆盖已读取页面，不能保证窗口内完整"
    cap = page_cfg.get("max_items")
    if cap and len(items) > cap:
        coverage_error = (coverage_error + "；" if coverage_error else "") + f"展示上限 max_items={cap}，结果已截断"
    return (items[:cap] if cap else items), coverage_error


def run(cfg, cfg_path, check_only=False):
    sections, capture = [], {"generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "pages": {}}
    for page_cfg in cfg.get("list_pages", []):
        items, err = fetch_list(page_cfg, cfg)
        sections.append((page_cfg["name"], items, err, page_cfg))
        capture["pages"][page_cfg["key"]] = {"count": len(items), "error": err, "items": items}

    if check_only:
        print(json.dumps(capture, ensure_ascii=False, indent=2))
        return not any(section[2] for section in sections)

    cap_dir = resolve_path(cfg_path, cfg.get("capture_dir", "captures"))
    cap_file = os.path.join(cap_dir, "career_watch_latest.json")
    previous = {}
    if os.path.exists(cap_file):
        try:
            with open(cap_file, encoding="utf-8") as f:
                previous = json.load(f).get("pages", {})
        except (ValueError, OSError):
            previous = {}
    for key, page in capture["pages"].items():
        prior = previous.get(key, {})
        old = prior.get("known_items", {it["url"]: it for it in prior.get("items", [])})
        page["new_urls"] = [it["url"] for it in page["items"] if it["url"] not in old]
        page["changed_urls"] = [it["url"] for it in page["items"] if it["url"] in old and it != old[it["url"]]]
        known = dict(old)
        known.update({it["url"]: it for it in page["items"]})
        # Keep a bounded local history so a failed run does not make everything new.
        page["known_items"] = dict(list(known.items())[-5000:])
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    lines = [
        f"# {cfg.get('school', '本校')}就业网监控（脚本自动生成）",
        "",
        f"> 生成时间：{now} ｜ 宣讲/招聘会窗口：未来 {cfg.get('future_days', 7)} 天 ｜ "
        f"公告窗口：最近 {cfg.get('days', 3)} 天 ｜ 命中逻辑：关键词/白名单 − 排除词",
        "> ⚠️ 本文件只提供候选，不改变投递状态；确认有价值后核实后更新唯一台账并生成视图。",
        "> 是否参加由用户结合目标和时间成本决定，参考 `../lessons/0002-宣讲会价值筛选.md`。",
        "",
    ]
    total = 0
    for name, items, err, page_cfg in sections:
        delta = capture["pages"][page_cfg["key"]]
        lines.append(f"## {name}（{len(items)}；较上次新增 {len(delta['new_urls'])} / 变化 {len(delta['changed_urls'])}）")
        if err:
            lines.append(f"- ⚠️ {err}")
        if not items and not err:
            lines.append("- （窗口内无命中）")
        if items:
            for it in items:
                hit = f"——{it['reason']}" if it.get("reason") else ""
                extra_str = "".join(f"｜{v}" for v in it.get("extra", {}).values() if v)
                lines.append(f"- [{it['date'] or '日期未识别'}] [{it['title']}]({it['url']}){extra_str} {hit}")
                total += 1
        lines.append("")
    lines += [
        "---",
        "合并规则：核实岗位、现场环节和信息价值，再按用户意愿加入主日程；扫描不替用户决定参加。",
    ]

    out_path = resolve_path(cfg_path, cfg.get("output_md", "../applications/宣讲会监控-latest.md"))
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    cap_dir = resolve_path(cfg_path, cfg.get("capture_dir", "captures"))
    os.makedirs(cap_dir, exist_ok=True)
    cap_file = os.path.join(cap_dir, "career_watch_latest.json")
    with open(cap_file, "w", encoding="utf-8") as f:
        json.dump(capture, f, ensure_ascii=False, indent=2)

    complete = not any(section[2] for section in sections)
    print(f"[{'OK' if complete else 'PARTIAL'}] 命中 {total} 条 → {out_path}")
    print(f"快照 → {cap_file}")
    return complete


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    check_only = "--check" in sys.argv
    cfg_path = os.path.abspath(args[0]) if args else os.path.join(HERE, "config.json")
    if not os.path.exists(cfg_path):
        example = os.path.join(HERE, "config.example.json")
        print(f"找不到配置 {cfg_path}。")
        if os.path.exists(example):
            print(f"请先复制示例配置：copy \"{example}\" \"{cfg_path}\"，再按本校情况修改。")
        sys.exit(1)
    try:
        complete = run(load_config(cfg_path), cfg_path, check_only=check_only)
    except (ValueError, OSError, KeyError, re.error) as exc:
        print(f"配置或输出失败：{exc}", file=sys.stderr)
        sys.exit(1)
    if not complete:
        sys.exit(2)


if __name__ == "__main__":
    main()
