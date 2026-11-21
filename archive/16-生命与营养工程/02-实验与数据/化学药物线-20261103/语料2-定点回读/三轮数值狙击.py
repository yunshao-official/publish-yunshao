#!/usr/bin/env python3
# 第三轮·数值狙击：每题只打印命中目标正则的句子，总量封顶
import json,re,ssl,time,urllib.parse,urllib.request,os,datetime
BASE="https://www.ebi.ac.uk/europepmc/webservices/rest/search"; CTX=ssl.create_default_context()
OUT=os.path.dirname(os.path.abspath(__file__)); RAW=os.path.join(OUT,"三轮原始"); os.makedirs(RAW,exist_ok=True)
LOG=os.path.join(OUT,"三轮日志.tsv"); NUM=os.path.join(OUT,"三轮读数.md")
Q=[
 ("S1","CC-1",r'ABSTRACT:"action spectrum" AND (ABSTRACT:"cytochrome c oxidase" OR ABSTRACT:"cytochrome oxidase")', r'\d{3,4}\s*(nm|nanometer)',6),
 ("S2","CC-1",r'ABSTRACT:"cytochrome c oxidase" AND ABSTRACT:"absorption peak" AND ABSTRACT:nm', r'\d{3,4}\s*(nm|nanometer)',6),
 ("S3","CC-1",r'ABSTRACT:"optical window" AND ABSTRACT:"tissue" AND ABSTRACT:nm', r'(6\d\d|7\d\d|8\d\d|9\d\d|1[0-4]\d\d)\s*[-–]\s*(7\d\d|9\d\d|1[0-4]\d\d)',6),
 ("S4","CC-5",r'ABSTRACT:"myocardial external efficiency"', r'(MEE|efficiency)[^.]{0,90}?\d{1,3}(\.\d+)?\s*%',8),
 ("S5","CC-5",r'ABSTRACT:"cardiac power output" AND ABSTRACT:(W OR watts)', r'(CPO|power output)[^.]{0,80}?\d\.\d{1,2}\s*(W|watts|J/s)',6),
 ("S6","CC-4",r'ABSTRACT:"cardiomyocyte" AND (ABSTRACT:"renewal" OR ABSTRACT:"turnover")', r'\d{1,2}(\.\d+)?\s*%[^.]{0,60}',8),
 ("S7","CC-2",r'ABSTRACT:(PROMISE OR vesnarinone) AND ABSTRACT:milrinone AND ABSTRACT:mortality', r'(\d{1,3}%|mortality|significant)',6),
 ("S8","CC-2",r'ABSTRACT:"MERIT-HF" AND ABSTRACT:"mortality"', r'\d{1,3}\s*%[^.]{0,60}',8),
 ("S9","CC-2",r'ABSTRACT:"CIBIS-II" AND ABSTRACT:"death"', r'\d{1,3}\s*%[^.]{0,60}',8),
 ("S10","CC-3",r'ABSTRACT:"SHIFT" AND ABSTRACT:"ivabradine" AND ABSTRACT:"hospitalization"', r'\d{1,3}\s*%[^.]{0,60}',8),
 ("S11","CC-10",r'ABSTRACT:"Dog Aging Project" AND (ABSTRACT:rapamycin OR ABSTRACT:"clinical trial")', r'(did not|no significant|however|failed|tolerab)[^.]{0,110}',6),
 ("S12","CC-10",r'ABSTRACT:"caloric restriction" AND ABSTRACT:"rhesus" AND ABSTRACT:survival', r'(did not|no (significant|effect)|improve[d]? survival|survival benefit)[^.]{0,110}',6),
 ("S13","CC-8",r'ABSTRACT:"senolytic" AND (ABSTRACT:"clearance" OR ABSTRACT:"dasatinib") AND (ABSTRACT:"old" OR ABSTRACT:"aged") AND ABSTRACT:"healthspan"', r'(extended|improve|increased|reduced)[^.]{0,90}',6),
 ("S14","CC-12",r'ABSTRACT:"nicotinamide riboside" AND ABSTRACT:"randomized"', r'(did not|no significant|no effect|unchanged)[^.]{0,110}',6),
]
TAG=datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
rows=[["编号","判据","检索式","执行UTC","HTTP","hitCount","取回","句数","文件"]]; md=[
 "# 第三轮·数值狙击读数","",
 "性质：判据读数补采（判据未改）。只打印含目标正则的逐字句，每题封顶若干条。执行 UTC %s。"%TAG,""]
def fetch(q,size=25):
    url=BASE+"?"+urllib.parse.urlencode({"query":q,"format":"json","pageSize":size,"resultType":"core"})
    req=urllib.request.Request(url,headers={"User-Agent":"yunshao-lit/1.0"})
    try:
        with urllib.request.urlopen(req,timeout=45,context=CTX) as r: return json.loads(r.read().decode()),200
    except Exception as e: return {"error":str(e)},0
for sid,cc,q,pat,cap in Q:
    d,st=fetch(q); hits=d.get("hitCount",0); res=(d.get("resultList") or {}).get("result") or []
    fn="%s_%s.json"%(sid,cc); json.dump(d,open(os.path.join(RAW,fn),"w",encoding="utf-8"),ensure_ascii=False)
    P=re.compile(pat,re.I); md.append("## %s (%s)"%(sid,cc)); md.append("- 检索式 `%s` hit=%s"%(q,hits))
    n=0
    for r in res:
        txt=re.sub(r"<[^>]+>"," ",r.get("abstractText") or "")
        for s in re.split(r"(?<=[.;])\s+",txt):
            if P.search(s.strip()):
                md.append("  - [%s, %s | DOI=%s] 「%s」"%(r.get("pubYear",""),(r.get("journalTitle") or "")[:26],
                            r.get("doi","NA"),s.strip()[:260])); n+=1
            if n>=cap: break
        if n>=cap: break
    if n==0: md.append("  - **NOT_FOUND**（本批未取到含该正则的逐字句）")
    md.append("")
    rows.append([sid,cc,q,TAG,str(st),str(hits),str(len(res)),str(n),fn])
    print(sid,"hit=",hits,"res=",len(res),"sent=",n); time.sleep(0.5)
open(LOG,"w",encoding="utf-8").write("\n".join("\t".join(x) for x in rows)+"\n")
open(NUM,"w",encoding="utf-8").write("\n".join(md)+"\n"); print("WROTE",NUM)
