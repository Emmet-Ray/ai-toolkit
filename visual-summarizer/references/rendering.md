# 调用图像生成工具

## 复用 image-generator

从已安装 skill 或当前仓库找到 `image-generator/SKILL.md` 并阅读，随后使用其 `scripts/image_gen.py`。路径按实际安装位置解析，不将某台机器的绝对路径或用户账户写进通用调用逻辑。模型默认值、凭据、重试和后端选择由它维护；本技能不重复实现这些逻辑。

没有现成提示词时，先根据内容与风格构思，再用 CLI 的 `--prompt` 直接传入；较长提示词可写入系统临时目录的 UTF-8 文件，通过 `--prompt-file` 传入。路径通过系统临时目录接口获取，不依赖固定的 `/tmp` 路径，也不为提示词在项目内创建额外目录。用户明确要求原样使用的完整提示词应保持原样。

生成新图的形状如下，替换实际路径；模型参数只在用户指定或任务明确选定时传入：

```bash
python /实际位置/image-generator/scripts/image_gen.py generate \
  --backend auto \
  --prompt-file /系统临时目录/subject-prompt.txt \
  --size 1024x1024 --quality medium --background opaque \
  --out /实际位置/subject.png
```

需要以参考图生成时，先打开查看它，再使用编辑入口；提示词明确“仅参考风格，替换画面主体”。不要仅因某张单图曾被认可就自动传入；参考图中的人物、姿态或构图可能收窄新画面。参考不适合当前任务时，使用提炼出的风格文字直接生成：

```bash
python /实际位置/image-generator/scripts/image_gen.py edit \
  --backend auto \
  --image /实际位置/approved-reference.png \
  --prompt-file /系统临时目录/new-subject-prompt.txt \
  --size 1024x1024 --quality medium --background opaque \
  --out /实际位置/new-subject.png
```

首次使用不熟悉的后端或参数时可先加 `--dry-run` 检查。需要替换已确认图时先生成到系统临时路径，检查后再更新最终文件；不直接用 `--force` 覆盖已确认图。

## 工具不可用时

若 `image-generator` 未安装，使用环境内可用的图像生成工具并遵循其说明。将同样的完整提示词与需要的参考图传入，不只交付提示词冒充出图完成。没有可调用的生成能力时，在对话中提供准备好的提示词，说明缺失的具体能力，不自动创建交付目录。

## 尺寸与预览

检查图片实际返回的格式和像素尺寸。本仓库的 Codex OAuth 后端曾在请求 `1024x1024` 和 `2048x2048` 时均返回 `1254x1254`；这是观测结果，不是稳定接口约定。精确尺寸有要求时，应报告差异并按用户要求处理，不能将请求尺寸当作实际尺寸。

README 中控制展示宽度通常不需要重新编码源图。系列校对需要缩略联系表时，在系统临时目录创建；联系表仅供检查，最终仍交付各张独立原图。技能自身 `assets/` 中的参考图是安装时自带的静态资源，不是每次运行都要创建的输出目录。
