from pathlib import Path
import pandas as pd
import re
import unicodedata

# =========================
# AYARLAR
# =========================
BASE_DIR = Path(__file__).resolve().parents[1]

INPUT_PATH = BASE_DIR / "datasets" / "clean_csv" / "istanbul_bars.csv"

OUT_DIR = BASE_DIR / "datasets" / "bar_output"
OUT_DIR.mkdir(parents=True, exist_ok=True)

OUT_MAIN = OUT_DIR / "bars_main.csv"
OUT_OTHER = OUT_DIR / "bars_other.csv"
OUT_REVIEW = OUT_DIR / "bars_review.csv"

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
# Bar MAIN = bar/pub/nightlife içeriği bariz olanlar
BAR_MAIN_KEYS = [
    "bar", "pub", "beer", "bira", "taproom", "tapas",
    "cocktail", "kokteyl", "whisky", "wine", "şarap", "sarap",
    "meyhane", "taverna", "rakı", "raki",
    "night", "club", "gece", "lounge"
]

# Bar datasında karışan şeyler (OTHER)
BAR_OTHER_KEYS = [
    "cafe", "kafe", "coffee", "kahve",
    "restaurant", "restoran", "lokanta", "ocakbasi", "ocakbaşı",
    "pide", "lahmacun", "kebap", "doner", "döner",
    "hotel", "otel", "hostel",
    "market", "bakkal", "supermarket", "süpermarket",
    "avm", "mall"
]

def decide_bar(row: pd.Series) -> str:
    name = norm(row.get("name", ""))

    if not name:
        return "review"

    # açıkça cafe/restoran/otel/market gibi sinyal varsa bar main'e sokma
    if has_any(name, BAR_OTHER_KEYS):
        return "other"

    # bar/pub/club vs sinyal varsa main
    if has_any(name, BAR_MAIN_KEYS):
        return "main"

    # net değil -> review
    return "review"

# =========================
# MAIN
# =========================
def main() -> None:
    if not INPUT_PATH.exists():
        raise FileNotFoundError(f"Bar CSV bulunamadı: {INPUT_PATH}")

    df = pd.read_csv(INPUT_PATH)
    if "name" not in df.columns:
        raise ValueError("CSV içinde 'name' kolonu yok. clean_all_csv sonrası kolonlar değişmiş olabilir.")

    bucket = df.apply(decide_bar, axis=1)
    main_df = df[bucket == "main"].copy()
    other_df = df[bucket == "other"].copy()
    review_df = df[bucket == "review"].copy()

    main_df.to_csv(OUT_MAIN, index=False)
    other_df.to_csv(OUT_OTHER, index=False)
    review_df.to_csv(OUT_REVIEW, index=False)

    print("\n--- Bar Filter DONE ---")
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
