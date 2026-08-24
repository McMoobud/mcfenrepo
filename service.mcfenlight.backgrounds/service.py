# -*- coding: utf-8 -*-
"""McFenlight Backgrounds v1.0.4

On every Kodi startup:
  1. Install the splash screen (UNCHANGED from v1.0.3).
  2. Refresh the Confluence home background with random movie art:
       - Emby: pull random fanart from the local Kodi library (native).
       - else TMDB: Trending / In Cinemas / Popular backdrops (zero-config).
  3. Wipe-and-replace: the rotation folder is emptied every boot, no history.

Refreshes on boot only. No timers, no in-session loop.
"""
import xbmc
import xbmcvfs
import xbmcaddon
import os
import shutil
import json
import random
import time

try:
    from urllib.request import urlopen, Request
except ImportError:  # py2 safety, never hit on Kodi 21
    from urllib2 import urlopen, Request

ADDON = xbmcaddon.Addon('service.mcfenlight.backgrounds')
ADDON_PATH = ADDON.getAddonInfo('path')
PROFILE = xbmcvfs.translatePath(ADDON.getAddonInfo('profile'))

TMDB_KEY = '027243e607c49fbfcea5034519055974'
TMDB_IMG = 'https://image.tmdb.org/t/p/w1280'
TMDB_ENDPOINTS = {
    'trending': 'https://api.themoviedb.org/3/trending/movie/week',
    'cinemas': 'https://api.themoviedb.org/3/movie/now_playing',
    'popular': 'https://api.themoviedb.org/3/movie/popular',
}
UA = {'User-Agent': 'McFenlightBG/1.0'}


def log(msg):
    xbmc.log('###McFenlightBG###: %s' % str(msg), xbmc.LOGINFO)


def setting(key, default=''):
    try:
        val = ADDON.getSetting(key)
    except Exception:
        val = ''
    return val if val not in (None, '') else default


# --- Splash (unchanged from v1.0.3) -----------------------------------------

def install_splash():
    splash_src = os.path.join(ADDON_PATH, 'splash.png')
    media_dir = xbmcvfs.translatePath('special://home/media/')
    splash_dest = os.path.join(media_dir, 'Splash.png')
    try:
        os.makedirs(media_dir, exist_ok=True)
        shutil.copy2(splash_src, splash_dest)
        log('Splash screen installed to %s' % splash_dest)
    except Exception as e:
        log('Failed to install splash: %s' % str(e))


# --- Sources ----------------------------------------------------------------

def _jsonrpc(method, params):
    req = json.dumps({'jsonrpc': '2.0', 'id': 1, 'method': method, 'params': params})
    return json.loads(xbmc.executeJSONRPC(req))


def current_skin():
    try:
        r = _jsonrpc('Settings.GetSettingValue', {'setting': 'lookandfeel.skin'})
        return r.get('result', {}).get('value', '')
    except Exception:
        return ''


def addon_enabled(addon_id):
    try:
        r = _jsonrpc('Addons.GetAddonDetails', {'addonid': addon_id, 'properties': ['enabled']})
        return bool(r.get('result', {}).get('addon', {}).get('enabled'))
    except Exception:
        return False


def ensure_confluence_skin():
    """Confluence is required for the custom background. Switch to it if needed."""
    if setting('set_skin', 'true') != 'true':
        return
    if current_skin() == 'skin.confluence':
        return
    if not addon_enabled('skin.confluence'):
        log('Confluence skin not installed/enabled — skipping skin switch')
        return
    try:
        _jsonrpc('Settings.SetSettingValue',
                 {'setting': 'lookandfeel.skin', 'value': 'skin.confluence'})
        log('Switched skin to Confluence')
        xbmc.Monitor().waitForAbort(3)  # let the skin reload before we set its string
    except Exception as e:
        log('skin switch failed: %s' % str(e))


def library_has_movies():
    try:
        r = _jsonrpc('VideoLibrary.GetMovies', {'limits': {'start': 0, 'end': 1}})
        return len(r.get('result', {}).get('movies', [])) > 0
    except Exception as e:
        log('library check failed: %s' % str(e))
        return False


def emby_fanarts(limit):
    """Random fanart URLs from the local Kodi (Emby-synced) library.
    URLs keep their Kodi options (e.g. |redirect-limit=1000) so xbmcvfs can
    fetch them via the same path Kodi uses to display them."""
    try:
        r = _jsonrpc('VideoLibrary.GetMovies', {
            'properties': ['art'],
            'sort': {'method': 'random'},
            'limits': {'start': 0, 'end': limit * 3},
        })
        movies = r.get('result', {}).get('movies', [])
        urls = []
        for m in movies:
            fan = (m.get('art') or {}).get('fanart') or ''
            if fan:
                urls.append(fan)
            if len(urls) >= limit:
                break
        return urls
    except Exception as e:
        log('Emby query failed: %s' % str(e))
        return []


def tmdb_fanarts(category, limit):
    url = TMDB_ENDPOINTS.get(category, TMDB_ENDPOINTS['trending'])
    url += '?api_key=%s&language=en-US&page=1' % TMDB_KEY
    for attempt in range(2):
        try:
            data = json.loads(urlopen(Request(url, headers=UA), timeout=15).read().decode('utf-8'))
            results = [r for r in data.get('results', []) if r.get('backdrop_path')]
            random.shuffle(results)
            return [TMDB_IMG + r['backdrop_path'] for r in results[:limit]]
        except Exception as e:
            log('TMDB fetch attempt %d failed: %s' % (attempt + 1, str(e)))
            time.sleep(10)
    return []


# --- Download ---------------------------------------------------------------

def download(url, dest):
    try:
        if 'image.tmdb.org' in url:
            data = urlopen(Request(url, headers=UA), timeout=20).read()
            with open(dest, 'wb') as fh:
                fh.write(data)
        else:
            # Emby / localhost proxy / Kodi-option URLs: use Kodi's own VFS.
            if xbmcvfs.exists(dest):
                xbmcvfs.delete(dest)
            if not xbmcvfs.copy(url, dest):
                return False
        return os.path.exists(dest) and os.path.getsize(dest) > 1024
    except Exception as e:
        log('download failed (%s): %s' % (url[:70], str(e)))
        return False


# --- Refresh ----------------------------------------------------------------

def refresh_backgrounds():
    try:
        count = int(setting('image_count', '15') or '15')
    except ValueError:
        count = 15
    mode = setting('source_mode', 'auto')       # auto | emby | tmdb
    category = setting('category', 'trending')   # trending | cinemas | popular

    use_emby = mode == 'emby' or (mode == 'auto' and library_has_movies())

    urls = []
    if use_emby:
        urls = emby_fanarts(count)
        log('Emby source: %d fanart url(s)' % len(urls))
    if not urls:
        urls = tmdb_fanarts(category, count)
        log('TMDB source (%s): %d url(s)' % (category, len(urls)))

    if not urls:
        log('No backgrounds available — leaving current background untouched')
        return

    rotation = os.path.join(PROFILE, 'rotation')
    try:
        if os.path.isdir(rotation):
            shutil.rmtree(rotation)
    except Exception as e:
        log('wipe failed: %s' % str(e))
    os.makedirs(rotation, exist_ok=True)

    saved = []
    for i, url in enumerate(urls):
        dest = os.path.join(rotation, '%02d.jpg' % i)
        if download(url, dest):
            saved.append(dest)
    log('Downloaded %d/%d backgrounds to %s' % (len(saved), len(urls), rotation))

    if not saved:
        log('All downloads failed — leaving current background untouched')
        return

    # Confluence's background is a single-image control (a folder renders blank),
    # so pick one random image for this boot. Fresh random pick every startup.
    chosen = random.choice(saved)
    xbmc.executebuiltin('Skin.SetString(CustomBackgroundPath,%s)' % chosen)
    xbmc.executebuiltin('Skin.SetBool(UseCustomBackground)')
    log('CustomBackgroundPath set to %s (from pool of %d)' % (chosen, len(saved)))


if __name__ == '__main__':
    monitor = xbmc.Monitor()
    monitor.waitForAbort(8)
    if not monitor.abortRequested():
        try:
            install_splash()
            ensure_confluence_skin()
            refresh_backgrounds()
        except Exception as e:
            log('FATAL: %s' % str(e))
