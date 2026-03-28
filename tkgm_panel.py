"""
TKGM Parsel Sorgulama — Panel Controller
Arayüz tasarımı ui_tkgm_panel.py modülündedir.
Bu dosya yalnızca sinyal-slot bağlantılarını ve iş mantığını içerir.
"""

from qgis.PyQt.QtWidgets import QDockWidget, QMessageBox
from qgis.PyQt.QtCore import Qt

from .ui_tkgm_panel import Ui_TKGMPanel
from .workers import (
    IlWorker, IlceWorker, MahalleWorker,
    ParselWorker, ParselKoordinatWorker,
)
from .layer_manager import parsel_katmana_ekle, parsele_zoom_yap
from .map_tool import ParselTiklamaAraci


# ─── Türkçe alfabetik sıralama yardımcısı ────────────────────────────────────
_SIRALA_CACHE = None


def _tr_sirala_map():
    global _SIRALA_CACHE
    if _SIRALA_CACHE is not None:
        return _SIRALA_CACHE
    tr_alfabe = "AaBbCcÇçDdEeFfGgĞğHhIıİiJjKkLlMmNnOoÖöPpRrSsŞşTtUuÜüVvYyZz"
    _SIRALA_CACHE = {ch: idx for idx, ch in enumerate(tr_alfabe)}
    return _SIRALA_CACHE


def _tr_sort_key(metin: str):
    """Türkçe alfabesine göre sıralama anahtarı üretir."""
    alfabe = _tr_sirala_map()
    return [alfabe.get(c, 9999) for c in metin]


# ─── Ana Panel Sınıfı ────────────────────────────────────────────────────────
class TKGMPanel(QDockWidget, Ui_TKGMPanel):
    """
    TKGM Parsel Sorgulama paneli.
    Ui_TKGMPanel → arayüz öğelerini oluşturur.
    Bu sınıf → sinyal/slot bağlantıları ve iş mantığını yürütür.
    """

    def __init__(self, iface):
        super().__init__("TKGM Parsel Sorgulama")
        self.iface = iface
        self.canvas = iface.mapCanvas()

        # Aktif worker referansları (GC'den korunmak için)
        self._workers = []

        # Harita tıklama aracı
        self._onceki_arac = None
        self._tiklama_araci = None

        # Son parsel verisi
        self._son_parsel = None

        # Arayüzü inşa et (Ui_TKGMPanel'den)
        self.setup_ui(self)

        # Sinyal-slot bağlantıları
        self._connect_signals()

        # İl listesini yükle
        self._load_iller()

    # ─────────────────────────────────── Sinyal Bağlantıları ──────────────────
    def _connect_signals(self):
        """Tüm sinyal-slot bağlantılarını tek bir yerde kurar."""
        self.cmb_il.currentIndexChanged.connect(self._on_il_degisti)
        self.cmb_ilce.currentIndexChanged.connect(self._on_ilce_degisti)
        self.btn_sorgula.clicked.connect(self._on_sorgula)
        self.btn_tikla_ac.toggled.connect(self._on_tikla_toggle)
        self.btn_zoom.clicked.connect(self._on_zoom)

    # ──────────────────────────────────── İdari Birim Yükleme ─────────────────
    def _load_iller(self):
        self._durum("İller yükleniyor...")
        w = IlWorker()
        w.finished.connect(self._on_iller_yuklendi)
        w.error.connect(lambda e: self._hata(f"İl listesi hatası: {e}"))
        self._workers.append(w)
        w.start()

    def _on_iller_yuklendi(self, iller):
        self.cmb_il.clear()
        self.cmb_il.addItem("— İl seçin —", None)
        for il in sorted(iller, key=lambda x: _tr_sort_key(x.get("ad", ""))):
            self.cmb_il.addItem(il["ad"], il["id"])
        self.cmb_il.setEnabled(True)
        self.cmb_il.setPlaceholderText("")
        self._durum(f"{len(iller)} il yüklendi")

    def _on_il_degisti(self, idx):
        self.cmb_ilce.clear()
        self.cmb_mahalle.clear()
        self.cmb_ilce.setEnabled(False)
        self.cmb_mahalle.setEnabled(False)

        il_kodu = self.cmb_il.currentData()
        if not il_kodu:
            return

        self._durum("İlçeler yükleniyor...")
        self.cmb_ilce.addItem("Yükleniyor...", None)
        w = IlceWorker(il_kodu)
        w.finished.connect(self._on_ilceler_yuklendi)
        w.error.connect(lambda e: self._hata(f"İlçe hatası: {e}"))
        self._workers.append(w)
        w.start()

    def _on_ilceler_yuklendi(self, ilceler):
        self.cmb_ilce.clear()
        self.cmb_ilce.addItem("— İlçe seçin —", None)
        for ilce in sorted(ilceler, key=lambda x: _tr_sort_key(x.get("ilceAdi", ""))):
            self.cmb_ilce.addItem(ilce["ilceAdi"], ilce["ilceKodu"])
        self.cmb_ilce.setEnabled(True)
        self._durum(f"{len(ilceler)} ilçe yüklendi")

    def _on_ilce_degisti(self, idx):
        self.cmb_mahalle.clear()
        self.cmb_mahalle.setEnabled(False)

        ilce_kodu = self.cmb_ilce.currentData()
        if not ilce_kodu:
            return

        self._durum("Mahalleler yükleniyor...")
        self.cmb_mahalle.addItem("Yükleniyor...", None)
        w = MahalleWorker(ilce_kodu)
        w.finished.connect(self._on_mahalleler_yuklendi)
        w.error.connect(lambda e: self._hata(f"Mahalle hatası: {e}"))
        self._workers.append(w)
        w.start()

    def _on_mahalleler_yuklendi(self, mahalleler):
        self.cmb_mahalle.clear()
        self.cmb_mahalle.addItem("— Mahalle seçin —", None)
        for mah in sorted(mahalleler, key=lambda x: _tr_sort_key(x.get("mahalleAdi", ""))):
            self.cmb_mahalle.addItem(mah["mahalleAdi"], mah["mahalleKodu"])
        self.cmb_mahalle.setEnabled(True)
        self._durum(f"{len(mahalleler)} mahalle yüklendi")

    # ──────────────────────────────────── Parsel Sorgulama ────────────────────
    def _on_sorgula(self):
        mah_kodu = self.cmb_mahalle.currentData()
        ada = self.txt_ada.text().strip()
        parsel = self.txt_parsel.text().strip()

        if not mah_kodu:
            self._hata("Lütfen il → ilçe → mahalle seçiniz")
            return
        if not ada or not parsel:
            self._hata("Ada ve Parsel numarası giriniz")
            return

        self._durum("Parsel sorgulanıyor...")
        self.btn_sorgula.setEnabled(False)

        w = ParselWorker(mah_kodu, ada, parsel)
        w.finished.connect(self._on_parsel_geldi)
        w.error.connect(self._on_parsel_hatasi)
        self._workers.append(w)
        w.start()

    def _sorgu_koordinat(self, lat, lng):
        self._durum(f"Koordinat sorgulanıyor: {lat:.6f}, {lng:.6f}")
        w = ParselKoordinatWorker(lat, lng)
        w.finished.connect(self._on_parsel_geldi)
        w.error.connect(self._on_parsel_hatasi)
        self._workers.append(w)
        w.start()

    def _on_parsel_geldi(self, parsel: dict):
        self.btn_sorgula.setEnabled(True)
        self._son_parsel = parsel

        # Sonuç panelini doldur
        alan = parsel.get("alan") or 0
        self._sonuc_etiketler["il"].setText(parsel.get("ilAd") or "—")
        self._sonuc_etiketler["ilce"].setText(parsel.get("ilceAd") or "—")
        self._sonuc_etiketler["mahalle"].setText(parsel.get("mahalleAd") or "—")
        self._sonuc_etiketler["ada"].setText(str(parsel.get("adaNo") or "—"))
        self._sonuc_etiketler["parsel"].setText(str(parsel.get("parselNo") or "—"))
        self._sonuc_etiketler["alan"].setText(
            f"{alan:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
        )
        self._sonuc_etiketler["nitelik"].setText(parsel.get("nitelik") or "—")
        self._sonuc_etiketler["pafta"].setText(parsel.get("pafta") or "—")

        self.grp_sonuc.setVisible(True)

        # Katmana ekle
        try:
            parsel_katmana_ekle(parsel)
            self.lbl_katman.setText("✅ Katmana eklendi: 'TKGM Parseller'")
            parsele_zoom_yap(self.canvas, parsel)
        except Exception as e:
            self.lbl_katman.setText(f"⚠ Katman hatası: {e}")

        ada_no = parsel.get("adaNo", "")
        prs = parsel.get("parselNo", "")
        self._durum(f"✅ Bulundu — Ada: {ada_no}, Parsel: {prs}")

    def _on_parsel_hatasi(self, hata: str):
        self.btn_sorgula.setEnabled(True)
        self._hata(f"Parsel bulunamadı: {hata}")

    # ──────────────────────────────────── Harita Tıklama Aracı ────────────────
    def _on_tikla_toggle(self, aktif: bool):
        if aktif:
            self.btn_tikla_ac.setText("🛑  Tıklama Modunu Kapat")
            self._onceki_arac = self.canvas.mapTool()
            self._tiklama_araci = ParselTiklamaAraci(self.canvas)
            self._tiklama_araci.koordinat_secildi.connect(self._sorgu_koordinat)
            self.canvas.setMapTool(self._tiklama_araci)
            self._durum("Haritaya tıklayın...")
        else:
            self.btn_tikla_ac.setText("🎯  Tıklama Modunu Aç")
            if self._tiklama_araci:
                try:
                    self._tiklama_araci.koordinat_secildi.disconnect()
                except Exception:
                    pass
            if self._onceki_arac:
                self.canvas.setMapTool(self._onceki_arac)
            else:
                self.canvas.unsetMapTool(self._tiklama_araci)
            self._tiklama_araci = None
            self._durum("Hazır")

    # ──────────────────────────────────── Zoom ────────────────────────────────
    def _on_zoom(self):
        if self._son_parsel:
            parsele_zoom_yap(self.canvas, self._son_parsel)

    # ──────────────────────────────────── Yardımcı ────────────────────────────
    def _durum(self, mesaj: str):
        self.lbl_durum.setText(mesaj)

    def _hata(self, mesaj: str):
        self.lbl_durum.setText(f"⚠ {mesaj}")
        QMessageBox.warning(self, "TKGM Parsel", mesaj)

    def hideEvent(self, event):
        if self.btn_tikla_ac.isChecked():
            self.btn_tikla_ac.setChecked(False)
        super().hideEvent(event)

    def closeEvent(self, event):
        if self.btn_tikla_ac.isChecked():
            self.btn_tikla_ac.setChecked(False)
        super().closeEvent(event)
