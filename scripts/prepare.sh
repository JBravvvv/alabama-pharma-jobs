#!/bin/bash
# Daily refresh, step 1: fresh copy of the site repo in /tmp/alrepo, plus the ids the browser script needs.
set -e
D="$HOME/mnt/Job Dashboard/alabama-site"
rm -rf /tmp/alrepo
git -c credential.helper= -c credential.helper="!GH_CONFIG_DIR='$D/.gh' '$D/.bin/gh' auth git-credential" clone -q https://github.com/JBravvvv/alabama-pharma-jobs.git /tmp/alrepo
cd /tmp/alrepo
echo "JOBS_ON_SITE $(grep -c . data/rows.txt)"
python3 - <<'PY'
import json, os
rows = [l.rstrip('\n').split('|') for l in open('data/rows.txt') if l.strip()]
known = [r[0] for r in rows]
seen = set(known)
for r in rows:
    if len(r) > 12 and r[12]: seen |= set(r[12].split(','))
if os.path.exists('data/ignored.txt'): seen |= set(open('data/ignored.txt').read().split())
print('window.__AL_KNOWN=' + json.dumps(known, separators=(',', ':')) + ';')
print('window.__AL_SEEN=' + json.dumps(sorted(seen), separators=(',', ':')) + ';')
print('KNOWN_COUNT', len(known), 'SEEN_COUNT', len(seen))
PY
