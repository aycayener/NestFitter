# scripts/filter_sports_centres_main.py
from pathlib import Path
import re
import unicodedata

import pandas as pd


# =========================
# AYARLAR
# =========================
BASE_DIR = Path(__file__).resolve().parents[1]

INPUT_PATH = BASE_DIR / "datasets" / "clean_csv" / "istanbul_sports_centres.csv"

OUT_DIR = BASE_DIR / "datasets" / "sports_centre_output"
OUT_DIR.mkdir(parents=True, exist_ok=True)

OUT_MAIN = OUT_DIR / "sports_centres_main.csv"
OUT_OTHER = OUT_DIR / "sports_centres_other.csv"
OUT_REVIEW = OUT_DIR / "sports_centres_review.csv"


# =========================
# YARDIMCI
# =========================
def normalize_text(s: str) -> str:
    """İsimleri daha tutarlı karşılaştırmak için sadeleştir."""
    s = "" if s is None else str(s)
    s = s.strip().lower()
    s = unicodedata.normalize("NFKD", s)
    s = "".join(ch for ch in s if not unicodedata.combining(ch))
    s = re.sub(r"\s+", " ", s)
    return s


def must_have_columns(df: pd.DataFrame, cols: list[str]) -> None:
    missing = [c for c in cols if c not in df.columns]
    if missing:
        raise ValueError(f"Eksik kolon(lar): {missing}. CSV kolonlarını kontrol et.")


def safe_col(df: pd.DataFrame, col: str) -> pd.Series:
    """Kolon yoksa NA döndür (ana zorunlular hariç)."""
    if col in df.columns:
        return df[col]
    return pd.Series([pd.NA] * len(df))


# =========================
# KURAL SETİ (İSİM BAZLI)
# =========================
# Main: gerçek spor alanları / tesisler
MAIN_KEYWORDS = [
    "spor tesisi", "spor kompleksi", "spor kompleksi", "spor merkezi",
    "spor salonu", "spor sahasi", "spor sahası", "futbol sahasi", "futbol sahası",
    "halı saha", "hali saha", "saha", "stadyum", "stadium", "arena",
    "basketbol", "voleybol", "tenis", "yuzme", "yüzme", "havuz",
    "atletizm", "salon", "gymnasium", "spor kulubu", "spor kulübü",
    "genclik merkezi", "gençlik merkezi", "olimpik", "olympic",
    "tesisleri", "tesis", "kompleks", "kapali spor", "kapalı spor",
]

# Other: spor merkezi diye geçip aslında başka şey olanlar (en sık karışanlar)
OTHER_KEYWORDS = [
    "otel", "hotel", "restaurant", "kafe", "cafe", "kahve",
    "avm", "alisveris", "alışveriş", "market", "bakkal",
    "site", "apartman", "residence", "rezidans",
    "oto yikama", "oto yıkama", "galeri", "bayi", "servis",
    "poliklinik", "klinik", "hastane",
    "okul", "kolej", "kurs", "etut", "etüt",
]

# Gym ile karışanlar: tamamen “fitness salonu” gibi ise biz bunu Review’a atalım
# (çünkü gym datası zaten ayrı kategoride var)
GYMISH_KEYWORDS = [
    "fitness", "fit ", "fitnes", "crossfit", "pilates", "body",
    "gym", "b fit", "macfit", "sports international", "be fit"
]


def is_any(text: str, keywords: list[str]) -> bool:
    return any(k in text for k in keywords)


# =========================
# MAIN
# =========================
def main() -> None:
    print("\n--- Sports Centres Filter START ---")

    if not INPUT_PATH.exists():
        raise FileNotFoundError(
            f"Sports centre CSV bulunamadı: {INPUT_PATH}\n"
            f"Dosya adını kontrol et (clean_csv içinde istanbul_sports_centres.csv olmalı)."
        )

    df = pd.read_csv(INPUT_PATH)

    print("Input:", INPUT_PATH)
    print("Toplam kayıt:", len(df))
    print("Kolonlar:", list(df.columns))

    # Zorunlu kolonlar
    must_have_columns(df, ["name"])
    # koordinatlar bazı dosyalarda longitude/latitude, bazılarında lon/lat olabiliyor:
    # sende clean_all_csv sonrası genelde longitude/latitude var.
    if "longitude" not in df.columns or "latitude" not in df.columns:
        raise ValueError("longitude/latitude kolonları yok. clean_all_csv çıktısını kullandığından emin ol.")

    # name normalize
    df["name"] = df["name"].astype(str).str.strip()
    df["name_norm"] = df["name"].apply(normalize_text)

    # Opsiyonel etiket kolonları (varsa bonus sinyal)
    leisure = safe_col(df, "leisure").astype(str).apply(normalize_text)
    sport = safe_col(df, "sport").astype(str).apply(normalize_text)
    amenity = safe_col(df, "amenity").astype(str).apply(normalize_text)

    main_rows = []
    other_rows = []
    review_rows = []

    for _, row in df.iterrows():
        name_norm = row["name_norm"]

        # 1) Direkt other (bariz alakasız)
        if is_any(name_norm, OTHER_KEYWORDS):
            other_rows.append(row)
            continue

        # 2) Gym gibi görünüyor → gym datasıyla karışmasın diye review
        if is_any(name_norm, GYMISH_KEYWORDS):
            review_rows.append(row)
            continue

        # 3) Etiket bazlı güçlü sinyal
        # OSM tarafında bazıları leisure=sports_centre / pitch / stadium / sports_hall gibi gelebilir
        tag_strong_main = (
            ("sports_centre" in leisure.values) or
            ("sports centre" in leisure.values) or
            ("pitch" in leisure.values) or
            ("stadium" in leisure.values) or
            ("sports_hall" in leisure.values) or
            ("sport" in sport.values) or
            ("sports_centre" in amenity.values)
        )
        # Yukarıdaki values kontrolü her satır için değil; bu satır özelinde kontrol edelim:
        leisure_v = normalize_text(row.get("leisure", ""))
        sport_v = normalize_text(row.get("sport", ""))
        amenity_v = normalize_text(row.get("amenity", ""))

        tag_main = any(x in leisure_v for x in ["sports_centre", "pitch", "stadium", "sports_hall"]) or \
                   (sport_v not in ["", "na", "none", "nan"]) or \
                   ("sports_centre" in amenity_v)

        if tag_main:
            main_rows.append(row)
            continue

        # 4) İsim bazlı main
        if is_any(name_norm, MAIN_KEYWORDS):
            main_rows.append(row)
            continue

        # 5) Geri kalanlar: emin değiliz
        review_rows.append(row)

    main_df = pd.DataFrame(main_rows).drop(columns=["name_norm"], errors="ignore")
    other_df = pd.DataFrame(other_rows).drop(columns=["name_norm"], errors="ignore")
    review_df = pd.DataFrame(review_rows).drop(columns=["name_norm"], errors="ignore")

    main_df.to_csv(OUT_MAIN, index=False)
    other_df.to_csv(OUT_OTHER, index=False)
    review_df.to_csv(OUT_REVIEW, index=False)

    print("\n--- Sports Centres Filter DONE ---")
    print("Main:", len(main_df), "->", OUT_MAIN)
    print("Other:", len(other_df), "->", OUT_OTHER)
    print("Review:", len(review_df), "->", OUT_REVIEW)

    if len(review_df) > 0 and "name" in review_df.columns:
        print("\nReview örnekleri (ilk 15):")
        print(review_df[["name"]].head(15).to_string(index=False))

    print("\nProcess finished.")


if __name__ == "__main__":
    main()
