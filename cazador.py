import requests,time,os,json
from datetime import datetime

KEEPA_KEY=os.environ.get("KEEPA_KEY","")
TG_BOT=os.environ.get("TG_BOT","")
TG_CHAT=os.environ.get("TG_CHAT","")
INTERVALO=5
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

def buscar_deals():
    selection={
        "page":0,
        "domainId":"9",
        "excludeCategories":[818936031,599382031,1661649031,599373031,599364031],
        "includeCategories":[],
        "priceTypes":[0],
        "deltaRange":[0,2147483647],
        "deltaPercentRange":[10,2147483647],
        "salesRankRange":[-1,-1],
        "currentRange":[0,2147483647],
        "minRating":-1,
        "isLowest":False,
        "isLowest90":False,
        "isLowestOffer":False,
        "isOutOfStock":False,
        "titleSearch":"",
        "isRangeEnabled":True,
        "isFilterEnabled":False,
        "filterErotic":True,
        "singleVariation":True,
        "hasReviews":False,
        "isPrimeExclusive":False,
        "mustHaveAmazonOffer":False,
        "mustNotHaveAmazonOffer":False,
        "sortType":4,
        "dateRange":"0",
        "warehouseConditions":[2,3,4,5],
        "hasAmazonOffer":True
    }
    try:
        params={
            "key":KEEPA_KEY,
            "selection":json.dumps(selection)
        }
        r=requests.get("https://api.keepa.com/deal",params=params,timeout=30)
        if r.status_code==200:
            d=r.json()
            dr=d.get("deals",{}).get("dr",[])
            return dr
        else:
            log(f"Error: {r.status_code}")
    except Exception as e:
        log(f"Error: {e}")
    return []

def precio_inflado(deal):
    avg90=deal.get("avg90",0)
    avg180=deal.get("avg180",0)
    current=deal.get("current",0)
    if not avg90 or not avg180 or not current:return True
    if avg90<=0 or avg180<=0:return True
    diferencia=abs(avg90-avg180)/avg180*100
    if diferencia>50:return True
    if current>=avg90:return True
    return False

def procesar(deal):
    global alertas
    try:
        asin=deal.get("asin","")
        if not asin or asin in vistos:return
        vistos.add(asin)
        if precio_inflado(deal):return
        titulo=str(deal.get("title","?"))[:60]
        pa=deal.get("current",0)
        pb=deal.get("avg90",0)
        if not pa or not pb or pa<=0 or pb<=0:return
        precio_ahora=pa/100
        precio_antes=pb/100
        bajada=round((1-pa/pb)*100)
        if bajada<10:return
        alertas+=1
        url="https://www.amazon.es/dp/"+asin
        m=(f"🚨 CHOLLO -{bajada}%\n"
           f"📦 {titulo}\n"
           f"💰 Ahora: {round(precio_ahora,2)}€\n"
           f"📊 Antes: {round(precio_antes,2)}€\n"
           f"🔗 {url}")
        log(m)
        tg(m)
    except Exception as e:
        log(f"Error: {e}")

log("CAZADOR INICIADO - 5 segundos")
tg("🚀 Cazador iniciado - Modo ultrarapido")

ciclo=0
while True:
    try:
        ciclo+=1
        deals=buscar_deals()
        nuevos=0
        for deal in deals:
            if deal.get("asin","") not in vistos:
                nuevos+=1
                procesar(deal)
        if nuevos>0:
            log(f"Ciclo {ciclo} | Nuevos: {nuevos} | Alertas: {alertas}")
        time.sleep(INTERVALO)
    except KeyboardInterrupt:
        log("Detenido")
        break
    except Exception as e:
        log(f"ERROR: {e}")
        time.sleep(10)

