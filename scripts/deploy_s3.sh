#!/usr/bin/env bash
# Berean — publish the site to S3 (+ CloudFront), the hosting path in docs/06.
#
# Berean is static, so "deploying" is copying files with the right cache headers.
# The site must be served from the REPO ROOT: web/ fetches ../library/, and the
# root index.html redirects to web/.
#
#   BUCKET=my-bucket [DISTRIBUTION=E123ABC] bash scripts/deploy_s3.sh [--dry-run]
#
# Headers matter more than usual here:
#   index.html, sw.js  — never cached, or a reader is stuck on an old service
#                        worker and never sees an update
#   web/*              — five minutes, so app changes land quickly
#   library/*          — a day; Scripture does not change, and the service worker
#                        caches it locally anyway
set -euo pipefail
cd "$(dirname "$0")/.."

: "${BUCKET:?set BUCKET=your-bucket-name}"
DRY=""
[ "${1:-}" = "--dry-run" ] && DRY="--dryrun"

echo "Verifying the library before publishing anything…"
python3 scripts/check_all.py

S3="s3://$BUCKET"
echo "→ $S3"

# the library: big, immutable in practice, cached for a day
aws s3 sync library "$S3/library" $DRY --delete \
  --cache-control "public, max-age=86400" \
  --exclude "*.py" --exclude "__pycache__/*"

# the app: small, cached briefly so updates land
aws s3 sync web "$S3/web" $DRY --delete \
  --cache-control "public, max-age=300" \
  --exclude "sw.js" --exclude "*.md"

# the two files that must never be served stale
aws s3 cp web/sw.js "$S3/web/sw.js" $DRY \
  --cache-control "no-cache, must-revalidate" --content-type "application/javascript"
aws s3 cp web/index.html "$S3/web/index.html" $DRY \
  --cache-control "no-cache, must-revalidate" --content-type "text/html; charset=utf-8"
aws s3 cp index.html "$S3/index.html" $DRY \
  --cache-control "no-cache, must-revalidate" --content-type "text/html; charset=utf-8"
aws s3 cp web/manifest.webmanifest "$S3/web/manifest.webmanifest" $DRY \
  --cache-control "public, max-age=300" --content-type "application/manifest+json"

# the documents the footer links to
for f in ROADMAP.md DEDICATION.md README.md LICENSE; do
  [ -f "$f" ] && aws s3 cp "$f" "$S3/$f" $DRY --cache-control "public, max-age=3600"
done

if [ -n "${DISTRIBUTION:-}" ] && [ -z "$DRY" ]; then
  echo "Invalidating CloudFront $DISTRIBUTION…"
  aws cloudfront create-invalidation --distribution-id "$DISTRIBUTION" \
    --paths "/index.html" "/web/*" "/library/*" >/dev/null
  echo "  invalidated"
fi

echo "Done. CloudFront must have compression enabled — the corpus is JSON and"
echo "compresses about four to one; without it every reader pays for that."
