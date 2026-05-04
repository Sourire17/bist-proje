import pandas as pd
from config import (RSI_ASIRI_SATIM, RSI_ASIRI_ALIM,
                    STOCH_ASIRI_SATIM, STOCH_ASIRI_ALIM,
                    HACIM_CARPAN, DESTEK_DIRENC_PENCERE)

def rsi(veri):
    fark = veri['Close'].diff()
    kazan = fark.where(fark > 0, 0)
    kayip = -fark.where(fark < 0, 0)
    ort_kazan = kazan.rolling(14).mean()
    ort_kayip = kayip.rolling(14).mean()
    rs = ort_kazan / ort_kayip
    deger = 100 - (100 / (1 + rs))
    son = deger.iloc[-1]
    if son < RSI_ASIRI_SATIM:
        return 1, round(son, 1), "Asiri satim"
    elif son > RSI_ASIRI_ALIM:
        return -1, round(son, 1), "Asiri alim"
    return 0, round(son, 1), "Notr"

def macd(veri):
    ema12 = veri['Close'].ewm(span=12).mean()
    ema26 = veri['Close'].ewm(span=26).mean()
    macd_line = ema12 - ema26
    sinyal = macd_line.ewm(span=9).mean()
    son_macd = macd_line.iloc[-1]
    son_sinyal = sinyal.iloc[-1]
    if son_macd > son_sinyal:
        return 1, round(son_macd, 2), "Yukselis"
    return -1, round(son_macd, 2), "Dusu"

def bollinger(veri):
    ort = veri['Close'].rolling(20).mean()
    std = veri['Close'].rolling(20).std()
    ust = ort + 2 * std
    alt = ort - 2 * std
    fiyat = veri['Close'].iloc[-1]
    if fiyat < alt.iloc[-1]:
        return 1, "Alt banda yakin", round(alt.iloc[-1], 2)
    elif fiyat > ust.iloc[-1]:
        return -1, "Ust banda yakin", round(ust.iloc[-1], 2)
    return 0, "Bant icinde", None

def destek_direnc(veri):
    pencere = DESTEK_DIRENC_PENCERE
    son_fiyat = veri['Close'].iloc[-1]
    yuksek = veri['High'].rolling(pencere).max().iloc[-1]
    dusuk = veri['Low'].rolling(pencere).min().iloc[-1]
    aralik = yuksek - dusuk
    if aralik == 0:
        return 0, round(dusuk, 2), round(yuksek, 2)
    direnc_uzaklik = (yuksek - son_fiyat) / aralik
    destek_uzaklik = (son_fiyat - dusuk) / aralik
    if destek_uzaklik < 0.2:
        return 1, round(dusuk, 2), round(yuksek, 2)
    elif direnc_uzaklik < 0.2:
        return -1, round(dusuk, 2), round(yuksek, 2)
    return 0, round(dusuk, 2), round(yuksek, 2)

def hacim(veri):
    ort_hacim = veri['Volume'].rolling(20).mean().iloc[-1]
    son_hacim = veri['Volume'].iloc[-1]
    son_degisim = veri['Close'].iloc[-1] - veri['Close'].iloc[-2]
    carpan = round(son_hacim / ort_hacim, 1) if ort_hacim > 0 else 1
    if son_hacim > ort_hacim * HACIM_CARPAN:
        if son_degisim > 0:
            return 1, carpan, "Yukselis hacmi"
        else:
            return -1, carpan, "Durus hacmi"
    return 0, carpan, "Normal"

def tum_kriterler(veri):
    rsi_p, rsi_v, rsi_a = rsi(veri)
    macd_p, macd_v, macd_a = macd(veri)
    bb_p, bb_a, bb_v = bollinger(veri)
    dd_p, destek, direnc = destek_direnc(veri)
    h_p, h_v, h_a = hacim(veri)

    toplam_puan = rsi_p + macd_p + bb_p + dd_p + h_p

    return {
        "puan": toplam_puan,
        "kriterler": {
            "RSI":            {"puan": rsi_p, "deger": rsi_v, "aciklama": rsi_a},
            "MACD":           {"puan": macd_p, "deger": macd_v, "aciklama": macd_a},
            "Bollinger":      {"puan": bb_p, "deger": bb_v, "aciklama": bb_a},
            "Destek/Direnc":  {"puan": dd_p, "deger": f"{destek} / {direnc}", "aciklama": "Destek" if dd_p==1 else ("Direnc" if dd_p==-1 else "Notr")},
            "Hacim":          {"puan": h_p, "deger": f"{h_v}x", "aciklama": h_a}
        },
        "destek": destek,
        "direnc": direnc,
        "fiyat": round(veri['Close'].iloc[-1], 2)
    }
