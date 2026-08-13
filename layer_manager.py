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
    pal.placement = getattr(getattr(QgsPalLayerSettings, "Placement", QgsPalLayerSettings), "AroundPoint")
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
    parsel_anahtar = _parsel_anahtar_uret(mahalle_kodu, ada_no, parsel_no)

    # Mevcut kayıtları temizle (bu parsele ait olanları)
    silinecek_id_listesi = []
    for feat in bb_layer.getFeatures():
        if str(feat.attribute("parselAnahtar")) == parsel_anahtar:
            silinecek_id_listesi.append(feat.id())

    bb_layer.startEditing()
    if silinecek_id_listesi:
        bb_layer.dataProvider().deleteFeatures(silinecek_id_listesi)

    # Yeni kayıtları ekle
    yeni_kayitlar = []
    fields = bb_layer.fields()

    for blok in bloklar_guvenli(blok_listesi):
        bb_arr = blok.get("bagimsizBolumler")
        if not bb_arr:
            continue
        
        for bb in bb_arr:
            feat = QgsFeature(fields)
            feat.setAttribute("parselAnahtar", parsel_anahtar)
            feat.setAttribute("blok", blok.get("blok") or "")
            feat.setAttribute("bbNo", str(bb.get("no") or ""))
            feat.setAttribute("tip", bb.get("tip") or "")
            feat.setAttribute("kat", bb.get("kat") or "")
            feat.setAttribute("giris", bb.get("giris") or "")
            feat.setAttribute("nitelik", bb.get("nitelik") or "")
            feat.setAttribute("durum", str(bb.get("durum") or ""))
            yeni_kayitlar.append(feat)

    if yeni_kayitlar:
        bb_layer.dataProvider().addFeatures(yeni_kayitlar)
    
    bb_layer.commitChanges()
    bb_layer.triggerRepaint()
    return True


KATMAN_ADRES_ADI = "TKGM Adresler"

def _get_or_create_adres_layer() -> QgsVectorLayer:
    """Mevcut adres katmanını bulur, yoksa yeni (Point) oluşturur."""
    for layer in QgsProject.instance().mapLayers().values():
        if layer.name() == KATMAN_ADRES_ADI:
            return layer

    layer = QgsVectorLayer("Point?crs=EPSG:4326", KATMAN_ADRES_ADI, "memory")
    pr = layer.dataProvider()
    pr.addAttributes([
        QgsField("il", TYPE_STRING),
        QgsField("ilce", TYPE_STRING),
        QgsField("mahalle", TYPE_STRING),
        QgsField("yol", TYPE_STRING),
        QgsField("kapiNo", TYPE_STRING),
        QgsField("tamAdres", TYPE_STRING),
    ])
    layer.updateFields()

    # Stil
    try:
        from qgis.core import QgsMarkerSymbol
        sembol = QgsMarkerSymbol.createSimple({'color': '227,26,28', 'size': '4', 'outline_color': 'white'})
        if hasattr(layer, "renderer") and layer.renderer():
            layer.renderer().setSymbol(sembol)
    except Exception:
        pass  # nosec B110

    # Etiket
    metin_fmt = QgsTextFormat()
    metin_fmt.setFont(QFont("Arial", 9))
    metin_fmt.setColor(QColor(40, 40, 40))
    tampon = QgsTextBufferSettings()
    tampon.setEnabled(True)
    tampon.setSize(1.0)
    tampon.setColor(QColor(255, 255, 255, 200))
    metin_fmt.setBuffer(tampon)

    pal = QgsPalLayerSettings()
    pal.setFormat(metin_fmt)
    pal.fieldName = "kapiNo"
    pal.isExpression = False
    
    # QgsPalLayerSettings.Placement.AroundPoint için dinamik enum:
    try:
        pal.placement = getattr(getattr(QgsPalLayerSettings, "Placement", QgsPalLayerSettings), "AroundPoint")
    except Exception:
        pass
        
    pal.enabled = True
    layer.setLabeling(QgsVectorLayerSimpleLabeling(pal))
    layer.setLabelsEnabled(True)

    QgsProject.instance().addMapLayer(layer)
    return layer

_ADRES_PREVIEW_RUBBERBAND = None


def adres_onizleme_temizle() -> None:
    """Mevcut adres önizleme vurgusunu haritadan temizler."""
    global _ADRES_PREVIEW_RUBBERBAND
    if _ADRES_PREVIEW_RUBBERBAND is not None:
        try:
            _ADRES_PREVIEW_RUBBERBAND.reset()
            _ADRES_PREVIEW_RUBBERBAND.hide()
        except Exception:
            pass
        _ADRES_PREVIEW_RUBBERBAND = None


def _dict_to_qgs_geometry(geom_dict: dict):
    """GeoJSON sözlüğünü QgsGeometry nesnesine dönüştürür."""
    if not geom_dict:
        return None
    try:
        from qgis.core import QgsGeometry, QgsPointXY
        gt = geom_dict.get("type")
        coords = geom_dict.get("coordinates")
        if not gt or not coords:
            return None

        if gt == "Point":
            return QgsGeometry.fromPointXY(QgsPointXY(float(coords[0]), float(coords[1])))
        elif gt == "Polygon":
            points = [QgsPointXY(float(pt[0]), float(pt[1])) for pt in coords[0]]
            return QgsGeometry.fromPolygonXY([points])
        elif gt == "MultiPolygon":
            multi_poly = []
            for poly in coords:
                points = [QgsPointXY(float(pt[0]), float(pt[1])) for pt in poly[0]]
                multi_poly.append([points])
            return QgsGeometry.fromMultiPolygonXY(multi_poly)
        elif gt == "LineString":
            points = [QgsPointXY(float(pt[0]), float(pt[1])) for pt in coords]
            return QgsGeometry.fromPolylineXY(points)
        elif gt == "MultiLineString":
            multi_line = []
            for line in coords:
                multi_line.append([QgsPointXY(float(pt[0]), float(pt[1])) for pt in line])
            return QgsGeometry.fromMultiPolylineXY(multi_line)
    except Exception:
        pass
    return None


def adres_onizleme_goster(canvas, geom_dict: dict) -> None:
    """GeoJSON sözlüğünden haritada önizleme rubberband oluşturur ve önceki önizlemeyi temizler."""
    global _ADRES_PREVIEW_RUBBERBAND
    adres_onizleme_temizle()

    if not canvas or not geom_dict:
        return

    try:
        from qgis.gui import QgsRubberBand
        from qgis.core import QgsCoordinateReferenceSystem, QgsWkbTypes
        from qgis.PyQt.QtGui import QColor

        qgs_geom = _dict_to_qgs_geometry(geom_dict)
        if not qgs_geom or qgs_geom.isEmpty():
            return

        g_type = qgs_geom.type()
        rb = QgsRubberBand(canvas, g_type)

        # Şık mavi/turkuaz önizleme stili
        rb.setColor(QColor(0, 150, 255, 65))
        rb.setStrokeColor(QColor(0, 120, 220, 230))
        rb.setWidth(2)

        if hasattr(QgsWkbTypes, "PointGeometry") and g_type == QgsWkbTypes.PointGeometry:
            rb.setIconSize(10)
        elif g_type == 0:
            rb.setIconSize(10)

        crs_src = QgsCoordinateReferenceSystem("EPSG:4326")
        rb.setToGeometry(qgs_geom, crs_src)
        rb.show()
        _ADRES_PREVIEW_RUBBERBAND = rb
    except Exception:
        pass


def adres_noktasi_katmana_ekle(lat: float, lng: float, adres_bilgisi: dict) -> QgsVectorLayer:
    """Adres bilgisini haritaya ve öznitelik tablosuna ekler."""
    adres_onizleme_temizle()
    layer = _get_or_create_adres_layer()

    feat = QgsFeature(layer.fields())
    feat.setGeometry(QgsGeometry.fromPointXY(QgsPointXY(lng, lat)))

    feat.setAttribute("il", adres_bilgisi.get("il", ""))
    feat.setAttribute("ilce", adres_bilgisi.get("ilce", ""))
    feat.setAttribute("mahalle", adres_bilgisi.get("mahalle", ""))
    feat.setAttribute("yol", adres_bilgisi.get("yol", ""))
    feat.setAttribute("kapiNo", adres_bilgisi.get("numarataj", ""))
    feat.setAttribute("tamAdres", adres_bilgisi.get("tamAdres", ""))

    layer.dataProvider().addFeatures([feat])
    layer.updateExtents()
    layer.triggerRepaint()

    import qgis.utils
    canvas = qgis.utils.iface.mapCanvas() if qgis.utils.iface else None

    if canvas:
        rect = QgsRectangle(lng - 0.001, lat - 0.001, lng + 0.001, lat + 0.001)
        if layer.crs() != canvas.mapSettings().destinationCrs():
            from qgis.core import QgsCoordinateTransform
            xform = QgsCoordinateTransform(layer.crs(), canvas.mapSettings().destinationCrs(), QgsProject.instance())
            try:
                rect = xform.transformBoundingBox(rect)
            except Exception:
                pass

        canvas.setExtent(rect)
        canvas.refresh()

    return layer


def geojson_geometriye_zoom_yap(canvas, geom_dict: dict) -> None:
    """GeoJSON sözlük verisini kullanarak haritada o kapsama zoom yapar ve canlı önizleme çizer."""
    if not canvas or not geom_dict:
        adres_onizleme_temizle()
        return

    try:
        from qgis.core import QgsCoordinateReferenceSystem, QgsCoordinateTransform, QgsProject

        qgs_geom = _dict_to_qgs_geometry(geom_dict)
        if not qgs_geom or qgs_geom.isEmpty():
            adres_onizleme_temizle()
            return

        # Önizlemeyi göster (öncekileri otomatik temizler)
        adres_onizleme_goster(canvas, geom_dict)

        rect = qgs_geom.boundingBox()
        if rect.isEmpty():
            center = qgs_geom.asPoint()
            rect = rect.fromCenterAndSize(center, 0.002, 0.002)
        else:
            rect.scale(1.1)

        # CRS dönüşümü (API her zaman EPSG:4326 dönüyor)
        crs_src = QgsCoordinateReferenceSystem("EPSG:4326")
        crs_dest = canvas.mapSettings().destinationCrs()
        if crs_src != crs_dest:
            xform = QgsCoordinateTransform(crs_src, crs_dest, QgsProject.instance())
            rect = xform.transformBoundingBox(rect)

        canvas.setExtent(rect)
        canvas.refresh()
    except Exception:
        pass


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
