# 🎵 MP3fy - Linux Terminal Kullanım Kılavuzu (Türkçe)

**MP3fy**, Spotify çalma listelerini, albümlerini ve parçalarını Linux terminali üzerinden yüksek kaliteli (320 kbps) MP3 formatına dönüştürüp, orijinal kapak görseli ve ID3 etiketleriyle kaydeden bağımsız bir komut satırı aracıdır.

---

## 📑 İçindekiler
1. [Öne Çıkan Özellikler](#-öne-çıkan-özellikler)
2. [Gereksinimler & Kurulum](#-gereksinimler--kurulum)
3. [Komut Olarak Kullanım (`mp3fy`)](#-komut-olarak-kullanım-mp3fy)
4. [Kullanım Senaryoları](#-kullanım-senaryoları)
   - [1. Etkileşimli Terminal Sihirbazı](#1-etkileşimli-terminal-sihirbazı)
   - [2. Doğrudan Tek Komutla İndirme](#2-doğrudan-tek-komutla-indirme)
   - [3. 100'lük Bölümleme (Batching)](#3-100lük-bölümleme-batching)
   - [4. Kalite ve Eşzamanlı İş Parçacığı Ayarı](#4-kalite-ve-eşzamanlı-iş-parçacığı-ayarı)
5. [Tüm Parametreler (CLI Flags)](#-tüm-parametreler-cli-flags)
6. [Sorun Giderme & SSS](#-sorun-giderme--sss)

---

## 🌟 Öne Çıkan Özellikler

- **⚡ Sistem Geneli Komut:** Kurulumdan sonra terminalinize sadece `mp3fy` yazarak doğrudan çalıştırabilirsiniz.
- **🔒 Sıfır Yapılandırma:** Spotify API anahtarı gerekmez; herkese açık çalma listeleri, albümler ve şarkılar doğrudan çözülür.
- **📦 100'lük Bölümleme (Batching):** 100, 200, 500+ şarkılık devasa listeleri 100'er parçalık gruplara böler; ister belirli bir bölümü (`--batch 1`), ister tümünü indirin.
- **📁 Akıllı Klasör Yönetimi:** Varsayılan olarak Linux standart `~/Music` klasörüne yazar. `-o` seçeneğiyle herhangi bir hedef dizin belirtebilirsiniz.
- **🏷️ Eksiksiz ID3v2.3 Etiketleri:** Kapak resmi (APIC), Sanatçı, Albüm, Şarkı Adı, Yıl ve Parça Numarası dosyaya gömülür.
- **📊 Canlı Terminal İlerlemesi:** Rich kütüphanesiyle canlı yüzdeler, indirme hızı (MB/s) ve kalan süre takibi.
- **🛡️ Temiz Kesinti:** `Ctrl+C` ile durdurulduğunda geçici dosyalar temizlenir ve sistem güvenle kapatılır.

---

## 🛠️ Gereksinimler & Kurulum

### Sistem Gereksinimleri
- **İşletim Sistemi:** Linux (Ubuntu, Debian, Linux Mint, Fedora, Arch Linux vb.)
- **Python:** Python 3.9 veya üzeri
- **FFmpeg:** MP3 dönüştürme için gereklidir.

### Kurulum Adımları
```bash
git clone https://github.com/kullaniciadi/mp3fy.git
cd mp3fy
chmod +x install.sh
./install.sh
```

Kurulum tamamlandığında `~/.local/bin/mp3fy` komutu oluşturulur ve anında kullanılabilir hale gelir.

---

## 🚀 Komut Olarak Kullanım (`mp3fy`)

Terminalde herhangi bir dizindeyken:
```bash
mp3fy
```

### 1. Etkileşimli Terminal Sihirbazı
Hiçbir parametre vermeden `mp3fy` yazdığınızda etkileşimli mod açılır:
1. **Spotify URL:** Şarkı, albüm veya çalma listesi linkini yapıştırın (çıkmak için `q`).
2. **Bölüm Seçimi:** Liste 100 şarkıdan büyükse hangi bölümü indirmek istediğinizi sorar (Tümünü indirmek için `T`).
3. **Hedef Klasör:** Varsayılan `~/Music` gelir, Enter ile onaylayabilir veya başka bir klasör yolu yazabilirsiniz.
4. **Ses Kalitesi:** 320, 256, 192 veya 128 kbps seçebilirsiniz (Varsayılan: 320).
5. **Eşzamanlı İşlem:** Aynı anda indirilecek parça sayısı (Varsayılan: 2).

### 2. Doğrudan Tek Komutla İndirme
Parametreleri tek satırda belirterek indirme yapabilirsiniz:
```bash
# Şarkı indirme
mp3fy "https://open.spotify.com/track/4LfCY65LvojKjWEnU7fNN4"

# Çalma listesini ~/Müzik klasörüne 320kbps olarak 3 iş parçacığıyla indirme
mp3fy "https://open.spotify.com/playlist/37i9dQZF1DXcBWIGoYBM5M" -o ~/Müzik -b 320 -w 3

# Albüm indirme
mp3fy "https://open.spotify.com/album/4m2880jivSbbyEGAKfITCa"
```

### 3. 100'lük Bölümleme (Batching)
Örneğin 250 şarkılık bir listede:
- 1. Bölüm: 1 - 100
- 2. Bölüm: 101 - 200
- 3. Bölüm: 201 - 250

Sadece 2. bölümü indirmek için:
```bash
mp3fy "https://open.spotify.com/playlist/37i9dQZF1DXcBWIGoYBM5M" --batch 2
```

---

## ⚙️ Tüm Parametreler (CLI Flags)

| Bayrak | Açıklama |
| :--- | :--- |
| `url` | İndirilecek Spotify URL'si (belirtilmezse etkileşimli mod başlar) |
| `-i`, `--interactive` | Etkileşimli sihirbazı zorunlu çalıştırır |
| `-o`, `--output` | İndirilen dosyaların yazılacağı hedef dizin (Varsayılan: `~/Music`) |
| `-b`, `--bitrate` | MP3 ses kalitesi (`128`, `192`, `256`, `320`) |
| `-w`, `--workers` | Eşzamanlı iş parçacığı sayısı (Varsayılan: `2`) |
| `--batch` | 100+ şarkılık listelerde belirli bölümü indirme (örn: `1`, `2`) |
| `-v`, `--version` | MP3fy sürüm numarasını gösterir |
| `-h`, `--help` | Yardım ve komut listesini gösterir |

---

## ❓ Sorun Giderme & SSS

**1. `mp3fy: komut bulunamadı` hatası alıyorum:**  
Terminalinizin `PATH` değişkenine `~/.local/bin` dizini ekli olmalıdır. Çoğu modern Linux dağıtımında bu varsayılandır. Manuel eklemek için:
```bash
echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc
source ~/.bashrc
```

**2. `ffmpeg` hatası alıyorum:**  
Sisteminizde FFmpeg eksikse terminalde şu komutla yükleyin:
```bash
sudo apt update && sudo apt install ffmpeg
```

**3. İndirilen şarkılar nerede?**  
Varsayılan konum ev dizininizdeki `~/Music` (veya Türkçe sistemlerde `~/Müzik`) klasörüdür.
