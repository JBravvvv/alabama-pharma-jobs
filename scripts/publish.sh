#!/bin/bash
# Daily refresh, step 3: rebuild from /tmp/alrepo/data/new_rows.txt, closed.txt, skipped.txt and push to GitHub.
# usage: publish.sh YYYY-MM-DD
set -e
D="$HOME/mnt/Job Dashboard/alabama-site"
cd /tmp/alrepo
touch data/new_rows.txt data/closed.txt data/skipped.txt
python3 scripts/apply_update.py "$1" data/new_rows.txt data/closed.txt data/skipped.txt
rm -f data/new_rows.txt data/closed.txt data/skipped.txt
git add -A
if git diff --cached --quiet; then echo "NO_CHANGES"; exit 0; fi
git -c user.name="JBravvvv" -c user.email="298791448+JBravvvv@users.noreply.github.com" commit -q -m "Daily refresh $1" -m "Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
git -c credential.helper= -c credential.helper="!GH_CONFIG_DIR='$D/.gh' '$D/.bin/gh' auth git-credential" push -q origin main
echo "PUSHED $(git log -1 --format=%h)"
