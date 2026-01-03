from pathlib import Path
import pandas as pd
import unicodedata

# =====================================================
# 1) AYARLAR
# =====================================================

BASE_DIR = Path(__file__).resolve().parents[1]

# clean_csv içinden okuyoruz (genelde en doğru yer)
INPUT_PATH = BASE_DIR / "datasets" / "clean_csv" / "istanbul_supermarkets.csv"

OUT_DIR = BASE_DIR / "datasets" / "supermarket_output"
OUT_DIR.mkdir(parents=True, exist_ok=True)

# =====================================================
# 2) YARDIMCI FONKSİYONLAR
# =====================================================

def normalize_text(text):
    """Metni sadeleştirir (küçük harf, Türkçe karakter temizliği)"""
    if not isinstance(text, str):
        return ""
    text = unicodedata.normalize("NFKD", text)
    text = "".join(c for c in text if not unicodedata.combining(c))
    return text.lower().strip()

# =====================================================
# 3) ANA FİLTRE KURALLARI
# =====================================================

# Ana süpermarket zincirleri
MAIN_KEYWORDS = [
    "migros",
    "carrefour",
    "macrocenter",
    "bim",
    "a101",
    "sok",
    "şok",
    "metro",
    "file"
]

# Kesin elenecek ifadeler
EXCLUDE_KEYWORDS = [
    "bakkal",
    "mini",
    "kucuk",
    "küçük",
    "corner",
    "local"
]

# Gri alan tetikleyiciler
REVIEW_KEYWORDS = [
    "avm",
    "market"
]

# =====================================================
# 4) MAIN
# =====================================================

def main():
    if not INPUT_PATH.exists():
        raise FileNotFoundError(
            f"Supermarket CSV bulunamadı: {INPUT_PATH}"
        )

    df = pd.read_csv(INPUT_PATH)
    print("\n--- Supermarket Filter START ---")
    print("Input:", INPUT_PATH)
    print("Toplam kayıt:", len(df))

    # Name normalize
    df["name_norm"] = df["name"].apply(normalize_text)

    main_rows = []
    other_rows = []
    review_rows = []

    for _, row in df.iterrows():
        name = row["name_norm"]

        # Ana zincir kontrolü
        if any(k in name for k in MAIN_KEYWORDS):
            main_rows.append(row)

        # Kesin elenecekler
        elif any(k in name for k in EXCLUDE_KEYWORDS):
            other_rows.append(row)

        # Gri alan
        elif any(k in name for k in REVIEW_KEYWORDS):
            review_rows.append(row)

        # Diğer her şey review
        else:
            review_rows.append(row)

    df_main = pd.DataFrame(main_rows).drop(columns=["name_norm"], errors="ignore")
    df_other = pd.DataFrame(other_rows).drop(columns=["name_norm"], errors="ignore")
    df_review = pd.DataFrame(review_rows).drop(columns=["name_norm"], errors="ignore")

    # =====================================================
    # 5) ÇIKTILAR
    # =====================================================

    main_path = OUT_DIR / "supermarkets_main.csv"
    other_path = OUT_DIR / "supermarkets_other.csv"
    review_path = OUT_DIR / "supermarkets_review.csv"

    df_main.to_csv(main_path, index=False)
    df_other.to_csv(other_path, index=False)
    df_review.to_csv(review_path, index=False)

    print("\n--- Supermarket Filter DONE ---")
    print("Main:", len(df_main), "->", main_path)
    print("Other:", len(df_other), "->", other_path)
    print("Review:", len(df_review), "->", review_path)

    print("\nReview örnekleri (ilk 15):")
    if not df_review.empty:
        print(df_review[["name"]].head(15))

    print("\nProcess finished.")

# =====================================================
if __name__ == "__main__":
    main()
