"""
TKGM Parsel Sorgulama QGIS Eklentisi
"""


def classFactory(iface):
    from .tkgm_parsel import TKGMParselPlugin
    return TKGMParselPlugin(iface)
