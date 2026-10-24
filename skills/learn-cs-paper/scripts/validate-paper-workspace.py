#!/usr/bin/env python3
"""Validate a learn-cs-paper workspace without changing it."""

from __future__ import annotations

import argparse
from dataclasses import asdict, dataclass
import json
from pathlib import Path, PureWindowsPath
import re
import sys
from typing import Any, Iterable, Mapping
from urllib.parse import unquote

from workspace_contract import (
    MANIFEST_RELATIVE,
    manifest_contract_issues,
    sanitize_name,
    sha256_file,
)


if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")


DEFAULT_VAULT = Path(r"D:\Markdown\Obsidian\Obsidian-Notes")
PLACEHOLDER_PATTERN = re.compile(r"\{\{[^{}\r\n]+\}\}")
BLOCK_ID_PATTERN = re.compile(r"^\s*\^([A-Za-z0-9_-]+)\s*$")
WIKILINK_PATTERN = re.compile(r"!?\[\[([^\]]+)\]\]")
MARKDOWN_LINK_START_PATTERN = re.compile(r"!?\[(?!\[)(?:\\.|[^\]\r\n])*\]\(")
URL_PATTERN = re.compile(r"^[A-Za-z][A-Za-z0-9+.-]*:")
COUNT_FIELDS = (
    "sections", "paragraphs", "figures", "tables", "equations",
    "algorithms", "appendices", "references",
)


@dataclass(frozen=True)
class Finding:
    """One deterministic validation result."""

    severity: str
    code: str
    path: str
    message: str


@dataclass(frozen=True)
class MarkdownDocument:
    """One Markdown file read once, with literal regions masked by line."""

    path: Path
    original_lines: tuple[str, ...]
    masked_lines: tuple[str, ...]


class WorkspaceLoadingError(Exception):
    """Expected error while locating or decoding a workspace."""

    def __init__(self, code: str, path: Path, message: str) -> None:
        super().__init__(message)
        self.code = code
        self.path = path
        self.message = message


class JsonArgumentParser(argparse.ArgumentParser):
    """Keep argument errors available for the JSON-only CLI contract."""

    def error(self, message: str) -> None:
        raise WorkspaceLoadingError("invalid-arguments", Path.cwd(), message)


def _absolute(path: Path) -> Path:
    return path.expanduser().resolve()


def _is_within(path: Path, parent: Path) -> bool:
    try:
        path.relative_to(parent)
    except ValueError:
        return False
    return True


def load_manifest(workspace: Path) -> dict[str, Any]:
    """Load the UTF-8 JSON manifest or report an invocation/loading error."""
    manifest_path = workspace / MANIFEST_RELATIVE
    if not workspace.exists() or not workspace.is_dir():
        raise WorkspaceLoadingError(
            "invalid-workspace", workspace, "workspace must be an existing directory"
        )
    if not manifest_path.is_file():
        raise WorkspaceLoadingError(
            "missing-manifest", manifest_path, "manifest file is missing"
        )
    try:
        data = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as error:
        raise WorkspaceLoadingError(
            "invalid-manifest", manifest_path, f"manifest must be valid JSON: {error}"
        ) from error
    if not isinstance(data, dict):
        raise WorkspaceLoadingError(
            "invalid-manifest", manifest_path, "manifest must be a JSON object"
        )
    return data


def collect_markdown(workspace: Path) -> list[Path]:
    """Return workspace Markdown files in a deterministic order."""
    return sorted(
        (path for path in workspace.rglob("*.md") if path.is_file()),
        key=lambda path: path.as_posix().casefold(),
    )


def _mask_markdown_literals(text: str) -> tuple[str, ...]:
    """Mask fenced/inline code and escaped characters without changing lines."""
    masked: list[str] = []
    fence: tuple[str, int] | None = None
    for line in text.splitlines():
        fence_match = re.match(r"^ {0,3}(`{3,}|~{3,})", line)
        if fence is not None:
            masked.append(" " * len(line))
            closing = re.match(rf"^ {{0,3}}({re.escape(fence[0])}+)[ \t]*$", line)
            if closing and len(closing.group(1)) >= fence[1]:
                fence = None
            continue
        if fence_match:
            opening = fence_match.group(1)
            fence = (opening[0], len(opening))
            masked.append(" " * len(line))
            continue
        characters = list(line)
        index = 0
        while index < len(characters):
            if (characters[index] == "\\" and index + 1 < len(characters)
                    and characters[index + 1] in "[]"):
                characters[index] = " "
                characters[index + 1] = " "
                index += 2
                continue
            if characters[index] == "`":
                marker_end = index
                while marker_end < len(characters) and characters[marker_end] == "`":
                    marker_end += 1
                marker = "`" * (marker_end - index)
                closing = line.find(marker, marker_end)
                end = len(characters) if closing == -1 else closing + len(marker)
                for position in range(index, end):
                    characters[position] = " "
                index = end
                continue
            index += 1
        masked.append("".join(characters))
    return tuple(masked)


def load_markdown(markdown_files: Iterable[Path]) -> tuple[list[MarkdownDocument], list[Finding]]:
    """Read all Markdown strictly once and retain deterministic error evidence."""
    documents: list[MarkdownDocument] = []
    findings: list[Finding] = []
    for path in markdown_files:
        try:
            text = path.read_text(encoding="utf-8", errors="strict")
        except (OSError, UnicodeDecodeError) as error:
            findings.append(_finding(
                "markdown-read-error", path,
                f"cannot read Markdown as UTF-8: {error}",
            ))
            continue
        lines = tuple(text.splitlines())
        documents.append(MarkdownDocument(path, lines, _mask_markdown_literals(text)))
    return documents, findings


def _finding(code: str, path: Path, message: str, severity: str = "error") -> Finding:
    return Finding(severity, code, str(path.resolve()), message)


def validate_required_paths(workspace: Path, manifest: Mapping[str, Any]) -> list[Finding]:
    """Check the fixed workspace layout and the one expected MOC file."""
    title = manifest.get("title")
    if not isinstance(title, str):
        paper = manifest.get("paper")
        title = paper.get("title") if isinstance(paper, Mapping) else ""
    moc_name = f"{sanitize_name(title if isinstance(title, str) else '')} - MOC.md"
    expected = ((moc_name, True), ("01-论文地图.md", True), ("02-双语对照", False),
                ("03-深度分析.md", True), ("04-知识地图.md", True),
                ("05-代码与复现.md", True), ("06-后续发展.md", True),
                ("07-互动学习记录.md", True), ("assets/figures", False),
                ("assets/tables", False), ("assets/paper-manifest.json", True))
    findings: list[Finding] = []
    for relative, expect_file in expected:
        path = workspace / relative
        if not path.exists():
            findings.append(_finding("missing-path", path, f"required path is missing: {relative}"))
        elif path.is_file() != expect_file:
            kind = "file" if expect_file else "directory"
            findings.append(_finding("wrong-path-kind", path, f"required path must be a {kind}: {relative}"))
    moc_candidates = sorted(
        (path.resolve() for path in workspace.rglob(moc_name) if path.is_file()),
        key=lambda path: path.as_posix().casefold(),
    )
    expected_moc = workspace / moc_name
    expected_resolved = expected_moc.resolve()
    if expected_resolved not in moc_candidates:
        findings.append(_finding("missing-path", expected_moc, f"required root MOC is missing: {moc_name}"))
    if len(moc_candidates) > 1:
        evidence = ", ".join(str(path) for path in moc_candidates)
        findings.append(_finding("duplicate-moc", expected_moc, f"duplicate titled MOC {moc_name}: {evidence}"))
    return findings


def validate_placeholders(documents: Iterable[MarkdownDocument]) -> list[Finding]:
    """Find unrendered template markers in Markdown files."""
    findings: list[Finding] = []
    for document in documents:
        for match in PLACEHOLDER_PATTERN.finditer("\n".join(document.original_lines)):
            findings.append(_finding("placeholder-token", document.path, f"unresolved placeholder {match.group(0)}"))
    return findings


def validate_block_ids(documents: Iterable[MarkdownDocument]) -> list[Finding]:
    """Report each repeated Obsidian block identifier with both locations."""
    locations: dict[str, list[tuple[Path, int]]] = {}
    for document in documents:
        for line_number, line in enumerate(document.masked_lines, start=1):
            match = re.search(r"(?:^|\s)\^([A-Za-z0-9_-]+)\s*$", line)
            if match:
                locations.setdefault(match.group(1), []).append((document.path, line_number))
    findings: list[Finding] = []
    for block_id, found in sorted(locations.items()):
        if len(found) > 1:
            evidence = ", ".join(f"{path.resolve()}:{line}" for path, line in found)
            findings.append(_finding("duplicate-block-id", found[0][0], f"duplicate block ID ^{block_id}: {evidence}"))
    return findings


def validate_bilingual_pairs(
    documents: Iterable[MarkdownDocument], workspace: Path
) -> list[Finding]:
    """Require paired -en/-zh block IDs only inside the bilingual directory."""
    bilingual_root = (workspace / "02-双语对照").resolve()
    pairs: dict[str, dict[str, tuple[Path, int]]] = {}
    for document in documents:
        if not _is_within(document.path.resolve(), bilingual_root):
            continue
        for line_number, line in enumerate(document.masked_lines, start=1):
            block_match = re.search(r"(?:^|\s)\^([A-Za-z0-9_-]+)\s*$", line)
            if not block_match:
                continue
            pair_match = re.fullmatch(r"(.+)-(en|zh)", block_match.group(1))
            if pair_match:
                pairs.setdefault(pair_match.group(1), {})[pair_match.group(2)] = (
                    document.path, line_number
                )
    findings: list[Finding] = []
    for base, sides in sorted(pairs.items()):
        for present, missing in (("en", "zh"), ("zh", "en")):
            if present in sides and missing not in sides:
                path, line_number = sides[present]
                findings.append(_finding(
                    "unpaired-bilingual-block-id",
                    path,
                    f"block ID ^{base}-{present} on line {line_number} requires matching "
                    f"^{base}-{missing} inside 02-双语对照",
                ))
    return findings


def _candidate_paths(base: Path, target: str) -> list[Path]:
    relative = Path(target.replace("\\", "/"))
    candidates = [base / relative]
    if not relative.suffix:
        candidates.append(base / f"{target}.md")
    return candidates


def _accepted_candidate(candidate: Path, vault: Path) -> bool:
    resolved = candidate.resolve()
    return _is_within(resolved, vault) and resolved.exists()


def _vault_basename_matches(vault: Path, target: str) -> list[Path]:
    if "/" in target or "\\" in target or not vault.is_dir():
        return []
    matches: list[Path] = []
    for path in vault.rglob("*"):
        if not path.exists():
            continue
        if (path.name == target or (not Path(target).suffix and path.stem == target)) and _accepted_candidate(path, vault):
            matches.append(path.resolve())
    return sorted(set(matches), key=lambda path: path.as_posix().casefold())


def _resolve_local_target(source: Path, target: str, workspace: Path, vault: Path) -> Path | None:
    """Resolve one local path without allowing absolute paths or Vault escape."""
    if not target:
        return source.resolve()
    raw_path = Path(target.replace("\\", "/"))
    if raw_path.is_absolute() or PureWindowsPath(target).is_absolute():
        return None
    if target.startswith("external:") or URL_PATTERN.match(target):
        return source.resolve()
    for base in (source.parent, workspace, vault):
        for candidate in _candidate_paths(base, target):
            if _accepted_candidate(candidate, vault):
                return candidate.resolve()
    matches = _vault_basename_matches(vault, target)
    return matches[0] if len(matches) == 1 else None


def _is_external_target(target: str) -> bool:
    """Recognize URL-like targets without misclassifying Windows absolute paths."""
    raw_path = Path(target.replace("\\", "/"))
    if raw_path.is_absolute() or PureWindowsPath(target).is_absolute():
        return False
    return target.startswith("external:") or bool(URL_PATTERN.match(target))


def _heading_keys(document: MarkdownDocument) -> set[str]:
    """Return exact and Markdown-slug forms for headings outside literal regions."""
    keys: set[str] = set()
    for line in document.masked_lines:
        match = re.match(r"^ {0,3}#{1,6}\s+(.+?)\s*#*\s*$", line)
        if not match:
            continue
        heading = " ".join(match.group(1).split()).strip()
        if not heading:
            continue
        keys.add(heading.casefold())
        slug = re.sub(r"[^\w\-\u0080-\uffff ]", "", heading, flags=re.UNICODE)
        keys.add(re.sub(r"[\s-]+", "-", slug).strip("-").casefold())
    return keys


def _block_ids(document: MarkdownDocument) -> set[str]:
    ids: set[str] = set()
    for line in document.masked_lines:
        match = re.search(r"(?:^|\s)\^([A-Za-z0-9_-]+)\s*$", line)
        if match:
            ids.add(match.group(1))
    return ids


def _split_target_and_anchor(value: str) -> tuple[str, str]:
    decoded = unquote(value.strip())
    if "#" not in decoded:
        return decoded, ""
    target, anchor = decoded.split("#", 1)
    return target.strip(), anchor.strip()


def _validate_anchor(
    source: MarkdownDocument,
    target_path: Path,
    anchor: str,
    documents_by_path: dict[Path, MarkdownDocument],
    unreadable_paths: set[Path],
    line_number: int,
) -> Finding | None:
    if not anchor:
        return None
    resolved_target = target_path.resolve()
    target_document = documents_by_path.get(resolved_target)
    if target_document is None and target_path.suffix.casefold() == ".md":
        if resolved_target in unreadable_paths:
            return None
        try:
            text = target_path.read_text(encoding="utf-8", errors="strict")
        except (OSError, UnicodeDecodeError) as error:
            unreadable_paths.add(resolved_target)
            return _finding(
                "markdown-read-error", target_path,
                f"cannot read Markdown as UTF-8: {error}",
            )
        target_document = MarkdownDocument(
            target_path, tuple(text.splitlines()), _mask_markdown_literals(text)
        )
        documents_by_path[resolved_target] = target_document
    if target_document is None:
        if target_path.suffix.casefold() != ".md":
            return None
        return _finding(
            "unresolved-heading-anchor", source.path,
            f"anchor target is not a readable Markdown note on line {line_number}: {anchor}",
        )
    if anchor.startswith("^"):
        block_id = anchor[1:]
        if block_id not in _block_ids(target_document):
            return _finding(
                "unresolved-block-anchor", source.path,
                f"unresolved block anchor '^{block_id}' on line {line_number}",
            )
        return None
    normalized = " ".join(anchor.split()).casefold()
    if normalized not in _heading_keys(target_document):
        return _finding(
            "unresolved-heading-anchor", source.path,
            f"unresolved heading anchor '{anchor}' on line {line_number}",
        )
    return None


def validate_wikilinks(
    documents: Iterable[MarkdownDocument],
    workspace: Path,
    vault: Path,
    documents_by_path: dict[Path, MarkdownDocument] | None = None,
    unreadable_paths: set[Path] | None = None,
) -> list[Finding]:
    """Resolve Obsidian links, including note heading and block anchors."""
    document_list = list(documents)
    if documents_by_path is None:
        documents_by_path = {
            document.path.resolve(): document for document in document_list
        }
    if unreadable_paths is None:
        unreadable_paths = set()
    findings: list[Finding] = []
    for document in document_list:
        for line_number, line in enumerate(document.masked_lines, start=1):
            for match in WIKILINK_PATTERN.finditer(line):
                link = match.group(1).strip()
                target, anchor = _split_target_and_anchor(link.split("|", 1)[0])
                if _is_external_target(target):
                    continue
                target_path = _resolve_local_target(document.path, target, workspace, vault)
                if target_path is None:
                    findings.append(_finding(
                        "unresolved-wikilink", document.path,
                        f"unresolved wikilink target '{target}' on line {line_number}",
                    ))
                    continue
                anchor_finding = _validate_anchor(
                    document, target_path, anchor, documents_by_path,
                    unreadable_paths, line_number
                )
                if anchor_finding is not None:
                    findings.append(anchor_finding)
    return findings


def _iter_markdown_destinations(line: str) -> Iterable[str]:
    """Yield inline-link bodies, respecting balanced destination parentheses."""
    for match in MARKDOWN_LINK_START_PATTERN.finditer(line):
        start = match.end()
        depth = 1
        index = start
        escaped = False
        while index < len(line):
            character = line[index]
            if escaped:
                escaped = False
            elif character == "\\":
                escaped = True
            elif character == "(":
                depth += 1
            elif character == ")":
                depth -= 1
                if depth == 0:
                    yield line[start:index]
                    break
            index += 1


def _markdown_destination(raw: str) -> str:
    """Extract the local destination from a CommonMark inline-link target."""
    value = raw.strip()
    if value.startswith("<") and ">" in value:
        return value[1:value.index(">")]
    title_match = re.match(
        r"^(.*?)(?:\s+(?:\"[^\"]*\"|'[^']*'|\([^()]*\)))\s*$", value
    )
    destination = title_match.group(1) if title_match else value
    return re.sub(r"\\([\\() ])", r"\1", destination.strip())


def validate_markdown_links(
    documents: Iterable[MarkdownDocument],
    workspace: Path,
    vault: Path,
    documents_by_path: dict[Path, MarkdownDocument] | None = None,
    unreadable_paths: set[Path] | None = None,
) -> list[Finding]:
    """Validate local Markdown note, image, PDF, and asset links plus anchors."""
    document_list = list(documents)
    if documents_by_path is None:
        documents_by_path = {
            document.path.resolve(): document for document in document_list
        }
    if unreadable_paths is None:
        unreadable_paths = set()
    findings: list[Finding] = []
    for document in document_list:
        for line_number, line in enumerate(document.masked_lines, start=1):
            for raw_destination in _iter_markdown_destinations(line):
                destination = unquote(_markdown_destination(raw_destination))
                if not destination or destination.startswith("#"):
                    target, anchor = "", destination[1:]
                else:
                    target, anchor = _split_target_and_anchor(destination)
                if _is_external_target(target):
                    continue
                target_path = _resolve_local_target(document.path, target, workspace, vault)
                if target_path is None:
                    findings.append(_finding(
                        "unresolved-markdown-link", document.path,
                        f"unresolved Markdown target '{target}' on line {line_number}",
                    ))
                    continue
                anchor_finding = _validate_anchor(
                    document, target_path, anchor, documents_by_path,
                    unreadable_paths, line_number
                )
                if anchor_finding is not None:
                    findings.append(anchor_finding)
    return findings


def validate_manifest_counts(workspace: Path, manifest: Mapping[str, Any]) -> list[Finding]:
    """Ensure manifest lists agree with their declared integer counts."""
    manifest_path = workspace / MANIFEST_RELATIVE
    structure = manifest.get("structure")
    counts = manifest.get("counts")
    if not isinstance(structure, Mapping) or not isinstance(counts, Mapping):
        return [_finding("invalid-manifest-structure", manifest_path, "structure and counts must be objects")]
    findings: list[Finding] = []
    for field in COUNT_FIELDS:
        values = structure.get(field)
        declared = counts.get(field)
        actual = len(values) if isinstance(values, list) else "not-a-list"
        if isinstance(declared, bool) or not isinstance(declared, int) or actual == "not-a-list" or declared != actual:
            findings.append(_finding(
                "manifest-count-mismatch", manifest_path,
                f"{field}: declared {declared!r}, actual {actual!r}",
            ))
    required_paths = structure.get("required_paths")
    declared_required = structure.get("required_paths_count")
    actual_required = len(required_paths) if isinstance(required_paths, list) else "not-a-list"
    if (isinstance(declared_required, bool) or not isinstance(declared_required, int)
            or actual_required == "not-a-list" or declared_required != actual_required):
        findings.append(_finding(
            "manifest-count-mismatch", manifest_path,
            f"required_paths_count: declared {declared_required!r}, actual {actual_required!r}",
        ))
    return findings


def validate_manifest_ownership(
    workspace: Path, manifest: Mapping[str, Any]
) -> list[Finding]:
    """Apply the same ownership/schema contract used by idempotent resume."""
    manifest_path = workspace / MANIFEST_RELATIVE
    return [
        _finding(
            "invalid-manifest-ownership",
            manifest_path,
            f"invalid {field}: {detail}",
        )
        for field, detail in manifest_contract_issues(workspace, manifest)
    ]


def validate_pdf_hash(workspace: Path, manifest: Mapping[str, Any]) -> list[Finding]:
    """Verify an optional copied PDF is contained, present, and unmodified."""
    manifest_path = workspace / MANIFEST_RELATIVE
    source = manifest.get("source")
    if not isinstance(source, Mapping):
        return [_finding("invalid-manifest-structure", manifest_path, "source must be an object")]
    copied_pdf = source.get("copied_pdf")
    if copied_pdf in (None, ""):
        return []
    if not isinstance(copied_pdf, str):
        return [_finding("missing-pdf", manifest_path, "copied_pdf must be a path string")]
    requested = Path(copied_pdf).expanduser()
    pdf_path = requested.resolve() if requested.is_absolute() else (workspace / requested).resolve()
    if not _is_within(pdf_path, workspace):
        return [_finding("pdf-outside-workspace", manifest_path, f"copied PDF is outside workspace: {copied_pdf}")]
    if not pdf_path.is_file():
        return [_finding("missing-pdf", manifest_path, f"copied PDF is missing: {copied_pdf}")]
    declared = source.get("sha256")
    if declared not in (None, ""):
        actual = sha256_file(pdf_path)
        if not isinstance(declared, str) or declared != actual or declared != declared.lower():
            return [_finding("pdf-hash-mismatch", manifest_path, f"sha256 mismatch for {copied_pdf}: declared {declared!r}, actual {actual}")]
    return []


def _frontmatter_properties(document: MarkdownDocument) -> dict[str, Any]:
    """Parse the initializer's JSON-compatible root frontmatter scalars."""
    if not document.original_lines or document.original_lines[0].strip() != "---":
        return {}
    properties: dict[str, Any] = {}
    for line in document.original_lines[1:]:
        if line.strip() == "---":
            break
        match = re.match(r"^([A-Za-z_][A-Za-z0-9_-]*):\s*(.*?)\s*$", line)
        if not match:
            continue
        raw = match.group(2)
        try:
            properties[match.group(1)] = json.loads(raw)
        except json.JSONDecodeError:
            properties[match.group(1)] = raw
    return properties


def validate_checkpoint_consistency(
    workspace: Path,
    manifest: Mapping[str, Any],
    documents: Iterable[MarkdownDocument],
) -> list[Finding]:
    """Keep manifest stage checkpoints synchronized with the MOC Properties."""
    manifest_path = workspace / MANIFEST_RELATIVE
    progress = manifest.get("progress")
    required = (
        "translation", "analysis", "knowledge", "code", "modern_context", "learning"
    )
    if not isinstance(progress, Mapping):
        return [_finding(
            "invalid-manifest-ownership", manifest_path,
            "invalid progress: must be an object",
        )]
    findings: list[Finding] = []
    for field in required:
        value = progress.get(field)
        if not isinstance(value, str) or not value:
            findings.append(_finding(
                "invalid-manifest-ownership", manifest_path,
                f"invalid progress.{field}: must be a nonempty string",
            ))
    if findings:
        return findings

    paper = manifest.get("paper")
    title = paper.get("title") if isinstance(paper, Mapping) else manifest.get("title")
    if not isinstance(title, str) or not title:
        return []
    moc_path = (workspace / f"{sanitize_name(title)} - MOC.md").resolve()
    document = next(
        (item for item in documents if item.path.resolve() == moc_path), None
    )
    if document is None:
        return []
    properties = _frontmatter_properties(document)
    field_map = {
        "translation_progress": "translation",
        "analysis_progress": "analysis",
        "learning_status": "learning",
    }
    published_mapping = {
        "translation": {
            "not-started": 0,
            "representative-only": "representative-only",
        },
        "analysis": {"not-started": 0, "trial-only": "trial-only"},
        "learning": {
            "not-started": "not-started",
            "awaiting-response": "awaiting-response",
        },
    }
    for moc_field, manifest_field in field_map.items():
        manifest_value = progress[manifest_field]
        actual = properties.get(moc_field)
        known_values = published_mapping[manifest_field]
        if moc_field not in properties or actual in (None, ""):
            findings.append(_finding(
                "checkpoint-mismatch", document.path,
                f"MOC {moc_field} must record a checkpoint value",
            ))
        elif manifest_value in known_values:
            expected = known_values[manifest_value]
            if actual != expected:
                findings.append(_finding(
                    "checkpoint-mismatch", document.path,
                    f"MOC {moc_field} is {actual!r}; manifest progress.{manifest_field} "
                    f"requires {expected!r}",
                ))
    moc_status = properties.get("status")
    if not isinstance(moc_status, str) or not moc_status:
        findings.append(_finding(
            "checkpoint-mismatch", document.path,
            "MOC status must be a nonempty string",
        ))
    elif moc_status == "initialized" and any(
        progress[field] != "not-started" for field in required
    ):
        findings.append(_finding(
            "checkpoint-mismatch", document.path,
            "MOC status 'initialized' is stale after manifest work has begun",
        ))
    return findings


def validate_workspace(workspace: Path, vault: Path | None = None) -> list[Finding]:
    """Run all validation rules after successfully loading the manifest."""
    workspace = _absolute(workspace)
    manifest = load_manifest(workspace)
    resolved_vault = validate_vault(workspace, vault)
    markdown_files = collect_markdown(workspace)
    markdown_documents, markdown_findings = load_markdown(markdown_files)
    documents_by_path = {
        document.path.resolve(): document for document in markdown_documents
    }
    unreadable_paths: set[Path] = set()
    findings = validate_manifest_ownership(workspace, manifest)
    findings.extend(validate_required_paths(workspace, manifest))
    findings.extend(markdown_findings)
    findings.extend(validate_placeholders(markdown_documents))
    findings.extend(validate_block_ids(markdown_documents))
    findings.extend(validate_bilingual_pairs(markdown_documents, workspace))
    findings.extend(validate_wikilinks(
        markdown_documents, workspace, resolved_vault,
        documents_by_path, unreadable_paths,
    ))
    findings.extend(validate_markdown_links(
        markdown_documents, workspace, resolved_vault,
        documents_by_path, unreadable_paths,
    ))
    findings.extend(validate_manifest_counts(workspace, manifest))
    findings.extend(validate_pdf_hash(workspace, manifest))
    findings.extend(validate_checkpoint_consistency(
        workspace, manifest, markdown_documents
    ))
    return sorted(findings, key=lambda item: (item.severity, item.code, item.path, item.message))


def infer_vault(workspace: Path) -> Path:
    """Choose a containing configured or Obsidian vault; otherwise stay local."""
    configured = _absolute(DEFAULT_VAULT)
    if configured.is_dir() and _is_within(workspace, configured):
        return configured
    for candidate in (workspace, *workspace.parents):
        if (candidate / ".obsidian").is_dir():
            return candidate
    return workspace


def validate_vault(workspace: Path, vault: Path | None) -> Path:
    """Resolve and prove the vault boundary used for local link resolution."""
    resolved_vault = _absolute(vault) if vault is not None else infer_vault(workspace)
    if not resolved_vault.is_dir():
        raise WorkspaceLoadingError("invalid-vault", workspace, "vault must be an existing directory")
    if not _is_within(workspace, resolved_vault):
        raise WorkspaceLoadingError("invalid-vault", workspace, "vault does not contain workspace")
    return resolved_vault


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = JsonArgumentParser(description=__doc__)
    parser.add_argument("workspace", type=Path)
    parser.add_argument("--vault", type=Path)
    parser.add_argument("--json", action="store_true")
    return parser.parse_args(argv)


def _payload(status: str, workspace: Path, findings: Iterable[Finding]) -> dict[str, Any]:
    return {"status": status, "workspace": str(workspace.resolve()), "findings": [asdict(item) for item in findings]}


def _emit(payload: Mapping[str, Any], as_json: bool) -> None:
    if as_json:
        print(json.dumps(payload, ensure_ascii=False))
        return
    print(f"{payload['status'].upper()}: {payload['workspace']}")
    for finding in payload["findings"]:
        print(f"{finding['severity'].upper()} {finding['code']} {finding['path']}: {finding['message']}")


def main(argv: list[str] | None = None) -> int:
    raw_argv = list(sys.argv[1:] if argv is None else argv)
    wants_json = "--json" in raw_argv
    fallback = Path.cwd().resolve()
    workspace = fallback
    try:
        args = parse_args(raw_argv)
        workspace = _absolute(args.workspace)
        findings = validate_workspace(workspace, args.vault)
    except WorkspaceLoadingError as error:
        finding = _finding(error.code, error.path, error.message)
        _emit(_payload("error", workspace, [finding]), wants_json)
        return 2
    except OSError as error:
        finding = _finding("workspace-load-failed", fallback, str(error) or error.__class__.__name__)
        _emit(_payload("error", fallback, [finding]), wants_json)
        return 2
    status = "invalid" if any(item.severity == "error" for item in findings) else "ok"
    _emit(_payload(status, workspace, findings), args.json)
    return 1 if status == "invalid" else 0


if __name__ == "__main__":
    raise SystemExit(main())
