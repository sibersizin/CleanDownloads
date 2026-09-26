#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Kapsamlı Test Paketi: organizer.py
Tüm uç durumları (edge cases), çakışma yönetimini ve Geri Al (Undo) mekanizmasını test eder.
"""

import os
import shutil
import tempfile
import unittest
from organizer import (
    organize_directory, 
    undo_last_organization, 
    get_unique_destination,
    is_ignored,
    CATEGORIES,
    EXTENSION_TO_CATEGORY
)

class TestOrganizer(unittest.TestCase):
    def setUp(self):
        # Her test için izole geçici çalışma klasörü
        self.test_dir = tempfile.mkdtemp(prefix="test_organizer_")

    def tearDown(self):
        # Test bittiğinde temizle
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)

    def create_dummy_file(self, filename: str, content: str = "test content") -> str:
        filepath = os.path.join(self.test_dir, filename)
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)
        return filepath

    def test_reverse_lookup_map(self):
        """Uzantıların O(1) haritasında doğru kategorilere eşleştiğini doğrula."""
        self.assertEqual(EXTENSION_TO_CATEGORY.get(".png"), "Görseller")
        self.assertEqual(EXTENSION_TO_CATEGORY.get(".pdf"), "Belgeler")
        self.assertEqual(EXTENSION_TO_CATEGORY.get(".zip"), "Arşivler")
        self.assertEqual(EXTENSION_TO_CATEGORY.get(".py"), "Yazılım_ve_Kod")
        self.assertEqual(EXTENSION_TO_CATEGORY.get(".exe"), "Uygulamalar")
        self.assertIsNone(EXTENSION_TO_CATEGORY.get(".bilinmeyen_uzanti_xyz"))

    def test_safe_destination_collision(self):
        """Aynı isimde dosya varsa üzerine yazmayıp (1), (2) ürettiğini doğrula."""
        folder = os.path.join(self.test_dir, "Görseller")
        os.makedirs(folder, exist_ok=True)
        
        # İlk dosyayı oluştur
        orig = os.path.join(folder, "resim.png")
        with open(orig, "w") as f:
            f.write("resim1")

        # İkinci için güvenli yol iste
        safe1 = get_unique_destination(folder, "resim.png")
        self.assertEqual(os.path.basename(safe1), "resim (1).png")
        with open(safe1, "w") as f:
            f.write("resim2")

        # Üçüncü için güvenli yol iste
        safe2 = get_unique_destination(folder, "resim.png")
        self.assertEqual(os.path.basename(safe2), "resim (2).png")

    def test_ignore_in_progress_downloads(self):
        """İndirme aşamasındaki geçici dosyaların ve sistem dosyalarının taşınmadığını doğrula."""
        self.assertTrue(is_ignored("/path/to/video.mp4.crdownload"))
        self.assertTrue(is_ignored("/path/to/archive.zip.part"))
        self.assertTrue(is_ignored("/path/to/file.tmp"))
        self.assertTrue(is_ignored("/path/to/.ds_store"))
        self.assertTrue(is_ignored("/path/to/.env"))
        self.assertTrue(is_ignored("/path/to/desktop.ini"))
        self.assertTrue(is_ignored("/path/to/Thumbs.db"))
        self.assertFalse(is_ignored("/path/to/normal_file.pdf"))

    def test_full_organization_and_undo_cycle(self):
        """Dosyaların doğru kategorilenmesi ve Geri Al (Undo) ile eksiksiz geri dönmesi."""
        # 1. Farklı kategorilerden dosyalar oluştur
        files = [
            "foto.jpg",
            "belge.pdf",
            "kod.py",
            "arsiv.zip",
            "program.exe",
            "notlar.txt",
            "bilinmeyen.xyz123"  # "Diğer" kategorisine gitmeli
        ]
        for f in files:
            self.create_dummy_file(f, f"data-{f}")

        # 2. Korunması gereken geçici bir dosya ekle
        self.create_dummy_file("indirme.zip.crdownload", "in-progress")

        # 3. Düzenle
        res = organize_directory(self.test_dir)
        self.assertEqual(res["total_moved"], len(files))
        self.assertEqual(res["total_skipped"], 1)  # .crdownload atlandı

        # Doğrula: Doğru klasörlere taşındı mı?
        self.assertTrue(os.path.exists(os.path.join(self.test_dir, "Görseller", "foto.jpg")))
        self.assertTrue(os.path.exists(os.path.join(self.test_dir, "Belgeler", "belge.pdf")))
        self.assertTrue(os.path.exists(os.path.join(self.test_dir, "Yazılım_ve_Kod", "kod.py")))
        self.assertTrue(os.path.exists(os.path.join(self.test_dir, "Arşivler", "arsiv.zip")))
        self.assertTrue(os.path.exists(os.path.join(self.test_dir, "Uygulamalar", "program.exe")))
        self.assertTrue(os.path.exists(os.path.join(self.test_dir, "Diğer", "bilinmeyen.xyz123")))
        
        # Geçici dosya hala ana dizinde durmalı
        self.assertTrue(os.path.exists(os.path.join(self.test_dir, "indirme.zip.crdownload")))

        # 4. Geri Al (Undo)
        undo_res = undo_last_organization(self.test_dir)
        self.assertEqual(undo_res["status"], "success")
        self.assertEqual(undo_res["restored_count"], len(files))

        # Doğrula: Tüm dosyalar ana dizine döndü mü?
        for f in files:
            self.assertTrue(os.path.exists(os.path.join(self.test_dir, f)))

        # Doğrula: Boş kalan klasörler temizlendi mi?
        self.assertFalse(os.path.exists(os.path.join(self.test_dir, "Görseller")))
        self.assertFalse(os.path.exists(os.path.join(self.test_dir, "Belgeler")))
        self.assertFalse(os.path.exists(os.path.join(self.test_dir, "Diğer")))

    def test_multi_session_undo(self):
        """Birden fazla kez ardışık düzenleme yapıldığında kademeli geri almanın çalıştığını doğrula."""
        # 1. Oturum 1: İki dosya düzenle
        self.create_dummy_file("resim1.png", "img1")
        self.create_dummy_file("yazi1.txt", "txt1")
        res1 = organize_directory(self.test_dir)
        self.assertEqual(res1["total_moved"], 2)

        # 2. Oturum 2: Sonradan iki yeni dosya daha gelsin ve düzenlensin
        self.create_dummy_file("resim2.png", "img2")
        self.create_dummy_file("yazi2.txt", "txt2")
        res2 = organize_directory(self.test_dir)
        self.assertEqual(res2["total_moved"], 2)

        # 3. İlk Geri Al: Yalnızca Oturum 2 geri dönmeli
        undo1 = undo_last_organization(self.test_dir)
        self.assertEqual(undo1["status"], "success")
        self.assertEqual(undo1["restored_count"], 2)
        self.assertEqual(undo1["remaining_sessions"], 1)
        self.assertTrue(os.path.exists(os.path.join(self.test_dir, "resim2.png")))
        self.assertTrue(os.path.exists(os.path.join(self.test_dir, "yazi2.txt")))
        # Oturum 1 dosyaları hala klasörlerinde olmalı
        self.assertTrue(os.path.exists(os.path.join(self.test_dir, "Görseller", "resim1.png")))
        self.assertTrue(os.path.exists(os.path.join(self.test_dir, "Belgeler", "yazi1.txt")))

        # 4. İkinci Geri Al: Artık Oturum 1 de geri dönmeli
        undo2 = undo_last_organization(self.test_dir)
        self.assertEqual(undo2["status"], "success")
        self.assertEqual(undo2["restored_count"], 2)
        self.assertEqual(undo2["remaining_sessions"], 0)
        self.assertTrue(os.path.exists(os.path.join(self.test_dir, "resim1.png")))
        self.assertTrue(os.path.exists(os.path.join(self.test_dir, "yazi1.txt")))

    def test_undo_collision_protection(self):
        """Geri alırken ana dizinde aynı isimde yeni dosya varsa üzerine yazmayıp güvenle adlandırdığını doğrula."""
        self.create_dummy_file("rapor.pdf", "eski-rapor")
        organize_directory(self.test_dir)
        self.assertTrue(os.path.exists(os.path.join(self.test_dir, "Belgeler", "rapor.pdf")))

        # Kullanıcı ana dizinde aynı isimde yeni bir dosya oluşturmuş olsun
        self.create_dummy_file("rapor.pdf", "yeni-olusan-rapor")

        # Geri al
        undo_res = undo_last_organization(self.test_dir)
        self.assertEqual(undo_res["status"], "success")
        self.assertEqual(undo_res["restored_count"], 1)

        # Yeni dosya duruyor olmalı ve eski dosya 'rapor (1).pdf' olarak kurtarılmış olmalı
        self.assertTrue(os.path.exists(os.path.join(self.test_dir, "rapor.pdf")))
        self.assertTrue(os.path.exists(os.path.join(self.test_dir, "rapor (1).pdf")))
        with open(os.path.join(self.test_dir, "rapor.pdf")) as f:
            self.assertEqual(f.read(), "yeni-olusan-rapor")
        with open(os.path.join(self.test_dir, "rapor (1).pdf")) as f:
            self.assertEqual(f.read(), "eski-rapor")

    def test_normalize_path(self):
        """Tırnaklı, tildeli veya boşluklu dizin yollarının hatasız normalize edildiğini doğrula."""
        from organizer import normalize_path
        home = os.path.expanduser("~")
        self.assertEqual(normalize_path(f'"{home}"'), home)
        self.assertEqual(normalize_path(f"'{home}'"), home)
        self.assertEqual(normalize_path("~"), home)

if __name__ == "__main__":
    unittest.main()
