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
    log('Fetching TMDB trending: %s' % TMDB_TRENDING)
    req = Request(TMDB_TRENDING, headers={'User-Agent': 'McFenlight Backgrounds/1.0'})
    resp = urlopen(req, timeout=15)
    raw = resp.read().decode('utf-8')
    log('TMDB response length: %d' % len(raw))
    data = json.loads(raw)
    results = data.get('results', [])
    log('Got %d trending movies' % len(results))
    return results


def download_image(url, dest):
    req = Request(url, headers={'User-Agent': 'McFenlight Backgrounds/1.0'})
    resp = urlopen(req, timeout=30)
    with open(dest, 'wb') as f:
        f.write(resp.read())


def refresh_backgrounds():
    log('Refreshing trending backgrounds')
    log('BG_DIR: %s' % BG_DIR)

    try:
        if os.path.exists(BG_DIR):
            shutil.rmtree(BG_DIR)
        os.makedirs(BG_DIR, exist_ok=True)
        log('Created fanart directory')
    except Exception as e:
        log('Failed to create directory: %s' % str(e))
        return False

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
            log('Downloaded %s' % os.path.basename(dest))
            count += 1
        except Exception as e:
            log('Failed to download %s: %s' % (backdrop, str(e)))

    log('Downloaded %d backgrounds total' % count)

    if count > 0:
        xbmc.executebuiltin('Skin.SetString(CustomBackgroundPath,%s)' % BG_DIR)
        xbmc.executebuiltin('Skin.SetBool(UseCustomBackground)')
        log('Skin background set to %s' % BG_DIR)
    else:
        log('No images downloaded — background not changed')

    return count > 0


if __name__ == '__main__':
    monitor = xbmc.Monitor()
    monitor.waitForAbort(10)
    if not monitor.abortRequested():
        try:
            refresh_backgrounds()
        except Exception as e:
            log('FATAL: %s' % str(e))
