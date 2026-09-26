# ⚡ CleanDownloads • Akıllı & Güvenli Dosya Düzenleyici

> **Sıfır Bağımlılık (Zero-Dependency) | Geri Al (Undo) Korumalı | Tek Tıkla Çalışan Masaüstü & CLI Asistanı**

---

## 🎯 Projenin Amacı ve Öne Çıkan Özellikleri

Klasik dosya düzenleyicilerin aksine bu araç, kullanıcıların veri kaybı yaşamasını engelleyen endüstriyel güvenlik önlemleriyle donatılmıştır:

* **↺ Geri Al (Undo / Ctrl+Z):** Yanlışlıkla çalıştırıldığında veya fikir değiştirildiğinde, tek tuşla tüm dosyaları orijinal konumlarına geri taşır ve boşalan klasörleri otomatik temizler.
* **🛡️ Çakışma Koruması (No Overwrite):** Hedefte aynı isimde dosya varsa üzerine yazmaz; `dosya (1).pdf` şeklinde akıllıca adlandırır.
* **🛑 İndirmeleri Koruma (Safe Filter):** Chrome, Edge, Firefox veya torrent gibi devam eden indirmeleri (`.crdownload`, `.part`, `.tmp`) tespit eder ve bozmaz.
* **⚡ O(1) Yüksek Performans:** 10.000 dosyayı 1 saniyenin altında sınıflandırır.
* **🎨 Çift Mod (Dual UI):** Windows/Mac'te Tkinter ile modern Koyu Tema (Dark Mode) masaüstü penceresi; sunucu/terminal ortamında ANSI renkli CLI arayüzü sunar.
* **📦 Sıfır Bağımlılık:** `pip install` gerektirmez, saf Python standart kütüphaneleriyle çalışır.

---

## 📂 Dosya Yapısı

```text
dosyasınıflandırma/
├── organizer.py        # Ana uygulama (Motor + GUI + CLI)
├── test_organizer.py   # Kapsamlı otomatik test paketi
└── README.md           # Dokümantasyon ve Video Kurgusu
```

---

## 🚀 Çalıştırma Seçenekleri

### 1. Doğrudan Çalıştırma (GUI veya Akıllı CLI)
```bash
python3 organizer.py
```
*(Windows'ta Tkinter yüklü olduğundan doğrudan şık Koyu Tema pencere açılır. Terminalde ise interaktif menü başlar.)*

### 2. Belirli Bir Klasörü Düzenleme
```bash
python3 organizer.py -t "/home/kullanici/Masaüstü" --auto
```

### 3. Yapılan İşlemi Geri Alma (Undo)
```bash
python3 organizer.py --undo
```

### 4. Simülasyon (Taşımadan Görme - Dry Run)
```bash
python3 organizer.py --dry-run
```

---

## 📦 Tek Tıkla Çalışan `.exe` Yapma (PyInstaller)

Kullanıcıların bilgisayarında Python olmadan çift tıklayıp kullanabilmesi için:

```bash
# 1. PyInstaller yükleyin (eğer yoksa)
pip install pyinstaller

# 2. Modern GUI Modunda Tek Dosya (.exe) Derleme:
# (--noconsole arka planda siyah terminal açılmasını engeller, saf pencere açar)
pyinstaller --onefile --noconsole --name "CleanDownloads" organizer.py

# 3. İsteğe bağlı: Terminal (CLI) sevenler için konsollu derleme:
pyinstaller --onefile --name "CleanDownloads_CLI" organizer.py
```
Çıkan `dist/CleanDownloads.exe` dosyasını Masaüstüne sabitleyip tek tıkla çalıştırabilirsiniz.

---

## 🎬 30 Saniyelik Instagram Reels / TikTok Viral Video Kurgusu

* **00:00 - 00:04 (Kanca - Hook):**
  * *Görüntü:* Yüzlerce dosyanın üst üste bindiği darmadağın bir Masaüstü / İndirilenler klasörü.
  * *Ses:* "Bilgisayarındaki İndirilenler klasörü de böyle bir çöplüğe mi döndü? Dosyalarını tek tıkla jilet gibi yapacak bir uygulama geliştirdim."
* **00:04 - 00:14 (Aksiyon - Action):**
  * *Görüntü:* `CleanDownloads` açılır. Tek bir tık: **"✨ TEK TIKLA DÜZENLE"**.
  * *Efekt:* Masaüstündeki yüzlerce dosya 1 saniye içinde tertemiz olur, klasörlerine uçar.
  * *Ses:* "Tek tıkla belgeler, görseller, kodlar ve arşivler anında kendi klasörlerine ayrılıyor."
* **00:14 - 00:22 (Vurucu Nokta - WOW / Güven Faktörü):**
  * *Görüntü:* Ekranda **"↺ Geri Al"** butonuna basılır. Bütün dosyalar anında eski orijinal yerlerine döner!
  * *Ses:* "En iyi özelliği ise yanlışlıkla düzenlerseniz 'Geri Al' dediğiniz an her şey anında eski yerine dönüyor. Aynı isimli dosyaları silmez, devam eden indirmeleri asla bozmaz."
* **00:22 - 00:30 (Yorum ve Takip Tuzağı - CTA):**
  * *Görüntü:* GitHub reposu veya indirme linki ekranda parlar.
  * *Ses:* "Hem Python kaynak kodunu hem de hazır `.exe` dosyasını paylaştım. Yorumlara **'DÜZENLE'** yazan herkese indirme linkini DM'den gönderiyorum. Takip etmeyi unutma!"
