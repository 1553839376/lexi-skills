#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""主题色落地：把 schemeClr 换成实际色值，避免网页预览显示白底。

    # 单个 XML 文件
    python3 theme_landing.py 页面.xml

    # 整个 pptx 的所有页（谨慎，会改动包里所有页）
    python3 theme_landing.py 演示.pptx

    # 只检查不修改
    python3 theme_landing.py 演示.pptx --check
"""
import argparse
import re
import shutil
import sys
import zipfile

MAP = {
    "lt1": "FAF6EE", "dk1": "1E3A38", "dk2": "5C716E", "lt2": "F2EDE0",
    "accent1": "2F8B84", "accent2": "F2C879", "accent3": "E8A84E",
    "accent4": "E6D8BF", "accent5": "4BACC6", "accent6": "F79646",
    "hlink": "F2C879", "folHlink": "E8A84E",
    "tx1": "1E3A38", "bg1": "FAF6EE", "tx2": "5C716E", "bg2": "F2EDE0",
}


def convert(xml):
    unknown = set()

    def rep(m):
        v = m.group(1)
        if v not in MAP:
            unknown.add(v)
            return m.group(0)
        return '<a:srgbClr val="%s"' % MAP[v]

    out = re.sub(r'<a:schemeClr val="(\w+)"', rep, xml)
    out = out.replace("</a:schemeClr>", "</a:srgbClr>")
    return out, unknown


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("path")
    ap.add_argument("--check", action="store_true")
    a = ap.parse_args()

    if a.path.lower().endswith(".xml"):
        src = open(a.path, encoding="utf-8").read()
        n = src.count("<a:schemeClr")
        if a.check:
            print("%s: schemeClr %d 处" % (a.path, n))
            return
        out, unknown = convert(src)
        open(a.path, "w", encoding="utf-8").write(out)
        print("%s: 替换 %d 处%s" % (
            a.path, n, ("，未识别 " + str(sorted(unknown))) if unknown else ""))
        return

    z = zipfile.ZipFile(a.path)
    slides = [n for n in z.namelist() if re.match(r"ppt/slides/slide\d+\.xml$", n)]
    hits = {}
    for n in slides:
        c = z.read(n).decode("utf-8", "ignore").count("<a:schemeClr")
        if c:
            hits[n] = c
    print("共 %d 页，含 schemeClr 的 %d 页" % (len(slides), len(hits)))
    for n, c in sorted(hits.items()):
        print("   %-24s %d 处" % (n.split("/")[-1], c))
    if a.check or not hits:
        return

    if input("确认把全部页的 schemeClr 落地为 srgbClr？(yes/no) ").strip().lower() != "yes":
        print("已取消")
        return

    tmp = a.path + ".landing"
    with zipfile.ZipFile(a.path) as zi, zipfile.ZipFile(tmp, "w", zipfile.ZIP_DEFLATED) as zo:
        for it in zi.infolist():
            data = zi.read(it.filename)
            if it.filename in hits:
                out, _ = convert(data.decode("utf-8"))
                data = out.encode("utf-8")
            zo.writestr(it, data)
    shutil.move(tmp, a.path)
    print("完成，已写回", a.path)


if __name__ == "__main__":
    main()
