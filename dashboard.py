import streamlit as st

# 1. Sayfa ayarlarını yap ve üst boşluğu tamamen sıfırla
st.set_page_config(layout="wide", page_title="BIST Sinyal Paneli", page_icon="📈")

# 2. CSS ile boşlukları sil ve banner'ı güzelleştir
st.markdown("""
    <style>
    /* Streamlit'in kendi boşluklarını (padding) sıfırlama */
    .block-container {
        padding-top: 0rem !important;
        padding-bottom: 0rem !important;
        padding-left: 1rem !important;
        padding-right: 1rem !important;
    }
    
    /* Banner Tasarımı */
    .custom-banner {
        background: linear-gradient(135deg, #FF4B4B 0%, #31112c 100%);
        padding: 30px;
        border-radius: 0px 0px 20px 20px; /* Sadece alt köşeler oval */
        color: white;
        text-align: center;
        margin-left: -1rem; /* Kenar boşluklarını kapatmak için */
        margin-right: -1rem;
        margin-bottom: 30px;
        box-shadow: 0 10px 30px rgba(255, 75, 75, 0.3); /* Kırmızımsı parlama */
        border-bottom: 2px solid rgba(255, 255, 255, 0.1);
    }
    
    .custom-banner h1 {
        font-family: 'Inter', sans-serif;
        font-weight: 800;
        font-size: 3rem !important;
        margin-bottom: 0px;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
    }
    
    .custom-banner p {
        font-style: italic;
        opacity: 0.8;
        font-size: 1.1rem;
    }
    </style>
    
    <div class="custom-banner">
        <h1>🚀 BIST Strateji ve Sinyal Paneli</h1>
        <p>Veriye Dayalı Anlık Teknik Analiz</p>
    </div>
""", unsafe_allow_html=True)


import streamlit as st
import yfinance as yf
import pandas as pd
from kriterler import tum_kriterler
from back_test import backtest, guven_skoru
from config import BIST30, PERIYOTLAR

st.set_page_config(page_title="BIST Sinyal Paneli", layout="wide")

st.markdown("""
<style>
.sinyal-al { color: #1D9E75; font-weight: 500; }
.sinyal-gal { color: #1D9E75; font-weight: 700; }
.sinyal-sat { color: #e24b4a; font-weight: 500; }
.sinyal-gsat { color: #e24b4a; font-weight: 700; }
.sinyal-bekle { color: #888; }
</style>
""", unsafe_allow_html=True)

def sinyal_karar(puan):
    if puan >= 4: return "GUCLU AL"
    elif puan >= 2: return "AL"
    elif puan <= -4: return "GUCLU SAT"
    elif puan <= -2: return "SAT"
    return "BEKLE"

sekme1, sekme2, sekme3 = st.tabs([
    "Sinyal Paneli",
    "Hisse Detay",
    "Nasil Calisir"
])

with sekme3:
    st.header("Sistem nasil calisir")
    st.markdown("""
Bu panel 5 teknik kriter kullanarak BIST hisseleri icin AL/SAT/BEKLE sinyali uretir.
Her kriter -1, 0 veya +1 puan verir. Toplam puan -5 ile +5 arasindadir.
""")
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("5 Kriter")
        st.markdown("""
**RSI (Relative Strength Index)**
Hissenin asiri alim veya asiri satim bolgelerinde olup olmadigini olcer.
- 35 alti: Asiri satim → AL sinyali (+1)
- 65 ustu: Asiri alim → SAT sinyali (-1)

**MACD**
Kisa ve uzun vadeli hareketli ortalamalar arasindaki farki olcer.
Momentum ve trend donuslerini gosterir.
- MACD sinyal cizgisinin ustundeyse: Yukselis (+1)
- Altindaysa: Dusu (-1)

**Bollinger Bantlari**
Fiyatin normal araliginin disina cikip cikmadini gosterir.
- Alt banda yakinsa: Asiri satilmis (+1)
- Ust banda yakinsa: Asiri alinmis (-1)

**Destek / Direnc**
Son 20 gunun en yuksek ve en dusuk fiyatlari baz alinir.
- Destege yakinsa (+1), dirence yakinsa (-1)

**Hacim Anomalisi**
Islem hacmi 20 gunluk ortalamanin 1.5 katini asiyorsa anomali var demektir.
- Yukselis + yuksek hacim: Guclu al (+1)
- Dusu + yuksek hacim: Guclu sat (-1)
""")
    with col2:
        st.subheader("Puanlama ve Guven Skoru")
        st.markdown("""
**Sinyal Karari**
| Puan | Karar |
|------|-------|
| +4, +5 | Guclu AL |
| +2, +3 | AL |
| -1, 0, +1 | BEKLE |
| -2, -3 | SAT |
| -4, -5 | Guclu SAT |

**Guven Skoru**
Her hisse icin gecmis sinyallerin dogrulugu backtest ile olculur.
Sinyal gucu (%40) + backtest dogrulugu (%60) birlestirilir.
Ornek: Puan 4/5 ve backtest %70 dogru ise guven skoru ~%58 olur.

**Zaman Dilimleri**
- 4 Saatlik: Kisa vadeli giris zamanlama
- Gunluk: Ana sinyal uretim zaman dilimi
- Haftalik: Genel trend yonu
""")
        st.subheader("Onemli Not")
        st.warning("Bu sistem yatirim tavsiyesi vermez. Teknik analiz gecmis veriye dayanir ve gelecegi garanti etmez. Kendi arastirmanizi yapiniz.")

with sekme1:
    col_a, col_b = st.columns([3, 1])
    with col_a:
        st.title("BIST Sinyal Paneli")
    with col_b:
        secili_periyot = st.selectbox("Zaman dilimi", list(PERIYOTLAR.keys()), index=1)

    veri_periyot = PERIYOTLAR[secili_periyot]

    with st.spinner("Veriler yukleniyor..."):
        sonuclar = []
        for hisse in BIST30:
            try:
                veri = yf.download(hisse, period=veri_periyot, progress=False)
                if veri.empty or len(veri) < 30:
                    continue
                veri.columns = veri.columns.get_level_values(0)
                analiz = tum_kriterler(veri)
                puan = analiz["puan"]
                karar = sinyal_karar(puan)
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
                    "Guven %": gskor,
                    "Backtest %": dogruluk,
                    "Destek": analiz["destek"],
                    "Direnc": analiz["direnc"]
                })
            except:
                continue

    df = pd.DataFrame(sonuclar)

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Toplam Hisse", len(df))
    col2.metric("AL Sinyali", len(df[df['Sinyal'].str.contains("AL")]))
    col3.metric("SAT Sinyali", len(df[df['Sinyal'].str.contains("SAT")]))
    col4.metric("Ort. Guven", f"%{df['Guven %'].mean():.1f}" if len(df) > 0 else "-")

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

    def renk_guven(val):
        if val >= 70: return "color:#1D9E75; font-weight:bold"
        elif val >= 50: return "color:#EF9F27"
        return "color:#e24b4a"

    styled = df.style\
        .map(renk_sinyal, subset=["Sinyal"])\
        .map(renk_degisim, subset=["Degisim %"])\
        .map(renk_guven, subset=["Guven %", "Backtest %"])

    st.dataframe(styled, use_container_width=True, height=600)

with sekme2:
    st.header("Hisse Detay")
    secili = st.selectbox("Hisse sec", [h.replace(".IS", "") for h in BIST30])
    secili_is = secili + ".IS"
    det_periyot = st.selectbox("Periyot", ["1mo", "3mo", "6mo", "1y"], index=1, key="det")

    veri = yf.download(secili_is, period=det_periyot, progress=False)
    if not veri.empty:
        veri.columns = veri.columns.get_level_values(0)
        analiz = tum_kriterler(veri)
        bt = backtest(secili_is)

        col_left, col_right = st.columns([2, 1])

        with col_left:
            bb_ort = veri['Close'].rolling(20).mean()
            bb_std = veri['Close'].rolling(20).std()
            veri['BB_UST'] = bb_ort + 2 * bb_std
            veri['BB_ALT'] = bb_ort - 2 * bb_std

            destek = analiz["destek"]
            direnc = analiz["direnc"]
            veri['Destek'] = destek
            veri['Direnc'] = direnc

            st.subheader(f"{secili} — Fiyat Grafigi")
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
            st.subheader("Kriter Analizi")
            for kriter_adi, kriter in analiz["kriterler"].items():
                p = kriter["puan"]
                renk = "#1D9E75" if p > 0 else ("#e24b4a" if p < 0 else "#888")
                isaret = "+" if p > 0 else ("" if p == 0 else "-")
                st.markdown(f"""
<div style='padding:10px;margin-bottom:8px;border-radius:8px;border:0.5px solid #2a2d3a;background:#1a1d27'>
<div style='display:flex;justify-content:space-between;align-items:center'>
<span style='font-weight:500;color:#ddd'>{kriter_adi}</span>
<span style='color:{renk};font-weight:bold'>{isaret}{abs(p)}</span>
</div>
<div style='font-size:12px;color:#888;margin-top:4px'>{kriter["aciklama"]} — {kriter["deger"]}</div>
</div>
""", unsafe_allow_html=True)

            st.divider()
            puan = analiz["puan"]
            karar = sinyal_karar(puan)
            dogruluk = bt["dogruluk"] if bt else 50.0
            gskor = guven_skoru(puan, dogruluk)

            st.metric("Toplam Puan", f"{puan}/5")
            st.metric("Sinyal", karar)
            st.metric("Backtest Dogrulugu", f"%{dogruluk}")
            st.metric("Guven Skoru", f"%{gskor}")
