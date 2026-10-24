"""Black-box regression tests for the learn-cs-paper workspace scripts."""

import hashlib
import json
import errno
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import unittest


SKILL_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = SKILL_ROOT / "scripts"
INITIALIZER = SCRIPTS_DIR / "init-paper-workspace.py"
VALIDATOR = SCRIPTS_DIR / "validate-paper-workspace.py"
COLLECTION = "论文/机器学习"
TITLE = "Attention Is All You Need"
MOC_NAME = f"{TITLE} - MOC.md"


class WorkspaceScriptsTests(unittest.TestCase):
    """Exercise command-line contracts against isolated temporary vaults."""

    def run_script(self, script, *args):
        """Run a script without converting a nonzero exit into an exception."""
        return subprocess.run(
            [sys.executable, str(script), *map(str, args)],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="strict",
            check=False,
        )

    @staticmethod
    def diagnostics(result):
        return f"stdout:\n{result.stdout}\nstderr:\n{result.stderr}"

    def parse_json_object(self, result, label):
        try:
            payload = json.loads(result.stdout)
        except json.JSONDecodeError as error:
            self.fail(
                f"{label} did not emit a JSON object: {error}; "
                f"{self.diagnostics(result)}"
            )
        self.assertIsInstance(payload, dict, self.diagnostics(result))
        return payload

    def assert_nonempty_string_field(self, payload, field, result):
        self.assertIn(field, payload, self.diagnostics(result))
        value = payload[field]
        self.assertIsInstance(value, str, self.diagnostics(result))
        self.assertTrue(value, self.diagnostics(result))
        return value

    def assert_workspace_under_vault(self, workspace_value, vault, result):
        workspace = Path(workspace_value).resolve()
        vault_root = Path(vault).resolve()
        try:
            workspace.relative_to(vault_root)
        except ValueError:
            self.fail(
                f"reported workspace {workspace} is outside vault {vault_root}; "
                f"{self.diagnostics(result)}"
            )
        return workspace

    def initializer_args(self, vault, pdf=None):
        args = [
            "--vault",
            vault,
            "--collection",
            COLLECTION,
            "--title",
            TITLE,
            "--source",
            "test-fixture",
            "--doi",
            "10.48550/arXiv.1706.03762",
            "--arxiv",
            "1706.03762",
            "--year",
            "2017",
            "--skill-version",
            "1.0.0",
            "--json",
        ]
        if pdf is not None:
            args.extend(["--source-pdf", pdf])
        return args

    def init_workspace(self, vault, pdf=None):
        """Initialize the standard fixture workspace and return its path."""
        result = self.run_script(INITIALIZER, *self.initializer_args(vault, pdf))
        self.assertEqual(result.returncode, 0, self.diagnostics(result))
        payload = self.parse_json_object(result, "initializer success")
        self.assertEqual(payload.get("status"), "ok", self.diagnostics(result))
        workspace_value = self.assert_nonempty_string_field(payload, "workspace", result)
        return self.assert_workspace_under_vault(workspace_value, vault, result)

    def assert_initializer_error(self, result, vault, expected_code, expected_workspace):
        self.assertNotEqual(result.returncode, 0, self.diagnostics(result))
        payload = self.parse_json_object(result, "initializer failure")
        self.assertEqual(payload.get("status"), "error", self.diagnostics(result))
        self.assertEqual(payload.get("code"), expected_code, self.diagnostics(result))
        workspace_value = self.assert_nonempty_string_field(payload, "workspace", result)
        reported_workspace = self.assert_workspace_under_vault(
            workspace_value, vault, result
        )
        self.assertEqual(
            reported_workspace, expected_workspace.resolve(), self.diagnostics(result)
        )
        self.assert_nonempty_string_field(payload, "message", result)

    def validate_workspace(self, workspace, vault):
        result = self.run_script(VALIDATOR, workspace, "--vault", vault, "--json")
        payload = self.parse_json_object(result, "validator")
        self.assert_nonempty_string_field(payload, "status", result)
        workspace_value = self.assert_nonempty_string_field(payload, "workspace", result)
        reported_workspace = self.assert_workspace_under_vault(
            workspace_value, vault, result
        )
        self.assertEqual(reported_workspace, workspace.resolve(), self.diagnostics(result))
        self.assertIn("findings", payload, self.diagnostics(result))
        findings = payload["findings"]
        self.assertIsInstance(findings, list, self.diagnostics(result))
        for finding in findings:
            self.assertIsInstance(finding, dict, self.diagnostics(result))
            self.assert_nonempty_string_field(finding, "severity", result)
            self.assert_nonempty_string_field(finding, "code", result)
            self.assert_nonempty_string_field(finding, "path", result)
            self.assert_nonempty_string_field(finding, "message", result)
        return result, payload

    def assert_error_finding(self, payload, result, code, path, evidence):
        matches = [
            finding
            for finding in payload["findings"]
            if finding["code"] == code and finding["severity"] == "error"
        ]
        self.assertTrue(matches, self.diagnostics(result))
        evidence_matches = [
            finding for finding in matches if evidence in finding["message"]
        ]
        self.assertTrue(evidence_matches, self.diagnostics(result))
        finding = evidence_matches[0]
        self.assertEqual(finding["path"], str(path.resolve()), self.diagnostics(result))

    @staticmethod
    def rewrite_manifest(workspace, mutate):
        """Apply one test mutation to the real manifest and write strict UTF-8 JSON."""
        manifest_path = workspace / "assets" / "paper-manifest.json"
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        mutate(manifest)
        manifest_path.write_text(
            json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        return manifest_path

    @staticmethod
    def replace_frontmatter_value(path, key, value):
        """Replace one root frontmatter scalar while preserving the note body."""
        text = path.read_text(encoding="utf-8")
        replacement = json.dumps(value, ensure_ascii=False)
        updated, count = re.subn(
            rf"(?m)^{re.escape(key)}: .*?$", f"{key}: {replacement}", text, count=1
        )
        if count != 1:
            raise AssertionError(f"frontmatter field not found exactly once: {key}")
        path.write_text(updated, encoding="utf-8")

    def test_init_creates_required_workspace_and_manifest(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            vault = Path(temp_dir) / "vault"
            workspace = self.init_workspace(vault)

            required_files = [
                workspace / MOC_NAME,
                workspace / "01-论文地图.md",
                workspace / "03-深度分析.md",
                workspace / "04-知识地图.md",
                workspace / "05-代码与复现.md",
                workspace / "06-后续发展.md",
                workspace / "07-互动学习记录.md",
                workspace / "assets" / "paper-manifest.json",
            ]
            required_directories = [
                workspace / "02-双语对照",
                workspace / "assets" / "figures",
                workspace / "assets" / "tables",
            ]
            for path in required_files:
                self.assertTrue(path.is_file(), str(path))
            for path in required_directories:
                self.assertTrue(path.is_dir(), str(path))

            manifest = json.loads(
                (workspace / "assets" / "paper-manifest.json").read_text(
                    encoding="utf-8"
                )
            )
            self.assertEqual(manifest["title"], TITLE)
            self.assertEqual(manifest["doi"], "10.48550/arXiv.1706.03762")
            self.assertEqual(manifest["arxiv"], "1706.03762")
            self.assertEqual(manifest["year"], "2017")
            self.assertIsInstance(manifest["source"], dict)
            self.assertEqual(manifest["source"]["reference"], "test-fixture")
            self.assertEqual(manifest["source"]["original_pdf"], "")
            self.assertEqual(manifest["source"]["copied_pdf"], "")
            self.assertEqual(manifest["source"]["sha256"], "")
            self.assertIsNone(manifest["source"]["page_count"])
            self.assertTrue(manifest["source"]["retrieved_at"])
            self.assertEqual(manifest["skill_version"], "1.0.0")
            self.assertEqual(manifest["skill"]["version"], "1.0.0")
            moc_text = (workspace / MOC_NAME).read_text(encoding="utf-8")
            self.assertIn("focus: []", moc_text)
            self.assertIn("translation_progress: 0", moc_text)
            self.assertIn("analysis_progress: 0", moc_text)
            self.assertIn("  - paper/computer-science", moc_text)
            self.assertIn("PDF：未提供 PDF", moc_text)
            self.assertNotIn("[原始论文]()", moc_text)
            source_pdf_line = next(
                line for line in moc_text.split("---", 2)[1].splitlines()
                if line.startswith("source_pdf: ")
            )
            self.assertEqual(json.loads(source_pdf_line.split(": ", 1)[1]), "")

    def test_reinitialize_preserves_manual_content(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            vault = Path(temp_dir) / "vault"
            workspace = self.init_workspace(vault)
            moc = workspace / MOC_NAME
            manual_line = "\n手工保留内容：不可覆盖。\n"
            with moc.open("a", encoding="utf-8", newline="") as file:
                file.write(manual_line)
            before = moc.read_bytes()

            second_workspace = self.init_workspace(vault)

            self.assertEqual(second_workspace, workspace)
            self.assertEqual(moc.read_bytes(), before)

    def test_omitted_skill_version_uses_canonical_installed_default(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            vault = Path(temp_dir) / "vault"
            args = [
                "--vault", vault,
                "--collection", COLLECTION,
                "--title", TITLE,
                "--source", "test-fixture",
                "--json",
            ]

            result = self.run_script(INITIALIZER, *args)

            self.assertEqual(result.returncode, 0, self.diagnostics(result))
            payload = self.parse_json_object(result, "default skill version")
            workspace = self.assert_workspace_under_vault(payload["workspace"], vault, result)
            manifest = json.loads(
                (workspace / "assets" / "paper-manifest.json").read_text(encoding="utf-8")
            )
            self.assertEqual(manifest["skill"]["version"], "1.0.0")
            self.assertEqual(manifest["skill_version"], "1.0.0")

    def test_rejects_noncanonical_explicit_skill_version_before_write(self):
        for invalid_version in ("", "test", "1.0.0-01"):
            with self.subTest(invalid_version=invalid_version):
                with tempfile.TemporaryDirectory() as temp_dir:
                    vault = Path(temp_dir) / "vault"
                    args = self.initializer_args(vault)
                    version_index = args.index("--skill-version") + 1
                    args[version_index] = invalid_version

                    result = self.run_script(INITIALIZER, *args)

                    self.assertNotEqual(result.returncode, 0, self.diagnostics(result))
                    payload = self.parse_json_object(result, "invalid skill version")
                    self.assertEqual(payload["code"], "invalid-skill-version", self.diagnostics(result))
                    self.assertFalse(vault.exists(), self.diagnostics(result))

    def test_existing_manifest_with_wrong_skill_refuses_takeover(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            vault = Path(temp_dir) / "vault"
            workspace = self.init_workspace(vault)
            manifest_path = workspace / "assets" / "paper-manifest.json"
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            manifest["skill"]["name"] = "unrelated-skill"
            manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

            result = self.run_script(INITIALIZER, *self.initializer_args(vault))

            self.assert_initializer_error(result, vault, "invalid-manifest-ownership", workspace)
            self.assertIn("skill.name", result.stdout, self.diagnostics(result))

    def test_existing_manifest_with_wrong_title_refuses_takeover(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            vault = Path(temp_dir) / "vault"
            workspace = self.init_workspace(vault)
            manifest_path = workspace / "assets" / "paper-manifest.json"
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            manifest["paper"]["title"] = "A Different Paper"
            manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

            result = self.run_script(INITIALIZER, *self.initializer_args(vault))

            self.assert_initializer_error(result, vault, "invalid-manifest-ownership", workspace)
            self.assertIn("paper.title", result.stdout, self.diagnostics(result))

    def test_existing_manifest_with_wrong_root_refuses_takeover(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            vault = Path(temp_dir) / "vault"
            workspace = self.init_workspace(vault)
            manifest_path = workspace / "assets" / "paper-manifest.json"
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            manifest["workspace"]["root"] = str((vault / "other-workspace").resolve())
            manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

            result = self.run_script(INITIALIZER, *self.initializer_args(vault))

            self.assert_initializer_error(result, vault, "invalid-manifest-ownership", workspace)
            self.assertIn("workspace.root", result.stdout, self.diagnostics(result))

    def test_existing_manifest_with_wrong_schema_refuses_takeover(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            vault = Path(temp_dir) / "vault"
            workspace = self.init_workspace(vault)
            manifest_path = workspace / "assets" / "paper-manifest.json"
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            manifest["schema_version"] = 999
            manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

            result = self.run_script(INITIALIZER, *self.initializer_args(vault))

            self.assert_initializer_error(result, vault, "invalid-manifest-ownership", workspace)
            self.assertIn("schema_version", result.stdout, self.diagnostics(result))

    def test_existing_manifest_with_malformed_hash_refuses_takeover(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            vault = Path(temp_dir) / "vault"
            workspace = self.init_workspace(vault)
            manifest_path = workspace / "assets" / "paper-manifest.json"
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            manifest["source"]["sha256"] = "not-a-sha256"
            manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

            result = self.run_script(INITIALIZER, *self.initializer_args(vault))

            self.assert_initializer_error(result, vault, "invalid-manifest-ownership", workspace)
            self.assertIn("source.sha256", result.stdout, self.diagnostics(result))

    def test_pdf_hash_change_creates_versioned_workspace(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            vault = temp_path / "vault"
            first_pdf = temp_path / "first.pdf"
            second_pdf = temp_path / "second.pdf"
            first_pdf.write_bytes(b"first fake PDF fixture")
            second_pdf.write_bytes(b"second fake PDF fixture")

            first_workspace = self.init_workspace(vault, first_pdf)
            second_workspace = self.init_workspace(vault, second_pdf)

            self.assertNotEqual(first_workspace, second_workspace)
            self.assertTrue(first_workspace.is_dir())
            self.assertTrue(second_workspace.is_dir())
            second_hash_prefix = hashlib.sha256(second_pdf.read_bytes()).hexdigest()[:8]
            self.assertIn(second_hash_prefix, second_workspace.name)

    def test_existing_directory_without_manifest_refuses_takeover(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            vault = Path(temp_dir) / "vault"
            existing = vault / Path(*COLLECTION.split("/")) / TITLE
            existing.mkdir(parents=True)
            manual_file = existing / "manual.md"
            manual_file.write_text("Do not overwrite me.\n", encoding="utf-8")

            result = self.run_script(INITIALIZER, *self.initializer_args(vault))

            self.assert_initializer_error(
                result, vault, "workspace-without-manifest", existing
            )
            self.assertEqual(
                manual_file.read_text(encoding="utf-8"), "Do not overwrite me.\n"
            )

    def test_pdf_copy_creates_relative_moc_link_and_nested_source_record(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            vault = temp_path / "vault"
            source_pdf = temp_path / "source.pdf"
            source_pdf.write_bytes(b"%PDF-1.4 fixture")
            workspace = self.init_workspace(vault, source_pdf)

            manifest = json.loads(
                (workspace / "assets" / "paper-manifest.json").read_text(encoding="utf-8")
            )
            source = manifest["source"]
            copied = Path(source["copied_pdf"])
            self.assertTrue(copied.is_file())
            self.assertEqual(source["original_pdf"], str(source_pdf.resolve()))
            self.assertEqual(source["sha256"], hashlib.sha256(source_pdf.read_bytes()).hexdigest())
            relative = copied.relative_to(workspace).as_posix()
            moc_text = (workspace / MOC_NAME).read_text(encoding="utf-8")
            self.assertIn(f"PDF：[原始论文]({relative})", moc_text)
            source_pdf_line = next(
                line for line in moc_text.split("---", 2)[1].splitlines()
                if line.startswith("source_pdf: ")
            )
            self.assertEqual(json.loads(source_pdf_line.split(": ", 1)[1]), relative)

    def test_initializer_creates_moc_with_obsidian_wikilinks_for_internal_entries(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            vault = temp_path / "vault"
            source_pdf = temp_path / "source.pdf"
            source_pdf.write_bytes(b"%PDF-1.4 wikilink fixture")
            workspace = self.init_workspace(vault, source_pdf)

            moc_text = (workspace / MOC_NAME).read_text(encoding="utf-8")
            expected_wikilinks = {
                "[[01-论文地图|论文地图]]",
                "[[03-深度分析|深度分析]]",
                "[[04-知识地图|知识地图]]",
                "[[05-代码与复现|代码与复现]]",
                "[[06-后续发展|后续发展]]",
                "[[07-互动学习记录|互动学习记录]]",
            }
            for wikilink in expected_wikilinks:
                self.assertIn(wikilink, moc_text)
            emitted_wikilinks = {
                match.group(0)
                for match in re.finditer(r"!?\[\[[^\]]+\]\]", moc_text)
            }
            self.assertEqual(emitted_wikilinks, expected_wikilinks)
            self.assertIn("[manifest](assets/paper-manifest.json)", moc_text)
            self.assertIn("[双语对照目录](02-双语对照/)", moc_text)

            result, payload = self.validate_workspace(workspace, vault)
            self.assertEqual(result.returncode, 0, self.diagnostics(result))
            self.assertEqual(payload["status"], "ok", self.diagnostics(result))

    def test_rejects_collection_traversal_without_outside_write(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            vault = temp_path / "vault"
            outside = temp_path / "escaped"
            result = self.run_script(
                INITIALIZER,
                "--vault", vault,
                "--collection", "..\\escaped",
                "--title", "Traversal Test",
                "--json",
            )

            self.assertNotEqual(result.returncode, 0, self.diagnostics(result))
            payload = self.parse_json_object(result, "collection traversal")
            self.assertEqual(payload["status"], "error", self.diagnostics(result))
            self.assertEqual(payload["code"], "invalid-collection", self.diagnostics(result))
            self.assert_workspace_under_vault(payload["workspace"], vault, result)
            self.assertFalse(outside.exists(), self.diagnostics(result))

    def test_json_parse_errors_are_single_json_object_under_vault(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            vault = Path(temp_dir) / "vault"
            result = self.run_script(INITIALIZER, "--vault", vault, "--json")

            self.assertNotEqual(result.returncode, 0, self.diagnostics(result))
            decoder = json.JSONDecoder()
            payload, end = decoder.raw_decode(result.stdout)
            self.assertFalse(result.stdout[end:].strip(), self.diagnostics(result))
            self.assertEqual(payload["status"], "error", self.diagnostics(result))
            self.assertEqual(payload["code"], "invalid-arguments", self.diagnostics(result))
            self.assert_workspace_under_vault(payload["workspace"], vault, result)
            self.assertTrue(result.stderr, self.diagnostics(result))

    def test_json_missing_vault_value_uses_configured_default_vault(self):
        result = self.run_script(INITIALIZER, "--vault", "--json")

        self.assertNotEqual(result.returncode, 0, self.diagnostics(result))
        payload = self.parse_json_object(result, "missing vault value")
        self.assertEqual(payload["status"], "error", self.diagnostics(result))
        self.assertEqual(payload["code"], "invalid-arguments", self.diagnostics(result))
        self.assert_workspace_under_vault(
            payload["workspace"],
            Path(r"D:\Markdown\Obsidian\Obsidian-Notes"),
            result,
        )

    def test_json_repeated_vault_uses_last_valid_value_during_parse_failure(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            first_vault = temp_path / "first-vault"
            last_vault = temp_path / "last-vault"
            result = self.run_script(
                INITIALIZER,
                "--vault", first_vault,
                f"--vault={last_vault}",
                "--unknown",
                "--json",
            )

            self.assertNotEqual(result.returncode, 0, self.diagnostics(result))
            payload = self.parse_json_object(result, "repeated vault parse failure")
            self.assertEqual(payload["status"], "error", self.diagnostics(result))
            self.assertEqual(payload["code"], "invalid-arguments", self.diagnostics(result))
            self.assert_workspace_under_vault(payload["workspace"], last_vault, result)
            self.assertFalse(first_vault.exists(), self.diagnostics(result))

    def test_missing_pdf_returns_json_error_before_workspace_write(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            vault = temp_path / "vault"
            missing_pdf = temp_path / "missing.pdf"
            result = self.run_script(INITIALIZER, *self.initializer_args(vault, missing_pdf))

            self.assertNotEqual(result.returncode, 0, self.diagnostics(result))
            payload = self.parse_json_object(result, "missing PDF")
            self.assertEqual(payload["status"], "error", self.diagnostics(result))
            self.assertEqual(payload["code"], "initialization-failed", self.diagnostics(result))
            self.assert_workspace_under_vault(payload["workspace"], vault, result)
            self.assertFalse(vault.exists(), self.diagnostics(result))

    def test_preexisting_workspace_lock_refuses_initialization(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            vault = Path(temp_dir) / "vault"
            workspace = vault / Path(*COLLECTION.split("/")) / TITLE
            workspace.mkdir(parents=True)
            (workspace / ".learn-cs-paper.lock").write_text("busy\n", encoding="utf-8")

            result = self.run_script(INITIALIZER, *self.initializer_args(vault))

            self.assert_initializer_error(result, vault, "workspace-locked", workspace)
            self.assertFalse((workspace / "assets" / "paper-manifest.json").exists())

    def test_yaml_frontmatter_uses_json_scalars_and_normalized_markdown_text(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            vault = Path(temp_dir) / "vault"
            title = 'A "Quoted": O\'Brien\\Path\nNext'
            doi = '10.1000/"quoted":\\path\nnext'
            arxiv = 'arXiv:"test"\\value\nnext'
            year = "2020:\nnext"
            result = self.run_script(
                INITIALIZER,
                "--vault", vault,
                "--collection", COLLECTION,
                "--title", title,
                "--source", 'Source: "quoted"\\path\nnext',
                "--doi", doi,
                "--arxiv", arxiv,
                "--year", year,
                "--json",
            )
            self.assertEqual(result.returncode, 0, self.diagnostics(result))
            payload = self.parse_json_object(result, "yaml escaping")
            workspace = self.assert_workspace_under_vault(payload["workspace"], vault, result)
            moc = next(workspace.glob("* - MOC.md"))
            frontmatter = moc.read_text(encoding="utf-8").split("---", 2)[1].strip().splitlines()
            scalar_values = {}
            for key in ("title", "year", "doi", "arxiv", "source_pdf", "created", "updated"):
                line = next(line for line in frontmatter if line.startswith(f"{key}: "))
                scalar_values[key] = json.loads(line.split(": ", 1)[1])
            alias_line = next(line for line in frontmatter if line.startswith("  - "))
            alias = json.loads(alias_line[4:])
            normalized_title = 'A "Quoted": O\'Brien\\Path Next'
            self.assertEqual(scalar_values["title"], normalized_title)
            self.assertEqual(alias, normalized_title)
            self.assertEqual(scalar_values["doi"], '10.1000/"quoted":\\path next')
            self.assertEqual(scalar_values["arxiv"], 'arXiv:"test"\\value next')
            self.assertEqual(scalar_values["year"], "2020: next")
            self.assertNotIn("\nNext", moc.read_text(encoding="utf-8"))

    def test_validator_accepts_initialized_workspace(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            vault = Path(temp_dir) / "vault"
            workspace = self.init_workspace(vault)

            result, payload = self.validate_workspace(workspace, vault)

            self.assertEqual(result.returncode, 0, self.diagnostics(result))
            self.assertEqual(payload["status"], "ok", self.diagnostics(result))
            self.assertFalse(
                [
                    finding
                    for finding in payload["findings"]
                    if finding["severity"] == "error"
                ],
                self.diagnostics(result),
            )

    def test_validator_rejects_wrong_manifest_schema_version(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            vault = Path(temp_dir) / "vault"
            workspace = self.init_workspace(vault)
            manifest_path = self.rewrite_manifest(
                workspace, lambda manifest: manifest.__setitem__("schema_version", 2)
            )

            result, payload = self.validate_workspace(workspace, vault)

            self.assertEqual(result.returncode, 1, self.diagnostics(result))
            self.assert_error_finding(
                payload, result, "invalid-manifest-ownership", manifest_path, "schema_version"
            )

    def test_validator_rejects_wrong_manifest_skill_name(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            vault = Path(temp_dir) / "vault"
            workspace = self.init_workspace(vault)
            manifest_path = self.rewrite_manifest(
                workspace,
                lambda manifest: manifest["skill"].__setitem__("name", "other-skill"),
            )

            result, payload = self.validate_workspace(workspace, vault)

            self.assertEqual(result.returncode, 1, self.diagnostics(result))
            self.assert_error_finding(
                payload, result, "invalid-manifest-ownership", manifest_path, "skill.name"
            )

    def test_validator_rejects_invalid_or_inconsistent_manifest_version(self):
        mutations = (
            (
                "non-semver",
                lambda manifest: manifest["skill"].__setitem__("version", "latest"),
                "skill.version",
            ),
            (
                "top-level-mismatch",
                lambda manifest: manifest.__setitem__("skill_version", "2.0.0"),
                "skill_version",
            ),
        )
        for label, mutate, evidence in mutations:
            with self.subTest(label=label), tempfile.TemporaryDirectory() as temp_dir:
                vault = Path(temp_dir) / "vault"
                workspace = self.init_workspace(vault)
                manifest_path = self.rewrite_manifest(workspace, mutate)

                result, payload = self.validate_workspace(workspace, vault)

                self.assertEqual(result.returncode, 1, self.diagnostics(result))
                self.assert_error_finding(
                    payload, result, "invalid-manifest-ownership", manifest_path, evidence
                )

    def test_validator_rejects_manifest_title_mismatch(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            vault = Path(temp_dir) / "vault"
            workspace = self.init_workspace(vault)
            manifest_path = self.rewrite_manifest(
                workspace,
                lambda manifest: manifest["paper"].__setitem__("title", "Different Paper"),
            )

            result, payload = self.validate_workspace(workspace, vault)

            self.assertEqual(result.returncode, 1, self.diagnostics(result))
            self.assert_error_finding(
                payload, result, "invalid-manifest-ownership", manifest_path, "paper.title"
            )

    def test_validator_rejects_wrong_manifest_workspace_root(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            vault = Path(temp_dir) / "vault"
            workspace = self.init_workspace(vault)
            manifest_path = self.rewrite_manifest(
                workspace,
                lambda manifest: manifest["workspace"].__setitem__(
                    "root", str((vault / "different-workspace").resolve())
                ),
            )

            result, payload = self.validate_workspace(workspace, vault)

            self.assertEqual(result.returncode, 1, self.diagnostics(result))
            self.assert_error_finding(
                payload, result, "invalid-manifest-ownership", manifest_path, "workspace.root"
            )

    def test_validator_rejects_invalid_manifest_source_fields(self):
        mutations = (
            (
                "reference-type",
                lambda manifest: manifest["source"].__setitem__("reference", 42),
                "source.reference",
            ),
            (
                "empty-retrieved-at",
                lambda manifest: manifest["source"].__setitem__("retrieved_at", ""),
                "source.retrieved_at",
            ),
            (
                "zero-page-count",
                lambda manifest: manifest["source"].__setitem__("page_count", 0),
                "source.page_count",
            ),
        )
        for label, mutate, evidence in mutations:
            with self.subTest(label=label), tempfile.TemporaryDirectory() as temp_dir:
                vault = Path(temp_dir) / "vault"
                workspace = self.init_workspace(vault)
                manifest_path = self.rewrite_manifest(workspace, mutate)

                result, payload = self.validate_workspace(workspace, vault)

                self.assertEqual(result.returncode, 1, self.diagnostics(result))
                self.assert_error_finding(
                    payload, result, "invalid-manifest-ownership", manifest_path, evidence
                )

    def test_validator_rejects_manifest_pdf_hash_presence_invariant(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            vault = temp_path / "vault"
            source_pdf = temp_path / "source.pdf"
            source_pdf.write_bytes(b"PDF ownership fixture")
            workspace = self.init_workspace(vault, source_pdf)
            manifest_path = self.rewrite_manifest(
                workspace,
                lambda manifest: manifest["source"].__setitem__("sha256", ""),
            )

            result, payload = self.validate_workspace(workspace, vault)

            self.assertEqual(result.returncode, 1, self.diagnostics(result))
            self.assert_error_finding(
                payload, result, "invalid-manifest-ownership", manifest_path, "source"
            )

    def test_validator_rejects_missing_required_file(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            vault = Path(temp_dir) / "vault"
            workspace = self.init_workspace(vault)
            missing_path = workspace / "03-深度分析.md"
            missing_path.unlink()

            result, payload = self.validate_workspace(workspace, vault)

            self.assertNotEqual(result.returncode, 0, self.diagnostics(result))
            self.assertEqual(payload["status"], "invalid", self.diagnostics(result))
            self.assert_error_finding(
                payload, result, "missing-path", missing_path, "03-深度分析.md"
            )

    def test_validator_checks_generated_moc_wikilinks(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            vault = Path(temp_dir) / "vault"
            workspace = self.init_workspace(vault)
            missing_path = workspace / "03-深度分析.md"
            missing_path.unlink()
            moc_path = workspace / MOC_NAME

            result, payload = self.validate_workspace(workspace, vault)

            self.assertNotEqual(result.returncode, 0, self.diagnostics(result))
            self.assertEqual(payload["status"], "invalid", self.diagnostics(result))
            self.assert_error_finding(
                payload, result, "unresolved-wikilink", moc_path, "03-深度分析"
            )

    def test_validator_rejects_duplicate_block_ids(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            vault = Path(temp_dir) / "vault"
            workspace = self.init_workspace(vault)
            analysis_path = workspace / "03-深度分析.md"
            knowledge_path = workspace / "04-知识地图.md"
            for path in (analysis_path, knowledge_path):
                with path.open("a", encoding="utf-8", newline="") as file:
                    file.write("\n^duplicate-fixture-id\n")

            result, payload = self.validate_workspace(workspace, vault)

            self.assertNotEqual(result.returncode, 0, self.diagnostics(result))
            self.assertEqual(payload["status"], "invalid", self.diagnostics(result))
            matches = [
                finding
                for finding in payload["findings"]
                if finding["code"] == "duplicate-block-id"
                and finding["severity"] == "error"
            ]
            self.assertTrue(matches, self.diagnostics(result))
            finding = matches[0]
            self.assertIn(
                finding["path"], {str(analysis_path.resolve()), str(knowledge_path.resolve())},
                self.diagnostics(result),
            )
            self.assertIn("duplicate-fixture-id", finding["message"], self.diagnostics(result))

    def test_validator_accepts_paired_bilingual_block_ids(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            vault = Path(temp_dir) / "vault"
            workspace = self.init_workspace(vault)
            bilingual = workspace / "02-双语对照" / "00-摘要.md"
            bilingual.write_text(
                "# 摘要\n\nEnglish paragraph. ^abstract-p1-en\n\n"
                "中文段落。 ^abstract-p1-zh\n",
                encoding="utf-8",
            )

            result, payload = self.validate_workspace(workspace, vault)

            self.assertEqual(result.returncode, 0, self.diagnostics(result))
            self.assertEqual(payload["status"], "ok", self.diagnostics(result))
            self.assertFalse(payload["findings"], self.diagnostics(result))

    def test_validator_rejects_orphan_bilingual_block_ids(self):
        for suffix, missing_suffix in (("en", "zh"), ("zh", "en")):
            with self.subTest(suffix=suffix), tempfile.TemporaryDirectory() as temp_dir:
                vault = Path(temp_dir) / "vault"
                workspace = self.init_workspace(vault)
                bilingual = workspace / "02-双语对照" / "00-摘要.md"
                bilingual.write_text(
                    f"# 摘要\n\nOnly one side. ^abstract-p1-{suffix}\n",
                    encoding="utf-8",
                )

                result, payload = self.validate_workspace(workspace, vault)

                self.assertEqual(result.returncode, 1, self.diagnostics(result))
                self.assert_error_finding(
                    payload,
                    result,
                    "unpaired-bilingual-block-id",
                    bilingual,
                    f"abstract-p1-{missing_suffix}",
                )

    def test_validator_ignores_translation_shaped_block_id_outside_bilingual_directory(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            vault = Path(temp_dir) / "vault"
            workspace = self.init_workspace(vault)
            analysis = workspace / "03-深度分析.md"
            with analysis.open("a", encoding="utf-8", newline="") as file:
                file.write("\nEvidence label ^analysis-only-en\n")

            result, payload = self.validate_workspace(workspace, vault)

            self.assertEqual(result.returncode, 0, self.diagnostics(result))
            self.assertEqual(payload["status"], "ok", self.diagnostics(result))
            self.assertFalse(payload["findings"], self.diagnostics(result))

    def test_validator_rejects_placeholder_tokens(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            vault = Path(temp_dir) / "vault"
            workspace = self.init_workspace(vault)
            target_path = workspace / "03-深度分析.md"
            with target_path.open("a", encoding="utf-8", newline="") as file:
                file.write("\n{{UNRESOLVED_TOKEN}}\n")

            result, payload = self.validate_workspace(workspace, vault)

            self.assertNotEqual(result.returncode, 0, self.diagnostics(result))
            self.assertEqual(payload["status"], "invalid", self.diagnostics(result))
            self.assert_error_finding(
                payload, result, "placeholder-token", target_path, "{{UNRESOLVED_TOKEN}}"
            )

    def test_validator_rejects_unresolved_local_wikilink(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            vault = Path(temp_dir) / "vault"
            workspace = self.init_workspace(vault)
            target_path = workspace / "03-深度分析.md"
            with target_path.open("a", encoding="utf-8", newline="") as file:
                file.write("\n[[missing-local-note]]\n")

            result, payload = self.validate_workspace(workspace, vault)

            self.assertNotEqual(result.returncode, 0, self.diagnostics(result))
            self.assertEqual(payload["status"], "invalid", self.diagnostics(result))
            self.assert_error_finding(
                payload, result, "unresolved-wikilink", target_path, "missing-local-note"
            )

    def test_validator_rejects_missing_wikilink_heading_anchor(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            vault = Path(temp_dir) / "vault"
            workspace = self.init_workspace(vault)
            source = workspace / "03-深度分析.md"
            with source.open("a", encoding="utf-8", newline="") as file:
                file.write("\n[[01-论文地图#不存在的标题]]\n")

            result, payload = self.validate_workspace(workspace, vault)

            self.assertEqual(result.returncode, 1, self.diagnostics(result))
            self.assert_error_finding(
                payload, result, "unresolved-heading-anchor", source, "不存在的标题"
            )

    def test_validator_rejects_missing_wikilink_block_anchor(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            vault = Path(temp_dir) / "vault"
            workspace = self.init_workspace(vault)
            source = workspace / "03-深度分析.md"
            with source.open("a", encoding="utf-8", newline="") as file:
                file.write("\n[[01-论文地图#^missing-block-id]]\n")

            result, payload = self.validate_workspace(workspace, vault)

            self.assertEqual(result.returncode, 1, self.diagnostics(result))
            self.assert_error_finding(
                payload, result, "unresolved-block-anchor", source, "missing-block-id"
            )

    def test_validator_accepts_existing_heading_and_block_anchors(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            vault = Path(temp_dir) / "vault"
            workspace = self.init_workspace(vault)
            target = workspace / "01-论文地图.md"
            with target.open("a", encoding="utf-8", newline="") as file:
                file.write("\n## 关键结构\n\n锚点段落 ^verified-block\n")
            source = workspace / "03-深度分析.md"
            with source.open("a", encoding="utf-8", newline="") as file:
                file.write(
                    "\n[[01-论文地图#关键结构]]\n"
                    "[[01-论文地图#^verified-block]]\n"
                    "[标准 Markdown 标题](01-论文地图.md#关键结构)\n"
                    "[标准 Markdown 块](01-论文地图.md#%5Everified-block)\n"
                )

            result, payload = self.validate_workspace(workspace, vault)

            self.assertEqual(result.returncode, 0, self.diagnostics(result))
            self.assertEqual(payload["status"], "ok", self.diagnostics(result))

    def test_validator_accepts_anchors_in_public_vault_note(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            vault = Path(temp_dir) / "vault"
            workspace = self.init_workspace(vault)
            public_note = vault / "知识" / "Multi Head Attention.md"
            public_note.parent.mkdir(parents=True)
            public_note.write_text(
                "# Multi Head Attention\n\n## 张量形状\n\n公共知识块 ^public-shape\n",
                encoding="utf-8",
            )
            source = workspace / "03-深度分析.md"
            with source.open("a", encoding="utf-8", newline="") as file:
                file.write(
                    "\n[[Multi Head Attention#张量形状]]\n"
                    "[[Multi Head Attention#^public-shape]]\n"
                    "[公共标题](../../../知识/Multi%20Head%20Attention.md#张量形状)\n"
                    "[公共块](../../../知识/Multi%20Head%20Attention.md#%5Epublic-shape)\n"
                )

            result, payload = self.validate_workspace(workspace, vault)

            self.assertEqual(result.returncode, 0, self.diagnostics(result))
            self.assertEqual(payload["status"], "ok", self.diagnostics(result))
            self.assertFalse(payload["findings"], self.diagnostics(result))

    def test_validator_rejects_missing_anchors_in_public_vault_note(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            vault = Path(temp_dir) / "vault"
            workspace = self.init_workspace(vault)
            public_note = vault / "知识" / "Attention Basics.md"
            public_note.parent.mkdir(parents=True)
            public_note.write_text("# Attention Basics\n\n## Existing\n", encoding="utf-8")
            source = workspace / "03-深度分析.md"
            with source.open("a", encoding="utf-8", newline="") as file:
                file.write(
                    "\n[[Attention Basics#Missing Heading]]\n"
                    "[公共缺失块](../../../知识/Attention%20Basics.md#%5Emissing-public-block)\n"
                )

            result, payload = self.validate_workspace(workspace, vault)

            self.assertEqual(result.returncode, 1, self.diagnostics(result))
            self.assert_error_finding(
                payload, result, "unresolved-heading-anchor", source, "Missing Heading"
            )
            self.assert_error_finding(
                payload, result, "unresolved-block-anchor", source, "missing-public-block"
            )

    def test_validator_strictly_reads_public_vault_note_for_anchor(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            vault = Path(temp_dir) / "vault"
            workspace = self.init_workspace(vault)
            public_note = vault / "知识" / "Unreadable.md"
            public_note.parent.mkdir(parents=True)
            public_note.write_bytes(b"\xff\xfe\xfa")
            source = workspace / "03-深度分析.md"
            with source.open("a", encoding="utf-8", newline="") as file:
                file.write("\n[[Unreadable#Heading]]\n")

            result, payload = self.validate_workspace(workspace, vault)

            self.assertEqual(result.returncode, 1, self.diagnostics(result))
            self.assert_error_finding(
                payload, result, "markdown-read-error", public_note, "UTF-8"
            )

    def test_validator_rejects_ambiguous_public_note_anchor(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            vault = Path(temp_dir) / "vault"
            workspace = self.init_workspace(vault)
            for folder in ("知识-A", "知识-B"):
                note = vault / folder / "Ambiguous.md"
                note.parent.mkdir(parents=True)
                note.write_text("# Ambiguous\n\n## Heading\n", encoding="utf-8")
            source = workspace / "03-深度分析.md"
            with source.open("a", encoding="utf-8", newline="") as file:
                file.write("\n[[Ambiguous#Heading]]\n")

            result, payload = self.validate_workspace(workspace, vault)

            self.assertEqual(result.returncode, 1, self.diagnostics(result))
            self.assert_error_finding(
                payload, result, "unresolved-wikilink", source, "Ambiguous"
            )

    def test_validator_accepts_local_pdf_page_fragment(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            vault = temp_path / "vault"
            source_pdf = temp_path / "source.pdf"
            source_pdf.write_bytes(b"%PDF-1.4 page fragment fixture")
            workspace = self.init_workspace(vault, source_pdf)
            source = workspace / "03-深度分析.md"
            with source.open("a", encoding="utf-8", newline="") as file:
                file.write("\n[原文第 2 页](assets/source.pdf#page=2)\n")

            result, payload = self.validate_workspace(workspace, vault)

            self.assertEqual(result.returncode, 0, self.diagnostics(result))
            self.assertEqual(payload["status"], "ok", self.diagnostics(result))

    def test_validator_accepts_angle_target_with_spaces_and_parentheses(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            vault = Path(temp_dir) / "vault"
            workspace = self.init_workspace(vault)
            figure = workspace / "assets" / "figures" / "figure (final).png"
            figure.write_bytes(b"PNG fixture")
            source = workspace / "03-深度分析.md"
            with source.open("a", encoding="utf-8", newline="") as file:
                file.write("\n![结果图](<assets/figures/figure (final).png>)\n")

            result, payload = self.validate_workspace(workspace, vault)

            self.assertEqual(result.returncode, 0, self.diagnostics(result))
            self.assertEqual(payload["status"], "ok", self.diagnostics(result))

    def test_validator_accepts_external_url_with_fragment(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            vault = Path(temp_dir) / "vault"
            workspace = self.init_workspace(vault)
            source = workspace / "03-深度分析.md"
            with source.open("a", encoding="utf-8", newline="") as file:
                file.write("\n[外部资料](https://example.com/paper#section-2)\n")

            result, payload = self.validate_workspace(workspace, vault)

            self.assertEqual(result.returncode, 0, self.diagnostics(result))
            self.assertEqual(payload["status"], "ok", self.diagnostics(result))

    def test_validator_rejects_missing_markdown_image(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            vault = Path(temp_dir) / "vault"
            workspace = self.init_workspace(vault)
            source = workspace / "03-深度分析.md"
            with source.open("a", encoding="utf-8", newline="") as file:
                file.write("\n![缺失图片](assets/figures/missing-figure.png)\n")

            result, payload = self.validate_workspace(workspace, vault)

            self.assertEqual(result.returncode, 1, self.diagnostics(result))
            self.assert_error_finding(
                payload, result, "unresolved-markdown-link", source, "missing-figure.png"
            )

    def test_validator_rejects_missing_markdown_pdf(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            vault = Path(temp_dir) / "vault"
            workspace = self.init_workspace(vault)
            source = workspace / "03-深度分析.md"
            with source.open("a", encoding="utf-8", newline="") as file:
                file.write("\n[论文 PDF](assets/missing-paper.pdf)\n")

            result, payload = self.validate_workspace(workspace, vault)

            self.assertEqual(result.returncode, 1, self.diagnostics(result))
            self.assert_error_finding(
                payload, result, "unresolved-markdown-link", source, "missing-paper.pdf"
            )

    def test_validator_rejects_missing_local_markdown_target(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            vault = Path(temp_dir) / "vault"
            workspace = self.init_workspace(vault)
            source = workspace / "03-深度分析.md"
            with source.open("a", encoding="utf-8", newline="") as file:
                file.write("\n[缺失笔记](missing-local-note.md)\n")

            result, payload = self.validate_workspace(workspace, vault)

            self.assertEqual(result.returncode, 1, self.diagnostics(result))
            self.assert_error_finding(
                payload, result, "unresolved-markdown-link", source, "missing-local-note.md"
            )

    def test_validator_rejects_absolute_markdown_target_outside_vault(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            vault = temp_path / "vault"
            workspace = self.init_workspace(vault)
            outside = (temp_path / "outside.pdf").resolve()
            outside.write_bytes(b"outside PDF fixture")
            source = workspace / "03-深度分析.md"
            with source.open("a", encoding="utf-8", newline="") as file:
                file.write(f"\n[越界文件](<{outside}>)\n")

            result, payload = self.validate_workspace(workspace, vault)

            self.assertEqual(result.returncode, 1, self.diagnostics(result))
            self.assert_error_finding(
                payload, result, "unresolved-markdown-link", source, str(outside)
            )

    def test_validator_rejects_manifest_count_mismatch(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            vault = Path(temp_dir) / "vault"
            workspace = self.init_workspace(vault)
            manifest_path = workspace / "assets" / "paper-manifest.json"
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            structure = manifest["structure"]
            self.assertEqual(
                structure["required_paths_count"], len(structure["required_paths"])
            )
            structure["required_paths_count"] += 1
            manifest_path.write_text(
                json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )

            result, payload = self.validate_workspace(workspace, vault)

            self.assertNotEqual(result.returncode, 0, self.diagnostics(result))
            self.assertEqual(payload["status"], "invalid", self.diagnostics(result))
            self.assert_error_finding(
                payload,
                result,
                "manifest-count-mismatch",
                manifest_path,
                "required_paths_count",
            )

    def test_validator_accepts_representative_trial_checkpoint(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            vault = Path(temp_dir) / "vault"
            workspace = self.init_workspace(vault)
            progress = {
                "translation": "representative-only",
                "analysis": "trial-only",
                "knowledge": "trial-only",
                "code": "verified-minimal",
                "modern_context": "not-started",
                "learning": "awaiting-response",
            }
            self.rewrite_manifest(
                workspace, lambda manifest: manifest.__setitem__("progress", progress)
            )
            moc = workspace / MOC_NAME
            self.replace_frontmatter_value(moc, "status", "trial")
            self.replace_frontmatter_value(
                moc, "translation_progress", "representative-only"
            )
            self.replace_frontmatter_value(moc, "analysis_progress", "trial-only")
            self.replace_frontmatter_value(moc, "learning_status", "awaiting-response")

            result, payload = self.validate_workspace(workspace, vault)

            self.assertEqual(result.returncode, 0, self.diagnostics(result))
            self.assertEqual(payload["status"], "ok", self.diagnostics(result))
            self.assertFalse(payload["findings"], self.diagnostics(result))

    def test_validator_rejects_stale_moc_progress_fields(self):
        cases = (
            ("translation", "translation_progress", "representative-only"),
            ("analysis", "analysis_progress", "trial-only"),
            ("learning", "learning_status", "awaiting-response"),
        )
        for manifest_field, moc_field, current_value in cases:
            with self.subTest(field=manifest_field), tempfile.TemporaryDirectory() as temp_dir:
                vault = Path(temp_dir) / "vault"
                workspace = self.init_workspace(vault)
                self.rewrite_manifest(
                    workspace,
                    lambda manifest, field=manifest_field, value=current_value: manifest[
                        "progress"
                    ].__setitem__(field, value),
                )

                result, payload = self.validate_workspace(workspace, vault)

                self.assertEqual(result.returncode, 1, self.diagnostics(result))
                self.assert_error_finding(
                    payload,
                    result,
                    "checkpoint-mismatch",
                    workspace / MOC_NAME,
                    moc_field,
                )

    def test_validator_does_not_overconstrain_future_checkpoint_values(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            vault = Path(temp_dir) / "vault"
            workspace = self.init_workspace(vault)
            progress = {
                "translation": "future-translation-stage",
                "analysis": "future-analysis-stage",
                "knowledge": "future-knowledge-stage",
                "code": "future-code-stage",
                "modern_context": "future-context-stage",
                "learning": "future-learning-stage",
            }
            self.rewrite_manifest(
                workspace, lambda manifest: manifest.__setitem__("progress", progress)
            )
            moc = workspace / MOC_NAME
            self.replace_frontmatter_value(moc, "status", "future-workflow")
            self.replace_frontmatter_value(moc, "translation_progress", 37)
            self.replace_frontmatter_value(moc, "analysis_progress", 12)
            self.replace_frontmatter_value(moc, "learning_status", "calibrating")

            result, payload = self.validate_workspace(workspace, vault)

            self.assertEqual(result.returncode, 0, self.diagnostics(result))
            self.assertEqual(payload["status"], "ok", self.diagnostics(result))
            self.assertFalse(payload["findings"], self.diagnostics(result))

    def test_validator_rejects_initialized_moc_after_work_begins(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            vault = Path(temp_dir) / "vault"
            workspace = self.init_workspace(vault)
            self.rewrite_manifest(
                workspace,
                lambda manifest: manifest["progress"].__setitem__(
                    "translation", "representative-only"
                ),
            )
            moc = workspace / MOC_NAME
            self.replace_frontmatter_value(
                moc, "translation_progress", "representative-only"
            )

            result, payload = self.validate_workspace(workspace, vault)

            self.assertEqual(result.returncode, 1, self.diagnostics(result))
            self.assert_error_finding(
                payload, result, "checkpoint-mismatch", moc, "status"
            )

    def test_validator_rejects_copied_pdf_outside_workspace(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            vault = temp_path / "vault"
            workspace = self.init_workspace(vault)
            outside_pdf = temp_path / "outside.pdf"
            outside_pdf.write_bytes(b"outside PDF fixture")
            manifest_path = workspace / "assets" / "paper-manifest.json"
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            manifest["source"]["copied_pdf"] = str(outside_pdf.resolve())
            manifest_path.write_text(
                json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )

            result, payload = self.validate_workspace(workspace, vault)

            self.assertEqual(result.returncode, 1, self.diagnostics(result))
            self.assertEqual(payload["status"], "invalid", self.diagnostics(result))
            self.assert_error_finding(
                payload, result, "pdf-outside-workspace", manifest_path, "outside.pdf"
            )

    def test_validator_rejects_copied_pdf_hash_mismatch(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            vault = temp_path / "vault"
            source_pdf = temp_path / "source.pdf"
            source_pdf.write_bytes(b"PDF hash fixture")
            workspace = self.init_workspace(vault, source_pdf)
            manifest_path = workspace / "assets" / "paper-manifest.json"
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            manifest["source"]["sha256"] = "0" * 64
            manifest_path.write_text(
                json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )

            result, payload = self.validate_workspace(workspace, vault)

            self.assertEqual(result.returncode, 1, self.diagnostics(result))
            self.assertEqual(payload["status"], "invalid", self.diagnostics(result))
            self.assert_error_finding(
                payload, result, "pdf-hash-mismatch", manifest_path, "sha256"
            )

    def test_validator_reports_invalid_manifest_as_loading_error(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            vault = Path(temp_dir) / "vault"
            workspace = self.init_workspace(vault)
            manifest_path = workspace / "assets" / "paper-manifest.json"
            manifest_path.write_text("{not JSON}\n", encoding="utf-8")

            result, payload = self.validate_workspace(workspace, vault)

            self.assertEqual(result.returncode, 2, self.diagnostics(result))
            self.assertEqual(payload["status"], "error", self.diagnostics(result))
            self.assert_error_finding(
                payload, result, "invalid-manifest", manifest_path, "valid JSON"
            )

    def test_validator_rejects_explicit_vault_that_does_not_contain_workspace(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            workspace = self.init_workspace(temp_path / "vault-a")
            foreign_vault = temp_path / "foreign-vault"
            foreign_vault.mkdir()

            result = self.run_script(VALIDATOR, workspace, "--vault", foreign_vault, "--json")
            payload = self.parse_json_object(result, "foreign vault")

            self.assertEqual(result.returncode, 2, self.diagnostics(result))
            self.assertEqual(payload["status"], "error", self.diagnostics(result))
            self.assert_error_finding(
                payload, result, "invalid-vault", workspace, "does not contain workspace"
            )

    def test_validator_rejects_wikilink_escape_outside_vault(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            vault = temp_path / "vault"
            workspace = self.init_workspace(vault)
            outside = temp_path / "outside-note.md"
            outside.write_text("# Outside\n", encoding="utf-8")
            source = workspace / "03-深度分析.md"
            with source.open("a", encoding="utf-8", newline="") as file:
                file.write("\n[[../../../../outside-note]]\n")

            result, payload = self.validate_workspace(workspace, vault)

            self.assertEqual(result.returncode, 1, self.diagnostics(result))
            self.assertEqual(payload["status"], "invalid", self.diagnostics(result))
            self.assert_error_finding(
                payload, result, "unresolved-wikilink", source, "../../../../outside-note"
            )

    def test_validator_rejects_absolute_local_wikilink_target(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            vault = temp_path / "vault"
            workspace = self.init_workspace(vault)
            outside = (temp_path / "outside-note.md").resolve()
            outside.write_text("# Outside\n", encoding="utf-8")
            source = workspace / "03-深度分析.md"
            with source.open("a", encoding="utf-8", newline="") as file:
                file.write(f"\n[[{outside}]]\n")

            result, payload = self.validate_workspace(workspace, vault)

            self.assertEqual(result.returncode, 1, self.diagnostics(result))
            self.assertEqual(payload["status"], "invalid", self.diagnostics(result))
            self.assert_error_finding(
                payload, result, "unresolved-wikilink", source, str(outside)
            )

    def test_validator_rejects_wikilink_symlink_escape_outside_vault(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            vault = temp_path / "vault"
            workspace = self.init_workspace(vault)
            outside_dir = temp_path / "outside"
            outside_dir.mkdir()
            (outside_dir / "outside-note.md").write_text("# Outside\n", encoding="utf-8")
            link_dir = workspace / "linked-outside"
            try:
                os.symlink(outside_dir, link_dir, target_is_directory=True)
            except OSError as error:
                if error.errno in (errno.EACCES, errno.EPERM) or getattr(error, "winerror", None) == 1314:
                    self.skipTest(f"symlink creation unavailable: {error}")
                raise
            source = workspace / "03-深度分析.md"
            with source.open("a", encoding="utf-8", newline="") as file:
                file.write("\n[[linked-outside/outside-note]]\n")

            result, payload = self.validate_workspace(workspace, vault)

            self.assertEqual(result.returncode, 1, self.diagnostics(result))
            self.assertEqual(payload["status"], "invalid", self.diagnostics(result))
            self.assert_error_finding(
                payload, result, "unresolved-wikilink", source, "linked-outside/outside-note"
            )

    def test_validator_reports_invalid_utf8_markdown(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            vault = Path(temp_dir) / "vault"
            workspace = self.init_workspace(vault)
            bad_markdown = workspace / "bad.md"
            bad_markdown.write_bytes(b"\xff\xfe\xfa")

            result, payload = self.validate_workspace(workspace, vault)

            self.assertEqual(result.returncode, 1, self.diagnostics(result))
            self.assertEqual(payload["status"], "invalid", self.diagnostics(result))
            self.assert_error_finding(
                payload, result, "markdown-read-error", bad_markdown, "UTF-8"
            )

    def test_validator_rejects_duplicate_inline_block_ids(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            vault = Path(temp_dir) / "vault"
            workspace = self.init_workspace(vault)
            analysis_path = workspace / "03-深度分析.md"
            knowledge_path = workspace / "04-知识地图.md"
            with analysis_path.open("a", encoding="utf-8", newline="") as file:
                file.write("\nalpha ^inline-duplicate-fixture\n")
            with knowledge_path.open("a", encoding="utf-8", newline="") as file:
                file.write("\nbeta ^inline-duplicate-fixture\n")

            result, payload = self.validate_workspace(workspace, vault)

            self.assertEqual(result.returncode, 1, self.diagnostics(result))
            self.assertEqual(payload["status"], "invalid", self.diagnostics(result))
            matches = [
                finding for finding in payload["findings"]
                if finding["code"] == "duplicate-block-id"
                and "inline-duplicate-fixture" in finding["message"]
            ]
            self.assertTrue(matches, self.diagnostics(result))
            self.assertIn(str(analysis_path.resolve()), matches[0]["message"], self.diagnostics(result))
            self.assertIn(str(knowledge_path.resolve()), matches[0]["message"], self.diagnostics(result))

    def test_validator_ignores_escaped_and_literal_wikilinks_and_block_ids(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            vault = Path(temp_dir) / "vault"
            workspace = self.init_workspace(vault)
            source = workspace / "03-深度分析.md"
            map_path = workspace / "01-论文地图.md"
            with map_path.open("a", encoding="utf-8", newline="") as file:
                file.write("\n## heading\n\nvalid block ^block\n")
            with source.open("a", encoding="utf-8", newline="") as file:
                file.write(
                    "\n\\[[missing-escaped]]\n"
                    "`[[missing-inline-code]]`\n"
                    "\\[missing escaped Markdown](missing-escaped.md)\n"
                    "`[missing inline Markdown](missing-inline.md)`\n"
                    "`inline ^literal-block-id`\n"
                    "```text\n[[missing-fenced-code]]\n"
                    "![missing fenced image](missing-fenced.png)\n"
                    "alpha ^literal-block-id\n```\n"
                    "![[01-论文地图]]\n"
                    "[[01-论文地图|alias]]\n"
                    "[[01-论文地图#heading]]\n"
                    "[[01-论文地图#^block]]\n"
                )

            result, payload = self.validate_workspace(workspace, vault)

            self.assertEqual(result.returncode, 0, self.diagnostics(result))
            self.assertEqual(payload["status"], "ok", self.diagnostics(result))
            self.assertFalse(payload["findings"], self.diagnostics(result))

    def test_validator_ignores_wikilinks_in_nested_backtick_and_tilde_fences(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            vault = Path(temp_dir) / "vault"
            workspace = self.init_workspace(vault)
            source = workspace / "03-深度分析.md"
            with source.open("a", encoding="utf-8", newline="") as file:
                file.write(
                    "\n````text\n"
                    "```\n"
                    "[[missing-in-four-backtick-code]]\n"
                    "````\n"
                    "~~~text\n"
                    "[[missing-in-tilde-code]]\n"
                    "~~~\n"
                )

            result, payload = self.validate_workspace(workspace, vault)

            self.assertEqual(result.returncode, 0, self.diagnostics(result))
            self.assertEqual(payload["status"], "ok", self.diagnostics(result))
            self.assertFalse(payload["findings"], self.diagnostics(result))

    def test_validator_does_not_close_fence_on_mixed_delimiters(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            vault = Path(temp_dir) / "vault"
            workspace = self.init_workspace(vault)
            source = workspace / "03-深度分析.md"
            with source.open("a", encoding="utf-8", newline="") as file:
                file.write(
                    "\n````text\n"
                    "````~\n"
                    "[[missing-in-mixed-fence-code]]\n"
                    "````\n"
                )

            result, payload = self.validate_workspace(workspace, vault)

            self.assertEqual(result.returncode, 0, self.diagnostics(result))
            self.assertEqual(payload["status"], "ok", self.diagnostics(result))
            self.assertFalse(payload["findings"], self.diagnostics(result))

    def test_validator_rejects_nested_duplicate_titled_moc(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            vault = Path(temp_dir) / "vault"
            workspace = self.init_workspace(vault)
            duplicate = workspace / "02-双语对照" / MOC_NAME
            duplicate.write_text("# Duplicate MOC\n", encoding="utf-8")

            result, payload = self.validate_workspace(workspace, vault)

            self.assertEqual(result.returncode, 1, self.diagnostics(result))
            self.assertEqual(payload["status"], "invalid", self.diagnostics(result))
            matches = [
                finding for finding in payload["findings"]
                if finding["code"] == "duplicate-moc" and finding["severity"] == "error"
            ]
            self.assertTrue(matches, self.diagnostics(result))
            self.assertIn(str((workspace / MOC_NAME).resolve()), matches[0]["message"], self.diagnostics(result))
            self.assertIn(str(duplicate.resolve()), matches[0]["message"], self.diagnostics(result))


if __name__ == "__main__":
    unittest.main()
