#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""单页替换：在用户已手工编辑的 pptx 上安全地换掉某一页。

核心保证：以源文件为底逐条复制，只替换目标页相关条目，
其余条目逐字节一致，并在替换后断言无悬空引用。

用法示例
--------
从新导出的包里取第 29 页（推荐）：
    python3 page_replace.py --src 交付版.pptx --page 29 \
        --export exports/new.pptx --out /tmp/out.pptx

手工指定页 XML 并补一张图：
    python3 page_replace.py --src 交付版.pptx --page 29 \
        --slide-xml /tmp/x/ppt/slides/slide29.xml \
        --rels /tmp/x/ppt/slides/_rels/slide29.xml.rels \
        --media /tmp/cm_work.jpg=ppt/media/image_abc.jpg --out /tmp/out.pptx
"""
import argparse
import hashlib
import os
import posixpath
import re
import shutil
import subprocess
import sys
import zipfile

# 暖调纸感项目色板：主题色 -> 实际色值
DEFAULT_THEME_MAP = {
    "lt1": "FAF6EE", "dk1": "1E3A38", "dk2": "5C716E", "lt2": "F2EDE0",
    "accent1": "2F8B84", "accent2": "F2C879", "accent3": "E8A84E",
    "accent4": "E6D8BF", "accent5": "4BACC6", "accent6": "F79646",
    "hlink": "F2C879", "folHlink": "E8A84E",
    "tx1": "1E3A38", "bg1": "FAF6EE", "tx2": "5C716E", "bg2": "F2EDE0",
}


# ---------------------------------------------------------------- 工具函数

def die(msg):
    print("!! " + msg, file=sys.stderr)
    sys.exit(1)


def page_order(z):
    """返回按显示顺序排列的 slide part 名列表。"""
    pr = z.read("ppt/presentation.xml").decode("utf-8")
    rels = z.read("ppt/_rels/presentation.xml.rels").decode("utf-8")
    m = dict(re.findall(r'Id="(rId\d+)"[^>]*?Target="([^"]+)"', rels))
    rids = re.findall(r'<p:sldId [^>]*?r:id="(rId\d+)"', pr)
    out = []
    for rid in rids:
        t = m.get(rid)
        if not t:
            die("presentation.xml.rels 缺少 %s" % rid)
        t = t.lstrip("/")
        out.append(t if t.startswith("ppt/") else "ppt/" + posixpath.normpath(t))
    return out


def rels_of(slide_part):
    d, f = posixpath.split(slide_part)
    return "%s/_rels/%s.rels" % (d, f)


def parse_rels(text):
    """返回 [(rId, type, target)]，target 已规范化为包内路径（外链保留原样）。"""
    out = []
    for tag in re.findall(r"<Relationship\b[^>]*/>", text):
        rid = re.search(r'Id="([^"]+)"', tag)
        typ = re.search(r'Type="([^"]+)"', tag)
        tgt = re.search(r'Target="([^"]+)"', tag)
        mode = re.search(r'TargetMode="(\w+)"', tag)
        if not (rid and tgt):
            continue
        out.append((rid.group(1), typ.group(1) if typ else "",
                    tgt.group(1), mode.group(1) if mode else "Internal"))
    return out


def theme_landing(xml, mapping):
    """把 <a:schemeClr val="lt1"/> 落成 <a:srgbClr val="FAF6EE"/>。"""
    unknown = set()

    def rep(m):
        v = m.group(1)
        if v not in mapping:
            unknown.add(v)
            return m.group(0)
        return '<a:srgbClr val="%s"' % mapping[v]

    out = re.sub(r'<a:schemeClr val="(\w+)"', rep, xml)
    out = out.replace("</a:schemeClr>", "</a:srgbClr>")
    return out, unknown


def strip_srcrect(xml):
    """删掉编译器自动加的裁剪值，否则图片只剩中间一条缝。"""
    return re.sub(r"<a:srcRect\b[^/]*/>", "", xml)


def ensure_content_type(ct_xml, part_name, content_type):
    """确保 [Content_Types].xml 登记了某 part。"""
    if 'PartName="%s"' % part_name in ct_xml:
        return ct_xml, False
    add = '<Override PartName="%s" ContentType="%s"/>' % (part_name, content_type)
    return ct_xml.replace("</Types>", add + "</Types>"), True


def ensure_default_ext(ct_xml, ext, content_type):
    if re.search(r'<Default Extension="%s"' % re.escape(ext), ct_xml, re.I):
        return ct_xml, False
    add = '<Default Extension="%s" ContentType="%s"/>' % (ext, content_type)
    return ct_xml.replace("</Types>", add + "</Types>"), True


MEDIA_TYPES = {
    "jpg": "image/jpeg", "jpeg": "image/jpeg", "png": "image/png",
    "gif": "image/gif", "bmp": "image/bmp", "tif": "image/tiff",
    "mp4": "video/mp4", "m4v": "video/mp4", "mov": "video/quicktime",
    "mp3": "audio/mpeg", "wav": "audio/wav", "m4a": "audio/mp4",
}


def force_layout(rels_text, layout_target):
    """把 rels 里所有 slideLayout 关系的 Target 换成本包的布局。

    新导出包的布局编号常与交付包不同（slideLayout7 vs slideLayout1），
    直接沿用会留下悬空引用，PowerPoint 打开就要求修复。
    """
    def rep(m):
        tag = m.group(0)
        if not tag.rstrip("/>").endswith('/slideLayout') and '/slideLayout"' not in tag:
            return tag
        return re.sub(r'Target="[^"]+"', 'Target="%s"' % layout_target, tag)

    return re.sub(r"<Relationship\b[^>]*/>", rep, rels_text)


def pick_layout(zf, names, old_rels_part, explicit=None):
    """决定新页该挂哪个布局：显式参数 > 老页的布局 > slideLayout1。"""
    if explicit:
        base = posixpath.basename(explicit)
        return "../slideLayouts/" + base
    if old_rels_part and old_rels_part in names:
        for rid, typ, tgt, mode in parse_rels(zf.read(old_rels_part).decode("utf-8")):
            if typ.endswith("/slideLayout"):
                return "../slideLayouts/" + posixpath.basename(tgt)
    return "../slideLayouts/slideLayout1.xml"


def check_dangling(zf, names):
    bad = []
    for n in names:
        if not n.endswith(".rels"):
            continue
        base = posixpath.dirname(posixpath.dirname(n))
        for tag in re.findall(r"<Relationship\b[^>]*/>", zf.read(n).decode("utf-8")):
            if 'TargetMode="External"' in tag:
                continue
            t = re.search(r'Target="([^"]+)"', tag)
            if not t:
                continue
            full = posixpath.normpath(posixpath.join(base, t.group(1)))
            if full not in names:
                bad.append((n, t.group(1)))
    return bad


# ---------------------------------------------------------------- 主流程

def main():
    ap = argparse.ArgumentParser(description="在已有 pptx 上安全替换一页")
    ap.add_argument("--src", required=True, help="源 pptx（用户当前在用的那版）")
    ap.add_argument("--out", required=True, help="输出 pptx")
    ap.add_argument("--page", type=int, help="目标显示页码，1 起")
    ap.add_argument("--export", help="新导出包；取其中同一显示页码的 slide 与 rels、媒体")
    ap.add_argument("--slide-xml", help="直接指定新页 XML")
    ap.add_argument("--rels", help="直接指定新页 rels")
    ap.add_argument("--media", action="append", default=[], help="src=dest，可重复")
    ap.add_argument("--drop", action="append", default=[], help="顺带从包内删除该条目")
    ap.add_argument("--layout", help="新 rels 指向的布局，默认沿用老页")
    ap.add_argument("--backup-dir", help="备份目录，默认 <src目录>/validation")
    ap.add_argument("--no-landing", action="store_true", help="跳过主题色落地")
    ap.add_argument("--strip-srcrect", action="store_true",
                    help="清除所有 srcRect（仅当图片被裁成一条缝时才用）")
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()

    if not os.path.isfile(a.src):
        die("源文件不存在: " + a.src)
    if not (a.page or a.slide_xml):
        die("需要 --page 或 --slide-xml")

    # 1) 占用检查
    try:
        r = subprocess.run(["lsof", a.src], capture_output=True, text=True)
        holders = [l for l in r.stdout.splitlines()[1:] if l.strip()]
        if holders:
            print("注意：文件正被以下进程打开，若在 PowerPoint 里请先关闭并保存")
            for h in holders[:5]:
                print("   ", h.split()[0])
            die("目标文件被占用，中止以免写回被覆盖")
    except FileNotFoundError:
        pass

    zin = zipfile.ZipFile(a.src)
    names = set(zin.namelist())
    order = page_order(zin)

    # 2) 定位目标页
    if a.page:
        if not (1 <= a.page <= len(order)):
            die("页码越界：共 %d 页" % len(order))
        target = order[a.page - 1]
    else:
        if a.slide_xml:
            # 由 slide 文件名反推包内路径
            base = os.path.basename(a.slide_xml.replace("\\", "/"))
            cand = "ppt/slides/" + base
            if cand not in names:
                die("包里找不到 %s" % cand)
            target = cand
        else:
            die("缺少定位信息")

    tgt_rels = rels_of(target)
    print("目标页：第 %s 页 -> %s" % (a.page or "?", target))

    # 老页的媒体概况，用于事后比对是否"丢内容"
    old_x = zin.read(target).decode("utf-8", "ignore") if target in names else ""
    old_stat = (old_x.count("<p:pic>"), old_x.count("videoFile"), old_x.count("<a:t>"))

    # 3) 取新页内容
    new_slide = None
    new_rels = a.rels and open(a.rels, "rb").read().decode("utf-8")
    media_from_export = {}

    if a.export:
        zex = zipfile.ZipFile(a.export)
        ex_order = page_order(zex)
        if a.page:
            if a.page > len(ex_order):
                die("导出包只有 %d 页" % len(ex_order))
            ex_part = ex_order[a.page - 1]
        else:
            base = os.path.basename(a.slide_xml.replace("\\", "/"))
            ex_part = "ppt/slides/" + base
        new_slide = zex.read(ex_part).decode("utf-8")
        ex_rels_part = rels_of(ex_part)
        if ex_rels_part in zex.namelist():
            ex_rels_text = zex.read(ex_rels_part).decode("utf-8")
            ex_base = posixpath.dirname(ex_part)
            for rid, typ, tgt, mode in parse_rels(ex_rels_text):
                if mode == "External":
                    continue
                full = posixpath.normpath(posixpath.join(ex_base, tgt))
                if full.startswith("ppt/media/"):
                    media_from_export[full] = zex.read(full)
            new_rels = ex_rels_text
        zex.close()
    elif a.slide_xml:
        new_slide = open(a.slide_xml, "rb").read().decode("utf-8")

    if new_slide is None:
        die("没有取到新页内容")

    # 4) 落地主题色（srcRect 默认保留：它是合法的裁剪参数）
    if not a.no_landing:
        new_slide, unknown = theme_landing(new_slide, DEFAULT_THEME_MAP)
        if unknown:
            print("警告：以下主题色未在映射表中，保持原样 ->", sorted(unknown))
    print("srcRect %d 处%s" % (
        new_slide.count("<a:srcRect"),
        "（已按 --strip-srcrect 清除）" if a.strip_srcrect else "（保留）"))
    if a.strip_srcrect:
        new_slide = strip_srcrect(new_slide)
    if "schemeClr" in new_slide:
        die("仍残留 schemeClr，请检查 --no-landing 或映射表")

    # 5) rels：没给就生成"仅 layout"的最小版（沿用老页布局）
    if new_rels is None:
        old_rels_path = tgt_rels if tgt_rels in names else None
        layout = a.layout
        if not layout and old_rels_path:
            for rid, typ, tgt, mode in parse_rels(zin.read(old_rels_path).decode("utf-8")):
                if typ.endswith("/slideLayout"):
                    layout = "slideLayouts/" + posixpath.basename(tgt)
                    break
        layout = layout or "slideLayouts/slideLayout1.xml"
        if not layout.startswith("slideLayouts/"):
            layout = "slideLayouts/" + posixpath.basename(layout)
        new_rels = (
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n'
            '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
            '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/'
            'relationships/slideLayout" Target="../%s"/></Relationships>' % layout
        )

    # 6) 布局对齐：新导出包的布局编号常与交付包不同，必须改成本包已有的
    layout_target = pick_layout(zin, names, tgt_rels if tgt_rels in names else None, a.layout)
    new_rels = force_layout(new_rels, layout_target)
    print("布局 ->", layout_target)

    # 7) 媒体收集：导出包里的 + --media 指定的
    drops = set()
    media_writes = {}   # 包内路径 -> bytes
    for part, data in media_from_export.items():
        media_writes[part] = data
    for spec in a.media:
        if "=" not in spec:
            die("--media 需要 src=dest 形式: " + spec)
        s, d = spec.split("=", 1)
        media_writes[d] = open(s, "rb").read()

    # 名字冲突且内容不同 -> 改名并重写 rels
    for part, data in list(media_writes.items()):
        if part in names:
            old = zin.read(part)
            if old != data:
                stem, ext = posixpath.splitext(part)
                h = hashlib.md5(data).hexdigest()[:8]
                newp = "%s_%s%s" % (stem, h, ext)
                print("媒体同名不同内容，改名 %s -> %s" % (posixpath.basename(part), posixpath.basename(newp)))
                new_rels = new_rels.replace(
                    posixpath.basename(part), posixpath.basename(newp))
                media_writes[newp] = media_writes.pop(part)
            else:
                media_writes.pop(part)
    for d in a.drop:
        drops.add(d)

    added_media = [p for p in media_writes if p not in names]
    repl_media = [p for p in media_writes if p in names]

    # 7) 打包
    backup = None
    if not a.dry_run:
        bdir = a.backup_dir or os.path.join(os.path.dirname(os.path.abspath(a.src)), "validation")
        os.makedirs(bdir, exist_ok=True)
        stamp = re.sub(r"[: ]", "", __import__("time").strftime("%Y-%m-%d %H:%M"))
        backup = os.path.join(bdir, "交付备份_%s_page%s前.pptx" % (stamp, a.page or "x"))
        shutil.copy2(a.src, backup)
        print("备份 ->", backup)

    tmp = a.out + ".part"
    same, repl, add, drop = 0, [], [], []
    ct_xml = zin.read("[Content_Types].xml").decode("utf-8")
    ct_changed = False

    # 补媒体扩展名声明
    for part in media_writes:
        ext = posixpath.splitext(part)[1].lstrip(".").lower()
        if ext in MEDIA_TYPES:
            ct_xml, ch = ensure_default_ext(ct_xml, ext, MEDIA_TYPES[ext])
            ct_changed |= ch

    with zipfile.ZipFile(a.src) as zi, zipfile.ZipFile(tmp, "w", zipfile.ZIP_DEFLATED) as zo:
        for it in zi.infolist():
            n = it.filename
            if n in drops:
                drop.append(n)
                continue
            if n == "[Content_Types].xml":
                zo.writestr(it, ct_xml.encode("utf-8"))
                if ct_changed:
                    repl.append(n)
                else:
                    same += 1
                continue
            if n == target:
                zo.writestr(it, new_slide.encode("utf-8"))
                repl.append(n)
                continue
            if n == tgt_rels:
                zo.writestr(it, new_rels.encode("utf-8"))
                repl.append(n)
                continue
            zo.writestr(it, zi.read(n))
            same += 1
        for part, data in media_writes.items():
            if part in names:
                continue
            zo.writestr(part, data)
            add.append(part)

    if a.dry_run:
        os.remove(tmp)
        print("[dry-run] 一致 %d | 替换 %s | 新增 %s | 删除 %s" % (same, repl, add, drop))
        return

    # 8) 校验
    zo = zipfile.ZipFile(tmp)
    n2 = set(zo.namelist())
    bad = check_dangling(zo, n2)
    diff = [n for n in (names & n2) if zin.read(n) != zo.read(n)]
    pr = zo.read("ppt/presentation.xml").decode("utf-8")
    npages = len(re.findall(r"<p:sldId ", pr))
    zo.close()
    zin.close()

    print("-" * 56)
    print("一致 %d | 替换 %d | 新增 %d | 删除 %d" % (same, len(repl), len(add), len(drop)))

    # 内容完整性：新页不该比老页少图、少视频、少文字
    new_stat = (new_slide.count("<p:pic>"), new_slide.count("videoFile"), new_slide.count("<a:t>"))
    labels = ("图片", "视频", "文本框")
    for lab, o, n in zip(labels, old_stat, new_stat):
        if n < o:
            print("警告：第 %s 页的%s数由 %d 降到 %d，请确认新页是否完整"
                  % (a.page or "?", lab, o, n))
            if lab == "视频":
                print("      ——含视频的页被换掉后视频会消失，必须确认新页 XML 里有 videoFile 节点")
    if add:
        print("新增:", [posixpath.basename(p) for p in add])
    if drop:
        print("删除:", [posixpath.basename(p) for p in drop])
    if diff:
        print("字节差异:", [posixpath.basename(p) for p in diff])
    print("悬空 Target:", bad)
    print("slides:", npages)

    fatal = False
    if bad:
        print("!! 存在悬空引用，开放会要求修复")
        fatal = True
    unexpected = [d for d in diff if d not in repl]
    if unexpected:
        print("!! 出现计划外的条目变化:", unexpected)
        fatal = True
    try:
        from pptx import Presentation
        n = len(Presentation(tmp).slides)
        print("python-pptx 打开正常，页数", n)
        if n != npages:
            print("!! python-pptx 页数与 sldIdLst 不一致")
            fatal = True
    except Exception as e:
        print("!! python-pptx 打开失败:", e)
        fatal = True

    if fatal:
        os.remove(tmp)
        die("校验未通过，已放弃写回（备份保留在 %s）" % backup)

    # 9) 原子写回
    shutil.copy2(tmp, a.out)
    os.remove(tmp)
    print("已写出 %s (%.2f MB)" % (a.out, os.path.getsize(a.out) / 1048576))


if __name__ == "__main__":
    main()
