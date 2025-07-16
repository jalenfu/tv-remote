from fastapi import APIRouter, Query, status, Request
from fastapi.responses import JSONResponse, RedirectResponse
from selenium.webdriver.common.keys import Keys
import threading
import os
import requests
import time
import pyautogui
import pygetwindow as gw
from selenium import webdriver
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.firefox.firefox_profile import FirefoxProfile
from dotenv import load_dotenv
import screeninfo
from selenium.webdriver.common.action_chains import ActionChains

# Load environment variables
load_dotenv()
TWITCH_CLIENT_ID = os.getenv('TWITCH_CLIENT_ID')
TWITCH_CLIENT_SECRET = os.getenv('TWITCH_CLIENT_SECRET')
TWITCH_REDIRECT_URI = os.getenv('TWITCH_REDIRECT_URI')

FIREFOX_TITLE = "Mozilla Firefox"

# In-memory token storage (for demo; use persistent storage for production)
twitch_access_token = None
twitch_refresh_token = None
twitch_user_id = None

selenium_lock = threading.Lock()
selenium_driver = None

def get_twitch_headers():
    return {
        'Authorization': f'Bearer {twitch_access_token}',
        'Client-Id': TWITCH_CLIENT_ID,
    }

def focus_firefox():
    import pygetwindow as gw
    windows = gw.getWindowsWithTitle(FIREFOX_TITLE)
    if windows:
        win = windows[0]
        try:
            win.minimize()
            win.restore()
            win.activate()
            time.sleep(0.2)  # Give time for focus
            return True
        except Exception as e:
            print(f"Error focusing Firefox: {e}")
            return False
    return False

def move_firefox_to_monitor(monitor_index=2):
    try:
        import screeninfo
        monitors = screeninfo.get_monitors()
        if monitor_index >= len(monitors):
            print(f"Monitor {monitor_index+1} not found.")
            return
        mon = monitors[monitor_index]
        windows = gw.getWindowsWithTitle("Mozilla Firefox")
        if windows:
            win = windows[0]
            win.moveTo(mon.x, mon.y)
            win.maximize()
            # Add a small delay to ensure window is properly positioned
            time.sleep(0.5)
            # Activate the window to ensure it has focus
            win.activate()
            time.sleep(0.2)
            # Send F11 to fullscreen the browser
            pyautogui.press('f11')
            print(f"Firefox moved to monitor {monitor_index+1} and fullscreened")
    except Exception as e:
        print(f"Could not move Firefox to monitor {monitor_index+1}: {e}")

def start_selenium_driver():
    global selenium_driver
    if selenium_driver is not None:
        try:
            selenium_driver.title
            return selenium_driver
        except Exception:
            try:
                selenium_driver.quit()
            except Exception:
                pass
            selenium_driver = None
    options = Options()
    profile_path = r"C:\\Users\\Jalen Fu\\AppData\\Roaming\\Mozilla\\Firefox\\Profiles\\dsmxt5ae.selenium_profile"
    options.profile = FirefoxProfile(profile_path)
    try:
        driver = webdriver.Firefox(options=options)
        selenium_driver = driver
        # Move to monitor 3 and maximize
        move_firefox_to_monitor(2)
        return driver
    except Exception as e:
        print(f"Error starting Selenium WebDriver: {e}")
        return None

def get_selenium_driver():
    global selenium_driver
    return start_selenium_driver()

def find_tab_by_url(driver, url_substring):
    for handle in driver.window_handles:
        driver.switch_to.window(handle)
        if url_substring in driver.current_url:
            return handle
    return None

def send_key_to_tab(driver, handle, key):
    driver.switch_to.window(handle)
    driver.switch_to.active_element.send_keys(key)

twitch_router = APIRouter()

@twitch_router.get('/api/twitch/login')
def twitch_login():
    url = (
        f'https://id.twitch.tv/oauth2/authorize?response_type=code'
        f'&client_id={TWITCH_CLIENT_ID}'
        f'&redirect_uri={TWITCH_REDIRECT_URI}'
        f'&scope=user:read:follows'
    )
    return RedirectResponse(url)

@twitch_router.get('/api/twitch/oauth/callback')
def twitch_oauth_callback(request: Request):
    global twitch_access_token, twitch_refresh_token, twitch_user_id
    code = request.query_params.get('code')
    if not code:
        return {'error': 'No code provided'}
    token_url = 'https://id.twitch.tv/oauth2/token'
    data = {
        'client_id': TWITCH_CLIENT_ID,
        'client_secret': TWITCH_CLIENT_SECRET,
        'code': code,
        'grant_type': 'authorization_code',
        'redirect_uri': TWITCH_REDIRECT_URI,
    }
    resp = requests.post(token_url, data=data)
    if resp.status_code != 200:
        return {'error': 'Failed to get token', 'details': resp.text}
    tokens = resp.json()
    twitch_access_token = tokens['access_token']
    twitch_refresh_token = tokens.get('refresh_token')
    user_resp = requests.get('https://api.twitch.tv/helix/users', headers=get_twitch_headers())
    if user_resp.status_code != 200:
        return {'error': 'Failed to get user info', 'details': user_resp.text}
    twitch_user_id = user_resp.json()['data'][0]['id']
    return RedirectResponse('/')

@twitch_router.get('/api/twitch/followed')
def twitch_followed():
    if not twitch_access_token or not twitch_user_id:
        login_url = f'/api/twitch/login'
        return JSONResponse({
            'error': 'Not authenticated',
            'login_url': login_url
        }, status_code=status.HTTP_401_UNAUTHORIZED)
    url = f'https://api.twitch.tv/helix/streams/followed?user_id={twitch_user_id}'
    resp = requests.get(url, headers=get_twitch_headers())
    if resp.status_code != 200:
        return {'error': 'Failed to fetch followed streams', 'details': resp.text}
    data = resp.json()
    return {'streams': data.get('data', [])}

@twitch_router.post('/api/twitch_stream')
def twitch_stream(channel: str = Query(..., description="Twitch channel name")):
    driver = get_selenium_driver()
    if driver is None:
        return JSONResponse({"error": "Selenium WebDriver not available"}, status_code=500)
    url = f"https://twitch.tv/{channel}"
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
            return {"status": f"Opened Twitch stream: {channel}"}
        except Exception as e:
            return JSONResponse({"error": f"Failed to open Twitch stream: {e}"}, status_code=500)

@twitch_router.post('/mute')
def mute_stream(channel: str = Query(None, description="Twitch channel name (optional)")):
    driver = get_selenium_driver()
    if driver is None:
        return JSONResponse({"error": "Selenium WebDriver not available"}, status_code=500)
    with selenium_lock:
        handle = None
        if channel:
            handle = find_tab_by_url(driver, f"twitch.tv/{channel}")
        if handle is None:
            for h in driver.window_handles:
                driver.switch_to.window(h)
                if "twitch.tv" in driver.current_url:
                    handle = h
                    break
        if handle is None:
            return JSONResponse({"error": "Twitch tab not found"}, status_code=404)
        try:
            send_key_to_tab(driver, handle, 'm')
            return {"status": "Mute/unmute sent"}
        except Exception as e:
            return JSONResponse({"error": f"Failed to send mute command: {e}"}, status_code=500)

@twitch_router.post('/theater_mode')
def theater_mode(channel: str = Query(None, description="Twitch channel name (optional)")):
    driver = get_selenium_driver()
    if driver is None:
        return JSONResponse({"error": "Selenium WebDriver not available"}, status_code=500)
    with selenium_lock:
        handle = None
        if channel:
            handle = find_tab_by_url(driver, f"twitch.tv/{channel}")
        if handle is None:
            for h in driver.window_handles:
                driver.switch_to.window(h)
                if "twitch.tv" in driver.current_url:
                    handle = h
                    break
        if handle is None:
            return JSONResponse({"error": "Twitch tab not found"}, status_code=404)
        try:
            driver.switch_to.window(handle)
            actions = ActionChains(driver)
            actions.key_down(Keys.ALT).send_keys('t').key_up(Keys.ALT).perform()
            return {"status": "Theater mode toggled"}
        except Exception as e:
            return JSONResponse({"error": f"Failed to send theater mode command: {e}"}, status_code=500)

@twitch_router.post('/api/twitch/playpause')
def twitch_playpause(channel: str = Query(None, description="Twitch channel name (optional)")):
    driver = get_selenium_driver()
    if driver is None:
        return JSONResponse({"error": "Selenium WebDriver not available"}, status_code=500)
    with selenium_lock:
        handle = None
        if channel:
            handle = find_tab_by_url(driver, f"twitch.tv/{channel}")
        if handle is None:
            for h in driver.window_handles:
                driver.switch_to.window(h)
                if "twitch.tv" in driver.current_url:
                    handle = h
                    break
        if handle is None:
            return JSONResponse({"error": "Twitch tab not found"}, status_code=404)
        try:
            send_key_to_tab(driver, handle, Keys.SPACE)
            return {"status": "Play/pause toggled (spacebar sent)"}
        except Exception as e:
            return JSONResponse({"error": f"Failed to send play/pause command: {e}"}, status_code=500)

@twitch_router.get('/api/twitch/playing')
def twitch_playing(channel: str = Query(None, description="Twitch channel name (optional)")):
    driver = get_selenium_driver()
    if driver is None:
        return JSONResponse({"error": "Selenium WebDriver not available"}, status_code=500)
    with selenium_lock:
        handle = None
        if channel:
            handle = find_tab_by_url(driver, f"twitch.tv/{channel}")
        if handle is None:
            for h in driver.window_handles:
                driver.switch_to.window(h)
                if "twitch.tv" in driver.current_url:
                    handle = h
                    break
        if handle is None:
            return JSONResponse({"error": "Twitch tab not found"}, status_code=404)
        try:
            driver.switch_to.window(handle)
            is_playing = driver.execute_script(
                """
                var v = document.querySelector('video');
                return v && !v.paused;
                """
            )
            return {"playing": bool(is_playing)}
        except Exception as e:
            return JSONResponse({"error": f"Failed to get play state: {e}"}, status_code=500)

# Add stream_volume and other Twitch-related endpoints as needed 