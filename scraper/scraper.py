import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from collections import deque 

BASE_URL = "https://kjsit.somaiya.edu.in"
DOMAIN = "kjsit.somaiya.edu.in"

visited_urls = set()


def fetch_page(url):
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        return response.text
    except Exception as e:
        print(f"Error fetching {url}: {e}")
        return None


def extract_text(html):
    soup = BeautifulSoup(html, "lxml")
    title = soup.title.string.strip() if soup.title else ""

    # Remove unwanted tags
    for tag in soup(["script", "style", "noscript", "nav", "footer", "header"]):
        tag.decompose()

    # Try to find main article content
    content_div = soup.find("div", class_="field--name-body")

    if not content_div:
        content_div = soup.find("main")

    if not content_div:
        content_div = soup.body

    text = content_div.get_text(separator="\n")

    lines = [line.strip() for line in text.split("\n")]
    clean_lines = [line for line in lines if line]

    body_text = "\n".join(clean_lines)
    return title + "\n\n" + body_text

def extract_links(html, base_url):
    soup = BeautifulSoup(html, "lxml")
    links = set()

    for a in soup.find_all("a", href=True):
        href = a["href"]
        full_url = urljoin(base_url, href)

        parsed = urlparse(full_url)

        if DOMAIN in parsed.netloc:
            links.add(full_url)

    return links


from collections import deque

IMPORTANT_KEYWORDS = [
    "principal-words",
    "about",
    "admission",
    "programme",
    "academics",
    "research",
    "placement"
]

JUNK_PATTERNS = [
    "#",
    "login",
    "portal",
    "newsletter",
    "gallery",
    "old",
    ".pdf",
    "staff-directory",
    "faculty-directory"
]

def is_valid_url(url):
    parsed = urlparse(url)

    # Restrict to KJSIT domain only
    if parsed.netloc != DOMAIN:
        return False

    url_lower = url.lower()

    # Reject junk
    if any(junk in url_lower for junk in JUNK_PATTERNS):
        return False

    # Allow only meaningful sections
    if not any(keyword in url_lower for keyword in IMPORTANT_KEYWORDS):
        return False

    return True


def crawl(start_url, max_depth=2):
    visited = set()
    queue = deque([(start_url, 0)])
    all_text_data = []

    while queue:
        url, depth = queue.popleft()

        if depth > max_depth:
            continue

        if url in visited:
            continue

        print(f"Scraping (depth {depth}): {url}")
        visited.add(url)

        html = fetch_page(url)
        if not html:
            continue

        text = extract_text(html)
        if text:
            all_text_data.append((url, text))

        links = extract_links(html, url)

        for link in links:
            if link not in visited and is_valid_url(link):
                queue.append((link, depth + 1))

    return all_text_data


if __name__ == "__main__":
    pages = crawl(BASE_URL, max_depth=2)

    print("\n\n--- SAMPLE OUTPUT ---\n")
    print(pages[0][:1000])