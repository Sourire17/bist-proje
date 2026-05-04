import streamlit as st
import yfinance as yf
import pandas as pd
from kriterler import tum_kriterler
from back_test import backtest, guven_skoru
from config import BIST30, PERIYOTLAR

st.set_page_config(page_title="BIST Sinyal Paneli", layout="wide", page_icon="chart_with_upwards_trend")

st.markdown("""
<style>
[data-testid="stAppViewContainer"] { background: #0f1117; }
.banner {
    padding: 28px 32px;
    border-radius: 12px;
    border: 0.5px solid #1D9E75;
    margin-bottom: 24px;
    display: flex;
    align-items: center;
    justify-content: space-between;
}
.banner-left h1 { font-size: 26px; font-weight: 500; color: #fff; margin: 0 0 6px 0; }
.banner-left p { font-size: 13px; color: #666; margin: 0; }
.banner-right { text-align: right; }
.banner-tag { font-size: 11px; color: #1D9E75; border: 0.5px solid #1D9E75; padding: 3px 10px; border-radius: 20px; }
</style>
""", unsafe_allow_html=True)

st.markdown("""
<div class="banner">
    <div class="banner-left">
        <h1>BIST Sinyal Paneli</h1>
        <p>RSI &nbsp;·&nbsp; MACD &nbsp;·&nbsp; Bollinger &nbsp;·&nbsp; Destek/Direnc &nbsp;·&nbsp; Hacim</p>
    </div>
    <div class="banner-right">
        <span class="banner-tag">Canli Veri</span>
    </div>
</div>
""", unsafe_allow_html=True)

def sinyal_karar(puan):
    if puan >= 4: return "GUCLU AL"
    elif puan >= 2: return "AL"
    elif puan <= -4: return "GUCLU SAT"
    elif puan <= -2: return "SAT"
    return "BEKLE"

sekme1, sekme2, sekme3 = st.tabs(["Sinyal Paneli", "Hisse Detay", "Nasil Calisir"])

with sekme3:
    st.header("Sistem nasil calisir")
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("5 Kriter")
        st.markdown("""
**RSI** — Asiri alim/satim tespiti
Hissenin asiri satilmis veya alinmis bolgede olup olmadigini olcer.
35 alti AL (+1), 65 ustu SAT (-1) sinyali uretir.

**MACD** — Momentum ve trend
Kisa/uzun vadeli ortalama farki. Sinyal cizgisi ustunde AL (+1), altinda SAT (-1).

**Bollinger Bantlari** — Volatilite
Fiyatin normal araliginin disina cikmasini olcer.
Alt banda yakin AL (+1), ust banda yakin SAT (-1).

**Destek / Direnc** — Fiyat seviyeleri
Son 20 gunun en yuksek ve dusuk seviyeleri baz alinir.
Destege yakin AL (+1), dirence yakin SAT (-1).

**Hacim Anomalisi** — Islem yogunlugu
Hacim 20 gunluk ortalamanin 1.5 katini asarsa anomali sayilir.
Yukselis + yuksek hacim AL (+1), dusu + yuksek hacim SAT (-1).
""")
    with col2:
        st.subheader("Puanlama")
        st.markdown("""
| Toplam Puan | Sinyal |
|-------------|--------|
| +4 veya +5 | Guclu AL |
| +2 veya +3 | AL |
| -1, 0, +1 | BEKLE |
| -2 veya -3 | SAT |
| -4 veya -5 | Guclu SAT |
""")
        st.subheader("Sinyal Gucu")
        st.markdown("""
Her hisse icin gecmis sinyallerin dogrulugu backtest ile olculur.
Sinyal gucu = Sinyal puani (%40) + Backtest dogrulugu (%60)
""")
        st.warning("Bu panel yatirim tavsiyesi vermez. Teknik analiz gecmis veriye dayanir.")

with sekme1:
    col_a, col_b = st.columns([3, 1])
    with col_a:
        pass
    with col_b:
        secili_periyot = st.selectbox("Zaman dilimi", list(PERIYOTLAR.keys()), index=1)

    veri_periyot = PERIYOTLAR[secili_periyot]

    @st.cache_data(ttl=3600)
    def veri_yukle(periyot):
        sonuclar = []
        for hisse in BIST30:
            try:
                veri = yf.download(hisse, period=periyot, progress=False)
                if veri.empty or len(veri) < 30:
                    continue
                veri.columns = veri.columns.get_level_values(0)
                analiz = tum_kriterler(veri)
                puan = analiz["puan"]
                karar = sinyal_karar(puan)
                if karar == "BEKLE":
                    continue
                bt = backtest(hisse)
                dogruluk = bt["dogruluk"] if bt else 50.0
                gskor = guven_skoru(puan, dogruluk)
                degisim = ((veri['Close'].iloc[-1] - veri['Close'].iloc[-2]) / veri['Close'].iloc[-2]) * 100
                sonuclar.append({
                    "Hisse": hisse.replace(".IS", ""),
                    "Fiyat": round(analiz["fiyat"], 2),
                    "Degisim %": round(degisim, 2),
                    "Puan": puan,
                    "Sinyal": karar,
                    "Sinyal Gucu %": round(gskor, 1),
                    "Backtest %": round(dogruluk, 1),
                    "Destek": round(analiz["destek"], 2),
                    "Direnc": round(analiz["direnc"], 2)
                })
            except:
                continue
        return pd.DataFrame(sonuclar)

    with st.spinner("Sinyaller hesaplaniyor..."):
        df = veri_yukle(veri_periyot)

    if df.empty:
        st.info("Su an icin AL veya SAT sinyali uretilemedi. Piyasa genel olarak notr gorunuyor.")
    else:
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Sinyal Uretilen", len(df))
        col2.metric("AL", len(df[df['Sinyal'].str.contains("AL")]))
        col3.metric("SAT", len(df[df['Sinyal'].str.contains("SAT")]))
        col4.metric("Ort. Sinyal Gucu", f"%{df['Sinyal Gucu %'].mean():.1f}")

        st.divider()

        def renk_sinyal(val):
            if val == "GUCLU AL": return "background-color:#0a2e1a; color:#1D9E75; font-weight:bold"
            elif val == "AL": return "background-color:#0a2e1a; color:#5DCAA5"
            elif val == "GUCLU SAT": return "background-color:#2e0a0a; color:#e24b4a; font-weight:bold"
            elif val == "SAT": return "background-color:#2e0a0a; color:#ffa8b8"
            return "color:#888"

        def renk_degisim(val):
            if val > 0: return "color:#1D9E75"
            elif val < 0: return "color:#e24b4a"
            return ""

        def renk_gucu(val):
            if val >= 70: return "color:#1D9E75; font-weight:bold"
            elif val >= 50: return "color:#EF9F27"
            return "color:#e24b4a"

        styled = df.style\
            .map(renk_sinyal, subset=["Sinyal"])\
            .map(renk_degisim, subset=["Degisim %"])\
            .map(renk_gucu, subset=["Sinyal Gucu %", "Backtest %"])

        st.dataframe(styled, use_container_width=True, height=500)

with sekme2:
    st.header("Hisse Detay")
    col_x, col_y = st.columns([2, 1])
    with col_x:
        secili = st.selectbox("Hisse sec", [h.replace(".IS", "") for h in BIST30])
    with col_y:
        det_periyot = st.selectbox("Periyot", ["1mo", "3mo", "6mo", "1y"], index=1, key="det")

    secili_is = secili + ".IS"

    @st.cache_data(ttl=3600)
    def detay_yukle(hisse, periyot):
        veri = yf.download(hisse, period=periyot, progress=False)
        if veri.empty:
            return None, None, None
        veri.columns = veri.columns.get_level_values(0)
        analiz = tum_kriterler(veri)
        bt = backtest(hisse)
        return veri, analiz, bt

    veri, analiz, bt = detay_yukle(secili_is, det_periyot)

    if veri is not None:
        col_left, col_right = st.columns([2, 1])

        with col_left:
            bb_ort = veri['Close'].rolling(20).mean()
            bb_std = veri['Close'].rolling(20).std()
            veri['BB_UST'] = bb_ort + 2 * bb_std
            veri['BB_ALT'] = bb_ort - 2 * bb_std
            veri['Destek'] = analiz["destek"]
            veri['Direnc'] = analiz["direnc"]

            st.subheader(f"{secili} — Fiyat")
            st.line_chart(veri[['Close', 'BB_UST', 'BB_ALT', 'Destek', 'Direnc']])

            fark = veri['Close'].diff()
            kazan = fark.where(fark > 0, 0)
            kayip = -fark.where(fark < 0, 0)
            rs = kazan.rolling(14).mean() / kayip.rolling(14).mean()
            veri['RSI'] = 100 - (100 / (1 + rs))
            st.subheader("RSI")
            st.line_chart(veri['RSI'])

            ema12 = veri['Close'].ewm(span=12).mean()
            ema26 = veri['Close'].ewm(span=26).mean()
            veri['MACD'] = ema12 - ema26
            veri['MACD_S'] = veri['MACD'].ewm(span=9).mean()
            st.subheader("MACD")
            st.line_chart(veri[['MACD', 'MACD_S']])

        with col_right:
            st.subheader("Kriterler")
            for kriter_adi, kriter in analiz["kriterler"].items():
                p = kriter["puan"]
                renk = "#1D9E75" if p > 0 else ("#e24b4a" if p < 0 else "#888")
                isaret = "+" if p > 0 else ("" if p == 0 else "-")
                st.markdown(f"""
<div style='padding:10px;margin-bottom:8px;border-radius:8px;border:0.5px solid #2a2d3a;background:#1a1d27'>
<div style='display:flex;justify-content:space-between'>
<span style='color:#ddd;font-weight:500'>{kriter_adi}</span>
<span style='color:{renk};font-weight:bold'>{isaret}{abs(p)}</span>
</div>
<div style='font-size:12px;color:#666;margin-top:4px'>{kriter["aciklama"]} — {kriter["deger"]}</div>
</div>
""", unsafe_allow_html=True)

            st.divider()
            puan = analiz["puan"]
            karar = sinyal_karar(puan)
            dogruluk = bt["dogruluk"] if bt else 50.0
            gskor = guven_skoru(puan, dogruluk)
            st.metric("Puan", f"{puan} / 5")
            st.metric("Sinyal", karar)
            st.metric("Backtest", f"%{dogruluk}")
            st.metric("Sinyal Gucu", f"%{gskor}")
