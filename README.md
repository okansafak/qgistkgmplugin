# 🗺 TKGM Parsel ve Adres Sorgulama — QGIS Eklentisi / QGIS Plugin

[![QGIS Version](https://img.shields.io/badge/QGIS-3.16%20--%204.99-success.svg)](https://qgis.org)
[![Python Version](https://img.shields.io/badge/Python-3.7+-blue.svg)](https://python.org)
[![Qt Compatibility](https://img.shields.io/badge/Qt-Qt5%20%7C%20Qt6-orange.svg)](https://riverbankcomputing.com/software/pyqt/)
[![License: GPL v2](https://img.shields.io/badge/License-GPL%20v2-blue.svg)](LICENSE)
[![Latest Release](https://img.shields.io/badge/version-0.3.1-brightgreen.svg)](https://github.com/okansafak/qgistkgmplugin/releases)

TKGM (Tapu ve Kadastro Genel Müdürlüğü) CBS ve MAKS API servislerini kullanarak QGIS ortamında **parsel sorgulama**, **geometri görselleştirme**, **haritadan koordinat ile sorgulama**, **bina/bağımsız bölüm (kat mülkiyeti) listeleme** ve **MAKS idari yapı ile kapı no seviyesinde adres sorgulama** işlemlerini gerçekleştiren gelişmiş bir QGIS eklentisidir.

A comprehensive QGIS plugin to perform **parcel queries**, **polygon geometry visualization**, **coordinate/map-click queries**, **building and condominium (independent unit) queries**, and **door-number-level address lookup via MAKS** using official TKGM CBS & MAKS APIs.

---

## ✨ Temel Özellikler / Key Features

| Özellik / Feature | Açıklama / Description |
|---|---|
| 🏛 **İdari Birim Seçimi / Administrative Selection** | İl → İlçe → Mahalle kademeli dropdown listeleri. Türkçe alfabetik sıralama ve her seçimde haritada dinamik önizleme / zoom. |
| 🔍 **Ada/Parsel Sorgusu / Plot & Parcel Query** | Mahalle, Ada No ve Parsel No girerek detaylı poligon geometri ve tapu öznitelik sorgulama (alan, nitelik, pafta vb.). |
| 🎯 **Harita Tıklama Modu / Map Click Mode** | Harita üzerinde herhangi bir noktaya tıklayarak o koordinattaki parseli otomatik sorgulama ve katmana ekleme. |
| 🏢 **Bina & Bağımsız Bölüm Listesi / Buildings & Units** | Parseldeki blokları, bağımsız bölüm sayılarını ve kat mülkiyeti detaylarını (Kat, Giriş, Nitelik, BB No, Durum) akordiyon görünümüyle listeleme ve öznitelik tablosuna 1-N ilişki (`QgsRelation`) ile kaydetme. |
| 📍 **MAKS Adres Sorgulama / MAKS Address Lookup** | İl → İlçe → Mahalle → Yol (Cadde/Sokak) → Numarataj (Kapı No) hiyerarşisiyle adres bulma, canlı rubberband önizlemesi ve nokta katmanı oluşturma. |
| 🔄 **Parsel Hareket & Pasiflik Takibi / Parcel History & Status** | Pasif durumdaki veya ifraz/tevhit gibi parsel hareketlerine uğramış taşınmazlar için uyarı ve gittiği ada/parsel referanslarının gösterimi. |
| 🗺 **Otomatik Katman & Stil Yönetimi / Layer & Style Management** | EPSG:4326 WGS84 verilerini proje CRS'ine otomatik dönüştürme, şeffaf yeşil dolgu stili, beyaz halo ile Ada/Parsel etiketlemesi. |
| 🔢 **Günlük Sorgu Sayacı / Daily Query Counter** | Günlük yerel sorgu sayacı takibi ve TKGM API limit aşımlarında (HTTP 403 vb.) kullanıcı dostu bilgilendirme. |
| ⚡ **QGIS 3 & QGIS 4 (Qt5/Qt6) Desteği / Multi-Platform Compatibility** | QGIS 3.16'dan QGIS 4.99'a kadar geriye ve ileriye dönük tam Qt5 ve Qt6 uyumluluğu. |
| 🛡 **Gizlilik Odaklı Anonim Metrikler / Privacy-Friendly Metrics** | Sadece kullanım koşulları onaylandığında çalışan ve hiçbir kişisel/parsel verisi toplamayan Supabase telemetri altyapısı. |

---

## 📁 Proje Mimarisi / Project Structure

```
tkgm_parsel_plugin/
├── __init__.py                # QGIS eklenti yükleyicisi ve giriş noktası (classFactory)
├── metadata.txt               # Eklenti meta verileri (sürüm: 0.3.1, QGIS 3.16-4.99)
├── icon.png                   # Araç çubuğu ve menü ikonu
├── tkgm_parsel.py             # Ana eklenti sınıfı (Menü/Toolbar entegrasyonu, kullanım koşulları)
├── tkgm_panel.py              # Panel Controller (İş mantığı, sinyal/slotlar, akordiyon, zoom)
├── ui_tkgm_panel.py           # Arayüz Tasarımı (QTabWidget, Parsel & Adres sekmeleri, stiller)
├── tkgm_api.py                # TKGM CBS & MAKS İdari Yapı API istemcisi, güvenli HTTP yöneticisi
├── layer_manager.py           # QGIS katmanları (Polygon, Point, Tablo), QgsRelation, RubberBand
├── map_tool.py                # QgsMapToolEmitPoint tabanlı harita tıklama aracı
├── workers.py                 # Asenkron HTTP istekleri için QThread iş parçacıkları
├── metrics.py                 # Supabase asenkron & toplu (batch) anonim metrik istemcisi
├── supabase_metrics_setup.sql # Supabase veritabanı şeması, RLS politikaları ve trigger kurulumu
└── test_parse_alan.py         # Alan ayrıştırma (locale-independent float parser) birim testleri
```

---

## 🛠 Kurulum / Installation

### Yöntem 1 — ZIP Dosyası ile Kurulum (Önerilen)
1. [GitHub Releases](https://github.com/okansafak/qgistkgmplugin/releases) sayfasından en son yayınlanan `tkgm_parsel_plugin_v0.3.1.zip` (veya güncel sürüm) dosyasını indirin.
2. QGIS menüsünden **Eklentiler** (*Plugins*) → **Eklentileri Yönet ve Kur** (*Manage and Install Plugins*) penceresini açın.
3. **ZIP'ten Kur** (*Install from ZIP*) sekmesine geçin.
4. İndirdiğiniz `.zip` dosyasını seçin ve **Eklentiyi Kur** (*Install Plugin*) butonuna tıklayın.

### Yöntem 2 — Manuel Kurulum (Geliştiriciler İçin)
1. Depoyu klonlayın veya kaynak kodları indirin:
   ```bash
   git clone https://github.com/okansafak/qgistkgmplugin.git
   ```
2. `tkgm_parsel_plugin` klasörünü işletim sisteminize uygun QGIS eklenti dizinine kopyalayın:
   - **Windows:** `%APPDATA%\QGIS\QGIS3\profiles\default\python\plugins\`
   - **Linux:** `~/.local/share/QGIS/QGIS3/profiles/default/python/plugins/`
   - **macOS:** `~/Library/Application Support/QGIS/QGIS3/profiles/default/python/plugins/`
3. QGIS'i yeniden başlatın ve **Eklentileri Yönet ve Kur** menüsünden **TKGM Parsel Sorgulama** eklentisini aktif hale getirin.

---

## 🚀 Kullanım Kılavuzu / User Guide

Eklenti arayüzü iki ana sekmeden oluşur:

### 1. 🗺 Parsel Sorgulama Sekmesi

#### A. İdari Birim ile Ada/Parsel Sorgusu:
1. **İl**, **İlçe** ve **Mahalle** seçimlerini sırayla yapın (her seçimde harita ilgili bölgeye otomatik yakınlaşır).
2. **Ada No** ve **Parsel No** değerlerini girin.
3. **Parsel Sorgula** butonuna tıklayın.
4. Parsel poligonu haritada oluşturulan `TKGM Parseller` katmanına eklenir, parsele otomatik zoom yapılır ve panelde öznitelikler görüntülenir.

#### B. Harita Tıklama Modu ile Sorgulama:
1. **🎯 Tıklama Modunu Aç** butonuna basın.
2. Harita tuvalinde ilgilendiğiniz herhangi bir noktaya tıklayın.
3. Eklenti, koordinatın denk geldiği parseli otomatik olarak bulur, katmana ekler ve bilgilerini doldurur.

#### C. Bina ve Bağımsız Bölüm (Kat Mülkiyeti) Sorgusu:
1. Bir parsel sorgulandıktan sonra sonuç panelindeki **🏢 Bina/BB Listesi Sorgula** butonuna tıklayın.
2. Parselde yer alan tüm bloklar ve her bloğa ait bağımsız bölümler (Kat, Giriş, Nitelik, Kapı/Daire No, Durum) akordiyon şeklinde listelenir.
3. Bağımsız bölümler arka planda `TKGM Bagimsiz Bolumler` tablosuna kaydedilir ve `TKGM Parseller` katmanına `QgsRelation` ilişkisiyle bağlanır.

---

### 2. 📍 Adres Sorgulama Sekmesi (MAKS İdari Yapı)

1. Üstteki **Adres Sorgulama** sekmesine geçin.
2. **İl** → **İlçe** → **Mahalle** → **Yol (Cadde/Sokak)** → **Numarataj (Kapı No)** dropdown seçimlerini kademeli olarak yapın.
3. Her seçimde ilgili coğrafi alanın sınırları harita üzerinde mavi/turkuaz vurguyla anlık gösterilir.
4. Numarataj seçildikten sonra **📍 Adres Sorgula** butonuna basın.
5. Seçilen adres noktası haritada `TKGM Adresler` katmanına (Point) eklenir ve harita tam o noktaya odaklanır.

---

## 🗂 Katmanlar ve Öznitelik Yapısı / Layers & Attributes

| Katman Adı / Layer Name | Geometri / Geometry | Açıklama & Öznitelikler / Description & Attributes |
|---|---|---|
| **`TKGM Parseller`** | `Polygon (EPSG:4326)` | Parsel sınırları. Alanlar: `mahalleKodu`, `adaNo`, `parselNo`, `alan`, `nitelik`, `pafta`, `il`, `ilce`, `mahalle`. |
| **`TKGM Bagimsiz Bolumler`** | `None (Tablo)` | Bağımsız bölüm / kat mülkiyeti tablosu. Alanlar: `parselKey`, `mahalleKodu`, `adaNo`, `parselNo`, `blok`, `bbNo`, `tip`, `kat`, `giris`, `nitelik`, `durum`. |
| **`TKGM Adresler`** | `Point (EPSG:4326)` | Adres/numarataj noktaları. Alanlar: `il`, `ilce`, `mahalle`, `yol`, `kapiNo`, `tamAdres`. |

---

## ⚙ Sistem Gereksinimleri & Bağımlılıklar

- **QGIS Sürümü:** ≥ 3.16 (QGIS 3.x ve QGIS 4.x tam desteklenir)
- **Python Sürümü:** Python 3.7+
- **Kütüphaneler:** Standart Python & QGIS API (ek harici `pip` bağımlılığı gerektirmez)
- **Ağ Erişimi:** TKGM CBS & MAKS servislerine erişim için internet bağlantısı

---

## 📡 API Servisleri / API Endpoints

- **TKGM CBS Web API:** `https://cbsapi.tkgm.gov.tr/megsiswebapi.v3.1/api`
- **TKGM Parsel Sorgu Veri Servisi:** `https://parselsorgu.tkgm.gov.tr/app/modules/administrativeQuery/data`
- **TKGM MAKS İdari Yapı API:** `https://cbsapi.tkgm.gov.tr/megsiswebapi.v3.1/api/maksIdariYapi`

> ⚠ **Yasal Uyarı / Disclaimer:** Bu eklenti, Tapu ve Kadastro Genel Müdürlüğü'nün (TKGM) kamuya açık web servislerini kullanmaktadır. Sunulan veriler bilgilendirme amaçlı olup resmi işlemlerde doğrudan kullanılamaz. Eklenti ilk açılışında kullanıcıdan TKGM kullanım koşullarının onaylanması talep edilir.

---

## 📊 Anonim Metrikler & Gizlilik / Privacy Policy

Eklenti, kullanım kalitesini artırmak ve hata oranlarını tespit etmek amacıyla kullanım koşulları onaylandığında **anonim metrikler** gönderir.

### Toplanan Veriler:
- İşlem türü (`manual_query`, `map_click_query`, `building_bb_query`, `adres_query`)
- İşlem durumu (`start`, `success`, `error`) ve hata türü (ör. timeout, HTTP 403)
- İl, ilçe, mahalle genel adı (istatistiksel yoğunluk analizi için)
- Eklenti sürümü, QGIS sürümü ve rastgele oluşturulmuş anonim kullanıcı UUID'si

### ❌ Asla Toplanmayan Veriler:
- Parsel ID / Ada ve Parsel Numaraları
- Koordinat ve Geometri verileri
- Kullanıcı adı, IP adresi, makine adı veya dosya yolları

---

## 📋 Sürüm Geçmişi / Changelog

| Sürüm | Tarih | Değişiklikler / Changes |
|---|---|---|
| **0.3.1** | 2026-08 | MAKS adres sorgulama geliştirmeleri, canlı rubberband önizleme, QGIS 4.0+ / Qt6 tam uyumluluğu, gelişmiş Türkçe alfabetik sıralama ve hata yönetimi |
| **0.3.0** | 2026-06 | MAKS İdari Yapı API entegrasyonu ile Adres Sorgulama sekmesi eklendi (İl/İlçe/Mahalle/Yol/Numarataj) |
| **0.2.8** | 2026-05 | Bina ve Bağımsız Bölüm (Kat Mülkiyeti) sorgusu, akordiyon görünümü ve `QgsRelation` 1-N tablo desteği |
| **0.2.0** | 2026-04 | Pasif taşınmazlar için "Gittiği Parsel" hareket uyarıları ve detaylı popup bilgilendirmesi |
| **0.1.0** | 2026-04 | Günlük sorgu sayacı, HTTP 403 ve API limit bilgilendirme mekanizması |
| **0.0.9** | 2026-04 | QGIS 4.0 (Qt6) uyumluluk güncellemeleri ve ağ hata loglama geliştirmeleri |
| **0.0.6** | 2026-04 | Supabase tabanlı anonim telemetri altyapısı ve kullanım koşulları onay sistemi |
| **0.0.1** | 2026-03 | İlk sürüm — İl/İlçe/Mahalle/Ada/Parsel sorgusu, harita tıklama modu, EPSG:4326 katman yönetimi |

---

## 📄 Lisans / License

Bu proje **GNU General Public License v2 (GPL-2.0)** altında lisanslanmıştır. Ayrıntılar için [LICENSE](LICENSE) dosyasını inceleyebilirsiniz.

---

## 🤝 Katkıda Bulunma / Contributing

Her türlü hata bildirimi, öneri ve katkı memnuniyetle karşılanır:
1. Bu depoyu Fork'layın (`Fork`)
2. Yeni bir özellik dalı oluşturun (`git checkout -b feature/yeni-ozellik`)
3. Değişikliklerinizi commit edin (`git commit -m 'feat: Yeni özellik eklendi'`)
4. Dalınızı push edin (`git push origin feature/yeni-ozellik`)
5. Bir Pull Request açın

---

**Geliştirici:** Okan Şafak  
**İletişim & Destek:** [GitHub Issues](https://github.com/okansafak/qgistkgmplugin/issues) | [opengisturkiye@gmail.com](mailto:opengisturkiye@gmail.com)
