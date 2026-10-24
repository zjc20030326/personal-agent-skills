---
name: skillspector
description: Scan AI agent skills, Git repositories, URLs, ZIP files, or SKILL.md files for security risks before installation. Use when the user asks whether a skill is safe or requests a security scan.
---

Use the globally installed skillspector command.

Run static analysis with:

skillspector scan TARGET --no-llm

Replace TARGET with the local path or URL supplied by the user.

Report the risk score, severity, important findings, and installation recommendation. Do not install the scanned skill unless the user separately requests it.
