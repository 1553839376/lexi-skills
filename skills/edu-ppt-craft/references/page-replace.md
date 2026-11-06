# 单页替换：在用户手工改过的 PPT 上改一页

## 为什么不能整包覆盖

用户会在 PowerPoint 里自己改字、调图、加视频。一旦整包覆盖，这些改动全没了——这是这套流程里最容易造成严重损失的错误。

正确做法：**以用户当前文件为底，逐条复制，只替换目标页**。其余条目原样搬运，并用"字节级一致"证明没有误伤。

## 标准调用

```bash
python3 <skill>/scripts/page_replace.py \
    --src   "/path/交付版.pptx" \
    --page  29 \
    --slide-xml /tmp/export/ppt/slides/slide29.xml \
    --out   /tmp/out.pptx
```

常用可选参数：

| 参数 | 作用 |
|---|---|
| `--rels` | 新页的关系文件（不给则自动生成"仅 layout"的最小 rels） |
| `--media src=dest` | 补一个媒体文件，可重复多次，如 `--media /tmp/img.jpg=ppt/media/image_x.jpg` |
| `--drop  条目` | 顺带删除包内某条目（如不再被引用的图片） |
| `--layout slideLayout1` | 指定新 rels 指向的布局（默认沿用老页的布局，**不要跟新导出走**） |
| `--no-landing` | 跳过主题色落地（一般不要用） |
| `--dry-run` | 只报告差异，不写文件 |

`--page` 是**显示页码**（第几页），脚本内部通过 `sldIdLst` 换算到实际文件名，不需要你自己找 `slideNN.xml` 对应关系。

## 脚本做的七件事

1. **占用检查**：`lsof` 目标文件，被 PowerPoint 打开就中止（否则写回会被覆盖或损坏）
2. **备份**：`validation/交付备份_<时间戳>_page<N>前.pptx`（放在源文件同级的 `validation/`）
3. **主题色落地**：`schemeClr` → `srgbClr`（见 `pitfalls.md` 第 1 条）
4. **裁剪切边检查**：默认保留 `srcRect`（它是合法的比例裁剪），只在 `--strip-srcrect` 时才清
5. **替换 + 补媒体**：写 slide XML、rels、media
6. **校验**：逐条比对，打印"一致 / 替换 / 新增 / 删除"四类计数，断言无悬空 Target，`python-pptx` 试打开
7. **原子写回**：先写 `.tmp_xxx.pptx` 再 `os.replace`

## 怎么读校验输出

正常输出长这样：

```
一致 300 | 替换 2 | 新增 1 | 删除 0
悬空 Target: []
slides: 32
字节差异: ['ppt/slides/slide33.xml', 'ppt/slides/_rels/slide33.xml.rels']
```

**关键看"一致"这个数字**：它应当等于"总条目 − 替换 − 删除 − 新增"。这个数字越大，说明误伤面越小。300/303 是安全水位；如果只剩 200 多条一致，说明有整片条目被重写，要停下来查。

若出现下面任一情况，**不要交付**：

- `悬空 Target` 非空 → 打开就报"需要修复"
- `字节差异` 里出现你没打算改的条目
- `python-pptx` 抛异常
- 页数变了但你没打算删/加页

## 页序的三个文件（删页/加页时）

`presentation.xml` 里 `sldIdLst` 决定显示顺序，`[Content_Types].xml` 决定文件是否被登记，`presentation.xml.rels` 决定关系是否有效。**三者必须同步改**，少一个就报错。

删页步骤（脚本 `--drop-page` 模式已封装）：

1. 从 `sldIdLst` 删掉那个 `<p:sldId>`（**不要**删 slide 文件本身）
2. 从 `presentation.xml.rels` 删掉对应 `<Relationship>`
3. 从 `[Content_Types].xml` 删掉对应 `<Override>`
4. 保留 `ppt/slides/slideNN.xml` 文件——PowerPoint 按 `sldIdLst` 显示，文件名不影响

正则注意：`[Content_Types].xml` 里的 `ContentType` 值含 `/`，用 `[^/]*` 匹配会静默失败留悬空 Override，**必须用 `[^>]*`**。

## 加页（复制现有页做新页）

1. 复制一份 `slideNN.xml` 与 `.rels` 为 `slideM.xml`（M 取当前最大编号 +1）
2. 改里面所有 `<a:t>` 文本、页码数字
3. 在 `[Content_Types].xml` 加 `<Override PartName="/ppt/slides/slideM.xml" ContentType=".../slide+xml"/>`
4. 在 `presentation.xml.rels` 加一条 Relationship（rId 取未用的最大值）
5. 在 `sldIdLst` 的目标位置插入 `<p:sldId id="新id" r:id="新rId"/>`（id 取未用的最大值）

页码数字若被拆成两个 run（如"3"+"0"），按 `name="TextBox NN"` 定位整块再改，不要盲目替换全文的单个数字。

## 交付节奏

每次改完，汇报里必须给出四个数字：**页数 / 一致条目数 / 替换条目 / 备份路径**。用户看这四个数就知道有没有被动坏。
