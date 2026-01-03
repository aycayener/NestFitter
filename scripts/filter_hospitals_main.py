from pathlib import Path
import pandas as pd
import unicodedata

# =========================
# 1) Ayarlar (burayı sen de rahatça değiştirebilirsin)
# =========================
BASE_DIR = Path(__file__).resolve().parents[1]

# Önce clean_csv'ten oku (genelde doğru yer)
INPUT_PATH = BASE_DIR / "datasets" / "clean_csv" / "istanbul_hospitals.csv"


OUT_DIR = BASE_DIR / "datasets" / "hospital_output"
OUT_DIR.mkdir(parents=True, exist_ok=True)

# “Ana hastane” tarafına almak istediğimiz kelimeler (pozitif sinyal)
HOSPITAL_KEEP = [
    "hastane", "hastanesi",
    "devlet hastanesi",
    "egitim ve arastirma", "eğitim ve araştırma",
    "universite hastanesi", "üniversite hastanesi",
    "sehir hastanesi", "şehir hastanesi",
    "tip fakultesi", "tıp fakültesi",
    "ozel hastane", "özel hastane",
]

# Klinik / merkez / poliklinik gibi “hastane değil” tarafına atacağımız kelimeler
CLINIC_DROP = [
    "klinik", "poliklinik", "muayenehane",
    "tip merkezi", "tıp merkezi",
    "saglik merkezi", "sağlık merkezi",
    "dispanser",
]

# Diş / ağız gibi ayrı sınıf yapmak istersen (şimdilik “other”a gidecek)
DENTAL_DROP = [
    "dis", "diş", "agiz", "ağız",
    "dental", "dent", "ortodonti", "implant",
]

# =========================
# 2) Küçük yardımcı: metin normalizasyonu
#    (eşleşmeler daha temiz olsun diye)
# =========================
def norm_text(s: str) -> str:
    """
    - küçük harf
    - Türkçe karakterleri sadeleştirir (ş->s, ğ->g vb.)
    - fazla boşlukları düzeltir
    """
    if pd.isna(s):
        return ""
    s = str(s).strip().lower()
    s = unicodedata.normalize("NFKD", s)
    s = "".join(ch for ch in s if not unicodedata.combining(ch))
    s = " ".join(s.split())
    return s

# =========================
# 3) CSV oku (encoding sorunlarına karşı küçük önlem)
# =========================
if not INPUT_PATH.exists():
    raise FileNotFoundError(
        f"Hospital CSV bulunamadı: {INPUT_PATH}\n"
        "Dosya adın farklıysa scripts/filter_hospitals.py içindeki INPUT_PATH'i güncelle."
    )

try:
    df = pd.read_csv(INPUT_PATH)
except UnicodeDecodeError:
    # Bazı dosyalarda bu lazım olabiliyor
    df = pd.read_csv(INPUT_PATH, encoding="utf-8-sig")

# =========================
# 4) Temel kolon kontrol + temel temizlik
# =========================
if "name" not in df.columns:
    raise ValueError(f"'name' kolonu yok. Kolonlar: {list(df.columns)}")

# name temizliği
df["name"] = df["name"].astype(str).str.strip()
df["name"] = df["name"].replace(["<null>", "null", "None", "nan", ""], pd.NA)
df = df.dropna(subset=["name"]).copy()

# koordinatlar varsa sayıya çevir, bozukları sil
for c in ["latitude", "longitude"]:
    if c in df.columns:
        df[c] = pd.to_numeric(df[c], errors="coerce")
if {"latitude", "longitude"}.issubset(df.columns):
    df = df.dropna(subset=["latitude", "longitude"]).copy()

# normalize isim
df["name_norm"] = df["name"].apply(norm_text)

# =========================
# 5) MIUUL-stili kural tabanlı sınıflandırma
#
# Mantık:
# - Diş/klinik kelimeleri varsa -> other (hastane değil)
# - Hastane kelimesi/ifadeleri varsa -> main_hospital
# - İkisi birden varsa -> review (karışık örnekler)
# - Hiçbiri yoksa -> review
# =========================
name_series = df["name_norm"]

has_keep = pd.Series(False, index=df.index)
for kw in HOSPITAL_KEEP:
    has_keep = has_keep | name_series.str.contains(norm_text(kw), na=False)

has_clinic = pd.Series(False, index=df.index)
for kw in CLINIC_DROP:
    has_clinic = has_clinic | name_series.str.contains(norm_text(kw), na=False)

has_dental = pd.Series(False, index=df.index)
for kw in DENTAL_DROP:
    has_dental = has_dental | name_series.str.contains(norm_text(kw), na=False)

# review: hem hastane hem klinik/diş gibi çakışanlar
is_review = has_keep & (has_clinic | has_dental)

# main: hastane sinyali var, ama klinik/diş sinyali yok
is_main = has_keep & ~(has_clinic | has_dental)

# other: klinik/diş sinyali var, ama hastane sinyali yok
is_other = (has_clinic | has_dental) & ~has_keep

# kalanlar: hiçbir şeye girmeyen -> review
is_review = is_review | ~(is_main | is_other)

df_main = df[is_main].copy()
df_other = df[is_other].copy()
df_review = df[is_review].copy()

# name_norm’u istersen bırakabilirsin; ben çıktılarda da kalsın dedim.
# İstemiyorsan şu satırlarla kaldır:
# df_main = df_main.drop(columns=["name_norm"])
# df_other = df_other.drop(columns=["name_norm"])
# df_review = df_review.drop(columns=["name_norm"])

# =========================
# 6) Kaydet + kısa rapor
# =========================
out_main = OUT_DIR / "hospitals_main.csv"
out_other = OUT_DIR / "hospitals_other.csv"
out_review = OUT_DIR / "hospitals_review.csv"

df_main.to_csv(out_main, index=False)
df_other.to_csv(out_other, index=False)
df_review.to_csv(out_review, index=False)

print("\n--- Hospital Filter DONE ---")
print("Input :", INPUT_PATH)
print("Total :", len(df))
print("Main  :", len(df_main), "->", out_main)
print("Other :", len(df_other), "->", out_other)
print("Review:", len(df_review), "->", out_review)

# İstersen review'den ilk 15 satırı gör:
print("\nReview örnekleri (ilk 15):")
print(df_review[["name"]].head(15).to_string(index=False))
