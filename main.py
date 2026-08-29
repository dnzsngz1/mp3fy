#!/usr/bin/env python3
"""
MP3fy - Spotify to MP3 Downloader & Converter
Entry point for CLI and Web Application.
"""

import os
import sys
import time
import argparse
import webbrowser
import threading
from pathlib import Path

# Add project root to sys.path
BASE_DIR = Path(__file__).resolve().parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from core.spotify import SpotifyFetcher
from core.downloader import Downloader, DownloadTask
from core.utils import ensure_directory, get_default_music_dir


def print_banner():
    banner = r"""
  __  __ _____ ____   __       
 |  \/  |  __ \___ \ / _|      
 | \  / | |__) |__) | |_ _   _ 
 | |\/| |  ___/|__ <|  _| | | |
 | |  | | |    ___) | | | |_| |
 |_|  |_|_|   |____/|_|  \__, |
                          __/ |
                         |___/ 
 Spotify to MP3 Downloader & Tagging Tool v1.0
 ---------------------------------------------
"""
    print(banner)


def run_cli_download(url: str, output_dir: Path, bitrate: str, max_workers: int):
    print_banner()
    print(f"[*] Spotify bağlantısı çözümleniyor: {url}")
    fetcher = SpotifyFetcher()
    try:
        data = fetcher.fetch(url)
    except Exception as e:
        print(f"[!] Hata: Spotify bilgisi alınamadı - {e}")
        sys.exit(1)

    print(f"[+] Başlık: {data.title}")
    print(f"[+] Sanatçı/Sahip: {data.owner}")
    print(f"[+] Tür: {data.type.upper()}")
    print(f"[+] Toplam Şarkı: {len(data.tracks)}")
    print(f"[+] Hedef Klasör: {output_dir}")
    print(f"[+] Ses Kalitesi: {bitrate} kbps")
    print("-" * 50)

    completed_count = 0
    total_count = len(data.tracks)

    def on_progress(task: DownloadTask):
        nonlocal completed_count
        if task.status == "downloading":
            print(
                f"\r[-] [{task.song.title[:30]}] İndiriliyor: %{task.progress:.0f} {task.speed} {task.eta}   ",
                end="",
                flush=True,
            )
        elif task.status == "converting":
            print(f"\r[-] [{task.song.title[:30]}] MP3 Dönüştürülüyor...               ", end="", flush=True)
        elif task.status == "tagging":
            print(f"\r[-] [{task.song.title[:30]}] Albüm Kapağı & ID3 Etiketleniyor... ", end="", flush=True)
        elif task.status == "completed":
            completed_count += 1
            print(f"\r[✓] ({completed_count}/{total_count}) {task.song.title} - Tamamlandı! ({task.file_size_mb:.1f} MB)\n")
        elif task.status == "error":
            print(f"\r[✗] [{task.song.title}] Hata: {task.error_message}\n")

    downloader = Downloader(
        output_dir=output_dir,
        bitrate=bitrate,
        max_workers=max_workers,
        on_progress=on_progress,
    )

    tasks = downloader.download_playlist(data.tracks)

    # Wait for all tasks to complete
    while True:
        all_done = all(t.status in ["completed", "error", "cancelled"] for t in tasks)
        if all_done:
            break
        time.sleep(0.5)

    print("-" * 50)
    print(f"[★] İndirme işlemi tamamlandı! {completed_count}/{total_count} şarkı '{output_dir}' klasörüne kaydedildi.")


def run_web(host: str, port: int, open_browser: bool):
    print_banner()
    url = f"http://{host}:{port}"
    print(f"[*] Web arayüzü başlatılıyor: {url}")
    print(f"[*] Siyah/Beyaz tema desteği ve canlı ilerleme paneli aktif.")
    print(f"[*] Durdurmak için Ctrl+C tuşlarına basın.\n")

    if open_browser:
        def _open():
            time.sleep(1.2)
            try:
                webbrowser.open(url)
            except Exception:
                pass

        threading.Thread(target=_open, daemon=True).start()

    import uvicorn
    from app import app
    uvicorn.run(app, host=host, port=port, log_level="warning")


def main():
    parser = argparse.ArgumentParser(
        description="MP3fy - Spotify Playlist/Album/Track to MP3 Converter with ID3 Metadata & Album Art."
    )
    parser.add_argument("url", nargs="?", help="Spotify playlist, album veya şarkı linki (CLI modu için)")
    parser.add_argument("--web", action="store_true", help="Web arayüzünü zorla başlat")
    parser.add_argument("--host", default="127.0.0.1", help="Web sunucu adresi (Varsayılan: 127.0.0.1)")
    parser.add_argument("--port", type=int, default=8888, help="Web sunucu portu (Varsayılan: 8888)")
    parser.add_argument("--no-browser", action="store_true", help="Tarayıcıyı otomatik açma")
    parser.add_argument(
        "-o",
        "--output",
        default=None,
        help="İndirilen MP3 dosyalarının kaydedileceği klasör (Varsayılan: Ev dizini ~/Music)",
    )
    parser.add_argument("-b", "--bitrate", default="320", choices=["128", "192", "256", "320"], help="MP3 Bitrate (Varsayılan: 320)")
    parser.add_argument("-w", "--workers", type=int, default=2, help="Eşzamanlı indirme sayısı (Varsayılan: 2)")

    args = parser.parse_args()

    # If URL is provided and not in web mode, run CLI
    if args.url and not args.web:
        out_path = Path(args.output).resolve() if args.output else get_default_music_dir()
        ensure_directory(out_path)
        run_cli_download(args.url, out_path, args.bitrate, args.workers)
    else:
        # Launch Web UI
        run_web(args.host, args.port, not args.no_browser)


if __name__ == "__main__":
    main()
