import trafilatura

def fetch_full_article(url: str) -> str | None:
    downloaded = trafilatura.fetch_url(url)
    if downloaded is None:
        return None
    extracted = trafilatura.extract(downloaded, url=url, include_comments=False)
    return extracted