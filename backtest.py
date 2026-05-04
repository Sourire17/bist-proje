import yfinance as yf
import pandas as pd

BIST30 = [
    "THYAO.IS", "GARAN.IS", "ASELS.IS", "SISE.IS", "EREGL.IS",
    "KCHOL.IS", "TUPRS.IS", "BIMAS.IS", "AKBNK.IS", "SAHOL.IS",
    "PETKM.IS", "TOASO.IS", "FROTO.IS", "TCELL.IS", "YKBNK.IS",
    "EKGYO.IS", "HALKB.IS", "VAKBN.IS", "PGSUS.IS", "TAVHL.IS",
    "ARCLK.IS", "KORDS.IS", "MGROS.IS", "SASA.IS",
    "CCOLA.IS", "DOHOL.IS", "ENKAI.IS", "OTKAR.IS", "SOKM.IS"
]

def rsi_hesapla(veri, periyot=14):
    fark = veri['Close'].diff()
    kazan = fark.where(fark > 0, 0)
    kayip = -fark.where(fark < 0, 0)
    ort_kazan = kazan.rolling(periyot).mean()
    ort_kayip = kayip.rolling(periyot).mean()
    rs = ort_kazan / ort_kayip
    return 100 - (100 / (1 + rs))

def macd_hesapla(veri):
    ema12 = veri['Close'].ewm(span=12).mean()
    ema26 = veri['Close'].ewm(span=26).mean()
    macd = ema12 - ema26
    sinyal = macd.ewm(span=9).mean()
    return macd, sinyal

def bollinger_hesapla(veri, periyot=20):
    ort = veri['Close'].rolling(periyot).mean()
    std = veri['Close'].rolling(periyot).std()
    return ort + 2 * std, ort, ort - 2 * std

def stochastic_hesapla(veri, periyot=14):
    en_yuksek = veri['High'].rolling(periyot).max()
    en_dusuk = veri['Low'].rolling(periyot).min()
    k = 100 * (veri['Close'] - en_dusuk) / (en_yuksek - en_dusuk)
    return k, k.rolling(3).mean()

def sinyal_uret(veri):
    rsi = rsi_hesapla(veri)
    macd, macd_s = macd_hesapla(veri)
    bb_ust, _, bb_alt = bollinger_hesapla(veri)
    stoch_k, _ = stochastic_hesapla(veri)
    sinyaller = []
    for i in range(30, len(veri)):
        puan = 0
        if rsi.iloc[i] < 35: puan += 1
        elif rsi.iloc[i] > 65: puan -= 1
        if macd.iloc[i] > macd_s.iloc[i]: puan += 1
        else: puan -= 1
        if veri['Close'].iloc[i] < bb_alt.iloc[i]: puan += 1
        elif veri['Close'].iloc[i] > bb_ust.iloc[i]: puan -= 1
        if stoch_k.iloc[i] < 25: puan += 1
        elif stoch_k.iloc[i] > 75: puan -= 1
        if puan >= 2: karar = "AL"
        elif puan <= -2: karar = "SAT"
        else: karar = "BEKLE"
        sinyaller.append({"tarih": veri.index[i], "fiyat": veri['Close'].iloc[i], "sinyal": karar})
    return pd.DataFrame(sinyaller)

def backtest_calistir(hisse, period="1y"):
    veri = yf.download(hisse, period=period, progress=False)
    if veri.empty or len(veri) < 60:
        return None
    veri.columns = veri.columns.get_level_values(0)
    sinyaller = sinyal_uret(veri)
    al_sinyalleri = sinyaller[sinyaller['sinyal'] == "AL"].copy()
    dogru = 0
    yanlis = 0
    sonuclar = []
    for _, satir in al_sinyalleri.iterrows():
        idx = veri.index.get_loc(satir['tarih'])
        if idx + 5 >= len(veri):
            continue
        giris = satir['fiyat']
        cikis = veri['Close'].iloc[idx + 5]
        getiri = ((cikis - giris) / giris) * 100
        if getiri > 0: dogru += 1
        else: yanlis += 1
        sonuclar.append({
            "Tarih": satir['tarih'].strftime("%Y-%m-%d"),
            "Giris": round(giris, 2),
            "Cikis 5g": round(cikis, 2),
            "Getiri": round(getiri, 2),
            "Sonuc": "DOGRU" if getiri > 0 else "YANLIS"
        })
    toplam = dogru + yanlis
    dogruluk = (dogru / toplam * 100) if toplam > 0 else 0
    return {
        "hisse": hisse.replace(".IS", ""),
        "toplam_sinyal": toplam,
        "dogru": dogru,
        "yanlis": yanlis,
        "dogruluk": round(dogruluk, 1),
        "detay": pd.DataFrame(sonuclar)
    }

if __name__ == "__main__":
    print(f"{'Hisse':<10} {'Sinyal':>7} {'Dogru':>6} {'Yanlis':>7} {'Dogruluk':>9}")
    print("-" * 45)
    for hisse in BIST30:
        sonuc = backtest_calistir(hisse)
        if sonuc and sonuc['toplam_sinyal'] > 0:
            print(f"{sonuc['hisse']:<10} {sonuc['toplam_sinyal']:>7} {sonuc['dogru']:>6} {sonuc['yanlis']:>7} %{sonuc['dogruluk']:>8}")
