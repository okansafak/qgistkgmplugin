"""
TKGM Parsel Sorgulama — Ana Eklenti Sınıfı
QGIS'e menu ve toolbar entegrasyonu sağlar.
"""

import os
try:
    from qgis.PyQt.QtGui import QAction
except ImportError:
    from qgis.PyQt.QtWidgets import QAction

from qgis.PyQt.QtWidgets import QToolBar
from qgis.PyQt.QtGui import QIcon
from qgis.PyQt.QtCore import Qt

def _get_qt_flag(scope, name):
    if hasattr(Qt, scope):
        s = getattr(Qt, scope)
        if hasattr(s, name):
            return getattr(s, name)
    if hasattr(Qt, name):
        return getattr(Qt, name)
    return 0

LeftDockWidgetArea = _get_qt_flag("DockWidgetArea", "LeftDockWidgetArea")
RightDockWidgetArea = _get_qt_flag("DockWidgetArea", "RightDockWidgetArea")

from .tkgm_panel import TKGMPanel


class TKGMParselPlugin:
    def __init__(self, iface):
        self.iface = iface
        self.panel = None
        self.action = None

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
            if self.panel is None:
                self.panel = TKGMPanel(self.iface)
                self.panel.setAllowedAreas(
                    LeftDockWidgetArea | RightDockWidgetArea
                )
                self.iface.addDockWidget(RightDockWidgetArea, self.panel)
                self.panel.visibilityChanged.connect(self._on_panel_visibility)
            else:
                self.panel.show()
        else:
            if self.panel:
                self.panel.hide()

    def _on_panel_visibility(self, visible: bool):
        """Panel kapatılınca butonu da deseçili yap."""
        if self.action:
            self.action.setChecked(visible)
