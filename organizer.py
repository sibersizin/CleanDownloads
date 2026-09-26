#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CleanDownloads / Dosya Düzenleyici (Zero-Dependency)
====================================================
Yüksek performanslı, güvenli, geri alma (undo) destekli ve 
sıfır bağımlılıklı (pure standard library) otomatik dosya sınıflandırıcı.

Özellikler:
- Geri Alma (Undo): Yapılan son işlemi tek tuşla geri döndürür.
- Çakışma Koruması: Aynı isimde dosya varsa üzerine yazmaz, 'dosya (1).ext' türetir.
- Güvenli Filtreleme: Devam eden indirmeleri (.crdownload, .part vb.), sistem ve gizli dosyaları bozmaz.
- Sıfır Bağımlılık: Harici 'pip' kütüphanesi gerektirmez.
- Çift Mod: Tkinter varsa modern Dark Mode GUI, yoksa ANSI Terminal UI.
"""

import os
import sys
import shutil
import json
import time
import stat
from datetime import datetime
from pathlib import Path

# ==============================================================================
# 1. KATEGORİ HAVUZU VE TERS SÖZLÜK (O(1) LOOKUP)
# ==============================================================================

CATEGORIES = {
    "Görseller": [
        ".png", ".jpg", ".jpeg", ".gif", ".webp", ".svg", ".ico", 
        ".bmp", ".tiff", ".heic", ".raw"
    ],
    "Videolar": [
        ".mp4", ".mkv", ".avi", ".mov", ".wmv", ".flv", ".webm", ".m4v"
    ],
    "Müzikler": [
        ".mp3", ".wav", ".flac", ".aac", ".ogg", ".m4a", ".wma"
    ],
    "Belgeler": [
        ".pdf", ".docx", ".doc", ".txt", ".xlsx", ".xls", ".pptx", 
        ".ppt", ".csv", ".epub", ".rtf", ".odt"
    ],
    "Arşivler": [
        ".zip", ".rar", ".7z", ".tar", ".gz", ".bz2", ".xz", ".iso"
    ],
    "Yazılım_ve_Kod": [
        ".py", ".js", ".ts", ".html", ".css", ".cpp", ".c", ".h", 
        ".cs", ".java", ".json", ".xml", ".yaml", ".yml", ".sql", 
        ".sh", ".bash", ".php", ".rs", ".go"
    ],
    "Uygulamalar": [
        ".exe", ".msi", ".dmg", ".pkg", ".deb", ".rpm", ".AppImage", 
        ".bat", ".cmd", ".lnk"
    ],
    "Tasarım": [
        ".psd", ".ai", ".xd", ".fig", ".sketch", ".blend", ".dwg"
    ]
}

# Hızlı arama için ters harita oluşturma (O(1) Karmaşıklık)
EXTENSION_TO_CATEGORY = {}
for category, extensions in CATEGORIES.items():
    for ext in extensions:
        EXTENSION_TO_CATEGORY[ext.lower()] = category

# Dokunulmaması gereken geçici, sistem ve özel uzantılar
IGNORE_EXTENSIONS = {
    ".crdownload",  # Chrome / Edge geçici indirme
    ".part",        # Firefox geçici indirme
    ".tmp",         # Genel geçici dosya
    ".download",    # Safari geçici indirme
    ".!ut",         # uTorrent geçici dosya
    ".aria2",       # Aria2 indirme
    ".lock",        # Kilit dosyaları
    ".swp"          # Vim swap dosyaları
}

# Dokunulmaması gereken özel dosya isimleri
IGNORE_FILENAMES = {
    ".ds_store", "thumbs.db", "desktop.ini", ".git", ".gitignore",
    "clean_history.json", ".organizer_history.json"
}

HISTORY_FILENAME = ".organizer_history.json"

# ==============================================================================
# 2. YARDIMCI VE GÜVENLİK FONKSİYONLARI
# ==============================================================================

def get_default_downloads_dir() -> str:
    """İşletim sistemine ve diline göre en doğru İndirilenler klasörünü bulur."""
    home = os.path.expanduser("~")
    
    # 1. Windows Kayıt Defteri (Registry) Kontrolü (D:\ sürücüsü veya OneDrive taşımaları dahil)
    if sys.platform == "win32":
        try:
            import winreg
            sub_key = r"Software\Microsoft\Windows\CurrentVersion\Explorer\User Shell Folders"
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, sub_key) as key:
                # Standart Downloads GUID veya doğrudan yol
                for guid in ("{374DE290-123F-4565-9164-39C4925E467B}", "{7D83EE9B-2244-4E70-B1F5-56B302E603B0}"):
                    try:
                        val, _ = winreg.QueryValueEx(key, guid)
                        val = os.path.expandvars(val)
                        if os.path.isdir(val):
                            return val
                    except Exception:
                        pass
        except Exception:
            pass

    # 2. Linux XDG kontrolü
    xdg_config = os.path.join(home, ".config", "user-dirs.dirs")
    if os.path.exists(xdg_config):
        try:
            with open(xdg_config, "r", encoding="utf-8") as f:
                for line in f:
                    if line.startswith("XDG_DOWNLOAD_DIR"):
                        raw_path = line.split("=", 1)[1].strip().strip('"')
                        resolved = raw_path.replace("$HOME", home)
                        if os.path.isdir(resolved):
                            return resolved
        except Exception:
            pass

    # 3. Standart İngilizce ve Türkçe yolları dene
    candidates = [
        os.path.join(home, "Downloads"),
        os.path.join(home, "İndirilenler"),
        os.path.join(home, "indirilenler"),
        os.path.join(home, "Desktop"),
        os.path.join(home, "Masaüstü")
    ]
    for path in candidates:
        if os.path.isdir(path):
            return path
            
    return home

def normalize_path(path_str: str) -> str:
    """
    Kullanıcının girdiği veya yapıştırdığı yolu temizler ve normalize eder.
    Tırnak işaretleri, boşluklar, ~ (home) ve %USERPROFILE% gibi değişkenleri çözer.
    """
    if not path_str:
        return ""
    cleaned = path_str.strip().strip("'\"").strip()
    expanded = os.path.expanduser(cleaned)
    expanded = os.path.expandvars(expanded)
    return os.path.abspath(expanded)

def get_unique_destination(folder_path: str, filename: str) -> str:
    """
    Aynı isimde dosya varsa üzerine yazmaz!
    'rapor.pdf' -> 'rapor (1).pdf', 'rapor (2).pdf' şeklinde türetir.
    """
    destination = os.path.join(folder_path, filename)
    if not os.path.exists(destination):
        return destination

    stem, ext = os.path.splitext(filename)
    counter = 1
    while True:
        new_filename = f"{stem} ({counter}){ext}"
        destination = os.path.join(folder_path, new_filename)
        if not os.path.exists(destination):
            return destination
        counter += 1

def is_ignored(filepath: str) -> bool:
    """Dosyanın atlanması gereken bir sistem veya geçici dosya olup olmadığını kontrol eder."""
    filename = os.path.basename(filepath)
    lower_name = filename.lower()
    
    # 1. Gizli dosyalar (dotfiles) ve özel dosyalar
    if lower_name.startswith(".") or lower_name in IGNORE_FILENAMES:
        return True
        
    # 2. Geçici indirme uzantıları
    _, ext = os.path.splitext(lower_name)
    if ext in IGNORE_EXTENSIONS:
        return True
        
    # 3. Çalışan script veya PyInstaller .exe dosyasının kendisi
    try:
        abs_file = os.path.abspath(filepath)
        if getattr(sys, 'frozen', False):
            if os.path.samefile(abs_file, sys.executable):
                return True
        if os.path.samefile(abs_file, os.path.abspath(sys.argv[0])):
            return True
    except Exception:
        pass

    # 4. Windows sistem ve gizli dosya öznitelikleri (Hidden / System file attributes)
    if sys.platform == "win32":
        try:
            attrs = os.stat(filepath).st_file_attributes
            if attrs & (stat.FILE_ATTRIBUTE_HIDDEN | stat.FILE_ATTRIBUTE_SYSTEM):
                return True
        except Exception:
            pass
        
    return False

# ==============================================================================
# 3. ÇEKİRDEK İŞ MANTIĞI: DÜZENLEME VE GERİ ALMA (UNDO)
# ==============================================================================

def organize_directory(target_dir: str, dry_run: bool = False) -> dict:
    """
    Klasörü düzenler. İşlemleri geri alınabilir günlük kaydına (manifest) yazar.
    Dönüş: Özet istatistik sözlüğü.
    """
    target_path = os.path.abspath(target_dir)
    if not os.path.isdir(target_path):
        raise ValueError(f"Geçersiz dizin: {target_path}")

    # Mevcut kategori isimleri (kendi oluşturduğumuz klasörleri tekrar işlememek için)
    category_folder_names = set(CATEGORIES.keys()) | {"Diğer"}

    history_entries = []
    category_stats = {}
    total_moved = 0
    total_skipped = 0

    entries = os.listdir(target_path)
    
    for filename in entries:
        source_path = os.path.join(target_path, filename)

        # Klasörleri atla (özellikle zaten oluşturulmuş kategori klasörlerini)
        if os.path.isdir(source_path):
            continue

        # Korunan/geçici dosyaları atla
        if is_ignored(source_path):
            total_skipped += 1
            continue

        # Uzantıyı belirle
        _, ext = os.path.splitext(filename)
        ext_lower = ext.lower()
        
        # Kategoriyi O(1) hızla bul
        target_category = EXTENSION_TO_CATEGORY.get(ext_lower, "Diğer")
        category_dir = os.path.join(target_path, target_category)

        # Güvenli hedef yol (çakışma kontrolü)
        dest_path = get_unique_destination(category_dir, filename)

        if not dry_run:
            try:
                os.makedirs(category_dir, exist_ok=True)
                shutil.move(source_path, dest_path)
                
                history_entries.append({
                    "original": source_path,
                    "current": dest_path,
                    "filename": filename,
                    "category": target_category
                })
                category_stats[target_category] = category_stats.get(target_category, 0) + 1
                total_moved += 1
            except (PermissionError, OSError):
                # Windows'ta kilitli veya kullanımda olan dosyaları atla
                total_skipped += 1
                continue
        else:
            category_stats[target_category] = category_stats.get(target_category, 0) + 1
            total_moved += 1

    # İşlem geçmişini kaydet (Çok Kademeli Geri Alma / Multi-Session Undo Stack)
    if not dry_run and history_entries:
        history_path = os.path.join(target_path, HISTORY_FILENAME)
        sessions = []
        if os.path.exists(history_path):
            try:
                with open(history_path, "r", encoding="utf-8") as f:
                    old_data = json.load(f)
                    if isinstance(old_data, dict):
                        if "sessions" in old_data and isinstance(old_data["sessions"], list):
                            sessions = old_data["sessions"]
                        elif "moves" in old_data:
                            # Eski tek oturumlu format ile tam geriye dönük uyumluluk
                            sessions = [old_data]
            except Exception:
                sessions = []

        new_session = {
            "timestamp": datetime.now().isoformat(),
            "target_dir": target_path,
            "moved_count": total_moved,
            "moves": history_entries
        }
        sessions.append(new_session)

        # Atomic yazma: geçici dosyaya yazıp replace ile değiştir (veri kaybını sıfırlar)
        temp_history = history_path + ".tmp"
        try:
            with open(temp_history, "w", encoding="utf-8") as f:
                json.dump({"sessions": sessions}, f, ensure_ascii=False, indent=2)
            os.replace(temp_history, history_path)
        except Exception as e:
            print(f"[!] Geçmiş günlüğü yazılamadı: {e}", file=sys.stderr)
            if os.path.exists(temp_history):
                try:
                    os.remove(temp_history)
                except Exception:
                    pass

    return {
        "status": "success",
        "target_dir": target_path,
        "total_moved": total_moved,
        "total_skipped": total_skipped,
        "categories": category_stats,
        "dry_run": dry_run
    }

def undo_last_organization(target_dir: str) -> dict:
    """
    Son yapılan sınıflandırma işlemini tersine çevirir (Çok Kademeli).
    Her geri alma çağrısı en son yapılan oturumu geri alır.
    Dosyaları orijinal konumlarına taşır ve boş kalan kategori klasörlerini siler.
    """
    target_path = os.path.abspath(target_dir)
    history_path = os.path.join(target_path, HISTORY_FILENAME)

    if not os.path.exists(history_path):
        return {
            "status": "error",
            "message": "Geri alınacak bir işlem geçmişi bulunamadı!"
        }

    try:
        with open(history_path, "r", encoding="utf-8") as f:
            history_data = json.load(f)
    except Exception as e:
        return {
            "status": "error",
            "message": f"Geçmiş dosyası okunamadı: {e}"
        }

    sessions = []
    if isinstance(history_data, dict):
        if "sessions" in history_data and isinstance(history_data["sessions"], list):
            sessions = history_data["sessions"]
        elif "moves" in history_data:
            sessions = [history_data]

    if not sessions:
        try:
            os.remove(history_path)
        except Exception:
            pass
        return {
            "status": "error",
            "message": "Geri alınacak bir işlem oturumu kalmadı!"
        }

    # En son oturumu yığından (stack) çek
    last_session = sessions.pop()
    moves = last_session.get("moves", [])
    restored_count = 0
    failed_count = 0
    folders_to_check = set()

    for item in moves:
        current_path = item["current"]
        original_path = item["original"]

        if os.path.exists(current_path):
            try:
                # Orijinal konumda çakışma varsa bile dosya kaybını engelle (numaralandır)
                safe_orig = get_unique_destination(os.path.dirname(original_path), os.path.basename(original_path))
                shutil.move(current_path, safe_orig)
                restored_count += 1
                folders_to_check.add(os.path.dirname(current_path))
            except Exception:
                failed_count += 1
        else:
            failed_count += 1

    # Boşalan kategori klasörlerini temizle
    for folder in folders_to_check:
        try:
            if os.path.exists(folder) and not os.listdir(folder):
                os.rmdir(folder)
        except Exception:
            pass

    # Kalan oturum varsa güncelle, hepsi bittiyse geçmiş dosyasını sil
    if sessions:
        temp_history = history_path + ".tmp"
        try:
            with open(temp_history, "w", encoding="utf-8") as f:
                json.dump({"sessions": sessions}, f, ensure_ascii=False, indent=2)
            os.replace(temp_history, history_path)
        except Exception:
            pass
    else:
        try:
            os.remove(history_path)
        except Exception:
            pass

    return {
        "status": "success",
        "restored_count": restored_count,
        "failed_count": failed_count,
        "remaining_sessions": len(sessions),
        "timestamp": last_session.get("timestamp")
    }

# ==============================================================================
# 4. GÖRSEL CLI ARAYÜZÜ (ANSI RENKLERİ VE TABLO)
# ==============================================================================

class Colors:
    CYAN = "\033[96m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    RED = "\033[91m"
    BOLD = "\033[1m"
    DIM = "\033[2m"
    RESET = "\033[0m"

    @classmethod
    def disable(cls):
        cls.CYAN = cls.GREEN = cls.YELLOW = cls.RED = cls.BOLD = cls.DIM = cls.RESET = ""

# Windows konsolunda ANSI renklerini aktif et
if sys.platform == "win32":
    try:
        import ctypes
        kernel32 = ctypes.windll.kernel32
        kernel32.SetConsoleMode(kernel32.GetStdHandle(-11), 7)
    except Exception:
        Colors.disable()

def print_banner():
    banner = f"""
{Colors.CYAN}{Colors.BOLD}╔═══════════════════════════════════════════════════════════╗
║               ⚡ CLEAN DOWNLOADS & ORGANIZER ⚡            ║
║       Akıllı, Güvenli ve Geri Alınabilir Dosya Asistanı   ║
╚═══════════════════════════════════════════════════════════╝{Colors.RESET}"""
    print(banner)

def run_cli_interactive(default_dir: str):
    print_banner()
    current_target = default_dir

    try:
        while True:
            print(f"\n{Colors.BOLD}Aktif Hedef Dizin:{Colors.RESET} {Colors.CYAN}{current_target}{Colors.RESET}")
            print(f"{Colors.DIM}Seçenekler: [ENTER] Düzenle | [U] Geri Al (Undo) | [F] Klasör Değiştir | [Q / Ctrl+C] Çıkış{Colors.RESET}")
            
            try:
                choice = input(f"{Colors.YELLOW}İşlem seçin [ENTER / U / F / Q]: {Colors.RESET}").strip().lower()
            except (KeyboardInterrupt, EOFError):
                print(f"\n\n{Colors.CYAN}[✓] Çıkış yapıldı (Ctrl+C). İyi günler!{Colors.RESET}")
                break

            if choice in ("q", "cikis", "exit"):
                print(f"\n{Colors.DIM}Çıkış yapıldı. İyi günler!{Colors.RESET}")
                break

            if choice == "f":
                try:
                    custom = input(f"{Colors.CYAN}Yeni hedef klasör yolunu girin: {Colors.RESET}").strip()
                except (KeyboardInterrupt, EOFError):
                    print(f"\n\n{Colors.CYAN}[✓] Çıkış yapıldı (Ctrl+C). İyi günler!{Colors.RESET}")
                    break
                norm = normalize_path(custom)
                if norm and os.path.isdir(norm):
                    current_target = norm
                    print(f"{Colors.GREEN}[✓] Hedef dizin güncellendi: {current_target}{Colors.RESET}")
                else:
                    print(f"{Colors.RED}[!] Geçersiz veya bulunamayan klasör yolu: '{custom}'{Colors.RESET}")
                continue

            if choice == "u":
                print(f"\n{Colors.YELLOW}[↺] Geri alma işlemi başlatılıyor...{Colors.RESET}")
                result = undo_last_organization(current_target)
                if result["status"] == "success":
                    print(f"{Colors.GREEN}[✔] {result['restored_count']} dosya başarıyla eski yerine taşındı!{Colors.RESET}")
                else:
                    print(f"{Colors.RED}[X] {result['message']}{Colors.RESET}")
                print(f"{Colors.DIM}------------------------------------------------------------{Colors.RESET}")
                continue

            # Varsayılan (ENTER) -> Düzenle
            print(f"\n{Colors.CYAN}[⚙] Düzenleniyor... Hedef: {current_target}{Colors.RESET}")
            start_time = time.time()
            
            try:
                result = organize_directory(current_target)
                elapsed = time.time() - start_time

                print(f"\n{Colors.GREEN}{Colors.BOLD}[✔] TAMAMLANDI! ({elapsed:.2f} saniye){Colors.RESET}")
                print(f"┌──────────────────────────────┬───────────────┐")
                print(f"│ Kategori                     │ Dosya Sayısı  │")
                print(f"├──────────────────────────────┼───────────────┤")
                
                for cat, count in sorted(result["categories"].items(), key=lambda x: x[1], reverse=True):
                    print(f"│ {cat:<28} │ {count:>13} │")
                    
                print(f"├──────────────────────────────┼───────────────┤")
                print(f"│ {Colors.BOLD}Toplam Taşınan{Colors.RESET}               │ {result['total_moved']:>13} │")
                print(f"│ {Colors.DIM}Korunan / Atlanan{Colors.RESET}            │ {result['total_skipped']:>13} │")
                print(f"└──────────────────────────────┴───────────────┘")
                print(f"{Colors.DIM}💡 İpucu: İşlemi geri almak için 'U' tuşlayabilir, çıkmak için [Ctrl+C] basabilirsiniz.{Colors.RESET}")
                print(f"{Colors.DIM}------------------------------------------------------------{Colors.RESET}")

            except Exception as e:
                print(f"{Colors.RED}[!] Beklenmedik hata oluştu: {e}{Colors.RESET}")

    except KeyboardInterrupt:
        print(f"\n\n{Colors.CYAN}[✓] Çıkış yapıldı (Ctrl+C). İyi günler!{Colors.RESET}")

# ==============================================================================
# 5. MODERN DARK-MODE GUI (TKINTER - ZERO DEPENDENCY)
# ==============================================================================

def launch_gui(initial_dir: str):
    """
    Tkinter ile çalışan modern, koyu temalı pencere arayüzü.
    Python yüklü Windows/macOS/Linux'ta harici paket olmadan anında açılır.
    """
    import tkinter as tk
    from tkinter import filedialog, messagebox

    # Windows'ta 4K ve yüksek DPI ekranlarda bulanıklığı engelle (High DPI Aware)
    if sys.platform == "win32":
        try:
            import ctypes
            ctypes.windll.shcore.SetProcessDpiAwareness(1)
        except Exception:
            pass

    root = tk.Tk()
    root.title("CleanDownloads • Akıllı Dosya Düzenleyici")
    root.geometry("540x520")
    root.resizable(False, False)

    # Koyu Tema Renk Paleti (Modern Slate / Dark)
    BG_DARK = "#12141a"
    CARD_BG = "#1e222d"
    ACCENT_GREEN = "#10b981"
    ACCENT_HOVER = "#059669"
    ACCENT_BLUE = "#3b82f6"
    TEXT_LIGHT = "#f3f4f6"
    TEXT_MUTED = "#9ca3af"
    BORDER_COLOR = "#2e3444"

    root.configure(bg=BG_DARK)

    # Başlık Alanı
    header_frame = tk.Frame(root, bg=BG_DARK)
    header_frame.pack(fill="x", padx=25, pady=(20, 10))

    title_lbl = tk.Label(
        header_frame, 
        text="⚡ CleanDownloads", 
        font=("Segoe UI", 18, "bold"), 
        fg=TEXT_LIGHT, 
        bg=BG_DARK
    )
    title_lbl.pack(anchor="w")

    subtitle_lbl = tk.Label(
        header_frame, 
        text="İndirilenler klasörünüzü tek tıkla jilet gibi düzenleyin.", 
        font=("Segoe UI", 10), 
        fg=TEXT_MUTED, 
        bg=BG_DARK
    )
    subtitle_lbl.pack(anchor="w", pady=(2, 0))

    # Dizin Seçim Kartı
    path_card = tk.Frame(root, bg=CARD_BG, highlightbackground=BORDER_COLOR, highlightthickness=1)
    path_card.pack(fill="x", padx=25, pady=10)

    selected_path_var = tk.StringVar(value=initial_dir)

    path_label = tk.Label(
        path_card, 
        text="Hedef Klasör:", 
        font=("Segoe UI", 9, "bold"), 
        fg=TEXT_MUTED, 
        bg=CARD_BG
    )
    path_label.pack(anchor="w", padx=12, pady=(10, 2))

    entry_frame = tk.Frame(path_card, bg=CARD_BG)
    entry_frame.pack(fill="x", padx=12, pady=(0, 12))

    path_entry = tk.Entry(
        entry_frame, 
        textvariable=selected_path_var, 
        font=("Segoe UI", 9), 
        bg="#171922", 
        fg=TEXT_LIGHT, 
        relief="flat", 
        highlightthickness=1, 
        highlightbackground=BORDER_COLOR
    )
    path_entry.pack(side="left", fill="x", expand=True, ipady=4, padx=(0, 8))

    def choose_folder():
        folder = filedialog.askdirectory(initialdir=selected_path_var.get())
        if folder:
            selected_path_var.set(folder)

    browse_btn = tk.Button(
        entry_frame, 
        text="Gözat...", 
        font=("Segoe UI", 9, "bold"), 
        bg=ACCENT_BLUE, 
        fg="white", 
        relief="flat", 
        cursor="hand2", 
        command=choose_folder, 
        padx=10, pady=2
    )
    browse_btn.pack(side="right")

    # Sonuç / Log Paneli
    result_card = tk.Frame(root, bg=CARD_BG, highlightbackground=BORDER_COLOR, highlightthickness=1)
    result_card.pack(fill="both", expand=True, padx=25, pady=10)

    status_var = tk.StringVar(value="Düzenlemeye hazır. 'Tek Tıkla Düzenle' butonuna basın.")
    status_label = tk.Label(
        result_card, 
        textvariable=status_var, 
        font=("Segoe UI", 9), 
        fg=TEXT_MUTED, 
        bg=CARD_BG, 
        wraplength=460, 
        justify="left"
    )
    status_label.pack(anchor="w", padx=12, pady=10)

    # Buton Fonksiyonları
    def on_organize():
        target = normalize_path(selected_path_var.get())
        if not target or not os.path.isdir(target):
            messagebox.showerror("Hata", f"Lütfen geçerli bir klasör seçin!\n'{selected_path_var.get()}' bulunamadı.")
            return

        try:
            res = organize_directory(target)
            cat_text = "\n".join([f" • {k}: {v} dosya" for k, v in res["categories"].items()])
            msg = f"✔ Başarıyla Tamamlandı!\nToplam Düzenlenen: {res['total_moved']} dosya\nAtlanan / Korunan: {res['total_skipped']} dosya\n\nKategoriler:\n{cat_text or ' (Yeni dosya bulunamadı)'}"
            status_var.set(msg)
            messagebox.showinfo("Başarılı", f"{res['total_moved']} dosya başarıyla kategorilere ayrıldı!")
        except Exception as e:
            messagebox.showerror("Hata", f"İşlem sırasında hata: {e}")

    def on_undo():
        target = normalize_path(selected_path_var.get())
        if not target or not os.path.isdir(target):
            messagebox.showerror("Hata", f"Lütfen geçerli bir klasör seçin!\n'{selected_path_var.get()}' bulunamadı.")
            return

        res = undo_last_organization(target)
        if res["status"] == "success":
            rem = res.get('remaining_sessions', 0)
            status_var.set(f"↺ Geri Alma Başarılı!\n{res['restored_count']} dosya eski yerine taşındı.\n(Kalan geri alma adımı: {rem})")
            messagebox.showinfo("Geri Alındı", f"{res['restored_count']} dosya başarıyla eski konumuna döndürüldü!")
        else:
            messagebox.showwarning("Bilgi", res["message"])

    # Eylem Butonları
    btn_frame = tk.Frame(root, bg=BG_DARK)
    btn_frame.pack(fill="x", padx=25, pady=(5, 20))

    action_btn = tk.Button(
        btn_frame, 
        text="✨ TEK TIKLA DÜZENLE", 
        font=("Segoe UI", 11, "bold"), 
        bg=ACCENT_GREEN, 
        fg="white", 
        relief="flat", 
        cursor="hand2", 
        command=on_organize, 
        pady=8
    )
    action_btn.pack(side="left", fill="x", expand=True, padx=(0, 6))

    undo_btn = tk.Button(
        btn_frame, 
        text="↺ Geri Al (Undo)", 
        font=("Segoe UI", 10, "bold"), 
        bg="#374151", 
        fg=TEXT_LIGHT, 
        relief="flat", 
        cursor="hand2", 
        command=on_undo, 
        pady=8, padx=14
    )
    undo_btn.pack(side="right")

    root.mainloop()

# ==============================================================================
# 6. GİRİŞ NOKTASI (ENTRY POINT)
# ==============================================================================

def main():
    default_dir = get_default_downloads_dir()

    # CLI bayraklarını kontrol et
    args = sys.argv[1:]
    
    if "--help" in args or "-h" in args:
        print_banner()
        print("""
Kullanım:
  python organizer.py [SEÇENEKLER]

Seçenekler:
  --cli, -c          Terminal (CLI) arayüzünde çalışmaya zorla
  --undo, -u         Son yapılan işlemi doğrudan geri al
  --target, -t DİZİN Belirtilen dizini hedef al
  --auto, -y         Onay sormadan doğrudan düzenle (otomasyon için)
  --dry-run          Dosyaları taşımadan simülasyon yap
  --help, -h         Bu yardım ekranını göster
        """)
        return

    # Hedef dizin parametresi belirtilmişse güncelle
    if "-t" in args:
        try:
            default_dir = normalize_path(args[args.index("-t") + 1])
        except IndexError:
            pass
    elif "--target" in args:
        try:
            default_dir = normalize_path(args[args.index("--target") + 1])
        except IndexError:
            pass

    if "--undo" in args or "-u" in args:
        res = undo_last_organization(default_dir)
        if res["status"] == "success":
            print(f"{Colors.GREEN}[✔] {res['restored_count']} dosya eski yerine taşındı.{Colors.RESET}")
        else:
            print(f"{Colors.RED}[X] {res['message']}{Colors.RESET}")
        return

    if "--auto" in args or "-y" in args or "--dry-run" in args:
        dry_run = "--dry-run" in args
        print_banner()
        print(f"\n{Colors.CYAN}[⚙] Doğrudan düzenleniyor... Hedef: {default_dir}{Colors.RESET}")
        res = organize_directory(default_dir, dry_run=dry_run)
        print(f"{Colors.GREEN}[✔] İşlem tamamlandı! Toplam düzenlenen: {res['total_moved']}, atlanan: {res['total_skipped']}{Colors.RESET}")
        return

    force_cli = "--cli" in args or "-c" in args or not sys.stdin.isatty()
    
    # GUI başlatmayı dene; Tkinter yoksa veya --cli seçilmişse CLI çalıştır
    if not force_cli:
        try:
            launch_gui(default_dir)
            return
        except (ImportError, Exception):
            # Tkinter desteklenmiyorsa sessizce CLI'a düş
            pass

    run_cli_interactive(default_dir)

if __name__ == "__main__":
    try:
        main()
    except (KeyboardInterrupt, EOFError):
        print(f"\n\n{Colors.CYAN}[✓] Çıkış yapıldı (Ctrl+C). İyi günler!{Colors.RESET}")
        sys.exit(0)
