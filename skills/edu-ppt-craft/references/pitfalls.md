# 六个坑（都真实踩过，按疼的程度排序）

## 1. 主题色未落地 → 网页预览显示白底

**症状**：新编译的页面在 PowerPoint 里颜色正常，但在网页预览器里背景变成**纯白**，和旁边页面明显不同。用户会说"你背景颜色都不对，我的明明是米色"。

**根因**：新版本编译器把 SVG 里的 `#FAF6EE` 写成 `<a:schemeClr val="lt1"/>`（引用主题），老页面是写死 `<a:srgbClr val="FAF6EE"/>`。PowerPoint 解析主题所以看不出差别，网页预览器不解析主题 → 落到默认白色。

**修法**：替换前把所有 `schemeClr` 映射为实际色值。

```python
MAP = {'lt1':'FAF6EE','dk1':'1E3A38','dk2':'5C716E','lt2':'F2EDE0',
       'accent1':'2F8B84','accent2':'F2C879','accent3':'E8A84E','accent4':'E6D8BF',
       'accent5':'4BACC6','accent6':'F79646','hlink':'F2C879','folHlink':'E8A84E',
       'tx1':'1E3A38','bg1':'FAF6EE','tx2':'5C716E','bg2':'F2EDE0'}
x = re.sub(r'<a:schemeClr val="(\w+)"', lambda m: '<a:srgbClr val="%s"' % MAP[m.group(1)], x)
x = x.replace('</a:schemeClr>', '</a:srgbClr>')
assert 'schemeClr' not in x
```

`page_replace.py` 已自动做这一步。**每页替换后都要断言 `schemeClr` 计数为 0。**

---

## 2. `srcRect`：多数时候合法，别乱删

**先纠正一个常见误解**：`<a:srcRect l="0" t="14184" r="0" b="14184"/>` 不是 bug。它的单位是**千分之一百分比**，14184 = 14.18%，是编译器为了让图片按 `preserveAspectRatio="slice"` 填满框而算出的合法裁剪。**正常页面里应当保留。**

**真正的 bug 形态**：某个 srcRect 的值明显不合比例——负数、单边 ≥ 100000（超过 100%）、或左右（上下）合计 ≥ 80000。这时图片会被裁成一条缝。

```python
for tag in re.findall(r"<a:srcRect[^/]*/>", x):
    v = {k: int(n) for k, n in re.findall(r'([lrtb])="(-?\d+)"', tag)}
    lr = v.get("l", 0) + v.get("r", 0)
    tb = v.get("t", 0) + v.get("b", 0)
    if min(v.values(), default=0) < 0 or lr >= 80000 or tb >= 80000:
        print("可疑:", tag)
```

**怎么判断**：先看渲染出来的 PNG。图片完整 → srcRect 正常，不要动；只剩一条缝 → 用 `--strip-srcrect` 清掉那一页的全部裁剪，重新编译时把图片按框的比例做好（`media.md` 里有尺寸建议）。

`page_replace.py` 默认**保留** srcRect，只有显式 `--strip-srcrect` 才清。`pptx_inspect.py --verify` 会自动挑出异常值。


---

## 3. 删页/加页要改三个文件，正则要用 `[^>]*`

**症状**：删了页，PowerPoint 打开提示"发现内容有问题，需要修复"；或者页数不对、出现空白页。

**根因**：`sldIdLst` 只决定显示顺序，`[Content_Types].xml` 决定文件是否登记，`presentation.xml.rels` 决定关系是否有效。漏改任一个就出悬空引用。

**修法**：三者同步（详见 `page-replace.md`）。两个细节：

- **不要重命名 slide 文件**，也不要把其他页往前挪。PowerPoint 按 `sldIdLst` 显示，文件名是内部编号，乱动只会破坏关系。
- `[Content_Types].xml` 的 `ContentType` 属性值里含 `/`，用 `<Override[^/]*/>` 这类正则匹配会静默失败、留下悬空 Override。**必须用 `<Override[^>]*/>`**。

---

## 4. 含视频的页被清空，媒体会被连带删除

**症状**：用户说"我第 28、29 页怎么不见了"。检查发现页还在，但 `slide28.xml` 只有 457 字节、空 `spTree`；两页引用的视频、封面图、配图全从 `ppt/media/` 消失了。后续页文件名整体前移一位。

**根因**：这两页被"重置或删除内容后又插入空白页"，PowerPoint 保存时顺带清理了不再被引用的媒体。

**修法**：从最近的干净交付版里取回**页 XML + rels + 全部媒体**，以用户当前文件为底只替换这几条。

```bash
# 恢复时必须连媒体一起补
--slide-xml 旧包/ppt/slides/slide32.xml
--rels      旧包/ppt/slides/_rels/slide32.xml.rels
--media     旧包/ppt/media/media2.mp4=ppt/media/media2.mp4
--media     旧包/ppt/media/image_t27v.jpeg=ppt/media/image_t27v.jpeg
```

**预防**：每轮交付完成后把当轮的干净整包另存一份到 `validation/完整交付版_xxx.pptx`，作为恢复源。有这个文件，恢复是几分钟的事；没有就得从头重做那两页。

---

## 5. 不要替用户编数据

**症状**：用户在评审时指出"那个备课时间缩短不要直接写个 40 分钟，我可没说这个"。

**根因**：为了让"成效"更有说服力，自动补了一个听起来合理的数字。这类数字一旦被问到出处，讲者当场下不来台。

**铁律**：**成效页里每一个数字都必须能在用户给的材料里找到出处**（论文、课件、用户口述）。找不到就改成定性表述——"比过去省了一大截"、"做起来快得多"。宁可说服力弱一点，也不能编。

同理适用于：学生人数、课时数、提升百分比、获奖等级。

---

## 6. 改版不要自创视觉元素

**症状**：用户要求"这页不要图片"，改完被告知"你背景颜色都不对""29 页要维持和 28 页差不多的样式呀，只不过没有图片而已"。

**根因**：把"去掉图片"理解成了"重新设计这一页"——顺手把圆点列表改成圆角卡片、圆点从墨绿换成陶土色、还加了标题右侧的点线装饰。

**铁律**：**用户说的"改一点点"，就只改那一点点。** 同组页面的骨架（底色、边框、角刻线、书签条、波浪、页码、字号、圆点颜色）一律不动。要调整只调位置，不加新元素、不换色、不改字号。

判断标准：改完之后，把这一页和相邻页并排放，**除了用户要求变化的那一处，其余应当看不出差别**。

---

## 附：还有三个小坑

- **页码是多个 run**：结语页的"30"被拆成 `3` + `0` 两个 run，按全文替换单个数字会改错。按 `name="TextBox NN"` 定位整块再改。
- **`data-pptx-bounds` 漏写**：编译后文本组在 PowerPoint 里选不中、改不了字。每个 `<g>` 内容组都要写。
- **Chrome 渲染静默失败**：`--screenshot` 有时不写文件也不报错，旧 PNG 留在原处，让你误判"渲染成功"。渲染前先 `rm -f`。
