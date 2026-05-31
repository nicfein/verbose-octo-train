"""SpotAPI-based metadata fetcher for slaves."""
import logging
from typing import Any, Tuple

from spotapi import PublicAlbum, Artist, Song

from slave.client_pool import get_pool

logger = logging.getLogger(__name__)


class SlaveFetcher:
    def fetch_album(self, album_id: str) -> Tuple[dict, str | None]:
        pool = get_pool()
        client = pool.get()
        try:
            album = PublicAlbum(album_id, client=client)
            data = album.get_album_info(limit=25)
            artist_id = None
            try:
                artist_data = data.get("data", {}).get("albumUnion", {}).get("artists", [])
                if artist_data:
                    uri = artist_data[0].get("uri", "")
                    artist_id = uri.split(":")[-1] if uri else None
            except Exception:
                pass
            return data, artist_id
        finally:
            pool.put(client)

    def fetch_artist(self, artist_id: str) -> dict:
        pool = get_pool()
        client = pool.get()
        try:
            artist = Artist(client=client)
            return artist.get_artist(artist_id)
        finally:
            pool.put(client)

    def fetch_song(self, song_id: str) -> dict:
        pool = get_pool()
        client = pool.get()
        try:
            song = Song(client=client)
            return song.get_track_info(song_id)
        finally:
            pool.put(client)
