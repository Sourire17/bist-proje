import yfinance as yf
import pandas as pd
from kriterler import tum_kriterler
from config import BACKTEST_PERIYOT

def backtest(hisse, period=None):
    if period is None:
        period = BACKTEST_PERIYOT

    veri = yf.download(hisse, period=period, progress=False)
    if veri.empty or len(veri) < 60:
        return None
    veri.columns = veri.columns.get_level_values(0)

    dogru = 0
    yanlis = 0

    for i in range(50, len(veri) - 5):
        parca = veri.iloc[:i].copy()
        try:
            sonuc = tum_kriterler(parca)
        except:
            continue

        puan = sonuc["puan"]
        if puan >= 2:
            giris = veri['Close'].iloc[i]
            cikis = veri['Close'].iloc[i + 5]
            if cikis > giris:
                dogru += 1
            else:
                yanlis += 1
        elif puan <= -2:
            giris = veri['Close'].iloc[i]
            cikis = veri['Close'].iloc[i + 5]
            if cikis < giris:
                dogru += 1
            else:
                yanlis += 1

    toplam = dogru + yanlis
    if toplam == 0:
        return None

    dogruluk = round((dogru / toplam) * 100, 1)

    return {
        "hisse": hisse.replace(".IS", ""),
        "toplam": toplam,
        "dogru": dogru,
        "yanlis": yanlis,
        "dogruluk": dogruluk
    }

def guven_skoru(puan, dogruluk):
    normalize = (abs(puan) / 5) * 100
    skor = (normalize * 0.4) + (dogruluk * 0.6)
    return round(skor, 1)
