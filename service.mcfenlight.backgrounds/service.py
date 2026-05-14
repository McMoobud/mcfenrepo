# -*- coding: utf-8 -*-
import xbmc
import xbmcvfs
import json
import os
import random

BG_DIR = xbmcvfs.translatePath('special://profile/addon_data/service.mcfenlight.backgrounds/fanart/')
MAX_IMAGES = 15


def log(msg):
    xbmc.log('###McFenlightBG###: %s' % str(msg), xbmc.LOGINFO)


def get_library_fanart():
    result = xbmc.executeJSONRPC(json.dumps({
        'jsonrpc': '2.0',
        'method': 'VideoLibrary.GetMovies',
        'params': {
            'properties': ['art'],
            'sort': {'method': 'random'},
            'limits': {'start': 0, 'end': 50}
        },
        'id': 1
    }))
    data = json.loads(result)
    movies = data.get('result', {}).get('movies', [])
    fanart_paths = []
    for movie in movies:
        art = movie.get('art', {})
        fanart = art.get('fanart')
        if fanart:
            fanart_paths.append(fanart)
    return fanart_paths


def refresh_backgrounds():
    log('Refreshing backgrounds from library')

    fanart_paths = get_library_fanart()
    log('Found %d movies with fanart' % len(fanart_paths))

    if not fanart_paths:
        log('No fanart in library — nothing to set')
        return False

    random.shuffle(fanart_paths)
    selected = fanart_paths[:MAX_IMAGES]

    try:
        if os.path.exists(BG_DIR):
            for f in os.listdir(BG_DIR):
                os.remove(os.path.join(BG_DIR, f))
        else:
            os.makedirs(BG_DIR, exist_ok=True)
    except Exception as e:
        log('Failed to prepare directory: %s' % str(e))
        return False

    count = 0
    for i, fanart_url in enumerate(selected):
        try:
            dest = os.path.join(BG_DIR, 'bg_%02d.jpg' % i)
            success = xbmcvfs.copy(fanart_url, dest)
            if success:
                count += 1
            else:
                log('xbmcvfs.copy failed for %s' % fanart_url)
        except Exception as e:
            log('Failed to copy fanart %d: %s' % (i, str(e)))

    log('Copied %d backgrounds' % count)

    if count > 0:
        xbmc.executebuiltin('Skin.SetString(CustomBackgroundPath,%s)' % BG_DIR)
        xbmc.executebuiltin('Skin.SetBool(UseCustomBackground)')
        log('Skin background set to %s' % BG_DIR)

    return count > 0


if __name__ == '__main__':
    monitor = xbmc.Monitor()
    # Wait for library to be ready
    monitor.waitForAbort(15)
    if not monitor.abortRequested():
        try:
            refresh_backgrounds()
        except Exception as e:
            log('FATAL: %s' % str(e))
