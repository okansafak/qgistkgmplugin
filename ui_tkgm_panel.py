"""
TKGM Parsel Sorgulama — Arayüz Tasarım Modülü (UI)
Tüm görsel öğelerin (widget) oluşturulması ve düzenlenmesi burada yapılır.
Controller mantığı tkgm_panel.py içindedir.
"""

from qgis.PyQt.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QComboBox, QLineEdit, QPushButton,
    QGroupBox, QGridLayout, QFrame, QScrollArea,
    QTabWidget,
)
from qgis.PyQt.QtCore import Qt
from qgis.PyQt.QtGui import QFont, QIcon
from qgis.core import QgsApplication

def _get_qt_flag(scope, name, fallback_scope=None):
    if hasattr(Qt, scope):
        s = getattr(Qt, scope)
        if hasattr(s, name):
            return getattr(s, name)
    if fallback_scope and hasattr(Qt, fallback_scope):
        s = getattr(Qt, fallback_scope)
        if hasattr(s, name):
            return getattr(s, name)
    if hasattr(Qt, name):
        return getattr(Qt, name)
    return 0


def _get_qframe_shape(name):
    if hasattr(QFrame, "Shape") and hasattr(QFrame.Shape, name):
        return getattr(QFrame.Shape, name)
    if hasattr(QFrame, name):
        return getattr(QFrame, name)
    return 0

AlignCenter = _get_qt_flag("AlignmentFlag", "AlignCenter", "Alignment")
TextSelectableByMouse = _get_qt_flag("TextInteractionFlag", "TextSelectableByMouse", "TextInteraction")
FrameNoFrame = _get_qframe_shape("NoFrame")
FrameHLine = _get_qframe_shape("HLine")


# ─── Stil Sabitleri ──────────────────────────────────────────────────────────
STIL_BASLIK = (
    "color: #ffffff; background: #2c7a4b; padding: 8px; border-radius: 6px;"
)
STIL_BTN_SORGULA = (
    "QPushButton { background:#2c7a4b; color:white; border-radius:5px; font-weight:bold; }"
    "QPushButton:hover { background:#236040; }"
    "QPushButton:disabled { background:#aaa; }"
)
STIL_BTN_BINA_BB = (
    "QPushButton { background:#0b7285; color:white; border-radius:5px; font-weight:bold; }"
    "QPushButton:hover { background:#0a5f6f; }"
    "QPushButton:disabled { background:#aaa; }"
)
STIL_BTN_TIKLA = (
    "QPushButton { background:#1565c0; color:white; border-radius:5px; font-weight:bold; }"
    "QPushButton:checked { background:#b71c1c; }"
    "QPushButton:hover:!checked { background:#0d47a1; }"
)
STIL_BTN_ZOOM = (
    "QPushButton { background:#e65100; color:white; border-radius:4px; font-weight:bold; }"
    "QPushButton:hover { background:#bf360c; }"
)
STIL_BTN_ADRES = (
    "QPushButton { background:#6a1b9a; color:white; border-radius:5px; font-weight:bold; }"
    "QPushButton:hover { background:#4a148c; }"
    "QPushButton:disabled { background:#aaa; }"
)
STIL_FORM_ELEMENTS = (
    "QComboBox, QLineEdit { background: #ffffff; color: #000000; padding: 4px; border: 1px solid #ccc; border-radius: 4px; }"
    "QComboBox:disabled, QLineEdit:disabled { background: #f0f0f0; color: #888; }"
)
STIL_ACIKLAMA = "color: #555; font-size: 11px;"
STIL_SONUC_KEY = "font-weight: bold; color: #444;"
STIL_KATMAN = "color: #2c7a4b; font-size: 11px;"
STIL_UYARI = (
    "QLabel {"
    " background:#fff4d6;"
    " border:1px solid #ead7a0;"
    " border-radius:4px;"
    " color:#7a5c1f;"
    " padding:6px;"
    " font-size:11px;"
    "}"
)
STIL_DURUM = "color: #555; font-size: 11px; padding: 3px 0;"
STIL_SORGU_SAYAC = "color: #2b4c7e; font-size: 11px; padding: 0 0 4px 0;"
STIL_AKORDIYON_CONTAINER = "QWidget { background: #f7f9fa; border: 1px solid #d9e2ec; border-radius: 6px; }"
STIL_ADRES_SONUC = (
    "QLabel {"
    " background:#e8f5e9;"
    " border:1px solid #a5d6a7;"
    " border-radius:4px;"
    " color:#2e7d32;"
    " padding:8px;"
    " font-size:12px;"
    "}"
)

# Sonuç panelinde gösterilecek satırlar
SONUC_SATIRLARI = [
    ("il",       "İl"),
    ("ilce",     "İlçe"),
    ("mahalle",  "Mahalle"),
    ("ada",      "Ada No"),
    ("parsel",   "Parsel No"),
    ("alan",     "Alan (m²)"),
    ("nitelik",  "Nitelik"),
    ("pafta",    "Pafta"),
]


class Ui_TKGMPanel:
    """
    Panel üzerindeki tüm widget'ları oluşturur ve düzenler.
    Controller sınıfı (TKGMPanel) bu sınıfı miras alarak
    sinyal-slot bağlantılarını kendisi kurar.
    """

    def setup_ui(self, dock_widget):
        """DockWidget üzerine tüm görsel öğeleri yerleştirir."""
        # Ana Kaydırma Alanı (Scroll Area) oluştur
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setFrameShape(FrameNoFrame)
        
        # İçerik Widget'ı
        self.container = QWidget()
        self.scroll_area.setWidget(self.container)
        
        # Form elemanları için genel stil uygula (okunabilirlik garantisi)
        self.container.setStyleSheet(STIL_FORM_ELEMENTS)
        
        # DockWidget'in ana widget'ı olarak scroll area'yı ayarla
        dock_widget.setWidget(self.scroll_area)
        dock_widget.setMinimumWidth(310)

        # Ana mizanpajı konteyner üzerine kur
        ana = QVBoxLayout(self.container)
        ana.setContentsMargins(10, 10, 10, 10)
        ana.setSpacing(8)

        # ── Başlık ───────────────────────────────────────────────────────
        self._build_baslik(ana)

        # ── QTabWidget — İki Sekme ────────────────────────────────────────
        self.tab_widget = QTabWidget()
        ana.addWidget(self.tab_widget)

        # ── Sekme 1: Parsel Sorgulama ─────────────────────────────────────
        self._parsel_tab = QWidget()
        self._parsel_tab.setStyleSheet(STIL_FORM_ELEMENTS)
        parsel_layout = QVBoxLayout(self._parsel_tab)
        parsel_layout.setContentsMargins(4, 8, 4, 4)
        parsel_layout.setSpacing(8)
        self._build_parsel_sekmesi(parsel_layout)
        self.tab_widget.addTab(self._parsel_tab, QgsApplication.getThemeIcon("/mIconPolygonLayer.svg"), "Parsel Sorgulama")

        # ── Sekme 2: Adres Sorgulama ─────────────────────────────────────
        self._adres_tab = QWidget()
        self._adres_tab.setStyleSheet(STIL_FORM_ELEMENTS)
        adres_layout = QVBoxLayout(self._adres_tab)
        adres_layout.setContentsMargins(4, 8, 4, 4)
        adres_layout.setSpacing(8)
        self._build_adres_sekmesi(adres_layout)
        self.tab_widget.addTab(self._adres_tab, QgsApplication.getThemeIcon("/mIconPointLayer.svg"), "Adres Sorgulama")

        ana.addStretch()

        # ── Durum Çubuğu ─────────────────────────────────────────────────
        self.lbl_durum = QLabel("Hazır")
        self.lbl_durum.setStyleSheet(STIL_DURUM)
        ana.addWidget(self.lbl_durum)

        self.lbl_gunluk_sorgu = QLabel("Bugünkü sorgu: 0")
        self.lbl_gunluk_sorgu.setStyleSheet(STIL_SORGU_SAYAC)
        ana.addWidget(self.lbl_gunluk_sorgu)

    # ================================================================
    #  Arayüz bölüm inşaatçıları
    # ================================================================

    def _build_baslik(self, layout):
        baslik = QLabel("TKGM Parsel & Adres Sorgulama")
        baslik_font = QFont()
        baslik_font.setPointSize(11)
        baslik_font.setBold(True)
        baslik.setFont(baslik_font)
        baslik.setAlignment(AlignCenter)
        baslik.setStyleSheet(STIL_BASLIK)
        layout.addWidget(baslik)

    # ────────────────────────────────────────────────────────────────────
    # Parsel Sekmesi İçeriği
    # ────────────────────────────────────────────────────────────────────

    def _build_parsel_sekmesi(self, layout):
        """Parsel sekmesindeki tüm widget'ları oluşturur."""
        # İdari Birim Seçimi
        self._build_idari_birim(layout)

        # Ada / Parsel
        self._build_ada_parsel(layout)

        # Sorgula Butonu
        self._build_sorgula_btn(layout)

        # Ayraç
        cizgi = QFrame()
        cizgi.setFrameShape(FrameHLine)
        cizgi.setStyleSheet("color: #ccc;")
        layout.addWidget(cizgi)

        # Koordinat ile Sorgula
        self._build_tikla_grubu(layout)

        # Sonuç Alanı
        self._build_sonuc(layout)

        # Bina/BB Sonuç Alanı
        self._build_bina_bb_sonuc(layout)

        layout.addStretch()

    def _build_idari_birim(self, layout):
        grp = QGroupBox("İdari Birim Seçimi")
        g = QGridLayout(grp)
        g.setSpacing(5)

        # İl
        g.addWidget(QLabel("İl:"), 0, 0)
        self.cmb_il = QComboBox()
        self.cmb_il.setPlaceholderText("Yükleniyor...")
        self.cmb_il.setEnabled(False)
        g.addWidget(self.cmb_il, 0, 1)

        # İlçe
        g.addWidget(QLabel("İlçe:"), 1, 0)
        self.cmb_ilce = QComboBox()
        self.cmb_ilce.setPlaceholderText("Önce il seçin")
        self.cmb_ilce.setEnabled(False)
        g.addWidget(self.cmb_ilce, 1, 1)

        # Mahalle
        g.addWidget(QLabel("Mahalle:"), 2, 0)
        self.cmb_mahalle = QComboBox()
        self.cmb_mahalle.setPlaceholderText("Önce ilçe seçin")
        self.cmb_mahalle.setEnabled(False)
        g.addWidget(self.cmb_mahalle, 2, 1)

        layout.addWidget(grp)

    def _build_ada_parsel(self, layout):
        grp = QGroupBox("Ada / Parsel No")
        h = QHBoxLayout(grp)
        h.addWidget(QLabel("Ada:"))
        self.txt_ada = QLineEdit()
        self.txt_ada.setPlaceholderText("ör: 112")
        self.txt_ada.setMaximumWidth(90)
        h.addWidget(self.txt_ada)
        h.addSpacing(12)
        h.addWidget(QLabel("Parsel:"))
        self.txt_parsel = QLineEdit()
        self.txt_parsel.setPlaceholderText("ör: 5")
        self.txt_parsel.setMaximumWidth(90)
        h.addWidget(self.txt_parsel)
        h.addStretch()
        layout.addWidget(grp)

    def _build_sorgula_btn(self, layout):
        self.btn_sorgula = QPushButton(" Parsel Sorgula")
        self.btn_sorgula.setIcon(QgsApplication.getThemeIcon("/mActionIdentify.svg"))
        self.btn_sorgula.setMinimumHeight(36)
        self.btn_sorgula.setStyleSheet(STIL_BTN_SORGULA)
        layout.addWidget(self.btn_sorgula)

    def _build_tikla_grubu(self, layout):
        grp = QGroupBox("Koordinat ile Sorgula")
        vt = QVBoxLayout(grp)
        vt.setSpacing(4)

        aciklama = QLabel("Haritaya tıklayarak o noktadaki parseli sorgulayın.")
        aciklama.setWordWrap(True)
        aciklama.setStyleSheet(STIL_ACIKLAMA)
        vt.addWidget(aciklama)

        ht = QHBoxLayout()
        self.btn_tikla_ac = QPushButton(" Tıklama Modunu Aç")
        self.btn_tikla_ac.setIcon(QgsApplication.getThemeIcon("/mActionMapIdentification.svg"))
        self.btn_tikla_ac.setCheckable(True)
        self.btn_tikla_ac.setMinimumHeight(32)
        self.btn_tikla_ac.setStyleSheet(STIL_BTN_TIKLA)
        ht.addWidget(self.btn_tikla_ac)
        vt.addLayout(ht)
        layout.addWidget(grp)

    def _build_sonuc(self, layout):
        self.grp_sonuc = QGroupBox("Parsel Bilgileri")
        self.grp_sonuc.setVisible(False)
        gs = QGridLayout(self.grp_sonuc)
        gs.setSpacing(4)

        self._sonuc_etiketler = {}
        for idx, (key, label) in enumerate(SONUC_SATIRLARI):
            lbl_key = QLabel(label + ":")
            lbl_key.setStyleSheet(STIL_SONUC_KEY)
            lbl_val = QLabel("—")
            lbl_val.setTextInteractionFlags(TextSelectableByMouse)
            lbl_val.setWordWrap(True)
            gs.addWidget(lbl_key, idx, 0)
            gs.addWidget(lbl_val, idx, 1)
            self._sonuc_etiketler[key] = lbl_val

        self.btn_bina_bb = QPushButton(" Bina/BB Listesi Sorgula")
        self.btn_bina_bb.setIcon(QgsApplication.getThemeIcon("/mActionOpenTable.svg"))
        self.btn_bina_bb.setMinimumHeight(34)
        self.btn_bina_bb.setStyleSheet(STIL_BTN_BINA_BB)
        gs.addWidget(self.btn_bina_bb, len(SONUC_SATIRLARI), 0, 1, 2)

        # Zoom butonu
        self.btn_zoom = QPushButton(" Parsele Git")
        self.btn_zoom.setIcon(QgsApplication.getThemeIcon("/mActionZoomToSelected.svg"))
        self.btn_zoom.setMinimumHeight(30)
        self.btn_zoom.setStyleSheet(STIL_BTN_ZOOM)
        gs.addWidget(self.btn_zoom, len(SONUC_SATIRLARI) + 1, 0, 1, 2)

        # Katman bilgisi
        self.lbl_katman = QLabel()
        self.lbl_katman.setStyleSheet(STIL_KATMAN)
        self.lbl_katman.setAlignment(AlignCenter)
        gs.addWidget(self.lbl_katman, len(SONUC_SATIRLARI) + 2, 0, 1, 2)

        self.lbl_parsel_hareket_uyari = QLabel("")
        self.lbl_parsel_hareket_uyari.setWordWrap(True)
        self.lbl_parsel_hareket_uyari.setVisible(False)
        self.lbl_parsel_hareket_uyari.setStyleSheet(STIL_UYARI)
        gs.addWidget(self.lbl_parsel_hareket_uyari, len(SONUC_SATIRLARI) + 3, 0, 1, 2)

        layout.addWidget(self.grp_sonuc)

    def _build_bina_bb_sonuc(self, layout):
        self.grp_bina_bb = QGroupBox("Bina/BB Listesi")
        self.grp_bina_bb.setVisible(False)
        self.grp_bina_bb.setMinimumHeight(360)
        vb = QVBoxLayout(self.grp_bina_bb)
        vb.setSpacing(6)

        self.lbl_bina_bb_ozet = QLabel("")
        self.lbl_bina_bb_ozet.setStyleSheet(STIL_ACIKLAMA)
        self.lbl_bina_bb_ozet.setWordWrap(True)
        vb.addWidget(self.lbl_bina_bb_ozet)

        self.bina_bb_scroll = QScrollArea()
        self.bina_bb_scroll.setWidgetResizable(True)
        self.bina_bb_scroll.setFrameShape(FrameNoFrame)
        self.bina_bb_scroll.setMinimumHeight(310)

        self.bina_bb_container = QWidget()
        self.bina_bb_container.setStyleSheet(STIL_AKORDIYON_CONTAINER)
        self.bina_bb_layout = QVBoxLayout(self.bina_bb_container)
        self.bina_bb_layout.setContentsMargins(8, 8, 8, 8)
        self.bina_bb_layout.setSpacing(6)
        self.bina_bb_layout.addStretch()

        self.bina_bb_scroll.setWidget(self.bina_bb_container)
        vb.addWidget(self.bina_bb_scroll)

        layout.addWidget(self.grp_bina_bb)

    # ────────────────────────────────────────────────────────────────────
    # Adres Sekmesi İçeriği
    # ────────────────────────────────────────────────────────────────────

    def _build_adres_sekmesi(self, layout):
        """Adres sekmesindeki tüm widget'ları oluşturur."""
        # Açıklama
        aciklama = QLabel(
            "TKGM MAKS İdari Yapı veritabanından adres sorgulama.\n"
            "İl → İlçe → Mahalle → Yol → Numarataj sırasıyla seçin."
        )
        aciklama.setWordWrap(True)
        aciklama.setStyleSheet(STIL_ACIKLAMA)
        layout.addWidget(aciklama)

        # Adres dropdown'ları
        self._build_adres_dropdowns(layout)

        # Adrese Git butonu
        self.btn_adres_sorgula = QPushButton(" Adres Sorgula")
        self.btn_adres_sorgula.setIcon(QgsApplication.getThemeIcon("/mActionZoomToSelected.svg"))
        self.btn_adres_sorgula.setMinimumHeight(36)
        self.btn_adres_sorgula.setStyleSheet(STIL_BTN_ADRES)
        self.btn_adres_sorgula.setEnabled(False)
        layout.addWidget(self.btn_adres_sorgula)

        # Sonuç alanı
        self._build_adres_sonuc(layout)

        layout.addStretch()

    def _build_adres_dropdowns(self, layout):
        grp = QGroupBox("Adres Bilgileri")
        g = QGridLayout(grp)
        g.setSpacing(5)

        # İl
        g.addWidget(QLabel("İl:"), 0, 0)
        self.cmb_adres_il = QComboBox()
        self.cmb_adres_il.setPlaceholderText("Yükleniyor...")
        self.cmb_adres_il.setEnabled(False)
        g.addWidget(self.cmb_adres_il, 0, 1)

        # İlçe
        g.addWidget(QLabel("İlçe:"), 1, 0)
        self.cmb_adres_ilce = QComboBox()
        self.cmb_adres_ilce.setPlaceholderText("Önce il seçin")
        self.cmb_adres_ilce.setEnabled(False)
        g.addWidget(self.cmb_adres_ilce, 1, 1)

        # Mahalle
        g.addWidget(QLabel("Mahalle:"), 2, 0)
        self.cmb_adres_mahalle = QComboBox()
        self.cmb_adres_mahalle.setPlaceholderText("Önce ilçe seçin")
        self.cmb_adres_mahalle.setEnabled(False)
        g.addWidget(self.cmb_adres_mahalle, 2, 1)

        # Yol (Cadde/Sokak)
        g.addWidget(QLabel("Yol:"), 3, 0)
        self.cmb_adres_yol = QComboBox()
        self.cmb_adres_yol.setPlaceholderText("Önce mahalle seçin")
        self.cmb_adres_yol.setEnabled(False)
        g.addWidget(self.cmb_adres_yol, 3, 1)

        # Numarataj (Kapı No)
        g.addWidget(QLabel("Kapı No:"), 4, 0)
        self.cmb_adres_numarataj = QComboBox()
        self.cmb_adres_numarataj.setPlaceholderText("Önce yol seçin")
        self.cmb_adres_numarataj.setEnabled(False)
        g.addWidget(self.cmb_adres_numarataj, 4, 1)

        layout.addWidget(grp)

    def _build_adres_sonuc(self, layout):
        self.grp_adres_sonuc = QGroupBox("Adres Sonucu")
        self.grp_adres_sonuc.setVisible(False)
        vs = QVBoxLayout(self.grp_adres_sonuc)
        vs.setSpacing(4)

        self.lbl_adres_tam = QLabel("")
        self.lbl_adres_tam.setWordWrap(True)
        self.lbl_adres_tam.setTextInteractionFlags(TextSelectableByMouse)
        self.lbl_adres_tam.setStyleSheet(STIL_ADRES_SONUC)
        vs.addWidget(self.lbl_adres_tam)

        self.lbl_adres_koordinat = QLabel("")
        self.lbl_adres_koordinat.setTextInteractionFlags(TextSelectableByMouse)
        self.lbl_adres_koordinat.setStyleSheet(STIL_ACIKLAMA)
        vs.addWidget(self.lbl_adres_koordinat)

        self.lbl_adres_katman = QLabel()
        self.lbl_adres_katman.setStyleSheet(STIL_KATMAN)
        self.lbl_adres_katman.setAlignment(AlignCenter)
        vs.addWidget(self.lbl_adres_katman)

        layout.addWidget(self.grp_adres_sonuc)
