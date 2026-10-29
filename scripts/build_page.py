"""usage: python3 scripts/build_page.py data/jobs.json "Oct 28" index.html"""
import json,re,sys
jobs=json.load(open(sys.argv[1])); updated=sys.argv[2]; out=sys.argv[3]
css=open('scripts/base.css').read()
t=open('scripts/template.html').read()
t=t.replace('/*CSS*/',css).replace('/*UPDATED*/',updated).replace('/*JOBS*/[]',json.dumps(jobs,ensure_ascii=False).replace('</','<\\/'))
t='<!doctype html>\n<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"></head><body>\n'+t+'\n</body></html>\n'
open(out,'w').write(t); print(len(t)//1024,'KB')
