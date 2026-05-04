import streamlit as st
import yfinance as yf
import pandas as pd
from backtest import backtest_calistir, BIST30

st.set_page_config(page_title="BIST Sinyal Paneli", layout="wide")

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

def hacim_anomali(veri, periyot=20):
    ort_hacim = veri['Volume'].rolling(periyot).mean()
    return veri['Volume'].iloc[-1] > ort_hacim.iloc[-1] * 1.5

st.title("BIST Sinyal Paneli")
st.caption("RSI - MACD - Bollinger - Stochastic - Hacim")

sekme1, sekme2 = st.tabs(["Canli Sinyaller", "Backtest Sonuclari"])

with sekme1:
    with st.spinner("Veriler yukleniyor..."):
        sonuclar = []
        for hisse in BIST30:
            veri = yf.download(hisse, period="3mo", progress=False)
            if veri.empty:
                continue
            veri.columns = veri.columns.get_level_values(0)
            veri['RSI'] = rsi_hesapla(veri)
            veri['MACD'], veri['MACD_S'] = macd_hesapla(veri)
            bb_ust, bb_ort, bb_alt = bollinger_hesapla(veri)
            stoch_k, stoch_d = stochastic_hesapla(veri)
            son = veri.iloc[-1]
            son_rsi = veri['RSI'].iloc[-1]
            son_macd = veri['MACD'].iloc[-1]
            son_macd_s = veri['MACD_S'].iloc[-1]
            son_fiyat = son['Close']
            son_bb_ust = bb_ust.iloc[-1]
            son_bb_alt = bb_alt.iloc[-1]
            son_stoch = stoch_k.iloc[-1]
            anomali = hacim_anomali(veri)
            puan = 0
            if son_rsi < 35: puan += 1
            elif son_rsi > 65: puan -= 1
            if son_macd > son_macd_s: puan += 1
            else: puan -= 1
            if son_fiyat < son_bb_alt: puan += 1
            elif son_fiyat > son_bb_ust: puan -= 1
            if son_stoch < 25: puan += 1
            elif son_stoch > 75: puan -= 1
            if puan >= 3: karar = "GUCLU AL"
            elif puan == 2: karar = "AL"
            elif puan <= -3: karar = "GUCLU SAT"
            elif puan == -2: karar = "SAT"
            else: karar = "BEKLE"
            degisim = ((son_fiyat - veri['Close'].iloc[-2]) / veri['Close'].iloc[-2]) * 100
            sonuclar.append({
                "Hisse": hisse.replace(".IS", ""),
                "Fiyat": round(son_fiyat, 2),
                "Degisim %": round(degisim, 2),
                "RSI": round(son_rsi, 1),
                "Stoch": round(son_stoch, 1),
                "MACD": round(son_macd, 2),
                "BB": "Alt" if son_fiyat < son_bb_alt else ("Ust" if son_fiyat > son_bb_ust else "Orta"),
                "Hacim": "VAR" if anomali else "-",
                "Puan": puan,
                "Sinyal": karar
            })

    df = pd.DataFrame(sonuclar)
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Toplam Hisse", len(df))
    col2.metric("AL Sinyali", len(df[df['Sinyal'].str.contains("AL")]))
    col3.metric("SAT Sinyali", len(df[df['Sinyal'].str.contains("SAT")]))
    col4.metric("Bekle", len(df[df['Sinyal'] == "BEKLE"]))
    st.divider()

    def renk(val):
        if val == "GUCLU AL": return "background-color:#1a472a; color:#69db7c; font-weight:bold"
        elif val == "AL": return "background-color:#2d6a4f; color:#95d5b2"
        elif val == "GUCLU SAT": return "background-color:#4a1010; color:#ff6b6b; font-weight:bold"
        elif val == "SAT": return "background-color:#6b2737; color:#ffa8b8"
        elif val == "VAR": return "color:#ffd43b; font-weight:bold"
        return ""

    def degisim_renk(val):
        if val > 0: return "color:#69db7c"
        elif val < 0: return "color:#ff6b6b"
        return ""

    styled = df.style.map(renk, subset=["Sinyal", "Hacim"]).map(degisim_renk, subset=["Degisim %"])
    st.dataframe(styled, use_container_width=True, height=600)

    st.divider()
    st.subheader("Detayli Grafik")
    col_a, col_b = st.columns([1, 3])
    with col_a:
        secili = st.selectbox("Hisse sec", [h.replace(".IS","") for h in BIST30])
        periyot = st.selectbox("Periyot", ["1mo", "3mo", "6mo", "1y"])
        goster = st.multiselect("Goster", ["Fiyat", "RSI", "MACD"], default=["Fiyat", "RSI"])
    secili_is = secili + ".IS"
    veri = yf.download(secili_is, period=periyot, progress=False)
    veri.columns = veri.columns.get_level_values(0)
    veri['RSI'] = rsi_hesapla(veri)
    veri['MACD'], veri['MACD_S'] = macd_hesapla(veri)
    bb_ust, bb_ort, bb_alt = bollinger_hesapla(veri)
    veri['BB_UST'] = bb_ust
    veri['BB_ALT'] = bb_alt
    with col_b:
        if "Fiyat" in goster:
            st.markdown("**Fiyat ve Bollinger**")
            st.line_chart(veri[['Close', 'BB_UST', 'BB_ALT']])
        if "RSI" in goster:
            st.markdown("**RSI**")
            st.line_chart(veri['RSI'])
        if "MACD" in goster:
            st.markdown("**MACD**")
            st.line_chart(veri[['MACD', 'MACD_S']])

with sekme2:
    st.subheader("Backtest Sonuclari - BIST 30")
    periyot_bt = st.selectbox("Test periyodu", ["1y", "2y"], key="bt_periyot")
    if st.button("Backtesti Calistir"):
        with st.spinner("Hesaplaniyor, bekleyin..."):
            bt_sonuclar = []
            for hisse in BIST30:
                sonuc = backtest_calistir(hisse, period=periyot_bt)
                if sonuc and sonuc['toplam_sinyal'] > 0:
                    bt_sonuclar.append({
                        "Hisse": sonuc['hisse'],
                        "Sinyal Sayisi": sonuc['toplam_sinyal'],
                        "Dogru": sonuc['dogru'],
                        "Yanlis": sonuc['yanlis'],
                        "Dogruluk %": sonuc['dogruluk']
                    })
            bt_df = pd.DataFrame(bt_sonuclar).sort_values("Dogruluk %", ascending=False)

            def bt_renk(val):
                if val >= 70: return "color:#69db7c; font-weight:bold"
                elif val >= 50: return "color:#ffd43b"
                else: return "color:#ff6b6b"

            st.dataframe(
                bt_df.style.map(bt_renk, subset=["Dogruluk %"]),
                use_container_width=True
            )
            ort_dogruluk = bt_df['Dogruluk %'].mean()
            st.metric("Ortalama Dogruluk", f"%{ort_dogruluk:.1f}")
