#!/usr/bin/env bash
# Post-deploy smoke checks (DECISIONS D80). Run by the Deploy workflow; also by hand:
#   API=https://api.diyneco.com WEB_URLS="https://merchant.diyneco.com ..." bash infra/deployment/smoke.sh
# Checks the API answers healthily over HTTPS with its hardening headers, refuses unauthenticated
# admin access, and that every web app loads with its security headers and talks only to this API.
set -uo pipefail

API="${API:?set API to the public API address}"
WEB_URLS="${WEB_URLS:-}"
failures=0

fail() { echo "::error::$*"; failures=$((failures + 1)); }
ok() { echo "ok: $*"; }

# Retries while a fresh deployment comes up.
fetch() {
  local url="$1" out="$2"
  for _ in $(seq 1 20); do
    code="$(curl -s -o "$out.body" -D "$out.headers" -w '%{http_code}' --max-time 10 "$url" || true)"
    [ "$code" != "000" ] && [ "${code:0:1}" != 5 ] && { echo "$code"; return; }
    sleep 6
  done
  echo "$code"
}

header() { grep -i "^$2:" "$1.headers" | head -1 | cut -d: -f2- | tr -d '\r' | sed 's/^ //'; }

tmp="$(mktemp -d)"

[[ "$API" == https://* ]] || [ "${ALLOW_HTTP:-}" = 1 ] || fail "API address must be https: $API"
code="$(fetch "$API/api/v1/health" "$tmp/health")"
[ "$code" = 200 ] && ok "API health 200" || fail "API health returned $code"
[ "$(header "$tmp/health" x-content-type-options)" = nosniff ] && [ "$(header "$tmp/health" cache-control)" = no-store ] \
  && ok "API sends its hardening headers" || fail "API responses lack hardening headers"

code="$(fetch "$API/api/v1/admin/health" "$tmp/admin")"
[ "$code" = 401 ] && ok "admin health refuses anonymous callers" || fail "admin health without a token returned $code"
grep -q '"request_id"' "$tmp/admin.body" || fail "error responses are not in the standard envelope"

api_host="$(sed -E 's#^https?://([^/:]+).*#\1#' <<<"$API")"
# Registrable domain: the last two labels, or three under a country's second level (co.za).
site() { awk -F. '{ if (NF > 2 && length($NF) == 2 && $(NF-1) ~ /^(co|com|org|net|ac|gov|edu)$/) print $(NF-2)"."$(NF-1)"."$NF; else print $(NF-1)"."$NF }' <<<"$1"; }
for url in $WEB_URLS; do
  code="$(fetch "$url/" "$tmp/web")"
  [ "$code" = 200 ] && ok "$url loads" || { fail "$url returned $code"; continue; }
  csp="$(header "$tmp/web" content-security-policy)"
  grep -q "connect-src[^;]*$API" <<<"$csp" || fail "$url's Content-Security-Policy does not allow $API (built for another API?)"
  [ "$(header "$tmp/web" x-frame-options)" = DENY ] || fail "$url can be framed"
  [ -n "$(header "$tmp/web" strict-transport-security)" ] || fail "$url sends no HSTS"
  web_host="$(sed -E 's#^https?://([^/:]+).*#\1#' <<<"$url")"
  # Staff sign-in keeps the refresh token in a SameSite=Strict cookie on the API, which the
  # browser only sends when the app and the API share a site (e.g. *.diyneco.com).
  [ "$(site "$web_host")" = "$(site "$api_host")" ] \
    || fail "$url and $API are on different sites; staff sign-in would not survive a reload"
done

rm -rf "$tmp"
if [ "$failures" -gt 0 ]; then
  echo "$failures smoke check(s) failed"
  exit 1
fi
echo "all smoke checks passed"
