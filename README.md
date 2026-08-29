# 🎵 MP3fy - Spotify to MP3 Converter & Downloader

<div align="center">

<img src="web/static/img/logo.jpg" alt="MP3fy Logo" width="120" style="border-radius: 20px; box-shadow: 0 8px 24px rgba(0,0,0,0.4);" />

### MP3fy

![Python Version](https://img.shields.io/badge/python-3.10%2B-blue?style=for-the-badge&logo=python)
![FastAPI](https://img.shields.io/badge/FastAPI-005571?style=for-the-badge&logo=fastapi)
![License](https://img.shields.io/badge/license-MIT-green?style=for-the-badge)
![Platform](https://img.shields.io/badge/platform-Windows%20%7C%20macOS%20%7C%20Linux-lightgrey?style=for-the-badge)

**Spotify Çalma Listesi, Albüm ve Şarkı bağlantılarından yüksek kaliteli MP3 (320kbps) dönüştürücü ve ID3 etiketleyici.**  
*Convert and download Spotify playlists, albums, and tracks to 320kbps MP3 files with full ID3 metadata and album art.*

---

📖 **Kılavuzlar / Guides:**  
🇹🇷 [**Türkçe Kullanım Kılavuzu**](KULLANIM_KILAVUZU.md) | 🇬🇧 [**English User Guide**](USER_GUIDE.md)

---

</div>

## ✨ Temel Özellikler / Key Features

- 🎧 **Spotify'dan Kolay İndirme / Easy Spotify Downloading:** Çalma listesi (Playlist), Albüm (Album) veya Tekil Şarkı (Track) bağlantılarını sıfır yapılandırmayla anında indirin.
- 📦 **100'lük Bölümleme (Batching / Pagination):** 100, 200, 500+ şarkılık devasa listeleri 100'erli bölümlere ayırır; ister tek tek bölümler halinde (`Bölüm 1`, `Bölüm 2`), ister tek tıkla tümünü indirin.
- 📁 **Özel İndirme Klasörü Seçimi / Custom Folder Selection:** Şarkıların nereye kaydedileceğini siz belirlersiniz. İster sistem klasör seçicisiyle (Gözat), ister hızlı konumlarla (`Müzik`, `İndirilenler`, `Masaüstü`), ister özel disk yoluyla.
- 🏷️ **Eksiksiz ID3 Etiketleme / ID3v2.3 Tagging:** Orijinal yüksek çözünürlüklü kapak görseli (APIC), Sanatçı (TPE1), Albüm (TALB), Şarkı Adı (TIT2), Yıl (TDRC) ve Parça No (TRCK).
- 🌓 **Siyah / Beyaz Cam Teması / Dark & Light Theme:** Modern koyu (Dark) ve açık (Light) cam panelli estetik tasarım.
- 🌐 **Türkçe & İngilizce Desteği (TR / EN):** Tek tıkla iki dil arasında anında geçiş.
- 🚀 **Canlı İlerleme / Real-time Progress:** WebSocket ile indirme yüzdesi, hız (MB/s), kalan süre ve dönüştürme durumları canlı izlenir.
- 🔊 **Entegre Ses Önizleme / Audio Preview:** Şarkıları indirmeden önce veya indirdikten sonra arayüz üzerinden dinleyin.
- ⚙️ **Özelleştirilebilir Kalite (Bitrate):** 320 kbps (Stüdyo Kalitesi), 256 kbps, 192 kbps veya 128 kbps seçenekleri.
- 💻 **Hem Web Arayüzü Hem CLI:** İster modern tarayıcı arayüzüyle, ister terminalden tek komutla kullanın.

---

## 🚀 Hızlı Başlangıç / Quick Start

### 1. Depoyu Klonlayın / Clone Repository
```bash
git clone https://github.com/kullaniciadi/mp3fy.git
cd mp3fy
```

### 2. Tek Tıkla Başlatma / Launch

#### Linux / macOS:
```bash
chmod +x run.sh
./run.sh
```

#### Windows:
`run.bat` dosyasına çift tıklayın veya komut satırından çalıştırın:
```cmd
run.bat
```

> Başlatıcı script sanal ortamı (`.venv`) kurar, bağımlılıkları yükler ve tarayıcınızda `http://localhost:8888` adresinde uygulamayı açar.

---

## 🛠️ Sistem Gereksinimleri / Prerequisites

1. **Python 3.10+**
2. **FFmpeg:** MP3 dönüştürme ve ses işleme için gereklidir:
   - **Ubuntu / Debian:** `sudo apt update && sudo apt install ffmpeg`
   - **Arch Linux:** `sudo pacman -S ffmpeg`
   - **macOS:** `brew install ffmpeg`
   - **Windows:** `winget install Gyan.FFmpeg` veya [gyan.dev](https://www.gyan.dev/ffmpeg/builds/) adresinden indirin.

---

## 💻 CLI (Komut Satırı) Kullanımı / CLI Usage

```bash
# Çalma listesi indirme / Download playlist
python main.py "https://open.spotify.com/playlist/37i9dQZF1DXcBWIGoYBM5M"

# Belirli bir klasöre ve 320kbps kalitede indirme
python main.py "https://open.spotify.com/track/4LfCY65LvojKjWEnU7fNN4" --output ~/Music --bitrate 320

# Eşzamanlı 3 iş parçacığı ile indirme
python main.py "https://open.spotify.com/album/4m2880jivSbbyEGAKfITCa" --workers 3
```

---

## 📁 Proje Yapısı / Project Structure

```
mp3fy/
├── core/
│   ├── __init__.py
│   ├── spotify.py          # Spotify URL ayrıştırma, metadata ve 100'lük bölümleme
│   ├── downloader.py       # yt-dlp ile ses indirme ve ffmpeg dönüştürme
│   ├── tagger.py           # mutagen ile ID3 etiketleme ve kapak görseli gömme
│   └── utils.py            # Klasör seçici, ev dizini tespiti ve dosya adı temizleme
├── web/
│   ├── static/
│   │   ├── css/            # Özel stiller
│   │   ├── js/
│   │   │   └── app.js      # Çok dilli (TR/EN) frontend controller, WebSocket & oynatıcı
│   │   └── img/
│   │       ├── logo.jpg    # Uygulama logosu
│   │       └── placeholder.svg
│   └── templates/
│       └── index.html      # Glassmorphic arayüz, tema/dil düğmeleri, bölüm sekmeleri
├── tests/
│   └── test_core.py        # Birim testleri
├── app.py                  # FastAPI/Uvicorn ana uygulama ve WebSocket sunucusu
├── main.py                 # CLI ve başlatıcı giriş noktası
├── requirements.txt        # Python paket bağımlılıkları
├── run.sh                  # Linux/macOS başlatıcı betik
├── run.bat                 # Windows başlatıcı betik
├── KULLANIM_KILAVUZU.md    # Detaylı Türkçe kullanım kılavuzu
├── USER_GUIDE.md           # Detailed English user guide
├── LICENSE                 # MIT Lisansı
└── README.md               # Proje belgelendirmesi
```

---

## 🧪 Testleri Çalıştırma / Running Tests

```bash
source .venv/bin/activate
python -m unittest discover tests
```

---

## 📄 Lisans / License

Bu proje [MIT Lisansı](LICENSE) altında lisanslanmıştır.
