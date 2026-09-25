from curl_cffi import requests
from bs4 import BeautifulSoup
import time
import json

def get_album_data(album_url):
    base_url = "https://downloads.khinsider.com"
    
    # 1. Use curl_cffi with browser impersonation to spoof Chrome's TLS fingerprint
    try:
        response = requests.get(album_url, impersonate="chrome")
        print(f"Status Code: {response.status_code}") # Should print 200 now!
        response.raise_for_status()
    except Exception as e:
        print(f"Failed to connect to page: {e}")
        return None

    # 2. Parse the HTML AFTER getting a successful response
    soup = BeautifulSoup(response.text, 'html.parser')
    print(f"Page Title: {soup.title.text.strip() if soup.title else 'No Title'}")

    # Check if Cloudflare still caught us
    if response.status_code == 403 or "Cloudflare" in soup.text or "Just a moment..." in soup.text:
        print("Error: Still being blocked by Cloudflare.")
        return None

    # 3. Extract Meta Data
    game_title = soup.find('h2').text.strip() if soup.find('h2') else "Unknown"

    # art_div = soup.find('div', class_='albumart')
    # art = art_div.find('img')['src'] if art_div and art_div.find('img') else ""

    # desc_p = soup.find('p', align='left')
    # desc = desc_p.get_text(separator=' ', strip=True) if desc_p else ""

    # 4. Extract Song List
    table = soup.find('table', {'id': 'songlist'})
    if not table:
        print("Error: Could not find table with id 'songlist'.")
        return None
        
    songs = []
    rows = table.find_all('tr')[1:]

    for row in rows:
        song_link_tag = row.find('a', href=True)
        
        if song_link_tag and '/game-soundtracks/album/' in song_link_tag['href']:
            title = song_link_tag.text.strip()
            song_page_url = base_url + song_link_tag['href']
            
            print(f"Processing: {title}")
            mp3_src = fetch_direct_mp3(song_page_url)
            
            if mp3_src:
                songs.append({"title": title, "src": mp3_src})
            
            time.sleep(1) # Polite delay
            
    return {
        "meta": {
            "game_title": game_title,
            # "art": art,
            # "desc": desc
        },
        "songs": songs
    }

def fetch_direct_mp3(song_page_url):
    try:
        # Also use impersonate="chrome" for fetching the individual song pages
        response = requests.get(song_page_url, impersonate="chrome")
        response.raise_for_status()
        song_soup = BeautifulSoup(response.text, 'html.parser')

        for a in song_soup.find_all('a', href=True):
            if a['href'].endswith('.mp3'):
                return a['href']
    except Exception as e:
        print(f"Failed to fetch {song_page_url}: {e}")
    return None

# Execution
if __name__ == "__main__":
    album_url = input("Input URL: ")
    data = get_album_data(album_url)
    if data:
        with open("album_data.json", "w", encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        print(f"Done! Saved {len(data['songs'])} songs to album_data.json")