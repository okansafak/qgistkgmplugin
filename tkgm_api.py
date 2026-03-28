"""
TKGM CBS API istemcisi
Tüm HTTP isteklerini yönetir.
"""

import json
import urllib.request
import urllib.error
from typing import Optional


TKGM_API_BASE = "https://cbsapi.tkgm.gov.tr/megsiswebapi.v3.1/api"
TKGM_PARSEL_BASE = "https://parselsorgu.tkgm.gov.tr/app/modules/administrativeQuery/data"

HEADERS = {
    "Accept": "application/json",
    "Content-Type": "application/json",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
}

TIMEOUT = 30


def _get(url: str) -> dict:
    """Verilen URL'ye GET isteği atar, JSON döner."""
    req = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
        raw = resp.read().decode("utf-8")
    return json.loads(raw)


def _parse_feature_collection(data: dict, tip: str) -> list:
    """GeoJSON FeatureCollection'ı düz liste olarak döner."""
    if data.get("type") == "FeatureCollection" and "features" in data:
        result = []
        for f in data["features"]:
            props = f.get("properties") or {}
            if tip == "il":
                result.append({
                    "id": props.get("id"),
                    "ad": props.get("text") or props.get("ad") or props.get("name", ""),
                    "kod": props.get("id"),
                })
            elif tip == "ilce":
                result.append({
                    "ilceKodu": props.get("id"),
                    "ilceAdi": props.get("text") or props.get("ilceAdi") or props.get("ad", ""),
                    "ilKodu": props.get("ilId"),
                })
            elif tip == "mahalle":
                result.append({
                    "mahalleKodu": props.get("id"),
                    "mahalleAdi": props.get("text") or props.get("mahalleAdi") or props.get("ad", ""),
                    "ilceKodu": props.get("ilceId"),
                })
        return result
    if isinstance(data, list):
        return data
    return []


def get_il_listesi() -> list:
    """81 ilin listesini döner."""
    try:
        url = f"{TKGM_PARSEL_BASE}/ilListe.json"
        data = _get(url)
        parsed = _parse_feature_collection(data, "il")
        if parsed:
            return parsed
    except Exception:
        pass
    # Statik fallback
    return [
        {"id": i, "ad": ad, "kod": i} for i, ad in enumerate([
            "Adana","Adıyaman","Afyonkarahisar","Ağrı","Amasya","Ankara","Antalya","Artvin",
            "Aydın","Balıkesir","Bilecik","Bingöl","Bitlis","Bolu","Burdur","Bursa","Çanakkale",
            "Çankırı","Çorum","Denizli","Diyarbakır","Edirne","Elazığ","Erzincan","Erzurum",
            "Eskişehir","Gaziantep","Giresun","Gümüşhane","Hakkari","Hatay","Isparta","Mersin",
            "İstanbul","İzmir","Kars","Kastamonu","Kayseri","Kırklareli","Kırşehir","Kocaeli",
            "Konya","Kütahya","Malatya","Manisa","Kahramanmaraş","Mardin","Muğla","Muş","Nevşehir",
            "Niğde","Ordu","Rize","Sakarya","Samsun","Siirt","Sinop","Sivas","Tekirdağ","Tokat",
            "Trabzon","Tunceli","Şanlıurfa","Uşak","Van","Yozgat","Zonguldak","Aksaray","Bayburt",
            "Karaman","Kırıkkale","Batman","Şırnak","Bartın","Ardahan","Iğdır","Yalova","Karabük",
            "Kilis","Osmaniye","Düzce",
        ], 1)
    ]


def get_ilce_listesi(il_kodu) -> list:
    """Verilen il koduna göre ilçe listesi döner."""
    url = f"{TKGM_API_BASE}/idariYapi/ilceListe/{il_kodu}"
    data = _get(url)
    return _parse_feature_collection(data, "ilce")


def get_mahalle_listesi(ilce_kodu) -> list:
    """Verilen ilçe koduna göre mahalle listesi döner."""
    url = f"{TKGM_API_BASE}/idariYapi/mahalleListe/{ilce_kodu}"
    data = _get(url)
    return _parse_feature_collection(data, "mahalle")


def _parse_parsel_feature(data: dict, mahalle_kodu=None, ada_no=None, parsel_no=None) -> Optional[dict]:
    """GeoJSON Feature'dan parsel bilgisi çıkarır."""
    if data.get("Message"):
        raise ValueError(data["Message"])

    if data.get("type") != "Feature":
        raise ValueError("Beklenmeyen API yanıtı")

    props = data.get("properties") or {}
    geom = data.get("geometry") or {}

    # Alan temizle
    alan_str = str(props.get("alan") or "0")
    try:
        alan = float(alan_str.replace(".", "").replace(",", "."))
    except ValueError:
        alan = 0.0

    # Merkez nokta hesapla
    center_lat, center_lng = 0.0, 0.0
    coords_raw = []
    if geom.get("type") == "Polygon" and geom.get("coordinates"):
        ring = geom["coordinates"][0]
        coords_raw = ring
        if ring:
            center_lng = sum(c[0] for c in ring) / len(ring)
            center_lat = sum(c[1] for c in ring) / len(ring)

    return {
        "mahalleKodu": props.get("mahalleId") or mahalle_kodu,
        "adaNo": int(props.get("adaNo") or ada_no or 0),
        "parselNo": int(props.get("parselNo") or parsel_no or 0),
        "alan": alan,
        "nitelik": props.get("nitelik") or "",
        "pafta": props.get("pafta") or "",
        "ilAd": props.get("ilAd") or "",
        "ilceAd": props.get("ilceAd") or "",
        "mahalleAd": props.get("mahalleAd") or "",
        "geometri": {
            "type": geom.get("type"),
            "coordinates": geom.get("coordinates"),
        },
        "merkezNokta": {
            "lat": center_lat,
            "lng": center_lng,
        },
        "koordinatlar": [{"lat": c[1], "lng": c[0]} for c in coords_raw],
    }


def get_parsel(mahalle_kodu, ada_no, parsel_no) -> dict:
    """Mahalle kodu, ada ve parsel numarasıyla parsel sorgular."""
    url = f"{TKGM_API_BASE}/parsel/{mahalle_kodu}/{ada_no}/{parsel_no}"
    data = _get(url)
    return _parse_parsel_feature(data, mahalle_kodu, ada_no, parsel_no)


def get_parsel_koordinat(lat: float, lng: float) -> dict:
    """Koordinat ile parsel sorgular."""
    url = f"{TKGM_API_BASE}/parsel/{lat}/{lng}/"
    data = _get(url)
    return _parse_parsel_feature(data)
