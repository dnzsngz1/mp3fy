# 🎵 MP3fy - Spotify to MP3 PowerShell & CLI Tool

<div align="center">

### MP3fy (PowerShell & CLI Edition)

![Python Version](https://img.shields.io/badge/python-3.9%2B-blue?style=for-the-badge&logo=python)
![PowerShell](https://img.shields.io/badge/PowerShell-5.1%20%7C%207%2B-5391FE?style=for-the-badge&logo=powershell&logoColor=white)
![Platform](https://img.shields.io/badge/platform-Windows%20%7C%20Linux-blueviolet?style=for-the-badge)
![CLI](https://img.shields.io/badge/interface-Terminal%20CLI-black?style=for-the-badge)

**Spotify Çalma Listesi, Albüm ve Şarkı bağlantılarından yüksek kaliteli MP3 (320kbps) dönüştürücü ve ID3 etiketleyici Terminal Aracı.**  
*Convert and download Spotify playlists, albums, and tracks to 320kbps MP3 files with full ID3 metadata and album art directly from your PowerShell terminal.*

---

📖 **Kılavuzlar / Guides:**  
🇹🇷 [**Türkçe Kullanım Kılavuzu**](KULLANIM_KILAVUZU.md) | 🇬🇧 [**English User Guide**](USER_GUIDE.md)

---

</div>

## ✨ Temel Özellikler / Key Features

- ⚡ **PowerShell & Windows Desteği:** Windows PowerShell 5.1, PowerShell Core 7+ ve CMD ile tam uyumlu; tek tıkla / tek komutla kurulum.
- 🎧 **Doğrudan Terminal Komutu (`mp3fy`):** Kurulumdan sonra sistemdeki herhangi bir dizinde doğrudan `mp3fy` yazarak çalıştırabilirsiniz (User PATH ve `$PROFILE` entegrasyonu).
- 🧙‍♂️ **Etkileşimli Terminal Sihirbazı:** Argüman girmeden `mp3fy` yazıldığında renkli ve kullanımı kolay bir arayüzle Spotify bağlantısı, kalite, bölüm ve kayıt yeri sorar.
- 🚀 **Parametreli Hızlı Kullanım:** `mp3fy <url> [seçenekler]` formatında tek satırda otomatik indirme.
- 📦 **100'lük Bölümleme (Batching):** 100, 200, 500+ şarkılık büyük listeleri 100'erlik dilimlere ayırır; ister belirli bir bölümü (`--batch 1`), ister tümünü indirin.
- 🏷️ **Eksiksiz ID3 Etiketleme / ID3v2.3 Tagging:** Orijinal yüksek çözünürlüklü kapak görseli (APIC), Sanatçı (TPE1), Albüm (TALB), Şarkı Adı (TIT2), Yıl (TDRC) ve Parça No (TRCK).
- 📊 **Canlı İlerleme Çubuğu & UTF-8 Desteği:** Rich kütüphanesiyle canlı indirme hızı (MB/s), kalan süre ve şarkı durum bildirimleri. Windows konsollarında UTF-8 desteği.
- 📁 **Özel İndirme Klasörü:** Varsayılan olarak `Music` (Müziğim) dizinine kaydeder veya `-o` ile dilediğiniz hedef klasörü belirleyebilirsiniz.
- ⚙️ **Özelleştirilebilir Kalite (Bitrate):** 320 kbps (Stüdyo Kalitesi), 256 kbps, 192 kbps veya 128 kbps seçenekleri.

---

## 🚀 Hızlı Başlangıç & Kurulum / Quick Start

### 🪟 Windows / PowerShell Kurulumu

#### 1. Depoyu Klonlayın veya İndirin
```powershell
git clone https://github.com/kullaniciadi/mp3fy.git
cd mp3fy
```

#### 2. Kurulum Scriptini Çalıştırın
```powershell
# Script çalıştırma izni vermek için (gerekirse):
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass

# Kurulumu başlatın:
.\install.ps1
```
> Bu script sanal ortamı kurar, bağımlılıkları yükler, `mp3fy.cmd` / `mp3fy.ps1` başlatıcılarını oluşturur, kullanıcı PATH değişkenine `$HOME\bin` ekler ve PowerShell profilinize (`$PROFILE`) `mp3fy` kısayolunu entegre eder.

#### 3. Çalıştırın
Kurulum bittikten sonra PowerShell'de herhangi bir klasördeyken:
```powershell
mp3fy
```
veya doğrudan hızlı başlatıcı:
```powershell
.\run.ps1
```

---

### 🐧 Linux Kurulumu

```bash
chmod +x install.sh
./install.sh
mp3fy
```

---

## 💻 Kullanım / Usage

### 1. Etkileşimli Mod (Sihirbaz)
Hiçbir parametre vermeden çalıştırıldığında etkileşimli mod açılır:
```powershell
mp3fy
```
Sizden Spotify linkini alır, çalma listesi/şarkı detaylarını listeler ve onayınızı alarak indirmeyi başlatır.

### 2. Komut Satırı Parametreleri (Direct CLI)
```powershell
# Çalma listesi indirme
mp3fy "https://open.spotify.com/playlist/37i9dQZF1DXcBWIGoYBM5M"

# Belirli bir klasöre ve 320kbps kalitede indirme
mp3fy "https://open.spotify.com/track/4LfCY65LvojKjWEnU7fNN4" -o "$HOME\Music" -b 320

# Eşzamanlı 3 iş parçacığı ile indirme
mp3fy "https://open.spotify.com/album/4m2880jivSbbyEGAKfITCa" -w 3

# Büyük çalma listelerinde sadece 2. bölümü (101-200) indirme
mp3fy "https://open.spotify.com/playlist/37i9dQZF1DXcBWIGoYBM5M" --batch 2
```

### Parametreler
| Parametre | Açıklama | Varsayılan |
| :--- | :--- | :--- |
| `url` | Spotify Çalma Listesi, Albüm veya Şarkı bağlantısı | `None` (Etkileşimli mod) |
| `-i`, `--interactive` | Etkileşimli modu zorunlu kıl | `False` |
| `-o`, `--output` | İndirilen MP3'lerin kaydedileceği klasör | `Music` Klasörü |
| `-b`, `--bitrate` | MP3 kalitesi (`128`, `192`, `256`, `320`) | `320` |
| `-w`, `--workers` | Eşzamanlı iş parçacığı sayısı (1 - 8) | `2` |
| `--batch` | 100+ şarkılık listelerde sadece belirtilen bölümü indir | `Tümü` |
| `-v`, `--version` | Sürüm bilgisini göster | - |
| `-h`, `--help` | Yardım menüsünü göster | - |

---

## 🛠️ Sistem Gereksinimleri

1. **İşletim Sistemi:** Windows 10/11 (PowerShell 5.1 veya PowerShell 7+) veya Linux
2. **Python 3.9+:**
   - Windows (PowerShell): `winget install Python.Python.3.11`
3. **FFmpeg:** MP3 dönüştürme için gereklidir:
   - Windows (PowerShell):
     ```powershell
     winget install Gyan.FFmpeg
     # veya Scoop ile:
     scoop install ffmpeg
     # veya Chocolatey ile:
     choco install ffmpeg
     ```
   - Linux:
     ```bash
     sudo apt update && sudo apt install ffmpeg
     ```

---

## 📁 Proje Yapısı

```
mp3fy/
├── core/
│   ├── __init__.py
│   ├── spotify.py          # Spotify URL ayrıştırma, metadata ve 100'lük bölümleme
│   ├── downloader.py       # yt-dlp ile ses indirme ve ffmpeg dönüştürme (Windows/Linux uyumlu)
│   ├── tagger.py           # mutagen ile ID3 etiketleme ve kapak görseli gömme
│   └── utils.py            # Dizin tespiti, temizleme ve yardımcı fonksiyonlar
├── tests/
│   ├── test_core.py        # Çekirdek birim ve platform testleri
│   ├── test_cli.py         # CLI argüman ve komut testleri
│   └── test_powershell.py  # PowerShell ve batch başlatıcı testleri
├── main.py                 # CLI ve etkileşimli terminal sihirbazı (UTF-8 konsol destekli)
├── install.ps1             # PowerShell otomatik kurulum scripti (Windows PATH & profil entegrasyonu)
├── run.ps1                 # PowerShell hızlı başlatıcı script
├── mp3fy.ps1               # PowerShell doğrudan çalıştırıcı
├── mp3fy.cmd               # Windows CMD / global PATH çalıştırıcı
├── run.bat                 # Windows çift tıklama / CMD başlatıcı
├── install.sh              # Linux kurulum scripti
├── run.sh                  # Linux başlatıcı script
├── pyproject.toml          # Standart Python paket yapılandırması
├── requirements.txt        # Bağımlılıklar (yt-dlp, mutagen, rich vb.)
├── KULLANIM_KILAVUZU.md    # Detaylı Türkçe kullanım kılavuzu
├── USER_GUIDE.md           # Detailed English user guide
└── README.md               # Proje belgelendirmesi
```

---

## 🧪 Testleri Çalıştırma

PowerShell üzerinden:
```powershell
.\run.ps1 -v
.venv\Scripts\python.exe -m unittest discover tests
```

Linux üzerinden:
```bash
./run.sh -v
.venv/bin/python -m unittest discover tests
```
