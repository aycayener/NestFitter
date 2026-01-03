# Amaç: "istanbul_schools.csv" içinden
# 1) devlet/resmi okul
# 2) özel okul/kolej
# 3) kurs/etüt/sanat (hobi okulları)
# 4) review (emin olmadıklarımız)
# şeklinde ayırmak.
#
# Not: Bu script "name" üzerinden gider. Tag'ler (amenity/shop vs.) varsa da kullanır.
# Çıktılar datasets/school_output/ içine yazılır.

from pathlib import Path
import re
import pandas as pd
import unicodedata

# =========================
# 1) AYARLAR
# =========================
BASE_DIR = Path(__file__).resolve().parents[1]

# Önce clean_csv'den okumak daha mantıklı
INPUT_PATH = BASE_DIR / "datasets" / "clean_csv" / "istanbul_schools.csv"

OUT_DIR = BASE_DIR / "datasets" / "school_output"
OUT_DIR.mkdir(parents=True, exist_ok=True)

OUT_PUBLIC = OUT_DIR / "schools_public.csv"
OUT_PRIVATE = OUT_DIR / "schools_private.csv"
OUT_COURSES = OUT_DIR / "schools_courses_hobby.csv"
OUT_REVIEW = OUT_DIR / "schools_review.csv"

# Eğer dosya adın farklıysa burayı değiştir:
# INPUT_PATH = BASE_DIR / "datasets" / "clean_csv" / "schools.csv"


# =========================
# 2) TEXT NORMALIZE
# =========================
def normalize_text(s: str) -> str:
    if s is None:
        return ""
    s = str(s).strip().lower()
    s = s.replace("’", "'").replace("`", "'")
    s = unicodedata.normalize("NFKD", s)
    s = "".join(ch for ch in s if not unicodedata.combining(ch))
    s = re.sub(r"[^a-z0-9ığüşöçıİĞÜŞÖÇ\s]", " ", s, flags=re.IGNORECASE)
    s = re.sub(r"\s+", " ", s).strip()
    return s


def has_any(text: str, keywords: list[str]) -> bool:
    return any(k in text for k in keywords)


# =========================
# 3) OKUL KURALLARI
# =========================
# Kurs/etüt/hobi (okul değil ama eğitim noktası)
COURSE_KEYS = [
    "etut", "etüt", "dershane", "kurs", "course",
    "dil okulu", "language", "akademi", "academy",
    "muzik", "müzik", "music", "konservatuvar",
    "resim", "sanat", "atolye", "atölye", "workshop",
    "bale", "dans", "spor okulu", "gymnasium",
    "surucu", "sürücü", "driving school",
    "cini", "çini"
]

# Özel okul/kolej göstergeleri
PRIVATE_KEYS = [
    "ozel", "özel", "kolej", "koleji", "college",
    "international", "ib", "bilfen", "bahcesehir", "bahçeşehir",
    "dogus", "doğuş", "final koleji", "mef", "ted",
    "enis", "mga", "sevk", "sevinç", "ugur", "uğur"
]

# Devlet/resmi okul göstergeleri (kesin değil ama güçlü ipucu)
PUBLIC_KEYS = [
    "ilkokulu", "ortaokulu", "lisesi",
    "anadolu lisesi", "mesleki ve teknik", "imam hatip",
    "fen lisesi", "sosyal bilimler lisesi",
    "halk egitim", "halk eğitim"
]

# Okul seviyesi anahtarları (devlet/özel fark etmeksizin okul olduğuna işaret)
SCHOOL_LEVEL_KEYS = [
    "anaokulu", "anasinifi", "ana sinifi", "kreş", "kres",
    "ilkokulu", "ortaokulu", "lisesi",
    "primary school", "middle school", "high school"
]


# =========================
# 4) SINIFLANDIRMA
# =========================
def classify_row(row: pd.Series) -> str:
    """
    return: 'public' | 'private' | 'courses' | 'review'
    """
    name_raw = row.get("name", "")
    name = normalize_text(name_raw)

    # Bazı dosyalarda name boş kalabiliyor
    if not name:
        return "review"

    # 1) Kurs/etüt/hobi - önce bunu ayırıyoruz (okul gibi görünse bile)
    # Çünkü "etüt merkezi", "dil okulu" vs. çocuk okulu değil.
    if has_any(name, COURSE_KEYS):
        return "courses"

    # 2) Tag varsa (bazı CSV'lerde amenity / school / education bilgisi geliyor)
    # Burada çok agresif davranmıyoruz, sadece yardımcı.
    amenity = normalize_text(row.get("amenity", ""))
    shop = normalize_text(row.get("shop", ""))
    leisure = normalize_text(row.get("leisure", ""))

    # Eğer "school" gibi bir tag net görünüyorsa, okul olduğu kesinleşir,
    # ama public/private ayrımı için yine name'e bakacağız.
    is_schoolish = False
    if "school" in amenity or "school" in name:
        is_schoolish = True
    if has_any(name, SCHOOL_LEVEL_KEYS) or has_any(name, PUBLIC_KEYS):
        is_schoolish = True
    if "university" in amenity or "college" in amenity:
        is_schoolish = True

    # 3) Özel okul
    if has_any(name, PRIVATE_KEYS):
        return "private"

    # 4) Devlet/resmi okul (isimde güçlü kalıplar)
    if has_any(name, PUBLIC_KEYS):
        return "public"

    # 5) Okul olduğunu anlıyoruz ama türü belirsizse review
    if is_schoolish:
        return "review"

    # 6) Hiçbir şeye uymuyorsa review
    return "review"


# =========================
# 5) MAIN
# =========================
def main():
    print("\n--- School Filter START ---")

    if not INPUT_PATH.exists():
        raise FileNotFoundError(
            f"School CSV bulunamadı: {INPUT_PATH}\n"
            f"Dosya adın farklıysa scripts/filter_schools_main.py içindeki INPUT_PATH'i güncelle."
        )

    print("Input:", INPUT_PATH)

    df = pd.read_csv(INPUT_PATH)
    print("Toplam kayıt:", len(df))
    print("Kolonlar:", list(df.columns))

    # name temizliği (clean_csv'den geliyor ama yine de garanti)
    if "name" in df.columns:
        df["name"] = df["name"].astype(str).str.strip()
        df["name"] = df["name"].replace(["<null>", "null", "None", "nan", ""], pd.NA)

    df = df.dropna(subset=["name"]).copy()

    # sınıflandır
    df["bucket"] = df.apply(classify_row, axis=1)

    public_df = df[df["bucket"] == "public"].drop(columns=["bucket"])
    private_df = df[df["bucket"] == "private"].drop(columns=["bucket"])
    courses_df = df[df["bucket"] == "courses"].drop(columns=["bucket"])
    review_df = df[df["bucket"] == "review"].drop(columns=["bucket"])

    # yaz
    public_df.to_csv(OUT_PUBLIC, index=False)
    private_df.to_csv(OUT_PRIVATE, index=False)
    courses_df.to_csv(OUT_COURSES, index=False)
    review_df.to_csv(OUT_REVIEW, index=False)

    print("\n--- School Filter DONE ---")
    print("Public:", len(public_df), "->", OUT_PUBLIC)
    print("Private:", len(private_df), "->", OUT_PRIVATE)
    print("Courses/Hobby:", len(courses_df), "->", OUT_COURSES)
    print("Review:", len(review_df), "->", OUT_REVIEW)

    # küçük kontrol: review'dan örnek gösterelim
    if len(review_df) > 0:
        print("\nReview örnekleri (ilk 15):")
        cols = ["name"]
        # name yoksa patlamasın
        cols = [c for c in cols if c in review_df.columns]
        print(review_df[cols].head(15).to_string(index=False))

    print("\nProcess finished.")


if __name__ == "__main__":
    main()
