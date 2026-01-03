import re
import unicodedata
from pathlib import Path

import pandas as pd
import requests
from rapidfuzz import process, fuzz

# ======================
# PROJE YOLLARI
# ======================
BASE_DIR = Path(__file__).resolve().parents[1]
POOL_PATH = BASE_DIR / "datasets" / "istanbul_malls.csv"

OUT_TRUE = "true_avm_from_your_pool.csv"
OUT_FALSE = "not_avm_from_your_pool.csv"
OUT_REPORT = "matching_report.csv"

FUZZY_THRESHOLD = 80

# ======================
# NORMALIZE
# ======================
def normalize_text(text):
    if pd.isna(text):
        return ""
    text = str(text).lower().strip()
    text = unicodedata.normalize("NFKD", text)
    text = "".join(c for c in text if not unicodedata.combining(c))
    text = re.sub(r"[^a-z0-9\s]", " ", text)
    text = re.sub(r"\s+", " ", text).strip()

    junk = {"avm", "alisveris", "merkezi", "shopping", "center", "centre", "mall"}
    words = [w for w in text.split() if w not in junk]
    return " ".join(words)

# ======================
# 1) WIKIDATA (STABİL / HATAYA DAYANIKLI)
# ======================
WIKIDATA_QUERY = """
SELECT ?itemLabel WHERE {
  ?item wdt:P31 wd:Q11315.
  ?item wdt:P131* wd:Q406.
  SERVICE wikibase:label { bd:serviceParam wikibase:language "tr,en". }
}
"""

def fetch_avms_from_wikidata():
    url = "https://query.wikidata.org/sparql"
    headers = {
        "User-Agent": "EvYasamOneriSistemi/1.0 (student project)",
        "Accept": "application/sparql-results+json",
        "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
    }

    # POST daha stabil
    r = requests.post(url, data={"query": WIKIDATA_QUERY}, headers=headers, timeout=60)

    # JSON değilse (HTML / boş / hata) kontrol edelim
    ct = (r.headers.get("Content-Type") or "").lower()
    if r.status_code != 200 or "json" not in ct:
        print("\n❌ Wikidata beklenmedik cevap döndürdü.")
        print("Status:", r.status_code)
        print("Content-Type:", r.headers.get("Content-Type"))
        print("Body (ilk 300 karakter):")
        print(r.text[:300])
        raise RuntimeError("Wikidata JSON dönmedi (rate-limit / servis hatası olabilir).")

    data = r.json()
    bindings = data.get("results", {}).get("bindings", [])
    names = []
    for b in bindings:
        lbl = b.get("itemLabel", {}).get("value")
        if lbl:
            names.append(lbl)

    df = pd.DataFrame({"avm_name": names})
    df["avm_norm"] = df["avm_name"].apply(normalize_text)
    df = df[df["avm_norm"] != ""].drop_duplicates("avm_norm").reset_index(drop=True)
    return df

# ======================
# 2) WIKIPEDIA API FALLBACK
# (Wikidata çökerse en azından isim listesi alalım)
# ======================
WIKI_TITLE = "İstanbul%27daki_alışveriş_merkezleri_listesi"

def fetch_avms_from_wikipedia_api():
    # MediaWiki parse API (HTML verir, ama 403 daha az olur)
    url = f"https://tr.wikipedia.org/w/api.php"
    params = {
        "action": "parse",
        "page": "İstanbul'daki alışveriş merkezleri listesi",
        "prop": "wikitext",
        "format": "json"
    }
    headers = {"User-Agent": "EvYasamOneriSistemi/1.0 (student project)"}
    r = requests.get(url, params=params, headers=headers, timeout=60)
    r.raise_for_status()
    data = r.json()

    wikitext = data.get("parse", {}).get("wikitext", {}).get("*", "")
    if not wikitext:
        return pd.DataFrame(columns=["avm_name", "avm_norm"])

    # Wikitext içinden maddeleri yakala: "* AVM Adı"
    names = []
    for line in wikitext.splitlines():
        line = line.strip()
        if line.startswith("*"):
            item = line.lstrip("*").strip()
            # linkleri temizle: [[Zorlu Center]] -> Zorlu Center
            item = re.sub(r"\[\[(?:[^\]|]+\|)?([^\]]+)\]\]", r"\1", item)
            item = re.sub(r"\{\{.*?\}\}", "", item)
            item = re.sub(r"<.*?>", "", item)
            item = item.strip()
            if item:
                names.append(item)

    names = list(dict.fromkeys(names))
    df = pd.DataFrame({"avm_name": names})
    df["avm_norm"] = df["avm_name"].apply(normalize_text)
    df = df[df["avm_norm"] != ""].drop_duplicates("avm_norm").reset_index(drop=True)
    return df

# ======================
# MAIN
# ======================
def main():
    print("1) AVM isimleri çekiliyor...")

    avm_df = None
    try:
        avm_df = fetch_avms_from_wikidata()
        print(f"✅ Wikidata: {len(avm_df)} AVM bulundu.")
    except Exception as e:
        print("⚠️ Wikidata başarısız, Wikipedia API ile deniyorum...")
        avm_df = fetch_avms_from_wikipedia_api()
        print(f"✅ Wikipedia API: {len(avm_df)} isim bulundu.")

    if avm_df is None or len(avm_df) == 0:
        print("\n❌ AVM isim listesi boş geldi. Bu durumda eşleştirme yapılamaz.")
        return

    print("Örnek AVM isimleri:", avm_df["avm_name"].head(10).to_list())

    print("\n2) Havuz okunuyor:", POOL_PATH)
    pool = pd.read_csv(POOL_PATH)

    name_col = "name"
    lat_col = "latitude"
    lon_col = "longitude"

    # kolonlar yoksa direkt dur
    for c in [name_col, lat_col, lon_col]:
        if c not in pool.columns:
            print("\n❌ Havuz CSV'de kolon bulunamadı:", c)
            print("Kolonlar:", list(pool.columns))
            return

    pool = pool.dropna(subset=[name_col, lat_col, lon_col]).copy()
    pool["pool_norm"] = pool[name_col].apply(normalize_text)

    print("\nHavuz örnek isimler (norm):")
    print(pool["pool_norm"].head(10).to_list())

    # EXACT
    avm_set = set(avm_df["avm_norm"].tolist())
    pool["exact_hit"] = pool["pool_norm"].isin(avm_set)

    # FUZZY
    choices = avm_df["avm_norm"].tolist()
    best_match = []
    best_score = []

    for x in pool["pool_norm"].tolist():
        if not x:
            best_match.append(None)
            best_score.append(0)
            continue

        m = process.extractOne(x, choices, scorer=fuzz.token_set_ratio)
        if m is None:
            best_match.append(None)
            best_score.append(0)
        else:
            best_match.append(m[0])
            best_score.append(m[1])

    pool["fuzzy_match"] = best_match
    pool["fuzzy_score"] = best_score
    pool["fuzzy_hit"] = pool["fuzzy_score"] >= FUZZY_THRESHOLD

    pool["is_avm"] = pool["exact_hit"] | pool["fuzzy_hit"]

    true_avm = pool[pool["is_avm"]].copy()
    not_avm = pool[~pool["is_avm"]].copy()

    report = true_avm.merge(
        avm_df[["avm_name", "avm_norm"]],
        left_on="fuzzy_match",
        right_on="avm_norm",
        how="left"
    ).drop(columns=["avm_norm"])

    true_avm.to_csv(BASE_DIR / OUT_TRUE, index=False, encoding="utf-8-sig")
    not_avm.to_csv(BASE_DIR / OUT_FALSE, index=False, encoding="utf-8-sig")
    report.to_csv(BASE_DIR / OUT_REPORT, index=False, encoding="utf-8-sig")

    print("\nBitti ✅")
    print(f"- AVM olanlar: {len(true_avm)} -> {OUT_TRUE}")
    print(f"- AVM olmayanlar: {len(not_avm)} -> {OUT_FALSE}")
    print(f"- Rapor satırı: {len(report)} -> {OUT_REPORT}")
    print(f"- Fuzzy threshold: {FUZZY_THRESHOLD}")

if __name__ == "__main__":
    main()
