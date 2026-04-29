import requests,time,os,json
from datetime import datetime

KEEPA_KEY=os.environ.get(“KEEPA_KEY”,””)
TG_BOT=os.environ.get(“TG_BOT”,””)
TG_CHAT=os.environ.get(“TG_CHAT”,””)
DESCUENTO=10
vistos=set()
alertas=0

def log(m):
t=datetime.now().strftime(”%H:%M:%S”)
l=”[”+t+”] “+m
print(l)
open(”/root/cazador.log”,“a”).write(l+”\n”)

def tg(m):
if not TG_BOT or not TG_CHAT:return
try:requests.post(“https://api.telegram.org/bot”+TG_BOT+”/sendMessage”,json={“chat_id”:TG_CHAT,“text”:m},timeout=10)
except:pass

def buscar_deals(pagina=0):
selection={
“page”:pagina,
“domainId”:“9”,
“excludeCategories”:[818936031,599382031,1661649031,599373031,599364031],
“includeCategories”:[],
“priceTypes”:[0],
“deltaRange”:[0,2147483647],
“deltaPercentRange”:[DESCUENTO,2147483647],
“salesRankRange”:[-1,-1],
“currentRange”:[0,2147483647],
“minRating”:-1,
“isLowest”:False,
“isLowest90”:False,
“isLowestOffer”:False,
“isOutOfStock”:False,
“titleSearch”:””,
“isRangeEnabled”:True,
“isFilterEnabled”:False,
“filterErotic”:True,
“singleVariation”:True,
“hasReviews”:False,
“isPrimeExclusive”:False,
“mustHaveAmazonOffer”:False,
“mustNotHaveAmazonOffer”:False,
“sortType”:4,
“dateRange”:“0”,
“warehouseConditions”:[2,3,4,5],
“hasAmazonOffer”:True
}
try:
r=requests.get(“https://api.keepa.com/deal”,params={“key”:KEEPA_KEY,“selection”:json.dumps(selection)},timeout=30)
if r.status_code==200:
return r.json().get(“deals”,{}).get(“dr”,[])
except Exception as e:
log(“Error: “+str(e))
return []

def precio_inflado(deal):
avg90=deal.get(“avg90”,0)
avg180=deal.get(“avg180”,0)
current=deal.get(“current”,0)
if not avg90 or not avg180 or not current:return True
if avg90<=0 or avg180<=0:return True
if abs(avg90-avg180)/avg180*100>50:return True
if current>=avg90:return True
return False

def procesar(deal):
global alertas
try:
asin=deal.get(“asin”,””)
if not asin or asin in vistos:return False
vistos.add(asin)
if precio_inflado(deal):return False
titulo=str(deal.get(“title”,”?”))[:60]
pa=deal.get(“current”,0)
pb=deal.get(“avg90”,0)
if not pa or not pb or pa<=0 or pb<=0:return False
precio_ahora=pa/100
precio_antes=pb/100
bajada=round((1-pa/pb)*100)
if bajada<DESCUENTO:return False
alertas+=1
url=“https://www.amazon.es/dp/”+asin
m=“CHOLLO -”+str(bajada)+”%\n”+titulo+”\nAhora: “+str(round(precio_ahora,2))+“e\nAntes: “+str(round(precio_antes,2))+“e\n”+url
log(m)
tg(m)
return True
except:
return False

log(“CAZADOR INICIADO - “+str(DESCUENTO)+”%+”)
tg(“Cazador iniciado - “+str(DESCUENTO)+”%+”)

ciclo=0
while True:
try:
ciclo+=1
pagina=0
analizados=0
while True:
deals=buscar_deals(pagina)
if not deals:break
for deal in deals:
if deal.get(“asin”,””) not in vistos:
analizados+=1
procesar(deal)
if len(deals)<150:break
pagina+=1
time.sleep(1)
log(“Ciclo “+str(ciclo)+” | Paginas: “+str(pagina+1)+” | Analizados: “+str(analizados)+” | Alertas: “+str(alertas))
time.sleep(5)
except KeyboardInterrupt:
log(“Detenido”)
break
except Exception as e:
log(“ERROR: “+str(e))
time.sleep(10)
