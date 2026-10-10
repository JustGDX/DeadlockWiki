import subprocess, concurrent.futures as cf
slugs = "abrams apollo baba bebop billy calico celeste drifter dynamo graves grey-talon haze holliday infernus ivy kelvin lady-geist lash mcginnis mina mirage mo-and-krill paige paradox pocket rat-king rem seven shiv silver sinclair solomon the-doorman venator victor vindicta viscous vyper warden wraith yamato".split()
def get(s):
    r = subprocess.run(["curl","-s","-m","60","-A","Mozilla/5.0","-o",f"/tmp/dl/{s}.html","-w","%{http_code}",f"https://deadlocklabs.gg/heroes/{s}/"],capture_output=True,text=True)
    return s, r.stdout
with cf.ThreadPoolExecutor(8) as ex:
    for s, code in ex.map(get, slugs):
        print(s, code)
