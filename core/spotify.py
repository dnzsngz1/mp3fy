"""
Spotify URL Parser and Metadata Fetcher for MP3fy.
Supports Playlists (with 100+ track pagination and 100-track batching), Albums, and Tracks.
"""

import re
import json
import logging
import math
from dataclasses import dataclass, field, asdict
from typing import List, Optional, Tuple, Dict, Any, Union
import requests
from urllib.parse import urlparse
from urllib3.util import Retry
from requests.adapters import HTTPAdapter

from core.utils import format_duration

logger = logging.getLogger(__name__)

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/122.0.0.0 Safari/537.36"
)

HTTP_HEADERS = {
    "User-Agent": USER_AGENT,
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9,tr;q=0.8",
}


def create_resilient_session(
    retries: int = 3,
    backoff_factor: float = 0.5,
    status_forcelist: tuple = (429, 500, 502, 503, 504),
) -> requests.Session:
    """Creates a requests.Session with exponential backoff and retry strategy."""
    session = requests.Session()
    retry_strategy = Retry(
        total=retries,
        read=retries,
        connect=retries,
        backoff_factor=backoff_factor,
        status_forcelist=status_forcelist,
        respect_retry_after_header=True,
        raise_on_status=False,
    )
    adapter = HTTPAdapter(max_retries=retry_strategy)
    session.mount("https://", adapter)
    session.mount("http://", adapter)
    session.headers.update(HTTP_HEADERS)
    return session


@dataclass
class SongMetadata:
    id: str
    title: str
    artist: str
    album: str = ""
    year: Optional[str] = None
    track_number: Optional[int] = None
    total_tracks: Optional[int] = None
    duration_ms: int = 0
    duration_formatted: str = "0:00"
    cover_url: Optional[str] = None
    preview_url: Optional[str] = None
    spotify_url: str = ""
    batch_index: int = 1  # 1-based index for 100-track chunks (e.g. 1 for 1-100, 2 for 101-200)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class BatchInfo:
    batch_index: int
    start_index: int
    end_index: int
    count: int
    name: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class PlaylistMetadata:
    id: str
    title: str
    description: str = ""
    owner: str = ""
    cover_url: Optional[str] = None
    total_tracks: int = 0
    type: str = "playlist"  # playlist, album, track
    tracks: List[SongMetadata] = field(default_factory=list)
    batches: List[BatchInfo] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "owner": self.owner,
            "cover_url": self.cover_url,
            "total_tracks": self.total_tracks,
            "type": self.type,
            "batches": [b.to_dict() for b in self.batches],
            "tracks": [t.to_dict() for t in self.tracks],
        }


def parse_spotify_url(url_or_uri: str) -> Tuple[Optional[str], Optional[str]]:
    """
    Parses a Spotify URL or URI and returns (type, id).
    Types: 'playlist', 'album', 'track'
    Supports regional language subtags (intl-[a-zA-Z0-9-]+/),
    embed URLs (/embed/(track|album|playlist)/[id]),
    legacy user playlist URLs (/user/[^/]+/playlist/[id]),
    and cleanly strips brackets (<...>), quotes, and query parameters.
    Only accepts valid Spotify domains: spotify.com, spotify.link, spoti.fi.
    """
    if not url_or_uri:
        return None, None

    url_clean = str(url_or_uri).strip()
    url_clean = re.sub(r'^[<"\'`\[\(]+|[>"\'`\]\)]+$', '', url_clean).strip()

    # Spotify URI: spotify:(playlist|album|track):([a-zA-Z0-9]+)
    uri_match = re.search(r"^spotify:(playlist|album|track):([a-zA-Z0-9]+)", url_clean)
    if uri_match:
        return uri_match.group(1), uri_match.group(2)

    if url_clean.startswith("spotify:"):
        return None, None

    # Parse with urllib.parse.urlparse
    parse_target = url_clean if "://" in url_clean else f"https://{url_clean}"
    try:
        parsed = urlparse(parse_target)
    except Exception:
        return None, None

    netloc = (parsed.netloc or "").lower()
    hostname = (parsed.hostname or netloc.split(":")[0]).lower()

    # Domain Validation: Only accept domains ending with spotify.com, spotify.link, or spoti.fi
    is_spotify_domain = (
        hostname == "spotify.com"
        or hostname.endswith(".spotify.com")
        or hostname == "spotify.link"
        or hostname.endswith(".spotify.link")
        or hostname == "spoti.fi"
        or hostname.endswith(".spoti.fi")
    )
    if not is_spotify_domain:
        return None, None

    # Safe Shortlink Check: Only trigger requests.head() if parsed netloc is spotify.link or spoti.fi
    if hostname == "spotify.link" or hostname.endswith(".spotify.link") or hostname == "spoti.fi" or hostname.endswith(".spoti.fi"):
        try:
            resp = requests.head(parse_target, allow_redirects=True, timeout=5)
            if resp.url and resp.url != parse_target:
                return parse_spotify_url(resp.url)
        except Exception:
            pass
        return None, None

    # Spotify Web URL matching:
    # Optional regional tag: (?:intl-[a-zA-Z0-9-]+/)?
    # Optional embed: (?:embed/)?
    # Legacy user playlist: (?:user/[^/?#]+/)?
    # Entity type: (playlist|album|track)
    # Entity ID: ([a-zA-Z0-9]+)
    url_match = re.search(
        r"(?:intl-[a-zA-Z0-9-]+/)?(?:embed/)?(?:user/[^/?#]+/)?(playlist|album|track)/([a-zA-Z0-9]+)",
        parsed.path,
    )
    if url_match:
        return url_match.group(1), url_match.group(2)

    return None, None


def _format_duration(duration_ms: Optional[Union[int, float]]) -> str:
    return format_duration(duration_ms)


def _create_batches(tracks: List[SongMetadata], batch_size: int = 100) -> List[BatchInfo]:
    """Divides tracks into 100-track sections."""
    if not tracks:
        return []
    
    total = len(tracks)
    num_batches = math.ceil(total / batch_size)
    batches = []
    
    for b_idx in range(1, num_batches + 1):
        start = (b_idx - 1) * batch_size + 1
        end = min(b_idx * batch_size, total)
        count = end - start + 1
        name = f"Bölüm {b_idx} ({start} - {end})"
        batches.append(BatchInfo(
            batch_index=b_idx,
            start_index=start,
            end_index=end,
            count=count,
            name=name
        ))
        
        # Tag tracks with batch_index
        for track in tracks[start - 1 : end]:
            track.batch_index = b_idx
            
    return batches


class SpotifyFetcher:
    """
    Handles fetching Spotify metadata using Spotapi (supports all 100+ tracks),
    Spotify Embed scraping fallback, or official Spotipy API.
    """

    def __init__(self, client_id: Optional[str] = None, client_secret: Optional[str] = None):
        self.client_id = client_id
        self.client_secret = client_secret
        self._sp_client = None
        self.session = create_resilient_session()

        if self.client_id and self.client_secret:
            try:
                import spotipy
                from spotipy.oauth2 import SpotifyClientCredentials

                auth_manager = SpotifyClientCredentials(
                    client_id=self.client_id, client_secret=self.client_secret
                )
                self._sp_client = spotipy.Spotify(auth_manager=auth_manager)
            except Exception as e:
                logger.warning(f"Could not initialize Spotipy client: {e}")

    def _http_get(self, url: str, headers: Optional[dict] = None, timeout: int = 15) -> requests.Response:
        hdrs = headers or HTTP_HEADERS
        return requests.get(url, headers=hdrs, timeout=timeout)

    def fetch(self, url_or_uri: str) -> Optional[PlaylistMetadata]:
        """
        Main entry point: fetches metadata for playlist, album, or track.
        """
        entity_type, entity_id = parse_spotify_url(url_or_uri)
        if not entity_type or not entity_id:
            raise ValueError("Geçersiz Spotify bağlantısı! Lütfen geçerli bir Spotify URL veya URI girin.")

        if self._sp_client:
            try:
                if entity_type == "playlist":
                    return self._fetch_playlist_api(entity_id)
                elif entity_type == "album":
                    return self._fetch_album_api(entity_id)
                elif entity_type == "track":
                    return self._fetch_track_api(entity_id)
            except Exception as e:
                logger.warning(f"Spotify API request failed, falling back to public scraper: {e}")

        # Try Spotapi / Public scraper first (handles full 100+ playlists!)
        try:
            if entity_type == "playlist":
                try:
                    return self._fetch_playlist_spotapi(entity_id)
                except Exception as e:
                    logger.warning(f"Spotapi fetch failed ({e}), falling back to embed scraper.")
                    return self._fetch_playlist_embed(entity_id)
            elif entity_type == "album":
                return self._fetch_album_embed(entity_id)
            elif entity_type == "track":
                return self._fetch_track_embed(entity_id)
        except requests.exceptions.HTTPError as e:
            if e.response is not None and e.response.status_code == 404:
                logger.warning(f"Spotify kaynağı bulunamadı veya gizli (404): {url_or_uri}")
            else:
                logger.warning(f"Spotify HTTP hatası: {e}")
            return None
        except requests.exceptions.RequestException as e:
            logger.warning(f"Spotify ağ isteği hatası: {e}")
            return None
        except Exception as e:
            logger.error(f"Spotify meta veri ayrıştırma hatası: {e}", exc_info=True)
            return None

        return None

    def _fetch_playlist_spotapi(self, playlist_id: str) -> PlaylistMetadata:
        """Fetch complete playlist (all 100+ tracks) using spotapi."""
        try:
            import spotapi
        except (ImportError, ModuleNotFoundError) as e:
            logger.warning(f"Spotapi modülü bulunamadı ({e}), embed kazıyıcıya geçiliyor.")
            return self._fetch_playlist_embed(playlist_id)

        # Get header info from embed first (for high-res cover, title, owner)
        title = "Spotify Çalma Listesi"
        owner = "Spotify"
        description = ""
        cover_url = None

        try:
            embed_url = f"https://open.spotify.com/embed/playlist/{playlist_id}"
            resp = self._http_get(embed_url, timeout=8)
            if resp.status_code == 200:
                match = re.search(r"<script id=\"__NEXT_DATA__\"[^>]*>(.*?)</script>", resp.text)
                if match:
                    data = json.loads(match.group(1)) or {}
                    props = data.get("props") or {}
                    page_props = props.get("pageProps") or {}
                    state = page_props.get("state") or {}
                    state_data = state.get("data") or {}
                    entity = state_data.get("entity") or {}

                    title = entity.get("title") or entity.get("name") or title
                    owner_info = entity.get("owner") or {}
                    owner = entity.get("subtitle") or owner_info.get("name") or owner
                    description = entity.get("description") or ""
                    cover_art = entity.get("coverArt") or {}
                    cover_sources = cover_art.get("sources") or []
                    if cover_sources and isinstance(cover_sources, list) and cover_sources[0]:
                        cover_url = cover_sources[0].get("url")
                    else:
                        vis = entity.get("visualIdentity") or {}
                        images = vis.get("image") or []
                        if images and isinstance(images, list) and images[0]:
                            cover_url = images[0].get("url")
        except Exception as e:
            logger.debug(f"Could not get embed header: {e}")

        try:
            public_api = spotapi.Public()
            tracks: List[SongMetadata] = []
            raw_pages = list(public_api.playlist_info(playlist_id))
        except Exception as e:
            logger.warning(f"Spotapi playlist_info başarısız: {e}")
            return self._fetch_playlist_embed(playlist_id)

        for page in raw_pages:
            items = (page or {}).get("items") or []
            for it in items:
                data_v2 = ((it or {}).get("itemV2") or {}).get("data") or {}
                if not data_v2:
                    continue
                t_title = data_v2.get("name") or "Bilinmeyen Parça"
                artists_data = data_v2.get("artists") or {}
                artists_items = artists_data.get("items") or []
                t_artist = ", ".join([
                    (a.get("profile") or {}).get("name", "")
                    for a in artists_items
                    if isinstance(a, dict) and (a.get("profile") or {}).get("name")
                ]) or owner
                album_info = data_v2.get("albumOfTrack") or {}
                album_name = album_info.get("name") or title
                duration_info = data_v2.get("trackDuration") or {}
                duration_ms = duration_info.get("totalMilliseconds") or 0
                cover_art = album_info.get("coverArt") or {}
                cover_sources = cover_art.get("sources") or []
                t_cover = cover_sources[-1].get("url") if (cover_sources and isinstance(cover_sources[-1], dict)) else cover_url
                uri = data_v2.get("uri") or ""
                t_id = uri.split(":")[-1] if uri else f"track_{len(tracks)+1}"
                date_info = album_info.get("date") or {}
                iso_str = date_info.get("isoString") or ""
                year = iso_str[:4] if iso_str and len(iso_str) >= 4 else None

                track_idx = len(tracks) + 1
                song = SongMetadata(
                    id=t_id,
                    title=t_title,
                    artist=t_artist,
                    album=album_name,
                    year=year,
                    track_number=track_idx,
                    duration_ms=duration_ms,
                    duration_formatted=format_duration(duration_ms),
                    cover_url=t_cover,
                    preview_url=None,
                    spotify_url=f"https://open.spotify.com/track/{t_id}",
                )
                tracks.append(song)

        if not tracks:
            # If spotapi yielded 0 tracks, fallback to embed
            return self._fetch_playlist_embed(playlist_id)

        # Update total tracks count on each song
        total_count = len(tracks)
        for t in tracks:
            t.total_tracks = total_count

        batches = _create_batches(tracks, batch_size=100)

        return PlaylistMetadata(
            id=playlist_id,
            title=title,
            description=description,
            owner=owner,
            cover_url=cover_url,
            total_tracks=total_count,
            type="playlist",
            tracks=tracks,
            batches=batches,
        )

    def _fetch_playlist_embed(self, playlist_id: str) -> PlaylistMetadata:
        embed_url = f"https://open.spotify.com/embed/playlist/{playlist_id}"
        resp = self._http_get(embed_url, timeout=15)
        resp.raise_for_status()

        match = re.search(r"<script id=\"__NEXT_DATA__\"[^>]*>(.*?)</script>", resp.text)
        if not match:
            raise ValueError("Spotify çalma listesi verisi ayrıştırılamadı.")

        data = json.loads(match.group(1)) or {}
        props = data.get("props") or {}
        page_props = props.get("pageProps") or {}
        state = page_props.get("state") or {}
        state_data = state.get("data") or {}
        entity = state_data.get("entity") or {}

        title = entity.get("title") or entity.get("name") or "Spotify Çalma Listesi"
        owner_info = entity.get("owner") or {}
        owner = entity.get("subtitle") or owner_info.get("name") or "Spotify"
        description = entity.get("description") or ""

        # Cover art
        cover_url = None
        cover_art = entity.get("coverArt") or {}
        cover_sources = cover_art.get("sources") or []
        if cover_sources and isinstance(cover_sources, list) and cover_sources[0]:
            cover_url = cover_sources[0].get("url")
        else:
            vis = entity.get("visualIdentity") or {}
            images = vis.get("image") or []
            if images and isinstance(images, list) and images[0]:
                cover_url = images[0].get("url")

        raw_tracks = entity.get("trackList") or []
        tracks: List[SongMetadata] = []

        for idx, t in enumerate(raw_tracks, start=1):
            if not isinstance(t, dict):
                continue
            t_uri = t.get("uri") or ""
            t_id = t_uri.split(":")[-1] if t_uri else f"track_{idx}"
            t_title = t.get("title") or "Bilinmeyen Parça"
            t_artist = t.get("subtitle") or owner
            t_duration = t.get("duration") or 0
            audio_preview = t.get("audioPreview") or {}
            t_preview = audio_preview.get("url")

            song = SongMetadata(
                id=t_id,
                title=t_title,
                artist=t_artist,
                album=title,
                year=None,
                track_number=idx,
                total_tracks=len(raw_tracks),
                duration_ms=t_duration,
                duration_formatted=format_duration(t_duration),
                cover_url=cover_url,
                preview_url=t_preview,
                spotify_url=f"https://open.spotify.com/track/{t_id}" if t_id else "",
            )
            tracks.append(song)

        batches = _create_batches(tracks, batch_size=100)

        return PlaylistMetadata(
            id=playlist_id,
            title=title,
            description=description,
            owner=owner,
            cover_url=cover_url,
            total_tracks=len(tracks),
            type="playlist",
            tracks=tracks,
            batches=batches,
        )

    def _fetch_album_embed(self, album_id: str) -> PlaylistMetadata:
        embed_url = f"https://open.spotify.com/embed/album/{album_id}"
        resp = self._http_get(embed_url, timeout=15)
        resp.raise_for_status()

        match = re.search(r"<script id=\"__NEXT_DATA__\"[^>]*>(.*?)</script>", resp.text)
        if not match:
            raise ValueError("Spotify albüm verisi ayrıştırılamadı.")

        data = json.loads(match.group(1)) or {}
        props = data.get("props") or {}
        page_props = props.get("pageProps") or {}
        state = page_props.get("state") or {}
        state_data = state.get("data") or {}
        entity = state_data.get("entity") or {}

        title = entity.get("title") or entity.get("name") or "Spotify Albümü"
        artists_list = entity.get("artists") or entity.get("authors") or []
        album_artist = ", ".join([a.get("name", "") for a in artists_list if isinstance(a, dict) and a.get("name")])
        if not album_artist:
            album_artist = entity.get("subtitle") or "Bilinmeyen Sanatçı"

        release_date = entity.get("releaseDate")
        year = None
        if isinstance(release_date, dict):
            iso_str = release_date.get("isoString") or ""
            if iso_str and len(iso_str) >= 4:
                year = iso_str[:4]
        elif isinstance(release_date, str) and len(release_date) >= 4:
            year = release_date[:4]

        # Cover art
        cover_url = None
        cover_art = entity.get("coverArt") or {}
        cover_sources = cover_art.get("sources") or []
        if cover_sources and isinstance(cover_sources, list) and cover_sources[0]:
            cover_url = cover_sources[0].get("url")
        else:
            vis = entity.get("visualIdentity") or {}
            images = vis.get("image") or []
            if images and isinstance(images, list) and images[0]:
                cover_url = images[0].get("url")

        raw_tracks = entity.get("trackList") or []
        tracks: List[SongMetadata] = []

        for idx, t in enumerate(raw_tracks, start=1):
            if not isinstance(t, dict):
                continue
            t_uri = t.get("uri") or ""
            t_id = t_uri.split(":")[-1] if t_uri else f"track_{idx}"
            t_title = t.get("title") or "Bilinmeyen Parça"
            t_artist = t.get("subtitle") or album_artist
            t_duration = t.get("duration") or 0
            audio_preview = t.get("audioPreview") or {}
            t_preview = audio_preview.get("url")

            song = SongMetadata(
                id=t_id,
                title=t_title,
                artist=t_artist,
                album=title,
                year=year,
                track_number=idx,
                total_tracks=len(raw_tracks),
                duration_ms=t_duration,
                duration_formatted=format_duration(t_duration),
                cover_url=cover_url,
                preview_url=t_preview,
                spotify_url=f"https://open.spotify.com/track/{t_id}" if t_id else "",
            )
            tracks.append(song)

        batches = _create_batches(tracks, batch_size=100)

        return PlaylistMetadata(
            id=album_id,
            title=title,
            description=f"Album by {album_artist}",
            owner=album_artist,
            cover_url=cover_url,
            total_tracks=len(tracks),
            type="album",
            tracks=tracks,
            batches=batches,
        )

    def _fetch_track_embed(self, track_id: str) -> PlaylistMetadata:
        embed_url = f"https://open.spotify.com/embed/track/{track_id}"
        resp = self._http_get(embed_url, timeout=15)
        resp.raise_for_status()

        match = re.search(r"<script id=\"__NEXT_DATA__\"[^>]*>(.*?)</script>", resp.text)
        if not match:
            raise ValueError("Spotify parça verisi ayrıştırılamadı.")

        data = json.loads(match.group(1)) or {}
        props = data.get("props") or {}
        page_props = props.get("pageProps") or {}
        state = page_props.get("state") or {}
        state_data = state.get("data") or {}
        entity = state_data.get("entity") or {}

        title = entity.get("title") or entity.get("name") or "Spotify Parçası"
        artists_list = entity.get("artists") or entity.get("authors") or []
        artist = ", ".join([a.get("name", "") for a in artists_list if isinstance(a, dict) and a.get("name")])
        if not artist:
            artist = entity.get("subtitle") or "Bilinmeyen Sanatçı"

        duration_ms = entity.get("duration") or 0
        audio_preview = entity.get("audioPreview") or {}
        preview_url = audio_preview.get("url")

        # Year
        release_date = entity.get("releaseDate")
        year = None
        if isinstance(release_date, dict):
            iso_str = release_date.get("isoString") or ""
            if iso_str and len(iso_str) >= 4:
                year = iso_str[:4]
        elif isinstance(release_date, str) and len(release_date) >= 4:
            year = release_date[:4]

        # Cover
        cover_url = None
        vis = entity.get("visualIdentity") or {}
        images = vis.get("image") or []
        if images and isinstance(images, list) and len(images) > 0:
            cover_url = (images[-1] or {}).get("url") or (images[0] or {}).get("url")
        else:
            cover_art = entity.get("coverArt") or {}
            sources = cover_art.get("sources") or []
            if sources and isinstance(sources, list) and len(sources) > 0:
                cover_url = (sources[0] or {}).get("url")

        if not cover_url:
            try:
                oemb_resp = self._http_get(
                    f"https://open.spotify.com/oembed?url=https://open.spotify.com/track/{track_id}",
                    timeout=5,
                )
                if oemb_resp.status_code == 200:
                    oemb_data = oemb_resp.json() or {}
                    cover_url = oemb_data.get("thumbnail_url")
            except Exception:
                pass

        song = SongMetadata(
            id=track_id,
            title=title,
            artist=artist,
            album=title,
            year=year,
            track_number=1,
            total_tracks=1,
            duration_ms=duration_ms,
            duration_formatted=format_duration(duration_ms),
            cover_url=cover_url,
            preview_url=preview_url,
            spotify_url=f"https://open.spotify.com/track/{track_id}",
            batch_index=1,
        )

        batches = _create_batches([song], batch_size=100)

        return PlaylistMetadata(
            id=track_id,
            title=title,
            description=f"Track by {artist}",
            owner=artist,
            cover_url=cover_url,
            total_tracks=1,
            type="track",
            tracks=[song],
            batches=batches,
        )

    def _fetch_playlist_api(self, playlist_id: str) -> PlaylistMetadata:
        sp = self._sp_client
        pl = sp.playlist(playlist_id) or {}
        title = pl.get("name") or "Spotify Playlist"
        description = pl.get("description") or ""
        owner_obj = pl.get("owner") or {}
        owner = owner_obj.get("display_name") or "Spotify"
        images = pl.get("images") or []
        cover_url = images[0].get("url") if images and isinstance(images[0], dict) else None

        tracks: List[SongMetadata] = []
        results = pl.get("tracks") or {}
        track_items = results.get("items") or []

        while results.get("next"):
            results = sp.next(results) or {}
            track_items.extend(results.get("items") or [])

        total_count = len(track_items)
        for idx, item in enumerate(track_items, start=1):
            t = (item or {}).get("track")
            if not t or not isinstance(t, dict):
                continue
            t_id = t.get("id") or f"track_{idx}"
            t_title = t.get("name") or "Unknown Track"
            artists_list = t.get("artists") or []
            t_artists = ", ".join([a.get("name", "") for a in artists_list if isinstance(a, dict) and a.get("name")])
            album_info = t.get("album") or {}
            album_name = album_info.get("name") or title
            album_images = album_info.get("images") or []
            t_cover = album_images[0].get("url") if album_images and isinstance(album_images[0], dict) else cover_url
            release_date = album_info.get("release_date") or ""
            year = release_date[:4] if release_date else None
            duration_ms = t.get("duration_ms") or 0
            preview_url = t.get("preview_url")
            ext_urls = t.get("external_urls") or {}
            spotify_url = ext_urls.get("spotify") or f"https://open.spotify.com/track/{t_id}"

            tracks.append(
                SongMetadata(
                    id=t_id,
                    title=t_title,
                    artist=t_artists,
                    album=album_name,
                    year=year,
                    track_number=idx,
                    total_tracks=total_count,
                    duration_ms=duration_ms,
                    duration_formatted=format_duration(duration_ms),
                    cover_url=t_cover,
                    preview_url=preview_url,
                    spotify_url=spotify_url,
                )
            )

        batches = _create_batches(tracks, batch_size=100)

        return PlaylistMetadata(
            id=playlist_id,
            title=title,
            description=description,
            owner=owner,
            cover_url=cover_url,
            total_tracks=len(tracks),
            type="playlist",
            tracks=tracks,
            batches=batches,
        )

    def _fetch_album_api(self, album_id: str) -> PlaylistMetadata:
        sp = self._sp_client
        alb = sp.album(album_id) or {}
        title = alb.get("name") or "Spotify Album"
        artists_list = alb.get("artists") or []
        artists = ", ".join([a.get("name", "") for a in artists_list if isinstance(a, dict) and a.get("name")])
        images = alb.get("images") or []
        cover_url = images[0].get("url") if images and isinstance(images[0], dict) else None
        release_date = alb.get("release_date") or ""
        year = release_date[:4] if release_date else None

        tracks: List[SongMetadata] = []
        track_dict = alb.get("tracks") or {}
        track_items = track_dict.get("items") or []
        total_count = len(track_items)
        for idx, t in enumerate(track_items, start=1):
            if not isinstance(t, dict):
                continue
            t_id = t.get("id") or f"track_{idx}"
            t_title = t.get("name") or "Unknown Track"
            t_artists_list = t.get("artists") or []
            t_artists = ", ".join([a.get("name", "") for a in t_artists_list if isinstance(a, dict) and a.get("name")]) or artists
            duration_ms = t.get("duration_ms") or 0
            ext_urls = t.get("external_urls") or {}
            spotify_url = ext_urls.get("spotify") or f"https://open.spotify.com/track/{t_id}"

            tracks.append(
                SongMetadata(
                    id=t_id,
                    title=t_title,
                    artist=t_artists,
                    album=title,
                    year=year,
                    track_number=idx,
                    total_tracks=total_count,
                    duration_ms=duration_ms,
                    duration_formatted=format_duration(duration_ms),
                    cover_url=cover_url,
                    preview_url=t.get("preview_url"),
                    spotify_url=spotify_url,
                )
            )

        batches = _create_batches(tracks, batch_size=100)

        return PlaylistMetadata(
            id=album_id,
            title=title,
            description=f"Album by {artists}",
            owner=artists,
            cover_url=cover_url,
            total_tracks=len(tracks),
            type="album",
            tracks=tracks,
            batches=batches,
        )

    def _fetch_track_api(self, track_id: str) -> PlaylistMetadata:
        sp = self._sp_client
        t = sp.track(track_id) or {}
        title = t.get("name") or "Unknown Track"
        artists_list = t.get("artists") or []
        artists = ", ".join([a.get("name", "") for a in artists_list if isinstance(a, dict) and a.get("name")])
        album_info = t.get("album") or {}
        album_name = album_info.get("name") or title
        album_images = album_info.get("images") or []
        cover_url = album_images[0].get("url") if album_images and isinstance(album_images[0], dict) else None
        release_date = album_info.get("release_date") or ""
        year = release_date[:4] if release_date else None
        duration_ms = t.get("duration_ms") or 0
        ext_urls = t.get("external_urls") or {}
        spotify_url = ext_urls.get("spotify") or f"https://open.spotify.com/track/{track_id}"

        song = SongMetadata(
            id=track_id,
            title=title,
            artist=artists,
            album=album_name,
            year=year,
            track_number=1,
            total_tracks=1,
            duration_ms=duration_ms,
            duration_formatted=format_duration(duration_ms),
            cover_url=cover_url,
            preview_url=t.get("preview_url"),
            spotify_url=spotify_url,
            batch_index=1,
        )

        batches = _create_batches([song], batch_size=100)

        return PlaylistMetadata(
            id=track_id,
            title=title,
            description=f"Track by {artists}",
            owner=artists,
            cover_url=cover_url,
            total_tracks=1,
            type="track",
            tracks=[song],
            batches=batches,
        )
