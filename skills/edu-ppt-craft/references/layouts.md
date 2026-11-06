# 版式库（26 种已验证版式）

每个版式都是"内容区"片段，**外层骨架**（底、纸框、角刻线、书签条、波浪、页码、页眉）一律照 `../assets/page-skeleton.svg`，此处不再重复。

内容区统一范围：x 88–1192，y 216–620。

---

## 1. 封面（cover）

左右分栏：左文右图，图用拱形裁切（PNG 预做透明通道），斜贴一条半透明纸胶带。

```xml
<g id="photo" data-pptx-role="decoration" data-pptx-bounds="716 72 564 494">
  <image id="cover-photo" href="../images/cover_arch.png" x="720" y="90" width="560" height="470"
         preserveAspectRatio="xMidYMid meet"/>
  <g id="tape" transform="rotate(-4 961 90)">
    <rect x="886" y="72" width="150" height="36" rx="3" fill="#F2C879" fill-opacity="0.85"/>
  </g>
</g>
<g id="kicker" data-pptx-bounds="84 128 560 40">
  <rect x="88" y="146" width="26" height="3" fill="#2F8B84"/>
  <text x="128" y="158" font-size="22" fill="#2F8B84">单位　·　场景说明</text>
</g>
<g id="title" data-pptx-bounds="84 186 630 176">
  <text x="88" y="256" font-size="64" font-weight="bold" fill="#1E3A38">主标题，<tspan x="88" dy="86">可折两行</tspan></text>
</g>
<rect id="title-rule" data-pptx-role="decoration" x="90" y="382" width="80" height="4" fill="#E8A84E"/>
<g id="subtitle" data-pptx-bounds="84 404 620 48">
  <text x="88" y="440" font-size="26" fill="#5C716E">副标题</text>
</g>
<g id="meta" data-pptx-bounds="84 456 620 46">
  <text x="88" y="490" font-size="22" fill="#8A9B96">姓名　·　单位　·　班级</text>
</g>
```

右上角可加大圆 `circle cx=1184 cy=650 r=118 fill=#E7F2EE`，左下角可加 4×3 点阵（`r=3.5 fill=#C6DED8`，间距 26）。

## 2. 目录/框架（toc）

左 1/3 放"一句话引出问题"，右 2/3 四条编号列表，每条左侧一条 7×62 暖黄色条。

```xml
<g id="lead" data-pptx-bounds="84 218 448 186">
  <text x="88" y="282" font-size="44" font-weight="bold" fill="#1E3A38">问题的起点</text>
  <text x="88" y="344" font-size="26" fill="#5C716E">两行说明文字，<tspan x="88" dy="44">用 dy 手动换行。</tspan></text>
</g>
<g id="toc-1" data-pptx-bounds="546 240 660 92">
  <rect x="548" y="250" width="7" height="62" rx="3.5" fill="#F2C879"/>
  <text x="578" y="274" font-size="22" font-weight="bold" fill="#2F8B84">01</text>
  <text x="622" y="274" font-size="32" font-weight="bold" fill="#1E3A38">第一部分标题</text>
</g>
<!-- toc-2/3/4 的 y 每次 +96 -->
```

## 3. 章节页（section）

左半 640px 满高图片（`x=0 y=0 width=640 height=720`），右侧 8px 浅青色条，右上放"第 N 部分"小标 + 两句标题 + 三行简介 + 底部一句备注。左下角可叠一个半透明白圆 + 大号章节数字。

```xml
<image id="ch-img" href="../images/ch2_how.jpg" x="0" y="0" width="640" height="720"
       preserveAspectRatio="xMidYMid meet"/>
<rect id="ch-bar" data-pptx-role="decoration" x="632" y="0" width="8" height="720" fill="#8FD0CB"/>
<g id="ch-stamp" data-pptx-bounds="32 612 88 92">
  <circle cx="76" cy="656" r="42" fill="#FAF6EE" fill-opacity="0.94"/>
  <text x="76" y="668" font-size="32" font-weight="bold" fill="#1E3A38" text-anchor="middle">09</text>
</g>
<rect id="ch-rule" data-pptx-role="decoration" x="700" y="180" width="46" height="4" fill="#8FD0CB"/>
<g id="ch-kicker" data-pptx-bounds="762 166 320 45">
  <text x="762" y="196" font-size="26" fill="#2F8B84">第二部分</text>
</g>
<g id="ch-title" data-pptx-bounds="700 259 496 144">
  <text x="700" y="310" font-size="44" font-weight="bold" fill="#1E3A38">标题第一行<tspan x="700" dy="70">标题第二行</tspan></text>
</g>
<g id="ch-body" data-pptx-bounds="700 440 496 133">
  <text x="700" y="470" font-size="26" fill="#5C716E">三行简介，<tspan x="700" dy="44">每行 dy=44。</tspan></text>
</g>
<g id="ch-note" data-pptx-bounds="700 609 520 40">
  <text x="700" y="636" font-size="22" fill="#8A9B96">底部一句备注。</text>
</g>
```

## 4. 定义/引文页（define）

上半一句 44 号定义（两行），下半三个"关键词胶囊"横排（`rect rx=20` + 22 号字），胶囊间距 24。

## 5. 三条理由（三卡横排）

三张 340×310 白色圆角卡，间距 42（88 / 470 / 852），顶部 6px 色条区分（暖黄 / 浅青 / 陶土）。

```xml
<g id="card-1" data-pptx-bounds="88 272 344 318">
  <rect x="88" y="276" width="340" height="310" rx="14" fill="#FFFFFF" stroke="#F0E5D1" stroke-width="2"/>
  <rect x="88" y="276" width="340" height="6" rx="3" fill="#F2C879"/>
  <text x="112" y="470" font-size="22" font-weight="bold" fill="#C08A2E">一</text>
  <text x="112" y="504" font-size="32" font-weight="bold" fill="#1E3A38">卡片标题</text>
  <text x="112" y="536" font-size="22" fill="#5C716E">一行说明</text>
  <text x="112" y="566" font-size="22" fill="#C08A2E">关键词·关键词</text>
</g>
```

## 6. 左文右图（最常用，内容页标准形态）

左侧三条要点（圆点列表），右侧一张图 + 图注。**这是全篇使用频率最高的版式，务必背下坐标。**

```xml
<g id="item-1" data-pptx-bounds="82 256 536 104">
  <circle cx="96" cy="282" r="5" fill="#2F8B84"/>
  <text x="114" y="290" font-size="26" fill="#1E3A38">第一行，<tspan x="114" dy="40">第二行。</tspan></text>
</g>
<!-- item-2 y=366, item-3 y=476（间距 110） -->
<g id="media" data-pptx-bounds="689 245 504 284">
  <rect x="689" y="245" width="504" height="284" fill="#FFFFFF" stroke="#E6D8BF" stroke-width="2"/>
  <image href="../images/xxx.jpg" x="690" y="246" width="502" height="282"
         preserveAspectRatio="xMidYMid slice"/>
</g>
<g id="media-cap" data-pptx-bounds="690 536 502 40">
  <text x="690" y="566" font-size="22" fill="#8A7A60">图注一行，不超过 18 字</text>
</g>
```

变体：**无图版**——只删 `media` 与 `media-cap` 两组，其余一律不动。若希望文字块居中，整体把 `x` 从 82 挪到 387（圆点 cx 401、文字 x 419），**不要改字号、不要改颜色、不要加卡片**。

## 7. 大字留白（question）

只有一句 56–64 号问句 + 一条金句线 + 一行 22 号小注，其余留白。用在每 4–5 页密内容后的节奏点。

## 8. 纵列三条 + 右侧故事图卡（barriers）

左 640px 三条，每条左侧 6px 竖色条（`#EFA98F`）+ 32 号粗标题 + 26 号正文；右侧一张 486 宽的图卡。

## 9. 横向步骤条（steps）

5 个等宽步骤块横排，每块 200×230，顶部序号圆（`r=22` 暖黄底 + 陶土字），块间用 2px 虚线箭头连接。

## 10. 剧本/气泡列（tools）

左侧竖排 5 个圆角气泡（`rx=24`），每气泡一句台词，右侧配一张角色图。适合"这节课教什么"的五句核心用语。

## 11. 角色卡并排（roles）

三张竖卡 320×400，图在上（320×300，`slice`）、名字在下，卡底加一句角色定位。

## 12. 左右对比（compare）

中线一条 2px 浅色竖线；左栏标"第一版"（珊瑚 `#EFA98F` 小标），右栏标"改后"（主色小标）；两栏各一张图 + 三条说明。

## 13. 大图 + 右侧清单（review）

左 586×294 白框大图 + 22 号图注；右侧 32 号粗体错误清单 + 一条带珊瑚竖条的"为什么对我们影响更大"小段。**这是"AI 会犯错"这类页的标准形态。**

## 14. 播放器（video）

16:9 视频框（502×282）+ 模拟播放按钮（`circle r=30 fill=#FFFFFF fill-opacity=0.9` + 三角 path）+ 下方一句引语气泡。编译时视频节点要手工插入（见 `build-pipeline.md`）。

## 15. 图卡网格（cards）

3×2 或 5+1 网格，每格 328×210，图片 `slice` 填满 + 底部一行 22 号标签。

## 16. 阶梯（stairs）

7 个横向条，每往下一级缩进 32px，左侧序号 + 一句目标描述。适合"同一节课七套目标"。

## 17. 拼贴（collage）

左侧 2×2 小图 + 右侧 1 张大图，用不同尺寸制造节奏。适合"五样东西"。

## 18. 闭环（loop）

横向三段 + 两段之间的弧形箭头，首尾用虚线回指。适合"情境有头有尾"。

## 19. 流程 + 角色卡（walk）

左侧竖排流程（4 步，虚线连接），右侧三张岗位卡横排。

## 20. 三行带分隔线（pits）

三行，每行：序号 + 32 号粗标题 + 26 号正文，行间一条 1px `#E6D8BF` 分隔线，行高 130。

## 21. 结语（closing）

左文右图（同第 6 式但无圆点），标题 44 号分两行，正文三段 26 号，末尾一句 32 号粗体落款式结论。

## 22. 谢谢（thanks）

居中：64 号"谢谢大家" + 上方一条短金句线 + 下方一行 22 号小字。**这一页容易空**，四周可加：四角双层角花、左右竖线 + 菱形端点、圆环引线、标题下菱形双线、底部分隔线。注意所有装饰 y 坐标要避开文字基线。

## 23. 六步流程图（process）

2 行 3 列，每格 328×170，格子左上角小号步骤数字（20 号陶土色），格内 26 号标题 + 22 号说明，格子间用箭头 path 连接。

## 24. 五宫格机关（mechanism）

五张等高卡横排（208×300），卡顶圆形图标位（`r=30` 浅青底），卡内 26 号标题 + 22 号一句效果描述。

## 25. 数据条（stat）

2–3 个大数字（64 号陶土色）+ 各配一行 26 号说明。**数字必须有真实来源，宁可不用。**

## 26. 双栏成效（effect）

左右两栏各 520 宽，栏标题 32 号粗体带主色小方块，栏内三条 26 号要点；栏间一条 1px 虚线。

---

## 使用建议

- 一套 30 页的分享，版式分布大约：封面 1、目录 1、章节 4、内容页 20（其中第 6 式占 8–10 页）、留白 2、结语 1、谢谢 1。
- **同一式连续出现不超过 3 页**，中间插章节页或留白页断开。
- 新增版式前先翻这份清单，八成能找到能改的。
