# 🗺 TKGM Parsel Sorgulama — QGIS Eklentisi / QGIS Plugin

TKGM (Tapu ve Kadastro Genel Müdürlüğü) CBS API'sini kullanarak QGIS ortamında **parsel sorgulama**, **geometri görüntüleme** ve **harita tıklama ile parsel bulma** işlemlerini gerçekleştiren bir QGIS eklentisidir.

A QGIS plugin that performs **parcel inquiry**, **geometry visualization**, and **parcel finding via map clicks** in the QGIS environment using the TKGM (General Directorate of Land Registry and Cadastre) CBS API.

---

## ✨ Özellikler / Features

| Özellik / Feature | Açıklama / Description |
|---|---|
| 🏛 **İdari Birim Seçimi / Administrative Selection** | İl → İlçe → Mahalle kademeli dropdown listeleri / Province → District → Neighborhood dropdowns |
| 🔍 **Ada/Parsel Sorgusu / Plot Inquiry** | Mahalle, Ada No ve Parsel No girerek detaylı sorgulama / Detailed query by entering Plot and Parcel numbers |
| 🎯 **Harita Tıklama Modu / Map Click Mode** | Haritaya tıklayarak o noktadaki parseli otomatik sorgulama / Automatically query the parcel at the clicked point |
| 🗺 **Geometri Görüntüleme / Geometry Display** | Bulunan parselin çokgen geometrisini QGIS katmanına ekleme / Add parcel polygon geometry to QGIS layers |
| 🔭 **Parsele Zoom / Zoom to Parcel** | Sorgulanan parsele otomatik yakınlaştırma / Automatic zoom to the queried parcel |
| 🏷 **Etiketleme / Labeling** | Ada/Parsel numarasını harita üzerinde etiketleme / Labeling Plot/Parcel numbers on the map |
| 📐 **CRS Desteği / CRS Support** | Farklı koordinat sistemleri arasında otomatik dönüşüm / Automatic conversion between different CRS |

---

## 📁 Proje Yapısı

```
tkgm_parsel_plugin/
├── __init__.py            # QGIS eklenti giriş noktası
├── metadata.txt           # Eklenti meta verileri
├── icon.png               # Araç çubuğu ikonu
├── tkgm_parsel.py         # Ana eklenti sınıfı (menü/toolbar entegrasyonu)
├── tkgm_panel.py          # Panel controller (sinyal/slot ve iş mantığı)
├── ui_tkgm_panel.py       # Arayüz tasarımı (widget oluşturma)
├── tkgm_api.py            # TKGM CBS API istemcisi
├── layer_manager.py       # QGIS katman yönetimi ve stil
├── map_tool.py            # Harita tıklama aracı
└── workers.py             # Arka plan iş parçacıkları (QThread)
```

---

## 🛠 Kurulum

### Yöntem 1 — ZIP ile Kurulum
1. [Releases](https://github.com/okansafak/qgistkgmplugin/releases) sayfasından en güncel `.zip` dosyasını indirin.
2. QGIS'i açın → **Eklentiler** → **Eklentileri Yönet ve Kur** → **ZIP'ten Kur** sekmesine gidin.
3. İndirdiğiniz `.zip` dosyasını seçin ve **Eklentiyi Kur** butonuna tıklayın.

### Yöntem 2 — Manuel Kurulum
1. Bu depoyu klonlayın veya ZIP olarak indirin.
2. `tkgm_parsel_plugin` klasörünü QGIS eklenti dizinine kopyalayın:
   ```
   Windows:  %APPDATA%\QGIS\QGIS3\profiles\default\python\plugins\
   Linux:    ~/.local/share/QGIS/QGIS3/profiles/default/python/plugins/
   macOS:    ~/Library/Application Support/QGIS/QGIS3/profiles/default/python/plugins/
   ```
3. QGIS'i yeniden başlatın.
4. **Eklentiler** → **Eklentileri Yönet ve Kur** → "TKGM Parsel Sorgulama" eklentisini aktifleştirin.

---

## 🚀 Kullanım

1. Araç çubuğundaki **TKGM Parsel Sorgulama** ikonuna tıklayın (veya menüden açın).
2. Sol tarafta açılan panelden:
   - **İdari Birim Sorgusu:** İl, İlçe ve Mahalle seçin → Ada ve Parsel numaralarını girin → **Parsel Sorgula** butonuna basın.
   - **Koordinat Sorgusu:** **Tıklama Modunu Aç** butonuna basın → Haritada ilgilendiğiniz noktaya tıklayın.
3. Parsel bilgileri panelde görüntülenir ve geometri haritaya eklenir.
4. **Parsele Git** butonu ile parsele yakınlaştırabilirsiniz.

---

## ⚙ Gereksinimler

- **QGIS** ≥ 3.16
- İnternet bağlantısı (TKGM CBS API erişimi için)

---

## 📡 Kullanılan API

- **TKGM CBS API:** `https://cbsapi.tkgm.gov.tr/megsiswebapi.v3.1/api`
- **TKGM Parsel Sorgu:** `https://parselsorgu.tkgm.gov.tr`

> ⚠ Bu eklenti, TKGM'nin kamuya açık CBS API servislerini kullanmaktadır. API yapısında değişiklik olması durumunda eklenti güncellenmelidir.

---

## 📋 Sürüm Geçmişi

| Sürüm | Tarih | Değişiklikler |
|---|---|---|
| **0.0.1** | 2026-03-28 | İlk sürüm — Modüler mimari, parsel sorgulama, tıklama modu |

---

## 📄 Lisans

Bu proje açık kaynak olarak sunulmaktadır. Detaylar için [LICENSE](LICENSE) dosyasına bakınız.

---

## 🤝 Katkıda Bulunma

1. Bu depoyu fork'layın
2. Yeni bir branch oluşturun (`git checkout -b ozellik/yeni-ozellik`)
3. Değişikliklerinizi commit edin (`git commit -m 'Yeni özellik eklendi'`)
4. Branch'inizi push edin (`git push origin ozellik/yeni-ozellik`)
5. Bir Pull Request oluşturun

---

**Geliştirici:** Okan Şafak  
**İletişim:** [GitHub](https://github.com/okansafak)
