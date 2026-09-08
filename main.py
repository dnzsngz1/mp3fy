#!/usr/bin/env python3
"""
MP3fy - Spotify to MP3 Downloader & ID3 Tagging CLI Tool for PowerShell, Windows & Linux.
"""

import os
import sys
import time
import signal
import argparse
from pathlib import Path
from typing import Optional, List

# Ensure UTF-8 console output and ANSI escape sequence support across platforms
if sys.platform == "win32":
    try:
        if hasattr(sys.stdout, "reconfigure"):
            sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        if hasattr(sys.stderr, "reconfigure"):
            sys.stderr.reconfigure(encoding="utf-8", errors="replace")
        if hasattr(sys.stdin, "reconfigure"):
            sys.stdin.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
    try:
        import ctypes
        kernel32 = ctypes.windll.kernel32
        # Enable VT100 / ANSI virtual terminal processing on stdout (-11) and stderr (-12)
        for handle_id in (-11, -12):
            h = kernel32.GetStdHandle(handle_id)
            mode = ctypes.c_ulong()
            if kernel32.GetConsoleMode(h, ctypes.byref(mode)):
                kernel32.SetConsoleMode(h, mode.value | 0x0004)
        # Ensure console code page is UTF-8 (65001)
        kernel32.SetConsoleOutputCP(65001)
        kernel32.SetConsoleCP(65001)
    except Exception:
        pass

# Ensure ~/.local/bin, ~/bin, project paths, and common Windows paths are in PATH and sys.path
BASE_DIR = Path(__file__).resolve().parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

local_bins = [
    str(Path.home() / "bin"),
    str(Path.home() / ".local" / "bin"),
    str(Path.home() / ".local" / "share" / "ffmpeg"),
    str(BASE_DIR / "bin"),
    str(BASE_DIR / ".venv" / "Scripts"),
]
if sys.platform == "win32":
    local_app_data = os.environ.get("LOCALAPPDATA", str(Path.home() / "AppData" / "Local"))
    program_files = os.environ.get("ProgramFiles", r"C:\Program Files")
    local_bins.extend([
        r"C:\ffmpeg\bin",
        os.path.join(program_files, "ffmpeg", "bin"),
        os.path.join(local_app_data, "Microsoft", "WinGet", "Links"),
        str(Path.home() / "scoop" / "shims"),
        str(Path.home() / "scoop" / "apps" / "ffmpeg" / "current" / "bin"),
        str(Path.home() / "AppData" / "Local" / "ffmpeg" / "bin"),
        r"C:\ProgramData\chocolatey\bin",
    ])

current_path = os.environ.get("PATH", "")
path_dirs = current_path.split(os.path.pathsep)
for p in local_bins:
    if p not in path_dirs and Path(p).exists():
        current_path = p + os.path.pathsep + current_path
os.environ["PATH"] = current_path

from core.spotify import SpotifyFetcher, PlaylistMetadata, SongMetadata, parse_spotify_url
from core.downloader import Downloader, DownloadTask
from core.utils import ensure_directory, get_default_music_dir, open_native_folder_picker

VERSION = "1.2.0"

# Attempt importing Rich for enhanced terminal UX
try:
    from rich.console import Console
    from rich.panel import Panel
    from rich.table import Table
    from rich.progress import (
        Progress,
        SpinnerColumn,
        BarColumn,
        TextColumn,
        TaskProgressColumn,
        TimeRemainingColumn,
        DownloadColumn,
        TransferSpeedColumn,
    )
    from rich.prompt import Prompt, Confirm
    from rich.text import Text
    from rich import print as rprint
    HAS_RICH = True
    console = Console()
except ImportError:
    HAS_RICH = False
    console = None


BANNER_TEXT = r"""
  __  __ _____ ____   __       
 |  \/  |  __ \___ \ / _|      
 | \  / | |__) |__) | |_ _   _ 
 | |\/| |  ___/|__ <|  _| | | |
 | |  | | |    ___) | | | |_| |
 |_|  |_|_|   |____/|_|  \__, |
                          __/ |
                         |___/ 
 Spotify to MP3 Downloader & Tagging Tool (PowerShell & CLI)
"""


def show_banner():
    if HAS_RICH:
        banner_panel = Panel(
            Text(BANNER_TEXT, style="bold cyan"),
            subtitle=f"[bold green]v{VERSION} | PowerShell & CLI Edition[/bold green]",
            border_style="bright_blue",
        )
        console.print(banner_panel)
    else:
        print(BANNER_TEXT)
        print(f" v{VERSION} - PowerShell & CLI Edition\n" + "-" * 50)


def check_dependencies():
    """Verify that ffmpeg is available in the system."""
    import shutil
    ffmpeg_found = shutil.which("ffmpeg") or (sys.platform == "win32" and shutil.which("ffmpeg.exe"))
    if not ffmpeg_found:
        if sys.platform == "win32":
            install_hint_rich = (
                "  PowerShell: [yellow]winget install Gyan.FFmpeg[/yellow]\n"
                "  veya Scoop: [yellow]scoop install ffmpeg[/yellow]\n"
                "  veya Choco: [yellow]choco install ffmpeg[/yellow]"
            )
            install_hint_plain = (
                "  PowerShell: winget install Gyan.FFmpeg\n"
                "  veya Scoop: scoop install ffmpeg\n"
                "  veya Choco: choco install ffmpeg"
            )
        elif sys.platform == "darwin":
            install_hint_rich = "  Terminal: [yellow]brew install ffmpeg[/yellow]"
            install_hint_plain = "  Terminal: brew install ffmpeg"
        else:
            install_hint_rich = "  Terminal: [yellow]sudo apt install ffmpeg[/yellow] (Ubuntu/Debian/Mint)"
            install_hint_plain = "  Terminal: sudo apt install ffmpeg (Ubuntu/Debian/Mint)"

        msg = (
            "[bold red][!] Uyarı: 'ffmpeg' komutu bulunamadı![/bold red]\n"
            "MP3 dönüştürme ve ses işleme için ffmpeg gereklidir.\n"
            "Yüklemek için:\n"
            f"{install_hint_rich}\n"
            "veya MP3fy otomatik kurucusu aracılığıyla ekleyin."
        ) if HAS_RICH else (
            "[!] Uyarı: 'ffmpeg' komutu bulunamadı!\n"
            "MP3 dönüştürme için ffmpeg gereklidir.\n"
            "Yüklemek için:\n"
            f"{install_hint_plain}"
        )
        if HAS_RICH:
            console.print(Panel(msg, title="[bold yellow]Bağımlılık Uyarısı[/bold yellow]", border_style="yellow"))
        else:
            print(msg)


def format_size(size_mb: Optional[float]) -> str:
    if size_mb is None:
        return "0.0 MB"
    return f"{size_mb:.1f} MB"


def execute_download(
    data: PlaylistMetadata,
    tracks_to_download: List[SongMetadata],
    output_dir: Path,
    bitrate: str,
    max_workers: int,
):
    """Executes the download queue with live terminal progress."""
    ensure_directory(output_dir)
    total_tracks = len(tracks_to_download)
    completed_count = 0
    failed_count = 0
    start_time = time.time()

    if HAS_RICH:
        # Summary table before starting
        summary_table = Table(title="🎵 İndirme Detayları", border_style="cyan", show_header=False)
        summary_table.add_column("Özellik", style="bold yellow")
        summary_table.add_column("Değer", style="white")

        summary_table.add_row("Başlık", data.title)
        summary_table.add_row("Sanatçı / Sahip", data.owner or "Bilinmiyor")
        summary_table.add_row("Tür", data.type.upper())
        summary_table.add_row("İndirilecek Şarkı", f"{total_tracks} adet")
        summary_table.add_row("Hedef Klasör", str(output_dir))
        summary_table.add_row("Ses Kalitesi", f"{bitrate} kbps")
        summary_table.add_row("Eşzamanlı İşlem", str(max_workers))
        console.print(summary_table)
        console.print()
    else:
        print(f"[*] Başlık: {data.title}")
        print(f"[*] Tür: {data.type.upper()} ({total_tracks} şarkı)")
        print(f"[*] Hedef: {output_dir} | Kalite: {bitrate} kbps | Eşzamanlı: {max_workers}")
        print("-" * 60)

    # Active downloader instance
    active_downloader: Optional[Downloader] = None

    def signal_handler(sig, frame):
        if HAS_RICH:
            console.print("\n[bold red][!] İşlem kullanıcı tarafından durduruldu (Ctrl+C). İptal ediliyor...[/bold red]")
        else:
            print("\n[!] İşlem durduruldu (Ctrl+C). İptal ediliyor...")
        if active_downloader:
            active_downloader.cancel_all()
        sys.exit(130)

    signal.signal(signal.SIGINT, signal_handler)

    if HAS_RICH:
        overall_progress = Progress(
            SpinnerColumn(spinner_name="dots"),
            TextColumn("[bold cyan]{task.description}"),
            BarColumn(bar_width=40),
            TaskProgressColumn(),
            TextColumn("•"),
            TimeRemainingColumn(),
            console=console,
        )

        with overall_progress:
            overall_task = overall_progress.add_task(
                f"[bold green]İndiriliyor: 0/{total_tracks}", total=total_tracks
            )

            # Dictionary to track task progress
            def on_progress_rich(task: DownloadTask):
                nonlocal completed_count, failed_count
                title_clean = task.song.title[:35]
                artist_clean = task.song.artist[:25]
                label = f"{artist_clean} - {title_clean}"

                if task.status == "completed":
                    completed_count += 1
                    overall_progress.update(
                        overall_task,
                        completed=completed_count + failed_count,
                        description=f"[bold green]Tamamlandı: {completed_count}/{total_tracks} ({task.file_size_mb or 0:.1f} MB)",
                    )
                    console.print(f" [bold green]✓[/bold green] [white]{label}[/white] - [green]Tamamlandı ({task.file_size_mb or 0:.1f} MB)[/green]")
                elif task.status == "error":
                    failed_count += 1
                    overall_progress.update(
                        overall_task,
                        completed=completed_count + failed_count,
                    )
                    console.print(f" [bold red]✗[/bold red] [white]{label}[/white] - [red]Hata: {task.error_message}[/red]")

            active_downloader = Downloader(
                output_dir=output_dir,
                bitrate=bitrate,
                max_workers=max_workers,
                on_progress=on_progress_rich,
            )

            tasks = active_downloader.download_playlist(tracks_to_download)

            # Wait for all tasks
            while True:
                all_done = all(t.status in ["completed", "error", "cancelled"] for t in tasks)
                if all_done:
                    break
                time.sleep(0.3)

    else:
        def on_progress_simple(task: DownloadTask):
            nonlocal completed_count, failed_count
            if task.status == "completed":
                completed_count += 1
                print(f"[✓] ({completed_count}/{total_tracks}) {task.song.artist} - {task.song.title} ({task.file_size_mb or 0:.1f} MB)")
            elif task.status == "error":
                failed_count += 1
                print(f"[✗] {task.song.title} - Hata: {task.error_message}")
            elif task.status == "downloading":
                print(f"\r[-] İndiriliyor: %{task.progress:.0f} {task.speed} {task.eta}   ", end="", flush=True)

        active_downloader = Downloader(
            output_dir=output_dir,
            bitrate=bitrate,
            max_workers=max_workers,
            on_progress=on_progress_simple,
        )

        tasks = active_downloader.download_playlist(tracks_to_download)
        while True:
            all_done = all(t.status in ["completed", "error", "cancelled"] for t in tasks)
            if all_done:
                break
            time.sleep(0.4)

    duration = time.time() - start_time
    duration_str = f"{int(duration // 60)}d {int(duration % 60)}s"

    if HAS_RICH:
        console.print()
        results_panel = Panel(
            Text.from_markup(
                f"[bold green]✔ İndirme işlemi tamamlandı![/bold green]\n\n"
                f"• Başarılı: [bold green]{completed_count}[/bold green] / {total_tracks}\n"
                f"• Hatalı: [bold red]{failed_count}[/bold red]\n"
                f"• Toplam Süre: [bold cyan]{duration_str}[/bold cyan]\n"
                f"• Kayıt Konumu: [bold white]{output_dir}[/bold white]"
            ),
            title="[bold green]İşlem Sonucu[/bold green]",
            border_style="green" if failed_count == 0 else "yellow",
        )
        console.print(results_panel)
    else:
        print("\n" + "=" * 60)
        print(f"[★] Tamamlandı! {completed_count}/{total_tracks} şarkı kaydedildi.")
        print(f"[*] Kayıt konumu: {output_dir}")
        print(f"[*] Toplam süre: {duration_str}")
        print("=" * 60)


def interactive_mode():
    """Interactive command-line wizard."""
    show_banner()
    check_dependencies()

    default_out = str(get_default_music_dir())

    while True:
        try:
            if HAS_RICH:
                url_prompt = Prompt.ask("\n[bold cyan]🎵 Spotify URL girin[/bold cyan] (veya çıkış için [bold red]q[/bold red])").strip()
            else:
                url_prompt = input("\n🎵 Spotify URL girin (veya çıkış için q): ").strip()

            if not url_prompt:
                continue
            if url_prompt.lower() in ["q", "quit", "exit", "cikis", "çıkış"]:
                if HAS_RICH:
                    console.print("[yellow]MP3fy sonlandırıldı. İyi günler![/yellow]")
                else:
                    print("MP3fy sonlandırıldı. İyi günler!")
                sys.exit(0)

            # Validate URL
            spotify_type, spotify_id = parse_spotify_url(url_prompt)
            if not spotify_type or not spotify_id:
                msg = "[bold red][!] Geçersiz Spotify bağlantısı![/bold red] Lütfen geçerli bir playlist, album veya şarkı linki girin."
                if HAS_RICH:
                    console.print(msg)
                else:
                    print("[!] Geçersiz Spotify bağlantısı!")
                continue

            # Fetch metadata
            if HAS_RICH:
                with console.status("[bold cyan]Spotify bilgileri taranıyor...[/bold cyan]", spinner="bouncingBar"):
                    fetcher = SpotifyFetcher()
                    data = fetcher.fetch(url_prompt)
            else:
                print("[*] Spotify bilgileri taranıyor...")
                fetcher = SpotifyFetcher()
                data = fetcher.fetch(url_prompt)

            if not data or not data.tracks:
                if HAS_RICH:
                    console.print("[bold red][!] Müzik bilgisi alınamadı veya liste boş.[/bold red]")
                else:
                    print("[!] Müzik bilgisi alınamadı veya liste boş.")
                continue

            # Display info
            if HAS_RICH:
                info_table = Table(border_style="blue", show_header=False)
                info_table.add_column("Alan", style="bold cyan")
                info_table.add_column("Detay", style="white")
                info_table.add_row("Tür", data.type.upper())
                info_table.add_row("Başlık", data.title)
                info_table.add_row("Sanatçı / Sahip", data.owner or "Belirtilmemiş")
                info_table.add_row("Şarkı Sayısı", str(len(data.tracks)))
                console.print(Panel(info_table, title="[bold green]Bağlantı Bilgisi[/bold green]"))
            else:
                print(f"[+] Başlık: {data.title} | Tür: {data.type.upper()} | Toplam: {len(data.tracks)} şarkı")

            tracks_to_download = data.tracks

            # Batch selection for playlists > 100 tracks
            if len(data.batches) > 1:
                if HAS_RICH:
                    console.print(f"\n[bold yellow]Bu liste {len(data.tracks)} şarkı içermektedir ve {len(data.batches)} bölüme ayrılmıştır:[/bold yellow]")
                    batch_table = Table(show_header=True, header_style="bold magenta")
                    batch_table.add_column("Bölüm", style="cyan")
                    batch_table.add_column("Aralık", style="green")
                    batch_table.add_column("Şarkı Sayısı", style="white")
                    for b in data.batches:
                        batch_table.add_row(f"Bölüm {b.batch_index}", f"{b.start_index} - {b.end_index}", str(b.count))
                    console.print(batch_table)

                    choice = Prompt.ask(
                        "İndirmek istediğiniz bölüm ([bold green]T[/bold green]=Tümü, veya bölüm no örn: 1, 2)",
                        default="T",
                    ).strip()
                else:
                    print(f"\nBu liste {len(data.tracks)} şarkı içermektedir ({len(data.batches)} bölüm).")
                    for b in data.batches:
                        print(f"  - Bölüm {b.batch_index}: {b.start_index}-{b.end_index} ({b.count} şarkı)")
                    choice = input("Bölüm seçin (T=Tümü, veya 1, 2...): [T] ").strip() or "T"

                if choice.upper() != "T":
                    try:
                        b_idx = int(choice)
                        selected_tracks = [t for t in data.tracks if getattr(t, "batch_index", 1) == b_idx]
                        if selected_tracks:
                            tracks_to_download = selected_tracks
                            if HAS_RICH:
                                console.print(f"[green]✓ Yalnızca Bölüm {b_idx} ({len(tracks_to_download)} şarkı) indirilecek.[/green]")
                            else:
                                print(f"Yalnızca Bölüm {b_idx} indirilecek.")
                    except ValueError:
                        pass

            # Folder selection
            if HAS_RICH:
                out_str = Prompt.ask("Hedef klasör (veya seçici için 'b')", default=default_out).strip()
            else:
                out_input = input(f"Hedef klasör (veya seçici için 'b') [{default_out}]: ").strip()
                out_str = out_input if out_input else default_out
            if out_str.lower() in ["b", "browse", "sec", "seç"]:
                picked = open_native_folder_picker(default_out)
                if picked:
                    out_str = picked
                    if HAS_RICH:
                        console.print(f"[green]✓ Klasör seçildi: {out_str}[/green]")
                    else:
                        print(f"Klasör seçildi: {out_str}")
                else:
                    out_str = default_out
            output_dir = Path(out_str).resolve()

            # Bitrate selection
            if HAS_RICH:
                bitrate = Prompt.ask(
                    "Ses Kalitesi (kbps)",
                    choices=["128", "192", "256", "320"],
                    default="320",
                )
            else:
                bit_input = input("Ses Kalitesi (128, 192, 256, 320) [320]: ").strip()
                bitrate = bit_input if bit_input in ["128", "192", "256", "320"] else "320"

            # Workers selection
            if HAS_RICH:
                workers_str = Prompt.ask("Eşzamanlı indirme sayısı", default="2")
            else:
                w_input = input("Eşzamanlı indirme sayısı [2]: ").strip()
                workers_str = w_input if w_input else "2"
            try:
                workers = max(1, min(8, int(workers_str)))
            except ValueError:
                workers = 2

            # Execute
            execute_download(data, tracks_to_download, output_dir, bitrate, workers)

        except (KeyboardInterrupt, EOFError):
            if HAS_RICH:
                console.print("\n[yellow]Çıkış yapılıyor...[/yellow]")
            else:
                print("\nÇıkış yapılıyor...")
            sys.exit(0)
        except Exception as e:
            if HAS_RICH:
                console.print(f"[bold red][!] Hata oluştu: {e}[/bold red]")
            else:
                print(f"[!] Hata oluştu: {e}")


def main():
    parser = argparse.ArgumentParser(
        prog="mp3fy",
        description="MP3fy - Spotify Playlist/Album/Track to MP3 Converter with ID3 Metadata & Album Art (PowerShell & CLI).",
    )
    parser.add_argument(
        "url",
        nargs="?",
        default=None,
        help="Spotify çalma listesi, albüm veya parça bağlantısı. Belirtilmezse etkileşimli mod açılır.",
    )
    parser.add_argument(
        "-i",
        "--interactive",
        action="store_true",
        help="Etkileşimli terminal sihirbazını başlat",
    )
    parser.add_argument(
        "-o",
        "--output",
        default=None,
        help="İndirilen MP3 dosyalarının kaydedileceği hedef klasör (Varsayılan: ~/Music)",
    )
    parser.add_argument(
        "-b",
        "--bitrate",
        default="320",
        choices=["128", "192", "256", "320"],
        help="MP3 ses kalitesi (kbps) (Varsayılan: 320)",
    )
    parser.add_argument(
        "-w",
        "--workers",
        type=int,
        default=2,
        help="Eşzamanlı indirme iş parçacığı sayısı (Varsayılan: 2)",
    )
    parser.add_argument(
        "--batch",
        type=int,
        default=None,
        help="100+ şarkılık listelerde sadece belirtilen bölümü indir (örneğin 1, 2)",
    )
    parser.add_argument(
        "-v",
        "--version",
        action="version",
        version=f"MP3fy v{VERSION}",
        help="Sürüm bilgisini göster",
    )

    args = parser.parse_args()

    # If no URL is provided or explicitly requested interactive, launch interactive mode
    if not args.url or args.interactive:
        interactive_mode()
        return

    # Direct CLI execution
    show_banner()
    check_dependencies()

    out_path = Path(args.output).resolve() if args.output else get_default_music_dir()
    ensure_directory(out_path)

    if HAS_RICH:
        console.print(f"[*] Spotify bağlantısı çözümleniyor: [bold cyan]{args.url}[/bold cyan]")
        with console.status("[bold cyan]Spotify verileri alınıyor...[/bold cyan]", spinner="dots"):
            fetcher = SpotifyFetcher()
            try:
                data = fetcher.fetch(args.url)
            except Exception as e:
                console.print(f"[bold red][!] Hata: Spotify bilgisi alınamadı - {e}[/bold red]")
                sys.exit(1)
    else:
        print(f"[*] Spotify bağlantısı çözümleniyor: {args.url}")
        fetcher = SpotifyFetcher()
        try:
            data = fetcher.fetch(args.url)
        except Exception as e:
            print(f"[!] Hata: Spotify bilgisi alınamadı - {e}")
            sys.exit(1)

    tracks = data.tracks
    if args.batch:
        tracks = [t for t in tracks if getattr(t, "batch_index", 1) == args.batch]
        if not tracks:
            msg = f"[!] Belirtilen bölüm ({args.batch}) bulunamadı. Toplam bölüm sayısı: {len(data.batches)}"
            if HAS_RICH:
                console.print(f"[bold red]{msg}[/bold red]")
            else:
                print(msg)
            sys.exit(1)

    execute_download(
        data=data,
        tracks_to_download=tracks,
        output_dir=out_path,
        bitrate=args.bitrate,
        max_workers=max(1, min(8, args.workers)),
    )


if __name__ == "__main__":
    main()
