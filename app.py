from pathlib import Path
import json
import streamlit as st
import pandas as pd
import time

from scripts.scoring_grid import run_profile, load_profiles_json
from scripts.make_map import make_map


BASE_DIR = Path(__file__).resolve().parent
OUT_MAPS = BASE_DIR / "outputs" / "maps"
OUT_MAPS.mkdir(parents=True, exist_ok=True)

st.set_page_config(page_title="Ev Yaşam Öneri Sistemi", layout="wide")
st.title("Ev Yaşam Öneri Sistemi (İstanbul)")
st.caption(
    "İstanbul genelinde çevresel veriler kullanılarak "
    "lokasyon bazlı yaşam uygunluğu skorlaması yapılır."
)


CATEGORIES = [
    "hospital_main",
    "supermarket_main",
    "school_public",
    "school_private",
    "park_main",
    "station_main",
    "mall_main",
    "gym_main",
    "sports_centre_main",
    "parking_main",
    "cafe_main",
    "bar_main",
]

CATEGORY_LABELS = {
    "hospital_main": "Hastane",
    "supermarket_main": "Süpermarket",
    "school_public": "Devlet Okulu",
    "school_private": "Özel Okul",
    "park_main": "Park",
    "station_main": "Ulaşım",
    "mall_main": "AVM",
    "gym_main": "Spor Salonu",
    "sports_centre_main": "Spor Merkezi",
    "parking_main": "Otopark",
    "cafe_main": "Kafe",
    "bar_main": "Bar",
}


PROFILE_LABELS = {
    "student": "Öğrenci",
    "family_with_children": "Çocuklu Aile",
    "elderly_couple": "Yaşlı Çift",
    "sport_focused_single": "Spor Odaklı Bekar",
    "social_life_focused": "Sosyal Hayat Odaklı",
    "quiet_seeker": "Sessizlik Arayan",
    "remote_worker": "Uzaktan Çalışan",
}


def semt_from_coord(lat, lon):
    if 28.98 <= lon <= 29.10 and 40.98 <= lat <= 41.10:
        return "Boğaz Hattı (yakın çevre)"

    if lon < 29.0:
        if lat > 41.05:
            return "Kuzey Avrupa Yakası"
        if lat > 41.0:
            return "Merkez Avrupa Yakası"
        return "Güney Avrupa Yakası"

    if lon < 29.20:
        return "Anadolu Yakası (Merkez)"
    return "Anadolu Yakası (Doğu)"


@st.cache_data(show_spinner=False)
def cached_run_profile(profile_json: str, cell_km: float, top_n: int):
    profile = json.loads(profile_json)
    out_csv, out_geo = run_profile(profile, cell_km=cell_km, top_n=top_n)
    return str(out_csv), str(out_geo)


def build_custom_profile() -> dict:
    st.sidebar.subheader("Kendi Profilini Oluştur")

    radius_m = st.sidebar.slider("Mesafe yarıçapı (m)", 300, 3000, 1000, 100)

    must_have = st.sidebar.multiselect(
        "Olmazsa olmaz",
        CATEGORIES,
        format_func=lambda x: CATEGORY_LABELS.get(x, x)
    )

    avoid = st.sidebar.multiselect(
        "Uzak olsun",
        CATEGORIES,
        format_func=lambda x: CATEGORY_LABELS.get(x, x)
    )

    st.sidebar.caption("Ağırlıklar: -2 (istemem) → +5 (çok isterim)")
    weights = {}
    for cat in CATEGORIES:
        weights[cat] = st.sidebar.slider(
            CATEGORY_LABELS.get(cat, cat),
            -2,
            5,
            0,
            1
        )

    weights = {k: v for k, v in weights.items() if v != 0}

    profile = {
        "profile_id": "custom",
        "profile_name": "Kişisel Profil",
        "description": "Kullanıcı tarafından oluşturuldu.",
        "radius_m": int(radius_m),
        "weights": weights,
    }

    if must_have:
        profile["must_have"] = must_have
    if avoid:
        profile["avoid"] = avoid

    return profile


mode = st.sidebar.radio(
    "Profil Modu",
    ["Preset Profil Seç", "Kendi Profilini Oluştur"],
    index=1
)

if mode == "Preset Profil Seç":
    profiles = load_profiles_json()

    profile_map = {}
    for p in profiles:
        pid = p["profile_id"]
        label = PROFILE_LABELS.get(pid, p["profile_name"])
        profile_map[label] = p

    selected_label = st.sidebar.selectbox(
        "Profil seç",
        list(profile_map.keys())
    )

    profile = profile_map[selected_label]

else:
    profile = build_custom_profile()


st.subheader("Aktif Profil (JSON)")
st.code(json.dumps(profile, ensure_ascii=False, indent=2), language="json")


cell_km = st.sidebar.selectbox(
    "Grid hücre boyutu (km)",
    [0.5, 1.0, 1.5, 2.0],
    index=1
)

top_n = st.sidebar.slider(
    "Analiz çıktısı limiti (satır)",
    min_value=200,
    max_value=5000,
    value=1000,
    step=200
)

map_n = st.sidebar.slider(
    "Haritada gösterilecek lokasyon sayısı",
    min_value=50,
    max_value=300,
    value=300,
    step=50
)


if st.button("Skorla ve Haritayı Göster"):
    t0 = time.time()

    profile_json = json.dumps(profile, ensure_ascii=False, sort_keys=True)

    with st.spinner("Skorlama yapılıyor..."):
        out_csv_str, out_geo_str = cached_run_profile(
            profile_json,
            float(cell_km),
            int(top_n)
        )

    out_csv = Path(out_csv_str)
    out_geo = Path(out_geo_str)

    st.info(f"Skorlama süresi: {time.time() - t0:.1f} sn")

    # TOP-20
    df = pd.read_csv(out_csv)
    top20 = df.head(20).copy()
    top20.insert(0, "rank", range(1, 21))
    top20["semt"] = top20.apply(
        lambda r: semt_from_coord(r["latitude"], r["longitude"]),
        axis=1
    )

    st.subheader("🏆 En İyi 20 Lokasyon")
    st.dataframe(
        top20[["rank", "semt", "score_total", "target_id"]],
        use_container_width=True
    )

    top_points = top20[
        ["rank", "latitude", "longitude", "score_total"]
    ].to_dict(orient="records")

    # Map
    out_html = OUT_MAPS / f"map_{profile.get('profile_id', 'custom')}.html"
    t1 = time.time()

    with st.spinner("Harita hazırlanıyor..."):
        make_map(
            geojson_path=out_geo,
            out_html=out_html,
            top_points=top_points,
            top_n=int(map_n),
            radius_m=int(profile.get("radius_m", 1000))
        )

    st.info(f"Harita üretim süresi: {time.time() - t1:.1f} sn")

    st.components.v1.html(
        out_html.read_text(encoding="utf-8"),
        height=700,
        scrolling=True
    )


