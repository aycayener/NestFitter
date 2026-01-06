# Live Demo
https://nestfitter-ccbpmdapr5bewiqcp23hxx.streamlit.app/

# Ev Yaşam Öneri Sistemi (İstanbul)

Ev seçimi sürecinde yalnızca konutun fiziksel özellikleri değil,
bulunduğu çevrenin sunduğu yaşam olanakları da kritik rol oynar.
Okul, hastane, park, toplu taşıma ve alışveriş merkezleri gibi noktalar,
bir evin günlük yaşam açısından ne kadar uygun olduğunu belirler.

Bu proje, İstanbul genelinde farklı yaşam alanlarına ait mekânsal verileri
toplayarak, konut çevresindeki yaşam olanaklarını karşılaştırılabilir
ve analiz edilebilir hale getiren konum bazlı bir veri altyapısı sunar.

Odak noktası, doğrudan ev ilanı önermekten ziyade,
ev seçiminin temelini oluşturan **lokasyon ve çevresel uygunluğu**
veri temelli olarak değerlendirmektir.

---

## Proje Amacı
Bu projenin temel amacı, ev arama sürecinde kullanıcıların yalnızca
evin fiziksel özelliklerine değil, bulunduğu çevrenin yaşam koşullarına da
daha bilinçli şekilde karar verebilmesini sağlamaktır.

Bu doğrultuda proje:

- Kullanıcının yaşam tarzı ve günlük ihtiyaçlarıyla
  yaşadığı çevre arasındaki ilişkiyi görünür hale getirmeyi  
- İstanbul’daki farklı lokasyonların,
  sundukları yaşam olanakları açısından karşılaştırılabilmesini  
- Ev seçimi sürecinde genellikle sezgisel yapılan
  “bu çevre bana uygun mu?” değerlendirmesini
  veri temelli bir yaklaşımla desteklemeyi  
- Kişiselleştirilmiş ev yaşam öneri sistemlerine
  altyapı oluşturacak mekânsal bir çerçeve sunmayı  
amaçlamaktadır.
---

## Kullanılan Veri Kaynakları

### 1. OpenStreetMap / Overpass API

İstanbul’daki mekanlara ait koordinat ve etiket bilgileri,
OpenStreetMap verileri kullanılarak **Overpass API** üzerinden elde edilmiştir.

Kullanılan başlıca POI (Point of Interest) kategorileri:

- Bars  
- Cafes  
- Convenience Stores  
- Gyms  
- Hospitals  
- Malls  
- Mosques  
- Parkings  
- Parks  
- Schools  
- Sports Centres  
- Stations  
- Supermarkets  
- Theatres  

Bu veriler, proje kapsamında **ham veri (data_raw)** olarak saklanmıştır.

---

### 2. Wikipedia (AVM Doğrulama Kaynağı)

İstanbul’daki alışveriş merkezlerinin resmi ve yaygın olarak kabul edilen isim listesi,
Türkçe Wikipedia sayfası referans alınarak kullanılmıştır.

Bu liste, POI havuzunda “AVM” etiketiyle gelen kayıtların
**isim bazlı doğrulanması ve yanlış etiketlerin ayıklanması** amacıyla kullanılmıştır.

---

## Nasıl Çalışır? (Özet Akış)

1. İstanbul’daki POI verileri Overpass API üzerinden çekilir  
2. Tüm kategoriler için genel veri temizliği uygulanır  
3. AVM kategorisi Wikipedia referansı ile doğrulanır  
4. Temiz ve tutarlı POI veri setleri oluşturulur  
5. Bu veri setleri, lokasyon bazlı analiz ve skorlamaya hazır hale getirilir  

---

## Klasör Yapısı

Ev_Yasam_Oneri_Sistemi/
│
├── data_raw/ # Overpass API’den çekilen ham veriler
│
├── datasets/
│ ├── archive/ # Temizleme öncesi ara CSV’ler (referans amaçlı)
│ ├── clean_csv/ # Genel temizlikten geçmiş ana veri setleri
│ └── avm_output/ # Wikipedia ile doğrulanmış AVM çıktıları
│
├── outputs/ # Final çıktı dosyaları (CSV / GeoJSON)
│
├── scripts/ # Tüm veri işleme ve pipeline scriptleri
│
└── README.mdEv_Yasam_Oneri_Sistemi/
│
├── data_raw/ # Overpass API’den çekilen ham veriler
│
├── datasets/
│ ├── archive/ # Temizleme öncesi ara CSV’ler (referans amaçlı)
│ ├── clean_csv/ # Genel temizlikten geçmiş ana veri setleri
│ └── avm_output/ # Wikipedia ile doğrulanmış AVM çıktıları
│
├── outputs/ # Final çıktı dosyaları (CSV / GeoJSON)
│
├── scripts/ # Tüm veri işleme ve pipeline scriptleri
│
└── README.md


## Veri Temizleme Süreci

Bu projede kullanılan konum verileri, OpenStreetMap / Overpass üzerinden elde edilen ham verilerden oluşmaktadır.  
Ham veriler, tek başına etiket bazlı kullanıldığında anlam kaybına ve yanlış önerilere yol açabileceği için çok aşamalı bir filtreleme ve ayrıştırma sürecinden geçirilmiştir.

---

### 1. Genel Temizlik (clean_all_csv.py)

Tüm kategoriler için ortak olarak uygulanan temel temizlik adımları:

- Boş, anlamsız veya geçersiz `name` alanlarının temizlenmesi  
- `latitude` / `longitude` değerlerinin sayısal formata dönüştürülmesi  
- Koordinatı eksik veya bozuk olan kayıtların elenmesi  

Bu aşama sonunda tüm kategorilere ait temizlenmiş veriler  
`datasets/clean_csv/` klasörüne yazılır ve sonraki adımlar için ortak giriş verisi olarak kullanılır.

---

### 2. AVM Özel Filtreleme (filter_avms_by_wikipedia.py)

AVM kategorisi, yanlış etiketlenmeye en açık veri gruplarından biri olduğu için ek bir doğrulama sürecinden geçirilmiştir.

Uygulanan yöntem:

- Wikipedia üzerinden İstanbul’daki gerçek AVM isimleri çekilir  
- İsimler normalize edilir (küçük harf, karakter sadeleştirme vb.)  
- POI havuzundaki kayıtlarla:
  - birebir eşleşme
  - fuzzy string matching (RapidFuzz)
  uygulanır  
- Belirlenen eşik değerinin altındaki eşleşmeler elenir  

Sonuç olarak:

- Gerçek AVM’ler → `true_avm_from_your_pool.csv`  
- AVM olmayan kayıtlar → `not_avm_from_your_pool.csv`  
- Eşleşme detayları → `matching_report.csv`  

üretilir.

---

### 3. AVM Pipeline (avm_pipeline.py)

Wikipedia ile doğrulanmış AVM verileri kullanılarak:

- Temiz AVM CSV dosyası  
- Harita ve mekânsal analizlerde kullanılmak üzere GeoJSON çıktısı  

oluşturulur ve `outputs/` klasörüne yazılır.

Pipeline çıktıları:

- `outputs/avm_clean.csv`  
- `outputs/avm_clean.geojson`  

Bu dosyalar proje boyunca **referans AVM verisi** olarak kullanılır.

---

### 4. Hastane Temizliği (filter_hospitals_main.py)

OSM verilerinde `hospital` etiketi; klinik, poliklinik ve küçük sağlık birimlerini de içerebildiği için hastane verileri isim bazlı kurallarla ayrıştırılmıştır.

Uygulanan temel mantık:

- İsmi içinde **“hastane”** veya **“hospital”** geçen kayıtlar → ana hastane adayları  
- Klinik, poliklinik, göz merkezi, diş kliniği vb. → review  
- Sağlık denetim merkezi, küçük sağlık birimleri → other  

Çıktılar `datasets/hospital_output/` klasörüne yazılır:

- `hospitals_main.csv`  
  → Devlet, özel ve üniversite hastaneleri (ana referans)  
- `hospitals_review.csv`  
  → Klinik ve poliklinikler (kullanıcı profiline göre opsiyonel)  
- `hospitals_other.csv`  
  → Analiz dışı tutulan kayıtlar  

---

### 5. Süpermarket Temizliği (filter_supermarkets_main.py)

“Supermarket” etiketi altında zincir marketler ile küçük mahalle marketleri aynı havuzda yer aldığı için veriler isim bazlı kurallarla üç gruba ayrılmıştır.

- **Main:** Migros, CarrefourSA, A101, Şok, BİM gibi zincir ve büyük ölçekli süpermarketler  
- **Other:** Bakkal, mini market, mahalle marketi gibi küçük yapılar  
- **Review:** AVM içi marketler veya net sınıflandırılamayan kayıtlar  

Bu ayrım sayesinde:

- Günlük alışveriş ihtiyacını karşılayan gerçek süpermarketler öne çıkarılmış  
- Gürültü yaratan küçük ölçekli yapılar ayrıştırılmış  
- Belirsiz kayıtlar manuel inceleme için korunmuştur  

Çıktılar `datasets/supermarket_output/` klasörüne yazılır.

---

### 6. Okul Filtreleme (filter_schools_main.py)

OSM’de tüm eğitim kurumları tek tip “school” etiketiyle geldiği için okullar isim bazlı kurallarla alt kategorilere ayrılmıştır.

- **Public:** Devlet okulları (ilkokul, ortaokul, lise, imam hatip vb.)  
- **Private:** Özel okul, kolej, college geçen kayıtlar  
- **Courses / Hobby:** Kurs, etüt, dil okulu, sanat/müzik/atölye gibi eğitim noktaları  
- **Review:** Türü net olmayan kayıtlar  

Bu yapı sayesinde:

- Çocuklu aileler için devlet okulları önceliklendirilebilir  
- Özel eğitim tercihleri ayrı değerlendirilebilir  
- Hobi ve kişisel gelişim odaklı eğitim noktaları farklı senaryolarda kullanılabilir  

Çıktılar `datasets/school_output/` klasörüne yazılır.

---

### 7. Park Temizliği (filter_parks_main.py)

Park verileri yüksek doğrulukta geldiği için büyük oranda ana grupta tutulmuştur.

- **Main:** Gerçek parklar ve yeşil alanlar  
- **Other / Review:** Park ismi taşısa da park niteliği zayıf olan sınırlı kayıtlar  

Park verileri, aile profilleri ve yaşam kalitesi analizlerinde doğrudan kullanılabilecek şekilde sadeleştirilmiştir.

---

### 8. Ulaşım İstasyonları (filter_stations_main.py)

Metro, tren ve raylı sistem istasyonları ayrıştırılarak:

- **Main:** Aktif istasyonlar  
- **Other / Review:** İstasyon olmayan veya belirsiz kayıtlar  

şeklinde sınıflandırılmıştır.

---

### 9. Sosyal ve Yaşam Alanları

Aşağıdaki kategoriler de aynı isim bazlı ve etiket destekli mantıkla filtrelenmiştir:

- Barlar (filter_bars_main.py)  
- Kafeler (filter_cafes_main.py)  
- Spor salonları (filter_gyms_main.py)  
- Spor merkezleri (filter_sports_centres_main.py)  
- Otoparklar (filter_parking_main.py)  

Bu kategoriler, ileride kullanıcı profiline göre **pozitif veya negatif ağırlık** verilebilecek şekilde ayrı veri setleri olarak tutulmuştur  
(örneğin yaşlı bireyler için barlara uzaklık, sporcular için spor merkezlerine yakınlık).

---

### Genel Sonuç

Bu filtreleme süreci sonunda:

- Tüm POI kategorileri anlamlı alt gruplara ayrılmış  
- Yanlış etiketlenmiş veya gürültü yaratan kayıtlar izole edilmiş  
- Kullanıcı profiline göre puanlama yapılabilecek temiz ve kontrollü bir veri altyapısı oluşturulmuştur.


---

## Yol Haritası (Güncel ve Planlanan Adımlar)

- [x] Overpass API ile POI verilerinin toplanması  
- [x] Genel CSV temizliği (clean_all_csv.py)  
- [x] AVM doğrulama (Wikipedia referansı)  
- [x] AVM Pipeline çıktıları (CSV + GeoJSON)  
- [x] Hospital kategori temizliği  
- [x] Supermarket kategori temizliği  
- [x] Diğer kategoriler için benzer doğrulama kuralları  
- [ ] Kullanıcı profili simülasyonları (öğrenci, aile, yaşlı birey vb.)  
- [ ] Çevresel faktörlere göre ağırlıklı skorlar  
- [ ] Lokasyon / semt bazlı yaşam uyumluluk skorları  
- [ ] Harita tabanlı görselleştirme ve analiz  


## Yol Haritası (Planlanan Adımlar)

Aşağıdaki adımlar, projenin ilerleyen aşamalarında gerçekleştirilecektir.
Her adım tamamlandıkça README güncellenecektir.

### 1. Kategoriye Özel Ek Temizlik
- Hospital: klinik / poliklinik / diş merkezi ayrımı  
- Supermarket & convenience store ayrımı  
- Ulaşım noktalarının alt türlere ayrılması  

### 2. Lokasyon Bazlı Özellik Çıkarımı
- Belirli yarıçaplarda POI yoğunluklarının hesaplanması  
- Lokasyon başına sayısal çevre özelliklerinin oluşturulması  

### 3. Kullanıcı Profili ve Simülasyon
- Öğrenci, aile, yaşlı birey gibi örnek kullanıcı profilleri  
- Profil önceliklerine göre lokasyon skorlama  

### 4. Skorlama ve Öneri Mantığı
- Ağırlıklı çevre skorları  
- Lokasyonların yaşam uygunluğuna göre sıralanması  

### 5. Harita ve Görselleştirme
- GeoJSON tabanlı interaktif harita  
- Profil bazlı lokasyon önerilerinin görsel sunumu  

---
# Proje Ekibi
- Ayça Berin Yener
- Celaleddin Tırıs
- Çağan Koç
- Fatma Sıla Türel
- Ferhunde Tuba Dandin
- Yusuf Mestan

## Notlar

- Ham veriler (`data_raw`) özellikle korunmuştur  
- Tüm temizlik adımları izlenebilir ve tekrar üretilebilir şekilde tasarlanmıştır  
- Proje, veri altyapısı ve karar destek sistemi odağındadır  

---

## V2 Planı (İlan Bazlı Öneri):
“Gerçek ilan havuzu ve konum bilgisi sağlandığında, her ilan için POI tabanlı çevre özellikleri çıkarılarak kullanıcı profiline göre ağırlıklandırılmış skor hesaplanacak ve Top-N ilan önerisi yapılacaktır.”
## Özet

Bu proje, İstanbul için konut odaklı yaşam verilerini
**temiz, doğrulanmış ve sürdürülebilir** bir yapıda sunmayı hedefler.
Elde edilen veri seti, gerçek dünya uygulamalarında
(ör. emlak platformları, akıllı şehir çözümleri)
kullanılabilecek sağlam bir temel sunar.
