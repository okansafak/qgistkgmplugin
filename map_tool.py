"""
Harita tıklama aracı — kullanıcı haritaya tıkladığında koordinatı yakalar.
"""

from qgis.gui import QgsMapTool
from qgis.core import QgsCoordinateReferenceSystem, QgsCoordinateTransform, QgsProject
from qgis.PyQt.QtCore import pyqtSignal
from qgis.PyQt.QtGui import QCursor
from qgis.PyQt.QtCore import Qt


class ParselTiklamaAraci(QgsMapTool):
    """Haritaya tıklandığında WGS84 koordinatını yayar."""

    koordinat_secildi = pyqtSignal(float, float)  # lat, lng

    def __init__(self, canvas):
        super().__init__(canvas)
        self.canvas = canvas
        self.setCursor(QCursor(Qt.CrossCursor))

    def canvasReleaseEvent(self, event):
        point = self.toMapCoordinates(event.pos())

        # Harita CRS'ini WGS84'e dönüştür
        crs_harita = self.canvas.mapSettings().destinationCrs()
        crs_wgs84 = QgsCoordinateReferenceSystem("EPSG:4326")
        transform = QgsCoordinateTransform(crs_harita, crs_wgs84, QgsProject.instance())
        point_wgs84 = transform.transform(point)

        self.koordinat_secildi.emit(point_wgs84.y(), point_wgs84.x())  # lat, lng
