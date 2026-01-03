from pathlib import Path
import pandas as pd

BASE_DIR = Path(__file__).resolve().parents[1]

# Park çıktın burada olmalı:
PARK_MAIN = BASE_DIR / "datasets" / "park_output" / "parks_main.csv"

# Eğer park_output yerine başka klasöre yazdıysan burayı değiştir:
# PARK_MAIN = BASE_DIR / "datasets" / "park_output" / "parks_main.csv"

if not PARK_MAIN.exists():
    raise FileNotFoundError(
        f"parks_main.csv bulunamadı: {PARK_MAIN}\n"
        "Önce filter_stations_main değil, park filtre scriptini çalıştırıp parks_main.csv üretmelisin."
    )

df = pd.read_csv(PARK_MAIN)
if "name" not in df.columns:
    raise ValueError(f"'name' kolonu yok. Kolonlar: {list(df.columns)}")

# --- 1) İsim bazlı hızlı kalite kontrol ---
keywords = [
    "çocuk park", "cocuk park",
    "oyun alan", "playground",
    "köpek park", "kopek park", "dog park",
    "fitness", "spor alan", "basket", "tenis",
    "halı saha", "hali saha", "futbol",
    "site", "rezidans", "apartman",
]

name_lower = df["name"].astype(str).str.lower()

print("\n=== PARK MAIN: İsim bazlı şüpheli/alt-tür taraması ===")
total = len(df)
print("Toplam parks_main satır:", total)

hits_total = 0
for k in keywords:
    cnt = name_lower.str.contains(k, na=False).sum()
    if cnt > 0:
        hits_total += cnt
        print(f"- '{k}' geçen kayıt: {cnt}")

print("\nNot:")
print("- Bu sayılar 'hata' demek değil; sadece parks_main içinde çocuk parkı/oyun alanı gibi alt türler var mı diye bakıyoruz.")
print("- Eğer bu sayı çok yüksekse: Park filtre kuralını sıkılaştırıp bu tipleri Other/Review'a atabiliriz.")

# --- 2) Tag kolonları varsa dağılımı yazdır ---
tag_cols = [c for c in ["leisure", "amenity", "landuse"] if c in df.columns]
if tag_cols:
    print("\n=== PARK MAIN: Tag dağılımları (varsa) ===")
    for col in tag_cols:
        print(f"\n[{col}] top 20:")
        print(df[col].astype(str).value_counts().head(20))
else:
    print("\n(Tag kolonları yok: sadece name/lat/lon ile gelmiş olabilir.)")

# --- 3) Birkaç örnek satır göster ---
print("\n=== Örnek ilk 25 park adı ===")
print(df["name"].head(25).to_string(index=False))
