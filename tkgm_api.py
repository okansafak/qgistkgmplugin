"""
TKGM CBS API istemcisi
Tüm HTTP isteklerini yönetir.
"""

import json
import html
import re
from datetime import date
from pathlib import Path
import threading
import urllib.parse
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
ALLOWED_URL_SCHEMES = {"http", "https"}
ALLOWED_URL_HOSTS = {"cbsapi.tkgm.gov.tr", "parselsorgu.tkgm.gov.tr"}
QUERY_COUNTER_FILE = Path.home() / ".tkgm_parsel_plugin_query_stats.json"
QUERY_COUNTER_LOCK = threading.Lock()


def _bugun_str() -> str:
    return date.today().isoformat()


def _load_query_stats() -> dict:
    today = _bugun_str()
    varsayilan = {"date": today, "count": 0}

    try:
        if not QUERY_COUNTER_FILE.exists():
            return varsayilan
        data = json.loads(QUERY_COUNTER_FILE.read_text(encoding="utf-8"))
        if not isinstance(data, dict):
            return varsayilan
    except Exception:
        return varsayilan

    raw_count = data.get("count", 0)
    try:
        count = max(0, int(raw_count))
    except (TypeError, ValueError):
        count = 0

    if data.get("date") != today:
        return {"date": today, "count": 0}
    return {"date": today, "count": count}


def _save_query_stats(stats: dict) -> None:
    try:
        QUERY_COUNTER_FILE.write_text(json.dumps(stats, ensure_ascii=False), encoding="utf-8")
    except Exception:
        pass


def _increment_daily_query_count() -> int:
    with QUERY_COUNTER_LOCK:
        stats = _load_query_stats()
        stats["count"] = int(stats.get("count", 0)) + 1
        _save_query_stats(stats)
        return stats["count"]


def get_gunluk_sorgu_sayisi() -> int:
    """Bugün yapılan toplam sorgu sayısını döner."""
    with QUERY_COUNTER_LOCK:
        stats = _load_query_stats()
        _save_query_stats(stats)
        return int(stats.get("count", 0))


def _extract_message_from_raw(raw: str) -> Optional[str]:
    metin = (raw or "").strip()
    if not metin:
        return None

    # XML string payload: <string>Mesaj</string>
    if metin.startswith("<"):
        m = re.search(r"<string[^>]*>(.*?)</string>", metin, flags=re.IGNORECASE | re.DOTALL)
        if m:
            return html.unescape(m.group(1).strip())

    # JSON payload içinde Message benzeri alanlar
    try:
        data = json.loads(metin)
        if isinstance(data, dict):
            for key in ("Message", "message", "error", "detail"):
                if data.get(key):
                    return str(data.get(key)).strip()
    except Exception:
        pass

    return None


def _validate_url(url: str) -> None:
    """Yalnızca beklenen HTTP(S) URL şemalarına izin ver."""
    parsed = urllib.parse.urlparse(url)
    if parsed.scheme.lower() not in ALLOWED_URL_SCHEMES:
        raise ValueError(f"Geçersiz URL şeması: {parsed.scheme}")
    host = (parsed.hostname or "").lower()
    if host not in ALLOWED_URL_HOSTS:
        raise ValueError(f"İzin verilmeyen URL hostu: {host}")


def _get(url: str) -> dict:
    """Verilen URL'ye GET isteği atar, JSON döner."""
    _validate_url(url)
    _increment_daily_query_count()
    req = urllib.request.Request(url, headers=HEADERS)
    opener = urllib.request.build_opener()
    try:
        # URL, şema + host allowlist kontrolünden geçtiği için burada kontrollü açılır.
        with opener.open(req, timeout=TIMEOUT) as resp:
            raw = resp.read().decode("utf-8")
    except urllib.error.HTTPError as e:
        raw_err = ""
        try:
            raw_err = e.read().decode("utf-8", errors="replace")
        except Exception:
            raw_err = ""

        mesaj = _extract_message_from_raw(raw_err)
        if mesaj:
            raise ValueError(mesaj)
        raise ValueError(f"HTTP {e.code}")

    mesaj = _extract_message_from_raw(raw)
    if mesaj:
        raise ValueError(mesaj)

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


def get_parsel_blok_listesi(mahalle_kodu, ada_no, parsel_no) -> list:
    """Parsel üzerindeki bina/blok (BB) listesini döner."""
    url = f"{TKGM_API_BASE}/parsel/blok/{mahalle_kodu}/{ada_no}/{parsel_no}"
    data = _get(url)

    if data.get("Message"):
        raise ValueError(data["Message"])

    if data.get("type") != "FeatureCollection":
        raise ValueError("Beklenmeyen API yanıtı")

    result = []
    for feature in data.get("features") or []:
        props = feature.get("properties") or {}
        result.append({
            "blok": props.get("blok") or "",
            "bagimsizBolumSayisi": props.get("bagimsizBolumSayisi") or 0,
            "zeminKmdurum": props.get("zeminKmdurum") or "",
            "atZeminId": props.get("atZeminId"),
            "mahalleId": props.get("mahalleId") or mahalle_kodu,
            "adaNo": str(props.get("adaNo") or ada_no),
            "parselNo": str(props.get("parselNo") or parsel_no),
        })

    return result


def get_parsel_bagimsiz_bolum_listesi(mahalle_kodu, ada_no, parsel_no, blok_no) -> list:
    """Parseldeki blok için bağımsız bölüm (kat mülkiyeti) listesini döner."""
    blok_enc = urllib.parse.quote(str(blok_no), safe="")
    url = f"{TKGM_API_BASE}/parsel/bagimsizbolum/{mahalle_kodu}/{ada_no}/{parsel_no}/{blok_enc}"
    data = _get(url)

    if data.get("Message"):
        raise ValueError(data["Message"])

    if data.get("type") != "FeatureCollection":
        raise ValueError("Beklenmeyen API yanıtı")

    result = []
    for feature in data.get("features") or []:
        props = feature.get("properties") or {}
        result.append({
            "tip": props.get("tip") or "",
            "kat": props.get("kat") or "",
            "giris": props.get("giris") or "",
            "nitelik": props.get("nitelik") or "",
            "no": str(props.get("no") or ""),
            "blok": str(props.get("blok") or blok_no),
            "durum": str(props.get("durum") or ""),
        })

    return result


def get_parsel_blok_ve_bb_listesi(mahalle_kodu, ada_no, parsel_no) -> list:
    """Parseldeki tüm blokları ve her blok için bağımsız bölüm listesini döner."""
    bloklar = get_parsel_blok_listesi(mahalle_kodu, ada_no, parsel_no)
    for blok in bloklar:
        # TKGM servisinde tek bloklu yapılarda blok değeri boş dönebilir;
        # bagimsizbolum uç noktası bu durumda "0" bekler.
        blok_no = blok.get("blok")
        if blok_no is None or str(blok_no).strip() == "":
            blok_no = 0
        try:
            blok["bagimsizBolumler"] = get_parsel_bagimsiz_bolum_listesi(
                mahalle_kodu,
                ada_no,
                parsel_no,
                blok_no,
            )
        except Exception:
            blok["bagimsizBolumler"] = []
    return bloklar
