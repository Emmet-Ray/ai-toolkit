# Skill 创建与维护

适用于本仓库自建 skill；命名规则用于新建或明确要求改名的情况。

1. **命名**：使用 kebab-case，优先采用“领域或对象 + 以 `-er` / `-or` 结尾的自然英文角色名”，如 `image-generator`、`sheet-music-snapper`。名称简短、职责明确，同系列结构一致，避免生造词、重名或重复能力。

2. **配图**：创建 skill 时，同时使用 `visual-summarizer` 生成配图，保存到仓库根目录 `.skill-images/<skill-name>.png`。

3. **引用维护**：目录名与 `SKILL.md` 的 `name` 保持一致；同步维护 `agents/openai.yaml`、README、todo、示例和配图引用。改名或移动后搜索旧名称、检查相关路径，避免遗漏。

4. **安装**：在 `~/.codex/skills/<skill-name>` 建立指向仓库 skill 目录的绝对路径符号链接。正确链接直接复用；改名或移动时更新、清理已确认属于本仓库的旧链接。同名文件、真实目录或其他来源链接保留并说明冲突。完成后确认能通过链接读取 `SKILL.md`。
