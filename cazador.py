import requests,time,os
from datetime import datetime

KEEPA_KEY=os.environ.get("KEEPA_KEY","")
TG_BOT=os.environ.get("TG_BOT","")
TG_CHAT=os.environ.get("TG_CHAT","")
DESCUENTO_MIN=30
PRECIO_MIN=15
INTERVALO=300
vistos=set()
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
    try:return requests.get("https://api.keepa.com/token",params={"key":KEEPA_KEY},timeout=10).json().get("tokensLeft",0)
    except:return 0

def buscar_productos():
    params={
        "key":KEEPA_KEY,
        "domain":9,
        "deltaPercent":DESCUENTO_MIN,
        "current_MAX_NEW_PRICE":50000,
        "current_MIN_NEW_PRICE":1500,
        "sort":[["deltaPercent","desc"]],
    }
    try:
        r=requests.post("https://api.keepa.com/query",params={"key":KEEPA_KEY,"domain":9},json=params,timeout=30)
        log(f"ProductFinder status: {r.status_code}")
        if r.status_code==200:
            d=r.json()
            log(f"Respuesta: {str(d)[:300]}")
            return d.get("asinList",[])
    except Exception as e:
        log(f"Error buscar: {e}")
    return []

def consultar_producto(asin):
    try:
        r=requests.get("https://api.keepa.com/product",params={"key":KEEPA_KEY,"domain":9,"asin":asin,"stats":90},timeout=20)
        if r.status_code==200:
            prods=r.json().get("products",[])
            if prods:return prods[0]
    except:pass
    return None

def analizar(asin):
    global alertas
    if asin in vistos:return
    vistos.add(asin)
    prod=consultar_producto(asin)
    if not prod:return
    stats=prod.get("stats",{})
    pa=stats.get("current",[None]*3)
    pb=stats.get("avg",[None]*3)
    if not pa or not pb:return
    pa=pa[0];pb=pb[0]
    if not pa or not pb or pa<=0 or pb<=0:return
    precio_ahora=pa/100
    precio_antes=pb/100
    if precio_ahora<PRECIO_MIN:return
    bajada=(1-pa/pb)*100
    if bajada<DESCUENTO_MIN:return
    alertas+=1
    titulo=str(prod.get("title","?"))[:60]
    url="https://www.amazon.es/dp/"+asin
    m=f"🚨 CHOLLO\n{titulo}\nAhora: {round(precio_ahora,2)}€\nAntes: {round(precio_antes,2)}€\nBajada: -{round(bajada)}%\n{url}"
    log(m)
    tg(m)

log("CAZADOR V5 INICIADO")
tg("🚀 Cazador iniciado")

ciclo=0
while True:
    try:
        ciclo+=1
        tk=tokens()
        log(f"=== CICLO {ciclo} | Tokens: {tk} | Alertas: {alertas} ===")
        if tk<50:
            log("Pocos tokens, esperando 3 minutos...")
            time.sleep(180)
            continue
        asins=buscar_productos()
        log(f"Productos encontrados: {len(asins)}")
        for asin in asins:
            if tokens()<20:
                log("Tokens bajos, parando ciclo")
                break
            analizar(asin)
            time.sleep(1)
        log(f"Ciclo {ciclo} completado. Esperando {INTERVALO}s...")
        time.sleep(INTERVALO)
    except KeyboardInterrupt:
        log("Detenido")
        break
    except Exception as e:
        log(f"ERROR: {e}")
        time.sleep(60)
