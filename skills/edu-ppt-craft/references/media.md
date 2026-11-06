# 素材获取：从课件与视频里取图

教育类 PPT 的图不该在网上搜——风格杂、有水印、和学生实际用的课件对不上。正确来源只有两个：**用户自己的课件** 和 **用户自己的课堂录像**。

## 一、从希沃课件解包（.enbx / .nbx）

希沃课件本质是 zip：

```bash
cd /tmp && rm -rf enbx && mkdir enbx && cd enbx
unzip -o -q "/path/课件.enbx"
find . -type f \( -name "*.png" -o -name "*.jpg" -o -name "*.jpeg" \) | head -50
```

图片通常按页序散落在若干目录，命名是哈希值。**取完图必须立刻登记来源**，否则第二天就分不清哪张是哪页：

```json
// images/image_sources.json
[
  {"file": "scene_sofa.jpg", "from": "《我是小主人》课件 p12", "use": "第20页 审核页大图"},
  {"file": "char_bear.png", "from": "《我是小主人》课件 p3", "use": "第13页 角色卡"}
]
```

筛选原则：

1. 优先取**角色立绘**和**完整场景**，这两类最能撑起版面。
2. 分辨率低于 600px 宽的不要（投影会糊）。
3. 带课件 UI 边框、带鼠标指针的截图不要。
4. 一张图只承担一个用途，不要一图多用（用户会发现"这图刚出现过"）。

## 二、从视频截帧

### 1. 找到 ffmpeg

系统装了 `imageio_ffmpeg` 就有现成的：

```bash
python3 -c "import imageio_ffmpeg;print(imageio_ffmpeg.get_ffmpeg_exe())"
# 形如 /Users/xxx/.workbuddy/binaries/python/versions/3.13.x/lib/python3.13/site-packages/imageio_ffmpeg/binaries/ffmpeg-macos-aarch64-v7.1
```

### 2. 先看时长，再决定抽样密度

```bash
"$FF" -hide_banner -i "$V" 2>&1 | grep -E "Duration|Stream" | head -5
```

### 3. 扫全片：拼网格一次看完

```bash
# 6 分钟的视频，每 5 秒一帧，6 列 8 行
"$FF" -hide_banner -loglevel error -i "$V" \
  -vf "fps=1/5,scale=320:180,tile=6x8:padding=4:color=white" \
  -frames:v 1 /tmp/scan/grid.png
```

30–45 分钟的长视频先粗扫：`fps=1/40` 加 `tile=6x10`。看网格图定位到目标区间，再细扫。

### 4. 细扫候选段

```bash
# 看 15–60 秒，每 3 秒一帧，5 列 3 行
"$FF" -hide_banner -loglevel error -ss 15 -t 45 -i "$V" \
  -vf "fps=1/3,scale=480:270,tile=5x3:padding=6:color=white" \
  -frames:v 1 /tmp/scan/seg1.png
```

### 5. 取单帧 + 去字幕 + 定尺寸

课堂录像底部通常有字幕，必须裁掉再入 PPT：

```bash
# 原片 1920×1080，字幕在下方 180px 内
# 先裁掉底部，再取中间 1600×900 保 16:9，最后缩到目标尺寸
"$FF" -hide_banner -loglevel error -ss 33 -i "$V" \
  -frames:v 1 -vf "crop=1600:900:160:0,scale=1008:567" -q:v 2 \
  images/cm_work.jpg
```

参数解读：`crop=宽:高:左偏移:上偏移`。`crop=1600:900:160:0` = 从 (160,0) 起取 1600×900，正好把底部字幕切掉。

取完用看图工具确认：字幕是否干净、主体是否完整、左右有没有切到人。

### 6. 截视频片段（要放进 PPT 播放时）

```bash
# 从 09:21 起截 5 秒，静音，720p，CRF 25
"$FF" -hide_banner -loglevel error -ss 561 -t 5 -i "$V" \
  -an -vf "scale=1280:720" -c:v libx264 -crf 25 -pix_fmt yuv420p clip.mp4
```

- 大文件务必把 `-ss` 放在 `-i` **之前**（前置定位只解码目标片段，快几十倍）
- `-an` 去掉音轨：课堂实录放 PPT 里同时出声会干扰讲解
- 5 秒 720p CRF25 大约 600–700 KB，适合入包

## 三、图片进入 SVG 的三条硬规定

```xml
<image href="../images/cm_work.jpg" x="690" y="246" width="502" height="282"
       preserveAspectRatio="xMidYMid slice"/>
```

1. **路径写 `../images/xxx.jpg`**——SVG 在 `svg_output/` 下，少两个点就渲染不出图。
2. **`preserveAspectRatio` 必须显式写**：`slice` 裁切填满（推荐，不留白边）、`meet` 完整显示（章节页整图用）。
3. **编译后检查 `<a:srcRect>`** 并删除——编译器会根据比例差异自动塞裁剪值，导致图只剩中间一条缝。用 `page_replace.py` 时脚本会自动删。

## 四、封面拱形图的做法

拱形裁切要在 PNG 里做好透明通道，不要指望 PPT 里裁剪：

```python
from PIL import Image, ImageDraw
im = Image.open("cover.jpg").convert("RGBA")
w, h = im.size
mask = Image.new("L", (w, h), 0)
d = ImageDraw.Draw(mask)
r = w // 2
d.rectangle([0, r, w, h], fill=255)          # 下半矩形
d.ellipse([0, 0, w, 2 * r], fill=255)        # 上半半圆
im.putalpha(mask)
im.save("cover_arch.png")
```

入 SVG 时用 `preserveAspectRatio="xMidYMid meet"` 保证拱形不被拉伸。

## 五、图片体积控制

- 单张控制在 150 KB 以内（`-q:v 2` 或 PIL `quality=85`）
- 尺寸不超过实际显示尺寸的 2 倍（502×282 的框，图做到 1008×567 足够）
- 一个 32 页的 PPT，图片总量控制在 5 MB 上下；视频单独算
- 全包超过 40 MB 时 PowerPoint 打开会明显变慢，要考虑压图
