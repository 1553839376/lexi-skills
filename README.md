# WorkBuddy Skills

我自己在用的一组 WorkBuddy 技能。每个技能都来自实际做过的活儿——踩过坑、返过工，最后沉淀成一套可以照着重跑的流程。

## 目录

| 技能 | 说明 |
|---|---|
| [`edu-ppt-craft`](skills/edu-ppt-craft/) | 教育分享类 PPT 全流程：暖调纸感视觉规范、SVG 逐页生产、编译为可编辑 pptx、在已手工编辑的文件上做单页安全替换、从课件与视频取素材、同步撰写教研风格逐字稿 |

## 安装

把一个技能目录整个拷到 WorkBuddy 的用户技能目录：

```bash
cp -R skills/<技能名> ~/.workbuddy/skills/
```

拷过去之后重启会话即可生效。技能靠 `SKILL.md` 头部的 `name` 和 `description` 触发，不需要额外注册。

## 技能结构

```
<技能名>/
├── SKILL.md          # 必需：头部写 name / description，正文是流程
├── references/       # 按需加载的细节文档
├── scripts/          # 确定性脚本，可直接执行
└── assets/           # 模板、骨架等成品资源
```

`SKILL.md` 只放主流程和判断标准，细节全部下沉到 `references/`——这样技能被触发时不会一次吃掉整个上下文。

## 约定

- 脚本用 Python 3，只依赖标准库；确实需要第三方库时在 `SKILL.md` 里写明。
- `references/` 里的每条经验都要能追到一次真实的事故或返工，不写"理论上应该"。
- 涉及改动用户已有文件的操作，脚本必须自带备份与校验，失败时放弃写回。
