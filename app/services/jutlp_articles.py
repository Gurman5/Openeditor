import random
import re
import threading
import time
from html import unescape
from urllib.parse import urljoin, urlparse

import requests
from lxml import html as lxml_html

SITEMAP_URL = "https://open-publishing.org/journals/index.php/jutlp/sitemap"
ARTICLE_PATH_RE = re.compile(r"/article/view/\d+/\d+(?:/?$|[?#])")
ARTICLE_IDS_RE = re.compile(
    r"^(?P<prefix>.+/article/view/)(?P<article_id>\d+)/\d+(?:/?(?:[?#].*)?)$"
)
ARTICLE_URL_RE = re.compile(r"https?://[^\s<>'\"]+/article/view/\d+/\d+")
RELATIVE_ARTICLE_RE = re.compile(
    r"/journals/index\.php/jutlp/article/view/\d+/\d+"
)

REQUEST_HEADERS = {
    "User-Agent": (
        "copy-editor-ai/1.0 (+https://open-publishing.org/journals/index.php/jutlp)"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}

FALLBACK_ARTICLE = {
    "title": (
        "The Artificial Intelligence Assessment Scale (AIAS): "
        "A Framework for Ethical Integration of Generative AI in Educational Assessment"
    ),
    "author": "Mike Perkins, Leon Furze, Jasper Roe, Jason MacVaugh",
    "abstract": (
        "This JUTLP article introduces the AI Assessment Scale as a practical "
        "framework for deciding when and how generative AI can be used in "
        "educational assessment. It focuses on transparent, ethical integration "
        "of AI tools while keeping learning outcomes, academic integrity, and "
        "student engagement at the centre of assessment design."
    ),
    "url": "https://open-publishing.org/journals/index.php/jutlp/article/view/810/769",
}

_CACHE_LOCK = threading.Lock()
_CACHE_UNTIL = 0.0
_CACHE_ARTICLES: list[dict] = []
_CACHE_TTL_SECONDS = 60 * 60 * 6


def get_jutlp_articles(limit: int = 10) -> list[dict]:
    """Return random published JUTLP articles, falling back safely on failure."""
    global _CACHE_ARTICLES, _CACHE_UNTIL

    limit = max(1, min(int(limit or 10), 12))

    with _CACHE_LOCK:
        cached = list(_CACHE_ARTICLES)
        cache_fresh = cached and time.time() < _CACHE_UNTIL

    if cache_fresh:
        return _sample_articles(cached, limit)

    try:
        fresh = _fetch_jutlp_articles(max_articles=18)
    except Exception:
        fresh = []

    if fresh:
        with _CACHE_LOCK:
            _CACHE_ARTICLES = fresh
            _CACHE_UNTIL = time.time() + _CACHE_TTL_SECONDS
        return _sample_articles(fresh, limit)

    if cached:
        return _sample_articles(cached, limit)
    return [FALLBACK_ARTICLE]


def _sample_articles(articles: list[dict], limit: int) -> list[dict]:
    clean = []
    for article in articles:
        normalised = _normalise_article(article)
        if normalised:
            clean.append(normalised)
    if not clean:
        return [FALLBACK_ARTICLE]
    random.shuffle(clean)
    return clean[:limit]


def _fetch_jutlp_articles(max_articles: int) -> list[dict]:
    with requests.Session() as session:
        session.headers.update(REQUEST_HEADERS)
        sitemap_html = _fetch_text(session, SITEMAP_URL, timeout=8)
        urls = _extract_article_urls(sitemap_html)
        random.shuffle(urls)

        articles = []
        for url in urls[: max(max_articles * 4, 40)]:
            article = _fetch_article(session, url)
            if article:
                articles.append(article)
            if len(articles) >= max_articles:
                break
        return articles


def _fetch_text(session: requests.Session, url: str, timeout: int) -> str:
    response = session.get(url, timeout=timeout)
    response.raise_for_status()
    return response.text


def _extract_article_urls(sitemap_html: str) -> list[str]:
    raw = unescape(sitemap_html or "")
    matches = set(ARTICLE_URL_RE.findall(raw))
    matches.update(urljoin(SITEMAP_URL, m) for m in RELATIVE_ARTICLE_RE.findall(raw))

    urls = []
    seen = set()
    for match in matches:
        url = match.strip().rstrip("/")
        parsed = urlparse(url)
        if parsed.scheme not in {"http", "https"}:
            continue
        if parsed.netloc != "open-publishing.org":
            continue
        if not ARTICLE_PATH_RE.search(parsed.path):
            continue
        if url in seen:
            continue
        seen.add(url)
        urls.append(url)
    return urls


def _fetch_article(session: requests.Session, url: str) -> dict | None:
    if not _is_valid_article_url(url):
        return None
    details_url = _article_details_url(url)
    try:
        page_html = _fetch_text(session, details_url, timeout=6)
        doc = lxml_html.fromstring(page_html)
    except Exception:
        try:
            page_html = _fetch_text(session, url, timeout=6)
            doc = lxml_html.fromstring(page_html)
        except Exception:
            return None

    article = {
        "title": _extract_title(doc),
        "author": _extract_author(doc),
        "abstract": _extract_abstract(doc),
        "url": url,
    }
    return _normalise_article(article)


def _article_details_url(url: str) -> str:
    match = ARTICLE_IDS_RE.match((url or "").rstrip("/"))
    if not match:
        return url
    return f"{match.group('prefix')}{match.group('article_id')}"


def _normalise_article(article: dict | None) -> dict | None:
    if not article:
        return None
    title = _clean_text(article.get("title"))
    abstract = _clean_text(article.get("abstract"))
    url = _clean_text(article.get("url"))
    if not title or not abstract or not _is_valid_article_url(url):
        return None
    return {
        "title": title,
        "author": _clean_text(article.get("author")),
        "abstract": abstract,
        "url": url,
    }


def _is_valid_article_url(url: str) -> bool:
    parsed = urlparse(url or "")
    return (
        parsed.scheme in {"http", "https"}
        and parsed.netloc == "open-publishing.org"
        and bool(ARTICLE_PATH_RE.search(parsed.path))
    )


def _extract_title(doc) -> str:
    for name in ("citation_title", "DC.Title", "og:title", "twitter:title"):
        value = _meta_value(doc, name)
        if value:
            return _strip_journal_suffix(value)
    for xpath in (
        "//h1[contains(@class, 'page_title')]",
        "//h1[contains(@class, 'title')]",
        "//h1",
    ):
        value = _xpath_text(doc, xpath)
        if value:
            return _strip_journal_suffix(value)
    return ""


def _extract_author(doc) -> str:
    authors = _meta_values(doc, "citation_author")
    if authors:
        return ", ".join(_clean_text(a) for a in authors if _clean_text(a))

    for xpath in (
        "//*[contains(@class, 'authors')]//*[contains(@class, 'name')]",
        "//*[contains(@class, 'authors')]//li",
        "//*[contains(@class, 'author')]//*[contains(@class, 'name')]",
    ):
        names = [_clean_text(node.text_content()) for node in doc.xpath(xpath)]
        names = [n for n in names if n]
        if names:
            return ", ".join(names)

    creator = _meta_value(doc, "DC.Creator")
    return creator or ""


def _extract_abstract(doc) -> str:
    for value in _abstract_candidates(doc):
        cleaned = _clean_abstract_candidate(value)
        if cleaned:
            return cleaned

    for name in ("DC.Description", "DCTERMS.abstract", "description", "og:description"):
        cleaned = _clean_abstract_candidate(_meta_value(doc, name))
        if cleaned:
            return cleaned
    return ""


def _abstract_candidates(doc) -> list[str]:
    candidates = []

    for xpath in (
        "//*[contains(concat(' ', normalize-space(@class), ' '), ' abstract ')]",
        "//*[contains(concat(' ', normalize-space(@class), ' '), ' item abstract ')]",
        "//section[contains(@class, 'item')][.//*[normalize-space()='Abstract']]"
        "//*[contains(@class, 'value') or self::p]",
        "//div[contains(@class, 'item')][.//*[normalize-space()='Abstract']]"
        "//*[contains(@class, 'value') or self::p]",
    ):
        value = _xpath_text(doc, xpath)
        if value:
            candidates.append(value)

    heading_xpath = (
        "//*[self::h2 or self::h3 or self::h4]"
        "[translate(normalize-space(.), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz')='abstract']"
    )
    for heading in doc.xpath(heading_xpath):
        parts = []
        node = heading.getnext()
        while node is not None and not _is_section_heading(node):
            text = _clean_text(node.text_content())
            if text:
                parts.append(text)
            node = node.getnext()
        if parts:
            candidates.append(" ".join(parts))

    return candidates


def _clean_abstract_candidate(value: str) -> str:
    text = _clean_text(value)
    if not text:
        return ""

    text = re.sub(r"^abstract\b[:\s]*", "", text, flags=re.IGNORECASE).strip()
    text = re.split(
        r"\b(?:downloads?|download data is not yet available|how to cite|"
        r"more citation formats|download citation|make a submission|scimago score)\b",
        text,
        maxsplit=1,
        flags=re.IGNORECASE,
    )[0].strip()
    text = re.sub(r"^doi:\s*https?://\S+\s*", "", text, flags=re.IGNORECASE).strip()

    lower = text.lower()
    bad_markers = (
        "download data is not yet available",
        "more citation formats",
        "download citation",
        "endnote/zotero/mendeley",
    )
    if not text or any(marker in lower for marker in bad_markers):
        return ""
    if lower.startswith(("https://doi.org/", "http://doi.org/", "doi:")):
        return ""
    if len(text.split()) < 20:
        return ""
    return text


def _is_section_heading(node) -> bool:
    tag = str(getattr(node, "tag", "")).lower()
    if tag in {"h1", "h2", "h3", "h4", "h5"}:
        return True
    classes = f" {node.get('class', '')} ".lower() if hasattr(node, "get") else ""
    return " item " in classes and bool(
        node.xpath(".//*[self::h2 or self::h3 or self::h4]")
    )


def _meta_value(doc, name: str) -> str:
    values = _meta_values(doc, name)
    return values[0] if values else ""


def _meta_values(doc, name: str) -> list[str]:
    values = doc.xpath(
        "//meta[translate(@name, 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz')=$name"
        " or translate(@property, 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz')=$name]"
        "/@content",
        name=name.lower(),
    )
    return [_clean_text(v) for v in values if _clean_text(v)]


def _xpath_text(doc, xpath: str) -> str:
    nodes = doc.xpath(xpath)
    parts = []
    for node in nodes:
        if isinstance(node, str):
            parts.append(node)
        else:
            parts.append(node.text_content())
    return _clean_text(" ".join(parts))


def _clean_text(value) -> str:
    text = unescape(str(value or ""))
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def _strip_journal_suffix(title: str) -> str:
    title = _clean_text(title)
    return re.sub(r"\s+\|\s+Journal of University Teaching.*$", "", title).strip()


def _trim_text(text: str, max_chars: int) -> str:
    text = _clean_text(text)
    if len(text) <= max_chars:
        return text
    return text[: max_chars - 3].rsplit(" ", 1)[0].rstrip(".,;:") + "..."
