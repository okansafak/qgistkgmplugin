"""
TKGM Parsel Sorgulama — Panel Controller
Arayüz tasarımı ui_tkgm_panel.py modülündedir.
Bu dosya yalnızca sinyal-slot bağlantılarını ve iş mantığını içerir.
"""

from qgis.PyQt.QtWidgets import (
    QDockWidget, QMessageBox, QWidget, QVBoxLayout, QHBoxLayout,
    QToolButton, QLabel, QFrame, QTableWidget, QTableWidgetItem,
    QAbstractItemView, QHeaderView,
)
from qgis.PyQt.QtCore import Qt

from .ui_tkgm_panel import Ui_TKGMPanel
from .workers import (
    IlWorker, IlceWorker, MahalleWorker,
    ParselWorker, ParselKoordinatWorker, ParselBlokVeBBWorker,
)
from .layer_manager import parsel_katmana_ekle, bagimsiz_bolumleri_katmana_ekle, parsele_zoom_yap
from .map_tool import ParselTiklamaAraci


def _get_class_enum(cls, scope, name):
    if hasattr(cls, scope):
        enum_scope = getattr(cls, scope)
        if hasattr(enum_scope, name):
            return getattr(enum_scope, name)
    if hasattr(cls, name):
        return getattr(cls, name)
    return 0


ToolButtonTextBesideIcon = _get_class_enum(Qt, "ToolButtonStyle", "ToolButtonTextBesideIcon")
RightArrow = _get_class_enum(Qt, "ArrowType", "RightArrow")
DownArrow = _get_class_enum(Qt, "ArrowType", "DownArrow")

NoEditTriggers = _get_class_enum(QAbstractItemView, "EditTrigger", "NoEditTriggers")
SelectRows = _get_class_enum(QAbstractItemView, "SelectionBehavior", "SelectRows")
SingleSelection = _get_class_enum(QAbstractItemView, "SelectionMode", "SingleSelection")

ResizeToContents = _get_class_enum(QHeaderView, "ResizeMode", "ResizeToContents")
Stretch = _get_class_enum(QHeaderView, "ResizeMode", "Stretch")


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
        self._son_bina_bb_sorgu = None

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
        self.btn_bina_bb.clicked.connect(self._on_bina_bb_sorgula)
        self.btn_tikla_ac.toggled.connect(self._on_tikla_toggle)
        self.btn_zoom.clicked.connect(self._on_zoom)

    # ──────────────────────────────────── İdari Birim Yükleme ─────────────────
    def _load_iller(self):
        self._durum("İller yükleniyor...")
        w = IlWorker()
        w.finished.connect(self._on_iller_yuklendi)
        w.error.connect(lambda e: self._hata(self._kullanici_hata_mesaji(e, "İl listesi alınamadı")))
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
        w.error.connect(lambda e: self._hata(self._kullanici_hata_mesaji(e, "İlçe listesi alınamadı")))
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
        w.error.connect(lambda e: self._hata(self._kullanici_hata_mesaji(e, "Mahalle listesi alınamadı")))
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
        self._clear_bina_bb_alani()
        self.grp_bina_bb.setVisible(False)
        self.lbl_bina_bb_ozet.setText("")

        # Sonuç panelini doldur
        alan = parsel.get("alan") or 0
        self._sonuc_etiketler["il"].setText(parsel.get("ilAd") or "—")
        self._sonuc_etiketler["ilce"].setText(parsel.get("ilceAd") or "—")
        self._sonuc_etiketler["mahalle"].setText(parsel.get("mahalleAd") or "—")
        ada_no = parsel.get("adaNo")
        parsel_no = parsel.get("parselNo")
        self._sonuc_etiketler["ada"].setText(
            "—" if ada_no is None or str(ada_no).strip() == "" else str(ada_no)
        )
        self._sonuc_etiketler["parsel"].setText(
            "—" if parsel_no is None or str(parsel_no).strip() == "" else str(parsel_no)
        )
        self._sonuc_etiketler["alan"].setText(
            f"{alan:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
        )
        self._sonuc_etiketler["nitelik"].setText(parsel.get("nitelik") or "—")
        self._sonuc_etiketler["pafta"].setText(parsel.get("pafta") or "—")

        self.grp_sonuc.setVisible(True)

        # Katmana ekle
        try:
            eklendi = parsel_katmana_ekle(parsel)
            if eklendi:
                self.lbl_katman.setText("✅ Katmana eklendi: 'TKGM Parseller'")
            else:
                self.lbl_katman.setText("ℹ Parsel zaten katmanda: 'TKGM Parseller'")
            parsele_zoom_yap(self.canvas, parsel)
        except Exception as e:
            self.lbl_katman.setText(f"⚠ Katman hatası: {e}")

        ada_no = parsel.get("adaNo", "")
        prs = parsel.get("parselNo", "")
        self._durum(f"✅ Bulundu — Ada: {ada_no}, Parsel: {prs}")

    def _on_parsel_hatasi(self, hata: str):
        self.btn_sorgula.setEnabled(True)
        self._hata(self._kullanici_hata_mesaji(hata, "Parsel bulunamadı"))

    def _on_bina_bb_sorgula(self):
        mahalle_kodu = self.cmb_mahalle.currentData()
        ada_no = self.txt_ada.text().strip()
        parsel_no = self.txt_parsel.text().strip()

        # Son başarılı sorgu varsa otomatik kullan (haritadan tıklama için de geçerli)
        if self._son_parsel:
            son_mahalle_kodu = self._son_parsel.get("mahalleKodu")
            son_ada_no = self._son_parsel.get("adaNo")
            son_parsel_no = self._son_parsel.get("parselNo")

            if son_mahalle_kodu is not None and str(son_mahalle_kodu).strip() != "":
                mahalle_kodu = son_mahalle_kodu
            if son_ada_no is not None and str(son_ada_no).strip() != "":
                ada_no = str(son_ada_no).strip()
            if son_parsel_no is not None and str(son_parsel_no).strip() != "":
                parsel_no = str(son_parsel_no).strip()

        if not mahalle_kodu or not ada_no or not parsel_no:
            self._hata("Bina/BB listesi için önce parsel seçin veya mahalle/ada/parsel girin")
            return

        try:
            ada_no_int = int(ada_no)
            parsel_no_int = int(parsel_no)
        except ValueError:
            self._hata("Ada ve Parsel sadece sayısal olmalıdır")
            return

        self._son_bina_bb_sorgu = {
            "mahalleKodu": str(mahalle_kodu),
            "adaNo": ada_no_int,
            "parselNo": parsel_no_int,
        }

        self._durum("Bina/BB listesi sorgulanıyor...")
        self.btn_bina_bb.setEnabled(False)
        self._clear_bina_bb_alani()

        w = ParselBlokVeBBWorker(mahalle_kodu, ada_no, parsel_no)
        w.finished.connect(self._on_bina_bb_listesi_geldi)
        w.error.connect(self._on_bina_bb_hatasi)
        self._workers.append(w)
        w.start()

    def _on_bina_bb_listesi_geldi(self, bloklar: list):
        self.btn_bina_bb.setEnabled(True)

        if not bloklar:
            self.grp_bina_bb.setVisible(True)
            self.lbl_bina_bb_ozet.setText("Bu parsel için bina/blok kaydı bulunamadı.")
            self._durum("Bina/BB listesi boş")
            return

        self.grp_bina_bb.setVisible(True)
        toplam_bb = 0
        for blok in bloklar:
            toplam_bb += len(blok.get("bagimsizBolumler") or [])
            self._akordiyon_blok_ekle(blok)

        self.lbl_bina_bb_ozet.setText(
            f"Toplam {len(bloklar)} blok bulundu. Toplam {toplam_bb} bağımsız bölüm listelendi."
        )

        if self._son_parsel:
            parsel_ref = self._son_parsel
        else:
            parsel_ref = self._son_bina_bb_sorgu or {}

        try:
            eklenen_bb, atlanan_bb = bagimsiz_bolumleri_katmana_ekle(parsel_ref, bloklar)
            self.lbl_bina_bb_ozet.setText(
                f"Toplam {len(bloklar)} blok bulundu. Toplam {toplam_bb} bağımsız bölüm listelendi. "
                f"Tabloya eklenen: {eklenen_bb}, mükerrer atlanan: {atlanan_bb}."
            )
        except Exception as e:
            self._hata(f"Bağımsız bölüm kayıt hatası: {e}")

        self._durum(f"Bina/BB listesi alındı ({len(bloklar)} kayıt)")

    def _on_bina_bb_hatasi(self, hata: str):
        self.btn_bina_bb.setEnabled(True)
        self._hata(self._kullanici_hata_mesaji(hata, "Bina/BB sorgusu başarısız"))

    def _clear_bina_bb_alani(self):
        if not hasattr(self, "bina_bb_layout"):
            return
        while self.bina_bb_layout.count() > 1:
            item = self.bina_bb_layout.takeAt(0)
            w = item.widget()
            if w:
                w.deleteLater()

    def _akordiyon_blok_ekle(self, blok: dict):
        blok_no = str(blok.get("blok") or "-")
        tip = blok.get("zeminKmdurum") or "-"
        bb_sayi = blok.get("bagimsizBolumSayisi") or 0
        bb_listesi = blok.get("bagimsizBolumler") or []

        kart = QWidget()
        kart_lay = QVBoxLayout(kart)
        kart_lay.setContentsMargins(0, 0, 0, 0)
        kart_lay.setSpacing(4)

        ust = QFrame()
        ust.setStyleSheet("QFrame { background:#eef3f8; border:1px solid #d0dbe7; border-radius:4px; }")
        ust_lay = QHBoxLayout(ust)
        ust_lay.setContentsMargins(8, 4, 8, 4)

        btn = QToolButton()
        btn.setToolButtonStyle(ToolButtonTextBesideIcon)
        btn.setArrowType(RightArrow)
        btn.setCheckable(True)
        btn.setChecked(False)
        btn.setText(f"Blok {blok_no} | Bina Nitelik: {tip} | Bağımsız Bölüm: {bb_sayi}")
        btn.setStyleSheet("QToolButton { font-weight: 600; color:#243b53; border:none; text-align:left; }")
        ust_lay.addWidget(btn)
        kart_lay.addWidget(ust)

        icerik = QWidget()
        icerik_lay = QVBoxLayout(icerik)
        icerik_lay.setContentsMargins(0, 0, 0, 0)
        icerik_lay.setSpacing(0)

        tablo = QTableWidget()
        tablo.setColumnCount(4)
        tablo.setHorizontalHeaderLabels(["Kat", "Giriş", "Nitelik", "BB No"])
        tablo.setEditTriggers(NoEditTriggers)
        tablo.setSelectionBehavior(SelectRows)
        tablo.setSelectionMode(SingleSelection)
        tablo.setAlternatingRowColors(True)
        tablo.verticalHeader().setVisible(False)
        tablo.verticalHeader().setDefaultSectionSize(28)
        tablo.horizontalHeader().setSectionResizeMode(0, ResizeToContents)
        tablo.horizontalHeader().setSectionResizeMode(1, ResizeToContents)
        tablo.horizontalHeader().setSectionResizeMode(2, Stretch)
        tablo.horizontalHeader().setSectionResizeMode(3, ResizeToContents)

        tablo.setRowCount(len(bb_listesi))
        for row, item in enumerate(bb_listesi):
            tablo.setItem(row, 0, QTableWidgetItem(item.get("kat") or "-"))
            tablo.setItem(row, 1, QTableWidgetItem(item.get("giris") or "-"))
            tablo.setItem(row, 2, QTableWidgetItem(item.get("nitelik") or "-"))
            tablo.setItem(row, 3, QTableWidgetItem(item.get("no") or "-"))

        gorunen_satir = max(8, min(len(bb_listesi), 12))
        if len(bb_listesi) == 0:
            gorunen_satir = 1
        baslik_h = tablo.horizontalHeader().height() + 4
        tablo.setMinimumHeight(baslik_h + (gorunen_satir * tablo.verticalHeader().defaultSectionSize()))

        icerik_lay.addWidget(tablo)
        icerik.setVisible(False)
        kart_lay.addWidget(icerik)

        def _toggle(aktif):
            icerik.setVisible(aktif)
            btn.setArrowType(DownArrow if aktif else RightArrow)

        btn.toggled.connect(_toggle)
        self.bina_bb_layout.insertWidget(self.bina_bb_layout.count() - 1, kart)

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

    def _kullanici_hata_mesaji(self, hata: str, varsayilan: str) -> str:
        temiz_hata = (hata or "").strip()
        hata_lower = temiz_hata.lower()

        if "günlük sorgu limitini aştınız" in hata_lower or "gunluk sorgu limitini astiniz" in hata_lower:
            return "Günlük sorgu limitini aştınız."

        # TKGM limit dolumu bazı uçlarda sadece HTTP 403 dönebiliyor.
        if "http 403" in hata_lower:
            return "Günlük sorgu limitini aştınız."

        if "http " in hata_lower or "http error" in hata_lower:
            return varsayilan

        return temiz_hata or varsayilan

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
