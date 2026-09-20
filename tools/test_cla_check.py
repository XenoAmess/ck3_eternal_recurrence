#!/usr/bin/env python3
from __future__ import annotations

import unittest

import cla_check


STATEMENT = (
    "I have read and agree to the Contributor License Agreement (CLA), version "
    "1.2, and I confirm that I have authority to grant the rights for my contribution."
)
CONFIG = {
    "acceptance_statement": STATEMENT,
    "comment_marker": "<!-- project-causality-cla-check:v1 -->",
    "exempt_users": ["XenoAmess"],
    "manual_override_labels": ["cla:manual"],
    "require_commit_authors": True,
    "version": "1.2",
}


def pr(author: str = "alice", labels: tuple[str, ...] = ()) -> dict:
    return {
        "user": {"login": author},
        "labels": [{"name": label} for label in labels],
    }


def commit(
    sha: str,
    login: str | None,
    name: str,
    email: str,
    message: str = "Change",
) -> dict:
    return {
        "sha": sha,
        "author": None if login is None else {"login": login},
        "commit": {
            "author": {"name": name, "email": email},
            "message": message,
        },
    }


def signed(login: str, body: str = STATEMENT) -> dict:
    return {
        "user": {"login": login, "type": "User"},
        "body": body,
        "html_url": f"https://example.test/{login}",
    }


class ClaCheckTests(unittest.TestCase):
    def test_repository_config_matches_cla_document(self) -> None:
        loaded = cla_check.load_config()
        self.assertEqual(loaded["version"], "1.2")
        self.assertEqual(loaded["acceptance_statement"], STATEMENT)

    def test_exact_signature_passes_for_pr_and_commit_authors(self) -> None:
        result = cla_check.evaluate(
            CONFIG,
            pr(),
            [commit("a" * 40, "bob", "Bob", "bob@example.test")],
            [signed("alice"), signed("bob")],
        )
        self.assertTrue(result.passed)
        self.assertEqual(result.required_users, ("alice", "bob"))

    def test_near_match_does_not_sign(self) -> None:
        result = cla_check.evaluate(
            CONFIG,
            pr(),
            [commit("a" * 40, "alice", "Alice", "alice@example.test")],
            [signed("alice", STATEMENT + " Thanks!")],
        )
        self.assertFalse(result.passed)
        self.assertEqual(result.missing_users, ("alice",))

    def test_noreply_authors_and_coauthors_are_mapped(self) -> None:
        message = (
            "Joint change\n\n"
            "Co-authored-by: Carol <456+carol@users.noreply.github.com>"
        )
        result = cla_check.evaluate(
            CONFIG,
            pr(),
            [
                commit(
                    "b" * 40,
                    None,
                    "Bob",
                    "123+bob@users.noreply.github.com",
                    message,
                )
            ],
            [signed("alice"), signed("bob"), signed("carol")],
        )
        self.assertTrue(result.passed)
        self.assertEqual(result.required_users, ("alice", "bob", "carol"))

    def test_unmapped_author_requires_review_without_exposing_email(self) -> None:
        result = cla_check.evaluate(
            CONFIG,
            pr(),
            [commit("c" * 40, None, "Offline Author", "private@example.test")],
            [signed("alice")],
        )
        self.assertFalse(result.passed)
        self.assertEqual(result.unresolved_authors, ("cccccccccccc (Offline Author)",))
        body = cla_check.render_comment(CONFIG, result, "https://example.test/CLA.md")
        self.assertNotIn("private@example.test", body)

    def test_maintainer_and_bots_are_exempt(self) -> None:
        result = cla_check.evaluate(
            CONFIG,
            pr("XenoAmess"),
            [commit("d" * 40, "dependabot[bot]", "Bot", "bot@example.test")],
            [],
        )
        self.assertTrue(result.passed)
        self.assertEqual(result.required_users, ())

    def test_manual_override_is_explicit(self) -> None:
        result = cla_check.evaluate(CONFIG, pr(labels=("CLA:Manual",)), [], [])
        self.assertTrue(result.passed)
        self.assertEqual(result.override_label, "cla:manual")

    def test_link_header_pagination(self) -> None:
        header = (
            '<https://api.github.test/items?page=2>; rel="next", '
            '<https://api.github.test/items?page=3>; rel="last"'
        )
        self.assertEqual(
            cla_check.next_link(header), "https://api.github.test/items?page=2"
        )

    def test_document_url_pins_the_trusted_revision(self) -> None:
        self.assertEqual(
            cla_check.document_url("owner/repo", "legal/CLA 1.2.md", "abc123"),
            "https://github.com/owner/repo/blob/abc123/legal/CLA%201.2.md",
        )


if __name__ == "__main__":
    unittest.main(verbosity=2)
