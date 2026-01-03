# scripts/scoring_grid.py
from __future__ import annotations

from pathlib import Path
import json
import math
import pandas as pd

BASE_DIR = Path(__file__).resolve().parents[1]

OUT_SCORING = BASE_DIR / "outputs" / "scoring"
OUT_SCORING.mkdir(parents=True, exist_ok=True)

OUT_PROFILES = BASE_DIR / "outputs" / "profiles"
OUT_PROFILES.mkdir(parents=True, exist_ok=True)


# Bu sözlük: kategori adı -> csv yolu
# Ama herkesin bilgisayarında tüm csv’ler olmayabilir.
# O yüzden scoring sırasında "varsa yükle" mantığıyla gidiyoruz.
INPUTS = {
    "hospital_main": BASE_DIR / "datasets" / "hospital_output" / "hospitals_main.csv",
    "supermarket_main": BASE_DIR / "datasets" / "supermarket_output" / "supermarkets_main.csv",
    "school_public": BASE_DIR / "datasets" / "school_output" / "schools_public.csv",
    "park_main": BASE_DIR / "datasets" / "park_output" / "parks_main.csv",
    "station_main": BASE_DIR / "datasets" / "station_output" / "stations_main.csv",
    "mall_main": BASE_DIR / "outputs" / "avm_clean.csv",
    # opsiyoneller
    "gym_main": BASE_DIR / "datasets" / "gym_output" / "gyms_main.csv",
    "sports_centre_main": BASE_DIR / "datasets" / "sports_output" / "sports_centre_main.csv",
    "parking_main": BASE_DIR / "datasets" / "parking_output" / "parking_main.csv",
    "cafe_main": BASE_DIR / "datasets" / "cafe_output" / "cafes_main.csv",
    "bar_main": BASE_DIR / "datasets" / "bar_output" / "bars_main.csv",
    "school_private": BASE_DIR / "datasets" / "school_output" / "schools_private.csv",
    "school_courses": BASE_DIR / "datasets" / "school_output" / "schools_courses.csv",
}

REQUIRED_COLS = ["latitude", "longitude"]


def _require_file(path: Path) -> None:
    # net hata: dosya yoksa “nerede beklediğini” söyleyelim
    if not path.exists():
        raise FileNotFoundError(f"Eksik dosya: {path}")


def load_poi_csv(path: Path) -> pd.DataFrame:
    """
    CSV okuyoruz + latitude/longitude kontrol ediyoruz.
    Buradaki kontrol şart, yoksa skorlamada hata aramak işkence oluyor.
    """
    _require_file(path)
    df = pd.read_csv(path)

    missing = [c for c in REQUIRED_COLS if c not in df.columns]
    if missing:
        raise ValueError(f"{path} şu kolonları içermiyor: {missing} | beklenen: {REQUIRED_COLS}")

    df = df.dropna(subset=["latitude", "longitude"]).copy()
    df["latitude"] = df["latitude"].astype(float)
    df["longitude"] = df["longitude"].astype(float)
    return df


def haversine_m(lat1, lon1, lat2, lon2) -> float:
    """
    İki nokta arası mesafeyi metre cinsinden buluyor.
    Çünkü 'radius_m' ile “1km içinde kaç tane var?” gibi hesap yapacağız.
    """
    R = 6371000.0
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dl = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dl / 2) ** 2
    return 2 * R * math.asin(math.sqrt(a))


def bbox_from_pois(pois: dict[str, pd.DataFrame]) -> tuple[float, float, float, float]:
    """
    Semt shapefile yoksa İstanbul'u “grid” yapacağız.
    Grid için bir alan (bbox) lazım.
    Bbox'u: tüm POI noktalarının min/max lat lon'una göre çıkartıyoruz.
    """
    all_df = pd.concat([df[["latitude", "longitude"]] for df in pois.values()], ignore_index=True)
    min_lat = float(all_df["latitude"].min())
    max_lat = float(all_df["latitude"].max())
    min_lon = float(all_df["longitude"].min())
    max_lon = float(all_df["longitude"].max())

    # küçük buffer: sınırda kalmasın diye
    pad_lat = 0.02
    pad_lon = 0.02
    return (min_lat - pad_lat, min_lon - pad_lon, max_lat + pad_lat, max_lon + pad_lon)


def build_grid(bbox, cell_km=1.0) -> pd.DataFrame:
    """
    İstanbul yerine “grid hücreleri” oluşturuyoruz.
    1km x 1km gibi düşünebilirsin.
    Sonra her hücrenin merkezini skorlayacağız.
    """
    min_lat, min_lon, max_lat, max_lon = bbox

    # 1 derece enlem ~ 111km. Bu yüzden km -> derece dönüşümü yapıyoruz.
    lat_step = cell_km / 111.0

    # boylam dönüşümü enleme göre değişiyor (cos(lat) var)
    mid_lat = (min_lat + max_lat) / 2
    lon_step = cell_km / (111.0 * math.cos(math.radians(mid_lat)))

    lats, lons = [], []
    lat = min_lat
    while lat <= max_lat:
        lon = min_lon
        while lon <= max_lon:
            lats.append(lat + lat_step / 2)  # hücre merkezi
            lons.append(lon + lon_step / 2)
            lon += lon_step
        lat += lat_step

    grid = pd.DataFrame({"latitude": lats, "longitude": lons})
    grid["target_id"] = [f"cell_{i:06d}" for i in range(len(grid))]
    grid["name"] = grid["target_id"]
    return grid


def count_within_radius(grid: pd.DataFrame, poi: pd.DataFrame, radius_m: int) -> list[int]:
    """
    Her grid noktası için:
    “radius_m içinde kaç POI var?” sayıyoruz.
    Şu an naive (yavaş) ama ilk demo için yeter.
    Gerekirse sonra optimize ederiz.
    """
    poi_points = list(zip(poi["latitude"].tolist(), poi["longitude"].tolist()))

    counts = []
    for _, row in grid.iterrows():
        lat, lon = float(row["latitude"]), float(row["longitude"])
        c = 0
        for plat, plon in poi_points:
            if haversine_m(lat, lon, plat, plon) <= radius_m:
                c += 1
        counts.append(c)
    return counts


def saturating_score(count: int) -> float:
    """
    “çok sayıda POI olunca puan sonsuza gitmesin” diye,
    diminishing returns uyguluyoruz.
    Yani: 1->çok değerli, 20->o kadar da fark etmesin.
    """
    return 5.0 * (1 - math.exp(-count / 3.0))


def load_pois_for_profile(profile: dict) -> dict[str, pd.DataFrame]:
    """
    Profilin weights/must_have/avoid alanlarına bakıp,
    sadece gereken POI csv’lerini yüklüyoruz.
    """
    pois = {}

    # weights içindeki kategorileri yükle
    for cat in profile.get("weights", {}).keys():
        if cat in INPUTS and INPUTS[cat].exists():
            pois[cat] = load_poi_csv(INPUTS[cat])

    # must_have varsa bunlar yoksa projeyi zaten bozar: net hata verelim
    for cat in profile.get("must_have", []) or []:
        if cat in INPUTS:
            _require_file(INPUTS[cat])
            pois[cat] = load_poi_csv(INPUTS[cat])

    # avoid varsa ve dosya varsa yükleyelim (yoksa çok problem değil)
    for cat in profile.get("avoid", []) or []:
        if cat in INPUTS and INPUTS[cat].exists():
            pois[cat] = load_poi_csv(INPUTS[cat])

    if not pois:
        raise ValueError("Hiç POI yüklenemedi. weights/must_have ve dosya yollarını kontrol et.")
    return pois


def score_grid(profile: dict, pois: dict[str, pd.DataFrame], cell_km=1.0) -> pd.DataFrame:
    """
    Burada gerçek skor çıkıyor.
    1) grid üret
    2) her kategori için count çıkar
    3) count -> puan çevir, weight ile çarp
    4) must_have kontrolü
    """
    radius_m = int(profile.get("radius_m", 1000))
    weights: dict = profile.get("weights", {})
    must_have = profile.get("must_have", []) or []
    avoid = set(profile.get("avoid", []) or [])

    bbox = bbox_from_pois(pois)
    grid = build_grid(bbox, cell_km=cell_km)

    score_total = [0.0] * len(grid)
    breakdown = {}

    for cat, w in weights.items():
        if cat not in pois:
            continue

        counts = count_within_radius(grid, pois[cat], radius_m)
        grid[f"{cat}_count"] = counts

        # avoid kategorilerde “yakınsa daha fazla ceza” mantığı koyuyoruz
        if cat in avoid:
            contrib = [float(w) * (c if c <= 2 else c * 2) for c in counts]
        else:
            contrib = [float(w) * saturating_score(c) for c in counts]

        breakdown[cat] = contrib
        score_total = [st + cc for st, cc in zip(score_total, contrib)]

    # must_have: mesela school_public şart ise,
    # o hücrenin 1km içinde en az 1 okul yoksa o hücreyi ele
    if must_have:
        ok_mask = [True] * len(grid)
        for cat in must_have:
            col = f"{cat}_count"
            if col not in grid.columns:
                ok_mask = [False] * len(grid)
                break
            ok_mask = [ok and (int(v) >= 1) for ok, v in zip(ok_mask, grid[col].tolist())]

        score_total = [s if ok else -1e9 for s, ok in zip(score_total, ok_mask)]

    grid["score_total"] = score_total

    # breakdown'u json string tutuyoruz ki csv içinde okunabilir olsun
    score_breakdown = []
    for i in range(len(grid)):
        d = {k: float(breakdown[k][i]) for k in breakdown.keys()}
        score_breakdown.append(json.dumps(d, ensure_ascii=False))
    grid["score_breakdown"] = score_breakdown

    grid = grid.sort_values("score_total", ascending=False).reset_index(drop=True)
    return grid


def to_geojson(df: pd.DataFrame, out_path: Path) -> None:
    """
    Streamlit + harita tarafı için GeoJSON çok iş görüyor.
    Burada df -> GeoJSON yazıyoruz.
    """
    feats = []
    for _, r in df.iterrows():
        feats.append(
            {
                "type": "Feature",
                "geometry": {"type": "Point", "coordinates": [float(r["longitude"]), float(r["latitude"])]},
                "properties": {
                    "target_id": r["target_id"],
                    "name": r.get("name", ""),
                    "score_total": float(r["score_total"]),
                    "score_breakdown": r.get("score_breakdown", "{}"),
                },
            }
        )

    geo = {"type": "FeatureCollection", "features": feats}
    out_path.write_text(json.dumps(geo, ensure_ascii=False), encoding="utf-8")


def run_profile(profile: dict, cell_km=1.0, top_n=5000):
    """
    App tarafında “butona basınca” çağırmak için bunu tek fonksiyon yaptık.
    Yani app.py sadece bunu çağırıyor, gerisini burada hallediyoruz.
    """
    pois = load_pois_for_profile(profile)
    df = score_grid(profile, pois, cell_km=cell_km)

    if top_n and len(df) > top_n:
        df = df.head(top_n).copy()

    pid = profile.get("profile_id", "custom")
    out_csv = OUT_SCORING / f"grid_scores_{pid}.csv"
    out_geo = OUT_SCORING / f"grid_scores_{pid}.geojson"

    df.to_csv(out_csv, index=False, encoding="utf-8")
    to_geojson(df, out_geo)

    print(f"[OK] profile={pid} | rows={len(df)}")
    print(df[["target_id", "latitude", "longitude", "score_total"]].head(10).to_string(index=False))

    return out_csv, out_geo


def load_profiles_json() -> list[dict]:
    """
    Preset profil seçme modu için.
    """
    path = OUT_PROFILES / "user_profiles.json"
    _require_file(path)
    return json.loads(path.read_text(encoding="utf-8"))


def main():
    # Terminalden test etmek istersek diye örnek main bıraktım.
    profiles = load_profiles_json()
    out_csv, out_geo = run_profile(profiles[0], cell_km=1.0, top_n=5000)
    print(out_csv, out_geo)


if __name__ == "__main__":
    main()
