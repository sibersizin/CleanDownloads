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

## 📄 Lisans

Bu proje [MIT Lisansı](LICENSE) altında açık kaynak olarak sunulmuştur. Özgürce kullanabilir, değiştirebilir ve geliştirebilirsiniz.
