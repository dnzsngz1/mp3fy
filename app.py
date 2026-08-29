"""
MP3fy Web Application Backend using FastAPI & Uvicorn.
Provides REST API, WebSocket real-time progress updates, and static files.
"""

import os
import sys
import asyncio
import json
import logging
from pathlib import Path
from typing import Optional, List, Dict, Any

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, Query
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from core.spotify import SpotifyFetcher, PlaylistMetadata, SongMetadata
from core.downloader import Downloader, DownloadTask
from core.utils import ensure_directory, get_default_music_dir, open_folder_in_explorer

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("mp3fy")

# Directories
BASE_DIR = Path(__file__).resolve().parent
STATIC_DIR = BASE_DIR / "web" / "static"
TEMPLATES_DIR = BASE_DIR / "web" / "templates"
MUSIC_DIR = get_default_music_dir()

app = FastAPI(title="MP3fy - Spotify to MP3 Converter", version="1.0.0")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))

# Global state
app_state: Dict[str, Any] = {
    "output_dir": str(MUSIC_DIR),
    "bitrate": "320",
    "max_workers": 2,
    "spotify_client_id": "",
    "spotify_client_secret": "",
    "current_playlist": None,
}

# WebSocket Manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []
        self._loop = None

    def set_loop(self, loop):
        self._loop = loop

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def broadcast(self, message: dict):
        for connection in list(self.active_connections):
            try:
                await connection.send_json(message)
            except Exception:
                self.disconnect(connection)

    def broadcast_sync(self, message: dict):
        if self._loop and self.active_connections:
            asyncio.run_coroutine_threadsafe(self.broadcast(message), self._loop)


ws_manager = ConnectionManager()


def on_download_progress(task: DownloadTask):
    """Callback fired by downloader on progress updates."""
    ws_manager.broadcast_sync({
        "type": "task_update",
        "task": task.to_dict(),
    })


# Instantiate Downloader and Fetcher
downloader = Downloader(
    output_dir=MUSIC_DIR,
    bitrate=app_state["bitrate"],
    max_workers=app_state["max_workers"],
    on_progress=on_download_progress,
)
fetcher = SpotifyFetcher()


@app.on_event("startup")
async def startup_event():
    loop = asyncio.get_running_loop()
    ws_manager.set_loop(loop)
    logger.info(f"MP3fy started. Music folder: {downloader.output_dir}")


# Request Models
class FetchRequest(BaseModel):
    url: str


class DownloadSingleRequest(BaseModel):
    song: Dict[str, Any]
    output_dir: Optional[str] = None
    bitrate: Optional[str] = None


class DownloadBatchRequest(BaseModel):
    songs: List[Dict[str, Any]]
    output_dir: Optional[str] = None
    bitrate: Optional[str] = None


class SettingsRequest(BaseModel):
    output_dir: Optional[str] = None
    bitrate: Optional[str] = None
    max_workers: Optional[int] = None
    spotify_client_id: Optional[str] = None
    spotify_client_secret: Optional[str] = None


# Routes
@app.get("/", response_class=HTMLResponse)
async def index_page():
    return templates.TemplateResponse("index.html", {"request": {}})


@app.post("/api/fetch")
async def fetch_spotify_url(req: FetchRequest):
    """Fetch playlist, album, or track info from Spotify link."""
    url = req.url.strip()
    if not url:
        raise HTTPException(status_code=400, detail="Lütfen bir Spotify bağlantısı girin.")

    try:
        # Use current credentials if set
        active_fetcher = SpotifyFetcher(
            client_id=app_state["spotify_client_id"] or None,
            client_secret=app_state["spotify_client_secret"] or None,
        )
        playlist_data = active_fetcher.fetch(url)
        if not playlist_data:
            raise HTTPException(status_code=404, detail="Bağlantıdan müzik bilgisi alınamadı.")

        app_state["current_playlist"] = playlist_data
        return JSONResponse(content={"status": "success", "data": playlist_data.to_dict()})
    except Exception as e:
        logger.error(f"Error fetching Spotify URL {url}: {e}", exc_info=True)
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/api/download/single")
async def download_single(req: DownloadSingleRequest):
    """Download a single track."""
    song_dict = req.song
    song = SongMetadata(
        id=song_dict["id"],
        title=song_dict["title"],
        artist=song_dict["artist"],
        album=song_dict.get("album", ""),
        year=song_dict.get("year"),
        track_number=song_dict.get("track_number", 1),
        total_tracks=song_dict.get("total_tracks", 1),
        duration_ms=song_dict.get("duration_ms", 0),
        duration_formatted=song_dict.get("duration_formatted", "0:00"),
        cover_url=song_dict.get("cover_url"),
        preview_url=song_dict.get("preview_url"),
        spotify_url=song_dict.get("spotify_url", ""),
    )

    out_dir = Path(req.output_dir) if req.output_dir else downloader.output_dir
    bitrate = req.bitrate or downloader.bitrate

    task = downloader.download_song(song, output_dir=out_dir, bitrate=bitrate)
    return JSONResponse(content={"status": "queued", "task": task.to_dict()})


@app.post("/api/download/batch")
async def download_batch(req: DownloadBatchRequest):
    """Download a batch of tracks."""
    songs_list = []
    for s_dict in req.songs:
        song = SongMetadata(
            id=s_dict["id"],
            title=s_dict["title"],
            artist=s_dict["artist"],
            album=s_dict.get("album", ""),
            year=s_dict.get("year"),
            track_number=s_dict.get("track_number", 1),
            total_tracks=s_dict.get("total_tracks", len(req.songs)),
            duration_ms=s_dict.get("duration_ms", 0),
            duration_formatted=s_dict.get("duration_formatted", "0:00"),
            cover_url=s_dict.get("cover_url"),
            preview_url=s_dict.get("preview_url"),
            spotify_url=s_dict.get("spotify_url", ""),
        )
        songs_list.append(song)

    out_dir = Path(req.output_dir) if req.output_dir else downloader.output_dir
    bitrate = req.bitrate or downloader.bitrate

    tasks = downloader.download_playlist(songs_list, output_dir=out_dir, bitrate=bitrate)
    return JSONResponse(content={"status": "queued", "tasks": [t.to_dict() for t in tasks]})


@app.post("/api/cancel/{song_id}")
async def cancel_download(song_id: str):
    downloader.cancel_task(song_id)
    return JSONResponse(content={"status": "cancelled", "song_id": song_id})


@app.post("/api/cancel-all")
async def cancel_all_downloads():
    downloader.cancel_all()
    return JSONResponse(content={"status": "all_cancelled"})


@app.get("/api/tasks")
async def get_tasks():
    tasks = {k: v.to_dict() for k, v in downloader.tasks.items()}
    return JSONResponse(content={"tasks": tasks})


@app.post("/api/open-folder")
async def open_music_folder():
    """Open the music folder in the OS file explorer."""
    current_dir = downloader.output_dir
    success = open_folder_in_explorer(current_dir)
    return JSONResponse(content={"status": "success" if success else "failed", "path": str(current_dir)})


@app.get("/api/settings")
async def get_settings():
    return JSONResponse(content={
        "output_dir": str(downloader.output_dir),
        "bitrate": downloader.bitrate,
        "max_workers": downloader.max_workers,
        "spotify_client_id": app_state["spotify_client_id"],
        "has_spotify_secret": bool(app_state["spotify_client_secret"]),
    })


@app.post("/api/settings")
async def update_settings(req: SettingsRequest):
    if req.output_dir:
        new_dir = ensure_directory(req.output_dir)
        downloader.set_output_dir(new_dir)
        app_state["output_dir"] = str(new_dir)

    if req.bitrate:
        downloader.set_bitrate(req.bitrate)
        app_state["bitrate"] = req.bitrate

    if req.spotify_client_id is not None:
        app_state["spotify_client_id"] = req.spotify_client_id.strip()

    if req.spotify_client_secret is not None:
        app_state["spotify_client_secret"] = req.spotify_client_secret.strip()

    return JSONResponse(content={"status": "updated", "settings": {
        "output_dir": str(downloader.output_dir),
        "bitrate": downloader.bitrate,
    }})


@app.get("/api/music/file")
async def stream_music_file(path: str = Query(...)):
    """Serve a local downloaded MP3 file for playback."""
    file_path = Path(path).resolve()
    if not file_path.exists() or file_path.suffix.lower() != ".mp3":
        raise HTTPException(status_code=404, detail="Müzik dosyası bulunamadı.")
    return FileResponse(file_path, media_type="audio/mpeg", filename=file_path.name)


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await ws_manager.connect(websocket)
    # Send initial tasks state
    await websocket.send_json({
        "type": "init",
        "tasks": {k: v.to_dict() for k, v in downloader.tasks.items()},
    })
    try:
        while True:
            data = await websocket.receive_text()
            # Can receive ping or client commands
            if data == "ping":
                await websocket.send_text("pong")
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket)
    except Exception:
        ws_manager.disconnect(websocket)


def run_server(host: str = "127.0.0.1", port: int = 8888, reload: bool = False):
    import uvicorn
    uvicorn.run("app:app", host=host, port=port, reload=reload)


if __name__ == "__main__":
    run_server()
