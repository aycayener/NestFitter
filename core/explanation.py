POI_LABELS = {
    "park_main": "park/yeşil alan",
    "supermarket_main": "süpermarket",
    "station_main": "toplu taşıma istasyonu",
    "gym_main": "spor salonu",
    "sports_centre_main": "spor merkezi",
    "school_public": "devlet okulu",
    "school_private": "özel okul",
    "school_courses": "kurs/atölye",
    "cafe_main": "kafe",
    "bar_main": "bar",
    "hospital_main": "hastane",
    "mall_main": "AVM",
    "parking_main": "otopark",
}


def generate_explanation(breakdown: dict, weights: dict, max_items: int = 6) -> str:
    """
    breakdown: {"park_main": 3, ...}  (sayım)
    weights: {"park_main": 4, ...}    (ağırlık)
    """
    if not isinstance(breakdown, dict) or not breakdown:
        return "Bu nokta için açıklama üretilemedi (POI sayımları boş)."

    positive_lines = []
    negative_lines = []

    # sadece sayısı > 0 olanlar
    items = [(k, int(v)) for k, v in breakdown.items() if v and int(v) > 0]

    # katkıya göre sırala: count * weight (mutlak katkı)
    def contrib(k, c):
        return abs(c * weights.get(k, 0))

    items = sorted(items, key=lambda x: contrib(x[0], x[1]), reverse=True)[:max_items]

    for poi_key, count in items:
        label = POI_LABELS.get(poi_key, poi_key)
        w = weights.get(poi_key, 0)

        if w > 0:
            positive_lines.append(f"{count} adet {label}")
        elif w < 0:
            negative_lines.append(f"{count} adet {label}")
        else:
            # ağırlığı 0 ise açıklamada göstermeyebiliriz (gürültü)
            pass

    parts = []
    if positive_lines:
        parts.append("Bu bölgede " + ", ".join(positive_lines) + " bulunuyor.")
    if negative_lines:
        parts.append("Dikkat: yakın çevrede " + ", ".join(negative_lines) + " da var (profilinde negatif etkili).")

    return " ".join(parts) if parts else "Bu nokta için anlamlı bir açıklama üretilemedi (ağırlıklar 0 olabilir)."
