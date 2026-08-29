"""
Spotify URL Parser and Metadata Fetcher for MP3fy
Supports Playlists, Albums, and Tracks without requiring Spotify API keys (with optional API key support).
"""

import re
import json
import logging
from dataclasses import dataclass, field, asdict
from typing import List, Optional, Tuple, Dict, Any
import requests

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

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "owner": self.owner,
            "cover_url": self.cover_url,
            "total_tracks": self.total_tracks,
            "type": self.type,
            "tracks": [t.to_dict() for t in self.tracks],
        }


def parse_spotify_url(url_or_uri: str) -> Tuple[Optional[str], Optional[str]]:
    """
    Parses a Spotify URL or URI and returns (type, id).
    Types: 'playlist', 'album', 'track'
    """
    if not url_or_uri:
        return None, None

    url_clean = url_or_uri.strip()

    # Spotify URI: spotify:track:4LfCY65LvojKjWEnU7fNN4
    uri_match = re.search(r"spotify:(playlist|album|track):([a-zA-Z0-9]+)", url_clean)
    if uri_match:
        return uri_match.group(1), uri_match.group(2)

    # Spotify Web URL: https://open.spotify.com/intl-tr/playlist/37i9dQZF1DXcBWIGoYBM5M?si=...
    url_match = re.search(
        r"spotify\.com/(?:intl-[a-z]+/)?(playlist|album|track)/([a-zA-Z0-9]+)",
        url_clean,
    )
    if url_match:
        return url_match.group(1), url_match.group(2)

    return None, None


def _format_duration(duration_ms: int) -> str:
    if not duration_ms or duration_ms <= 0:
        return "0:00"
    total_sec = duration_ms // 1000
    minutes = total_sec // 60
    seconds = total_sec % 60
    return f"{minutes}:{seconds:02d}"


class SpotifyFetcher:
    """
    Handles fetching Spotify metadata using Embed scraping or official Spotipy API.
    """

    def __init__(self, client_id: Optional[str] = None, client_secret: Optional[str] = None):
        self.client_id = client_id
        self.client_secret = client_secret
        self._sp_client = None

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
                logger.warning(f"Spotify API request failed, falling back to embed scraper: {e}")

        # Fallback to embed scraper (Zero config required!)
        if entity_type == "playlist":
            return self._fetch_playlist_embed(entity_id)
        elif entity_type == "album":
            return self._fetch_album_embed(entity_id)
        elif entity_type == "track":
            return self._fetch_track_embed(entity_id)

        return None

    def _fetch_playlist_embed(self, playlist_id: str) -> PlaylistMetadata:
        embed_url = f"https://open.spotify.com/embed/playlist/{playlist_id}"
        resp = requests.get(embed_url, headers=HTTP_HEADERS, timeout=15)
        resp.raise_for_status()

        match = re.search(r"<script id=\"__NEXT_DATA__\"[^>]*>(.*?)</script>", resp.text)
        if not match:
            raise ValueError("Spotify çalma listesi verisi ayrıştırılamadı.")

        data = json.loads(match.group(1))
        entity = (
            data.get("props", {})
            .get("pageProps", {})
            .get("state", {})
            .get("data", {})
            .get("entity", {})
        )

        title = entity.get("title") or entity.get("name") or "Spotify Çalma Listesi"
        owner = entity.get("subtitle") or entity.get("owner", {}).get("name") or "Spotify"
        description = entity.get("description") or ""

        # Cover art
        cover_url = None
        cover_sources = entity.get("coverArt", {}).get("sources", [])
        if cover_sources:
            cover_url = cover_sources[0].get("url")
        elif entity.get("visualIdentity", {}).get("image"):
            images = entity.get("visualIdentity", {}).get("image", [])
            if images:
                cover_url = images[0].get("url")

        raw_tracks = entity.get("trackList", [])
        tracks: List[SongMetadata] = []

        for idx, t in enumerate(raw_tracks, start=1):
            t_uri = t.get("uri", "")
            t_id = t_uri.split(":")[-1] if t_uri else f"track_{idx}"
            t_title = t.get("title") or "Bilinmeyen Parça"
            t_artist = t.get("subtitle") or owner
            t_duration = t.get("duration", 0)
            t_preview = t.get("audioPreview", {}).get("url")

            song = SongMetadata(
                id=t_id,
                title=t_title,
                artist=t_artist,
                album=title,
                year=None,
                track_number=idx,
                total_tracks=len(raw_tracks),
                duration_ms=t_duration,
                duration_formatted=_format_duration(t_duration),
                cover_url=cover_url,
                preview_url=t_preview,
                spotify_url=f"https://open.spotify.com/track/{t_id}" if t_id else "",
            )
            tracks.append(song)

        return PlaylistMetadata(
            id=playlist_id,
            title=title,
            description=description,
            owner=owner,
            cover_url=cover_url,
            total_tracks=len(tracks),
            type="playlist",
            tracks=tracks,
        )

    def _fetch_album_embed(self, album_id: str) -> PlaylistMetadata:
        embed_url = f"https://open.spotify.com/embed/album/{album_id}"
        resp = requests.get(embed_url, headers=HTTP_HEADERS, timeout=15)
        resp.raise_for_status()

        match = re.search(r"<script id=\"__NEXT_DATA__\"[^>]*>(.*?)</script>", resp.text)
        if not match:
            raise ValueError("Spotify albüm verisi ayrıştırılamadı.")

        data = json.loads(match.group(1))
        entity = (
            data.get("props", {})
            .get("pageProps", {})
            .get("state", {})
            .get("data", {})
            .get("entity", {})
        )

        title = entity.get("title") or entity.get("name") or "Spotify Albümü"
        artists_list = entity.get("artists") or entity.get("authors") or []
        album_artist = ", ".join([a.get("name", "") for a in artists_list if a.get("name")])
        if not album_artist:
            album_artist = entity.get("subtitle") or "Bilinmeyen Sanatçı"

        release_date = entity.get("releaseDate")
        year = None
        if isinstance(release_date, dict):
            iso_str = release_date.get("isoString", "")
            if iso_str and len(iso_str) >= 4:
                year = iso_str[:4]
        elif isinstance(release_date, str) and len(release_date) >= 4:
            year = release_date[:4]

        # Cover art
        cover_url = None
        cover_sources = entity.get("coverArt", {}).get("sources", [])
        if cover_sources:
            cover_url = cover_sources[0].get("url")
        elif entity.get("visualIdentity", {}).get("image"):
            images = entity.get("visualIdentity", {}).get("image", [])
            if images:
                cover_url = images[0].get("url")

        raw_tracks = entity.get("trackList", [])
        tracks: List[SongMetadata] = []

        for idx, t in enumerate(raw_tracks, start=1):
            t_uri = t.get("uri", "")
            t_id = t_uri.split(":")[-1] if t_uri else f"track_{idx}"
            t_title = t.get("title") or "Bilinmeyen Parça"
            t_artist = t.get("subtitle") or album_artist
            t_duration = t.get("duration", 0)
            t_preview = t.get("audioPreview", {}).get("url")

            song = SongMetadata(
                id=t_id,
                title=t_title,
                artist=t_artist,
                album=title,
                year=year,
                track_number=idx,
                total_tracks=len(raw_tracks),
                duration_ms=t_duration,
                duration_formatted=_format_duration(t_duration),
                cover_url=cover_url,
                preview_url=t_preview,
                spotify_url=f"https://open.spotify.com/track/{t_id}" if t_id else "",
            )
            tracks.append(song)

        return PlaylistMetadata(
            id=album_id,
            title=title,
            description=f"Album by {album_artist}",
            owner=album_artist,
            cover_url=cover_url,
            total_tracks=len(tracks),
            type="album",
            tracks=tracks,
        )

    def _fetch_track_embed(self, track_id: str) -> PlaylistMetadata:
        embed_url = f"https://open.spotify.com/embed/track/{track_id}"
        resp = requests.get(embed_url, headers=HTTP_HEADERS, timeout=15)
        resp.raise_for_status()

        match = re.search(r"<script id=\"__NEXT_DATA__\"[^>]*>(.*?)</script>", resp.text)
        if not match:
            raise ValueError("Spotify parça verisi ayrıştırılamadı.")

        data = json.loads(match.group(1))
        entity = (
            data.get("props", {})
            .get("pageProps", {})
            .get("state", {})
            .get("data", {})
            .get("entity", {})
        )

        title = entity.get("title") or entity.get("name") or "Spotify Parçası"
        artists_list = entity.get("artists") or entity.get("authors") or []
        artist = ", ".join([a.get("name", "") for a in artists_list if a.get("name")])
        if not artist:
            artist = entity.get("subtitle") or "Bilinmeyen Sanatçı"

        duration_ms = entity.get("duration", 0)
        preview_url = entity.get("audioPreview", {}).get("url")

        # Year
        release_date = entity.get("releaseDate")
        year = None
        if isinstance(release_date, dict):
            iso_str = release_date.get("isoString", "")
            if iso_str and len(iso_str) >= 4:
                year = iso_str[:4]
        elif isinstance(release_date, str) and len(release_date) >= 4:
            year = release_date[:4]

        # Cover
        cover_url = None
        images = entity.get("visualIdentity", {}).get("image", [])
        if images:
            # Sort by width or pick the largest
            cover_url = images[-1].get("url") or images[0].get("url")
        elif entity.get("coverArt", {}).get("sources"):
            cover_url = entity["coverArt"]["sources"][0].get("url")

        # Also fallback to oEmbed thumbnail if not found
        if not cover_url:
            try:
                oemb = requests.get(
                    f"https://open.spotify.com/oembed?url=https://open.spotify.com/track/{track_id}",
                    headers=HTTP_HEADERS,
                    timeout=5,
                ).json()
                cover_url = oemb.get("thumbnail_url")
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
            duration_formatted=_format_duration(duration_ms),
            cover_url=cover_url,
            preview_url=preview_url,
            spotify_url=f"https://open.spotify.com/track/{track_id}",
        )

        return PlaylistMetadata(
            id=track_id,
            title=title,
            description=f"Track by {artist}",
            owner=artist,
            cover_url=cover_url,
            total_tracks=1,
            type="track",
            tracks=[song],
        )

    def _fetch_playlist_api(self, playlist_id: str) -> PlaylistMetadata:
        sp = self._sp_client
        pl = sp.playlist(playlist_id)
        title = pl.get("name", "Spotify Playlist")
        description = pl.get("description", "")
        owner = pl.get("owner", {}).get("display_name", "Spotify")
        images = pl.get("images", [])
        cover_url = images[0]["url"] if images else None

        tracks: List[SongMetadata] = []
        results = pl.get("tracks", {})
        track_items = results.get("items", [])

        while results.get("next"):
            results = sp.next(results)
            track_items.extend(results.get("items", []))

        for idx, item in enumerate(track_items, start=1):
            t = item.get("track")
            if not t:
                continue
            t_id = t.get("id") or f"track_{idx}"
            t_title = t.get("name", "Unknown Track")
            t_artists = ", ".join([a["name"] for a in t.get("artists", []) if "name" in a])
            album_info = t.get("album", {})
            album_name = album_info.get("name", title)
            album_images = album_info.get("images", [])
            t_cover = album_images[0]["url"] if album_images else cover_url
            release_date = album_info.get("release_date", "")
            year = release_date[:4] if release_date else None
            duration_ms = t.get("duration_ms", 0)
            preview_url = t.get("preview_url")

            tracks.append(
                SongMetadata(
                    id=t_id,
                    title=t_title,
                    artist=t_artists,
                    album=album_name,
                    year=year,
                    track_number=idx,
                    total_tracks=len(track_items),
                    duration_ms=duration_ms,
                    duration_formatted=_format_duration(duration_ms),
                    cover_url=t_cover,
                    preview_url=preview_url,
                    spotify_url=t.get("external_urls", {}).get("spotify", f"https://open.spotify.com/track/{t_id}"),
                )
            )

        return PlaylistMetadata(
            id=playlist_id,
            title=title,
            description=description,
            owner=owner,
            cover_url=cover_url,
            total_tracks=len(tracks),
            type="playlist",
            tracks=tracks,
        )

    def _fetch_album_api(self, album_id: str) -> PlaylistMetadata:
        sp = self._sp_client
        alb = sp.album(album_id)
        title = alb.get("name", "Spotify Album")
        artists = ", ".join([a["name"] for a in alb.get("artists", [])])
        images = alb.get("images", [])
        cover_url = images[0]["url"] if images else None
        release_date = alb.get("release_date", "")
        year = release_date[:4] if release_date else None

        tracks: List[SongMetadata] = []
        track_items = alb.get("tracks", {}).get("items", [])
        for idx, t in enumerate(track_items, start=1):
            t_id = t.get("id") or f"track_{idx}"
            t_title = t.get("name", "Unknown Track")
            t_artists = ", ".join([a["name"] for a in t.get("artists", [])]) or artists
            duration_ms = t.get("duration_ms", 0)

            tracks.append(
                SongMetadata(
                    id=t_id,
                    title=t_title,
                    artist=t_artists,
                    album=title,
                    year=year,
                    track_number=idx,
                    total_tracks=len(track_items),
                    duration_ms=duration_ms,
                    duration_formatted=_format_duration(duration_ms),
                    cover_url=cover_url,
                    preview_url=t.get("preview_url"),
                    spotify_url=t.get("external_urls", {}).get("spotify", f"https://open.spotify.com/track/{t_id}"),
                )
            )

        return PlaylistMetadata(
            id=album_id,
            title=title,
            description=f"Album by {artists}",
            owner=artists,
            cover_url=cover_url,
            total_tracks=len(tracks),
            type="album",
            tracks=tracks,
        )

    def _fetch_track_api(self, track_id: str) -> PlaylistMetadata:
        sp = self._sp_client
        t = sp.track(track_id)
        title = t.get("name", "Unknown Track")
        artists = ", ".join([a["name"] for a in t.get("artists", [])])
        album_info = t.get("album", {})
        album_name = album_info.get("name", title)
        album_images = album_info.get("images", [])
        cover_url = album_images[0]["url"] if album_images else None
        release_date = album_info.get("release_date", "")
        year = release_date[:4] if release_date else None
        duration_ms = t.get("duration_ms", 0)

        song = SongMetadata(
            id=track_id,
            title=title,
            artist=artists,
            album=album_name,
            year=year,
            track_number=1,
            total_tracks=1,
            duration_ms=duration_ms,
            duration_formatted=_format_duration(duration_ms),
            cover_url=cover_url,
            preview_url=t.get("preview_url"),
            spotify_url=t.get("external_urls", {}).get("spotify", f"https://open.spotify.com/track/{track_id}"),
        )

        return PlaylistMetadata(
            id=track_id,
            title=title,
            description=f"Track by {artists}",
            owner=artists,
            cover_url=cover_url,
            total_tracks=1,
            type="track",
            tracks=[song],
        )
