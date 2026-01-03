# PROJE KİLİT PROMPT (DEĞİŞTİRME)

Sen bu projede "Ev Yaşam Öneri Sistemi (İstanbul)" için KOD üretiyorsun.
Amaç: var olan POI (Point of Interest) temiz veri setlerinden yola çıkarak,
kullanıcı profili simülasyonu + ağırlıklı skor + semt/lokasyon uygunluk skoru + harita görselleştirme üretmek.

## ZORUNLU KURALLAR
- Projeyi farklı bir şeye çevirmeye çalışma (ev fiyat tahmini, ilan scraping, sahibinden verisi vs. YOK).
- Kodlar "MiUUL stili" gibi okunabilir olsun: kısa fonksiyonlar, net değişken isimleri, yorumlar kısa-öz.
- "AI gibi" uzun açıklama yazma. Yorumlar 1 satır, gerektiği kadar.
- Python: pandas + numpy + geopandas + shapely + folium (gerekirse) kullan.
- Path kullan: BASE_DIR = Path(__file__).resolve().parents[1]
- Girdi dizini: datasets/*_output/ (main dosyaları) ve outputs/
- Çıktıları yeni klasörlere yaz:
  - outputs/scoring/
  - outputs/maps/
  - outputs/profiles/
- Çıktılar hem CSV hem (mümkünse) GeoJSON olsun.

## GİRDİ DOSYALARI (varsayılan)
- hospitals: datasets/hospital_output/hospitals_main.csv
- supermarkets: datasets/supermarket_output/supermarkets_main.csv
- schools: datasets/school_output/schools_public.csv (+ courses/hobby opsiyon)
- parks: datasets/park_output/parks_main.csv
- stations: datasets/station_output/stations_main.csv
- malls: outputs/avm_clean.csv (referans AVM)
- bars/cafes/gyms/sports/parking: kendi *_output klasörlerindeki main dosyaları

## GENEL ÇIKTI FORMATLARI
- Her skor tablosunda şu kolonlar olsun:
  - target_id (semt veya nokta id)
  - name (varsa)
  - latitude, longitude
  - score_total
  - score_breakdown (json string gibi olabilir)
- Her script çalışınca konsola özet yazsın: input sayısı, output sayısı, örnek 10 satır.

## ÖNEMLİ
- Eğer semt sınırı (shapefile/geojson) yoksa: semt yerine "grid hücre" yaklaşımı kullan.
  (Örn. İstanbul’u 1km x 1km grid’e böl, her grid için skor üret.)
- Eksik dosya olursa: net hata ver, ama nerede beklediğini yaz.

Şimdi aşağıdaki görev promptuna göre tek bir .py dosyası üret.


## GÖREV: Kullanıcı Profil Simülasyonu (scripts/generate_user_profiles.py)

Amaç:
- 6–8 adet "persona" üret ve outputs/profiles/user_profiles.json olarak kaydet.
- Persona'lar sabit olsun (random değil), herkes aynı profilleri görsün.

ZORUNLU PROFİLLER (en az):
1) Öğrenci (üniversite/çalışan öğrenci)
2) Çocuklu Aile (ilkokul çocuğu)
3) Yaşlı Çift
4) Spor Odaklı Bekar (spor merkezi/fitness yakınlığı önemser)
5) Sosyal Hayat Odaklı Genç (cafe/bar yakınlığı sever)
6) Sessizlik Arayan (bar/cafe uzak olsun, park yakın olsun)

Her profil şu alanları içersin:
- profile_id
- profile_name
- description (1-2 cümle)
- weights (kategori ağırlıkları, -2 ile +5 arası)
- radius_m (mesafe metriği için varsayılan yarıçap, örn 500m/1000m)
- must_have (opsiyonel: ["school_public", "hospital_main"] gibi)
- avoid (opsiyonel: ["bars_main"] gibi)

Kategori anahtarları şu isimlerle olsun:
- hospital_main
- supermarket_main
- school_public
- school_private
- school_courses
- park_main
- station_main
- mall_main
- gym_main
- sports_centre_main
- parking_main
- cafe_main
- bar_main

Çıktı:
- outputs/profiles/user_profiles.json

Konsol çıktısı:
- kaç profil yazıldı + profil isimlerini listele.

Not:
- Kod kısa olsun, json dump ile yaz.




## GÖREV: Ağırlıklı Çevre Skoru Motoru (scripts/score_locations_grid.py)

Amaç:
- İstanbul genelinde "grid hücre" üret (semt geojson yoksa zorunlu).
- Her hücre merkez noktası için: belirli yarıçap içinde POI sayıları -> ağırlıklarla skor -> toplam skor.

Grid:
- bbox'ı POI verilerinden çıkar (min/max lat/lon).
- cell_size_m = 1000 (1km) default.
- Grid hücre merkezlerini üret.

Mesafe hesabı:
- Haversine fonksiyonu yaz (numpy ile).
- Her grid noktası için her kategori POI sayısını hesapla (radius_m: profilden gelecek).
- Performans: çok optimize etmeye çalışma ama makul yaz (chunk mantığı opsiyonel).

Girdiler:
- outputs/profiles/user_profiles.json
- datasets/*_output/ içindeki main csv'ler
- outputs/avm_clean.csv

Çıktılar:
- outputs/scoring/grid_scores_<profile_id>.csv
Kolonlar:
- grid_id
- latitude
- longitude
- score_total
- poi_counts_json (json string)
- score_breakdown_json (json string)

Konsol:
- grid sayısı, her profil için top 10 grid (score_total en yüksek).

Not:
- Bu script "tek komutla" tüm profiller için skor üretsin.



## GÖREV: Lokasyon Önerisi Listesi (scripts/recommend_top_locations.py)

Amaç:
- Grid skorlarından her profil için "Top N lokasyon" listesi üret.
- N default 20 olsun.
- Hem CSV hem GeoJSON export olsun.

Girdiler:
- outputs/scoring/grid_scores_<profile_id>.csv (her profil için)

Çıktılar:
- outputs/scoring/recommendations_<profile_id>.csv
- outputs/scoring/recommendations_<profile_id>.geojson

CSV kolonları:
- rank
- grid_id
- latitude
- longitude
- score_total
- poi_counts_json
- score_breakdown_json

GeoJSON:
- Point geometry (lon, lat)
- properties: rank, score_total, profile_id

Konsol:
- her profil için ilk 5 lokasyonu bas (rank + score_total).



## GÖREV: Harita Görselleştirme (scripts/make_maps.py)

Amaç:
- Her profil için interaktif HTML harita üret (folium).
- Haritada:
  - Top 20 lokasyon marker (renk skalası şart değil, default olur)
  - İsteğe bağlı: hospital_main, school_public, park_main gibi 3-4 önemli kategori layer olarak gösterilsin.
- Bar/cafe gibi negatif olabilecek kategoriler haritada opsiyonel layer olarak kalsın (default kapalı).

Girdiler:
- outputs/scoring/recommendations_<profile_id>.geojson
- POI main csv'ler (hospital_main, school_public, park_main, station_main, mall_main)

Çıktılar:
- outputs/maps/map_<profile_id>.html

Konsol:
- kaç marker eklendi, hangi layerlar eklendi.

Not:
- Harita merkezini: top 1 lokasyona göre ayarla.
- Zoom: 12 default.


> Not: Bazı kategoriler kullanıcı profiline göre negatif ağırlık alabilir.
> Örn: Yaşlı birey profili için bar/cafe yakınlığı eksi puan; park ve hastane artı puan.
