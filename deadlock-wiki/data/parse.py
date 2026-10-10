import re, json, html, glob, os
def clean(s): return html.unescape(s.replace('\\"','"'))
def names_with_delta(sentence):
    out=[]
    for m in re.finditer(r"([A-Z][A-Za-z'&\-\. ]*?)\s*\(([+\-−]?[\d\.]+)% win rate delta\)", sentence):
        out.append({"name": m.group(1).strip().lstrip('and ').strip(), "delta": float(m.group(2).replace('−','-'))})
    return out
res={}
for f in sorted(glob.glob('/tmp/dl/*.html')):
    slug=os.path.basename(f)[:-5]
    t=clean(open(f,encoding='utf-8',errors='ignore').read())
    d={"slug":slug}
    m=re.search(r'running a ([\d.]+)% win rate and a ([\d.]+)% pick rate across ([\d,]+) tracked',t)
    if m: d.update(wr=float(m.group(1)), pr=float(m.group(2)), matches=m.group(3))
    else:
        m=re.search(r'holding a ([\d.]+)% win rate',t); d['wr']=float(m.group(1)) if m else None
    m=re.search(r'ranks in the ([A-S]\+?) tier',t); d['tier']=m.group(1) if m else None
    m=re.search(r'loses lane weight against (.*?)\.\s',t)
    d['worst_sentence']=m.group(1) if m else None
    d['worst']=names_with_delta(m.group(1)) if m else []
    m=re.search(r'pairs strongest with (.*?)\.\s',t)
    d['syn_sentence']=m.group(1) if m else None
    d['synergy']=names_with_delta(m.group(1)) if m else []
    i=t.find('>Best Matchups<'); j=t.find('</section>',i) if i>=0 else -1
    rows=[]
    if i>=0:
        sec=t[i:j]
        for href,body in re.findall(r'<a [^>]*href="/heroes/([^"/]+)/?"[^>]*>(.*?)</a>',sec, flags=re.S):
            names=re.findall(r'<span class="truncate">([^<]+)</span>',body)
            wr=re.search(r'>([\d.]+)%</span>',body)
            dl=re.search(r'>([+\-−][\d.]+)%</span>',body)
            rows.append({"enemy_slug":href,"enemy":names[-1] if names else href,"hero":names[0] if names else slug,"wr":float(wr.group(1)) if wr else None,"delta":float(dl.group(1).replace('−','-')) if dl else None})
    d['best_matchups']=rows
    res[slug]=d
json.dump(res,open('/tmp/dl/parsed.json','w'),indent=1,ensure_ascii=False)
for k,v in res.items():
    print(k, v.get('wr'), v.get('pr'), v.get('tier'), '| WORST:', [(x['name'],x['delta']) for x in v['worst']], '| SYN:', [(x['name'],x['delta']) for x in v['synergy']], '| BEST:', [(r['enemy'],r['wr']) for r in v['best_matchups']][:4])
