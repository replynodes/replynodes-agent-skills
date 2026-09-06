# Endpoint examples - App Store Public Reads (v1)

All operations below are GET-only public reads. Replace `BASE_URL` with your
workspace gateway URL and `API_KEY` with your ReplyNodes fetcher API key.
Never commit real keys.

- The nine documented read operations have stable public contracts with bounded requests and normalized v1 responses.
- Route paths in this catalog are stable capability identifiers used for agent tool bindings; public gateway exposure for this platform is issued to your workspace at onboarding and must not be assumed reachable anywhere else.
- No availability, uptime, latency, or success-rate figure is claimed anywhere in this package; example payloads are illustrative fixtures, not captured responses.

## Generic HTTP (curl)

### GET /v1/appstore/app - lookup by track id

```sh
curl -sS \
  -H 'Authorization: Bearer ***' \
  "BASE_URL/v1/appstore/app?id=553834731"
```

### GET /v1/appstore/app - lookup by bundle id

```sh
curl -sS \
  -H 'Authorization: Bearer ***' \
  "BASE_URL/v1/appstore/app?appId=com.example.app"
```

### GET /v1/appstore/developer - lookup by track id

```sh
curl -sS \
  -H 'Authorization: Bearer ***' \
  "BASE_URL/v1/appstore/developer?id=553834731"
```

### GET /v1/appstore/developer - lookup by bundle id

```sh
curl -sS \
  -H 'Authorization: Bearer ***' \
  "BASE_URL/v1/appstore/developer?appId=com.example.app"
```

### GET /v1/appstore/list - storefront chart listing

```sh
curl -sS \
  -H 'Authorization: Bearer ***' \
  "BASE_URL/v1/appstore/list?category=TOP_FREE&country=us"
```

### GET /v1/appstore/privacy - lookup by track id

```sh
curl -sS \
  -H 'Authorization: Bearer ***' \
  "BASE_URL/v1/appstore/privacy?id=553834731"
```

### GET /v1/appstore/privacy - lookup by bundle id

```sh
curl -sS \
  -H 'Authorization: Bearer ***' \
  "BASE_URL/v1/appstore/privacy?appId=com.example.app"
```

### GET /v1/appstore/ratings - lookup by track id

```sh
curl -sS \
  -H 'Authorization: Bearer ***' \
  "BASE_URL/v1/appstore/ratings?id=553834731"
```

### GET /v1/appstore/ratings - lookup by bundle id

```sh
curl -sS \
  -H 'Authorization: Bearer ***' \
  "BASE_URL/v1/appstore/ratings?appId=com.example.app"
```

### GET /v1/appstore/reviews - paged by country

```sh
curl -sS \
  -H 'Authorization: Bearer ***' \
  "BASE_URL/v1/appstore/reviews?id=553834731&country=us"
```

### GET /v1/appstore/search - bounded term search

```sh
curl -sS \
  -H 'Authorization: Bearer ***' \
  "BASE_URL/v1/appstore/search?term=test"
```

### GET /v1/appstore/similar - related apps

```sh
curl -sS \
  -H 'Authorization: Bearer ***' \
  "BASE_URL/v1/appstore/similar?id=553834731"
```

### GET /v1/appstore/suggest - type-ahead suggestions

```sh
curl -sS \
  -H 'Authorization: Bearer ***' \
  "BASE_URL/v1/appstore/suggest?term=tes&country=us"
```

## Normalized errors

Every non-2xx response uses the envelope above with one of: `400 invalid_request`, `401 invalid_or_expired_token`, `404 not_found`, `429 rate_limited`, `502 upstream_unavailable`, `503 degraded`.

An unauthenticated request to a priced route returns `402` with an x402 v2 challenge, not `401` — `401` is reserved for a Bearer key that is present but invalid, malformed, expired, or revoked, and the gateway does not fall back to x402 in that case; it fails closed.

The full meaning table lives in this file; retry only idempotent reads on 502/503 with backoff, treat 400/404 as terminal for the attempt, and honor `Retry-After` on 429.