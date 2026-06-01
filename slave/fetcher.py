"""SpotAPI-based metadata fetcher for slaves."""
import logging
from typing import Any, Tuple

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "SpotAPI"))
from spotapi import PublicAlbum, Artist, Song

from slave.client_pool import get_pool

logger = logging.getLogger(__name__)


class SlaveFetcher:
    def fetch_album(self, album_id: str) -> Tuple[dict, str | None]:
        pool = get_pool()
        for attempt in range(2):
            client = pool.get()
            try:
                album = PublicAlbum(album_id, client=client)
                data = album.get_album_info(limit=343)
                if not isinstance(data, dict):
                    logger.warning(f"fetch_album returned non-dict for {album_id}: {type(data)}, attempt {attempt + 1}")
                    pool.discard(client)
                    if attempt == 0:
                        continue
                    return {}, None
                artist_id = None
                try:
                    artist_data = data.get("data", {}).get("albumUnion", {}).get("artists", [])
                    if artist_data:
                        uri = artist_data[0].get("uri", "")
                        artist_id = uri.split(":")[-1] if uri else None
                except Exception:
                    pass
                pool.put(client)
                return data, artist_id
            except Exception as e:
                logger.warning(f"fetch_album error for {album_id}: {e}, attempt {attempt + 1}")
                pool.discard(client)
                if attempt == 0:
                    continue
                return {}, None
        return {}, None

    def fetch_artist(self, artist_id: str) -> dict:
        pool = get_pool()
        for attempt in range(2):
            client = pool.get()
            try:
                artist = Artist(client=client)
                data = artist.get_artist(artist_id)
                if not isinstance(data, dict):
                    logger.warning(f"fetch_artist returned non-dict for {artist_id}: {type(data)}, attempt {attempt + 1}")
                    pool.discard(client)
                    if attempt == 0:
                        continue
                    return {}
                pool.put(client)
                return data
            except Exception as e:
                logger.warning(f"fetch_artist error for {artist_id}: {e}, attempt {attempt + 1}")
                pool.discard(client)
                if attempt == 0:
                    continue
                return {}
        return {}

    def fetch_song(self, song_id: str) -> dict:
        pool = get_pool()
        for attempt in range(2):
            client = pool.get()
            try:
                song = Song(client=client)
                data = song.get_track_info(song_id)
                if not isinstance(data, dict):
                    logger.warning(f"fetch_song returned non-dict for {song_id}: {type(data)}, attempt {attempt + 1}")
                    pool.discard(client)
                    if attempt == 0:
                        continue
                    return {}
                pool.put(client)
                return data
            except Exception as e:
                logger.warning(f"fetch_song error for {song_id}: {e}, attempt {attempt + 1}")
                pool.discard(client)
                if attempt == 0:
                    continue
                return {}
        return {}

    
