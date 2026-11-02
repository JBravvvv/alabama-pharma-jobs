#!/bin/bash
# Alabama refresh, step 3. Rebuilds from /tmp/alrepo/data/{new_rows,closed,skipped}.txt and pushes to GitHub.
# usage: bash /tmp/alrepo/scripts/publish.sh YYYY-MM-DD
# Sign-in: the GitHub token saved in iCloud > Job Dashboard > alabama-site > .gh > hosts.yml.
# iCloud offloads that file, so the run must download it first (device_stage_files on that path) before calling this.
set -e
HOSTS="$HOME/mnt/Job Dashboard/alabama-site/.gh/hosts.yml"
head -c 1 "$HOSTS" >/dev/null 2>&1 || { echo "SIGNIN_FILE_UNREADABLE: download it first (stage $HOSTS)"; exit 3; }
export AL_HOSTS="$HOSTS"
cd /tmp/alrepo
touch data/new_rows.txt data/closed.txt data/skipped.txt
python3 scripts/apply_update.py "$1" data/new_rows.txt data/closed.txt data/skipped.txt
rm -f data/new_rows.txt data/closed.txt data/skipped.txt
git add -A
if git diff --cached --quiet; then echo "NO_CHANGES"; exit 0; fi
git -c user.name="JBravvvv" -c user.email="298791448+JBravvvv@users.noreply.github.com" commit -q -m "Daily refresh $1" -m "Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
HELPER='!f(){ echo username=x-access-token; printf "password=%s\n" "$(python3 -c "import os,re;print(re.search(r\"oauth_token:\\s*(\\S+)\",open(os.environ[\"AL_HOSTS\"]).read()).group(1))")"; }; f'
git -c credential.helper= -c credential.helper="$HELPER" push -q origin main
echo "PUSHED $(git log -1 --format=%h)"
