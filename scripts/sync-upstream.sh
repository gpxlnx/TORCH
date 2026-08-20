#!/usr/bin/env bash
# Sync this fork with upstream (Encod3d-Sec/TORCH) without breaking local
# customizations.
#
#   bash scripts/sync-upstream.sh
#
# Branch layout this script assumes:
#   main      - pure mirror of upstream/main. Never commit here directly.
#   customize - your personalizations, rebased onto main after each sync.
#
# On a rebase conflict the script stops and leaves you mid-rebase (normal
# `git status` / resolve / `git rebase --continue` flow applies). Nothing is
# pushed until the rebase finishes cleanly.
set -uo pipefail

VAULT="$(cd "$(dirname "$(readlink -f "$0")")/.." && pwd)"
cd "$VAULT" || exit 1

if ! git remote get-url upstream >/dev/null 2>&1; then
  echo "FAIL: no 'upstream' remote configured." >&2
  echo "  git remote add upstream https://github.com/Encod3d-Sec/TORCH.git" >&2
  exit 1
fi

if [ -n "$(git status --porcelain)" ]; then
  echo "FAIL: working tree not clean. Commit or stash before syncing." >&2
  exit 1
fi

echo "== fetching upstream/main =="
git fetch upstream main || exit 1

echo "== fast-forwarding main =="
git checkout main || exit 1
git merge --ff-only upstream/main || {
  echo "FAIL: main is not a fast-forward of upstream/main (was it committed to directly?)." >&2
  exit 1
}
git push origin main || exit 1

echo "== rebasing customize onto main =="
git checkout customize || exit 1
if ! git rebase main; then
  echo "" >&2
  echo "CONFLICT: resolve, then 'git add <files>' + 'git rebase --continue'." >&2
  echo "Abort instead with: git rebase --abort" >&2
  exit 1
fi

echo "== pushing customize =="
git push origin customize --force-with-lease || exit 1

echo "done: main mirrors upstream, customize rebased and pushed."

if [ -f "$VAULT/scripts/campaign-doctor.py" ]; then
  echo ""
  echo "== campaign-health check (scripts/hooks/skills wiring) =="
  python3 "$VAULT/scripts/campaign-doctor.py" || echo "^ fix above, then re-run or apply manually (setup/install-skills.sh, setup/install-hooks.sh)."
fi
