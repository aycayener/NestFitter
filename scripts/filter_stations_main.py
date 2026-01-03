from pathlib import Path
import pandas as pd
import re
import unicodedata


# =========================
# AYARLAR
# =========================
BASE_DIR = Path(__file__).resolve().parents[1]
INPUT_PATH = BASE_DIR / "datasets" / "clean_csv" / "istanbul_stations.csv"

OUT_DIR = BASE_DIR / "datasets" / "station_output"
OUT_DIR.mkdir(parents=True, exist_ok=True)

OUT_MAIN = OUT_DIR / "stations_main.csv"
OUT_OTHER = OUT_DIR / "stations_other.csv"
OUT_REVIEW = OUT_DIR / "stations_review.csv"


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


def main():
    print("\n--- Station Filter START ---")
    print("Input:", INPUT_PATH)

    if not INPUT_PATH.exists():
        raise FileNotFoundError(f"Stations CSV bulunamadı: {INPUT_PATH}")

    df = pd.read_csv(INPUT_PATH)
    print("Toplam kayıt:", len(df))
    print("Kolonlar:", list(df.columns))

    if not {"name", "latitude", "longitude"}.issubset(df.columns):
        raise ValueError("Beklenen kolonlar yok. name/latitude/longitude olmalı.")

    df["name_norm"] = df["name"].apply(norm_text)

    railway = df["railway"].astype(str).str.lower() if "railway" in df.columns else pd.Series([""] * len(df))
    pt = df["public_transport"].astype(str).str.lower() if "public_transport" in df.columns else pd.Series([""] * len(df))
    amenity = df["amenity"].astype(str).str.lower() if "amenity" in df.columns else pd.Series([""] * len(df))

    bad_names = {"", "nan", "none", "<null>", "null"}

    # Main sinyaller (ana ulaşım)
    main_railway = {"station", "tram_stop", "halt", "subway_entrance"}
    main_pt = {"station", "platform"}
    main_amenity = {"ferry_terminal", "bus_station"}

    main_name_keywords = [
        "metro", "marmaray", "istasyonu", "tren", "tramvay", "metrobüs", "metrobüs",
        "iskele", "vapur", "terminal", "otogar", "gar"
    ]

    # Other sinyaller (küçük duraklar)
    other_name_keywords = [
        "dolmus", "minibus", "taksi duragi", "taksi", "otobus duragi", "durak"
    ]

    def classify(row) -> str:
        n = row["name_norm"]
        r = str(row.get("railway", "")).lower()
        p = str(row.get("public_transport", "")).lower()
        a = str(row.get("amenity", "")).lower()

        if n in bad_names:
            return "review"

        # Other: açık durak/dolmuş/taksi
        if any(k in n for k in other_name_keywords):
            return "other"

        # Main: tag ile yakala
        if r in main_railway:
            return "main"
        if p in main_pt:
            return "main"
        if a in main_amenity:
            return "main"

        # Main: isimden yakala
        if any(k in n for k in main_name_keywords):
            return "main"

        return "review"

    df["bucket"] = df.apply(classify, axis=1)

    main_df = df[df["bucket"] == "main"].drop(columns=["name_norm", "bucket"], errors="ignore")
    other_df = df[df["bucket"] == "other"].drop(columns=["name_norm", "bucket"], errors="ignore")
    review_df = df[df["bucket"] == "review"].drop(columns=["name_norm", "bucket"], errors="ignore")

    main_df.to_csv(OUT_MAIN, index=False)
    other_df.to_csv(OUT_OTHER, index=False)
    review_df.to_csv(OUT_REVIEW, index=False)

    print("\n--- Station Filter DONE ---")
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
