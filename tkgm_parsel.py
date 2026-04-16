"""
TKGM Parsel Sorgulama — Ana Eklenti Sınıfı
QGIS'e menu ve toolbar entegrasyonu sağlar.
"""

import os
import json
try:
    from qgis.PyQt.QtGui import QAction
except ImportError:
    from qgis.PyQt.QtWidgets import QAction

from qgis.PyQt.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QLabel,
    QTextEdit,
    QCheckBox,
    QDialogButtonBox,
    QMessageBox,
)
from qgis.PyQt.QtGui import QIcon
from qgis.PyQt.QtCore import Qt, QSettings
from .metrics import (
    SETTINGS_ASKED_VERSION_KEY,
    SETTINGS_CONSENT_KEY,
    SupabaseMetricsClient,
)

def _get_qt_flag(scope, name):
    if hasattr(Qt, scope):
        s = getattr(Qt, scope)
        if hasattr(s, name):
            return getattr(s, name)
    if hasattr(Qt, name):
        return getattr(Qt, name)
    return 0


def _get_dialog_code(name):
    if hasattr(QDialog, "DialogCode") and hasattr(QDialog.DialogCode, name):
        return getattr(QDialog.DialogCode, name)
    if hasattr(QDialog, name):
        return getattr(QDialog, name)
    return 0


def _get_buttonbox_standard(name):
    if hasattr(QDialogButtonBox, "StandardButton") and hasattr(QDialogButtonBox.StandardButton, name):
        return getattr(QDialogButtonBox.StandardButton, name)
    if hasattr(QDialogButtonBox, name):
        return getattr(QDialogButtonBox, name)
    return 0

LeftDockWidgetArea = _get_qt_flag("DockWidgetArea", "LeftDockWidgetArea")
RightDockWidgetArea = _get_qt_flag("DockWidgetArea", "RightDockWidgetArea")
DialogAccepted = _get_dialog_code("Accepted")
BtnOk = _get_buttonbox_standard("Ok")
BtnCancel = _get_buttonbox_standard("Cancel")

from .tkgm_panel import TKGMPanel


KULLANIM_KOSULLARI_METNI = (
    "Tapu ve Kadastro Genel Müdürlüğü (TKGM) Parsel Sorgulama Uygulamasını ziyaret eden her kullanıcı "
    "aşağıda belirtilen kullanım koşullarını kabul etmiş sayılır. Lütfen sitemizi kullanmadan önce "
    "kullanım koşullarını dikkatlice okuyunuz.\n\n"
    "KULLANIM KOŞULLARI:\n\n"
    "1- Bu site, hizmet sunmak için çerezleri kullanır. Bu siteyi kullanarak çerezlerin kullanılmasını kabul etmiş olursunuz. "
    "Bu çerezler; dil seçimi gibi kullanıcı tercihlerine göre, sitenin çalışma veya görüntülenme biçimini değiştiren bilgileri hatırlamasını sağlar.\n"
    "2- Parsel Sorgulama Uygulamasının çalışması için ihtiyaç duyulan web servislerine TKGM'den izin almaksızın doğrudan ve/veya dolaylı yöntemler ile erişimde bulunulamaz.\n"
    "3- Sorgulama sonucu sunulan bilgi ve belgeler bilgilendirme amaçlıdır. Resmi işlemlerde kullanılamaz. Ayrıca ticari amaçla kullanılması yasaktır. "
    "Amacı dışında kullanılması halinde her türlü hukuki, cezai ve mali sorumluluk uygunsuz kullanan kişilere aittir.\n"
    "4- Kullanıcılar hiçbir şekilde sitede yer alan bilgilerin hatalı olması nedeniyle zarara uğradığı iddiasında bulunamaz.\n"
    "5- TKGM sitenin içeriğini veya kullanıcılara sağlanan herhangi bir hizmeti, dilediği zaman değiştirme ya da sona erdirme hakkını saklı tutar.\n"
    "6- TKGM sitenin 24 saat erişilebilir olması için çalışmaktadır. Ancak değişik sebeplerle sitenin erişilebilir olmamasından sorumlu değildir. "
    "Bu siteye erişim, herhangi bir duyuru yapılmaksızın geçici olarak durdurulabilir.\n"
    "7- İnternetin yapısı gereği bilgiler yeterli güvenlik önlemleri olmaksızın dolaşabilir, çoğaltılabilir ve yetkili olmayan kişiler tarafından alınıp kullanılabilir. "
    "Bu kullanım ve kullanımdan doğacak zarar, TKGM'nin sorumluluğunda değildir.\n"
    "8- Kullanıcılar ile TKGM arasında ortaya çıkabilecek ihtilaflarda, TKGM'nin kayıtları delil olarak kabul edilecektir.\n"
    "9- TKGM kullanım koşullarının herhangi bir maddesini bildirimde bulunmaksızın değiştirme, yenileme veya iptal hakkına sahiptir. "
    "Değiştirilen ya da yürürlükten kaldırılan her hüküm, yayım tarihinde tüm kullanıcılar bakımından hüküm ifade edecektir.\n"
    "10- İhtilafların çözümünde Türkiye Cumhuriyeti kanunları uygulanır ve Ankara mahkemelerinin yetkili olduğu kabul edilir.\n"
    "11- Parsel Sorgulama Uygulamasının tüm hakları saklıdır."
)

ANONIM_METRIK_AYDINLATMA_METNI = (
    "Anonim kullanım istatistikleri (isteğe bağlı):\n\n"
    "Toplanan alanlar: sorgu tipi, başarı durumu, il/ilçe/mahalle, sürüm ve saat dilimi.\n"
    "Toplanmayan alanlar: isim, parcel_id, ada/parsel, koordinat, dosya yolu.\n\n"
    "Bu veri, eklentiyi geliştirmek ve hata oranlarını izlemek için kullanılır."
)


class KullanimKosullariDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("TKGM Parsel - Kullanım Koşulları")
        self.resize(700, 520)

        lay = QVBoxLayout(self)

        baslik = QLabel("Lütfen eklentiyi kullanmadan önce kullanım koşullarını onaylayınız.")
        baslik.setWordWrap(True)
        lay.addWidget(baslik)

        metin = QTextEdit()
        metin.setReadOnly(True)
        metin.setPlainText(KULLANIM_KOSULLARI_METNI)
        lay.addWidget(metin)

        self.chk_kabul = QCheckBox("Okudum ve kabul ediyorum")
        lay.addWidget(self.chk_kabul)

        self.btn_box = QDialogButtonBox(BtnOk | BtnCancel)
        self.btn_box.button(BtnOk).setText("Kabul Ediyorum")
        self.btn_box.button(BtnCancel).setText("Kabul Etmiyorum")
        self.btn_box.button(BtnOk).setEnabled(False)
        lay.addWidget(self.btn_box)

        self.chk_kabul.toggled.connect(
            lambda v: self.btn_box.button(BtnOk).setEnabled(v)
        )
        self.btn_box.accepted.connect(self.accept)
        self.btn_box.rejected.connect(self.reject)


class TKGMParselPlugin:
    def __init__(self, iface):
        self.iface = iface
        self.panel = None
        self.action = None
        self.plugin_version = self._plugin_surumu_oku()
        self.metrics = SupabaseMetricsClient(plugin_version=self.plugin_version)

    def _plugin_surumu_oku(self) -> str:
        metadata = os.path.join(os.path.dirname(__file__), "metadata.txt")
        try:
            with open(metadata, "r", encoding="utf-8") as f:
                for line in f:
                    s = line.strip()
                    if s.lower().startswith("version="):
                        return s.split("=", 1)[1].strip()
        except Exception:
            pass
        return "0.0.0"

    def _onay_dosya_yolu(self) -> str:
        return os.path.join(os.path.dirname(__file__), ".kullanim_kosullari_onay.json")

    def _onay_surum_dosyadan_oku(self) -> str:
        path = self._onay_dosya_yolu()
        if not os.path.exists(path):
            return ""
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            return str(data.get("accepted_version") or "")
        except Exception:
            return ""

    def _onay_surum_dosyaya_yaz(self, version: str) -> None:
        path = self._onay_dosya_yolu()
        data = {"accepted_version": str(version)}
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def _kullanim_kosulu_onayli_mi(self) -> bool:
        # Öncelik: eklenti klasöründeki onay dosyası (yeniden kurulumda sıfırlanır)
        onay_surum = self._onay_surum_dosyadan_oku()
        if onay_surum:
            return onay_surum == self.plugin_version

        # Geriye dönük uyumluluk için eski QSettings anahtarı
        settings = QSettings()
        key = "TKGMParsel/kullanimKosullariOnaySurum"
        onay_surum = settings.value(key, "", type=str)
        return onay_surum == self.plugin_version

    def _kullanim_kosulu_onaylat(self) -> bool:
        if self._kullanim_kosulu_onayli_mi():
            return True

        dlg = KullanimKosullariDialog(self.iface.mainWindow())
        if hasattr(dlg, "exec"):
            sonuc = dlg.exec()
        else:
            sonuc = dlg.exec_()

        if sonuc != DialogAccepted:
            QMessageBox.information(
                self.iface.mainWindow(),
                "TKGM Parsel",
                "Eklentiyi kullanabilmek için kullanım koşullarını kabul etmeniz gerekir.",
            )
            return False

        settings = QSettings()
        settings.setValue("TKGMParsel/kullanimKosullariOnaySurum", self.plugin_version)
        try:
            self._onay_surum_dosyaya_yaz(self.plugin_version)
        except Exception:
            # Dosyaya yazılamazsa QSettings fallback devam eder.
            pass
        return True

    def _metrik_onayi_sor_eger_gerekirse(self) -> None:
        settings = QSettings()
        sorulan_surum = settings.value(SETTINGS_ASKED_VERSION_KEY, "", type=str)
        if str(sorulan_surum or "") == self.plugin_version:
            return

        cevap = QMessageBox.question(
            self.iface.mainWindow(),
            "TKGM Parsel - Anonim Metrik Onayı",
            ANONIM_METRIK_AYDINLATMA_METNI,
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        settings.setValue(SETTINGS_CONSENT_KEY, cevap == QMessageBox.Yes)
        settings.setValue(SETTINGS_ASKED_VERSION_KEY, self.plugin_version)

    def initGui(self):
        """QGIS arayüzüne eklenti öğelerini ekler."""
        icon_path = os.path.join(os.path.dirname(__file__), "icon.png")
        icon = QIcon(icon_path) if os.path.exists(icon_path) else QIcon()

        self.action = QAction(icon, "TKGM Parsel Sorgulama", self.iface.mainWindow())
        self.action.setCheckable(True)
        self.action.setToolTip("TKGM Parsel Sorgulama panelini aç/kapat")
        self.action.triggered.connect(self._panel_toggle)

        # Menu
        self.iface.addPluginToMenu("&TKGM Parsel", self.action)

        # Toolbar
        self.iface.addToolBarIcon(self.action)

    def unload(self):
        """Eklenti kaldırıldığında temizlik yapar."""
        try:
            self.metrics.flush()
        except Exception:
            pass

        self.iface.removePluginMenu("&TKGM Parsel", self.action)
        self.iface.removeToolBarIcon(self.action)

        if self.panel:
            # Eklenti reload edilirken harita aracının takılı kalmasını önle
            if self.panel.btn_tikla_ac.isChecked():
                self.panel.btn_tikla_ac.setChecked(False)
            
            self.iface.removeDockWidget(self.panel)
            self.panel = None

    def _panel_toggle(self, checked: bool):
        """Paneli aç/kapat."""
        if checked:
            if not self._kullanim_kosulu_onaylat():
                if self.action:
                    self.action.setChecked(False)
                return

            self._metrik_onayi_sor_eger_gerekirse()

            if self.panel is None:
                self.panel = TKGMPanel(self.iface)
                self.panel.set_metrics_client(self.metrics)
                self.panel.setAllowedAreas(
                    LeftDockWidgetArea | RightDockWidgetArea
                )
                self.iface.addDockWidget(RightDockWidgetArea, self.panel)
                self.panel.visibilityChanged.connect(self._on_panel_visibility)
                self.metrics.track("plugin_start", status="success")
            else:
                self.panel.set_metrics_client(self.metrics)
                self.panel.show()
        else:
            if self.panel:
                self.panel.hide()

    def _on_panel_visibility(self, visible: bool):
        """Panel kapatılınca butonu da deseçili yap."""
        if self.action:
            self.action.setChecked(visible)
