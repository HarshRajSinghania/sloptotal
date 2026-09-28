import pytest

from app.scraper import _check_public_url


@pytest.mark.parametrize(
    "url",
    [
        "http://127.0.0.1:8000/health",
        "http://localhost/",
        "http://169.254.169.254/latest/meta-data/",
        "http://10.0.0.5/",
        "http://192.168.1.1/",
        "http://[::1]/",
        "file:///etc/passwd",
        "ftp://example.com/",
    ],
)
async def test_rejects_non_public_urls(url):
    with pytest.raises(ValueError):
        await _check_public_url(url)


async def test_allows_public_ip():
    await _check_public_url("https://1.1.1.1/")
