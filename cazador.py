import requests,time,os
from datetime import datetime

KEEPA_KEY=os.environ.get("KEEPA_KEY","")
TG_BOT=os.environ.get("TG_BOT","")
TG_CHAT=os.environ.get("TG_CHAT","")
INTERVALO=120
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
    params={
        "key":KEEPA_KEY,
        "domain":9,
        "page":0,
        "dealCondition":0,
        "priceTypes":0,
        "deltaPercentRange":"70,2147483647",
        "hasAmazonOffer":1,
        "isOutOfStock":0,
        "filterErotic":1,
        "singleVariation":1,
        "sortType":0,
        "perPage":150,
        "minRating":10,
    }
    try:
        r=requests.get("https://api.keepa.com/deal",params=params,timeout=30)
        log(f"Deal status: {r.status_code}")
        if r.status_code==200:
            d=r.json()
            dr=d.get("deals",{}).get("dr",[])
            log(f"Deals recibidos: {len(dr)}")
            return dr
    except Exception as e:
        log(f"Error: {e}")
    return []

def precio_inflado(deal):
    # Comprueba si el precio anterior es real
    avg90=deal.get("avg90",0)
    avg180=deal.get("avg180",0)
    current=deal.get("current",0)
    if not avg90 or not avg180 or not current:return True
    # Si la media de 90 y 180 dias es similar el precio es real
    if avg90<=0 or avg180<=0:return True
    # Si la media de 90 dias es muy diferente a la de 180 dias es inflado
    diferencia=abs(avg90-avg180)/avg180*100
    if diferencia>50:return True
    # Si el precio actual es mayor que la media es inflado
    if current>=avg90:return True
    return False

def es_reciente(deal):
    # Solo chollos de las ultimas 24 horas
    delta_time=deal.get("deltaTime",0)
    if not delta_time:return False
    horas=delta_time/3600000
    return horas<=24

def tiene_historial(deal):
    # Minimo 90 dias de historial
    avg90=deal.get("avg90",0)
    return avg90 and avg90>0

def buen_rango_ventas(deal):
    # Que tenga rango de ventas razonable (que se venda)
    rank=deal.get("salesRank",0)
    if not rank or rank<=0:return False
    return rank<=500000

def procesar(deal):
    global alertas
    try:
        asin=deal.get("asin","")
        if not asin or asin in vistos:return
        vistos.add(asin)

        # Filtro anti-inflado
        if precio_inflado(deal):
            log(f"Precio inflado descartado: {asin}")
            return

        # Filtro reciente
        if not es_reciente(deal):
            log(f"No reciente descartado: {asin}")
            return

        # Filtro historial
        if not tiene_historial(deal):
            log(f"Sin historial descartado: {asin}")
            return

        # Filtro rango ventas
        if not buen_rango_ventas(deal):
            log(f"Mal rango ventas descartado: {asin}")
            return

        titulo=str(deal.get("title","?"))[:60]
        pa=deal.get("current",0)
        pb=deal.get("avg90",0)
        if not pa or not pb or pa<=0 or pb<=0:return
        precio_ahora=pa/100
        precio_antes=pb/100
        bajada=round((1-pa/pb)*100)
        if bajada<70:return

        reseñas=deal.get("totalReviews",0)
        if not reseñas or reseñas<10:
            log(f"Pocas reseñas descartado: {asin}")
            return

        rank=deal.get("salesRank",0)
        alertas+=1
        url="https://www.amazon.es/dp/"+asin
        m=(f"🚨 CHOLLO REAL -{bajada}%\n"
           f"📦 {titulo}\n"
           f"💰 Ahora: {round(precio_ahora,2)}€\n"
           f"📊 Antes: {round(precio_antes,2)}€\n"
           f"⭐ Reseñas: {reseñas}\n"
           f"📈 Ranking: {rank}\n"
           f"🔗 {url}")
        log(m)
        tg(m)
    except Exception as e:
        log(f"Error procesando: {e}")

log("CAZADOR V5 INICIADO - MODO ANTI-INFLADO")
tg("🚀 Cazador iniciado - Chollos reales 70%+")

ciclo=0
while True:
    try:
        ciclo+=1
        tk=tokens()
        log(f"=== CICLO {ciclo} | Tokens: {tk} | Alertas: {alertas} ===")
        if tk<10:
            log("Pocos tokens, esperando 3 min...")
            time.sleep(180)
            continue
        deals=buscar_deals()
        nuevos=0
        for deal in deals:
            asin=deal.get("asin","")
            if asin not in vistos:
                nuevos+=1
                procesar(deal)
                time.sleep(0.3)
        log(f"Nuevos esta ronda: {nuevos}")
        log(f"Esperando {INTERVALO}s...")
        time.sleep(INTERVALO)
    except KeyboardInterrupt:
        log("Detenido")
        break
    except Exception as e:
        log(f"ERROR: {e}")
        time.sleep(60)
