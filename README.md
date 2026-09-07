# 🎵 MP3fy - Spotify to MP3 Linux CLI Tool

<div align="center">

### MP3fy (Linux CLI Edition)

![Python Version](https://img.shields.io/badge/python-3.9%2B-blue?style=for-the-badge&logo=python)
![Platform](https://img.shields.io/badge/platform-Linux-green?style=for-the-badge&logo=linux)
![CLI](https://img.shields.io/badge/interface-Terminal%20CLI-black?style=for-the-badge)

**Spotify Çalma Listesi, Albüm ve Şarkı bağlantılarından yüksek kaliteli MP3 (320kbps) dönüştürücü ve ID3 etiketleyici Linux Terminal Aracı.**  
*Convert and download Spotify playlists, albums, and tracks to 320kbps MP3 files with full ID3 metadata and album art directly from your Linux terminal.*

---

📖 **Kılavuzlar / Guides:**  
🇹🇷 [**Türkçe Kullanım Kılavuzu**](KULLANIM_KILAVUZU.md) | 🇬🇧 [**English User Guide**](USER_GUIDE.md)

---

</div>

## ✨ Temel Özellikler / Key Features

- 🎧 **Doğrudan Terminal Komutu (`mp3fy`):** Kurulumdan sonra sistemdeki herhangi bir dizinde doğrudan `mp3fy` yazarak çalıştırabilirsiniz.
- 🧙‍♂️ **Etkileşimli Terminal Sihirbazı:** Argüman girmeden `mp3fy` yazıldığında renkli ve kullanımı kolay bir arayüzle Spotify bağlantısı, kalite, bölüm ve kayıt yeri sorar.
- ⚡ **Parametreli Hızlı Kullanım:** `mp3fy <url> [seçenekler]` formatında tek satırda otomatik indirme.
- 📦 **100'lük Bölümleme (Batching):** 100, 200, 500+ şarkılık büyük listeleri 100'erlik dilimlere ayırır; ister belirli bir bölümü, ister tümünü indirin.
- 🏷️ **Eksiksiz ID3 Etiketleme / ID3v2.3 Tagging:** Orijinal yüksek çözünürlüklü kapak görseli (APIC), Sanatçı (TPE1), Albüm (TALB), Şarkı Adı (TIT2), Yıl (TDRC) ve Parça No (TRCK).
- 🚀 **Canlı İlerleme Çubuğu:** Rich kütüphanesi destekli canlı indirme hızı (MB/s), kalan süre ve şarkı durum bildirimleri.
- 📁 **Özel İndirme Klasörü:** Varsayılan olarak `~/Music` dizinine kaydeder veya `-o` ile dilediğiniz hedef klasörü belirleyebilirsiniz.
- ⚙️ **Özelleştirilebilir Kalite (Bitrate):** 320 kbps (Stüdyo Kalitesi), 256 kbps, 192 kbps veya 128 kbps seçenekleri.

---

## 🚀 Hızlı Başlangıç & Kurulum / Quick Start

### 1. Depoyu Klonlayın
```bash
git clone https://github.com/kullaniciadi/mp3fy.git
cd mp3fy
```

### 2. Tek Komutla Kurun (Installer)
```bash
chmod +x install.sh
./install.sh
```
> Bu script sanal ortamı kurar, bağımlılıkları yükler ve `~/.local/bin/mp3fy` komutunu sisteme bağlar.

### 3. Çalıştırın
Terminalde herhangi bir konumdayken:
```bash
mp3fy
```

---

## 💻 Kullanım / Usage

### 1. Etkileşimli Mod (Sihirbaz)
Hiçbir parametre vermeden çalıştırıldığında etkileşimli mod açılır:
```bash
mp3fy
```
Sizden Spotify linkini alır, çalma listesi/şarkı detaylarını listeler ve onayınızı alarak indirmeyi başlatır.

### 2. Komut Satırı Parametreleri (Direct CLI)
```bash
# Çalma listesi indirme
mp3fy "https://open.spotify.com/playlist/37i9dQZF1DXcBWIGoYBM5M"

# Belirli bir klasöre ve 320kbps kalitede indirme
mp3fy "https://open.spotify.com/track/4LfCY65LvojKjWEnU7fNN4" -o ~/Music -b 320

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
| `-o`, `--output` | İndirilen MP3'lerin kaydedileceği klasör | `~/Music` |
| `-b`, `--bitrate` | MP3 kalitesi (`128`, `192`, `256`, `320`) | `320` |
| `-w`, `--workers` | Eşzamanlı iş parçacığı sayısı (1 - 8) | `2` |
| `--batch` | 100+ şarkılık listelerde sadece belirtilen bölümü indir | `Tümü` |
| `-v`, `--version` | Sürüm bilgisini göster | - |
| `-h`, `--help` | Yardım menüsünü göster | - |

---

## 🛠️ Sistem Gereksinimleri

1. **Linux İşletim Sistemi** (Ubuntu, Debian, Linux Mint, Arch, Fedora vb.)
2. **Python 3.9+**
3. **FFmpeg:** MP3 dönüştürme için gereklidir:
   ```bash
   sudo apt update && sudo apt install ffmpeg
   ```
   *(Sisteminizde FFmpeg yoksa MP3fy yerel ikili dosyayı da otomatik olarak kullanabilir).*

---

## 📁 Proje Yapısı

```
mp3fy/
├── core/
│   ├── __init__.py
│   ├── spotify.py          # Spotify URL ayrıştırma, metadata ve 100'lük bölümleme
│   ├── downloader.py       # yt-dlp ile ses indirme ve ffmpeg dönüştürme
│   ├── tagger.py           # mutagen ile ID3 etiketleme ve kapak görseli gömme
│   └── utils.py            # Dizin tespiti, temizleme ve yardımcı fonksiyonlar
├── tests/
│   ├── test_core.py        # Çekirdek birim testleri
│   └── test_cli.py         # CLI argüman ve komut testleri
├── main.py                 # CLI ve etkileşimli terminal sihirbazı
├── install.sh              # Otomatik Linux kurulum scripti (mp3fy komutunu oluşturur)
├── run.sh                  # Hızlı başlatıcı script
├── pyproject.toml          # Standart Python paket yapılandırması
├── requirements.txt        # Bağımlılıklar (yt-dlp, mutagen, rich vb.)
├── KULLANIM_KILAVUZU.md    # Detaylı Türkçe kullanım kılavuzu
├── USER_GUIDE.md           # Detailed English user guide
└── README.md               # Proje belgelendirmesi
```

---

## 🧪 Testleri Çalıştırma

```bash
./run.sh -v
.venv/bin/python -m unittest discover tests
```
