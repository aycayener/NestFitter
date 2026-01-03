## Kullanıcı Profili Simülasyonları (Ağırlık Tabloları)

Bu aşamada 5-6 farklı kullanıcı profili tanımlanır.
Her profil için çevresel faktörlere (POI) net ağırlıklar verilir.

Ağırlık ölçeği:
- **+5**: Çok önemli (olmazsa olmaz)
- **+3**: Önemli
- **+1**: İyi olur
- **0**: Nötr / önemsiz
- **-1**: Tercih etmiyor
- **-2**: Kaçınır (negatif etki)

> Not: Negatif ağırlıklar “yakın olmasını istemiyor” anlamına gelir (ör: yaşlı birey için bar).

---

### Profil 1 — Öğrenci (Üniversite)
Amaç: Ulaşım + kafe + günlük ihtiyaçlar.

| Kategori | Ağırlık |
|---|---:|
| Stations (metro/metrobüs vb.) | +5 |
| Cafes | +3 |
| Supermarkets (Main) | +3 |
| Parks | +1 |
| Gyms / Sports Centres | +1 |
| Hospitals (Main) | +1 |
| Malls (AVM) | 0 |
| Bars | 0 / -1 (kişiye göre) |

---

### Profil 2 — Çocuklu Aile (İlkokul/Ortaokul)
Amaç: Okul + park + hastane + günlük ihtiyaç.

| Kategori | Ağırlık |
|---|---:|
| Schools (Public) | +5 |
| Parks | +5 |
| Hospitals (Main) | +3 |
| Supermarkets (Main) | +3 |
| Parkings | +1 |
| Malls (AVM) | +1 |
| Stations | +1 |
| Bars | -2 |

---

### Profil 3 — Yaşlı Çift
Amaç: Hastane + sakinlik + temel ihtiyaç.

| Kategori | Ağırlık |
|---|---:|
| Hospitals (Main) | +5 |
| Parks | +3 |
| Supermarkets (Main) | +3 |
| Stations | +1 |
| Parkings | +1 |
| Malls (AVM) | 0 |
| Bars | -2 |

---

### Profil 4 — Beyaz Yaka (Yoğun Çalışan)
Amaç: Ulaşım + market + hızlı yaşam.

| Kategori | Ağırlık |
|---|---:|
| Stations | +5 |
| Supermarkets (Main) | +3 |
| Cafes | +1 |
| Parkings | +1 |
| Gyms / Sports Centres | +1 |
| Hospitals (Main) | 0 |
| Bars | 0 |
| Parks | 0 |

---

### Profil 5 — Spor Odaklı (Hobi: Fitness/Yüzme/Halı saha)
Amaç: spor tesisleri + gym.

| Kategori | Ağırlık |
|---|---:|
| Gyms | +5 |
| Sports Centres | +5 |
| Parks | +1 |
| Supermarkets (Main) | +1 |
| Stations | +1 |
| Cafes | 0 |
| Bars | 0 |

---

## Skor Mantığı (Sonraki Adım)
Her lokasyon/mahalle için:
- Her POI kategorisinde bir “yakınlık” veya “yoğunluk” skoru çıkarılır.
- Profil ağırlıkları ile çarpılarak toplam yaşam uygunluk skoru hesaplanır.

Örnek:
ToplamSkor = Σ (KategoriSkoru * ProfilAğırlığı)


## Skor Mantığı (Nasıl Çalışır?)

Bu aşamada elimizde ev ilanı/ev koordinatı olmadığı için **ev önermek yerine lokasyon/semt uygunluğu** skorlanır.
Mantık: “Bu bölgede yaşamak, şu profile ne kadar uygun?”

Genel formül:
**ToplamSkor = Σ (KategoriSkoru × ProfilAğırlığı)**

- **KategoriSkoru:** o bölgede ilgili POI’nin ne kadar iyi seviyede olduğunu gösteren sayı
- **ProfilAğırlığı:** ( +5, +3, +1, 0, -1, -2 ) tablosundan gelen değer

---

## KategoriSkoru Nasıl Üretilecek? (3 Seçenek)

Aynı projede hepsi yapılabilir ama en pratik olanı 1 veya 2.

### Seçenek 1 — Yoğunluk (Count) Skoru
Her semt/mahalle içinde POI sayısı alınır.

Örnek:
- `stations_count`, `parks_count`, `schools_public_count`…

Sonra normalize edilir:
- Min–Max:  
  `norm = (x - min) / (max - min)`  → 0 ile 1 arası

✅ Artı: çok hızlı, veri yoksa bile çalışır  
⚠️ Eksi: semt alanı büyükse sayılar şişebilir (istersen “alan başına yoğunluk” eklenir)

---

### Seçenek 2 — Yakınlık (Mesafe) Skoru (Lokasyon noktası seçerek)
Ev koordinatı yoksa bile, her semt için bir temsil nokta seçebiliriz:
- semt merkez koordinatı (centroid) veya
- “örnek lokasyon noktası” (manual 5-10 nokta)

Sonra “en yakın POI mesafesi” hesaplanır:
- `min_distance_km`

Mesafeyi skora çevirme örneği (basit):
- 0–0.5 km → 1.0
- 0.5–1 km → 0.8
- 1–2 km → 0.5
- 2–3 km → 0.2
- 3+ km → 0.0

✅ Artı: “yakın mı?” sorusuna net cevap  
⚠️ Eksi: semt polygon/centroid bilgisi gerekir (ya da manuel nokta)

---

### Seçenek 3 — Karma Skor (Tavsiye Edilen)
Hem sayıyı hem mesafeyi kullan:
- `KategoriSkoru = 0.6 * yoğunluk_norm + 0.4 * yakınlık_norm`

✅ Artı: daha dengeli sonuçlar

---

## Negatif Ağırlıklar Nasıl Uygulanacak?

Negatif ağırlık = “yakın olmasını istemiyor” demek.

Örnek: yaşlı profilinde Bars = -2  
- Eğer bar yoğunluğu yüksekse veya bar çok yakınsa → toplam skor düşer.

Basit uygulama:
- BarKategoriSkoru 0–1 arası çıkacak
- ToplamSkor’a `(-2 × BarKategoriSkoru)` eklenecek

---

## Review Dosyaları Ne Olacak?

Bazı kategorilerde (supermarkets_review, hospitals_review vb.) kararsız kayıtları ayırdık.
Kullanım kuralı:

- **Main:** skorlamaya direkt girer
- **Other:** genelde dışarıda kalır (isteğe bağlı)
- **Review:** 2 yöntem:
  1) Şimdilik dışarıda tut (en temiz yaklaşım)
  2) “opsiyonel” kategori gibi ekle (profil isterse devreye sok)

Not:
Review dosyalarını projede “manuel kontrol kuyruğu” gibi düşün.
Jüriye de bu yaklaşım daha temiz görünür.

---

## Çıktı / Sunum (Harita + Liste)

Bu aşamadan sonra hedef çıktı:
- Her semt için:
  - ToplamSkor (profil bazlı)
  - En güçlü 3 kategori (neden o semt?)
- Harita üstünde:
  - Semtler renk skalası (yüksek skor = daha koyu)
  - İstersek POI katmanları aç/kapa

---

## Dipnot (Profil Mantığı)
Bazı kategoriler “herkes için iyi” değildir:
- Örn: **Bars** bazı profiller için negatif olabilir.
Bu yüzden profil ağırlıkları zorunlu ve “tek skor herkese uymaz”.
