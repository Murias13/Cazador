import requests,time,os,json
from datetime import datetime

KEEPA_KEY=os.environ.get(“KEEPA_KEY”,””)
TG_BOT=os.environ.get(“TG_BOT”,””)
TG_CHAT=os.environ.get(“TG_CHAT”,””)
vistos=set()

def log(m):
t=datetime.now().strftime(”%H:%M:%S”)
l=”[”+t+”] “+m
print(l)
open(”/root/cazador.log”,“a”).write(l+”\n”)

def tg(m):
if not TG_BOT or not TG_CHAT:return
try:requests.post(“https://api.telegram.org/bot”+TG_BOT+”/sendMessage”,json={“chat_id”:TG_CHAT,“text”:m},timeout=10)
except:pass

def v(x):
if isinstance(x,list):return x[0] if x else 0
return x if x else 0

def buscar():
sel={“page”:0,“domainId”:“9”,“priceTypes”:[0],“deltaPercentRange”:[70,2147483647],“hasAmazonOffer”:True,“isOutOfStock”:False,“sortType”:4,“filterErotic”:True,“singleVariation”:True}
try:
r=requests.get(“https://api.keepa.com/deal”,params={“key”:KEEPA_KEY,“selection”:json.dumps(sel)},timeout=30)
if r.status_code==200:
return r.json().get(“deals”,{}).get(“dr”,[])
except:pass
return []

log(“CAZADOR INICIADO”)
tg(“Cazador iniciado - Monitorizando Keepa 70%+”)

while True:
try:
deals=buscar()
for deal in deals:
asin=deal.get(“asin”,””)
if not asin or asin in vistos:continue
vistos.add(asin)
titulo=str(deal.get(“title”,”?”))[:60]
pa=v(deal.get(“current”,0))
avg=v(deal.get(“avg”,0))
bajada=v(deal.get(“deltaPercent”,0))
if not pa:continue
precio_ahora=pa/100
precio_antes=avg/100 if avg else 0
url=“https://www.amazon.es/dp/”+asin
m=(“NUEVO -”+str(round(bajada))+”%\n”
+titulo+”\n”
+“Ahora: “+str(round(precio_ahora,2))+“e\n”
+“Antes: “+str(round(precio_antes,2))+“e\n”
+url)
log(m)
tg(m)
time.sleep(2)
except KeyboardInterrupt:
log(“Detenido”)
break
except Exception as e:
log(“ERROR:”+str(e))
time.sleep(5)
