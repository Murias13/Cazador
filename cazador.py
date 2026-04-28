import requests,time,json,os
from datetime import datetime
KEEPA_KEY=os.environ.get("KEEPA_KEY","")
TG_BOT=os.environ.get("TG_BOT","")
TG_CHAT=os.environ.get("TG_CHAT","")
DESCUENTO_MIN=60
PRECIO_MIN=30
INTERVALO=60
vistos=set()
total=0
alertas=0
def log(m):
    t=datetime.now().strftime("%H:%M:%S")
    l="["+t+"] "+m
    print(l)
    open("/root/cazador.log","a").write(l+"\n")
def tg(m):
    if not TG_BOT or not TG_CHAT:return
    try:requests.post("https://api.telegram.org/bot"+TG_BOT+"/sendMessage",json={"chat_id":TG_CHAT,"text":m},timeout=10)
    except:pass
def tokens():
    try:return str(requests.get("https://api.keepa.com/token",params={"key":KEEPA_KEY},timeout=10).json().get("tokensLeft","?"))
    except:return "?"
def deals(p=0):
    s={"page":p,"domainId":3,"priceTypes":[0],"deltaPercent":DESCUENTO_MIN,"deltaPercentInInterval":DESCUENTO_MIN,"interval":720,"isFilterEnabled":True,"isAvailable":1,"isNew":1,"isUsed":0}
    r=requests.get("https://api.keepa.com/deal",params={"key":KEEPA_KEY,"selection":json.dumps(s)},timeout=20)
    if r.status_code==200:
        d=r.json()
        if "deals" in d:return d
    raise Exception("HTTP "+str(r.status_code))
def analizar(item):
    global total,alertas
    asin=item.get("asin")
    if not asin or asin in vistos:return
    cur=item.get("current") or []
    avg=item.get("avg90") or item.get("avg180") or []
    cp=cur[0] if cur else None
    ap=avg[0] if avg else None
    if not cp or not ap or cp<=0 or ap<=0:return
    pa=cp/100
    pb=ap/100
    if pa<PRECIO_MIN:return
    b=(1-cp/ap)*100
    total+=1
    if b<DESCUENTO_MIN:return
    vistos.add(asin)
    alertas+=1
    t=str(item.get("title",asin))[:60]
    u="https://www.amazon.es/dp/"+asin
    m="ALERTA ERROR PRECIO\n"+t+"\nAhora:"+str(round(pa,2))+"e\nAntes:"+str(round(pb,2))+"e\nBajada:-"+str(round(b))+"pct\n"+u
    log(m)
    tg(m)
log("CAZADOR V3 INICIADO")
log("Tokens:"+tokens())
tg("CAZADOR V3 ACTIVO")
c=0
while True:
    c+=1
    log("=== CICLO #"+str(c)+" T:"+tokens()+" Anal:"+str(total)+" Alert:"+str(alertas)+" ===")
    for p in range(10):
        try:
            d=deals(p)
            items=d.get("deals",{}).get("items",[])
            if not items:
                log("Pag "+str(p)+" vacia")
                break
            log("Pag "+str(p)+":"+str(len(items))+" productos")
            for i in items:analizar(i)
            time.sleep(3.2)
        except Exception as e:
            log("Error:"+str(e))
            time.sleep(15)
            break
    log("Esperando "+str(INTERVALO)+"s...")
    time.sleep(INTERVALO)
