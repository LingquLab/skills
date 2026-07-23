#!/usr/bin/env python3
"""Offline regression tests for the Ascend documentation search client."""

from __future__ import annotations

import importlib.util
import json
import pathlib
import sys
import unittest
from unittest import mock


ROOT = pathlib.Path(__file__).resolve().parents[2]
SCRIPT = (
    ROOT
    / "plugins"
    / "ascendc-development"
    / "skills"
    / "ascendc-docs-search"
    / "scripts"
    / "search_ascend_docs.py"
)
SPEC = importlib.util.spec_from_file_location("search_ascend_docs", SCRIPT)
if SPEC is None or SPEC.loader is None:
    raise RuntimeError(f"cannot load {SCRIPT}")
SEARCH = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = SEARCH
SPEC.loader.exec_module(SEARCH)


class SearchAscendDocsTest(unittest.TestCase):
    def test_request_uses_current_canonical_referer(self) -> None:
        response = mock.MagicMock()
        response.__enter__.return_value = response
        response.geturl.return_value = SEARCH.SEARCH_URL
        response.headers.get_content_charset.return_value = "utf-8"
        response.read.return_value = b"{}"
        with mock.patch.object(SEARCH, "urlopen", return_value=response) as opener:
            SEARCH._get(SEARCH.SEARCH_URL, 1, search_request=True)
        request = opener.call_args.args[0]
        self.assertEqual(request.get_header("Referer"), "https://www.hiascend.com/")

    def test_official_url_transforms_source_path_and_rejects_other_hosts(self) -> None:
        actual = SEARCH._official_url(
            "/source/zh/CANNCommunityEdition/910beta3/API/ascendcopapi/example.html"
        )
        self.assertEqual(
            actual,
            "https://www.hiascend.com/document/detail/zh/"
            "CANNCommunityEdition/910beta3/API/ascendcopapi/example.html",
        )
        with self.assertRaises(SEARCH.DocsSearchError):
            SEARCH._official_url("https://example.com/document/detail/example.html")

    def test_search_uses_single_url_encoding_for_base64_keyword(self) -> None:
        payload = {
            "success": True,
            "data": {
                "data": [
                    {
                        "docTitle": "<em>SetAtomicType</em>",
                        "docContent": "API summary",
                        "docUrl": "/source/zh/example.html",
                        "version": "9.1.0-beta.3",
                    }
                ]
            },
        }

        def fake_get(url: str, timeout: float, *, search_request: bool = False):
            self.assertTrue(search_request)
            self.assertIn("keyword=U2V0QXRvbWljVHlwZQ%3D%3D", url)
            self.assertNotIn("%253D", url)
            return json.dumps(payload).encode(), "utf-8", SEARCH.SEARCH_URL

        with mock.patch.object(SEARCH, "_get", side_effect=fake_get):
            results = SEARCH.search_documents(
                "SetAtomicType",
                lang="zh",
                doc_type="DOC",
                page=1,
                max_results=5,
                version=None,
                timeout=1,
            )
        self.assertEqual(results[0]["title"], "SetAtomicType")

    def test_parser_excludes_title_and_navigation_but_keeps_code(self) -> None:
        parser = SEARCH.DocumentParser()
        parser.feed(
            "<html><head><title>SetAtomicType docs</title></head>"
            "<body><header>SetAtomicType navigation</header><main>"
            "<h1>Function</h1><p>SetAtomicType changes the atomic data type.</p>"
            "<pre>template &lt;typename T&gt; void SetAtomicType();</pre>"
            "</main></body></html>"
        )
        parsed = parser.result()
        self.assertEqual(parsed["title"], "SetAtomicType docs")
        self.assertNotIn("navigation", parsed["content"])
        self.assertIn("SetAtomicType changes", parsed["content"])
        self.assertIn("SetAtomicType", parsed["code_blocks"][0])


if __name__ == "__main__":
    unittest.main()
