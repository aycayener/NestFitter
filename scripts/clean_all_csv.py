from pathlib import Path
import re
import pandas as pd

BASE_DIR = Path(__file__).resolve().parents[1]   # proje kökü (Ev_Yasam_Oneri_Sistemi)
IN_DIR = BASE_DIR / "datasets"
OUT_DIR = BASE_DIR / "datasets" / "clean_csv"
OUT_DIR.mkdir(parents=True, exist_ok=True)

print("BASE_DIR:", BASE_DIR)
print("IN_DIR:", IN_DIR, "| exists:", IN_DIR.exists())
print("OUT_DIR:", OUT_DIR)

# -----------------------
# KATEGORİYE ÖZEL AYARLAR
# -----------------------

# Supermarket zincirleri (TR) - normalize edilmiş haliyle yakalanacak
CHAIN_MARKETS = [
    "migros", "carrefour", "carrefoursa", "a101", "bim", "sok", "şok",
    "macrocenter", "metro", "hakmar", "onur market", "file market"
]

# Health sınıflandırma (TR) - normalize edilmiş haliyle yakalanacak
HOSPITAL_POS = [
    "hastane", "şehir hastanesi", "egitim ve arastirma", "eğitim ve araştırma"
]
HOSPITAL_NEG = [
    "klinik", "poliklinik", "tip merkezi", "tıp merkezi",
    "dis", "diş", "dental", "agiz", "ağız", "muayenehane"
]

def normalize_text(s: str) -> str:
    """Basit TR normalize: küçük harf, TR karakter sadeleştirme, noktalama temizliği."""
    if pd.isna(s):
        return ""
    s = str(s).lower().strip()
    # TR karakterler
    s = (s.replace("ı", "i").replace("ş", "s").replace("ğ", "g")
           .replace("ü", "u").replace("ö", "o").replace("ç", "c"))
    # noktalama/özel karakterleri temizle
    s = re.sub(r"[^a-z0-9\s]", " ", s)
    s = re.sub(r"\s+", " ", s).strip()
    return s

def add_health_type(df: pd.DataFrame) -> pd.DataFrame:
    """Health dosyaları için health_type kolonunu ekler."""
    df = df.copy()
    df["name_norm"] = df["name"].apply(normalize_text)

    pos_norm = [normalize_text(x) for x in HOSPITAL_POS]
    neg_norm = [normalize_text(x) for x in HOSPITAL_NEG]

    def has_any(text: str, kws) -> bool:
        return any(k in text for k in kws)

    df["has_hospital_word"] = df["name_norm"].apply(lambda x: has_any(x, pos_norm))
    df["has_clinic_word"] = df["name_norm"].apply(lambda x: has_any(x, neg_norm))

    # Sınıflandırma mantığı:
    # - clinic_dental: name içinde klinik/diş/tıp merkezi vb. varsa
    # - hospital: "hastane" vb. varsa ve clinic_dental tetiklenmiyorsa
    # - other_health: ikisi de değilse
    def classify(row):
        if row["has_clinic_word"]:
            return "clinic_dental"
        if row["has_hospital_word"]:
            return "hospital"
        return "other_health"

    df["health_type"] = df.apply(classify, axis=1)

    # debug kolonlarını istersen tutabiliriz; paylaşım için temiz olsun diye siliyorum
    df = df.drop(columns=["name_norm", "has_hospital_word", "has_clinic_word"])
    return df

def add_market_type(df: pd.DataFrame) -> pd.DataFrame:
    """Supermarket dosyaları için market_type kolonunu ekler."""
    df = df.copy()
    df["name_norm"] = df["name"].apply(normalize_text)

    chain_norm = [normalize_text(x) for x in CHAIN_MARKETS]

    def is_chain(n: str) -> bool:
        return any(k in n for k in chain_norm)

    # Bazı kayıtlar market değil de AVM/Center gibi yer isimleri taşıyabiliyor
    def looks_like_mall(n: str) -> bool:
        return any(x in n for x in ["avm", "mall", "shopping", "center", "centre"])

    df["is_chain"] = df["name_norm"].apply(is_chain)
    df["looks_like_mall"] = df["name_norm"].apply(looks_like_mall)

    def classify(row):
        # AVM gibi görünenleri unknown yap (istersen tamamen ele de diyebiliriz)
        if row["looks_like_mall"]:
            return "unknown"
        if row["is_chain"]:
            return "chain"
        return "local"

    df["market_type"] = df.apply(classify, axis=1)

    df = df.drop(columns=["name_norm", "is_chain", "looks_like_mall"])
    return df

# -----------------------
# CLEAN ALL
# -----------------------
csv_files = list(IN_DIR.glob("*.csv"))
print("Toplam csv:", len(csv_files))

for path in csv_files:
    df = pd.read_csv(path)

    # name temizliği (string null'ları NA yap)
    if "name" in df.columns:
        df["name"] = df["name"].astype(str).str.strip()
        df["name"] = df["name"].replace(["<null>", "null", "None", "nan", ""], pd.NA)
        df = df.dropna(subset=["name"])   # genel temizlik: adı olmayanları sil
    else:
        # name kolonu yoksa bu dosya proje standardına uymuyor -> net hata
        raise ValueError(f"{path.name} dosyasında 'name' kolonu yok. Kolonlar: {list(df.columns)}")

    # koordinatları sayıya çevir, bozukları sil
    for c in ["latitude", "longitude"]:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors="coerce")
        else:
            raise ValueError(f"{path.name} dosyasında '{c}' kolonu yok. Kolonlar: {list(df.columns)}")

    df = df.dropna(subset=["latitude", "longitude"])

    # duplicate temizliği (aynı isim+koordinat)
    df = df.drop_duplicates(subset=["name", "latitude", "longitude"]).reset_index(drop=True)

    # -----------------------
    # KATEGORİYE ÖZEL ETİKETLEME
    # -----------------------
    stem = path.stem.lower()

    # Health/Hospital dosyaları
    if "hospital" in stem or "health" in stem:
        df = add_health_type(df)

    # Supermarket dosyaları
    if "supermarket" in stem:
        df = add_market_type(df)

    out_path = OUT_DIR / path.name
    df.to_csv(out_path, index=False, encoding="utf-8-sig")
    print("Saved:", out_path, "| rows:", len(df))

print("Bitti.")
