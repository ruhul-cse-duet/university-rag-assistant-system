import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from collections import deque
from io import BytesIO
from pypdf import PdfReader


def _same_domain(url, base_netloc):
    return urlparse(url).netloc == base_netloc


def _clean_html(html: str) -> str:
    soup = BeautifulSoup(html, "html.parser")
    for tag in soup(["script", "style", "noscript"]):
        tag.extract()
    text = soup.get_text(separator="\n")
    return "\n".join([line.strip() for line in text.splitlines() if line.strip()])


def _extract_pdf_text(content: bytes) -> str:
    reader = PdfReader(BytesIO(content))
    pages = []
    for page in reader.pages:
        try:
            pages.append(page.extract_text() or "")
        except Exception:
            continue
    return "\n".join([p.strip() for p in pages if p.strip()])


def scrape_website(
    url: str,
    max_pages: int = 800,
    max_pdfs: int = 200,
    same_domain: bool = True,
    pdf_max_mb: int = 15,
) -> str:
    """
    Crawl a site (starting from `url`), collect HTML and PDF text, and return combined text.
    Designed for notice pages where PDF links contain notices.
    """
    session = requests.Session()
    session.headers.update({"User-Agent": "Mozilla/5.0 (RAG-Univ-Assistant)"})

    parsed = urlparse(url)
    base_netloc = parsed.netloc

    queue = deque([url])
    visited = set()
    collected_texts = []
    pdf_count = 0
    page_count = 0
    pdf_max_bytes = pdf_max_mb * 1024 * 1024

    while queue and (page_count < max_pages or pdf_count < max_pdfs):
        current = queue.popleft()
        if current in visited:
            continue
        visited.add(current)

        try:
            resp = session.get(current, timeout=20)
        except Exception:
            continue

        ctype = resp.headers.get("Content-Type", "").lower()

        # Handle PDFs
        if "application/pdf" in ctype or current.lower().endswith(".pdf"):
            if pdf_count >= max_pdfs:
                continue
            if len(resp.content) > pdf_max_bytes:
                continue
            try:
                pdf_text = _extract_pdf_text(resp.content)
                if pdf_text:
                    collected_texts.append(pdf_text)
                    pdf_count += 1
            except Exception:
                continue
            continue

        # Handle HTML
        if "text/html" in ctype or ctype == "":
            page_count += 1
            cleaned = _clean_html(resp.text)
            if cleaned:
                collected_texts.append(cleaned)

            # Enqueue links
            soup = BeautifulSoup(resp.text, "html.parser")
            for a in soup.find_all("a", href=True):
                href = a["href"].strip()
                if href.startswith("#") or href.startswith("mailto:") or href.startswith("javascript:"):
                    continue
                next_url = urljoin(current, href)
                parsed_next = urlparse(next_url)
                if parsed_next.scheme not in ("http", "https"):
                    continue
                if same_domain and not _same_domain(next_url, base_netloc):
                    continue
                if next_url not in visited and len(visited) + len(queue) < (max_pages + max_pdfs) * 2:
                    queue.append(next_url)

            # Collect PDF links found in page
            for a in soup.find_all("a", href=True):
                href = a["href"].strip()
                if href.lower().endswith(".pdf"):
                    next_url = urljoin(current, href)
                    if next_url not in visited and pdf_count < max_pdfs:
                        queue.append(next_url)

    if not collected_texts:
        return ""

    return "\n\n".join(collected_texts)
