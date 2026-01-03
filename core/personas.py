FEATURE_KEYS = [
    # Age
    "age_18_25",
    "age_26_35",
    "age_36_50",
    "age_50_plus",

    # Family
    "is_married",
    "has_child",

    # Transport
    "uses_public_transport",
    "has_car",

    # Lifestyle
    "social_life_high",
    "silence_important",
    "sport_active",
    "park_important",
    "mall_lover"
]

PERSONA_FEATURES = {

    "student": {
        "age_18_25": 1,
        "uses_public_transport": 1,
        "social_life_high": 1
    },

    "family_with_child": {
        "age_36_50": 1,
        "is_married": 1,
        "has_child": 1,
        "park_important": 1,
        "silence_important": 1
    },

    "elderly_couple": {
        "age_50_plus": 1,
        "is_married": 1,
        "silence_important": 1,
        "park_important": 1
    },

    "sports_focused_single": {
        "age_26_35": 1,
        "sport_active": 1,
        "park_important": 1
    },

    "social_young": {
        "age_18_25": 1,
        "social_life_high": 1
    },

    "quiet_seeker": {
        "silence_important": 1,
        "park_important": 1
    },

    "remote_worker": {
        "age_26_35": 1,
        "silence_important": 1,
        "park_important": 1
    },

    "newly_married_couple": {
        "age_26_35": 1,
        "is_married": 1
    },

    "wellbeing_oriented": {
        "sport_active": 1,
        "silence_important": 1,
        "park_important": 1
    },

    "car_owner_worker": {
        "age_26_35": 1,
        "has_car": 1
    },

    "mall_oriented": {
        "mall_lover": 1,
        "social_life_high": 1
    },

    "chronic_patient": {
        "age_36_50": 1,
        "silence_important": 1,
        "park_important": 1
    }
}
