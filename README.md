# 🎵 MP3fy - Spotify MP3 İndirici & Dönüştürücü

<div align="center">

![Python Version](https://img.shields.io/badge/python-3.10%2B-blue?style=for-the-badge&logo=python)
![FastAPI](https://img.shields.io/badge/FastAPI-005571?style=for-the-badge&logo=fastapi)
![License](https://img.shields.io/badge/license-MIT-green?style=for-the-badge)
![Platform](https://img.shields.io/badge/platform-Windows%20%7C%20macOS%20%7C%20Linux-lightgrey?style=for-the-badge)

**Spotify Çalma Listesi, Albüm ve Şarkı bağlantılarından yüksek kaliteli MP3 (320kbps) dönüştürücü ve ID3 etiketleyici.**

[Özellikler](#-özellikler) • [Ekran Görüntüleri & Temalar](#-temalar-siyah--beyaz) • [Kurulum](#-kurulum) • [Kullanım](#-kullanım) • [CLI Modu](#-cli-komut-satırı-kullanımı) • [Gereksinimler](#-sistem-gereksinimleri)

</div>

---

## ✨ Özellikler

- 🎧 **Spotify'dan Kolay İndirme:** Çalma listesi (Playlist), Albüm (Album) veya Tekil Şarkı (Track) bağlantılarını doğrudan yapıştırarak anında indirin.
- 📂 **Otomatik `music/` Klasörü Yönetimi:** İndirilen tüm MP3'ler doğrudan projedeki `music/` klasörüne (veya ayarlardan seçtiğiniz özel dizine) düzenli bir şekilde kaydedilir. Arayüzdeki *"Music Klasörünü Aç"* butonuyla tek tıkla klasöre erişebilirsiniz.
- 🏷️ **Eksiksiz ID3 Etiketleme (Metadata):**
  - 🖼️ **Yüksek Çözünürlüklü Albüm Kapağı (APIC Cover Art):** Spotify'daki orijinal kapak görseli MP3 dosyasına doğrudan gömülür.
  - 🎤 **Sanatçı (Artist / Performer):** `TPE1`
  - 💿 **Albüm Adı:** `TALB`
  - 🎵 **Şarkı Adı (Title):** `TIT2`
  - 📅 **Çıkış Yılı:** `TDRC` / `TYER`
  - 🔢 **Parça Numarası:** `TRCK` (Örn: 1/12)
- 🌓 **Siyah / Beyaz Tema Düğmesi (Dark / Light Theme):** Modern, göz yormayan Koyu (Siyah) tema ve pırıl pırıl Açık (Beyaz) tema arasında tek tıkla geçiş yapın. Tema seçiminiz tarayıcıda otomatik olarak hatırlanır.
- 🚀 **Gerçek Zamanlı WebSocket İlerlemesi:** İndirme yüzdesi, hız (MB/s), kalan süre ve dönüştürme durumları anlık olarak güncellenir.
- 🔊 **Entegre Ses Önizleme:** Şarkıları indirmeden önce veya indirdikten sonra arayüz üzerinden dinleyin.
- ⚙️ **Özelleştirilebilir Kalite (Bitrate):** 320 kbps (Stüdyo Kalitesi), 256 kbps, 192 kbps veya 128 kbps seçenekleri.
- 🔑 **Sıfır Yapılandırma Zorunluluğu:** Spotify API anahtarı olmadan hemen çalışır (Gelişmiş kullanıcılar için özel API anahtarı desteği de mevcuttur).
- 💻 **Hem Web Arayüzü Hem CLI:** İster modern tarayıcı arayüzüyle, ister terminalden tek komutla kullanın.

---

## 🎨 Temalar (Siyah & Beyaz)

| 🌙 Koyu (Siyah) Tema | ☀️ Açık (Beyaz) Tema |
| :---: | :---: |
| Modern Spotify yeşili detaylara ve cam efektlerine (glassmorphism) sahip gece modu | Temiz, yüksek kontrastlı ve sade gündüz modu |

---

## 🚀 Kurulum

### 1. Depoyu Klonlayın
```bash
git clone https://github.com/kullaniciadi/mp3fy.git
cd mp3fy
```

### 2. Tek Tıkla Başlatma (Önerilen)

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

---

### 3. Manuel Kurulum

Python sanal ortamı oluşturup bağımlılıkları yükleyin:

```bash
# Sanal ortam oluşturma
python3 -m venv .venv

# Sanal ortamı aktifleştirme (Linux/macOS)
source .venv/bin/activate

# Sanal ortamı aktifleştirme (Windows CMD / PowerShell)
# .venv\Scripts\activate.bat   veya   .venv\Scripts\Activate.ps1

# Bağımlılıkları yükleme
pip install -r requirements.txt

# Uygulamayı başlatma
python main.py
```

Uygulama otomatik olarak varsayılan tarayıcınızda `http://127.0.0.1:8888` adresinde açılacaktır.

---

## 💻 CLI (Komut Satırı) Kullanımı

Web arayüzünü açmadan doğrudan terminalden de çalma listesi indirebilirsiniz:

```bash
# Çalma listesi indirme
python main.py "https://open.spotify.com/playlist/37i9dQZF1DXcBWIGoYBM5M"

# Belirli bir klasöre ve 320kbps kalitede indirme
python main.py "https://open.spotify.com/track/4LfCY65LvojKjWEnU7fNN4" --output music/ --bitrate 320

# Eşzamanlı 3 iş parçacığı ile indirme
python main.py "https://open.spotify.com/album/4m2880jivSbbyEGAKfITCa" --workers 3
```

### CLI Seçenekleri:
- `--web`: Web arayüzünü zorla başlatır.
- `--port 8888`: Web sunucu portu.
- `-o, --output music/`: İndirilen MP3'lerin kaydedileceği hedef klasör.
- `-b, --bitrate 320`: Ses kalitesi (`320`, `256`, `192`, `128`).
- `-w, --workers 2`: Eşzamanlı indirme iş parçacığı sayısı.

---

## 🛠️ Sistem Gereksinimleri

1. **Python 3.10 veya daha yenisi**
2. **FFmpeg:** MP3 dönüştürme ve ses işleme için sisteminizde `ffmpeg` kurulu olmalıdır:
   - **Ubuntu / Debian:** `sudo apt update && sudo apt install ffmpeg`
   - **Arch Linux:** `sudo pacman -S ffmpeg`
   - **macOS:** `brew install ffmpeg`
   - **Windows:** `winget install Gyan.FFmpeg` veya [gyan.dev](https://www.gyan.dev/ffmpeg/builds/) adresinden indirip PATH ortam değişkenine ekleyin.

---

## 📁 Proje Dizin Yapısı

```
mp3fy/
├── core/
│   ├── __init__.py
│   ├── spotify.py          # Spotify URL ayrıştırma ve metadata çekici
│   ├── downloader.py       # yt-dlp ile ses indirme ve ffmpeg dönüştürme
│   ├── tagger.py           # mutagen ile ID3 etiketleme ve kapak görseli gömme
│   └── utils.py            # Dosya adı temizleme, klasör yönetimi, sistem araçları
├── web/
│   ├── static/
│   │   ├── css/
│   │   │   └── style.css   # Dark/Light tema stilleri, responsive UI
│   │   ├── js/
│   │   │   └── app.js      # WebSocket bağlantısı, tema geçişi, canlı indirme paneli
│   │   └── img/
│   │       └── placeholder.svg
│   └── templates/
│       └── index.html      # Ana sayfa, tema düğmesi, indirme tablosu
├── music/                  # İndirilen MP3 dosyalarının kaydedildiği klasör (.gitkeep)
├── tests/
│   └── test_core.py        # Birim testleri
├── app.py                  # FastAPI/Uvicorn ana uygulama ve WebSocket sunucusu
├── main.py                 # CLI ve uygulama başlatıcı giriş noktası
├── requirements.txt        # Python paket bağımlılıkları
├── .gitignore              # Git yoksayma dosyası
├── run.sh                  # Linux/macOS başlatıcı betik
├── run.bat                 # Windows başlatıcı betik
├── LICENSE                 # MIT Lisansı
└── README.md               # Proje belgelendirmesi
```

---

## 🧪 Testleri Çalıştırma

```bash
python -m unittest discover tests
```

---

## 📄 Lisans

Bu proje [MIT Lisansı](LICENSE) altında lisanslanmıştır.
