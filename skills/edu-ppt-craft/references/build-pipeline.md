# 编译流水线：SVG → 可编辑 PPTX

依赖 `ppt-master` skill 的编译器（`<ppt-master>/scripts/svg_to_pptx.py`、`svg_quality_checker.py`）。本 skill 只负责"怎么把它用对"。

## 一、项目目录约定

```
<项目根>/
├── spec_lock.md              # 规格锁（编译器读它）
├── svg_output/               # 逐页 SVG，01_xx.svg 连续编号
├── images/                   # 所有图片素材（SVG 用 ../images/ 引用）
├── exports/                  # 编译产物，带时间戳
└── validation/               # 每轮改动的备份
```

`svg_output/` 里文件名编号必须连续、两位数；页序由文件名排序决定，不连续会导致页序错乱。

## 二、spec_lock.md（缺 `## canvas` 会被拒）

```markdown
# 项目规格锁 —— <项目标题>

## typography

- font_family : Microsoft YaHei
- title_family : Microsoft YaHei
- body_family : Microsoft YaHei
- title : 44
- body : 26
- display : 64
- heading : 32
- caption : 22

## colors

- bg : #FAF6EE
- secondary_bg : #F2EDE0
- text : #1E3A38
- text_secondary : #5C716E
- primary : #2F8B84
- accent : #F2C879
- secondary_accent : #E8A84E
- border : #E6D8BF

## pptx_structure

- mode : flat

## canvas

- viewBox : 0 0 1280 720
```

`## canvas` 段是 release 级导出的**硬门槛**，漏了就报"未声明画布"。格式必须是 `- viewBox : 0 0 1280 720`（键值之间有空格）。

## 三、三步走

### 1. 先跑质量检查

```bash
python3 <skill>/scripts/run_svg.py <ppt-master>/scripts/svg_quality_checker.py <项目根> \
        --canonical-authoring --stage final --json
```

看 `validation/svg_quality_report.json` 的 `summary`：

```bash
python3 -c "
import json;d=json.load(open('<项目根>/validation/svg_quality_report.json'));print(d['summary'])"
```

正常形态是「N 页 / 多数通过 / 若干 warning / 0 error」。**warning 可放行，error 必须改。**

### 2. 再编译

```bash
python3 <skill>/scripts/run_svg.py <ppt-master>/scripts/svg_to_pptx.py <项目根>
```

产物在 `exports/<slug>_<时间戳>.pptx`。取最新那个时间戳。

### 3. 定位"第 N 页对应哪个 slideNN.xml"

**不要靠文件名推断页序**，一定能序错：

```bash
python3 <skill>/scripts/pptx_inspect.py <pptx> --list
```

它读 `presentation.xml` 的 `sldIdLst` + `presentation.xml.rels` 得到真实顺序，并打印每页的文本摘要。改哪页、取哪个文件，以它为准。

## 四、沙箱 `mkdir` 报错的绕法

ppt-master 的脚本在沙箱里跑会因 `pathlib.Path.mkdir` 抛 `EEXIST`（目录已存在但 broker 拦截）。`scripts/run_svg.py` 已内置绕法：还原原生 `Path.mkdir` 后用 `runpy` 执行目标脚本。

用法固定为：

```bash
python3 <skill>/scripts/run_svg.py <要执行的脚本.py> <脚本参数...>
```

不要 `cd` 到项目目录再跑，保持工作目录在项目外（`/tmp` 即可）。

## 五、渲染 PNG 自检

```bash
python3 <skill>/scripts/render_svg.py <svg文件> <输出png>
```

内部用 Chrome headless：

```bash
"/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" \
  --headless=new --no-sandbox --disable-gpu --hide-scrollbars \
  --allow-file-access-from-files --force-device-scale-factor=1 \
  --window-size=1280,720 --screenshot=<png> "file://<svg绝对路径>"
```

要点：

- **渲染前先 `rm -f` 目标 png**——Chrome 有时静默失败，旧图会留下，让你误以为渲染成功。
- 必须用 `--headless=new`，旧的 `--headless` 对 file:// + 内嵌图片支持不稳。
- 复杂页（大量渐变和 path）可能超时，重试一次即可；连续失败就把该页简化。
- 预览图只是自检用，**不要写进交付目录**。

## 六、视频页的特殊处理

编译器不会把 `<image>` 变成视频。做法是**照抄一份已有的视频页 XML**，只改文本与位置：

```xml
<p:pic>
  ...
  <p:nvPicPr><p:cNvPr id="..." name="video"/><p:cNvPicPr><a:videoFile r:link="rId3"/></p:cNvPicPr></p:nvPicPr>
  <p:blipFill><a:blip r:embed="rId4"/></p:blipFill>
  ...
  <p14:media r:embed="rId4" xmlns:p14="..."/>
</p:pic>
```

- `a:videoFile r:link` 和 `p14:media r:embed` 指向**同一个** mp4 的两个 rId。
- rels 里两条关系都要有，且都指向 `../media/xxx.mp4`。
- 删掉编译器塞进来的 `<a:srcRect>`。
- 封面图（`a:blip` 引的那张 poster）要一起进包。

## 七、导出后的必查项

```bash
python3 <skill>/scripts/pptx_inspect.py <pptx> --verify
```

检查四件事：

1. 页数是否符合预期
2. 每个 `.rels` 的 Target 是否都存在于包内（**悬空引用**是打不开的头号原因）
3. 每页里 `schemeClr` 计数是否为 0（不为 0 就去落地，见 `pitfalls.md` 第 1 条）
4. 每页 `<p:pic>` 数与预期图片数是否一致
