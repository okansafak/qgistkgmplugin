"""
Supabase tabanlı anonim metrik gönderimi.

Bu modül yalnızca opt-in açıkken çalışır ve kişisel veri içermeyen
alanları toplu (batch) biçimde gönderir.
"""

import json
import os
import uuid
from datetime import datetime, timezone

from qgis.PyQt.QtCore import QByteArray, QSettings, QTimer, QUrl
from qgis.PyQt.QtNetwork import QNetworkRequest
from qgis.core import Qgis, QgsNetworkAccessManager


SUPABASE_URL = os.getenv("TKGM_SUPABASE_URL", "https://pewfpbslwiclaqfhwkhg.supabase.co")
SUPABASE_ANON_KEY = os.getenv("TKGM_SUPABASE_ANON_KEY", "sb_publishable_QCqUDjdVfKPPeJmXZup71Q_cBSJgFMi")

SETTINGS_CONSENT_KEY = "TKGMParsel/metricsConsent"
SETTINGS_ASKED_VERSION_KEY = "TKGMParsel/metricsAskedVersion"
SETTINGS_ANON_UID_KEY = "TKGMParsel/metricsAnonUid"


class SupabaseMetricsClient:
    def __init__(self, plugin_version: str, batch_size: int = 20, flush_ms: int = 15000):
        self.plugin_version = plugin_version
        self.batch_size = max(1, int(batch_size))
        self.flush_ms = max(1000, int(flush_ms))
        self.endpoint = ""
        if SUPABASE_URL.strip():
            self.endpoint = f"{SUPABASE_URL.rstrip('/')}/rest/v1/events"

        self._queue = []
        self._timer = QTimer()
        self._timer.setSingleShot(True)
        self._timer.timeout.connect(self.flush)

    def is_configured(self) -> bool:
        return bool(self.endpoint and SUPABASE_ANON_KEY.strip())

    def is_enabled(self) -> bool:
        return QSettings().value(SETTINGS_CONSENT_KEY, False, type=bool)

    def _anon_user_id(self) -> str:
        s = QSettings()
        uid = s.value(SETTINGS_ANON_UID_KEY, "", type=str)
        uid = str(uid or "").strip()
        if uid:
            return uid
        uid = str(uuid.uuid4())
        s.setValue(SETTINGS_ANON_UID_KEY, uid)
        return uid

    def track(
        self,
        query_type: str,
        status: str = "success",
        city: str = "",
        district: str = "",
        neighborhood: str = "",
        count: int = 1,
        extra: dict = None,
    ) -> None:
        if not self.is_enabled() or not self.is_configured():
            return

        now = datetime.now(timezone.utc)
        payload = {
            "plugin_version": self.plugin_version,
            "qgis_version": str(getattr(Qgis, "QGIS_VERSION", "")),
            "anon_user_id": self._anon_user_id(),
            "event_date": now.strftime("%Y-%m-%d"),
            "event_hour": now.hour,
            "query_type": str(query_type or "").strip(),
            "status": str(status or "").strip(),
            "city": self._clean_text(city),
            "district": self._clean_text(district),
            "neighborhood": self._clean_text(neighborhood),
            "count": max(1, int(count)),
            "extra": extra if isinstance(extra, dict) and extra else None,
        }

        if not payload["query_type"]:
            return

        self._queue.append(payload)
        if len(self._queue) >= self.batch_size:
            self._timer.stop()
            self.flush()
            return

        if not self._timer.isActive():
            self._timer.start(self.flush_ms)

    def flush(self) -> None:
        if not self._queue or not self.is_configured():
            return

        batch = self._queue.copy()
        self._queue.clear()

        req = QNetworkRequest(QUrl(self.endpoint))
        req.setHeader(QNetworkRequest.ContentTypeHeader, "application/json")
        req.setRawHeader(b"apikey", SUPABASE_ANON_KEY.encode("utf-8"))
        req.setRawHeader(b"Authorization", f"Bearer {SUPABASE_ANON_KEY}".encode("utf-8"))
        req.setRawHeader(b"Prefer", b"return=minimal")

        body = QByteArray(json.dumps(batch, ensure_ascii=False).encode("utf-8"))
        reply = QgsNetworkAccessManager.instance().post(req, body)
        reply.finished.connect(reply.deleteLater)

    def _clean_text(self, value: str) -> str:
        text = str(value or "").strip()
        if text in {"—", "Yükleniyor...", "-", "None", "none"}:
            return ""
        return text
