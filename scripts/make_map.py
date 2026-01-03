from pathlib import Path
import json
import math
import folium
from folium.features import DivIcon

BASE_DIR = Path(__file__).resolve().parents[1]
OUT_MAPS = BASE_DIR / "outputs" / "maps"
OUT_MAPS.mkdir(parents=True, exist_ok=True)


def haversine_m(lat1, lon1, lat2, lon2):
    R = 6371000  # Dünya yarıçapı (metre)
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)

    a = (
        math.sin(dphi / 2) ** 2
        + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
    )
    return 2 * R * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def make_map(
    geojson_path: Path,
    out_html: Path,
    top_points: list,
    top_n: int = 400,
    radius_m: int = 1000,
) -> None:


    data = json.loads(geojson_path.read_text(encoding="utf-8"))
    features = data["features"]


    if top_points:
        center_lat = sum(p["latitude"] for p in top_points) / len(top_points)
        center_lon = sum(p["longitude"] for p in top_points) / len(top_points)
    else:
        center_lat, center_lon = 41.02, 29.00

    m = folium.Map(
        location=(center_lat, center_lon),
        zoom_start=11,
        tiles="OpenStreetMap"
    )


    other_layer = folium.FeatureGroup(
        name="Diğer Uygun Lokasyonlar",
        show=True
    )
    m.add_child(other_layer)

    for f in features[:top_n]:
        lat = f["geometry"]["coordinates"][1]
        lon = f["geometry"]["coordinates"][0]


        inside_red = False
        for row in top_points:
            d = haversine_m(
                lat,
                lon,
                float(row["latitude"]),
                float(row["longitude"])
            )
            if d <= radius_m:
                inside_red = True
                break

        if inside_red:
            continue

        folium.Circle(
            location=(lat, lon),
            radius=int(radius_m * 0.5),
            color="#2b83ba",
            fill=True,
            fill_opacity=0.10,
            weight=1,
        ).add_to(other_layer)


    for row in top_points:
        lat = float(row["latitude"])
        lon = float(row["longitude"])
        rank = int(row["rank"])
        score = float(row["score_total"])

        # Etki alanı (gerçek metre)
        folium.Circle(
            location=(lat, lon),
            radius=radius_m,
            color="#d7191c",
            fill=True,
            fill_opacity=0.18,
            weight=2,
        ).add_to(m)


        folium.Marker(
            location=(lat, lon),
            icon=DivIcon(
                icon_size=(30, 30),
                icon_anchor=(15, 15),
                html=f"""
                <div style="
                    background:#d7191c;
                    color:white;
                    border-radius:50%;
                    width:30px;
                    height:30px;
                    text-align:center;
                    line-height:30px;
                    font-size:14px;
                    font-weight:bold;
                    box-shadow:0 0 6px rgba(0,0,0,0.6);
                ">{rank}</div>
                """,
            ),
            tooltip=f"TOP {rank} | Score: {score:.2f}",
        ).add_to(m)

    folium.LayerControl(collapsed=False).add_to(m)
    m.save(str(out_html))
