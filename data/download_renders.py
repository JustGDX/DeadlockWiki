import re,glob,os,subprocess,concurrent.futures as cf
OUT='/home/user/deadlock-wiki/assets/heroes'
jobs=[]
for f in sorted(glob.glob('/tmp/dl/*.html')):
    slug=os.path.basename(f)[:-5]
    s=open(f,encoding='utf-8',errors='ignore').read().replace('\\"','"')
    rs=[r.split('/')[-1] for r in re.findall(r'/heroes/renders/[A-Za-z_\-%0-9\.]+\.webp',s)]
    rs=[r for r in rs if r!='Haze.webp'] or ['Haze.webp']
    if slug=='haze': rs=['Haze.webp']
    jobs.append((slug, rs[0]))
# upcoming (not on deadlocklabs pages): try names
for slug,name in [('deadman-danny','Deadman_Danny.webp'),('nurse-harrow','Nurse_Harrow.webp'),('violet','Violet.webp')]:
    jobs.append((slug,name))
def get(job):
    slug,name=job
    dst=f'{OUT}/{slug}.webp'
    r=subprocess.run(['curl','-s','-m','60','-A','Mozilla/5.0','-o',dst,'-w','%{http_code}',f'https://deadlocklabs.gg/heroes/renders/{name}'],capture_output=True,text=True)
    code=r.stdout.strip()
    if code!='200' or os.path.getsize(dst)<2000:
        if os.path.exists(dst): os.remove(dst)
        return slug,name,code,'FAIL'
    return slug,name,code,os.path.getsize(dst)
with cf.ThreadPoolExecutor(8) as ex:
    for row in ex.map(get,jobs): print(row)
