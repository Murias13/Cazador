import time,os,requests
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By

TG_BOT=os.environ.get("TG_BOT","")
TG_CHAT=os.environ.get("TG_CHAT","")
INTERVALO=120
vistos=set()
alertas=0

URL="https://keepa.com/#!deals/%7B%22page%22%3A0%2C%22domainId%22%3A%229%22%2C%22excludeCategories%22%3A%5B%5B%5D%2C%5B%5D%2C%5B%5D%2C%5B%5D%2C%5B%5D%2C%5B%5D%2C%5B%5D%2C%5B%5D%2C%5B%5D%2C%5B818936031%2C599382031%2C1661649031%2C599373031%2C599364031%5D%2C%5B%5D%2C%5B%5D%2C%5B%5D%2C%5B%5D%2C%5B%5D%5D%2C%22includeCategories%22%3A%5B%5B%5D%2C%5B%5D%2C%5B%5D%2C%5B%5D%2C%5B%5D%2C%5B%5D%2C%5B%5D%2C%5B%5D%2C%5B%5D%2C%5B%5D%2C%5B%5D%2C%5B%5D%2C%5B%5D%2C%5B%5D%2C%5B%5D%5D%2C%22priceTypes%22%3A%5B0%5D%2C%22deltaPercentRange%22%3A%5B70%2C2147483647%5D%2C%22hasAmazonOffer%22%3Atrue%2C%22isOutOfStock%22%3Afalse%2C%22filterErotic%22%3Atrue%2C%22singleVariation%22%3Atrue%2C%22sortType%22%3A4%2C%22dateRange%22%3A%220%22%2C%22perPage%22%3A150%7D"

def log(m):
    t=datetime.now().strftime("%H:%M:%S")
    l="["+t+"] "+m
    print(l)
    open("/root/cazador.log","a").write(l+"\n")

def tg(m):
    if not TG_BOT or not TG_CHAT:return
    try:requests.post("https://api.telegram.org/bot"+TG_BOT+"/sendMessage",json={"chat_id":TG_CHAT,"text":m},timeout=10)
    except:pass

def crear_driver():
    opts=Options()
    opts.add_argument("--headless")
    opts.add_argument("--no-sandbox")
    opts.add_argument("--disable-dev-shm-usage")
    opts.add_argument("--disable-gpu")
    opts.add_argument("--window-size=1920,1080")
    opts.binary_location="/snap/bin/chromium"
    service=Service("/usr/bin/chromedriver")
    return webdriver.Chrome(service=service,options=opts)

def raspar():
    driver=None
    try:
        driver=crear_driver()
        log("Abriendo Keepa...")
        driver.get(URL)
        log("Esperando que cargue la página...")
        time.sleep(20)
        html=driver.page_source
        log(f"HTML recibido: {len(html)} chars")
        productos=driver.find_elements(By.CSS_SELECTOR,"div.dealItem")
        log(f"Productos encontrados: {len(productos)}")
        resultados=[]
        for p in productos:
            try:
                asin=p.get_attribute("data-asin") or ""
                titulo=p.find_element(By.CSS_SELECTOR,"div.dealTitle").text.strip()[:60]
                descuento=p.find_element(By.CSS_SELECTOR,"div.dealDelta").text.strip()
                precio=p.find_element(By.CSS_SELECTOR,"div.dealCurrent").text.strip()
                if asin:
                    resultados.append({"asin":asin,"titulo":titulo,"descuento":descuento,"precio":precio})
            except:pass
        return resultados
    except Exception as e:
        log(f"Error selenium: {e}")
        return []
    finally:
        if driver:driver.quit()

log("CAZADOR SELENIUM INICIADO")
tg("🚀 Cazador Selenium iniciado")

ciclo=0
while True:
    try:
        ciclo+=1
        log(f"=== CICLO {ciclo} | Alertas: {alertas} ===")
        productos=raspar()
        nuevos=0
        for p in productos:
            asin=p["asin"]
            if asin in vistos:continue
            vistos.add(asin)
            nuevos+=1
            alertas+=1
            url="https://www.amazon.es/dp/"+asin
            m=(f"🚨 CHOLLO {p['descuento']}\n"
               f"📦 {p['titulo']}\n"
               f"💰 {p['precio']}\n"
               f"🔗 {url}")
            log(m)
            tg(m)
        log(f"Nuevos: {nuevos} | Esperando {INTERVALO}s...")
        time.sleep(INTERVALO)
    except KeyboardInterrupt:
        log("Detenido")
        break
    except Exception as e:
        log(f"ERROR: {e}")
        time.sleep(60)

