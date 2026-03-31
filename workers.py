"""
Arka plan iş parçacıkları — API çağrılarını UI'yı dondurmadan yapar.
"""

from qgis.PyQt.QtCore import QThread, pyqtSignal


class IlWorker(QThread):
    finished = pyqtSignal(list)
    error = pyqtSignal(str)

    def run(self):
        try:
            from .tkgm_api import get_il_listesi
            self.finished.emit(get_il_listesi())
        except Exception as e:
            self.error.emit(str(e))


class IlceWorker(QThread):
    finished = pyqtSignal(list)
    error = pyqtSignal(str)

    def __init__(self, il_kodu):
        super().__init__()
        self.il_kodu = il_kodu

    def run(self):
        try:
            from .tkgm_api import get_ilce_listesi
            self.finished.emit(get_ilce_listesi(self.il_kodu))
        except Exception as e:
            self.error.emit(str(e))


class MahalleWorker(QThread):
    finished = pyqtSignal(list)
    error = pyqtSignal(str)

    def __init__(self, ilce_kodu):
        super().__init__()
        self.ilce_kodu = ilce_kodu

    def run(self):
        try:
            from .tkgm_api import get_mahalle_listesi
            self.finished.emit(get_mahalle_listesi(self.ilce_kodu))
        except Exception as e:
            self.error.emit(str(e))


class ParselWorker(QThread):
    finished = pyqtSignal(dict)
    error = pyqtSignal(str)

    def __init__(self, mahalle_kodu, ada_no, parsel_no):
        super().__init__()
        self.mahalle_kodu = mahalle_kodu
        self.ada_no = ada_no
        self.parsel_no = parsel_no

    def run(self):
        try:
            from .tkgm_api import get_parsel
            self.finished.emit(get_parsel(self.mahalle_kodu, self.ada_no, self.parsel_no))
        except Exception as e:
            self.error.emit(str(e))


class ParselKoordinatWorker(QThread):
    finished = pyqtSignal(dict)
    error = pyqtSignal(str)

    def __init__(self, lat, lng):
        super().__init__()
        self.lat = lat
        self.lng = lng

    def run(self):
        try:
            from .tkgm_api import get_parsel_koordinat
            self.finished.emit(get_parsel_koordinat(self.lat, self.lng))
        except Exception as e:
            self.error.emit(str(e))


class ParselBlokListesiWorker(QThread):
    finished = pyqtSignal(list)
    error = pyqtSignal(str)

    def __init__(self, mahalle_kodu, ada_no, parsel_no):
        super().__init__()
        self.mahalle_kodu = mahalle_kodu
        self.ada_no = ada_no
        self.parsel_no = parsel_no

    def run(self):
        try:
            from .tkgm_api import get_parsel_blok_listesi
            self.finished.emit(get_parsel_blok_listesi(self.mahalle_kodu, self.ada_no, self.parsel_no))
        except Exception as e:
            self.error.emit(str(e))


class ParselBlokVeBBWorker(QThread):
    finished = pyqtSignal(list)
    error = pyqtSignal(str)

    def __init__(self, mahalle_kodu, ada_no, parsel_no):
        super().__init__()
        self.mahalle_kodu = mahalle_kodu
        self.ada_no = ada_no
        self.parsel_no = parsel_no

    def run(self):
        try:
            from .tkgm_api import get_parsel_blok_ve_bb_listesi
            self.finished.emit(get_parsel_blok_ve_bb_listesi(self.mahalle_kodu, self.ada_no, self.parsel_no))
        except Exception as e:
            self.error.emit(str(e))
