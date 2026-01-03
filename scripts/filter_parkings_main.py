from pathlib import Path
import pandas as pd
import re
import unicodedata

# =========================
# 1) AYARLAR
# =========================
BASE_DIR = Path(__file__).resolve().parents[1]

# genelde doğru yer:
INPUT_PATH = BASE_DIR / "datasets" / "clean_csv" / "istanbul_parkings.csv"
# eğer farklıysa şurayı değiştir:
# INPUT_PATH = BASE_DIR / "datasets" / "clean_csv" / "parkings.csv"

OUT_DIR = BASE_DIR / "datasets" / "parking_output"
OUT_DIR.mkdir(parents=True, exist_ok=True)

OUT_MAIN = OUT_DIR / "parkings_main.csv"
OUT_OTHER = OUT_DIR / "parkings_other.csv"
OUT_REVIEW = OUT_DIR / "parkings_review.csv"

# =========================
# 2) TEXT NORMALIZE
# =========================
def norm_text(s: str) -> str:
    if s is None:
        return ""
    s = str(s).strip().lower()
    s = unicodedata.normalize("NFKD", s)
    s = "".join(ch for ch in s if not unicodedata.combining(ch))  # türkçe aksan kır
    s = re.sub(r"[^a-z0-9\s]", " ", s)
    s = re.sub(r"\s+", " ", s).strip()
    return s

def has_any(text: str, keywords: list[str]) -> bool:
    return any(k in text for k in keywords)

# =========================
# 3) KURAL SETİ (isim bazlı + tag bazlı)
# =========================
# İyi/gerçek park yeri sinyalleri
KW_PARKING_GOOD = [
    "otopark", "parking", "car park", "park alani", "park alanı",
    "kapali otopark", "acik otopark", "katli otopark", "yer alti otopark", "yeraltı otopark",
    "valet", "vale", "ispark", "i spark"
]

# Park yeri değil / servis gibi şeyler (yanlış etiketlenmiş olabiliyor)
KW_NOT_PARKING = [
    "oto yikama", "oto yıkama", "car wash", "yikama", "yıkama",
    "lastik", "tire", "tamir", "repair", "servis", "service",
    "kaporta", "boya", "oto ekspertiz", "ekspertiz",
    "galeri", "oto galeri", "showroom",
    "akaryakit", "akaryakıt", "benzin", "petrol", "fuel", "lpg",
    "rent a car", "kiralik arac", "kiralık araç"
]

# “Diğer”e atmak istediğimiz: özel/site/apartman içi, sadece konut için olan parklar
KW_PRIVATE_HINT = [
    "site", "apartman", "residence", "rezidans", "konut",
    "blok", "bina", "daire", "villa",
    "personel", "staff", "only", "sakin", "sakinleri"
]

# Tag sinyalleri (OSM kolonları varsa)
PRIVATE_ACCESS_VALUES = {"private", "customers", "permissive"}  # müşteriye özel de “main” olabilir ama çoğu karışık
GOOD_PARKING_TYPES = {"multi-storey", "underground", "surface", "street_side"}

# =========================
# 4) ANA AKIŞ
# =========================
def main():
    print("\n--- Parking Filter START ---")
    print("Input:", INPUT_PATH)

    if not INPUT_PATH.exists():
        raise FileNotFoundError(
            f"Parking CSV bulunamadı: {INPUT_PATH}\n"
            f"Dosya adı farklıysa scripts/filter_parkings_main.py içindeki INPUT_PATH'i güncelle."
        )

    df = pd.read_csv(INPUT_PATH)
    print("Toplam kayıt:", len(df))
    print("Kolonlar:", list(df.columns))

    # kolonlar değişebiliyor: biz güvenli biçimde okuyalım
    name_col = "name" if "name" in df.columns else None

    # OSM tarafı bazen: amenity=parking + access + parking gibi kolonlarla geliyor
    access_col = "access" if "access" in df.columns else None
    parking_col = "parking" if "parking" in df.columns else None
    amenity_col = "amenity" if "amenity" in df.columns else None

    # isim normalize
    if name_col:
        df["_name_raw"] = df[name_col].astype(str)
        df["_name_norm"] = df["_name_raw"].map(norm_text)
    else:
        df["_name_raw"] = ""
        df["_name_norm"] = ""

    # Tag normalize (varsa)
    def safe_lower(series_name: str) -> pd.Series:
        if series_name and series_name in df.columns:
            return df[series_name].astype(str).str.strip().str.lower()
        return pd.Series([""] * len(df))

    df["_access"] = safe_lower(access_col)
    df["_parking_tag"] = safe_lower(parking_col)
    df["_amenity"] = safe_lower(amenity_col)

    labels = []
    for _, row in df.iterrows():
        n = row["_name_norm"]
        access = row["_access"]
        ptag = row["_parking_tag"]
        amenity = row["_amenity"]

        # 1) Net “park yeri değil” sinyali
        if has_any(n, KW_NOT_PARKING):
            labels.append("OTHER")
            continue

        # 2) Tag bazlı net sinyal (amenity=parking ise genelde iyi)
        # ama “private/site” gibi ipuçları varsa OTHER'a alıyoruz
        if amenity == "parking":
            if (access in PRIVATE_ACCESS_VALUES and has_any(n, KW_PRIVATE_HINT)) or has_any(n, KW_PRIVATE_HINT):
                labels.append("OTHER")
            else:
                # parking tipi biliniyorsa daha güvenli
                if ptag in GOOD_PARKING_TYPES or has_any(n, KW_PARKING_GOOD):
                    labels.append("MAIN")
                else:
                    labels.append("REVIEW")
            continue

        # 3) İsme göre karar
        if has_any(n, KW_PARKING_GOOD):
            # “site/apartman” gibi özel kullanım çok baskınsa OTHER
            if has_any(n, KW_PRIVATE_HINT):
                labels.append("OTHER")
            else:
                labels.append("MAIN")
            continue

        # 4) Hiçbir şey yakalamadıysa: REVIEW
        labels.append("REVIEW")

    df["bucket"] = labels

    main_df = df[df["bucket"] == "MAIN"].drop(columns=["bucket"], errors="ignore")
    other_df = df[df["bucket"] == "OTHER"].drop(columns=["bucket"], errors="ignore")
    review_df = df[df["bucket"] == "REVIEW"].drop(columns=["bucket"], errors="ignore")

    # Kaydet
    main_df.to_csv(OUT_MAIN, index=False)
    other_df.to_csv(OUT_OTHER, index=False)
    review_df.to_csv(OUT_REVIEW, index=False)

    print("\n--- Parking Filter DONE ---")
    print("Main:", len(main_df), "->", OUT_MAIN)
    print("Other:", len(other_df), "->", OUT_OTHER)
    print("Review:", len(review_df), "->", OUT_REVIEW)

    # Küçük örnek (abartmadan)
    if len(review_df) > 0:
        sample = review_df[["name"]].head(15) if "name" in review_df.columns else review_df.head(15)
        print("\nReview örnekleri (ilk 15):")
        print(sample.to_string(index=False))

    print("\nProcess finished.")

if __name__ == "__main__":
    main()
