from pathlib import Path
import geopandas as gpd

# Proje kökü
BASE_DIR = Path(__file__).resolve().parents[1]

RAW_DIR = BASE_DIR / "datasets" / "raw_geojson"
OUT_DIR = BASE_DIR / "datasets" / "processed_csv"

OUT_DIR.mkdir(parents=True, exist_ok=True)

print("RAW_DIR:", RAW_DIR)
print("OUT_DIR:", OUT_DIR)

def to_point_geometry(gdf):
    gdf = gdf.copy()
    non_points = ~gdf.geometry.geom_type.isin(["Point"])
    gdf.loc[non_points, "geometry"] = gdf.loc[non_points, "geometry"].centroid
    return gdf

for geojson_file in RAW_DIR.glob("*.geojson"):
    print(f"Processing: {geojson_file.name}")

    gdf = gpd.read_file(geojson_file)
    gdf = to_point_geometry(gdf)

    gdf["longitude"] = gdf.geometry.x
    gdf["latitude"] = gdf.geometry.y

    if "name" not in gdf.columns:
        gdf["name"] = None

    keep_cols = [
        c for c in ["name", "amenity", "shop", "leisure", "longitude", "latitude"]
        if c in gdf.columns
    ]

    df = gdf[keep_cols]

    out_csv = OUT_DIR / f"{geojson_file.stem}.csv"
    df.to_csv(out_csv, index=False)

    print(f"Saved → {out_csv.name}")

print("✅ Tüm GeoJSON dosyaları başarıyla CSV’ye çevrildi.")

