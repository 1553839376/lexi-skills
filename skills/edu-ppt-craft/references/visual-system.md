# 视觉系统：暖调纸感教育风

一套为**教育类分享 / 教研汇报**设计的视觉语言。特点：暖米纸底、墨绿正文、细纸边框、底部浅绿波浪承托结论句。投影下对比足够，打印也不糊。

画布固定 **1280×720**（16:9）。所有坐标以 px 计，SVG 与 PPT 比例一致，编译后不需要换算。

## 一、色卡（只用这些，不要临时加色）

| 用途 | 色值 | 说明 |
|---|---|---|
| 页面底色 | `#FAF6EE` | 暖米。**绝不能用纯白**，用户会一眼看出不对 |
| 次级底色 | `#F2EDE0` | 卡片底、对比区块 |
| 主文字 | `#1E3A38` | 深墨绿，接近黑但更暖 |
| 次要文字 | `#5C716E` | 说明性段落 |
| 图注 / 极轻文字 | `#8A7A60` | 图片下方一行 |
| 章节小标 | `#8A9B96` | 页脚备注 |
| 主色 | `#2F8B84` | 圆点、页码描边、左边竖条 |
| 浅主色 | `#8FD0CB` | 章节页色条、次级强调 |
| 暖黄 | `#F2C879` | 左边缘书签条、序号底 |
| 金句线 | `#E8A84E` | 标题下短横线、引线 |
| 珊瑚 | `#EFA98F` | 对比页的"改前"标记 |
| 陶土 | `#B0735A` | 序号数字、强调数字 |
| 边框 | `#E6D8BF` | 外层纸框、卡片描边 |
| 内框 | `#F2E7D3` | 内层纸框 |
| 波浪 | `#E4F0EC` | 底部承托色带 |
| 卡片白 | `#FFFFFF` | 图片白框、纯色卡片 |
| 校对蓝 | `#1F6FB2` | 仅用于逐字稿里的"论文补充"段，PPT 不用 |

## 二、字号阶梯（只有这几级，不许再加）

| 层级 | 字号 | 字重 | 用在哪 |
|---|---|---|---|
| 封面主标题 | 64 | bold | 封面、结语大字 |
| 页标题 | 44 | bold | 每页顶部 |
| 章节页标题 | 44 | bold | 章节页 |
| 模块标题 / 结论句 | 32 | bold | 金句、卡片标题 |
| 正文 | 26 | normal | 条目正文、段落 |
| 小标题 | 26 | normal | 章节小标（配主色） |
| 注释 | 22 | normal | 图注、页码、页脚备注 |
| 序号 | 20 | bold | 卡片内 01/02/03 |

字号与字重的分工原则：**靠字号和字重分层，不靠颜色堆叠**。一页里出现三种以上颜色就意味着降噪失败。

## 三、栅格

- 内容区左右边界：x = **88** 到 x = **1192**（宽 1104）
- 标题块：章节小标 baseline 120，主标题 baseline 184，标题下短横线 y = 206
- 正文起始：y = **256**
- 条目间距：**110**（单行）或 **124**（带副行的卡片）
- 卡片内边距：**30**；卡片间距：**64–76**
- 底部金句：baseline **660**，x = 88
- 底部波浪：从 y = **612** 起伏到 698
- 页码胶囊：x 1146, y 632, 68×40, rx 20

## 四、每页固定装饰四件套

这些是所有内页共用的骨架，**一页都不能少**，也不要额外加东西。完整可复制代码见 `../assets/page-skeleton.svg`。

```xml
<!-- 1. 底 -->
<rect id="page-bg" data-pptx-role="background" x="0" y="0" width="1280" height="720" fill="#FAF6EE"/>

<!-- 2. 双层纸边框 -->
<rect id="frame-outer" data-pptx-role="decoration" x="26" y="22" width="1228" height="676" rx="18"
      fill="none" stroke="#E6D8BF" stroke-width="2"/>
<rect id="frame-inner" data-pptx-role="decoration" x="38" y="34" width="1204" height="652" rx="12"
      fill="none" stroke="#F2E7D3" stroke-width="1"/>

<!-- 3. 角刻线 + 右上同心圆 -->
<g id="corner-ticks" data-pptx-role="decoration" data-pptx-bounds="44 40 1192 96">
  <path d="M44 68 L44 44 L68 44" fill="none" stroke="#E3D3B4" stroke-width="2"/>
  <path d="M1212 44 L1236 44 L1236 68" fill="none" stroke="#E3D3B4" stroke-width="2"/>
  <circle cx="1210" cy="94" r="30" fill="none" stroke="#EFF5F2" stroke-width="2"/>
  <circle cx="1210" cy="94" r="17" fill="#F7E6C6"/>
</g>

<!-- 4. 左边缘书签条 + 底部波浪 + 页码胶囊 -->
<rect id="edge-tab" data-pptx-role="decoration" x="18" y="340" width="16" height="88" rx="9" fill="#F2C879"/>
<path id="wave" data-pptx-role="decoration"
      d="M26 612 C 210 572 400 646 620 612 C 840 578 1050 648 1254 606 L1254 698 L26 698 Z"
      fill="#E4F0EC"/>
<g id="footer-page" data-pptx-bounds="1144 630 74 44">
  <rect x="1146" y="632" width="68" height="40" rx="20" fill="none" stroke="#2F8B84" stroke-width="1.5"/>
  <text x="1180" y="660" font-size="22" font-weight="bold" fill="#2F8B84" text-anchor="middle">28</text>
</g>
```

页眉三件套：

```xml
<rect id="header-bar" data-pptx-role="decoration" x="88" y="84" width="7" height="48" fill="#2F8B84"/>
<g id="header" data-pptx-bounds="82 88 1060 118">
  <text x="112" y="120" font-size="26" fill="#2F8B84">04　成效与反思</text>
  <text x="88" y="184" font-size="44" font-weight="bold" fill="#1E3A38">学生：看得进去，也用得出来</text>
</g>
<rect id="header-rule" data-pptx-role="decoration" x="90" y="206" width="80" height="4" fill="#E8A84E"/>
```

章节小标里的间隔用**全角空格**（`04　成效与反思`），不要用两个半角空格，否则会被压成一格。

## 五、必须遵守的 SVG 写法

编译器靠属性判断元素角色，写错会丢样式：

1. `data-pptx-role`：`background` / `decoration` / 不写（内容）。装饰件加 `decoration` 才能被识别为可单独选中的装饰。
2. 文本组加 `data-pptx-bounds="x y w h"`：**必填**，否则编译后用 PowerPoint 选不中、改不了。
3. 多行文本用 `<tspan x="..." dy="40">` 手动换行，**不要**靠 `<text>` 自动换行——编译器不会算。
4. 字体写在根 `<svg font-family="Microsoft YaHei">`，不要逐节点写。
5. 图片路径必须 `../images/xxx.jpg`（SVG 在 `svg_output/` 下）；`preserveAspectRatio` 用 `xMidYMid slice`（裁切填满）或 `meet`（完整显示）。
6. 不要把 `<a:...>` 之类的 PPT 语法写进 SVG。

## 六、页面角色标记

根节点写 `data-pptx-page-role`，决定编译时的页面处理方式：

- `section` —— 章节页（整页色块 + 左图）
- `content` —— 普通内容页
- `cover` / `closing` —— 封面与收束页

## 七、节奏控制

整套 PPT 的呼吸感来自"密—疏—密"交替，不要让每页都塞满：

- 每 4–5 页密内容后插一页**大字留白页**（只有一句问句或一个数字）
- 章节页永远左图右文，图占左半 640px 满高，形成翻页时的视觉停顿
- 结论句（金句）只在成效页、反思页出现，不是每页都有
