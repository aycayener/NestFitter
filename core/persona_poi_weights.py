PERSONA_POI_WEIGHTS = {

    # -------------------------------------------------
    # Öğrenci / Genç
    # -------------------------------------------------
    "student": {
        "station_main": 5,
        "supermarket_main": 4,
        "cafe_main": 3,
        "bar_main": 2,
        "park_main": 2,
        "mall_main": 1,
        "gym_main": 1
    },

    "social_young": {
        "cafe_main": 5,
        "bar_main": 4,
        "station_main": 3,
        "mall_main": 2,
        "park_main": 1
    },

    # -------------------------------------------------
    # Aile / Evli
    # -------------------------------------------------
    "family_with_child": {
        "school_main": 5,
        "park_main": 5,
        "supermarket_main": 4,
        "hospital_main": 3,
        "station_main": 2,
        "bar_main": -3
    },

    "newly_married_couple": {
        "supermarket_main": 4,
        "park_main": 3,
        "mall_main": 3,
        "station_main": 2,
        "bar_main": -1
    },

    # -------------------------------------------------
    # Yaşlı / Sessiz
    # -------------------------------------------------
    "elderly_couple": {
        "hospital_main": 5,
        "park_main": 4,
        "supermarket_main": 3,
        "station_main": 2,
        "bar_main": -4
    },

    "quiet_seeker": {
        "park_main": 5,
        "supermarket_main": 3,
        "hospital_main": 2,
        "bar_main": -5,
        "cafe_main": -2
    },

    # -------------------------------------------------
    # Spor / Wellbeing
    # -------------------------------------------------
    "sports_focused_single": {
        "gym_main": 5,
        "sports_centre_main": 4,
        "park_main": 3,
        "supermarket_main": 2,
        "bar_main": -1
    },

    "wellbeing_oriented": {
        "park_main": 5,
        "gym_main": 3,
        "hospital_main": 2,
        "supermarket_main": 2,
        "bar_main": -3
    },

    # -------------------------------------------------
    # Doğa & Sessizlik (spor zorunlu değil)
    # -------------------------------------------------
    "nature_lover_single": {
        "park_main": 5,
        "supermarket_main": 3,
        "station_main": 2,
        "gym_main": -1,
        "bar_main": -4
    },

    "remote_worker": {
        "park_main": 4,
        "supermarket_main": 4,
        "station_main": 2,
        "bar_main": -3
    },

    "home_body_single": {
        "supermarket_main": 4,
        "park_main": 3,
        "bar_main": -4,
        "cafe_main": -2
    },

    # -------------------------------------------------
    # Ulaşım / Araç
    # -------------------------------------------------
    "car_owner_worker": {
        "parking_main": 5,
        "supermarket_main": 3,
        "mall_main": 2,
        "station_main": -1
    },

    # -------------------------------------------------
    # AVM & Sosyal
    # -------------------------------------------------
    "mall_oriented": {
        "mall_main": 5,
        "supermarket_main": 3,
        "cafe_main": 2,
        "park_main": 1
    },

    # -------------------------------------------------
    # Sağlık
    # -------------------------------------------------
    "chronic_patient": {
        "hospital_main": 5,
        "park_main": 3,
        "supermarket_main": 2,
        "bar_main": -4
    }
}
