# 我使用的第三方 MCP

以下为 Codex 中手动配置的第三方 MCP，配置状态核对于 **2026-10-29**。启用状态来自配置文件，不代表本次执行了连通性测试。

| MCP | 用途 | 接入方式 | 配置状态 |
| --- | --- | --- | --- |
| [Context7](https://github.com/upstash/context7) | 查询库、框架和 SDK 的文档 | 本地通过 `npx` 运行 `@upstash/context7-mcp` | 启用（未显式禁用） |
| [Figma](https://developers.figma.com/docs/figma-mcp-server/) | 获取设计上下文，辅助设计转代码 | 远程服务 `https://mcp.figma.com/mcp` | 已禁用（`enabled = false`） |

## 配置位置

- Codex 入口：`~/.codex/config.toml`。
- 实际文件：`~/dotfiles/codex/.codex/config.toml`，入口通过软链接指向该文件。
- 对应配置节：`[mcp_servers.context7]` 和 `[mcp_servers.figma]`。
- 配置由 [dotfiles](https://github.com/Emmet-Ray/dotfiles) 管理；接入和认证步骤以各 MCP 官方文档及实际配置为准。

## 维护方式

添加或停用 MCP 时更新上表和核对日期。需要详细记录时，再补充安装要求、认证方式、使用心得和已知限制；密钥和 token 留在本机或密码管理器中。

本清单覆盖上述 Codex 配置中的第三方服务。应用配套的 `node_repl`、`computer-use` 以及插件提供的工具不计入此清单。
