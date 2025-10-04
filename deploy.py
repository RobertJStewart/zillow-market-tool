import os,subprocess,requests,sys
GITHUB_USER=os.getenv("GH_USER");REPO_NAME=os.getenv("REPO_NAME","zillow-market-tool");TOKEN=os.getenv("GH_TOKEN")
if not GITHUB_USER or not TOKEN: sys.exit("❌ Please set GH_USER and GH_TOKEN")
headers={"Authorization":f"token {TOKEN}"};repo_url=f"https://api.github.com/repos/{GITHUB_USER}/{REPO_NAME}"
r=requests.get(repo_url,headers=headers)
if r.status_code==404: requests.post("https://api.github.com/user/repos",headers=headers,json={"name":REPO_NAME,"private":False})
subprocess.run(["git","init"]);subprocess.run(["git","branch","-M","main"]);subprocess.run(["git","remote","remove","origin"],check=False)
subprocess.run(["git","remote","add","origin",f"https://{TOKEN}@github.com/{GITHUB_USER}/{REPO_NAME}.git"])
subprocess.run(["git","add","."]);subprocess.run(["git","commit","-m","init"],check=False)
subprocess.run(["git","push","-u","origin","main","--force"])
print("✅ Repo pushed. Enable Pages in settings if not automatic.")
