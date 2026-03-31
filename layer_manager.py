"""
QGIS katman yöneticisi — parsel geometrilerini katmana ekler/günceller.
"""

from qgis.core import (
    QgsVectorLayer,
    QgsFeature,
    QgsGeometry,
    QgsPointXY,
    QgsField,
    QgsFields,
    QgsProject,
    QgsFillSymbol,
    QgsCoordinateReferenceSystem,
    QgsRectangle,
    QgsPalLayerSettings,
    QgsVectorLayerSimpleLabeling,
    QgsTextFormat,
    QgsTextBufferSettings,
    QgsRelation,
)
from qgis.PyQt.QtCore import QVariant, Qt
# QGIS 3 ve 4 uyumluluğu için en güvenli tip tanımlamaları
TYPE_STRING = QVariant.String
TYPE_INT = QVariant.Int
TYPE_DOUBLE = QVariant.Double

from qgis.PyQt.QtGui import QColor, QFont


KATMAN_ADI = "TKGM Parseller"
KATMAN_BB_ADI = "TKGM Bagimsiz Bolumler"
PARSEL_BB_REL_ID = "tkgm_parsel_bb_rel"
PARSEL_BB_REL_NAME = "Parsel-BagimsizBolum"


def _parsel_anahtar_uret(mahalle_kodu, ada_no, parsel_no) -> str:
    return f"{str(mahalle_kodu)}|{int(ada_no)}|{int(parsel_no)}"


def _layer_adi_ile_bul(layer_name: str):
    for layer in QgsProject.instance().mapLayers().values():
        if layer.name() == layer_name:
            return layer
    return None


def _parsel_bb_iliski_kur() -> None:
    """Parsel ile bağımsız bölüm katmanları arasında ilişkiyi garanti eder."""
    parsel_layer = _layer_adi_ile_bul(KATMAN_ADI)
    bb_layer = _layer_adi_ile_bul(KATMAN_BB_ADI)
    if not parsel_layer or not bb_layer:
        return

    mgr = QgsProject.instance().relationManager()
    mevcut = mgr.relation(PARSEL_BB_REL_ID)

    if mevcut and mevcut.isValid():
        ayni_katmanlar = (
            mevcut.referencedLayerId() == parsel_layer.id()
            and mevcut.referencingLayerId() == bb_layer.id()
        )
        if ayni_katmanlar:
            return
        mgr.removeRelation(PARSEL_BB_REL_ID)

    rel = QgsRelation()
    rel.setId(PARSEL_BB_REL_ID)
    rel.setName(PARSEL_BB_REL_NAME)
    rel.setReferencedLayer(parsel_layer.id())
    rel.setReferencingLayer(bb_layer.id())

    # Child -> Parent alan eşlemesi (bb katmanı -> parsel katmanı)
    rel.addFieldPair("mahalleKodu", "mahalleKodu")
    rel.addFieldPair("adaNo", "adaNo")
    rel.addFieldPair("parselNo", "parselNo")

    if rel.isValid():
        mgr.addRelation(rel)


def _etiket_ayarla(layer: QgsVectorLayer) -> None:
    """Katmana Ada/Parsel etiketini yapılandırır."""
    metin_fmt = QgsTextFormat()

    yazi_tipi = QFont("Arial", 8)
    yazi_tipi.setBold(True)
    metin_fmt.setFont(yazi_tipi)
    metin_fmt.setSize(8)
    metin_fmt.setColor(QColor(0, 60, 20))

    # Beyaz halo (arka plan) — okunabilirlik için
    tampon = QgsTextBufferSettings()
    tampon.setEnabled(True)
    tampon.setSize(1.0)
    tampon.setColor(QColor(255, 255, 255, 200))
    metin_fmt.setBuffer(tampon)

    pal = QgsPalLayerSettings()
    pal.setFormat(metin_fmt)
    # "Ada: 112\nParsel: 5" formatında iki satır etiket
    pal.fieldName = "'Ada: ' || adaNo || '\\nParsel: ' || parselNo"
    pal.isExpression = True
    pal.placement = QgsPalLayerSettings.AroundPoint
    pal.enabled = True

    layer.setLabeling(QgsVectorLayerSimpleLabeling(pal))
    layer.setLabelsEnabled(True)


def _get_or_create_layer() -> QgsVectorLayer:
    """Mevcut parsel katmanını bulur, yoksa yeni oluşturur."""
    for layer in QgsProject.instance().mapLayers().values():
        if layer.name() == KATMAN_ADI:
            _parsel_bb_iliski_kur()
            return layer

    # Yeni bellek katmanı oluştur
    layer = QgsVectorLayer("Polygon?crs=EPSG:4326", KATMAN_ADI, "memory")
    provider = layer.dataProvider()

    # Alanlar
    fields = QgsFields()
    for name, tip in [
        ("mahalleKodu", TYPE_STRING),
        ("adaNo",       TYPE_INT),
        ("parselNo",    TYPE_INT),
        ("alan",        TYPE_DOUBLE),
        ("nitelik",     TYPE_STRING),
        ("pafta",       TYPE_STRING),
        ("il",          TYPE_STRING),
        ("ilce",        TYPE_STRING),
        ("mahalle",     TYPE_STRING),
    ]:
        fields.append(QgsField(name, tip))

    provider.addAttributes(fields)
    layer.updateFields()

    # Stil: yeşil şeffaf dolgu, koyu yeşil kenar
    symbol = QgsFillSymbol.createSimple({
        "color": "0,180,100,80",
        "outline_color": "0,120,60,255",
        "outline_width": "0.6",
    })
    layer.renderer().setSymbol(symbol)

    # Etiket ayarla
    _etiket_ayarla(layer)

    QgsProject.instance().addMapLayer(layer)
    _parsel_bb_iliski_kur()
    return layer


def _get_or_create_bb_layer() -> QgsVectorLayer:
    """Bağımsız bölüm tablosunu bulur, yoksa oluşturur."""
    for layer in QgsProject.instance().mapLayers().values():
        if layer.name() == KATMAN_BB_ADI:
            _parsel_bb_iliski_kur()
            return layer

    layer = QgsVectorLayer("None", KATMAN_BB_ADI, "memory")
    provider = layer.dataProvider()

    fields = QgsFields()
    for name, tip in [
        ("parselKey", TYPE_STRING),
        ("mahalleKodu", TYPE_STRING),
        ("adaNo", TYPE_INT),
        ("parselNo", TYPE_INT),
        ("blok", TYPE_STRING),
        ("bbNo", TYPE_STRING),
        ("tip", TYPE_STRING),
        ("kat", TYPE_STRING),
        ("giris", TYPE_STRING),
        ("nitelik", TYPE_STRING),
        ("durum", TYPE_STRING),
    ]:
        fields.append(QgsField(name, tip))

    provider.addAttributes(fields)
    layer.updateFields()
    QgsProject.instance().addMapLayer(layer)
    _parsel_bb_iliski_kur()
    return layer


def parsel_katmana_ekle(parsel: dict) -> bool:
    """Parsel bilgisini QGIS katmanına mükerrer kontrolü ile ekler."""
    layer = _get_or_create_layer()

    koordinatlar = parsel.get("koordinatlar") or []
    if not koordinatlar:
        return False

    mahalle_kodu = str(parsel.get("mahalleKodu") or "")
    ada_no = int(parsel.get("adaNo") or 0)
    parsel_no = int(parsel.get("parselNo") or 0)

    for f in layer.getFeatures():
        if (
            str(f["mahalleKodu"] or "") == mahalle_kodu
            and int(f["adaNo"] or 0) == ada_no
            and int(f["parselNo"] or 0) == parsel_no
        ):
            return False

    # Polygon oluştur
    points = [QgsPointXY(k["lng"], k["lat"]) for k in koordinatlar]
    geom = QgsGeometry.fromPolygonXY([points])

    feat = QgsFeature(layer.fields())
    feat.setGeometry(geom)
    feat.setAttributes([
        mahalle_kodu,
        ada_no,
        parsel_no,
        float(parsel.get("alan") or 0),
        str(parsel.get("nitelik") or ""),
        str(parsel.get("pafta") or ""),
        str(parsel.get("ilAd") or ""),
        str(parsel.get("ilceAd") or ""),
        str(parsel.get("mahalleAd") or ""),
    ])

    layer.dataProvider().addFeature(feat)
    layer.updateExtents()
    layer.triggerRepaint()
    return True


def bagimsiz_bolumleri_katmana_ekle(parsel: dict, bloklar: list) -> tuple:
    """Bağımsız bölümleri parselle ilişkili tabloya mükerrer eklemeden kaydeder."""
    bb_layer = _get_or_create_bb_layer()

    mahalle_kodu = str(parsel.get("mahalleKodu") or "")
    ada_no = int(parsel.get("adaNo") or 0)
    parsel_no = int(parsel.get("parselNo") or 0)
    parsel_key = _parsel_anahtar_uret(mahalle_kodu, ada_no, parsel_no)

    mevcut_anahtarlar = set()
    for f in bb_layer.getFeatures():
        mevcut_anahtarlar.add(
            (
                str(f["parselKey"] or ""),
                str(f["blok"] or ""),
                str(f["bbNo"] or ""),
            )
        )

    yeni_featler = []
    eklenen = 0
    atlanan = 0

    for blok in bloklar or []:
        blok_no = str(blok.get("blok") or "")
        for bb in blok.get("bagimsizBolumler") or []:
            bb_no = str(bb.get("no") or "")
            anahtar = (parsel_key, blok_no, bb_no)
            if anahtar in mevcut_anahtarlar:
                atlanan += 1
                continue

            feat = QgsFeature(bb_layer.fields())
            feat.setAttributes([
                parsel_key,
                mahalle_kodu,
                ada_no,
                parsel_no,
                blok_no,
                bb_no,
                str(bb.get("tip") or ""),
                str(bb.get("kat") or ""),
                str(bb.get("giris") or ""),
                str(bb.get("nitelik") or ""),
                str(bb.get("durum") or ""),
            ])
            yeni_featler.append(feat)
            mevcut_anahtarlar.add(anahtar)
            eklenen += 1

    if yeni_featler:
        bb_layer.dataProvider().addFeatures(yeni_featler)
        bb_layer.updateExtents()
        bb_layer.triggerRepaint()

    return eklenen, atlanan


def parsele_zoom_yap(canvas, parsel: dict) -> None:
    """Haritayı parsel sınır kutusuna zoom yapar."""
    koordinatlar = parsel.get("koordinatlar") or []
    if not koordinatlar:
        merkez = parsel.get("merkezNokta") or {}
        lat = merkez.get("lat") or 0
        lng = merkez.get("lng") or 0
        if lat and lng:
            rect = QgsRectangle(lng - 0.001, lat - 0.001, lng + 0.001, lat + 0.001)
            canvas.setExtent(rect)
            canvas.refresh()
        return

    lnglar = [k["lng"] for k in koordinatlar]
    latlar = [k["lat"] for k in koordinatlar]
    margin_x = (max(lnglar) - min(lnglar)) * 0.3 or 0.001
    margin_y = (max(latlar) - min(latlar)) * 0.3 or 0.001

    rect = QgsRectangle(
        min(lnglar) - margin_x,
        min(latlar) - margin_y,
        max(lnglar) + margin_x,
        max(latlar) + margin_y,
    )

    # Eğer harita CRS farklıysa dönüştür
    from qgis.core import QgsCoordinateTransform
    crs_wgs84 = QgsCoordinateReferenceSystem("EPSG:4326")
    crs_harita = canvas.mapSettings().destinationCrs()
    if crs_harita != crs_wgs84:
        transform = QgsCoordinateTransform(crs_wgs84, crs_harita, QgsProject.instance())
        rect = transform.transformBoundingBox(rect)

    canvas.setExtent(rect)
    canvas.refresh()
