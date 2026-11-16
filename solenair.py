
import hmac, io, os, sqlite3
from datetime import datetime, time

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import plotly.io as pio
import requests
import streamlit as st

DB = os.path.join(os.path.dirname(os.path.abspath(__file__)), "veri.db")
OLLAMA_MODEL = "gemma3:4b" 
PARAMS = ["Sıcaklık (°C)", "Nem (%)", "PM2.5", "PM10", "Basınç Farkı (Pa)", "Toksisite Düzeyi"]
#
LIMITS = {
    "PM2.5": [(15, "İyi"), (25, "Orta"), (37.5, "Hassas"), (75, "Sağlıksız"), (1e9, "Kötü")],
    "PM10": [(45, "İyi"), (75, "Orta"), (100, "Hassas"), (150, "Sağlıksız"), (1e9, "Kötü")],
    "Toksisite Düzeyi": [(150, "İyi"), (200, "Orta"), (300, "Yüksek"), (1e9, "Çok yüksek")],
}
st.set_page_config(page_title="Solenair", page_icon="🌬️", layout="wide")


# ---------- tasarim  ----------
pio.templates["solenair"] = go.layout.Template(layout=go.Layout(
    font=dict(family="Manrope, Inter, sans-serif", color="#16424A", size=13),
    colorway=["#1F9D8B", "#16424A", "#E3A857", "#D9694E", "#7A8F94", "#8FC9B9"],
    paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
    title=dict(font=dict(size=16, family="Fraunces, Georgia, serif", color="#0F2A2E"), x=0.02),
    xaxis=dict(showgrid=False, linecolor="#CBD7D4", ticks="outside", tickcolor="#CBD7D4",
               title=dict(font=dict(size=11, color="#8AA0A5"))),
    yaxis=dict(gridcolor="#E9EFED", zeroline=False, title=dict(font=dict(size=11, color="#8AA0A5"))),
    legend=dict(orientation="h", y=1.14, x=0, title_text=""),
    margin=dict(l=10, r=10, t=60, b=10), hovermode="x unified",
))
pio.templates.default = "plotly_white+solenair"

CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,500;9..144,600&family=Manrope:wght@400;500;600;700&display=swap');
:root{--ink:#0F2A2E;--teal:#1F9D8B;--line:#E1E9E7;--mute:#6B8288}
.stApp,.stApp p,.stApp label,.stApp li,.stApp button,.stApp input,.stApp td,.stApp th,.stApp h1,.stApp h2,.stApp h3{font-family:'Manrope',-apple-system,'Segoe UI',sans-serif}
.stApp{color:var(--ink);background:radial-gradient(1200px 520px at 88% -12%,#D9EEE8 0%,rgba(245,248,247,0) 60%),#F5F8F7}
#MainMenu,footer{visibility:hidden}
header[data-testid="stHeader"]{background:transparent}
.block-container{padding-top:2.2rem;max-width:1200px}
.stApp .hero{background:linear-gradient(135deg,#0B1F24 0%,#12383B 55%,#1B5E58 100%);border-radius:22px;padding:36px 42px;margin-bottom:28px;position:relative;overflow:hidden;box-shadow:0 22px 44px -26px rgba(11,31,36,.6)}
.hero:after{content:"";position:absolute;right:-70px;top:-90px;width:300px;height:300px;border-radius:50%;background:radial-gradient(circle,rgba(47,181,154,.38),rgba(47,181,154,0) 70%)}
.stApp .hero .eyebrow{font-size:.72rem;letter-spacing:.24em;color:#7FD6C4;font-weight:700}
.stApp .hero h1{font-family:'Fraunces',Georgia,serif!important;color:#fff!important;font-weight:600;font-size:2.7rem!important;margin:.4rem 0 .5rem;padding:0;line-height:1.1}
.stApp .hero p{color:#B9CFCB;margin:0;font-size:1rem;max-width:640px;line-height:1.55}
[data-testid="stSidebar"]{background:linear-gradient(180deg,#0B1F24,#0F2D31);border-right:0}
[data-testid="stSidebar"] *{color:#D5E4E1}
.brand{display:flex;align-items:center;gap:12px;padding:6px 4px 22px;margin-bottom:10px;border-bottom:1px solid rgba(255,255,255,.1)}
.brand .logo{width:42px;height:42px;border-radius:12px;background:linear-gradient(135deg,#2FB59A,#157A6E);display:flex;align-items:center;justify-content:center;font-family:'Fraunces',Georgia,serif;font-weight:600;font-size:1.35rem;color:#fff!important;box-shadow:0 10px 20px -10px rgba(47,181,154,.9)}
.brand .name{font-family:'Fraunces',Georgia,serif;font-size:1.3rem;font-weight:600;color:#fff!important;line-height:1.1}
.brand .tag{font-size:.68rem;letter-spacing:.14em;text-transform:uppercase;opacity:.65}
[data-testid="stSidebar"] [role="radiogroup"] label{padding:8px 10px;border-radius:10px;transition:background .2s}
[data-testid="stSidebar"] [role="radiogroup"] label:hover{background:rgba(255,255,255,.07)}
[data-testid="stSidebar"] .stButton>button{background:transparent;border:1px solid rgba(255,255,255,.25);color:#fff}
.stTabs [data-baseweb="tab-list"]{gap:6px;border-bottom:1px solid var(--line)}
.stTabs [data-baseweb="tab"]{height:46px;padding:0 18px;font-weight:600;color:var(--mute)}
.stTabs [aria-selected="true"]{color:var(--teal)}
.stTabs [data-baseweb="tab-highlight"]{background:var(--teal);height:3px;border-radius:3px}
[data-testid="stPlotlyChart"]{background:#fff;border:1px solid var(--line);border-radius:18px;padding:10px 12px;box-shadow:0 14px 28px -22px rgba(15,42,46,.45)}
[data-testid="stVerticalBlockBorderWrapper"]{border-radius:16px}
[data-testid="stMarkdownContainer"] code{background:#E3F3EF;color:#0F6F62;border-radius:999px;padding:.12rem .75rem;font-weight:700;font-size:.78rem}
[data-testid="stWidgetLabel"] p{font-weight:600;font-size:.82rem;color:var(--mute)}
div[data-baseweb="select"]>div,div[data-baseweb="input"]>div{border-radius:12px;border-color:var(--line);background:#fff}
div.stButton>button,div.stDownloadButton>button,[data-testid="stFormSubmitButton"]>button{border-radius:12px;font-weight:600;padding:.55rem 1.4rem;border:1px solid var(--line);background:#fff;transition:all .2s}
div.stButton>button:hover,div.stDownloadButton>button:hover{border-color:var(--teal);color:var(--teal);transform:translateY(-1px)}
button[kind="primary"],button[data-testid="stBaseButton-primary"],[data-testid="stForm"] [data-testid="stFormSubmitButton"]>button{background:linear-gradient(135deg,#1F9D8B,#157A6E)!important;color:#fff!important;border:0!important;box-shadow:0 12px 24px -14px rgba(31,157,139,.9)}
[data-testid="stForm"]{background:#fff;border:1px solid var(--line);border-radius:20px;padding:30px;max-width:460px;box-shadow:0 20px 40px -28px rgba(15,42,46,.5)}
[data-testid="stFileUploaderDropzone"]{border:1.5px dashed #9CC9C1;border-radius:16px;background:#F1F8F6}
[data-testid="stDataFrame"]{border:1px solid var(--line);border-radius:14px;overflow:hidden}
[data-testid="stAlert"]{border-radius:14px;border:1px solid var(--line)}
[data-testid="stCaptionContainer"]{color:var(--mute)}
</style>
"""
st.markdown(CSS, unsafe_allow_html=True)

BRAND = ('<div class="brand"><div class="logo">S</div><div><div class="name">Solenair</div>'
         '<div class="tag">Air Quality Intelligence</div></div></div>')


def hero(eyebrow, title, sub):
    st.markdown(f'<div class="hero"><div class="eyebrow">{eyebrow}</div><h1>{title}</h1><p>{sub}</p></div>',
                unsafe_allow_html=True)


# ---------- veri katmani ----------
def load():
    c = sqlite3.connect(DB)
    try:
        df = pd.read_sql_query("SELECT * FROM olcum", c)
    except Exception:
        return pd.DataFrame(columns=["zaman"] + PARAMS)
    finally:
        c.close()
    df["zaman"] = pd.to_datetime(df["zaman"], errors="coerce")
    return df.dropna(subset=["zaman"]).sort_values("zaman")


def write(df):
    df = df.copy()
    df["zaman"] = pd.to_datetime(df["zaman"]).dt.strftime("%Y-%m-%d %H:%M:%S")
    c = sqlite3.connect(DB)
    df.to_sql("olcum", c, if_exists="replace", index=False)
    c.close()


def add(new):
    old = load()
    df = new if old.empty else pd.concat([old, new])
    write(df.drop_duplicates("zaman", keep="last").sort_values("zaman"))


def gunler_of(df):
    return sorted({t.date() for t in df.zaman})


def day_of(df, gun):
    t0 = pd.Timestamp(gun)
    return df[(df.zaman >= t0) & (df.zaman < t0 + pd.Timedelta(days=1))]


def parse(file, gun, bas, bit):
    df = pd.read_excel(file)
    eksik = [p for p in PARAMS if p not in df.columns]
    if eksik:
        raise ValueError("Eksik sütun(lar): " + ", ".join(eksik))
    df[PARAMS] = df[PARAMS].apply(lambda c: pd.to_numeric(c.astype(str).str.replace(",", "."), errors="coerce"))
    if "Zaman" in df.columns:  # dosyada zaman varsa onu kullan
        df["zaman"] = pd.to_datetime(df["Zaman"], errors="coerce", dayfirst=True)
        if df["zaman"].isna().any():
            raise ValueError("Zaman sütunundaki bazı hücreler tarih/saat olarak okunamadı (örn. 14.11.2026 10:30).")
    else:  # yoksa satirlari secilen saat araligina esit dagit
        df["zaman"] = pd.date_range(datetime.combine(gun, bas), datetime.combine(gun, bit), periods=len(df))
    return df[["zaman"] + PARAMS]


def template():
    buf = io.BytesIO()
    pd.DataFrame([[datetime.now().replace(microsecond=0)] + [0] * len(PARAMS)],
                 columns=["Zaman"] + PARAMS).to_excel(buf, index=False)
    return buf.getvalue()


# ---------- yorum motoru ----------
def level(p, v):
    return next(s for lim, s in LIMITS[p] if v <= lim)


def yorumla(d, taban):
    """Her parametre icin (parametre, seviye, yorum, oneri) listesi."""
    out = []
    for p in PARAMS:
        s = d[p].dropna()
        if s.empty:
            continue
        o, m = s.mean(), s.max()
        if p == "Sıcaklık (°C)":
            sev = "Sıcak" if o > 28 else "Soğuk" if o < 16 else "Konforlu"
            tip = {"Sıcak": "Havalandırmayı artır, üniteyi doğrudan güneşten koru; yüksek sıcaklık sensör ve LiPo ömrünü kısaltır.",
                   "Soğuk": "Düşük sıcaklıkta batarya verimi düşer; pil bölmesini yalıt.",
                   "Konforlu": "Müdahale gerekmiyor."}[sev]
        elif p == "Nem (%)":
            sev = "Yüksek" if o > 70 else "Düşük" if o < 30 else "İdeal"
            tip = {"Yüksek": "Yüksek nem PM sensörlerini şişirip yüksek gösterebilir ve filtreyi nemlendirir; kurutucu/silika jel ekle.",
                   "Düşük": "Kuru hava toz kalkmasını artırır; ortam nemini dengele.",
                   "İdeal": "Müdahale gerekmiyor."}[sev]
        elif p == "Basınç Farkı (Pa)":
            r = o / taban if taban else 1
            sev = "Normal" if r < 1.5 else "Tıkanma başlıyor" if r < 2 else "Filtre tıkalı"
            tip = {"Normal": "Filtre temiz çalışıyor.",
                   "Tıkanma başlıyor": "Filtre değişimini planla; debi düşmeye başlayabilir.",
                   "Filtre tıkalı": "PTFE filtreyi hemen değiştir/temizle, aksi halde arıtma verimi düşer."}[sev]
        else:
            sev = level(p, o)
            tip = ("Müdahale gerekmiyor." if sev == "İyi" else
                   "Kaynağı belirle (ısınma, yanma, solvent) ve ortamı havalandır; filtre ünitesini yüksek hızda çalıştır.")
        out.append((p, sev, f"Ortalama {o:.1f}, en yüksek {m:.1f}.", tip))
    return out


def ai_comment(rows):
    ozet = "\n".join(f"- {p}: {sev}. {y}" for p, sev, y, _ in rows)
    prompt = ("Sen bir hava kalitesi uzmanısın. Aşağıdaki günlük ölçüm özetini Türkçe, parametre parametre, "
              "kısa yorumla ve her biri için tek cümlelik bir çözüm öner:\n" + ozet)
    r = requests.post("http://localhost:11434/api/generate",
                      json={"model": OLLAMA_MODEL, "prompt": prompt, "stream": False}, timeout=300)
    return r.json()["response"]


# ---------- kullanici paneli ----------
def user_panel():
    hero("CANLI İZLEME · HAVA KALİTESİ", "Solenair", "Mikro plastik ve ince partikül ölçümü: günlük ve aylık analiz, parametre bazlı yorum ve çözüm önerileri.")
    df = load()
    if df.empty:
        st.info("Henüz veri yok.")
        return
    g_tab, a_tab, y_tab = st.tabs(["Günlük", "Aylık", "Yorum ve Öneriler"])
    gunler = gunler_of(df)
    st.caption(f"Kayıtlı {len(df)} ölçüm · {df.zaman.min():%d.%m.%Y %H:%M} → {df.zaman.max():%d.%m.%Y %H:%M}")

    with g_tab:
        gun = st.selectbox("Gün", gunler, index=len(gunler) - 1, key="g1")
        aralik = st.slider("Saat aralığı", value=(time(0, 0), time(23, 59)), key="s1")
        t0, t1 = datetime.combine(gun, aralik[0]), datetime.combine(gun, aralik[1])
        d = df[df.zaman.between(t0, t1)]
        cols = st.columns(2)
        for i, p in enumerate(PARAMS):
            cols[i % 2].plotly_chart(px.line(d, x="zaman", y=p, title=p), key=f"gc{i}", theme=None)

    with a_tab:
        aylar = sorted(df.zaman.dt.strftime("%Y-%m").unique())
        ay = st.selectbox("Ay", aylar, index=len(aylar) - 1)
        p = st.selectbox("Parametre", PARAMS)
        d = df[df.zaman.dt.strftime("%Y-%m") == ay]
        g = d.set_index("zaman")[p].resample("D").agg(["min", "mean", "max"]).dropna().reset_index()
        g.columns = ["zaman", "min", "ortalama", "maks"]
        st.plotly_chart(px.line(g, x="zaman", y=["min", "ortalama", "maks"], markers=True,
                                title=f"{p} – {ay} günlük özet"), key="ac", theme=None)

    with y_tab:
        gun = st.selectbox("Yorumlanacak gün", gunler, index=len(gunler) - 1, key="g2")
        taban = day_of(df, gunler[0])["Basınç Farkı (Pa)"].median()
        rows = yorumla(day_of(df, gun), taban)
        for p, sev, y, tip in rows:
            with st.container(border=True):
                st.markdown(f"**{p}** · `{sev}`  \n{y}  \n**Öneri:** {tip}")
        if st.button("Yapay zekâ ile detaylandır"):
            try:
                with st.spinner("Model yorumluyor..."):
                    st.markdown(ai_comment(rows))
            except Exception:
                st.warning("Yerel yapay zekâ modeline ulaşılamadı (Ollama çalışıyor mu?). Kural tabanlı yorumlar yukarıda.")


# ---------- admin paneli ----------
def secret(k, d):
    try:
        return st.secrets[k]
    except Exception:
        return os.environ.get(k, d)


def login():
    hero("YÖNETİM", "Admin Girişi", "Veri yüklemek ve yönetmek için oturum açın.")
    u0, p0 = secret("ADMIN_USER", "admin"), secret("ADMIN_PASS", "degistir")
    if p0 == "degistir":
        st.warning("Varsayılan şifre kullanılıyor. ADMIN_PASS ortam değişkeni ile değiştir.")
    with st.form("login"):
        u = st.text_input("Kullanıcı adı")
        p = st.text_input("Şifre", type="password")
        if st.form_submit_button("Giriş"):
            if hmac.compare_digest(u, str(u0)) and hmac.compare_digest(p, str(p0)):
                st.session_state.admin = True
                st.rerun()
            st.error("Hatalı kullanıcı adı veya şifre.")


def admin_panel():
    hero("YÖNETİM", "Admin Paneli", "Ölçüm dosyalarını yükleyin, günleri görüntüleyin ve saat aralığı bazında düzenleyin.")
    y_tab, g_tab = st.tabs(["Veri Yükle", "Gün Görüntüle / Sil"])

    with y_tab:
        c = st.columns(3)
        gun = c[0].date_input("Gün")
        bas = c[1].time_input("Başlangıç saati", time(0, 0))
        bit = c[2].time_input("Bitiş saati", time(23, 59))
        st.caption("Dosyada **Zaman** sütunu varsa o kullanılır; yoksa satırlar seçtiğin saat aralığına eşit dağıtılır.")
        st.download_button("Örnek .xlsx şablonu indir", template(), "sablon.xlsx")
        f = st.file_uploader("Excel dosyası (.xlsx)", type="xlsx")
        if f:
            try:
                if bit <= bas and "Zaman" not in pd.read_excel(f, nrows=0).columns:
                    raise ValueError("Bitiş saati başlangıçtan sonra olmalı.")
                f.seek(0)
                new = parse(f, gun, bas, bit)
                st.dataframe(new, height=200)
                bos = int(new[PARAMS].isna().sum().sum())
                if bos:
                    st.warning(f"{bos} hücre sayıya çevrilemedi ve boş kaldı. Excel'de değerlerin sayı olduğunu kontrol et.")
                if st.button("Kaydet", type="primary"):
                    add(new)
                    st.success(f"{len(new)} satır kaydedildi. Veritabanında toplam {len(load())} ölçüm var.")
            except Exception as e:
                st.error(f"Dosya okunamadı: {e}")

    with g_tab:
        df = load()
        if df.empty:
            st.info("Kayıtlı veri yok.")
            return
        gun = st.selectbox("Gün", gunler_of(df), key="ag")
        d = day_of(df, gun)
        st.dataframe(d, height=300)
        c = st.columns(2)
        bas = c[0].time_input("Silinecek başlangıç", time(0, 0), key="sb")
        bit = c[1].time_input("Silinecek bitiş", time(23, 59), key="se")
        if st.button("Bu saat aralığını sil"):
            t0, t1 = datetime.combine(gun, bas), datetime.combine(gun, bit)
            write(df[~df.zaman.between(t0, t1)])
            st.rerun()


# ---------- yonlendirme ----------
st.sidebar.markdown(BRAND, unsafe_allow_html=True)
sayfa = st.sidebar.radio("Panel", ["Kullanıcı Paneli", "Admin"])
if sayfa == "Kullanıcı Paneli":
    user_panel()
elif st.session_state.get("admin"):
    if st.sidebar.button("Çıkış yap"):
        st.session_state.admin = False
        st.rerun()
    admin_panel()
else:
    login()