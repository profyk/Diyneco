#!/usr/bin/env bash
# Vercel "Ignored Build Step" for every web app (apps/*/vercel.json). Vercel runs it from the
# app's folder: exit 0 skips the build, any other exit builds.
#
# Builds when the app, a shared package or the lockfile changed since the commit this project
# last deployed (VERCEL_GIT_PREVIOUS_SHA), not only in the newest commit: pushing several
# commits at once must never skip an app that one of the earlier commits changed.
# Builds whenever that cannot be worked out (first deployment, commit not in the clone).
# FORCE_BUILD=1 in the project's environment variables always builds, for a redeploy after
# changing environment variables (NEXT_PUBLIC_* values are fixed at build time).

if [ "${FORCE_BUILD:-}" = "1" ]; then
  echo "FORCE_BUILD=1: building."
  exit 1
fi

base="${VERCEL_GIT_PREVIOUS_SHA:-}"
if [ -z "$base" ] || ! git cat-file -e "${base}^{commit}" 2>/dev/null; then
  echo "No previous deployment to compare with: building."
  exit 1
fi

if git diff --quiet "$base" HEAD -- . ../../packages ../../pnpm-lock.yaml ../../package.json; then
  echo "Nothing for this app changed since ${base}: skipping the build."
  exit 0
fi
echo "Changes since ${base}: building."
exit 1
