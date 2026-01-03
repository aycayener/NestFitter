from __future__ import annotations

import json
from pathlib import Path

import pandas as pd


"""
AVM PIPELINE (PAYLAŞILABİLİR SÜRÜM)

Girdi:
- Proje kök dizininde üretilen 'true_avm_from_your_pool.csv' (filter_avms_by_wikipedia.py çıktısı)

Çıktı:
- outputs/avm_clean.csv
- outputs/avm_clean.geojson

Not:
- Bu dosya "opsiyonel akış" içermez. Gerekli dosya/kolon yoksa net hata verir.
"""


# -------------------------
# PATH AYARLARI
# -------------------------
BASE_DIR = Path(__file__).resolve().parents[1]
OUT_DIR = BASE_DIR / "outputs"
OUT_DIR.mkdir(exist_ok=True)

AVM_INPUT = BASE_DIR / "true_avm_from_your_pool.csv"   # ✅ tek doğru kaynak

OUT_AVM_CSV = OUT_DIR / "avm_clean.csv"
OUT_AVM_GEOJSON = OUT_DIR / "avm_clean.geojson"


# -------------------------
# KOLON STANDARTLARI
# -------------------------
NAME_COL = "name"
LAT_COL = "latitude"
LON_COL = "longitude"


def require_file(path: Path, label: str) -> None:
    if not path.exists():
        raise FileNotFoundError(f"[{label}] Dosya bulunamadı: {path}")


def require_columns(df: pd.DataFrame, cols: list[str], label: str) -> None:
    missing = [c for c in cols if c not in df.columns]
    if missing:
        raise ValueError(
            f"[{label}] Eksik kolon(lar): {missing}\n"
            f"Mevcut kolonlar: {list(df.columns)}"
        )


def to_geojson_points(df: pd.DataFrame, lat_col: str, lon_col: str, prop_cols: list[str]) -> dict:
    features = []
    for _, row in df.iterrows():
        lat = float(row[lat_col])
        lon = float(row[lon_col])

        props = {}
        for c in prop_cols:
            v = row[c]
            props[c] = None if pd.isna(v) else v

        features.append(
            {
                "type": "Feature",
                "geometry": {"type": "Point", "coordinates": [lon, lat]},
                "properties": props,
            }
        )
    return {"type": "FeatureCollection", "features": features}


def main() -> None:
    print("=== AVM PIPELINE ===")
    print("BASE_DIR:", BASE_DIR)

    # 1) Girdi dosyası kontrol
    require_file(AVM_INPUT, "AVM_INPUT")

    # 2) Oku
    avm = pd.read_csv(AVM_INPUT)
    require_columns(avm, [NAME_COL, LAT_COL, LON_COL], "AVM_INPUT")

    # 3) Tip dönüşümü / temizlik
    avm = avm.copy()
    avm[LAT_COL] = pd.to_numeric(avm[LAT_COL], errors="coerce")
    avm[LON_COL] = pd.to_numeric(avm[LON_COL], errors="coerce")
    avm = avm.dropna(subset=[LAT_COL, LON_COL])

    # İsteğe bağlı değil, standardizasyon: aynı isim+koordinat tekrarlarını kaldır
    avm = avm.drop_duplicates(subset=[NAME_COL, LAT_COL, LON_COL]).reset_index(drop=True)

    print(f"Toplam AVM (temiz): {len(avm)}")

    # 4) CSV çıktı
    avm.to_csv(OUT_AVM_CSV, index=False, encoding="utf-8-sig")
    print("Yazıldı:", OUT_AVM_CSV)

    # 5) GeoJSON çıktı
    prop_cols = [c for c in avm.columns if c not in {LAT_COL, LON_COL}]
    geo = to_geojson_points(avm, LAT_COL, LON_COL, prop_cols)

    with open(OUT_AVM_GEOJSON, "w", encoding="utf-8") as f:
        json.dump(geo, f, ensure_ascii=False)

    print("Yazıldı:", OUT_AVM_GEOJSON)
    print("Bitti ✅")


if __name__ == "__main__":
    main()
