#!/usr/bin/env python3
"""Executable checks for current product truth and governance wiring."""

from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]


class ProductContractTest(unittest.TestCase):
    def test_current_specs_exist_and_name_both_distinct_editions(self):
        product = (ROOT / "docs" / "PRODUCT_SPEC.md").read_text(encoding="utf-8")
        security = (ROOT / "docs" / "SECURITY_SPEC.md").read_text(encoding="utf-8")
        growth = (ROOT / "docs" / "GROWTH_ROADMAP.md").read_text(encoding="utf-8")
        repo_map = (ROOT / "docs" / "REPOSITORY_MAP.md").read_text(encoding="utf-8")

        for required in (
            "### Morning edition",
            "### Evening edition",
            "at most 130 characters",
            "absolute, credential-free HTTPS",
        ):
            self.assertIn(required, product)
        self.assertIn("Reader privacy", security)
        self.assertIn("1,000,000 followers", growth)
        self.assertIn("Production source of truth", repo_map)

    def test_chronicles_describes_actual_reader_queue_and_publication(self):
        page = (ROOT / "chronicles.html").read_text(encoding="utf-8")

        for current_truth in (
            "at most one waiting question, oldest first",
            "one waiting reader letter is answered, oldest first",
            "at most one waiting pin goes on the board, oldest first",
            "may be published on the public site",
            "Do not include private or sensitive information",
        ):
            self.assertIn(current_truth, page)
        for stale_promise in (
            "draws five questions",
            "up to three letters are drawn",
            "Whatever&rsquo;s on the board when the ovens fire goes out",
        ):
            self.assertNotIn(stale_promise, page)

    def test_bake_cannot_change_its_reader_input_snapshot(self):
        workflow = (ROOT / ".github" / "workflows" / "ddb-bake.yml").read_text(
            encoding="utf-8"
        )
        allowlist_line = next(
            line for line in workflow.splitlines()
            if line.strip().startswith("allow='^(index")
        )
        self.assertNotIn("counter\\.csv", allowlist_line)
        self.assertIn("persist-credentials: false", workflow)
        self.assertRegex(workflow, r"(?m)^permissions:\n  contents: write$")

        bake_spec = (ROOT / "BAKE.md").read_text(encoding="utf-8")
        self.assertIn("`--plan` never refreshes or mutates it", bake_spec)

    def test_main_writers_are_serialized(self):
        bake = (ROOT / ".github" / "workflows" / "ddb-bake.yml").read_text(
            encoding="utf-8"
        )
        counter = (ROOT / ".github" / "workflows" / "counter-sync.yml").read_text(
            encoding="utf-8"
        )
        self.assertIn("group: ddb-main-writers", bake)
        self.assertIn("group: ddb-main-writers", counter)
        self.assertIn("git pull --rebase origin main", counter)

    def test_workflow_dependencies_are_immutable(self):
        workflows = "\n".join(
            path.read_text(encoding="utf-8")
            for path in sorted((ROOT / ".github" / "workflows").glob("*.yml"))
        )
        self.assertNotRegex(workflows, r"uses:\s+[^\s]+@v\d+(?:\s|$)")
        self.assertIn("@anthropic-ai/claude-code@2.1.220", workflows)
        self.assertIn("sha512sum --check", workflows)
        self.assertIn("pytest==8.4.2", workflows)

    def test_security_scanning_is_wired(self):
        codeql = (ROOT / ".github" / "workflows" / "codeql.yml").read_text(
            encoding="utf-8"
        )
        dependabot = (ROOT / ".github" / "dependabot.yml").read_text(
            encoding="utf-8"
        )
        self.assertIn("language: [python, javascript-typescript]", codeql)
        self.assertIn("security-extended", codeql)
        self.assertIn("package-ecosystem: github-actions", dependabot)

    def test_archive_contract_is_named_consistently_across_active_docs(self):
        for relative in ("README.md", "BAKE.md", "docs/PRODUCT_SPEC.md"):
            text = (ROOT / relative).read_text(encoding="utf-8")
            with self.subTest(path=relative):
                self.assertIn("archive.json", text)
                self.assertIn("morning", text.lower())
                self.assertIn("evening", text.lower())


if __name__ == "__main__":
    unittest.main()
