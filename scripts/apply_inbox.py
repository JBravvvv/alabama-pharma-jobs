"""Run by the GitHub Action. Applies every inbox/<YYYY-MM-DD>.txt the daily Claude run uploads, then rebuilds
index.html and refresh/payload.txt. Inbox format:
#NEW
id|title|company|location|listed|min|max|car|q|yrs|ote   (one per line)
#CLOSED
<linkedin id per line>
#SKIP
<linkedin id per line>
Files named test*.txt are deleted without being applied. A file that would close more than 40% of the jobs is
moved to inbox/rejected/ instead (LinkedIn answered badly; the jobs didn't really close)."""
import glob, os, re, subprocess, sys, json, shutil
os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
def rows():
    return [l.rstrip('\n').split('|') for l in open('data/rows.txt') if l.strip()]
for path in sorted(glob.glob('inbox/*.txt')):
    name = os.path.basename(path)
    if name.lower().startswith('test'):
        print('TEST FILE, deleted:', name); os.remove(path); continue
    m = re.match(r'(\d{4}-\d{2}-\d{2})', name)
    if not m: print('SKIPPED (bad name):', name); continue
    sec = {'NEW': [], 'CLOSED': [], 'SKIP': []}; cur = None
    for line in open(path, encoding='utf-8'):
        line = line.rstrip('\n').rstrip('\r')
        if line.strip() in ('#NEW', '#CLOSED', '#SKIP'): cur = line.strip()[1:]; continue
        if cur and line.strip(): sec[cur].append(line.strip() if cur != 'NEW' else line)
    on_site = len(rows())
    if on_site and len(sec['CLOSED']) > 0.4 * on_site:
        os.makedirs('inbox/rejected', exist_ok=True); shutil.move(path, 'inbox/rejected/' + name)
        print(f'REJECTED {name}: {len(sec["CLOSED"])} of {on_site} marked closed'); continue
    open('data/new_rows.txt', 'w').write('\n'.join(sec['NEW']) + '\n')
    open('data/closed.txt', 'w').write('\n'.join(sec['CLOSED']) + '\n')
    open('data/skipped.txt', 'w').write('\n'.join(sec['SKIP']) + '\n')
    r = subprocess.run([sys.executable, 'scripts/apply_update.py', m.group(1), 'data/new_rows.txt', 'data/closed.txt', 'data/skipped.txt'], capture_output=True, text=True)
    print(r.stdout); print(r.stderr, file=sys.stderr)
    for f in ('data/new_rows.txt', 'data/closed.txt', 'data/skipped.txt'): os.remove(f)
    if r.returncode: sys.exit(r.returncode)
    os.remove(path)
# Payload for the next run: the ids to recheck / already handled, then the scraper, ready to paste into a LinkedIn tab.
rs = rows(); known = [r[0] for r in rs]; seen = set(known)
for r in rs:
    if len(r) > 12 and r[12]: seen |= set(r[12].split(','))
if os.path.exists('data/ignored.txt'): seen |= set(open('data/ignored.txt').read().split())
os.makedirs('refresh', exist_ok=True)
payload = ('window.__AL_KNOWN=' + json.dumps(known, separators=(',', ':')) + ';window.__AL_SEEN=' + json.dumps(sorted(seen), separators=(',', ':')) + ';\n'
           + open('scripts/scrape_alabama.js', encoding='utf-8').read())
open('refresh/payload.txt', 'w', encoding='utf-8').write(payload)
open('refresh/status.json', 'w').write(json.dumps({'jobs_on_site': len(known), 'seen': len(seen), 'payload_chars': len(payload)}))
print('PAYLOAD', len(payload), 'chars;', len(known), 'jobs on site')
