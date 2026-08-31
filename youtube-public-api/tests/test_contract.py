#!/usr/bin/env python3
import re
from pathlib import Path

root = Path(__file__).parents[1]
text = (root / 'SKILL.md').read_text()
expected = [
    '/v1/youtube/search', '/v1/youtube/video/{id}', '/v1/youtube/channel/{id}',
    '/v1/youtube/comments/{id}', '/v1/youtube/playlist/{id}',
    '/v1/youtube/related/{id}', '/v1/youtube/transcript/{id}',
]
assert all(p in text for p in expected)
assert text.count('`GET /v1/youtube/') == 7
assert 'ReplyNodes' not in text.split('\n', 12)[0:12].__str__()
assert '# YouTube Public Data' in text
assert 'payment requirements only' in text
assert 'does not implement payment' in text
assert 'No YouTube login' in text
assert 'cookies' in text and 'publishing' in text
assert (root / 'VERSION').read_text().strip() == '1.0.1'
print('PASS route_count=7 naming=x402-read-only-boundary')
