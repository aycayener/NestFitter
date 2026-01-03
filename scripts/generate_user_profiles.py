from pathlib import Path
import json

# Bu BASE_DIR sayesinde dosya yolları her bilgisayarda aynı mantıkla çalışıyor.
# (PyCharm'da nereden çalıştırırsan çalıştır, proje kökünü buluyor.)
BASE_DIR = Path(__file__).resolve().parents[1]

# Bu scriptin amacı: profilleri tek bir json dosyasına yazmak.
# O yüzden outputs/profiles klasörünü garantiye alıyoruz.
OUTPUT_DIR = BASE_DIR / "outputs" / "profiles"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

OUTPUT_PATH = OUTPUT_DIR / "user_profiles.json"


def generate_profiles():
    """
    Buraya profilleri liste olarak yazıyoruz çünkü:
    - sabit (random değil) profiller istiyoruz
    - app tarafında bu listeyi okuyup seçenek olarak göstereceğiz
    """

    profiles = [
        # -------------------------
        # ZORUNLU PROFİLLER (proje isterleri)
        # -------------------------
        {
            "profile_id": "student",
            "profile_name": "Öğrenci",
            "description": "Üniversiteye yakın, ulaşımı kolay ve sosyal imkanları olan lokasyonları tercih eder.",
            "radius_m": 1000,
            # weights: her kategoriye + / - önem değeri veriyoruz
            # +5 çok isterim, -2 istemem
            "weights": {
                "station_main": 5,
                "school_public": 4,
                "school_courses": 3,
                "supermarket_main": 3,
                "cafe_main": 2,
                "bar_main": 1,
                "park_main": 1,
                "mall_main": 1,
            },
        },
        {
            "profile_id": "family_with_child",
            "profile_name": "Çocuklu Aile",
            "description": "İlkokul, park ve sağlık hizmetlerine yakın, daha sakin yaşam alanlarını tercih eder.",
            "radius_m": 1000,

            # must_have: “Bu kategori hiç yoksa ben bu yeri önermem” gibi düşün.
            # Örn: okul yoksa çocuklu aileye önerme.
            "must_have": ["school_public"],

            "weights": {
                "school_public": 5,
                "park_main": 4,
                "hospital_main": 4,
                "supermarket_main": 3,
                "station_main": 2,
                "bar_main": -2,
            },
        },
        {
            "profile_id": "elderly_couple",
            "profile_name": "Yaşlı Çift",
            "description": "Sağlık hizmetlerine yakın ve daha sakin bölgeleri tercih eder.",
            "radius_m": 800,
            "weights": {
                "hospital_main": 5,
                "park_main": 4,
                "supermarket_main": 3,
                "station_main": 2,
                "bar_main": -3,
                "cafe_main": -1,
            },
        },
        {
            "profile_id": "sport_focused_single",
            "profile_name": "Spor Odaklı Bekar",
            "description": "Spor salonlarına ve açık spor alanlarına yakın yaşamayı önemser.",
            "radius_m": 1000,
            "weights": {
                "gym_main": 5,
                "sports_centre_main": 5,
                "park_main": 3,
                "supermarket_main": 2,
                "bar_main": 1,
            },
        },
        {
            "profile_id": "social_young",
            "profile_name": "Sosyal Hayat Odaklı Genç",
            "description": "Cafe, bar ve sosyal mekanlara yakın, daha canlı bölgeleri sever.",
            "radius_m": 800,
            "weights": {
                "cafe_main": 5,
                "bar_main": 5,
                "mall_main": 3,
                "station_main": 3,
                "park_main": 1,
            },
        },
        {
            "profile_id": "quiet_seeker",
            "profile_name": "Sessizlik Arayan",
            "description": "Kalabalıktan uzak, yeşil alana yakın ve sakin lokasyonları tercih eder.",
            "radius_m": 1000,

            # avoid: “Bunlar yakınsa puan düşür, istemiyorum”
            "avoid": ["bar_main", "cafe_main"],

            "weights": {
                "park_main": 5,
                "hospital_main": 3,
                "supermarket_main": 3,
                "bar_main": -5,
                "cafe_main": -4,
                "mall_main": -2,
            },
        },

        # -------------------------
        # EK PROFİLLER (opsiyonel)
        # Bunlar “güzel olur” profilleri. İstersen azaltabilirsin.
        # -------------------------
        {
            "profile_id": "remote_worker",
            "profile_name": "Uzaktan Çalışan",
            "description": "Sessiz ama ihtiyaçlara yakın lokasyonları tercih eder.",
            "radius_m": 1000,
            "weights": {
                "supermarket_main": 4,
                "park_main": 3,
                "cafe_main": 2,
                "station_main": 1,
                "bar_main": -2,
            },
        },
        {
            "profile_id": "car_owner_worker",
            "profile_name": "Araç Sahibi Çalışan",
            "description": "Otopark erişimi olan, pratik bölgeleri tercih eder.",
            "radius_m": 1200,
            "weights": {
                "parking_main": 5,
                "station_main": 3,
                "supermarket_main": 3,
                "mall_main": 2,
                "bar_main": -1,
            },
        },
    ]
    return profiles


def main():
    # main() koymamızın sebebi şu:
    # - dosya import edilirse çalışmasın
    # - sadece terminalden çalıştırınca JSON üretsin
    profiles = generate_profiles()

    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(profiles, f, ensure_ascii=False, indent=2)

    print(f"[OK] {len(profiles)} profil yazıldı -> {OUTPUT_PATH}")
    for p in profiles:
        print(f" - {p['profile_name']} ({p['profile_id']})")


if __name__ == "__main__":
    main()
