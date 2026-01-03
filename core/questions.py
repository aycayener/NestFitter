QUESTIONS = [
    {
        "question": "Yaş aralığınız?",
        "options": {
            "18–25": ["age_18_25"],
            "26–35": ["age_26_35"],
            "36–50": ["age_36_50"],
            "50+": ["age_50_plus"]
        }
    },
    {
        "question": "Medeni durumunuz?",
        "options": {
            "Bekar": [],
            "Evli": ["is_married"]
        }
    },
    {
        "question": "Çocuğunuz var mı?",
        "options": {
            "Evet": ["has_child"],
            "Hayır": []
        }
    },
    {
        "question": "Ulaşım tercihiniz?",
        "options": {
            "Toplu taşıma": ["uses_public_transport"],
            "Özel araç": ["has_car"]
        }
    },
    {
        "question": "Sosyal hayat sizin için ne kadar önemli?",
        "options": {
            "Çok önemli": ["social_life_high"],
            "Orta": [],
            "Önemli değil": ["silence_important"]
        }
    },
    {
        "question": "Sporla aktif olarak ilgileniyor musunuz?",
        "options": {
            "Evet": ["sport_active"],
            "Hayır": []
        }
    },
    {
        "question": "Park / yeşil alan yakınlığı sizin için önemli mi?",
        "options": {
            "Evet, çok önemli": ["park_important"],
            "Fark etmez": [],
            "Hayır": []
        }
    }
{
    "id": "health_priority",
    "question": "Sağlık hizmetlerine (hastane) yakınlık sizin için önemli mi?",
    "options": [
        {"text": "Evet", "features": ["health_priority"]},
        {"text": "Hayır", "features": []}
    ]
}

]
