# 我的 Skills

这里收录我创建和维护的技能，以及日常使用的第三方技能。本仓库维护的技能提供源码、使用说明与示例；第三方技能按使用场景归类，仅列出技能名称和上游链接。

## 本仓库维护

| 技能                                                        | 用途                               |
| ----------------------------------------------------------- | ---------------------------------- |
| [tldr-en-page-maintainer](tldr-en-page-maintainer/SKILL.md) | 创建、更新和润色英文 tldr 页面     |
| [tldr-zh-page-maintainer](tldr-zh-page-maintainer/SKILL.md) | 翻译、同步和润色简体中文 tldr 页面 |
| [image-generator](image-generator/SKILL.md)                 | 生成、编辑和批量生成图片           |
| [musescore-snapper](musescore-snapper/SKILL.md)             | 搜索曲谱并逐页截图保存 PNG         |

### tldr-en-page-maintainer

维护 [tldr-pages 项目](https://github.com/tldr-pages/tldr)中的英文命令页面，适用于补充缺失页面、根据当前命令行为更新内容，以及润色已有描述。

使用示例：

```text
@tldr-en-page-maintainer 为 git commit 补充英文页面。
@tldr-en-page-maintainer 根据当前官方文档更新 jq 的英文页面。
```

### tldr-zh-page-maintainer

维护 [tldr-pages 项目](https://github.com/tldr-pages/tldr)中的简体中文命令页面，适用于从英文源页面创建翻译、同步英文源页面变更，以及润色已有翻译。

使用示例：

```text
@tldr-zh-page-maintainer 为 git commit 补充简体中文翻译。
@tldr-zh-page-maintainer 将 jq 的简体中文页面与当前英文页面同步。
```

### image-generator

适用于根据文字描述生成图片、修改已有图片，以及批量生成多张图片。

使用示例：

```text
@image-generator 生成一张 16:9 的科技主题演示封面，保存到 output/cover.png。
@image-generator 编辑 input.png，保留布局，提高对比度，让标题更清晰，保存到 output/edited.png。
```

### musescore-snapper

从 MuseScore 链接获取完整谱面截图；只给曲名时先搜索并确认版本，未提供保存目录时先询问。在确认的目录下创建曲名文件夹，逐页保存为 `1.png`、`2.png`……。

使用示例：

```text
@musescore-snapper 把 https://musescore.com/user/44509610/scores/7703828 保存到 ~/Music/Scores
@musescore-snapper 给我《穿越时空的思念》的钢琴谱
```

## 日常使用的第三方技能

### 前端开发与设计

- [frontend-skill](https://developers.openai.com/blog/designing-delightful-frontends-with-gpt-5-4)
- [vercel-react-best-practices](https://github.com/vercel-labs/agent-skills/tree/main/skills/react-best-practices)
- [vercel-composition-patterns](https://github.com/vercel-labs/agent-skills/tree/main/skills/composition-patterns)
- [web-design-guidelines](https://github.com/vercel-labs/agent-skills/tree/main/skills/web-design-guidelines)

### 浏览器自动化与测试

- [playwright](https://github.com/openai/skills/tree/main/skills/.curated/playwright)
- [playwright-interactive](https://github.com/openai/skills/tree/main/skills/.curated/playwright-interactive)

### 文档处理

- [tencent-docs](https://docs.qq.com/scenario/open-claw.html)
- [image-to-editable-ppt](https://github.com/ningzimu/image-to-editable-ppt-skill/tree/main/skills/image-to-editable-ppt)

### 需求梳理与方案讨论

- [grill-me](https://github.com/mattpocock/skills/tree/main/skills/productivity/grill-me)
