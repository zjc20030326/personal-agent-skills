"""Pure ownership invariants shared by learn-cs-paper workspace CLIs."""

from __future__ import annotations

import hashlib
from pathlib import Path
import re
from typing import Any, Mapping


SKILL_NAME = "learn-cs-paper"
SCHEMA_VERSION = 1
DEFAULT_SKILL_VERSION = "1.0.0"
MANIFEST_RELATIVE = Path("assets") / "paper-manifest.json"
INVALID_WINDOWS_CHARS = re.compile(r'[<>:"/\\|?*\x00-\x1f]')
SEMVER_PATTERN = re.compile(
    r"^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)"
    r"(?:-(?:0|[1-9]\d*|\d*[A-Za-z-][0-9A-Za-z-]*)"
    r"(?:\.(?:0|[1-9]\d*|\d*[A-Za-z-][0-9A-Za-z-]*))*)?"
    r"(?:\+[0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*)?$"
)
SHA256_PATTERN = re.compile(r"^[0-9a-f]{64}$")


def sanitize_name(value: str) -> str:
    """Make a nonempty Windows-safe directory component from a title."""
    cleaned = INVALID_WINDOWS_CHARS.sub("", value)
    cleaned = re.sub(r"\s+", " ", cleaned).strip().rstrip(". ")
    return cleaned or "untitled-paper"


def sha256_file(path: Path) -> str:
    """Hash a file without reading the whole file into memory."""
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _is_within(path: Path, parent: Path) -> bool:
    try:
        path.relative_to(parent)
    except ValueError:
        return False
    return True


def _resolved_manifest_pdf(workspace: Path, value: str) -> Path:
    requested = Path(value).expanduser()
    return requested.resolve() if requested.is_absolute() else (workspace / requested).resolve()


def manifest_contract_issues(
    workspace: Path,
    manifest: Any,
    expected_title: str | None = None,
) -> list[tuple[str, str]]:
    """Return field/detail pairs for ownership violations without CLI side effects."""
    workspace = workspace.resolve()
    issues: list[tuple[str, str]] = []
    if not isinstance(manifest, Mapping):
        return [("root", "must be a JSON object")]
    if manifest.get("schema_version") != SCHEMA_VERSION:
        issues.append(("schema_version", f"expected {SCHEMA_VERSION!r}"))

    skill = manifest.get("skill")
    recorded_version: str | None = None
    if not isinstance(skill, Mapping):
        issues.append(("skill", "must be an object"))
    else:
        if skill.get("name") != SKILL_NAME:
            issues.append(("skill.name", f"expected {SKILL_NAME!r}"))
        candidate_version = skill.get("version")
        if not isinstance(candidate_version, str) or not SEMVER_PATTERN.fullmatch(candidate_version):
            issues.append(("skill.version", "must be canonical SemVer"))
        else:
            recorded_version = candidate_version
            if manifest.get("skill_version") != recorded_version:
                issues.append(("skill_version", "must equal skill.version"))

    paper = manifest.get("paper")
    paper_title: str | None = None
    if not isinstance(paper, Mapping):
        issues.append(("paper", "must be an object"))
    else:
        candidate_title = paper.get("title")
        if not isinstance(candidate_title, str) or not candidate_title:
            issues.append(("paper.title", "must be a nonempty string"))
        else:
            paper_title = candidate_title
            required_title = expected_title if expected_title is not None else paper_title
            if paper_title != required_title or manifest.get("title") != required_title:
                issues.append(("paper.title", f"expected {required_title!r}"))

    workspace_record = manifest.get("workspace")
    if not isinstance(workspace_record, Mapping):
        issues.append(("workspace", "must be an object"))
    else:
        recorded_root = workspace_record.get("root")
        if not isinstance(recorded_root, str) or not recorded_root:
            issues.append(("workspace.root", "must be a nonempty path"))
        elif Path(recorded_root).expanduser().resolve() != workspace:
            issues.append(("workspace.root", "must equal the existing workspace"))

    source = manifest.get("source")
    stored_hash = ""
    copied_pdf = ""
    original_pdf = ""
    if not isinstance(source, Mapping):
        issues.append(("source", "must be an object"))
    else:
        source_types_valid = True
        for field in ("reference", "original_pdf", "copied_pdf", "sha256", "retrieved_at"):
            if not isinstance(source.get(field), str):
                issues.append((f"source.{field}", "must be a string"))
                source_types_valid = False
        if isinstance(source.get("retrieved_at"), str) and not source.get("retrieved_at"):
            issues.append(("source.retrieved_at", "must be nonempty"))
        page_count = source.get("page_count")
        if page_count is not None and (
            isinstance(page_count, bool) or not isinstance(page_count, int) or page_count < 1
        ):
            issues.append(("source.page_count", "must be null or a positive integer"))
        if source_types_valid:
            stored_hash = source["sha256"]
            copied_pdf = source["copied_pdf"]
            original_pdf = source["original_pdf"]
            if stored_hash:
                if not SHA256_PATTERN.fullmatch(stored_hash):
                    issues.append((
                        "source.sha256", "must be 64 lowercase hexadecimal characters"
                    ))
                if not copied_pdf or not original_pdf:
                    issues.append(("source", "PDF paths and sha256 must be present together"))
                if copied_pdf:
                    copied_path = _resolved_manifest_pdf(workspace, copied_pdf)
                    if not _is_within(copied_path, workspace):
                        issues.append(("source.copied_pdf", "must stay inside the workspace"))
                    elif not copied_path.is_file():
                        issues.append(("source.copied_pdf", "recorded PDF does not exist"))
                    elif SHA256_PATTERN.fullmatch(stored_hash) and sha256_file(copied_path) != stored_hash:
                        issues.append(("source.sha256", "does not match the copied PDF"))
            elif copied_pdf or original_pdf:
                issues.append(("source", "PDF paths require a canonical sha256"))

    if paper_title:
        valid_names = {sanitize_name(paper_title)}
        if SHA256_PATTERN.fullmatch(stored_hash):
            valid_names.add(f"{sanitize_name(paper_title)}-{stored_hash[:8]}")
        if workspace.name not in valid_names:
            issues.append(("workspace.root", "directory name does not match the sanitized title"))
    return issues
