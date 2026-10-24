# Personal Agent Skills

个人维护及保留快照的 Agent Skills。公共使用库由 CC Switch 管理；本仓库是个人包的维护源，不保存账号、Agent 配置、聊天记录、论文原文或备份。

## 包目录

| Skill | 用途 | 类型 |
|---|---|---|
| [learn-anything-fast](skills/learn-anything-fast/SKILL.md) | 通用学习路径与掌握检查 | personal |
| [learn-cs-paper](skills/learn-cs-paper/SKILL.md) | 计算机论文的双语精读与可恢复笔记工作区 | personal |
| [writing-mathematical-latex](skills/writing-mathematical-latex/SKILL.md) | 按聊天、Markdown、TeX 目标规范数学排版 | personal |
| [skillspector](skills/skillspector/SKILL.md) | 调用已安装扫描器的本地封装 | personal |
| [doc](skills/doc/SKILL.md) | OpenAI 已移除包的最后可用维护快照 | archived-upstream |
| [sora](skills/sora/SKILL.md) | OpenAI 已移除包的最后可用维护快照 | archived-upstream |
| [developing-with-bigquery](skills/developing-with-bigquery/SKILL.md) | 保留已安装 Google 包，当前未确认对应上游路径 | legacy-google-snapshot |
| [gcloud-auth-verification](skills/gcloud-auth-verification/SKILL.md) | 保留旧名称的 Google 身份认证指导包 | legacy-google-snapshot |
| [skill-repair](skills/skill-repair/SKILL.md) | 保留依赖宿主安装清单的 Google 修复指导包 | legacy-google-snapshot |

本仓库共 9 个可独立发现的 Skill；`sources.json` 同时记录本机 48 个公共包的准确仓库、子目录和本次上游提交。39 个第三方原版直接从各自上游更新，并未复制进本仓库。

## 更新流程

1. 在这个 Git 工作区修改个人包，并检查它的支持文件。
2. 运行 `python scripts/validate.py`；修改论文工作区脚本时另运行 `python -m unittest discover -s skills/learn-cs-paper/tests -v`。
3. 提交并推送到 GitHub 的 `main`。
4. 在 CC Switch 的 Skills 页面检查更新并更新。公共库和各 Agent 的分发副本由 CC Switch 维护，不在各副本中分别编辑。

仓库工作区和公共安装库是两个位置；未推送的本地修改不会经 GitHub 自动进入公共库。全局 Skill 发生实质变化时，仍需按使用者的规则备份和同步更新 Obsidian 说明。

## 来源与许可

- `learn-anything-fast`、`learn-cs-paper`、`writing-mathematical-latex` 是保留的个人工作流；`skillspector` 是已有的本地命令封装，不冒充 NVIDIA 官方 Skill。
- `doc`、`sora` 上游来源为 `openai/skills`；其公开目录已经移除。保留最后可用提交、原始 `LICENSE.txt`，来源提交见 `sources.json`。它们不会被标注为持续跟踪上游的新包。
- 3 个 `legacy-google-snapshot` 保留已有包及其 Apache-2.0 声明。已知发布者为 Google，但当前对应的准确公开上游路径未确认，不能以相近名称冒充来源；CC Switch 跟踪的是本仓库的保留版本。
- 第三方文件沿用各包自带许可证；本仓库未对全部内容统一重新授权。

## 公共目录与分发

公共主库为用户主目录中的 `.agents/skills`。Codex、Gemini CLI 原生读取此目录；DeepSeek Skills Manager 启用公共来源。Copilot CLI 官方支持此目录，但本机目前只有 VS Code 启动器，未安装实际 CLI。

Claude Code 使用 CC Switch 的复制分发。CC Switch 中 Claude 的专属分发开关启用；Codex/Gemini 的专属分发关闭以避免重复副本。这些开关表示“是否复制到专属目录”，不表示原生公共库中的 Skill 不可用。系统和插件自带的 Skill 留在软件自己的目录。

Windows 当前无符号链接权限，因此未更改系统权限，也未用目录链接绕过 CC Switch 的同步逻辑。只通过 CC Switch 更新公共库和 Claude 副本。

## 兼容性

公共发现不等于依赖齐全。`skillspector` 需要同名 CLI；论文脚本需要 Python，PDF 工具按实际任务加载；`doc` 的渲染需要 LibreOffice/Poppler 等；`sora` 仍需要有效 API 权限，历史快照不保证远端服务仍兼容；Google 包需要对应的工具、MCP 或安装清单。系统和插件附带的 Skill 不由本仓库管理。
