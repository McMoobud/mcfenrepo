# -*- coding: utf-8 -*-
import xbmc
import xbmcgui
import xbmcvfs
import json
import os
import zipfile

try:
    from urllib.request import Request, urlopen
except ImportError:
    from urllib2 import Request, urlopen

ADDONS_PATH = xbmcvfs.translatePath('special://home/addons/')
TEMP_PATH = xbmcvfs.translatePath('special://temp/')
EMBY_REPO_ZIP = 'https://embydata.com/downloads/addons/xbmb3c/multi-repo/repositories/repository.emby.kodi/repository.emby.kodi-1.0.8.zip'


def log(msg):
    xbmc.log('###McFenlightEmby###: %s' % str(msg), xbmc.LOGINFO)


def download_file(url, dest):
    req = Request(url, headers={'User-Agent': 'McFenlight Emby Setup/1.0'})
    resp = urlopen(req, timeout=30)
    data = resp.read()
    with open(dest, 'wb') as f:
        f.write(data)
    return len(data)


def install_zip(zip_path):
    with zipfile.ZipFile(zip_path, 'r') as zf:
        zf.extractall(ADDONS_PATH)


def main():
    ok_dialog = xbmcgui.Dialog()
    dialog = xbmcgui.DialogProgress()

    if not ok_dialog.yesno(
        'McFenlight Emby Setup',
        'This will install the Emby repository and Emby for Kodi.\n\n'
        'After installation, restart Kodi and Emby will guide you through connecting to your Emby Server.\n\n'
        'Continue?'
    ):
        return

    dialog.create('McFenlight Emby Setup', 'Downloading Emby repository...')
    dialog.update(0)
    try:
        emby_zip = os.path.join(TEMP_PATH, 'repository.emby.kodi.zip')
        download_file(EMBY_REPO_ZIP, emby_zip)
        dialog.update(40, 'Installing Emby repository...')
        install_zip(emby_zip)
        os.remove(emby_zip)
        log('Emby repo installed')
    except Exception as e:
        log('Emby repo install failed: %s' % str(e))
        dialog.close()
        ok_dialog.ok('McFenlight Emby Setup', 'Failed to download Emby repository: %s' % str(e))
        return

    dialog.update(60, 'Activating Emby repository...')
    xbmc.executebuiltin('UpdateLocalAddons')
    xbmc.sleep(3000)
    xbmc.executeJSONRPC(json.dumps({
        'jsonrpc': '2.0', 'method': 'Addons.SetAddonEnabled',
        'params': {'addonid': 'repository.emby.kodi', 'enabled': True}, 'id': 1
    }))
    log('Emby repo enabled')

    dialog.update(75, 'Installing Emby for Kodi from repository...')
    xbmc.executebuiltin('InstallAddon(plugin.video.emby)')
    xbmc.sleep(10000)
    log('Emby addon install triggered')

    dialog.update(100, 'Done!')
    xbmc.sleep(1000)
    dialog.close()

    ok_dialog.ok(
        'McFenlight Emby Setup',
        'Emby for Kodi has been installed!\n\n'
        'Please restart Kodi now.\n\n'
        'After restart, Emby will automatically launch its setup wizard '
        'to connect to your Emby Server.'
    )
    log('Emby setup complete')


if __name__ == '__main__':
    main()
