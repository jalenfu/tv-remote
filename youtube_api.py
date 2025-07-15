from fastapi import APIRouter, Query, status, Request, Body
from fastapi.responses import JSONResponse, RedirectResponse
import os
import requests
from dotenv import load_dotenv
from concurrent.futures import ThreadPoolExecutor, as_completed
from selenium.webdriver.common.keys import Keys
import threading
import time
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.firefox.firefox_profile import FirefoxProfile
import isodate

# Load environment variables
load_dotenv()
YOUTUBE_CLIENT_ID = os.getenv('YOUTUBE_CLIENT_ID')
YOUTUBE_CLIENT_SECRET = os.getenv('YOUTUBE_CLIENT_SECRET')
YOUTUBE_REDIRECT_URI = os.getenv('YOUTUBE_REDIRECT_URI')

youtube_access_token = None
youtube_refresh_token = None
youtube_token_expiry = None

selenium_lock = threading.Lock()

def get_youtube_headers():
    return {
        'Authorization': f'Bearer {youtube_access_token}',
        'Accept': 'application/json',
    }

def get_selenium_driver():
    # Import from twitch_api to reuse the shared driver
    from twitch_api import get_selenium_driver as shared_get_selenium_driver, selenium_lock
    return shared_get_selenium_driver(), selenium_lock

def find_tab_by_url(driver, url_substring):
    for handle in driver.window_handles:
        driver.switch_to.window(handle)
        if url_substring in driver.current_url:
            return handle
    return None

def is_not_short(details):
    # Filter out videos shorter than 60 seconds
    duration_str = details.get('contentDetails', {}).get('duration')
    if duration_str:
        try:
            duration = isodate.parse_duration(duration_str).total_seconds()
            return duration >= 60
        except Exception:
            pass
    # If duration is missing or can't be parsed, include the video
    return True

youtube_router = APIRouter()

@youtube_router.get('/api/youtube/login')
def youtube_login():
    scope = 'https://www.googleapis.com/auth/youtube.readonly'
    oauth_url = (
        'https://accounts.google.com/o/oauth2/v2/auth?'
        f'client_id={YOUTUBE_CLIENT_ID}'
        f'&redirect_uri={YOUTUBE_REDIRECT_URI}'
        f'&response_type=code'
        f'&scope={scope}'
        f'&access_type=offline'
        f'&prompt=consent'
    )
    return RedirectResponse(oauth_url)

@youtube_router.get('/api/youtube/oauth/callback')
def youtube_oauth_callback(request: Request):
    global youtube_access_token, youtube_refresh_token, youtube_token_expiry
    code = request.query_params.get('code')
    if not code:
        return {'error': 'No code provided'}
    token_url = 'https://oauth2.googleapis.com/token'
    data = {
        'client_id': YOUTUBE_CLIENT_ID,
        'client_secret': YOUTUBE_CLIENT_SECRET,
        'code': code,
        'grant_type': 'authorization_code',
        'redirect_uri': YOUTUBE_REDIRECT_URI,
    }
    resp = requests.post(token_url, data=data)
    if resp.status_code != 200:
        return {'error': 'Failed to get token', 'details': resp.text}
    tokens = resp.json()
    youtube_access_token = tokens['access_token']
    youtube_refresh_token = tokens.get('refresh_token')
    youtube_token_expiry = tokens.get('expires_in')
    return RedirectResponse('/')

@youtube_router.get('/api/youtube/subscriptions')
def youtube_subscriptions():
    if not youtube_access_token:
        return JSONResponse({'error': 'Not authenticated with YouTube'}, status_code=401)
    url = 'https://www.googleapis.com/youtube/v3/subscriptions'
    params = {
        'part': 'snippet',
        'mine': 'true',
        'maxResults': 50
    }
    resp = requests.get(url, headers=get_youtube_headers(), params=params)
    if resp.status_code != 200:
        return JSONResponse({'error': 'Failed to fetch subscriptions', 'details': resp.text}, status_code=500)
    data = resp.json()
    channels = [
        {
            'channelId': item['snippet']['resourceId']['channelId'],
            'title': item['snippet']['title'],
            'thumbnail': item['snippet']['thumbnails']['default']['url']
        }
        for item in data.get('items', [])
    ]
    return {'channels': channels}

@youtube_router.get('/api/youtube/search')
def youtube_search(q: str):
    print(f"[YouTube Search] Starting search for: {q}")
    import time as _time
    start_time = _time.time()
    if not youtube_access_token:
        return JSONResponse({'error': 'Not authenticated with YouTube'}, status_code=401)
    url = 'https://www.googleapis.com/youtube/v3/search'
    params = {
        'part': 'snippet',
        'q': q,
        'type': 'video',
        'maxResults': 10
    }
    search_start = _time.time()
    resp = requests.get(url, headers=get_youtube_headers(), params=params)
    search_end = _time.time()
    print(f"[YouTube Search] Search API call took {search_end - search_start:.2f} seconds")
    if resp.status_code != 200:
        return JSONResponse({'error': 'Failed to search YouTube', 'details': resp.text}, status_code=500)
    data = resp.json()
    video_items = [
        item for item in data.get('items', [])
        if item.get('id', {}).get('videoId')
    ]
    video_ids = [item['id']['videoId'] for item in video_items]
    if not video_ids:
        print(f"[YouTube Search] No video IDs found. Total time: {_time.time() - start_time:.2f} seconds")
        return {'videos': []}

    # Batch fetch full video details
    videos_url = 'https://www.googleapis.com/youtube/v3/videos'
    videos_params = {
        'part': 'snippet,contentDetails,statistics',
        'id': ','.join(video_ids)
    }
    details_start = _time.time()
    videos_resp = requests.get(videos_url, headers=get_youtube_headers(), params=videos_params)
    details_end = _time.time()
    print(f"[YouTube Search] Video details API call took {details_end - details_start:.2f} seconds")
    if videos_resp.status_code != 200:
        return JSONResponse({'error': 'Failed to fetch video details', 'details': videos_resp.text}, status_code=500)
    videos_data = videos_resp.json()
    details_map = {item['id']: item for item in videos_data.get('items', [])}

    # Merge details and filter out Shorts by duration
    videos = []
    for item in video_items:
        vid = item['id']['videoId']
        details = details_map.get(vid)
        if not details:
            continue
        snippet = details['snippet']
        content_details = details['contentDetails']
        statistics = details.get('statistics', {})
        if not is_not_short(details):
            continue  # Skip Shorts
        thumbnails = snippet.get('thumbnails', {})
        videos.append({
            'videoId': vid,
            'title': snippet['title'],
            'channelTitle': snippet['channelTitle'],
            'thumbnail': thumbnails['default']['url'],
            'publishedAt': snippet['publishedAt'],
            'duration': content_details['duration'],
            'viewCount': statistics.get('viewCount'),
        })
    total_time = _time.time() - start_time
    print(f"[YouTube Search] Total endpoint time: {total_time:.2f} seconds")
    return {'videos': videos}

@youtube_router.get('/api/youtube/feed')
def youtube_feed():
    if not youtube_access_token:
        return JSONResponse({'error': 'Not authenticated with YouTube'}, status_code=401)
    subs_url = 'https://www.googleapis.com/youtube/v3/subscriptions'
    subs_params = {
        'part': 'snippet',
        'mine': 'true',
        'maxResults': 30
    }
    subs_resp = requests.get(subs_url, headers=get_youtube_headers(), params=subs_params)
    if subs_resp.status_code != 200:
        return JSONResponse({'error': 'Failed to fetch subscriptions', 'details': subs_resp.text}, status_code=500)
    subs_data = subs_resp.json()
    channels = [
        {
            'channelId': item['snippet']['resourceId']['channelId'],
            'title': item['snippet']['title'],
            'thumbnail': item['snippet']['thumbnails']['default']['url']
        }
        for item in subs_data.get('items', [])
    ]
    feed = []
    def fetch_channel_uploads(ch):
        try:
            ch_url = 'https://www.googleapis.com/youtube/v3/channels'
            ch_params = {
                'part': 'contentDetails',
                'id': ch['channelId']
            }
            ch_resp = requests.get(ch_url, headers=get_youtube_headers(), params=ch_params)
            if ch_resp.status_code != 200:
                return []
            ch_data = ch_resp.json()
            items = ch_data.get('items', [])
            if not items:
                return []
            uploads_playlist = items[0]['contentDetails']['relatedPlaylists']['uploads']
            pl_url = 'https://www.googleapis.com/youtube/v3/playlistItems'
            pl_params = {
                'part': 'snippet',
                'playlistId': uploads_playlist,
                'maxResults': 3
            }
            pl_resp = requests.get(pl_url, headers=get_youtube_headers(), params=pl_params)
            if pl_resp.status_code != 200:
                return []
            pl_data = pl_resp.json()
            vids = []
            video_ids = []
            snippet_map = {}
            for vid in pl_data.get('items', []):
                s = vid['snippet']
                video_id = s['resourceId']['videoId']
                video_ids.append(video_id)
                snippet_map[video_id] = s
            # Batch fetch details for these videos
            if not video_ids:
                return []
            videos_url = 'https://www.googleapis.com/youtube/v3/videos'
            videos_params = {
                'part': 'snippet,contentDetails,statistics',
                'id': ','.join(video_ids)
            }
            videos_resp = requests.get(videos_url, headers=get_youtube_headers(), params=videos_params)
            if videos_resp.status_code != 200:
                return []
            videos_data = videos_resp.json()
            for details in videos_data.get('items', []):
                s = snippet_map.get(details['id'])
                if not s:
                    continue
                if not is_not_short(details):
                    continue  # Skip Shorts
                thumbnails = s.get('thumbnails', {})
                vids.append({
                    'videoId': details['id'],
                    'title': s['title'],
                    'channelTitle': s['channelTitle'],
                    'channelId': ch['channelId'],
                    'thumbnail': thumbnails['medium']['url'] if 'medium' in thumbnails else thumbnails['default']['url'],
                    'publishedAt': s['publishedAt']
                })
            return vids
        except Exception:
            return []
    channels = channels[:10]
    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = [executor.submit(fetch_channel_uploads, ch) for ch in channels]
        for future in as_completed(futures):
            feed.extend(future.result())
    feed.sort(key=lambda v: v['publishedAt'], reverse=True)
    return {'feed': feed[:15]}

@youtube_router.post("/api/youtube/video/open")
def youtube_video_open(videoId: str = Query(..., description="YouTube video ID")):
    driver, selenium_lock = get_selenium_driver()
    if driver is None:
        return JSONResponse({"error": "Selenium WebDriver not available"}, status_code=500)
    url = f"https://www.youtube.com/watch?v={videoId}"
    with selenium_lock:
        try:
            # Use the first tab, or open one if none exist
            if driver.window_handles:
                driver.switch_to.window(driver.window_handles[0])
                driver.get(url)
            else:
                driver.execute_script(f"window.open('{url}', '_blank');")
                import time; time.sleep(1)
                driver.switch_to.window(driver.window_handles[0])
            return {"status": f"Opened YouTube video: {videoId}"}
        except Exception as e:
            return JSONResponse({"error": f"Failed to open YouTube video: {e}"}, status_code=500)

@youtube_router.post("/api/youtube/video/playpause")
def youtube_video_playpause(videoId: str = Query(..., description="YouTube video ID")):
    driver, selenium_lock = get_selenium_driver()
    if driver is None:
        return JSONResponse({"error": "Selenium WebDriver not available"}, status_code=500)
    with selenium_lock:
        try:
            if not driver.window_handles:
                return JSONResponse({"error": "No browser tab open"}, status_code=404)
            driver.switch_to.window(driver.window_handles[0])
            driver.switch_to.active_element.send_keys(Keys.SPACE)
            return {"status": "Play/pause toggled (spacebar sent)"}
        except Exception as e:
            return JSONResponse({"error": f"Failed to play/pause: {e}"}, status_code=500)

@youtube_router.post("/api/youtube/video/fullscreen")
def youtube_video_fullscreen(videoId: str = Query(..., description="YouTube video ID")):
    driver, selenium_lock = get_selenium_driver()
    if driver is None:
        return JSONResponse({"error": "Selenium WebDriver not available"}, status_code=500)
    with selenium_lock:
        try:
            if not driver.window_handles:
                return JSONResponse({"error": "No browser tab open"}, status_code=404)
            driver.switch_to.window(driver.window_handles[0])
            driver.switch_to.active_element.send_keys('f')
            return {"status": "Fullscreen toggled (f sent)"}
        except Exception as e:
            return JSONResponse({"error": f"Failed to toggle fullscreen: {e}"}, status_code=500)

@youtube_router.post("/api/youtube/video/seek/relative")
def youtube_video_seek_relative(videoId: str = Query(..., description="YouTube video ID"), delta: int = Query(...)):
    driver, selenium_lock = get_selenium_driver()
    if driver is None:
        return JSONResponse({"error": "Selenium WebDriver not available"}, status_code=500)
    with selenium_lock:
        try:
            if not driver.window_handles:
                return JSONResponse({"error": "No browser tab open"}, status_code=404)
            driver.switch_to.window(driver.window_handles[0])
            key = Keys.RIGHT if delta > 0 else Keys.LEFT
            for _ in range(abs(delta) // 5):
                driver.switch_to.active_element.send_keys(key)
            return {"status": f"Seeked by {delta} seconds using arrow keys"}
        except Exception as e:
            return JSONResponse({"error": f"Failed to seek by delta: {e}"}, status_code=500)

@youtube_router.post("/api/youtube/video/volume")
def youtube_video_set_volume(videoId: str = Query(..., description="YouTube video ID"), volume: float = Query(..., ge=0.0, le=1.0)):
    driver, selenium_lock = get_selenium_driver()
    if driver is None:
        return JSONResponse({"error": "Selenium WebDriver not available"}, status_code=500)
    with selenium_lock:
        try:
            if not driver.window_handles:
                return JSONResponse({"error": "No browser tab open"}, status_code=404)
            driver.switch_to.window(driver.window_handles[0])
            js = f"var v = document.querySelector('video'); if (v) v.volume = {volume};"
            driver.execute_script(js)
            return {"status": f"Volume set to {volume}"}
        except Exception as e:
            return JSONResponse({"error": f"Failed to set volume: {e}"}, status_code=500)

@youtube_router.get("/api/youtube/video/info")
def youtube_video_info(videoId: str = Query(...)):
    if not youtube_access_token:
        return JSONResponse({'error': 'Not authenticated with YouTube'}, status_code=401)
    url = 'https://www.googleapis.com/youtube/v3/videos'
    params = {
        'part': 'snippet,contentDetails',
        'id': videoId
    }
    resp = requests.get(url, headers=get_youtube_headers(), params=params)
    if resp.status_code != 200:
        return JSONResponse({'error': 'Failed to fetch video info', 'details': resp.text}, status_code=500)
    data = resp.json()
    if not data.get('items'):
        return JSONResponse({'error': 'Video not found'}, status_code=404)
    s = data['items'][0]['snippet']
    return {
        'videoId': videoId,
        'title': s['title'],
        'channelTitle': s['channelTitle'],
        'thumbnail': s['thumbnails']['medium']['url'] if 'medium' in s['thumbnails'] else s['thumbnails']['default']['url'],
        'publishedAt': s['publishedAt']
    }

@youtube_router.get('/api/youtube/video/playing')
def youtube_video_playing(videoId: str = Query(...)):
    driver, selenium_lock = get_selenium_driver()
    if driver is None:
        return JSONResponse({"error": "Selenium WebDriver not available"}, status_code=500)
    with selenium_lock:
        try:
            driver.switch_to.window(driver.window_handles[0])
            is_playing = driver.execute_script(
                """var v = document.querySelector('video'); return v && !v.paused;"""
            )
            return {"playing": bool(is_playing)}
        except Exception as e:
            return JSONResponse({"error": f"Failed to get play state: {e}"}, status_code=500)

@youtube_router.get("/api/system_volume")
def get_system_volume():
    try:
        import comtypes
        from pycaw.pycaw import AudioUtilities
        comtypes.CoInitialize()
        devices = AudioUtilities.GetSpeakers()
        interface = devices.Activate(
            comtypes.GUID('{5CDF2C82-841E-4546-9722-0CF74078229A}'),
            comtypes.CLSCTX_ALL, None)
        from pycaw.pycaw import IAudioEndpointVolume
        volume = interface.QueryInterface(IAudioEndpointVolume)
        level = volume.GetMasterVolumeLevelScalar()
        return {"volume": level}
    except Exception as e:
        return JSONResponse({"error": f"Failed to get system volume: {e}"}, status_code=500) 