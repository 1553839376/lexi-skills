#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""pptx 体检：列出真实页序、核对引用完整性。

    python3 pptx_inspect.py 文件.pptx --list     # 页序 + 每页文本摘要
    python3 pptx_inspect.py 文件.pptx --verify   # 悬空引用 / 主题色 / 图片数 / 页数
"""
import argparse
import posixpath
import re
import sys
import zipfile


def page_order(z):
    pr = z.read("ppt/presentation.xml").decode("utf-8")
    rels = z.read("ppt/_rels/presentation.xml.rels").decode("utf-8")
    m = dict(re.findall(r'Id="(rId\d+)"[^>]*?Target="([^"]+)"', rels))
    out = []
    for rid in re.findall(r'<p:sldId [^>]*?r:id="(rId\d+)"', pr):
        t = m.get(rid, "")
        t = t.lstrip("/")
        out.append(t if t.startswith("ppt/") else "ppt/" + posixpath.normpath(t))
    return out


def slide_text(x):
    parts = re.findall(r"<a:t>(.*?)</a:t>", x, re.S)
    return " / ".join(s.strip() for s in parts if s.strip())[:90]


def dangling(z, names):
    bad = []
    for n in names:
        if not n.endswith(".rels"):
            continue
        base = posixpath.dirname(posixpath.dirname(n))
        for tag in re.findall(r"<Relationship\b[^>]*/>", z.read(n).decode("utf-8")):
            if 'TargetMode="External"' in tag:
                continue
            t = re.search(r'Target="([^"]+)"', tag)
            if not t:
                continue
            full = posixpath.normpath(posixpath.join(base, t.group(1)))
            if full not in names:
                bad.append((n, t.group(1)))
    return bad


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("pptx")
    ap.add_argument("--list", action="store_true")
    ap.add_argument("--verify", action="store_true")
    a = ap.parse_args()
    if not (a.list or a.verify):
        a.verify = True

    z = zipfile.ZipFile(a.pptx)
    names = set(z.namelist())
    order = page_order(z)

    if a.list:
        print("共 %d 页，%d 个包内条目" % (len(order), len(names)))
        for i, part in enumerate(order, 1):
            if part not in names:
                print("%3d  %-18s !! 文件缺失" % (i, posixpath.basename(part)))
                continue
            x = z.read(part).decode("utf-8", "ignore")
            print("%3d  %-18s pic=%-2d %s" % (
                i, posixpath.basename(part), x.count("<p:pic>"), slide_text(x)))

    if a.verify:
        print("\n--- 体检 ---")
        bad = dangling(z, names)
        print("悬空 Target:", bad if bad else "无")
        print("页数(sldIdLst):", len(order))

        medias = [n for n in names if n.startswith("ppt/media/")]
        total = sum(z.getinfo(n).file_size for n in medias)
        print("媒体 %d 个 / %.2f MB" % (len(medias), total / 1048576))

        probs = []
        for i, part in enumerate(order, 1):
            if part not in names:
                probs.append((i, "文件缺失"))
                continue
            x = z.read(part).decode("utf-8", "ignore")
            if "schemeClr" in x:
                probs.append((i, "含 %d 处 schemeClr（网页预览会偏色）" % x.count("<a:schemeClr")))
            bad_crop = []
            for tag in re.findall(r"<a:srcRect[^/]*/>", x):
                v = {k: int(n) for k, n in re.findall(r'([lrtb])="(-?\d+)"', tag)}
                lr = v.get("l", 0) + v.get("r", 0)
                tb = v.get("t", 0) + v.get("b", 0)
                if lr >= 80000 or tb >= 80000 or max(abs(v) for v in v.values()) >= 100000:
                    bad_crop.append(tag)
            if bad_crop:
                probs.append((i, "srcRect 异常（图片可能被裁成一条缝）：%s" % bad_crop[0]))
        if probs:
            print("问题页：")
            for i, m in probs:
                print("  第 %d 页: %s" % (i, m))
        else:
            print("问题页：无")

        try:
            from pptx import Presentation
            print("python-pptx 打开正常，页数", len(Presentation(a.pptx).slides))
        except Exception as e:
            print("python-pptx 打开失败:", e)
            return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
