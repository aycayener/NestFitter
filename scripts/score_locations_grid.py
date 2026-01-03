import pandas as pd
import numpy as np
from pathlib import Path
import folium

# ==================================================
# PATH
# ==================================================
BASE_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = BASE_DIR / "datasets" / "clean_csv"

# ==================================================
# AYARLAR
# ==================================================
GRID_SIZE_KM = 1.0
RADIUS_M = 1000  # 1 km

# ==================================================
# HAVERSINE
# ==================================================
def haversine(lat1, lon1, lat2, lon2):
    R = 6371000  # metre
    phi1 = np.radians(lat1)
    phi2 = np.radians(lat2)
    dphi = np.radians(lat2 - lat1)
    dlambda = np.radians(lon2 - lon1)

    a = np.sin(dphi / 2) ** 2 + np.cos(phi1) * np.cos(phi2) * np.sin(dlambda / 2) ** 2
    return 2 * R * np.arcsin(np.sqrt(a))

# ==================================================
# POI YÜKLE
# ==================================================
def load_poi(csv_name):
    path = DATA_DIR / csv_name

    if not path.exists():
        print(f"[WARN] {csv_name} bulunamadı")
        return pd.DataFrame(columns=["latitude", "longitude"])

    df = pd.read_csv(path)

    # Kolon kontrolü
    required_cols = {"latitude", "longitude"}
    if not required_cols.issubset(df.columns):
        raise ValueError(
            f"{csv_name} kolonları hatalı. Bulunan: {list(df.columns)}"
        )

    # Sayısal dönüşüm (ÇOK ÖNEMLİ)
    df["latitude"] = pd.to_numeric(df["latitude"], errors="coerce")
    df["longitude"] = pd.to_numeric(df["longitude"], errors="coerce")

    df = df.dropna(subset=["latitude", "longitude"])

    return df[["latitude", "longitude"]]


# ==================================================
# GRID OLUŞTUR
# ==================================================
def create_grid():
    dfs = []
    for f in DATA_DIR.glob("istanbul_*.csv"):
        df = pd.read_csv(f)
        dfs.append(df)

    all_df = pd.concat(dfs, ignore_index=True)

    min_lat, max_lat = all_df["latitude"].min(), all_df["latitude"].max()
    min_lon, max_lon = all_df["longitude"].min(), all_df["longitude"].max()

    # 1 km grid adımı (coğrafi doğru)
    step_lat = GRID_SIZE_KM / 111
    step_lon = GRID_SIZE_KM / (111 * np.cos(np.radians((min_lat + max_lat) / 2)))

    grid = []
    grid_id = 0

    lat = min_lat
    while lat <= max_lat:
        lon = min_lon
        while lon <= max_lon:
            grid.append({
                "grid_id": grid_id,
                "latitude": lat,
                "longitude": lon
            })
            grid_id += 1
            lon += step_lon
        lat += step_lat

    grid_df = pd.DataFrame(grid)
    return grid_df


# ==================================================
# SKOR HESAPLA
# ==================================================
def score_grids(weights: dict):
    grid_df = create_grid()

    poi_map = {
        "park_main": "istanbul_parks.csv",
        "gym_main": "istanbul_gyms.csv",
        "sports_centre_main": "istanbul_sports_centres.csv",
        "station_main": "istanbul_stations.csv",
        "bar_main": "istanbul_bars.csv",
        "supermarket_main": "istanbul_supermarkets.csv",
        "mall_main": "istanbul_malls.csv",
        "cafe_main": "istanbul_cafes.csv",
        "school_public": "istanbul_schools.csv",
        "hospital_main": "istanbul_hospitals.csv"
    }

    poi_data = {
        k: load_poi(v) for k, v in poi_map.items()
    }

    scores = []

    for _, grid in grid_df.iterrows():
        total_score = 0
        breakdown = {}

        for poi_key, weight in weights.items():
            if poi_key not in poi_data:
                continue

            poi_df = poi_data[poi_key]
            if poi_df.empty:
                continue

            dists = haversine(
                grid["latitude"],
                grid["longitude"],
                poi_df["latitude"].values,
                poi_df["longitude"].values
            )

            count = int((dists <= RADIUS_M).sum())
            if count > 0:
                print(f"[DEBUG] {poi_key}: {count} bulundu")

            breakdown[poi_key] = count
            total_score += count * weight

        scores.append({
            "grid_id": grid["grid_id"],
            "latitude": grid["latitude"],
            "longitude": grid["longitude"],
            "score": total_score,
            "breakdown": breakdown
        })

    return pd.DataFrame(scores).sort_values("score", ascending=False)

# ==================================================
# HARİTA
# ==================================================
def create_map(scored_df, top_n=5):
    top = scored_df.head(top_n)

    m = folium.Map(
        location=[top.iloc[0]["latitude"], top.iloc[0]["longitude"]],
        zoom_start=11
    )

    for _, row in top.iterrows():
        folium.Marker(
            location=[row["latitude"], row["longitude"]],
            popup=f"Skor: {row['score']}<br>Detay: {row['breakdown']}",
            icon=folium.Icon(color="green", icon="home")
        ).add_to(m)

    return m
