# AI Toolkit

我创建的 skills、我使用的第三方 skills 和 MCP。

## 目录

- [Skills](skills/README.md)：自建 skills 总览、使用示例和第三方 skills 清单。
- [MCP](mcp/README.md)：第三方 MCP 的来源、用途、接入方式和配置状态。

## 本地使用

自建 skills 位于 `skills/<skill-name>/`，通过绝对路径符号链接安装到 `~/.codex/skills/<skill-name>`。例如，在仓库根目录执行：

```bash
ln -s "$PWD/skills/image-generator" "$HOME/.codex/skills/image-generator"
```

安装前检查目标是否已存在；仓库移动后同步更新已有链接，并确认可以通过链接读取 `SKILL.md`。

MCP 的实际配置由 [dotfiles](https://github.com/Emmet-Ray/dotfiles) 管理，本仓库记录使用情况和配置位置。
