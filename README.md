# Alabama Pharma & Med Sales Jobs

Open pharma, biotech, medical device and diagnostics field sales jobs in Alabama, pulled from LinkedIn and refreshed daily.

- `data/rows.txt` – the latest list of open postings
- `scripts/build_jobs.py` – sorts each posting into a city, specialty and level
- `scripts/build_page.py` – builds `index.html`

Rebuild by hand: `python3 scripts/build_jobs.py YYYY-MM-DD data/jobs.json && python3 scripts/build_page.py data/jobs.json "Mon D" index.html`

## Daily refresh
Run by a Claude scheduled task on Josh's Mac: `scripts/prepare.sh` (clone + ids), the browser scraper `scripts/scrape_alabama.js` in a signed-in LinkedIn tab, then `scripts/publish.sh YYYY-MM-DD` (merge, rebuild, push).
