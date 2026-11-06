#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""用 Chrome headless 把 SVG 渲染成 PNG，供自检。

    python3 render_svg.py 目标.svg [输出.png] [--width 1280] [--height 720]
"""
import argparse
import os
import subprocess
import sys

CHROME_CANDIDATES = [
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
    "/Applications/Chromium.app/Contents/MacOS/Chromium",
    "/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge",
]


def find_chrome():
    for p in CHROME_CANDIDATES:
        if os.path.exists(p):
            return p
    for name in ("google-chrome", "chromium", "chromium-browser"):
        from shutil import which
        p = which(name)
        if p:
            return p
    return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("svg")
    ap.add_argument("png", nargs="?")
    ap.add_argument("--width", default="1280")
    ap.add_argument("--height", default="720")
    a = ap.parse_args()

    svg = os.path.abspath(a.svg)
    if not os.path.isfile(svg):
        sys.exit("找不到 " + svg)
    png = a.png or (os.path.splitext(svg)[0] + ".png")

    chrome = find_chrome()
    if not chrome:
        sys.exit("未找到 Chrome / Chromium / Edge")

    # 必须先删：Chrome 偶尔静默失败，旧图会冒充新图
    if os.path.exists(png):
        os.remove(png)

    cmd = [
        chrome, "--headless=new", "--no-sandbox", "--disable-gpu",
        "--hide-scrollbars", "--allow-file-access-from-files",
        "--force-device-scale-factor=1",
        "--window-size=%s,%s" % (a.width, a.height),
        "--screenshot=" + png, "file://" + svg,
    ]
    subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=120)

    if not os.path.exists(png):
        # 重试一次
        subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=120)
    if not os.path.exists(png):
        sys.exit("渲染失败，请检查 SVG 是否合法或减少渐变/path 复杂度")

    print("%s  (%.0f KB)" % (png, os.path.getsize(png) / 1024))


if __name__ == "__main__":
    main()
