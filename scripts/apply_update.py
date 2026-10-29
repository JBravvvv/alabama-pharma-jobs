"""Apply one day's refresh and rebuild the site.
usage: python3 scripts/apply_update.py YYYY-MM-DD data/new_rows.txt data/closed.txt [data/skipped.txt]
new_rows: id|title|company|location|listed|min|max|car|q|yrs|ote   closed / skipped: one LinkedIn id per line
rows.txt fields: id|title|company|locations|listed|min|max|car|q|yrs|ote|count|all ids (comma list)
data/ignored.txt: ids already looked at and left off (not healthcare field sales, not Alabama), so they aren't re-fetched.
"""
import re, sys, subprocess, datetime
TODAY, NEW, CLOSED = sys.argv[1], sys.argv[2], sys.argv[3]
SKIP = sys.argv[4] if len(sys.argv) > 4 else None
ROWS, IGN = 'data/rows.txt', 'data/ignored.txt'
import os

KEEP = r'pharma|biotech|biolog|oncolog|hematolog|specialty|sales rep|sales specialist|territory|account (manager|executive|specialist)|key account|clinical (sales|specialist|consultant)|medical (sales|device)|device|surgical|ortho|spine|implant|diagnostic|lab|vaccine|neuro|cardio|derm|immunolog|rare|therapeutic|med sales|business manager|sales consultant|sales associate|sales manager|sales executive|representative|specialist'
NOT_HEALTH = r'insurance|realty|motors|solar|roofing|wireless|bank|financial|staffing|logistics|foods|beverage|automotive|security|aflac|primerica|globe life|bankers life|state farm|mutual|amazon|walmart|lowe|home depot|cintas|uline|adt|sherwin|philip morris|airgas|chart industries|deloitte|wolters kluwer|amcor|spectrum|paylocity|adp|equipmentshare|daxko|regions|henkel|advantage solutions|hiller|pepperl|comfort keepers|hexarmor|optavise|koalafi|duraserv|advance local|encompass|adapthealth|smile doctors|bradford|naphcare|laseraway|sono bello|advanced navigation|rochester electronics|pursuit|empower brands|mccorquodale|ally property|risus|harris computer|guideway|numotion|insight global|paladin|johnson controls|masa\b|bureau veritas|alten|abb\b|core & main|tricon|trelleborg|blastone|fix supply|control systems|coverall|alleviation|alliance risk|fluid flow|times microwave|directpath|ppg|medical eyeglass|talented medical|apt\b'
HEALTH = r'pharma|bio|therapeut|medical|health|diagnost|lab|surgical|ortho|scien|oncolog|vaccin|medtech|syneos|amplity|inizio|iqvia|pfizer|merck|novartis|lilly|abbvie|amgen|gilead|astrazeneca|bristol|sanofi|gsk|bayer|takeda|novo|boehringer|johnson|janssen|abbott|stryker|medtronic|boston scientific|zimmer|smith|arthrex|intuitive|edwards|becton|\bbd\b|baxter|hologic|olympus|dexcom|insulet|teleflex|conmed|cook|integra|convatec|depuy|alcon|bausch|regeneron|biogen|vertex|alnylam|incyte|natera|quest|labcorp|siemens|philips|ge healthcare|steris|globus|otsuka|lundbeck|teva|sumitomo|supernus|axsome|alkermes|ipsen|ucb|argenx|eisai|astellas|csl|sobi|ionis|corcept|collegium|vanda|praxis|coloplast|inspire|canon|leica|thermo|tempus|cardinal|medline|agiliti|avanos|nobel|cynosure|heartflow|cleerly|karius|rxsalespros'
def healthcare(title, co):
    t, c = title.lower().replace('alabama', ' '), co.lower().replace('alabama', ' ')
    if re.search(NOT_HEALTH, c): return False
    if not re.search(KEEP, t): return False
    if re.search(r'client engagement|inside|remote', t): return False
    return bool(re.search(HEALTH, c) or re.search(r'pharma|biotech|oncolog|medical|surgical|device|ortho|diagnostic|lab|vaccine|neuro|cardio|derm|immunolog|rare|clinical|health|wound|ostomy|respiratory|infusion', t))

T = lambda s: re.sub(r'[^a-z0-9]+', ' ', s.lower().replace('&', ' and ')).strip()
rows = [l.rstrip('\n').split('|') for l in open(ROWS) if l.strip()]
for r in rows:
    r += [''] * (13 - len(r))
    if not r[12]: r[12] = r[0]
ignored = set(open(IGN).read().split()) if os.path.exists(IGN) else set()
new_ignored = set()
closed = {l.strip() for l in open(CLOSED) if l.strip()}
before = len(rows)
gone = [r for r in rows if r[0] in closed]
rows = [r for r in rows if r[0] not in closed]
closed_titles = {T(r[1]) for r in gone}
index = {T(r[2]) + '|' + T(r[1]): r for r in rows}
by_title = {T(r[1]): r for r in rows}
added, merged, skipped = [], 0, []
for l in open(NEW):
    if not l.strip(): continue
    p = l.rstrip('\n').split('|'); p += [''] * (11 - len(p))
    id_, title, co, loc = p[0], p[1], p[2], p[3]
    if not healthcare(title, co): skipped.append(f'{co} – {title}'); new_ignored.add(id_); continue
    loc = re.sub(r', AL\b', '', loc)
    if co == 'BioSpace' and T(title) in closed_titles: new_ignored.add(id_); continue   # repost of a job that just closed
    hit = index.get(T(co) + '|' + T(title)) or (by_title.get(T(title)) if co == 'BioSpace' else None)
    if hit:
        locs = hit[3].split(' / ')
        if loc and loc not in locs: hit[3] = ' / '.join(locs + [loc])
        ids = hit[12].split(',')
        if id_ not in ids: ids.append(id_); hit[12] = ','.join(ids)
        hit[11] = str(max(int(hit[11] or 1), len(ids))); merged += 1; continue
    r = p[:11] + ['1', id_]; r[3] = loc
    rows.append(r); index[T(co) + '|' + T(title)] = r; by_title.setdefault(T(title), r); added.append(f'{co} – {title}')
open(ROWS, 'w').write('\n'.join('|'.join(r[:13]) for r in rows) + '\n')
if SKIP and os.path.exists(SKIP): new_ignored |= set(open(SKIP).read().split())
for g in gone: new_ignored |= set(g[12].split(','))   # closed postings: never re-add
ignored |= new_ignored
open(IGN, 'w').write('\n'.join(sorted(ignored)) + '\n')
d = datetime.date.fromisoformat(TODAY); label = d.strftime('%b ') + str(d.day)
subprocess.run([sys.executable, 'scripts/build_jobs.py', TODAY, 'data/jobs.json'], check=True, capture_output=True)
subprocess.run([sys.executable, 'scripts/build_page.py', 'data/jobs.json', label, 'index.html'], check=True, capture_output=True)
print(f'BEFORE {before} | CLOSED {len(gone)} | ADDED {len(added)} | MERGED {merged} | NOW {len(rows)}')
for g in gone: print('  closed:', g[2], '–', g[1])
for a in added: print('  added:', a)
for s in skipped[:40]: print('  skipped (not healthcare sales):', s)
