#!/usr/bin/env python3
"""Create a conservative, idempotent learn-cs-paper workspace."""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import sys
import tempfile
from datetime import datetime
from pathlib import Path
from pathlib import PureWindowsPath
from typing import Any, Mapping

from workspace_contract import (
    DEFAULT_SKILL_VERSION,
    MANIFEST_RELATIVE,
    SCHEMA_VERSION,
    SEMVER_PATTERN,
    SKILL_NAME,
    manifest_contract_issues,
    sanitize_name,
    sha256_file,
)


# Tests and callers consume JSON as UTF-8 even when Windows inherits a legacy
# console code page for redirected output.
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")


SKILL_ROOT = Path(__file__).resolve().parent.parent
TEMPLATE_DIR = SKILL_ROOT / "assets" / "templates"
DEFAULT_VAULT = r"D:\Markdown\Obsidian\Obsidian-Notes"
DEFAULT_COLLECTION = "论文\\机器学习"

TEMPLATE_FILES = {
    "paper-moc.md": None,
    "paper-map.md": "01-论文地图.md",
    "analysis.md": "03-深度分析.md",
    "concept-note.md": "04-知识地图.md",
    "study-log.md": "07-互动学习记录.md",
}

CODE_NOTE = """# 代码与复现\n\n状态：未开始，以下内容均未核验。\n\n- 原作者代码：待核验。\n- 复现环境与结果：待开始。\n"""
MODERN_CONTEXT_NOTE = """# 后续发展\n\n状态：未开始，以下内容均未核验。\n\n- 后续工作：待检索与核验。\n- 当前关联：待分析。\n"""


class InitializationError(Exception):
    """An expected safe-initialization refusal."""

    def __init__(self, code: str, workspace: Path, message: str) -> None:
        super().__init__(message)
        self.code = code
        self.workspace = workspace
        self.message = message


class ArgumentParseError(Exception):
    """A parser error which main can serialize as JSON when requested."""


class JsonAwareArgumentParser(argparse.ArgumentParser):
    """Prevent argparse from writing a non-JSON failure to stdout."""

    def error(self, message: str) -> None:
        raise ArgumentParseError(message)


class WorkspaceLock:
    """A cooperative exclusive lock for all writes to one workspace."""

    def __init__(self, workspace: Path) -> None:
        self.workspace = workspace
        self.path = workspace / ".learn-cs-paper.lock"
        self.descriptor: int | None = None

    def __enter__(self) -> "WorkspaceLock":
        if self.path.exists():
            raise InitializationError("workspace-locked", self.workspace, "workspace initialization lock already exists")
        if self.workspace.exists() and not (self.workspace / MANIFEST_RELATIVE).is_file():
            raise InitializationError("workspace-without-manifest", self.workspace, "existing workspace has no manifest; refusing takeover")
        self.workspace.mkdir(parents=True, exist_ok=True)
        try:
            self.descriptor = os.open(str(self.path), os.O_CREAT | os.O_EXCL | os.O_WRONLY)
            os.write(self.descriptor, str(os.getpid()).encode("ascii"))
        except FileExistsError as error:
            raise InitializationError("workspace-locked", self.workspace, "workspace initialization lock already exists") from error
        return self

    def __exit__(self, exc_type: object, exc: object, traceback: object) -> None:
        if self.descriptor is not None:
            os.close(self.descriptor)
        try:
            if self.path.exists():
                self.path.unlink()
        finally:
            self.descriptor = None


def now_iso() -> str:
    """Return a local, timezone-aware ISO 8601 timestamp."""
    return datetime.now().astimezone().isoformat(timespec="seconds")


def normalize_markdown_text(value: str) -> str:
    """Keep renderer values to one physical line in Markdown and YAML."""
    return re.sub(r"\s+", " ", value).strip()


def _replace_tokens(segment: str, values: Mapping[str, str], yaml_scalars: bool) -> str:
    rendered = segment
    for token in (
        "TITLE", "CREATED", "UPDATED", "SOURCE", "DOI", "ARXIV", "YEAR",
        "WORKSPACE_NAME", "SOURCE_PDF", "MANIFEST_PATH",
    ):
        value = values.get(token, "")
        rendered = rendered.replace("{{" + token + "}}", json.dumps(value, ensure_ascii=False) if yaml_scalars else value)
    return rendered


def render_template(template: str, values: Mapping[str, str], yaml_values: Mapping[str, str] | None = None) -> str:
    """Render approved tokens, JSON-quoting scalar values in frontmatter."""
    if template.startswith("---\n"):
        closing = template.find("\n---\n", 4)
        if closing == -1:
            raise ValueError("template frontmatter is not closed")
        yaml_values = yaml_values or values
        rendered = _replace_tokens(template[: closing + 5], yaml_values, True)
        rendered += _replace_tokens(template[closing + 5 :], values, False)
    else:
        rendered = _replace_tokens(template, values, False)
    if "{{" in rendered or "}}" in rendered:
        raise ValueError("template contains an unsupported or unresolved token")
    return rendered


def atomic_write_text(path: Path, text: str) -> None:
    """Atomically write UTF-8 text in the target directory."""
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary_path: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w", encoding="utf-8", newline="\n", delete=False, dir=path.parent,
            prefix=f".{path.name}.", suffix=".tmp",
        ) as temporary:
            temporary.write(text)
            temporary_path = Path(temporary.name)
        if path.exists():
            raise InitializationError("destination-exists", path.parent, f"refusing to overwrite existing file: {path}")
        temporary_path.replace(path)
    finally:
        if temporary_path is not None and temporary_path.exists():
            temporary_path.unlink()


def atomic_write_json(path: Path, value: Mapping[str, Any]) -> None:
    """Atomically write an indented UTF-8 JSON document."""
    atomic_write_text(path, json.dumps(value, ensure_ascii=False, indent=2) + "\n")


def safe_copy_pdf(source: Path, assets_dir: Path, source_hash: str) -> Path:
    """Copy a PDF without replacing an unequal pre-existing file."""
    if not source.is_file():
        raise FileNotFoundError(f"source PDF does not exist: {source}")
    assets_dir.mkdir(parents=True, exist_ok=True)
    filename = sanitize_name(source.stem) + source.suffix
    destination = assets_dir / filename
    if destination.exists() and sha256_file(destination) != source_hash:
        destination = assets_dir / f"{sanitize_name(source.stem)}-{source_hash[:8]}{source.suffix}"
    if destination.exists():
        if sha256_file(destination) != source_hash:
            raise InitializationError(
                "pdf-destination-conflict", assets_dir.parent,
                f"refusing to overwrite unequal PDF: {destination}",
            )
        return destination
    temporary_path: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(delete=False, dir=assets_dir, prefix=".pdf.", suffix=".tmp") as temporary:
            temporary_path = Path(temporary.name)
        shutil.copy2(source, temporary_path)
        if sha256_file(temporary_path) != source_hash:
            raise RuntimeError("temporary PDF hash did not match source")
        if destination.exists():
            if sha256_file(destination) == source_hash:
                return destination
            raise InitializationError("pdf-destination-conflict", assets_dir.parent, f"refusing to overwrite unequal PDF: {destination}")
        temporary_path.replace(destination)
    finally:
        if temporary_path is not None and temporary_path.exists():
            temporary_path.unlink()
    return destination


def _required_paths(moc_name: str) -> list[str]:
    return [
        moc_name, "01-论文地图.md", "02-双语对照", "03-深度分析.md",
        "04-知识地图.md", "05-代码与复现.md", "06-后续发展.md",
        "07-互动学习记录.md", "assets/paper-manifest.json", "assets/figures",
        "assets/tables",
    ]


def build_manifest(args: argparse.Namespace, workspace: Path, pdf_copy: Path | None,
                   pdf_hash: str | None, timestamp: str) -> dict[str, Any]:
    """Build the initial manifest; existing manifests are never rebuilt."""
    structure = {
        "sections": [], "paragraphs": [], "figures": [], "tables": [],
        "equations": [], "algorithms": [], "appendices": [], "references": [],
        "required_paths": _required_paths(f"{sanitize_name(args.title)} - MOC.md"),
    }
    counts = {key: len(value) for key, value in structure.items()}
    structure["required_paths_count"] = len(structure["required_paths"])
    return {
        "schema_version": SCHEMA_VERSION,
        "skill": {"name": SKILL_NAME, "version": args.skill_version},
        "paper": {
            "title": args.title, "authors": [], "year": args.year, "venue": "",
            "doi": args.doi, "arxiv": args.arxiv, "paper_type": "unverified",
            "domain": "computer-science",
        },
        "source": {
            "reference": args.source, "original_pdf": str(args.source_pdf.resolve()) if args.source_pdf else "",
            "copied_pdf": str(pdf_copy.resolve()) if pdf_copy else "",
            "sha256": pdf_hash or "", "page_count": None, "retrieved_at": timestamp,
        },
        "workspace": {"root": str(workspace.resolve()), "created": timestamp, "updated": timestamp},
        "structure": structure,
        "counts": counts,
        "progress": {
            "translation": "not-started", "analysis": "not-started", "knowledge": "not-started",
            "code": "not-started", "modern_context": "not-started", "learning": "not-started",
        },
        "uncertainties": ["论文元数据、结构和 PDF 页数尚未核验。"],
        "validated_sections": [],
        "last_validation": None,
        "title": args.title, "doi": args.doi, "arxiv": args.arxiv, "year": args.year,
        "source_reference": args.source, "skill_version": args.skill_version,
    }


def _manifest_hash(manifest: Mapping[str, Any]) -> str:
    source = manifest.get("source")
    if isinstance(source, Mapping):
        value = source.get("sha256", "")
        return value if isinstance(value, str) else ""
    return ""


def _manifest_refusal(workspace: Path, field: str, detail: str) -> InitializationError:
    return InitializationError(
        "invalid-manifest-ownership", workspace,
        f"existing manifest has invalid {field}: {detail}; refusing takeover",
    )


def validate_existing_manifest(
    workspace: Path, manifest: Any, expected_title: str
) -> Mapping[str, Any]:
    """Prove an existing workspace is owned by this skill and self-consistent."""
    issues = manifest_contract_issues(workspace, manifest, expected_title)
    if issues:
        field, detail = issues[0]
        raise _manifest_refusal(workspace, field, detail)
    return manifest


def _load_owned_manifest(workspace: Path, expected_title: str) -> Mapping[str, Any]:
    manifest_path = workspace / MANIFEST_RELATIVE
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8", errors="strict"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as error:
        raise InitializationError(
            "invalid-manifest", workspace, f"cannot read existing manifest: {error}"
        ) from error
    return validate_existing_manifest(workspace, manifest, expected_title)


def select_workspace(
    base: Path, pdf_hash: str | None, expected_title: str, check_lock: bool = True
) -> Path:
    """Select a safe base or hash-versioned workspace without taking over files."""
    base = base.resolve()
    if check_lock and (base / ".learn-cs-paper.lock").exists():
        raise InitializationError("workspace-locked", base, "workspace initialization lock already exists")
    manifest_path = base / MANIFEST_RELATIVE
    if not base.exists():
        return base
    if not manifest_path.is_file():
        raise InitializationError("workspace-without-manifest", base, "existing workspace has no manifest; refusing takeover")
    manifest = _load_owned_manifest(base, expected_title)
    stored_hash = _manifest_hash(manifest)
    if not pdf_hash or pdf_hash == stored_hash:
        return base
    versioned = base.with_name(f"{base.name}-{pdf_hash[:8]}")
    versioned_manifest = versioned / MANIFEST_RELATIVE
    if check_lock and (versioned / ".learn-cs-paper.lock").exists():
        raise InitializationError("workspace-locked", versioned, "workspace initialization lock already exists")
    if not versioned.exists():
        return versioned
    if not versioned_manifest.is_file():
        raise InitializationError("workspace-without-manifest", versioned, "hash-versioned workspace has no manifest; refusing takeover")
    versioned_data = _load_owned_manifest(versioned, expected_title)
    if _manifest_hash(versioned_data) != pdf_hash:
        raise InitializationError("workspace-hash-conflict", versioned, "hash-versioned workspace belongs to a different PDF")
    return versioned


def _ensure_generated_files(workspace: Path, values: Mapping[str, str], yaml_values: Mapping[str, str], moc_name: str) -> list[str]:
    created: list[str] = []
    for relative in ("02-双语对照", "assets", "assets/figures", "assets/tables"):
        directory = workspace / relative
        if not directory.exists():
            directory.mkdir(parents=True, exist_ok=True)
            created.append(relative)
    for template_name, target_name in TEMPLATE_FILES.items():
        target_name = moc_name if target_name is None else target_name
        target = workspace / target_name
        if not target.exists():
            template = (TEMPLATE_DIR / template_name).read_text(encoding="utf-8")
            atomic_write_text(target, render_template(template, values, yaml_values if template_name == "paper-moc.md" else None))
            created.append(target_name)
    for target_name, content in (("05-代码与复现.md", CODE_NOTE), ("06-后续发展.md", MODERN_CONTEXT_NOTE)):
        target = workspace / target_name
        if not target.exists():
            atomic_write_text(target, content)
            created.append(target_name)
    return created


def collection_parts(value: str) -> tuple[str, ...]:
    """Validate an explicitly relative collection path before any write."""
    if not value or not value.strip():
        raise ValueError("collection must not be empty")
    windows_path = PureWindowsPath(value)
    if windows_path.is_absolute() or windows_path.drive or windows_path.root:
        raise ValueError("collection must be a relative path")
    parts = tuple(re.split(r"[\\/]", value))
    if not parts or any(part in ("", ".", "..") for part in parts):
        raise ValueError("collection contains an unsafe component")
    return parts


def workspace_base(vault: Path, collection: str, title: str) -> Path:
    """Return an absolute title workspace proven to be contained by vault."""
    resolved_vault = vault.expanduser().resolve()
    try:
        candidate = (resolved_vault / Path(*collection_parts(collection)) / sanitize_name(title)).resolve()
        candidate.relative_to(resolved_vault)
    except ValueError as error:
        raise InitializationError("invalid-collection", resolved_vault / sanitize_name(title), str(error)) from error
    return candidate


def initialize_workspace(args: argparse.Namespace) -> dict[str, Any]:
    """Initialize or safely revisit a workspace and return the JSON contract."""
    vault = args.vault.expanduser().resolve()
    base = workspace_base(vault, args.collection, args.title)
    if not isinstance(args.skill_version, str) or not SEMVER_PATTERN.fullmatch(args.skill_version):
        raise InitializationError(
            "invalid-skill-version", base,
            "skill version must be a nonempty canonical SemVer value",
        )
    pdf_hash = sha256_file(args.source_pdf) if args.source_pdf else None
    workspace = select_workspace(base, pdf_hash, args.title)
    with WorkspaceLock(workspace):
        # Revalidate after acquiring the exclusive lock; another initializer may
        # have completed between the initial selection and lock acquisition.
        locked_workspace = workspace
        if (locked_workspace / MANIFEST_RELATIVE).is_file():
            workspace = select_workspace(base, pdf_hash, args.title, check_lock=False)
        if workspace != locked_workspace:
            raise InitializationError("workspace-selection-changed", workspace, "workspace selection changed while acquiring lock; retry")
        is_new = not (workspace / MANIFEST_RELATIVE).is_file()
        timestamp = now_iso()
        manifest_path = workspace / MANIFEST_RELATIVE
        source_pdf_value = ""
        pdf_copy: Path | None = None
        if args.source_pdf:
            pdf_copy = safe_copy_pdf(args.source_pdf, workspace / "assets", pdf_hash or "")
            source_pdf_value = pdf_copy.relative_to(workspace).as_posix()
        display_values = {
            "TITLE": normalize_markdown_text(args.title), "CREATED": timestamp, "UPDATED": timestamp,
            "SOURCE": normalize_markdown_text(args.source), "DOI": normalize_markdown_text(args.doi),
            "ARXIV": normalize_markdown_text(args.arxiv), "YEAR": normalize_markdown_text(args.year),
            "WORKSPACE_NAME": workspace.name,
            "SOURCE_PDF": f"[原始论文]({source_pdf_value})" if pdf_copy else "未提供 PDF",
            "MANIFEST_PATH": MANIFEST_RELATIVE.as_posix(),
        }
        yaml_values = dict(display_values)
        yaml_values["SOURCE_PDF"] = source_pdf_value
        moc_name = f"{sanitize_name(args.title)} - MOC.md"
        created = _ensure_generated_files(workspace, display_values, yaml_values, moc_name)
        if not manifest_path.exists():
            manifest = build_manifest(args, workspace, pdf_copy, pdf_hash, timestamp)
            atomic_write_json(manifest_path, manifest)
            created.append(MANIFEST_RELATIVE.as_posix())
    return {
        "status": "ok", "workspace": str(workspace.resolve()), "created": created,
        "manifest": str(manifest_path.resolve()), "new_workspace": is_new,
    }


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = JsonAwareArgumentParser(description=__doc__)
    parser.add_argument("--vault", type=Path, default=Path(DEFAULT_VAULT))
    parser.add_argument("--collection", default=DEFAULT_COLLECTION)
    parser.add_argument("--title", required=True)
    parser.add_argument("--source", default="")
    parser.add_argument("--source-pdf", type=Path)
    parser.add_argument("--doi", default="")
    parser.add_argument("--arxiv", default="")
    parser.add_argument("--year", default="")
    parser.add_argument("--skill-version", default=DEFAULT_SKILL_VERSION)
    parser.add_argument("--json", action="store_true")
    return parser.parse_args(argv)


def _option_value(argv: list[str], name: str, default: str) -> str:
    """Return the last syntactically valid option value from partial argv."""
    selected = default
    for index, argument in enumerate(argv):
        candidate: str | None = None
        if argument == name and index + 1 < len(argv):
            candidate = argv[index + 1]
        elif argument.startswith(name + "="):
            candidate = argument[len(name) + 1 :]
        if candidate and not candidate.startswith("-"):
            selected = candidate
    return selected


def fallback_workspace(argv: list[str]) -> Path:
    """Build a safe, absolute error path from partial command-line input."""
    vault = Path(_option_value(argv, "--vault", DEFAULT_VAULT)).expanduser().resolve()
    collection = _option_value(argv, "--collection", DEFAULT_COLLECTION)
    title = _option_value(argv, "--title", "untitled-paper")
    try:
        return workspace_base(vault, collection, title)
    except InitializationError:
        return (vault / sanitize_name(title)).resolve()


def main(argv: list[str] | None = None) -> int:
    raw_argv = list(sys.argv[1:] if argv is None else argv)
    wants_json = "--json" in raw_argv
    try:
        args = parse_args(raw_argv)
    except ArgumentParseError as error:
        message = str(error) or "invalid arguments"
        payload = {"status": "error", "code": "invalid-arguments", "workspace": str(fallback_workspace(raw_argv)), "message": message}
        if wants_json:
            print(json.dumps(payload, ensure_ascii=False))
        print(message, file=sys.stderr)
        return 2
    intended = fallback_workspace(raw_argv)
    try:
        payload = initialize_workspace(args)
    except InitializationError as error:
        payload = {"status": "error", "code": error.code, "workspace": str(error.workspace.resolve()), "message": error.message}
        print(json.dumps(payload, ensure_ascii=False) if args.json else error.message)
        return 1
    except (OSError, RuntimeError, ValueError) as error:
        payload = {"status": "error", "code": "initialization-failed", "workspace": str(intended.resolve()), "message": str(error) or error.__class__.__name__}
        print(json.dumps(payload, ensure_ascii=False) if args.json else payload["message"])
        return 1
    print(json.dumps(payload, ensure_ascii=False) if args.json else payload["workspace"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
