"""Check playlist audio links and repair moved files from their album pages."""

from __future__ import annotations

import argparse
import difflib
import json
import re
import sys
import time
import unicodedata
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from urllib.parse import unquote, urlparse

from bs4 import BeautifulSoup
from curl_cffi import requests


PLAYLIST_DIR = Path("playlists")
ALBUM_BASE = "https://downloads.khinsider.com/game-soundtracks/album/"
GOOD_STATUSES = {200, 206}
RETRY_STATUSES = {403, 429, 500, 502, 503, 504}
IMPERSONATIONS = ("chrome", "safari", "firefox")


def fetch(
    url: str,
    *,
    method: str = "GET",
    stream: bool = False,
    byte_range: str | None = None,
):
    last_response = None
    for attempt, impersonation in enumerate(IMPERSONATIONS):
        response = requests.request(
            method,
            url,
            impersonate=impersonation,
            allow_redirects=True,
            timeout=30,
            stream=stream,
            headers={"Range": byte_range} if byte_range else None,
        )
        last_response = response
        if response.status_code not in RETRY_STATUSES:
            return response
        response.close()
        time.sleep(2 ** attempt)
    return last_response


def url_works(url: str) -> bool:
    """Verify that a URL returns MP3 bytes, not merely an HTTP 200 page."""
    if not url:
        return False

    try:
        response = fetch(url, stream=True, byte_range="bytes=0-4095")
        if response.status_code not in GOOD_STATUSES:
            response.close()
            return False
        first_bytes = next(response.iter_content(chunk_size=4096), b"")
        content_type = response.headers.get("content-type", "").casefold()
        response.close()
        has_id3 = first_bytes.startswith(b"ID3")
        has_mp3_frame = any(
            first_bytes[index] == 0xFF and first_bytes[index + 1] & 0xE0 == 0xE0
            for index in range(max(0, len(first_bytes) - 1))
        )
        looks_like_html = first_bytes.lstrip().lower().startswith((b"<!doctype", b"<html"))
        return not looks_like_html and (
            has_id3 or has_mp3_frame or ("audio/" in content_type and bool(first_bytes))
        )
    except Exception:
        return False


def album_url_from_playlist(data: dict) -> str | None:
    configured = data.get("meta", {}).get("source")
    if configured:
        return configured

    for song in data.get("songs", []):
        source = song.get("src", "")
        match = re.search(r"/soundtracks/([^/]+)/", source)
        if match:
            return ALBUM_BASE + match.group(1)
    return None


def normalized_title(value: str) -> str:
    value = unicodedata.normalize("NFKC", unquote(value)).casefold()
    value = value.replace("’", "'").replace("`", "'")
    return re.sub(r"[^\w]+", " ", value).strip()


def album_song_pages(album_url: str) -> list[tuple[str, str]]:
    response = fetch(album_url)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, "html.parser")
    table = soup.find("table", id="songlist")
    if table is None:
        raise RuntimeError("album page did not contain the song list")

    result = []
    for link in table.find_all("a", href=True):
        href = link["href"]
        if "/game-soundtracks/album/" not in href:
            continue
        if href.startswith("/"):
            href = "https://downloads.khinsider.com" + href
        result.append((link.get_text(strip=True), href))
    return result


def comparable_title(value: str) -> str:
    """Normalize common source-site renames without changing song meaning."""
    value = normalized_title(value)
    value = re.sub(r"\blightning\b", "hit by lightning", value)
    value = re.sub(r"\btime trials?\b", "ta vs", value)
    value = re.sub(r"\brace\b", "gp", value)
    value = re.sub(r"\s+", " ", value).strip()
    common_renames = {
        "title screen": "main theme",
        "main menu": "menu",
        "super star": "star invincibility",
        "course intro fanfare gp": "course fanfare gp",
        "course intro fanfare battle": "course fanfare battle",
        "bowser s castle luigi s mansion": "bowser s castle",
        "1st place results": "goal 1st",
        "2nd 4th place results": "goal 2nd 4th",
        "5th 8th place results": "goal 5th 8th",
        "losing results": "no trophy for you",
        "award ceremony": "you got a trophy",
        "battle results": "battle end",
        "staff credits": "staff roll",
        "staff credits 2": "staff roll pal50",
    }
    return common_renames.get(value, value)


def direct_mp3(song_page_url: str) -> str | None:
    response = fetch(song_page_url)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, "html.parser")
    for link in soup.find_all("a", href=True):
        href = link["href"]
        if urlparse(href).path.casefold().endswith(".mp3"):
            return href
    return None


def find_song_page(title: str, song_pages: list[tuple[str, str]]) -> str | None:
    wanted = comparable_title(title)
    unique_pages = list(dict.fromkeys(song_pages))
    exact = [url for candidate, url in unique_pages if comparable_title(candidate) == wanted]
    if len(exact) == 1:
        return exact[0]

    scored = sorted(
        (
            difflib.SequenceMatcher(None, wanted, comparable_title(candidate)).ratio(),
            url,
        )
        for candidate, url in unique_pages
    )
    if not scored:
        return None
    best_score, best_url = scored[-1]
    second_score = scored[-2][0] if len(scored) > 1 else 0
    if best_score >= 0.88 and best_score - second_score >= 0.04:
        return best_url
    return None


def repair_playlist(path: Path, bad_indexes: list[int], *, dry_run: bool) -> int:
    data = json.loads(path.read_text(encoding="utf-8-sig"))
    album_url = album_url_from_playlist(data)
    if not album_url:
        print(f"  SKIP {path}: no album source could be determined")
        return 0

    try:
        pages = album_song_pages(album_url)
    except Exception as error:
        print(f"  SKIP {path}: could not read {album_url}: {error}")
        return 0

    replacements: dict[int, str] = {}
    for index in bad_indexes:
        song = data["songs"][index]
        page = find_song_page(song.get("title", ""), pages)
        if not page:
            print(f"  UNMATCHED {path}: {song.get('title', '(untitled)')}")
            continue

        try:
            replacement = direct_mp3(page)
        except Exception as error:
            print(f"  ERROR {path}: {song.get('title')}: {error}")
            continue

        old_url = song.get("src", "")
        if replacement and replacement != old_url and url_works(replacement):
            replacements[index] = replacement
            print(f"  REPAIRED {path}: {song.get('title')}")
        else:
            print(f"  NO REPLACEMENT {path}: {song.get('title')}")
        time.sleep(0.25)

    if replacements and not dry_run:
        for index, replacement in replacements.items():
            data["songs"][index]["src"] = replacement
        data.setdefault("meta", {}).setdefault("source", album_url)
        path.write_text(
            json.dumps(data, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
    return len(replacements)


def load_playlists(selected: str | None) -> list[tuple[Path, dict]]:
    paths = [Path(selected)] if selected else sorted(PLAYLIST_DIR.rglob("*.json"))
    loaded = []
    for path in paths:
        try:
            data = json.loads(path.read_text(encoding="utf-8-sig"))
        except Exception as error:
            print(f"INVALID JSON {path}: {error}")
            continue
        if any(song.get("src") for song in data.get("songs", [])):
            loaded.append((path, data))
    return loaded


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--playlist", help="check only one playlist JSON file")
    parser.add_argument("--workers", type=int, default=16)
    args = parser.parse_args()

    playlists = load_playlists(args.playlist)
    checks: list[tuple[Path, int, str]] = []
    for path, data in playlists:
        checks.extend(
            (path, index, song.get("src", ""))
            for index, song in enumerate(data.get("songs", []))
            if song.get("src")
        )

    print(f"Checking {len(checks)} audio links in {len(playlists)} playlists...")
    failures: dict[Path, list[int]] = {}
    with ThreadPoolExecutor(max_workers=max(1, args.workers)) as executor:
        futures = {
            executor.submit(url_works, url): (path, index)
            for path, index, url in checks
        }
        for future in as_completed(futures):
            path, index = futures[future]
            if not future.result():
                failures.setdefault(path, []).append(index)

    failed_count = sum(map(len, failures.values()))
    if checks and failed_count / len(checks) > 0.35:
        print(
            f"Safety stop: {failed_count}/{len(checks)} links appeared unavailable. "
            "This probably means the host blocked the checker; no files were changed."
        )
        return 1

    print(f"Found {failed_count} unavailable links in {len(failures)} playlists.")
    repaired = 0
    for path, indexes in sorted(failures.items()):
        repaired += repair_playlist(path, sorted(indexes), dry_run=args.dry_run)

    print(f"{'Would repair' if args.dry_run else 'Repaired'} {repaired} links.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
