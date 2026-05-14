# -*- coding: utf-8 -*-
import xbmc
import xbmcvfs
import json
import os
import shutil

try:
    from urllib.request import Request, urlopen
except ImportError:
    from urllib2 import Request, urlopen

TMDB_API_KEY = '027243e607c49fbfcea5034519055974'
TMDB_TRENDING = 'https://api.themoviedb.org/3/trending/movie/week?api_key=%s' % TMDB_API_KEY
TMDB_IMG_BASE = 'https://image.tmdb.org/t/p/original'

BG_DIR = xbmcvfs.translatePath('special://profile/addon_data/service.mcfenlight.backgrounds/fanart/')
MAX_IMAGES = 15


def log(msg):
    xbmc.log('###McFenlightBG###: %s' % str(msg), xbmc.LOGINFO)


def fetch_trending():
    req = Request(TMDB_TRENDING, headers={'User-Agent': 'McFenlight Backgrounds/1.0'})
    resp = urlopen(req, timeout=15)
    data = json.loads(resp.read().decode('utf-8'))
    return data.get('results', [])


def download_image(url, dest):
    req = Request(url, headers={'User-Agent': 'McFenlight Backgrounds/1.0'})
    resp = urlopen(req, timeout=30)
    with open(dest, 'wb') as f:
        f.write(resp.read())


def refresh_backgrounds():
    log('Refreshing trending backgrounds')

    if os.path.exists(BG_DIR):
        shutil.rmtree(BG_DIR)
    os.makedirs(BG_DIR, exist_ok=True)

    try:
        movies = fetch_trending()
    except Exception as e:
        log('Failed to fetch trending: %s' % str(e))
        return False

    count = 0
    for movie in movies:
        if count >= MAX_IMAGES:
            break
        backdrop = movie.get('backdrop_path')
        if not backdrop:
            continue
        url = TMDB_IMG_BASE + backdrop
        dest = os.path.join(BG_DIR, 'bg_%02d.jpg' % count)
        try:
            download_image(url, dest)
            count += 1
        except Exception as e:
            log('Failed to download %s: %s' % (backdrop, str(e)))

    log('Downloaded %d backgrounds' % count)

    if count > 0:
        xbmc.executebuiltin('Skin.SetString(CustomBackgroundPath,%s)' % BG_DIR)
        xbmc.executebuiltin('Skin.SetBool(UseCustomBackground)')
        log('Skin background set to %s' % BG_DIR)

    return count > 0


if __name__ == '__main__':
    monitor = xbmc.Monitor()
    # Wait for Kodi to be fully started
    monitor.waitForAbort(10)
    if not monitor.abortRequested():
        refresh_backgrounds()
