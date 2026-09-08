# 🎵 MP3fy - PowerShell & Terminal Kullanım Kılavuzu (Türkçe)

**MP3fy**, Spotify çalma listelerini, albümlerini ve parçalarını PowerShell ve Linux terminali üzerinden yüksek kaliteli (320 kbps) MP3 formatına dönüştürüp, orijinal kapak görseli ve ID3 etiketleriyle kaydeden bağımsız bir komut satırı aracıdır.

---

## 📑 İçindekiler
1. [Öne Çıkan Özellikler](#-öne-çıkan-özellikler)
2. [Gereksinimler & Kurulum](#-gereksinimler--kurulum)
   - [Windows / PowerShell Kurulumu](#windows--powershell-kurulumu)
   - [Linux Kurulumu](#linux-kurulumu)
3. [Komut Olarak Kullanım (`mp3fy`)](#-komut-olarak-kullanım-mp3fy)
4. [Kullanım Senaryoları](#-kullanım-senaryoları)
   - [1. Etkileşimli Terminal Sihirbazı](#1-etkileşimli-terminal-sihirbazı)
   - [2. Doğrudan Tek Komutla İndirme](#2-doğrudan-tek-komutla-indirme)
   - [3. 100'lük Bölümleme (Batching)](#3-100lük-bölümleme-batching)
   - [4. Kalite ve Eşzamanlı İş Parçacığı Ayarı](#4-kalite-ve-eşzamanlı-iş-parçacığı-ayarı)
5. [Tüm Parametreler (CLI Flags)](#-tüm-parametreler-cli-flags)
6. [PowerShell & Windows İpuçları](#-powershell--windows-i̇puçları)
7. [Sorun Giderme & SSS](#-sorun-giderme--sss)

---

## 🌟 Öne Çıkan Özellikler

- **⚡ Sistem Geneli Komut (`mp3fy`):** Kurulumdan sonra terminalinize veya PowerShell pencerenize sadece `mp3fy` yazarak doğrudan çalıştırabilirsiniz.
- **🪟 Tam PowerShell & Windows Desteği:** Windows PowerShell 5.1 ve PowerShell Core 7+ üzerinde otomatik PATH ve `$PROFILE` entegrasyonu, UTF-8 konsol desteği.
- **🔒 Sıfır Yapılandırma:** Spotify API anahtarı gerekmez; herkese açık çalma listeleri, albümler ve şarkılar doğrudan çözülür.
- **📦 100'lük Bölümleme (Batching):** 100, 200, 500+ şarkılık devasa listeleri 100'er parçalık gruplara böler; ister belirli bir bölümü (`--batch 1`), ister tümünü indirin.
- **📁 Akıllı Klasör Yönetimi:** Varsayılan olarak standart Müzik klasörünüze (`Music` / `Müzik`) yazar. `-o` seçeneğiyle herhangi bir hedef dizin belirtebilirsiniz.
- **🏷️ Eksiksiz ID3v2.3 Etiketleri:** Kapak resmi (APIC), Sanatçı, Albüm, Şarkı Adı, Yıl ve Parça Numarası dosyaya gömülür.
- **📊 Canlı Terminal İlerlemesi:** Rich kütüphanesiyle canlı yüzdeler, indirme hızı (MB/s) ve kalan süre takibi.
- **🛡️ Temiz Kesinti:** `Ctrl+C` ile durdurulduğunda geçici dosyalar temizlenir ve sistem güvenle kapatılır.

---

## 🛠️ Gereksinimler & Kurulum

### Sistem Gereksinimleri
- **İşletim Sistemi:** Windows 10/11 (PowerShell) veya Linux (Ubuntu, Debian, Mint, Fedora, Arch vb.)
- **Python:** Python 3.9 veya üzeri
- **FFmpeg:** MP3 dönüştürme için gereklidir.

---

### Windows / PowerShell Kurulumu

1. **PowerShell'i açın ve depoyu klonlayın:**
   ```powershell
   git clone https://github.com/kullaniciadi/mp3fy.git
   cd mp3fy
   ```

2. **Kurulum Scriptini Çalıştırın:**
   ```powershell
   # Gerekirse script çalıştırma iznini açın:
   Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass

   # Kurulumu başlatın:
   .\install.ps1
   ```

3. **FFmpeg'i Yükleyin (Henüz sisteminizde yoksa):**
   ```powershell
   winget install Gyan.FFmpeg
   # veya Scoop kullanıyorsanız:
   scoop install ffmpeg
   # veya Chocolatey kullanıyorsanız:
   choco install ffmpeg
   ```

Kurulum tamamlandığında `$HOME\bin\mp3fy.cmd` ve `mp3fy.ps1` oluşturulur, kullanıcı PATH değişkeninize eklenir ve PowerShell profilinize (`$PROFILE`) `mp3fy` fonksiyonu tanımlanır. Artık herhangi bir PowerShell penceresinde sadece `mp3fy` yazmanız yeterlidir!

---

### Linux Kurulumu

```bash
chmod +x install.sh
./install.sh
```

---

## 🚀 Komut Olarak Kullanım (`mp3fy`)

Terminalde veya PowerShell penceresinde herhangi bir dizindeyken:
```powershell
mp3fy
```

### 1. Etkileşimli Terminal Sihirbazı
Hiçbir parametre vermeden `mp3fy` yazdığınızda etkileşimli mod açılır:
1. **Spotify URL:** Şarkı, albüm veya çalma listesi linkini yapıştırın (çıkmak için `q`).
2. **Bölüm Seçimi:** Liste 100 şarkıdan büyükse hangi bölümü indirmek istediğinizi sorar (Tümünü indirmek için `T`).
3. **Hedef Klasör:** Varsayılan müzik dizini gelir, Enter ile onaylayabilir veya başka bir klasör yolu yazabilirsiniz.
4. **Ses Kalitesi:** 320, 256, 192 veya 128 kbps seçebilirsiniz (Varsayılan: 320).
5. **Eşzamanlı İşlem:** Aynı anda indirilecek parça sayısı (Varsayılan: 2).

### 2. Doğrudan Tek Komutla İndirme
Parametreleri tek satırda belirterek indirme yapabilirsiniz:
```powershell
# Şarkı indirme
mp3fy "https://open.spotify.com/track/4LfCY65LvojKjWEnU7fNN4"

# Çalma listesini özel klasöre 320kbps olarak 3 iş parçacığıyla indirme
mp3fy "https://open.spotify.com/playlist/37i9dQZF1DXcBWIGoYBM5M" -o "$HOME\Music\Favoriler" -b 320 -w 3

# Albüm indirme
mp3fy "https://open.spotify.com/album/4m2880jivSbbyEGAKfITCa"
```

### 3. 100'lük Bölümleme (Batching)
Örneğin 250 şarkılık bir listede:
- 1. Bölüm: 1 - 100
- 2. Bölüm: 101 - 200
- 3. Bölüm: 201 - 250

Sadece 2. bölümü indirmek için:
```powershell
mp3fy "https://open.spotify.com/playlist/37i9dQZF1DXcBWIGoYBM5M" --batch 2
```

---

## ⚙️ Tüm Parametreler (CLI Flags)

| Bayrak | Açıklama |
| :--- | :--- |
| `url` | İndirilecek Spotify URL'si (belirtilmezse etkileşimli mod başlar) |
| `-i`, `--interactive` | Etkileşimli sihirbazı zorunlu çalıştırır |
| `-o`, `--output` | İndirilen dosyaların yazılacağı hedef dizin (Varsayılan: Müzik klasörü) |
| `-b`, `--bitrate` | MP3 ses kalitesi (`128`, `192`, `256`, `320`) |
| `-w`, `--workers` | Eşzamanlı iş parçacığı sayısı (Varsayılan: `2`) |
| `--batch` | 100+ şarkılık listelerde belirli bölümü indirme (örn: `1`, `2`) |
| `-v`, `--version` | MP3fy sürüm numarasını gösterir |
| `-h`, `--help` | Yardım ve komut listesini gösterir |

---

## 💡 PowerShell & Windows İpuçları

1. **Hızlı Başlatıcı Script:**
   Depo klasöründeyseniz doğrudan `.\run.ps1` veya `.\run.bat` ile de başlatabilirsiniz.
2. **Karakter Kodlaması (UTF-8):**
   MP3fy, Windows konsolunda otomatik olarak UTF-8 ve ANSI Virtual Terminal Processing modunu etkinleştirir; şarkı başlıklarındaki Türkçe ve özel karakterler bozulmadan ekrana yansır.
3. **ExecutionPolicy Hatası:**
   Eğer `install.ps1` çalışırken script yürütme politikası uyarısı alırsanız:
   ```powershell
   Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned
   ```
   komutunu bir kez çalıştırmanız yeterlidir.

---

## ❓ Sorun Giderme & SSS

**1. `mp3fy: komut bulunamadı` veya `The term 'mp3fy' is not recognized` hatası alıyorum:**  
Yeni bir PowerShell penceresi açın. Kurulum scripti `$HOME\bin` dizinini kullanıcı PATH değişkenine ekler. Eğer terminali kapatmadan denediyseniz:
```powershell
$env:Path = "$HOME\bin;$env:Path"
```
çalıştırarak geçerli oturumu güncelleyebilirsiniz.

**2. `ffmpeg` hatası alıyorum:**  
Sisteminizde FFmpeg eksikse PowerShell'de şu komutla yükleyin:
```powershell
winget install Gyan.FFmpeg
```
Yükledikten sonra PowerShell'i yeniden başlatın.

**3. İndirilen şarkılar nerede saklanıyor?**  
Varsayılan konum Windows'ta `C:\Users\<Kullanıcı>\Music` klasörüdür.
