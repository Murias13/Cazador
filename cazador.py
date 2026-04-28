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
CATEGORIAS=[667048031,715370031,3277877031,3277875031,599367031,599379031,599368031,2589407031,3166781]
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
def buscar_categoria(cat_id,pagina=0):
    params={"key":KEEPA_KEY,"domain":9,"category":cat_id,"range":pagina}
    r=requests.get("https://api.keepa.com/bestsellers",params=params,timeout=20)
    if r.status_code==200:
        d=r.json()
        return d.get("asinList",[])
    return []
def consultar_producto(asin):
    params={"key":KEEPA_KEY,"domain":9,"asin":asin,"stats":90,"history":1}
    r=requests.get("https://api.keepa.com/product",params=params,timeout=20)
    if r.status_code==200:
        d=r.json()
        prods=d.get("products",[])
        if prods:return prods[0]
    return None
def analizar_producto(asin):
    global total,alertas
    if asin in vistos:return
    vistos.add(asin)
    prod=consultar_producto(asin)
    if not prod:return
    total+=1
    stats=prod.get("stats",{})
    precio_actual=stats.get("current",[None]*3)
    avg90=stats.get("avg",[None]*3)
    if not precio_actual or not avg90:return
    pa=precio_actual[0] if precio_actual[0] else None
    pb=avg90[0] if avg90[0] else None
    if not pa or not pb or pa<=0 or pb<=0:return
    precio_ahora=pa/100
    precio_antes=pb/100
    if precio_ahora<PRECIO_MIN:return
    bajada=(1-pa/pb)*100
    if bajada<DESCUENTO_MIN:return
    alertas+=1
    titulo=str(prod.get("title","?"))[:60]
    url="https://www.amazon.es/dp/"+asin
    m="ALERTA\n"+titulo+"\nAhora:"+str(round(precio_ahora,2))+"e\nAntes:"+str(round(precio_antes,2))+"e\n-"+str(round(bajada))+"pct\n"+url
    log(m)
    tg(m)
log("CAZADOR V5 INICIADO")
log("Tokens:"+tokens())
tg("CAZADOR V5 ACTIVO")
c=0
while True:
    c+=1
    log("CICLO "+str(c)+" T:"+tokens()+" Anal:"+str(total)+" Alert:"+str(alertas))
    for cat in CATEGORIAS:
        for pag in range(3):
            try:
                asins=buscar_categoria(cat,pag)
                if not asins:
                    log("Cat "+str(cat)+" pag "+str(pag)+" vacia")
                    break
                log("Cat "+str(cat)+" pag "+str(pag)+":"+str(len(asins))+" ASINs")
                for asin in asins:
                    analizar_producto(asin)
                    time.sleep(3.2)
            except Exception as e:
                log("Error:"+str(e))
                time.sleep(15)
                break
    log("Esperando "+str(INTERVALO)+"s...")
    time.sleep(INTERVALO)
