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
)
try:
    from qgis.PyQt.QtCore import QVariant
except ImportError:
    class QVariant:
        pass

try:
    from qgis.PyQt.QtCore import QMetaType
    TYPE_STRING = QMetaType.Type.QString
    TYPE_INT = QMetaType.Type.Int
    TYPE_DOUBLE = QMetaType.Type.Double
except AttributeError:
    # Older PyQt5
    TYPE_STRING = QVariant.String
    TYPE_INT = QVariant.Int
    TYPE_DOUBLE = QVariant.Double

from qgis.PyQt.QtGui import QColor, QFont


KATMAN_ADI = "TKGM Parseller"


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
    return layer


def parsel_katmana_ekle(parsel: dict) -> None:
    """Parsel bilgisini QGIS katmanına Feature olarak ekler."""
    layer = _get_or_create_layer()

    koordinatlar = parsel.get("koordinatlar") or []
    if not koordinatlar:
        return

    # Polygon oluştur
    points = [QgsPointXY(k["lng"], k["lat"]) for k in koordinatlar]
    geom = QgsGeometry.fromPolygonXY([points])

    feat = QgsFeature(layer.fields())
    feat.setGeometry(geom)
    feat.setAttributes([
        str(parsel.get("mahalleKodu") or ""),
        int(parsel.get("adaNo") or 0),
        int(parsel.get("parselNo") or 0),
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
