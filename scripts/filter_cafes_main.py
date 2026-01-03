from pathlib import Path
import pandas as pd
import re
import unicodedata

# =========================
# AYARLAR
# =========================
BASE_DIR = Path(__file__).resolve().parents[1]

INPUT_PATH = BASE_DIR / "datasets" / "clean_csv" / "istanbul_cafes.csv"

OUT_DIR = BASE_DIR / "datasets" / "cafe_output"
OUT_DIR.mkdir(parents=True, exist_ok=True)

OUT_MAIN = OUT_DIR / "cafes_main.csv"
OUT_OTHER = OUT_DIR / "cafes_other.csv"
OUT_REVIEW = OUT_DIR / "cafes_review.csv"

# =========================
# TEMEL YARDIMCILAR
# =========================
def norm(s: str) -> str:
    if s is None:
        return ""
    s = str(s).strip().lower()
    s = unicodedata.normalize("NFKD", s)
    s = "".join(ch for ch in s if not unicodedata.combining(ch))
    s = re.sub(r"\s+", " ", s)
    return s

def has_any(text: str, keywords: list[str]) -> bool:
    return any(k in text for k in keywords)

# =========================
# KURALLAR
# =========================
# Cafe için MAIN = kahve/kafe ağırlıklı yerler
CAFE_MAIN_KEYS = [
    "cafe", "kafe", "coffee", "kahve", "espresso", "latte", "mocha",
    "coffeehouse", "coffeeshop", "roastery", "kahveci",
    "starbucks", "gloria jeans", "kahve dunyasi", "kahve dünyası",
    "caribou", "tchibo", "coffeelab", "coffee lab", "petra", "fabrik", "moc"
]

# Cafe datasında yanlışlıkla gelen/karışan şeyler (OTHER)
CAFE_OTHER_KEYS = [
    "bar", "pub", "club", "night", "gece", "meyhane", "bira",
    "restaurant", "restoran", "lokanta", "ocakbasi", "ocakbaşı",
    "pide", "lahmacun", "kebap", "doner", "döner",
    "hotel", "otel", "hostel",
    "market", "bakkal", "supermarket", "süpermarket"
]

# Net değilse review
# (ör: sadece marka/özel isim, içinde cafe/kahve geçmiyorsa vb.)
def decide_cafe(row: pd.Series) -> str:
    name = norm(row.get("name", ""))

    # adı yoksa zaten clean_all_csv'de silinmiş olmalı ama garanti olsun
    if not name:
        return "review"

    # bar/pub/club gibi şeyler varsa cafe main'e sokma
    if has_any(name, CAFE_OTHER_KEYS):
        return "other"

    # cafe/kahve sinyali varsa main
    if has_any(name, CAFE_MAIN_KEYS):
        return "main"

    # bazı isimler “pastane” gibi: cafe olabilir ama garanti değil -> review
    # (istersen sonra burayı main'e alırsın)
    fuzzy_like = ["pastane", "patisserie", "patiseri", "bakery", "fırın", "tatli", "tatlı", "dondurma", "gelato"]
    if has_any(name, fuzzy_like):
        return "review"

    return "review"

# =========================
# MAIN
# =========================
def main() -> None:
    if not INPUT_PATH.exists():
        raise FileNotFoundError(f"Cafe CSV bulunamadı: {INPUT_PATH}")

    df = pd.read_csv(INPUT_PATH)

    # beklenen kolonlar yoksa net hata verelim (proje standardı)
    if "name" not in df.columns:
        raise ValueError("CSV içinde 'name' kolonu yok. clean_all_csv sonrası kolonlar değişmiş olabilir.")

    # sınıflandır
    bucket = df.apply(decide_cafe, axis=1)
    main_df = df[bucket == "main"].copy()
    other_df = df[bucket == "other"].copy()
    review_df = df[bucket == "review"].copy()

    main_df.to_csv(OUT_MAIN, index=False)
    other_df.to_csv(OUT_OTHER, index=False)
    review_df.to_csv(OUT_REVIEW, index=False)

    print("\n--- Cafe Filter DONE ---")
    print("Input :", INPUT_PATH)
    print("Total :", len(df))
    print("Main  :", len(main_df), "->", OUT_MAIN)
    print("Other :", len(other_df), "->", OUT_OTHER)
    print("Review:", len(review_df), "->", OUT_REVIEW)

    if len(review_df) > 0:
        print("\nReview örnekleri (ilk 15):")
        print(review_df[["name"]].head(15).to_string(index=False))

    print("\nProcess finished.")

if __name__ == "__main__":
    main()
