#!/usr/bin/env python3
"""Search and fetch official Huawei Ascend documentation."""

from __future__ import annotations

import argparse
import base64
import json
import re
import sys
from html.parser import HTMLParser
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode, urljoin, urlparse
from urllib.request import Request, urlopen


BASE_URL = "https://www.hiascend.com"
SEARCH_URL = f"{BASE_URL}/ascendgateway/ascendservice/content/search"
ALLOWED_HOST = "www.hiascend.com"
USER_AGENT = "Mozilla/5.0 (compatible; AscendDocsSearch/2.0)"
BLOCK_TAGS = {
    "address",
    "article",
    "blockquote",
    "br",
    "dd",
    "div",
    "dl",
    "dt",
    "figcaption",
    "figure",
    "h1",
    "h2",
    "h3",
    "h4",
    "h5",
    "h6",
    "hr",
    "li",
    "main",
    "ol",
    "p",
    "pre",
    "section",
    "table",
    "td",
    "th",
    "tr",
    "ul",
}
SKIP_TAGS = {"aside", "button", "footer", "form", "header", "nav", "script", "style", "svg"}


class DocsSearchError(RuntimeError):
    """An expected search or fetch failure."""


class DocumentParser(HTMLParser):
    """Extract readable text and code without third-party HTML dependencies."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.title_parts: list[str] = []
        self.description = ""
        self.all_parts: list[str] = []
        self.main_parts: list[str] = []
        self.code_blocks: list[str] = []
        self._in_title = False
        self._main_depth = 0
        self._pre_depth = 0
        self._current_code: list[str] = []
        self._skip_depth = 0

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        tag = tag.lower()
        attrs_dict = dict(attrs)
        if tag in SKIP_TAGS:
            self._skip_depth += 1
            return
        if self._skip_depth:
            return
        if tag == "title":
            self._in_title = True
        if tag == "meta" and attrs_dict.get("name", "").lower() == "description":
            self.description = attrs_dict.get("content") or ""
        if tag in {"main", "article"}:
            self._main_depth += 1
        if tag == "pre":
            self._pre_depth += 1
            if self._pre_depth == 1:
                self._current_code = []
        if tag in BLOCK_TAGS:
            self._break()

    def handle_startendtag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        self.handle_starttag(tag, attrs)
        if tag.lower() not in SKIP_TAGS:
            self.handle_endtag(tag)

    def handle_endtag(self, tag: str) -> None:
        tag = tag.lower()
        if tag in SKIP_TAGS:
            if self._skip_depth:
                self._skip_depth -= 1
            return
        if self._skip_depth:
            return
        if tag == "title":
            self._in_title = False
        if tag == "pre" and self._pre_depth:
            self._pre_depth -= 1
            if self._pre_depth == 0:
                code = _normalize_text(" ".join(self._current_code), preserve_lines=True)
                if code:
                    self.code_blocks.append(code)
                self._current_code = []
        if tag in BLOCK_TAGS:
            self._break()
        if tag in {"main", "article"} and self._main_depth:
            self._main_depth -= 1

    def handle_data(self, data: str) -> None:
        if self._skip_depth or not data.strip():
            return
        if self._in_title:
            self.title_parts.append(data)
            return
        self.all_parts.append(data)
        if self._main_depth:
            self.main_parts.append(data)
        if self._pre_depth:
            self._current_code.append(data)

    def _break(self) -> None:
        self.all_parts.append("\n")
        if self._main_depth:
            self.main_parts.append("\n")
        if self._pre_depth:
            self._current_code.append("\n")

    def result(self) -> dict[str, Any]:
        main_text = _normalize_text(" ".join(self.main_parts), preserve_lines=True)
        all_text = _normalize_text(" ".join(self.all_parts), preserve_lines=True)
        return {
            "title": _normalize_text(" ".join(self.title_parts)),
            "description": re.sub(
                r"^<!DOCTYPE\s+html>\s*", "", _normalize_text(self.description), flags=re.IGNORECASE
            ),
            "content": main_text if len(main_text) >= 100 else all_text,
            "code_blocks": self.code_blocks,
        }


def _normalize_text(value: str, preserve_lines: bool = False) -> str:
    value = value.replace("\xa0", " ")
    if not preserve_lines:
        return re.sub(r"\s+", " ", value).strip()
    lines = [re.sub(r"[ \t]+", " ", line).strip() for line in value.splitlines()]
    return "\n".join(line for line in lines if line)


def _plain_text(fragment: str) -> str:
    parser = DocumentParser()
    parser.feed(fragment)
    parser.close()
    return parser.result()["content"]


def _official_url(value: str) -> str:
    url = urljoin(BASE_URL, value.replace("/source/", "/document/detail/"))
    parsed = urlparse(url)
    if parsed.scheme != "https" or parsed.hostname != ALLOWED_HOST:
        raise DocsSearchError(f"refusing non-official documentation URL: {url}")
    return url


def _get(url: str, timeout: float, *, search_request: bool = False) -> tuple[bytes, str, str]:
    headers = {
        "Accept": "application/json" if search_request else "text/html,application/xhtml+xml",
        "Referer": f"{BASE_URL}/",
        "User-Agent": USER_AGENT,
    }
    if search_request:
        headers["x-request-type"] = "machine"
    request = Request(url, headers=headers)
    try:
        with urlopen(request, timeout=timeout) as response:
            final_url = response.geturl()
            _official_url(final_url)
            charset = response.headers.get_content_charset() or "utf-8"
            return response.read(), charset, final_url
    except HTTPError as exc:
        raise DocsSearchError(f"HTTP {exc.code} for {url}") from exc
    except URLError as exc:
        raise DocsSearchError(f"request failed for {url}: {exc.reason}") from exc


def search_documents(
    keyword: str,
    *,
    lang: str,
    doc_type: str,
    page: int,
    max_results: int,
    version: str | None,
    timeout: float,
) -> list[dict[str, Any]]:
    encoded_keyword = base64.b64encode(keyword.strip().encode("utf-8")).decode("ascii")
    params = {
        "keyword": encoded_keyword,
        "lang": lang,
        "type": doc_type,
        "pageNum": page,
        "pageSize": max_results,
        "sort": 1,
        "ignoreCorrection": "false",
        "searchType": "true",
    }
    body, charset, _ = _get(f"{SEARCH_URL}?{urlencode(params)}", timeout, search_request=True)
    try:
        payload = json.loads(body.decode(charset))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise DocsSearchError("official search endpoint returned invalid JSON") from exc

    if not payload.get("success"):
        raise DocsSearchError(str(payload.get("msg") or "official search request failed"))
    records = payload.get("data", {}).get("data", [])
    if not isinstance(records, list):
        raise DocsSearchError("official search endpoint returned an unexpected data shape")

    results: list[dict[str, Any]] = []
    for item in records:
        if not isinstance(item, dict) or not item.get("docUrl"):
            continue
        item_version = str(item.get("version") or "")
        if version and version.casefold() not in item_version.casefold():
            continue
        results.append(
            {
                "title": _plain_text(str(item.get("docTitle") or "")),
                "summary": _plain_text(str(item.get("docContent") or "")),
                "url": _official_url(str(item["docUrl"])),
                "version": item_version,
                "publish_time": str(item.get("publishTime") or ""),
            }
        )
    return results


def _excerpts(content: str, keyword: str, *, radius: int = 600, limit: int = 3) -> list[str]:
    folded_content = content.casefold()
    folded_keyword = keyword.casefold()
    excerpts: list[str] = []
    cursor = 0
    last_end = -1
    while len(excerpts) < limit:
        match = folded_content.find(folded_keyword, cursor)
        if match < 0:
            break
        start = max(0, match - radius)
        end = min(len(content), match + len(keyword) + radius)
        cursor = match + len(keyword)
        if start <= last_end:
            continue
        excerpt = content[start:end].strip()
        if start:
            excerpt = "..." + excerpt
        if end < len(content):
            excerpt += "..."
        excerpts.append(excerpt)
        last_end = end
    return excerpts


def fetch_document(
    result: dict[str, Any], keyword: str, *, timeout: float, full_content: bool
) -> dict[str, Any]:
    body, charset, final_url = _get(result["url"], timeout)
    try:
        html = body.decode(charset)
    except UnicodeDecodeError:
        html = body.decode("utf-8", errors="replace")
    parser = DocumentParser()
    parser.feed(html)
    parser.close()
    parsed = parser.result()
    content = parsed.pop("content")
    code_matches = [code for code in parsed["code_blocks"] if keyword.casefold() in code.casefold()]
    fetched = {
        "url": final_url,
        "title": parsed["title"] or result["title"],
        "description": parsed["description"],
        "content_length": len(content),
        "keyword_found": keyword.casefold() in content.casefold(),
        "excerpts": _excerpts(content, keyword),
        "matching_code_blocks": code_matches[:5],
    }
    if full_content:
        fetched["content"] = content
    return fetched


def _bounded_int(minimum: int, maximum: int):
    def parse(value: str) -> int:
        number = int(value)
        if not minimum <= number <= maximum:
            raise argparse.ArgumentTypeError(f"must be between {minimum} and {maximum}")
        return number

    return parse


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("keyword", help="API name or documentation search phrase")
    parser.add_argument("--lang", choices=("zh", "en"), default="zh")
    parser.add_argument("--doc-type", choices=("DOC", "API"), default="DOC")
    parser.add_argument("--page", type=_bounded_int(1, 100), default=1)
    parser.add_argument("--max-results", type=_bounded_int(1, 10), default=5)
    parser.add_argument("--version", help="case-insensitive version substring")
    parser.add_argument("--fetch", action="store_true", help="fetch matching result pages")
    parser.add_argument("--fetch-limit", type=_bounded_int(1, 10), default=3)
    parser.add_argument("--full-content", action="store_true", help="include fetched page text")
    parser.add_argument("--timeout", type=float, default=15.0)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    output: dict[str, Any] = {
        "success": False,
        "query": args.keyword,
        "lang": args.lang,
        "version_filter": args.version,
        "results": [],
    }
    try:
        results = search_documents(
            args.keyword,
            lang=args.lang,
            doc_type=args.doc_type,
            page=args.page,
            max_results=args.max_results,
            version=args.version,
            timeout=args.timeout,
        )
        if args.fetch or args.full_content:
            for result in results[: args.fetch_limit]:
                result["document"] = fetch_document(
                    result, args.keyword, timeout=args.timeout, full_content=args.full_content
                )
        output.update({"success": True, "count": len(results), "results": results})
        print(json.dumps(output, ensure_ascii=False, indent=2))
        return 0 if results else 2
    except (DocsSearchError, ValueError) as exc:
        output["error"] = str(exc)
        print(json.dumps(output, ensure_ascii=False, indent=2))
        return 1


if __name__ == "__main__":
    sys.exit(main())
