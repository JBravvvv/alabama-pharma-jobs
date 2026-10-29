"""Builds data/jobs.json from data/rows.txt. usage: python3 scripts/build_jobs.py YYYY-MM-DD data/jobs.json
rows.txt (id|title|co|locs|listed|min|max|car|q|yrs|ote|n) -> jobs.json for the Alabama page."""
import re, json, sys, glob
from collections import Counter
def spec(t,c):
    s=(t+' '+c).lower()
    if re.search(r'oncolog|hematolog|myeloma|cancer|tumor|cutaneous onc',s): return 'Oncology / Hematology'
    if re.search(r'neuro|psych|ms\b|specialty ms|migraine|stroke|psychedelic',s): return 'Neuroscience / Psychiatry'
    if re.search(r'ophthalm|eye|optic',s): return 'Eye care'
    if re.search(r'immunolog|derm|aesthetic|rheumat|ibd|gastro|\bgi\b|liver',s): return 'Immunology / Dermatology'
    if re.search(r'rare|lsd|orphan|cell therapy|genetics|endo & metabol',s): return 'Rare disease'
    if re.search(r'cardio|cardiac|kidney|heart|crm|tavi|structural|metabolic|nephro|thrombo|pulmonary|cardiopulmonary',s): return 'Cardiovascular / Metabolic'
    if re.search(r'vaccin|hiv|infect',s): return 'Vaccines / Infectious disease'
    if re.search(r"women's health|gyn|obgyn",s): return "Women's health"
    if re.search(r'primary care',s): return 'Primary care'
    if re.search(r'diagnost|lab|patholog|clinical pathology|quest|natera|caris|castle bio|hemostasis|labcorp|core lab|randox',s): return 'Diagnostics / Lab'
    if re.search(r'device|surgical|surgery|ortho|spine|trauma|sports|implant|dental|vascular|ivl|shockwave|robotic|mis\b|wound|tissue|endoscop|pain treatments|insulet|zoll|vapotherm|tactile|organox|sciton|bd\b|conmed|stryker|arthrex|smith\+nephew|aesculap|convatec|integra|avanos|edwards|boston scientific|crown medical|cook medical|apria|respiratory|matriderm|hemanext|ge healthcare|cmr|applied medical|bioventus|dentsply|medical sales',s): return 'Medical device'
    return 'Other specialty'
def area(t,c,sp):
    s=(t+' '+c).lower()
    for k,v in [('lung','Oncology – lung cancer'),('breast','Oncology – breast cancer'),('myeloma','Oncology – multiple myeloma'),('hematolog','Oncology – hematology'),('cutaneous','Oncology – skin cancer'),('psychiatr','Psychiatry'),('psychedelic','Psychiatry – psychedelics'),('specialty ms','Neurology – MS'),('neurolog','Neurology'),('neuroscience','Neuroscience'),('neurocare','Neurology'),('stroke','Stroke / thrombosis'),('migraine','Neurology – migraine'),('ophthalm','Eye care – immunology'),('derm','Dermatology'),('aesthetic','Aesthetics'),('immunolog','Immunology'),('liver','Liver / rare'),('rare','Rare disease'),('lsd','Rare – lysosomal storage'),('cell therapy','Cell therapy'),('cardio kidney','Diagnostics – cardio/kidney'),('kidney','Kidney'),('cardiovascular','Cardiovascular'),('crm','Device – cardiac rhythm'),('tavi','Device – structural heart'),('heart valve','Device – structural heart'),('pulmonary','Pulmonary'),('pain','Pain'),('women','Women\'s health'),('primary care','Primary care'),('dental','Device – dental implants'),('ortho','Device – orthopedics'),('spine','Device – spine'),('trauma','Device – trauma'),('sports','Device – sports medicine'),('vascular','Device – vascular'),('surgical','Device – surgical'),('wound','Device – wound care'),('hemostasis','Diagnostics – hemostasis'),('patholog','Diagnostics – pathology'),('diagnost','Diagnostics'),('nutrition','Nutrition')]:
        if k in s: return v
    return sp
def level(t,lvl):
    s=t.lower()
    if re.search(r'district manager|area sales director|regional manager|area sales manager - arizona|senior sales leader|associate director|strategic account director|regional medical sales executive|head of',s): return 'Manager / Director'
    if re.search(r'associate|entry level|\(entry',s) or lvl=='Entry level': return 'Entry / Associate'
    if re.search(r'account manager|key account|account executive|kam|territory manager|territory business manager|territory sales manager|account specialist|account liaison|development executive|strategic account liaison',s): return 'Account Manager / KAM'
    if re.search(r'senior|sr\.?|specialist|consultant',s): return 'Specialist / Senior'
    return 'Sales Representative'

TODAY = sys.argv[1]; OUT = sys.argv[2]; ROWS = sys.argv[3] if len(sys.argv) > 3 else 'data/rows*.txt'

CITY = [
 ('BHM', 'birmingham|hoover|vestavia|homewood|mountain brook|pelham|alabaster|trussville|bessemer|helena|irondale|leeds|gardendale|chelsea|calera|hueytown|fultondale|jasper'),
 ('HSV', 'huntsville|madison|decatur|athens|hartselle|harvest|cullman|scottsboro|guntersville|north alabama'),
 ('MGM', 'montgomery|prattville|millbrook|wetumpka|pike road|selma'),
 ('MOB', 'mobile|daphne|fairhope|spanish fort|foley|gulf shores|saraland|theodore'),
 ('TCL', 'tuscaloosa|northport|university of alabama'),
 ('AUB', 'auburn|opelika|phenix city'),
 ('DHN', 'dothan|enterprise|ozark'),
 ('SHL', 'florence|muscle shoals|sheffield|tuscumbia'),
 ('GAD', 'gadsden|anniston|oxford|talladega'),
]
def cities_of(locs, title):
    tags = []
    for c, pat in CITY:
        if re.search(r'\b(' + pat + r')\b', locs.lower()) or re.search(r'\b(' + pat + r')\b', title.lower()):
            tags.append(c)
    if 'north alabama' in title.lower() and 'BHM' in tags and 'HSV' not in tags: tags.append('HSV')
    return tags or ['STW']

# (pattern on "company | title", specialty, area)
MAP = [
 (r'Quipt|VieMed|Blackstone', 'Medical device', 'Respiratory / sleep'),
 (r'Infusion|Soleo|Vital Care', 'Other specialty', 'Infusion services'),
 (r'Abbott \| Abbott Nutrition', 'Other specialty', 'Nutrition'), (r'Abbott \| Diabetes|Tandem', 'Medical device', 'Device – diabetes'),
 (r'Abbott \| .*(TAVI|Structural)', 'Medical device', 'Device – structural heart'), (r'Abbott \| .*(CRM|Cardiac Rhythm)', 'Medical device', 'Device – cardiac rhythm'),
 (r'Corcept', 'Other specialty', 'Endocrinology'), (r'Aquestive', 'Other specialty', ''), (r'SUN PHARMA \| Health Systems', 'Other specialty', ''), (r'^SPR ', 'Medical device', 'Device – neuromodulation'), (r'Karius|Tempus|Spear Bio|Madison Core|Thermo Fisher|Cardinal Health \| .*Laboratory|BD \| Technical|Leica|Siemens Healthineers \| Plasma|Roche', 'Diagnostics / Lab', None),
 (r'Cleerly|Heartflow', 'Medical device', 'Device – cardiac imaging'), (r'Canon Medical', 'Medical device', 'Device – ultrasound'),
 (r'QOL Medical', 'Rare disease', 'Rare – GI'), (r'CSL \| .*HAE', 'Rare disease', 'Rare – hereditary angioedema'), (r'Alnylam|Sobi|Ionis', 'Rare disease', 'Rare disease'),
 (r'Takeda \| Rare', 'Rare disease', 'Rare – alpha-1'), (r'Otsuka .*Rare', 'Rare disease', 'Rare disease'),
 (r'argenx \| Neurology', 'Neuroscience / Psychiatry', 'Neurology'), (r'argenx \| Rheumatology', 'Immunology / Dermatology', 'Rheumatology'),
 (r'Regeneron \| .*Ophthalmology', 'Eye care', 'Eye care – retina'), (r'Allergy-ENT', 'Immunology / Dermatology', 'Allergy / ENT'),
 (r'Hologic \| Oncology', 'Oncology / Hematology', 'Oncology – women’s cancers'), (r'Immunome|Eisai|AbbVie \| .*Oncology', 'Oncology / Hematology', 'Oncology'), (r'GSK \| .*Hematology', 'Oncology / Hematology', 'Oncology – hematology'),
 (r'Supernus', 'Neuroscience / Psychiatry', 'Psychiatry – postpartum depression'), (r'Collegium|Tris Pharma', 'Neuroscience / Psychiatry', 'Psychiatry – ADHD'),
 (r'Teva \| NeuroCare', 'Neuroscience / Psychiatry', 'Neurology'), (r'Teva \| Long Term Care|Axsome', 'Neuroscience / Psychiatry', 'Neuroscience – long-term care'),
 (r'Alkermes|Vanda|AbbVie \| .*Psychiatry|Otsuka .*Neuroscience', 'Neuroscience / Psychiatry', 'Psychiatry'), (r'Praxis', 'Neuroscience / Psychiatry', 'Neurology – epilepsy'),
 (r'AbbVie \| .*Migraine', 'Neuroscience / Psychiatry', 'Neurology – migraine'), (r'RxSalesPros', 'Neuroscience / Psychiatry', 'Psychiatry'),
 (r'Boehringer|Amgen \| Cardiovascular|Syneos Health Commercial Solutions \| Cardiovascular', 'Cardiovascular / Metabolic', 'Cardiovascular'),
 (r'Amgen \| .*Bone Health', "Women's health", 'Bone health'), (r'Amgen \| .*Rheumatology', 'Immunology / Dermatology', 'Rheumatology'),
 (r'SUN PHARMA \| Territory', 'Immunology / Dermatology', 'Dermatology'), (r'Astellas \| Ophthalmic', 'Eye care', 'Eye care – retina'),
 (r'Bayer \| Primary', 'Primary care', 'Primary care'), (r'Syneos Health Commercial Solutions \| Sales Representative \(Primary', 'Primary care', 'Primary care'),
 (r'Pfizer \| Gastro|Lilly .*GI', 'Immunology / Dermatology', 'Gastroenterology'), (r'Takeda \| .*Derm|Incyte \| .*Derm|Vanigent|UCB|Top Candidate', 'Immunology / Dermatology', 'Dermatology'),
 (r'Johnson & Johnson Innovative Medicine', 'Immunology / Dermatology', 'Immunology'), (r'Urology', 'Other specialty', 'Urology'),
 (r'GSK \| .*Vaccines', 'Vaccines / Infectious disease', 'Vaccines'), (r'GSK \| .*Anti-Infectives', 'Vaccines / Infectious disease', 'Hospital anti-infectives'), (r'ViiV', 'Vaccines / Infectious disease', 'HIV'),
 (r'Johnson & Johnson MedTech \| .*Surgery', 'Medical device', 'Device – surgical'), (r'Ortho', 'Medical device', 'Device – orthopedics'),
 (r'Arthrex|Prime Surgical|Fallstaff', 'Medical device', 'Device – orthopedics / surgical'), (r'Stryker \| .*Breast', 'Medical device', 'Device – breast care'),
 (r'Stryker \| .*Smart Care|Stryker \| .*Injury', 'Medical device', 'Device – infection prevention'), (r'Stryker \| .*(Vascular|Arterial)|Cook Medical|Rhevera', 'Medical device', 'Device – vascular'),
 (r'Inspire', 'Medical device', 'Device – sleep apnea'), (r'Medtronic \| .*Nervous', 'Medical device', 'Device – neuromodulation'), (r'Medtronic \| Coronary|Philips', 'Medical device', 'Device – cardiac'),
 (r'Coloplast|Convatec', 'Medical device', 'Device – ostomy / wound'), (r'Skilled Wound|BioTissue|Smith\+Nephew', 'Medical device', 'Device – wound care'),
 (r'Agiliti|Medline|Crown Medical|FloodGate|Providence Medical|Nabi|Ambu|Avanos|e3 Diagnostics|BD \| National|Siemens Healthineers \| Zone|Cynosure|Nobel Biocare',
  'Medical device', None),
 (r'Nobel Biocare', 'Medical device', 'Device – dental implants'), (r'Cynosure', 'Medical device', 'Aesthetics / lasers'), (r'Ambu', 'Medical device', 'Device – anesthesia'),
 (r'Avanos', 'Medical device', 'Device – enteral feeding'), (r'e3 Diagnostics', 'Medical device', 'Device – audiology'),
]
CSO = r'Syneos|TSP, a Syneos|Inizio|Amplity|IQVIA|Vanigent'
RECRUIT = r'RxSalesPros|Top Candidate|Innovativ|Fallstaff'
AWAY = r'\b(TN|MS|FL|GA|AR|KY|LA)\b|Knoxville|Hattiesburg|Panhandle|Atlanta|Mississippi Valley|Nashville|Tupelo|Pensacola|Panama City|Jackson|Chattanooga|Louisiana|Tennessee|Georgia|Southeast|Gulf Coast|South\b|East Central'

docs = []
for f in sorted(glob.glob(ROWS)):
    for line in open(f):
        line = line.rstrip('\n')
        if not line: continue
        p = line.split('|'); p += [''] * (12 - len(p))
        id_, title, co, locs, listed, mn, mx, car, q, yrs, ote, n = p[:12]
        title = re.sub(r'\s+', ' ', title).replace('​', '').strip()
        bmin = int(mn) if mn else None; bmax = int(mx) if mx else None
        if bmin and bmax and bmin > bmax: bmin, bmax = bmax, bmin
        notes = []; inc = 'Quarterly incentive mentioned' if q else 'Not stated'
        if ote == 'O' and bmin:
            inc = f'Posted ${round(bmin/1000)}K–${round((bmax or bmin)/1000)}K looks like total pay (OTE), not base'; bmin = bmax = None
        tt = re.sub(r'alabama', 'AL', title, flags=re.I); cc = re.sub(r'systems|biosystems', '', co, flags=re.I)
        sp = spec(tt, cc); ar = area(tt, cc, sp); lv = level(tt, '')
        key = co + ' | ' + title
        for pat, s2, a2 in MAP:
            if re.search(pat, key):
                sp = s2; ar = a2 or ''
        t = title.lower()
        if re.search(r'entry level|associate (sales|territory|account)|assoc sales|sales associate|break into', t): lv = 'Entry / Associate'
        elif re.search(r'director|district (sales )?manager|regional (sales )?manager|area sales manager|regional business|mgr regional|first line leader|general manager|senior sales leader|clinical sales manager', t): lv = 'Manager / Director'
        elif re.search(r'territory (sales )?manager|business manager|account manager|account executive|key account', t): lv = 'Account Manager / KAM'
        elif lv == 'Manager / Director' and not re.search(r'director|manager|leader', t): lv = 'Sales Representative'
        if lv == 'Manager / Director' and not re.search(r'account manager|territory (sales )?manager|key account|business manager|clinical account manager', t):
            notes.append('Leadership or people-manager role')
        if re.search(r'\bclinical specialist|field clinical|sales support', t): notes.append('Clinical support role that works alongside the sales team')
        if re.search(r'remote|hybrid', t): notes.append('Remote or hybrid role')
        if co == 'BioSpace': notes.append('Reposted by the BioSpace job board. Find the employer’s own posting to apply')
        elif re.search(RECRUIT, co): notes.append('Recruiter listing. The employer may not be named')
        elif re.search(CSO, co): notes.append('Contract sales organization role (you’d represent a partner company’s product)')
        if re.search(AWAY, title): notes.append('Territory may reach outside Alabama. Check the posting')
        if int(n or 1) > 1: notes.append(f'LinkedIn shows {n} listings for this job in Alabama')
        y = int(yrs) if yrs.isdigit() and 1 <= int(yrs) <= 12 else None
        if y: notes.append(f'Asks for {y}+ years of experience')
        if listed and listed < '2026-06-01': notes.append('Posted a long time ago. It may be an evergreen listing')
        carv = {'A': 'Car allowance', 'C': 'Company car'}.get(car, 'Not stated')
        loc = locs if len(locs) < 60 else locs[:57] + '…'
        loc = re.sub(r'^Alabama$', 'Alabama (statewide)', loc)
        pay = 'Pay not posted' if bmin is None else (f'${round(bmin/1000)}K–${round(bmax/1000)}K' if bmax and bmax != bmin else f'${round(bmin/1000)}K')
        summ = f"{co} is hiring {'an' if title[:1].lower() in 'aeiou' else 'a'} {title}" + (f" ({loc})." if loc else '.') + (' Posted base pay: ' + pay + '.' if bmin else " Base pay isn't posted on LinkedIn.")
        slug = re.sub(r'[^a-z0-9]+', '-', (co.split(',')[0].split('(')[0] + ' ' + title)[:48].lower()).strip('-') + '-' + id_[-5:]
        docs.append(dict(id=slug, company=co, role=title, territory=loc, cities=cities_of(locs, title), specialty=sp, area=ar if ar != sp else '', level=lv,
          base_min=bmin, base_max=bmax, incentive=inc, quarterly_stated=bool(q), car=carv,
          car_detail={'Car allowance': 'Posting mentions a car or vehicle allowance.', 'Company car': 'Posting mentions a company car or fleet vehicle.'}.get(carv, 'Posting doesn’t mention a car policy. Ask the recruiter.'),
          note='; '.join(notes), summary=summ, url=f'https://www.linkedin.com/jobs/view/{id_}/', linkedin_id=id_, verified_on=TODAY, found=listed))
ids = Counter(d['id'] for d in docs); assert all(v == 1 for v in ids.values()), [k for k, v in ids.items() if v > 1]
json.dump(docs, open(OUT, 'w'), ensure_ascii=False, indent=0)
print(len(docs), 'jobs')
print(Counter(c for d in docs for c in d['cities']))
print(Counter(d['specialty'] for d in docs))
print(Counter(d['level'] for d in docs))
print('with pay', sum(d['base_min'] is not None for d in docs))
