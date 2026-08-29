# 🎵 MP3fy - Kullanım Kılavuzu (Türkçe)

**MP3fy**, Spotify çalma listelerini, albümlerini ve tekil parçalarını yüksek kaliteli (320 kbps) MP3 formatına dönüştürüp, orijinal albüm kapağı ve ID3 etiketleriyle birlikte dilediğiniz klasöre kaydeden modern, hızlı ve açık kaynaklı bir müzik indirme aracıdır.

---

## 📑 İçindekiler
1. [Öne Çıkan Özellikler](#-öne-çıkan-özellikler)
2. [Gereksinimler & Kurulum](#-gereksinimler--kurulum)
3. [Uygulamayı Başlatma](#-uygulamayı-başlatma)
4. [Kullanım Adımları](#-kullanım-adımları)
   - [1. Spotify Bağlantısı Getirme](#1-spotify-bağlantısı-getirme)
   - [2. 100'lük Bölümlere (Batches) Ayırma](#2-100lük-bölümlere-batches-ayırma)
   - [3. İndirme Klasörünü Seçme](#3-indirme-klasörünü-seçme)
   - [4. İndirme & Dönüştürme](#4-indirme--dönüştürme)
   - [5. Siyah / Beyaz Tema ve Dil Değiştirme](#5-siyah--beyaz-tema-ve-dil-değiştirme)
5. [Ayarlar & Ses Kalitesi](#-ayarlar--ses-kalitesi)
6. [Sıkça Sorulan Sorular & Sorun Giderme](#-sıkça-sorulan-sorular--sorun-giderme)

---

## 🌟 Öne Çıkan Özellikler

- **🔒 Spotify API Anahtarı Zorunluluğu Yok:** Sıfır yapılandırma ile tüm Spotify linklerini doğrudan çözer.
- **📦 100'lük Bölümleme (Batching):** 100, 200, 500+ şarkılık devasa listeleri 100'erli bölümlere ayırır; ister tek tek bölümler halinde ister tek tıkla tümünü indirmenizi sağlar.
- **📁 Esnek İndirme Klasörü:** Şarkıların nereye kaydedileceğini siz belirlersiniz. İster sistem klasör seçicisiyle (Gözat), ister hızlı konumlarla (`Müzik`, `İndirilenler`, `Masaüstü`), ister özel disk yoluyla.
- **🏷️ Kusursuz ID3v2.3 Etiketleme:** Albüm kapağı (APIC), Sanatçı (TPE1), Albüm (TALB), Şarkı Adı (TIT2), Yıl (TDRC) ve Parça No (TRCK) otomatik olarak MP3 içine yazılır.
- **🎧 Stüdyo Kalitesi Ses:** `yt-dlp` ve `ffmpeg` ile 320 kbps saf MP3 dönüştürme.
- **🌓 Siyah / Beyaz Cam Teması:** Modern koyu (Dark) ve açık (Light) cam panelli estetik tasarım.
- **🌐 Türkçe & İngilizce (TR / EN):** Tek tıkla anında dil değiştirme desteği.

---

## 🛠️ Gereksinimler & Kurulum

### Sistem Gereksinimleri
- **İşletim Sistemi:** Linux (Ubuntu/Debian/Fedora/Arch), Windows 10/11, macOS
- **Python:** Python 3.10 veya üzeri
- **FFmpeg:** Ses işleme ve MP3 dönüştürme için gereklidir.

### FFmpeg Kurulumu:
- **Ubuntu / Debian / Linux Mint:**
  ```bash
  sudo apt update && sudo apt install ffmpeg -y
  ```
- **Arch Linux:**
  ```bash
  sudo pacman -S ffmpeg
  ```
- **macOS (Homebrew):**
  ```bash
  brew install ffmpeg
  ```
- **Windows:**
  [FFmpeg Resmi Sitesi](https://ffmpeg.org/download.html) üzerinden indirip `PATH` ortam değişkenine ekleyin veya `winget install Gyan.FFmpeg` komutunu kullanın.

---

## 🚀 Uygulamayı Başlatma

### Linux / macOS:
Proje dizininde yer alan başlatıcı scriptini çalıştırın:
```bash
cd mp3fy
chmod +x run.sh
./run.sh
```

### Windows:
Proje klasöründeki `run.bat` dosyasına çift tıklayın veya komut satırından çalıştırın:
```cmd
cd mp3fy
run.bat
```

> **Not:** Script; Python sanal ortamını (`.venv`) otomatik oluşturur, bağımlılıkları yükler ve tarayıcınızda `http://localhost:8888` adresini açar.

---

## 📖 Kullanım Adımları

### 1. Spotify Bağlantısı Getirme
1. Spotify uygulamasından veya web oynatıcısından herhangi bir **Çalma Listesi (Playlist)**, **Albüm** veya **Şarkı** linkini kopyalayın.
2. MP3fy arama kutusuna yapıştırın (veya **"Yapıştır"** butonuna basın).
3. **"Listeyi Getir"** butonuna tıklayın. Şarkı listesi saniyeler içinde ekrana gelecektir.

### 2. 100'lük Bölümlere (Batches) Ayırma
- Spotify listelerinde 100'den fazla şarkı olduğunda (örneğin 150 veya 500 şarkı), MP3fy listeyi otomatik olarak 100'lük dilimlere ayırır:
  - `[✨ Tümü (150)]`
  - `[📦 Bölüm 1 (1 - 100)]`
  - `[📦 Bölüm 2 (101 - 150)]`
- Dilediğiniz bölüme tıklayarak sadece o bölümdeki şarkıları görüntüleyebilir ve **"Bu Bölümü İndir"** butonu ile parça parça indirebilirsiniz.

### 3. İndirme Klasörünü Seçme
- Üst menüde yer alan **"📁 Klasör: [Konum]"** butonuna tıklayarak klasör seçim modalını açabilirsiniz:
  - **Bilgisayardan Klasör Seç (Gözat...):** Sistem dosya yöneticisi penceresini açar.
  - **Hızlı Konumlar:** `Müzik (~/Music)`, `İndirilenler (~/Downloads)`, `Masaüstü (~/Desktop)`, `Belgeler (~/Documents)`.
  - **Özel Dizin Yolu:** İstediğiniz herhangi bir klasör veya harici disk yolunu yazıp **"Uygula"** butonuna basabilirsiniz.

### 4. İndirme & Dönüştürme
- **Tümünü İndir:** Seçili olan tüm şarkıları kuyruğa alır ve indirmeye başlar.
- **Tekil İndirme:** Her şarkı satırının sağındaki **"İndir"** butonuna basarak tek tek indirebilirsiniz.
- **Canlı İlerleme:** İndirme yüzdesi, indirme hızı (MB/s) ve dönüştürme durumunu tablodan anlık takip edebilirsiniz.
- **Önizleme / Dinleme:** Şarkı satırındaki **"Oynat"** ikonu ile şarkıyı indirmeden önce önizleyebilir veya indirdikten sonra doğrudan tarayıcı üzerinden dinleyebilirsiniz.

### 5. Siyah / Beyaz Tema ve Dil Değiştirme
- **Tema:** Üst menüdeki `[🌙 Karanlık / ☀️ Aydınlık]` butonu ile temayı değiştirebilirsiniz.
- **Dil:** Üst menüdeki `[🌐 TR / EN]` butonu ile uygulamayı anında Türkçe veya İngilizce yapabilirsiniz.

---

## ⚙️ Ayarlar & Ses Kalitesi

Sağ üstteki **⚙️ Ayarlar** butonuna basarak:
- **MP3 Ses Kalitesi:** 320 kbps (Stüdyo - Önerilen), 256 kbps, 192 kbps veya 128 kbps seçeneklerinden birini belirleyebilirsiniz.
- **Özel Spotify API:** İsteğe bağlı olarak kendi Spotify Developer Client ID / Secret bilgilerinizi girebilirsiniz (zorunlu değildir).

---

## ❓ Sıkça Sorulan Sorular & Sorun Giderme

**S: Şarkılar nereye kaydediliyor?**  
**C:** Seçtiğiniz indirme klasörüne kaydedilir (varsayılan: `~/Music`). Üst menüdeki klasör butonuna basarak istediğiniz klasörü seçebilir veya klasör ikonuna basarak indirilen yeri açabilirsiniz.

**S: Şarkı etiketleri ve kapak resimleri MP3 dosyasına işleniyor mu?**  
**C:** Evet. Tüm şarkılar Spotify'dan alınan orijinal yüksek çözünürlüklü kapak görseli, sanatçı, albüm, şarkı adı ve yıl etiketleriyle (ID3v2.3) eksiksiz kaydedilir. Otomobil teyplerinde, telefonlarda ve tüm müzik çalarlarda sorunsuz görünür.

**S: "FFmpeg bulunamadı" hatası alıyorum, ne yapmalıyım?**  
**C:** Sisteminizde FFmpeg kurulu olduğundan emin olun (`ffmpeg -version` komutunu çalıştırarak kontrol edebilirsiniz). Kurulum adımları yukarıdaki Kurulum bölümünde açıklanmıştır.
