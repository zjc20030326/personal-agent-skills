# Repository maintenance

Keep each Skill self-contained under `skills/<name>/` with its required references, scripts and assets. Preserve the declared name and invocation policy. Keep external upstream packages in `sources.json`; do not vendor all third-party packages merely to change their source metadata.

Do not publish credentials, chats, private papers, local databases or machine backups. Preserve third-party attribution and package licenses. A preserved snapshot is not an upstream update subscription.

Run `python scripts/validate.py` before pushing. Run the existing `learn-cs-paper` tests when its scripts change. Update the source registry and README when package membership or provenance changes.
