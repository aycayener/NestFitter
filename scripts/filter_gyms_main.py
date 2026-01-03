from pathlib import Path
import pandas as pd
import re
import unicodedata

# =========================
# AYARLAR
# =========================
BASE_DIR = Path(__file__).resolve().parents[1]

# clean_csv içinden oku
INPUT_PATH = BASE_DIR / "datasets" / "clean_csv" / "istanbul_gyms.csv"

OUT_DIR = BASE_DIR / "datasets" / "gym_output"
OUT_DIR.mkdir(parents=True, exist_ok=True)

OUT_MAIN = OUT_DIR / "gyms_main.csv"
OUT_OTHER = OUT_DIR / "gyms_other.csv"
OUT_REVIEW = OUT_DIR / "gyms_review.csv"

# =========================
# YARDIMCI
# =========================
def norm_text(s: str) -> str:
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
# KURALLAR (isim bazlı)
# =========================
# Main: spor salonu / fitness / gym / pilates vb.
MAIN_KEYS = [
    "gym", "fitness", "fitnes", "spor salon", "spor merkezi", "spor merkezi̇",
    "body", "crossfit", "pilates", "reformer", "yoga", "kick boks", "kickboks",
    "boks", "boxing", "mma", "martial", "judo", "taekwondo", "karate",
    "studio", "stüdyo", "antrenman", "workout",
    # zincir/marka örnekleri (isimler çok geçiyor olabilir)
    "macfit", "mac fit", "biggym", "big gym", "hillside", "sports international",
    "fit in time", "fittime", "fit time"
]

# Other: aslında gym değil gibi duranlar (aşırı riskli olanlar)
# (Bunları direkt silmiyoruz, ayrı dosyaya alıyoruz.)
OTHER_KEYS = [
    "halisaha", "halı saha", "futbol sah", "tenis", "basket", "voleybol",
    "yuzme", "yüzme", "havuz", "olimpik", "stad", "stadyum",
    "club", "kulup", "kulüb", "dernek", "vakfi", "vakfı",
    "hotel", "otel", "resort", "spa", "hamam", "masaj",
    "avm", "mall"
]

# Review: net değilse burada kalsın (sonradan bakılacak)

# =========================
# MAIN
# =========================
def main() -> None:
    print("\n--- Gym Filter START ---")
    print("Input:", INPUT_PATH)

    if not INPUT_PATH.exists():
        raise FileNotFoundError(
            f"Gym CSV bulunamadı: {INPUT_PATH}\n"
            f"Dosya adını kontrol et: datasets/clean_csv/istanbul_gyms.csv"
        )

    df = pd.read_csv(INPUT_PATH)
    print("Toplam kayıt:", len(df))
    print("Kolonlar:", list(df.columns))

    if "name" not in df.columns:
        raise ValueError("CSV içinde 'name' kolonu yok. Clean_all çıktını kontrol et.")

    df["_name_norm"] = df["name"].apply(norm_text)

    # 1) MAIN adayları
    is_main = df["_name_norm"].apply(lambda x: has_any(x, MAIN_KEYS))

    # 2) OTHER adayları (main olanların içinde bile geçebilir; önce main seçiyoruz, sonra other'ı ayrı kontrol ediyoruz)
    is_other = df["_name_norm"].apply(lambda x: has_any(x, OTHER_KEYS))

    # Kural:
    # - MAIN: main_keys var VE other_keys yok
    # - OTHER: other_keys var VE main_keys yok (ya da bariz başka şey)
    # - REVIEW: geri kalan (belirsiz)
    main_df = df[is_main & (~is_other)].copy()
    other_df = df[(~is_main) & (is_other)].copy()
    review_df = df.drop(main_df.index).drop(other_df.index).copy()

    # temiz kolon
    for d in (main_df, other_df, review_df):
        d.drop(columns=["_name_norm"], inplace=True, errors="ignore")

    main_df.to_csv(OUT_MAIN, index=False)
    other_df.to_csv(OUT_OTHER, index=False)
    review_df.to_csv(OUT_REVIEW, index=False)

    print("\n--- Gym Filter DONE ---")
    print("Main:", len(main_df), "->", OUT_MAIN)
    print("Other:", len(other_df), "->", OUT_OTHER)
    print("Review:", len(review_df), "->", OUT_REVIEW)

    if len(review_df) > 0:
        sample = review_df[["name"]].head(15)
        print("\nReview örnekleri (ilk 15):")
        print(sample.to_string(index=False))

    print("\nProcess finished.")

if __name__ == "__main__":
    main()
