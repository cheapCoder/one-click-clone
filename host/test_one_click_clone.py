import unittest

from one_click_clone import parse_page_url, resolve_ref, same_repo


class ParsePageUrlTest(unittest.TestCase):
    def test_github_root(self):
        self.assertEqual(
            parse_page_url("https://github.com/cheapCoder/one-click-clone"),
            ("https://github.com/cheapCoder/one-click-clone.git", "one-click-clone", []),
        )

    def test_github_ignores_query_hash_and_git_suffix(self):
        repo_url, name, ref_parts = parse_page_url("https://github.com/a/b.git?tab=readme#top")
        self.assertEqual((repo_url, name, ref_parts), ("https://github.com/a/b.git", "b", []))

    def test_github_tree_keeps_all_segments_after_marker(self):
        _, _, ref_parts = parse_page_url("https://github.com/a/b/tree/feature/vite-ts/src")
        self.assertEqual(ref_parts, ["feature", "vite-ts", "src"])

    def test_github_blob(self):
        _, _, ref_parts = parse_page_url("https://github.com/a/b/blob/main/README.md")
        self.assertEqual(ref_parts, ["main", "README.md"])

    def test_github_other_page_has_no_ref(self):
        _, _, ref_parts = parse_page_url("https://github.com/a/b/pulls")
        self.assertEqual(ref_parts, [])

    def test_decodes_percent_encoded_ref(self):
        _, _, ref_parts = parse_page_url("https://github.com/a/b/tree/%E4%B8%AD%E6%96%87")
        self.assertEqual(ref_parts, ["中文"])

    def test_gitlab_nested_groups_root(self):
        self.assertEqual(
            parse_page_url("https://gitlab.example.com/group/sub/team/project"),
            ("https://gitlab.example.com/group/sub/team/project.git", "project", []),
        )

    def test_gitlab_tree(self):
        repo_url, _, ref_parts = parse_page_url("https://gitlab.example.com/g/sub/p/-/tree/feat/x/src")
        self.assertEqual(repo_url, "https://gitlab.example.com/g/sub/p.git")
        self.assertEqual(ref_parts, ["feat", "x", "src"])

    def test_gitlab_other_page_has_no_ref(self):
        repo_url, _, ref_parts = parse_page_url("https://gitlab.example.com/g/p/-/merge_requests/12")
        self.assertEqual((repo_url, ref_parts), ("https://gitlab.example.com/g/p.git", []))

    def test_rejects_non_repo_pages(self):
        for url in ("https://github.com/", "https://github.com/cheapCoder", "chrome://extensions/"):
            with self.subTest(url=url), self.assertRaises(ValueError):
                parse_page_url(url)


class ResolveRefTest(unittest.TestCase):
    def test_single_segment_needs_no_lookup(self):
        self.assertEqual(resolve_ref(["main"], lambda: self.fail("不应查询远程")), "main")

    def test_picks_longest_existing_prefix(self):
        refs = {"main", "feature", "feature/vite-ts"}
        self.assertEqual(resolve_ref(["feature", "vite-ts", "src"], lambda: refs), "feature/vite-ts")

    def test_unknown_ref_raises(self):
        with self.assertRaises(ValueError):
            resolve_ref(["abc123", "src"], lambda: {"main"})

    def test_no_ref(self):
        self.assertIsNone(resolve_ref([], lambda: self.fail("不应查询远程")))


class SameRepoTest(unittest.TestCase):
    def test_ignores_credentials_case_and_suffix(self):
        self.assertTrue(same_repo("https://github.com/cheapCoder/One.git", "https://user@GitHub.com/cheapcoder/one/"))

    def test_ssh_matches_https(self):
        self.assertTrue(same_repo("git@gitlab.example.com:g/p.git", "https://gitlab.example.com/g/p.git"))

    def test_different_owner(self):
        self.assertFalse(same_repo("https://github.com/a/one.git", "https://github.com/b/one.git"))


if __name__ == "__main__":
    unittest.main()
