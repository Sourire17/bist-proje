import yfinance as yf
import pandas as pd

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

hisseler = ["THYAO.IS", "GARAN.IS", "ASELS.IS", "SISE.IS", "EREGL.IS"]

print(f"{'Hisse':<12} {'Fiyat':>8} {'RSI':>6} {'MACD':>8} {'Sinyal'}")
print("-" * 50)

for hisse in hisseler:
    veri = yf.download(hisse, period="3mo", progress=False)
    veri.columns = veri.columns.get_level_values(0)
    
    veri['RSI'] = rsi_hesapla(veri)
    veri['MACD'], veri['MACD_S'] = macd_hesapla(veri)
    
    son_rsi = veri['RSI'].iloc[-1]
    son_macd = veri['MACD'].iloc[-1]
    son_macd_s = veri['MACD_S'].iloc[-1]
    son_fiyat = veri['Close'].iloc[-1]
    
    # RSI sinyali
    if son_rsi < 30:
        rsi_sinyal = 1
    elif son_rsi > 70:
        rsi_sinyal = -1
    else:
        rsi_sinyal = 0
    
    # MACD sinyali
    if son_macd > son_macd_s:
        macd_sinyal = 1
    else:
        macd_sinyal = -1
    
    # Birleşik sinyal
    toplam = rsi_sinyal + macd_sinyal
    if toplam >= 2:
        karar = "GÜÇLÜ AL"
    elif toplam == 1:
        karar = "AL"
    elif toplam == -2:
        karar = "GÜÇLÜ SAT"
    elif toplam == -1:
        karar = "SAT"
    else:
        karar = "BEKLE"
    
    print(f"{hisse:<12} {son_fiyat:>8.2f} {son_rsi:>6.1f} {son_macd:>8.2f} {karar}")