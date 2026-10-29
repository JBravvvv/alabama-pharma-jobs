// Daily Alabama refresh, run inside a signed-in LinkedIn tab (https://www.linkedin.com/jobs/).
// Before running, set (prepare.sh prints both): window.__AL_KNOWN = [ids to recheck]; window.__AL_SEEN = [every id already handled];
// It starts in the background and returns at once. Progress: localStorage '__alx_prog'.
// Results when done: localStorage '__alx_new' (new rows), '__alx_closed' and '__alx_skip' (ids, one per line).
(() => {
  const KNOWN = window.__AL_KNOWN || []; const SEEN = new Set((window.__AL_SEEN || []).map(String));
  ['__alx_prog', '__alx_new', '__alx_closed', '__alx_skip', '__alx_err'].forEach((k) => localStorage.removeItem(k));
  const kws = ['pharmaceutical sales', 'medical device sales', 'medical sales', 'oncology sales', 'specialty sales representative', 'biotech sales', 'territory manager medical', 'surgical sales'];
  const Q = kws.map((kw) => [kw, 'Alabama', 5]);
  ['pharmaceutical sales', 'medical device sales', 'medical sales', 'oncology sales', 'specialty sales representative'].forEach((kw) => Q.push([kw, 'Birmingham, AL', 3]));
  ['Huntsville, AL', 'Montgomery, AL', 'Mobile, AL'].forEach((pl) => ['pharmaceutical sales', 'medical device sales', 'medical sales'].forEach((kw) => Q.push([kw, pl, 2])));
  ['Tuscaloosa, AL', 'Dothan, AL', 'Auburn, AL'].forEach((pl) => Q.push(['pharmaceutical sales', pl, 1]));
  const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
  const CARDS = {}; let done = 0; const TOTAL = Q.length;
  const prog = (extra) => localStorage.setItem('__alx_prog', JSON.stringify({ searches: done + '/' + TOTAL, found: Object.keys(CARDS).length, ...(extra || {}) }));
  async function worker(n) {
    const f = document.createElement('iframe');
    f.style.cssText = 'position:fixed;left:' + (n * 300) + 'px;top:' + (n * 120) + 'px;width:1100px;height:800px;z-index:9999' + n + ';background:#fff';
    document.body.appendChild(f);
    while (Q.length) {
      const [kw, pl, P] = Q.shift();
      try {
        await new Promise((res) => { f.onload = res; f.src = '/jobs/search-results/?keywords=' + encodeURIComponent(kw + ' jobs in ' + pl); setTimeout(res, 15000); });
        await sleep(4500);
        const d = f.contentDocument;
        for (let p = 0; p < P; p++) {
          if (p > 0) { const nx = [...d.querySelectorAll('button')].find((b) => b.innerText.trim() === 'Next'); if (!nx || nx.disabled) break; nx.click(); await sleep(3500); }
          const cs = [...d.querySelectorAll('div[componentkey^="job-card-component-ref-"]')];
          for (let k = 0; k < cs.length; k += 4) { cs[k].scrollIntoView({ block: 'center' }); await sleep(30); }
          for (const c of d.querySelectorAll('div[componentkey^="job-card-component-ref-"]')) {
            const id = (c.getAttribute('componentkey').match(/(\d{6,})/) || [])[1];
            if (id && !CARDS[id]) CARDS[id] = 1;
          }
        }
      } catch (e) { localStorage.setItem('__alx_err', String(e)); }
      done++; prog();
    }
    f.remove();
  }
  const tok = (document.cookie.match(/JSESSIONID="?([^";]+)/) || [])[1];
  const n = (s) => { if (!s) return ''; s = s.replace(/[,\s]/g, ''); return /k$/i.test(s) ? Math.round(parseFloat(s) * 1000) : parseInt(s); };
  async function detail(id) {
    const r = await fetch('/voyager/api/jobs/jobPostings/' + id + '?decorationId=com.linkedin.voyager.deco.jobs.web.shared.WebFullJobPosting-65', { headers: { 'csrf-token': tok, accept: 'application/vnd.linkedin.normalized+json+2.1' } });
    if (r.status === 404 || r.status === 410) return { gone: true };
    if (!r.ok) throw new Error('HTTP ' + r.status);
    const j = await r.json(); const d = j.data || {};
    const tx = ((d.description && d.description.text) || '').replace(/\s+/g, ' ');
    const co = ((j.included || []).find((x) => x.name && /Company/.test(x.$type || '')) || {}).name || '';
    const m = tx.match(/\$\s?(\d{2,3}(?:,\d{3})+|\d{2,3}(?:\.\d+)?\s?[kK])(?:\.\d{2})?\s*(?:-|–|—|to)\s*\$?\s?(\d{2,3}(?:,\d{3})+|\d{2,3}(?:\.\d+)?\s?[kK])/);
    return {
      gone: (d.jobState && d.jobState !== 'LISTED') || !!d.closedAt,
      title: (d.title || '').replace(/[|\n]/g, '/'), co: co.replace(/[|\n]/g, '/'), loc: (d.formattedLocation || '').replace(/, United States$/, '').replace(/ Metropolitan Area| Area$/, ''),
      listed: d.listedAt ? new Date(d.listedAt).toISOString().slice(0, 10) : '', min: m ? n(m[1]) : '', max: m ? n(m[2]) : '',
      car: /car allowance|vehicle allowance|auto allowance/i.test(tx) ? 'A' : /company car|fleet|company vehicle|company-provided vehicle/i.test(tx) ? 'C' : '',
      q: /quarterl/i.test(tx) ? 'Q' : '', yrs: (tx.match(/(\d{1,2})\+?\s*(?:or more\s*)?years?/i) || [])[1] || '', ote: /\bOTE\b|on-target earnings|on target earnings/i.test(tx) ? 'O' : '',
    };
  }
  const DROP = /\bmsl\b|medical science liaison|inside sales|virtual|reimbursement|marketing|insurance|nurse|\brn\b|technician|pharmacist|driver|warehouse|customer service|call center|recruiter|engineer|software|saas|real estate|mortgage|solar|roofing|automotive|car sales|retail|store|cashier|merchandis|financial|telecom|security|hvac|pest|propane|furniture|apparel|beverage|food|billing|coder|coding|scheduler|receptionist|medical assistant|patient access|patient care|caregiver|home care|hospice|home health|therapist|scientist|research|analyst|intern\b|internship|veterinar|animal|hygienist|optician|educator|field service|service engineer|data|coordinator|pharmacy|physician assistant|surgical tech|sterile|liaison|inside account|client engagement/i;
  (async () => {
    try {
      prog({ step: 'searching' });
      await Promise.all([worker(0), worker(1), worker(2)]);
      const known = new Set(KNOWN.map(String));
      const closed = []; let checked = 0, errs = 0;
      for (const id of known) {                       // recheck everything already listed
        try { const d = await detail(id); if (d.gone) closed.push(id); } catch (e) { errs++; }
        checked++; if (checked % 20 === 0) prog({ step: 'rechecking', checked, of: known.size });
        await sleep(300);
      }
      const rows = [], skip = []; let fresh = 0;
      for (const id of Object.keys(CARDS).filter((x) => !known.has(x) && !SEEN.has(x))) {   // details for new ids only
        try {
          const d = await detail(id); fresh++;
          if (fresh % 20 === 0) prog({ step: 'new details', fresh });
          if (d.gone || (!/,\s*AL\b|Alabama/i.test(d.loc) && !/Alabama|\bAL\b/.test(d.title)) || DROP.test(d.title)) { skip.push(id); continue; }
          rows.push([id, d.title, d.co, d.loc, d.listed, d.min, d.max, d.car, d.q, d.yrs, d.ote].join('|'));
        } catch (e) { errs++; }
        await sleep(300);
      }
      localStorage.setItem('__alx_new', rows.join('\n').replace(/https?:\/\/\S+/g, ''));
      localStorage.setItem('__alx_closed', closed.join('\n'));
      localStorage.setItem('__alx_skip', skip.join('\n'));
      prog({ step: 'done', done: true, newRows: rows.length, closed: closed.length, skipped: skip.length, skipLen: skip.join('\n').length, errors: errs, rechecked: checked, newLen: rows.join('\n').length });
    } catch (e) { localStorage.setItem('__alx_err', String(e)); prog({ step: 'failed', done: true, error: String(e) }); }
  })();
  return 'started ' + Q.length + ' searches';
})()
