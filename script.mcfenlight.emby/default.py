# -*- coding: utf-8 -*-
import xbmc
import xbmcgui
import xbmcvfs
import json
import os
import shutil
import zipfile

try:
    from urllib.request import Request, urlopen
except ImportError:
    from urllib2 import Request, urlopen

ADDONS_PATH = xbmcvfs.translatePath('special://home/addons/')
TEMP_PATH = xbmcvfs.translatePath('special://temp/')

EMBY_REPO_ZIP = 'https://embydata.com/downloads/addons/xbmb3c/multi-repo/repositories/repository.emby.kodi/repository.emby.kodi-1.0.8.zip'
EMBY_SERVICE_ZIP = 'https://embydata.com/downloads/addons/xbmb3c/multi-repo/release/v21_omega/plugin.service.emby-next-gen/plugin.service.emby-next-gen-11.1.27.zip'
EMBY_VIDEO_ZIP = 'https://embydata.com/downloads/addons/xbmb3c/multi-repo/release/v21_omega/plugin.video.emby-next-gen/plugin.video.emby-next-gen-10.1.2.zip'


def log(msg):
    xbmc.log('###McFenlightEmby###: %s' % str(msg), xbmc.LOGINFO)


def download_file(url, dest):
    req = Request(url, headers={'User-Agent': 'McFenlight Emby Setup/1.0'})
    resp = urlopen(req, timeout=60)
    data = resp.read()
    with open(dest, 'wb') as f:
        f.write(data)
    return len(data)


def install_zip_with_rename(zip_path, expected_folder):
    """Extract zip and rename root folder to the expected addon ID."""
    with zipfile.ZipFile(zip_path, 'r') as zf:
        root_folders = set(n.split('/')[0] for n in zf.namelist() if '/' in n)
        zf.extractall(ADDONS_PATH)
    for actual_folder in root_folders:
        if actual_folder != expected_folder:
            src = os.path.join(ADDONS_PATH, actual_folder)
            dst = os.path.join(ADDONS_PATH, expected_folder)
            if os.path.exists(dst):
                shutil.rmtree(dst)
            os.rename(src, dst)
            log('Renamed %s -> %s' % (actual_folder, expected_folder))


def install_zip(zip_path):
    with zipfile.ZipFile(zip_path, 'r') as zf:
        zf.extractall(ADDONS_PATH)


def main():
    ok_dialog = xbmcgui.Dialog()
    dialog = xbmcgui.DialogProgress()

    if not ok_dialog.yesno(
        'McFenlight Emby Setup',
        'This will install Emby for Kodi (emby-next-gen).\n\n'
        'After installation, restart Kodi and Emby will guide you through connecting to your Emby Server.\n\n'
        'Continue?'
    ):
        return

    # Step 1: Install Emby repo
    dialog.create('McFenlight Emby Setup', 'Downloading Emby repository...')
    dialog.update(0)
    try:
        emby_zip = os.path.join(TEMP_PATH, 'repository.emby.kodi.zip')
        download_file(EMBY_REPO_ZIP, emby_zip)
        dialog.update(10, 'Installing Emby repository...')
        install_zip(emby_zip)
        os.remove(emby_zip)
        log('Emby repo installed')
    except Exception as e:
        log('Emby repo install failed: %s' % str(e))
        dialog.close()
        ok_dialog.ok('McFenlight Emby Setup', 'Failed to download Emby repository: %s' % str(e))
        return

    # Step 2: Install dateutil dependency
    dialog.update(15, 'Installing dependencies...')
    xbmc.executebuiltin('InstallAddon(script.module.dateutil)')
    xbmc.sleep(8000)
    log('dateutil dependency install triggered')

    # Step 3: Install Emby service addon (dependency)
    dialog.update(25, 'Downloading Emby service (this may take a moment)...')
    try:
        svc_zip = os.path.join(TEMP_PATH, 'plugin.service.emby-next-gen.zip')
        download_file(EMBY_SERVICE_ZIP, svc_zip)
        dialog.update(50, 'Installing Emby service...')
        install_zip_with_rename(svc_zip, 'plugin.service.emby-next-gen')
        os.remove(svc_zip)
        log('Emby service addon installed')
    except Exception as e:
        log('Emby service install failed: %s' % str(e))
        dialog.close()
        ok_dialog.ok('McFenlight Emby Setup', 'Failed to install Emby service: %s' % str(e))
        return

    # Step 4: Install Emby video addon
    dialog.update(65, 'Downloading Emby for Kodi...')
    try:
        vid_zip = os.path.join(TEMP_PATH, 'plugin.video.emby-next-gen.zip')
        download_file(EMBY_VIDEO_ZIP, vid_zip)
        dialog.update(80, 'Installing Emby for Kodi...')
        install_zip_with_rename(vid_zip, 'plugin.video.emby-next-gen')
        os.remove(vid_zip)
        log('Emby video addon installed')
    except Exception as e:
        log('Emby video install failed: %s' % str(e))
        dialog.close()
        ok_dialog.ok('McFenlight Emby Setup', 'Failed to install Emby for Kodi: %s' % str(e))
        return

    # Step 5: Register and enable all addons
    dialog.update(90, 'Activating Emby addons...')
    xbmc.executebuiltin('UpdateLocalAddons')
    xbmc.sleep(3000)
    for addon_id in ['repository.emby.kodi', 'plugin.service.emby-next-gen', 'plugin.video.emby-next-gen']:
        xbmc.executeJSONRPC(json.dumps({
            'jsonrpc': '2.0', 'method': 'Addons.SetAddonEnabled',
            'params': {'addonid': addon_id, 'enabled': True}, 'id': 1
        }))
        log('Enabled %s' % addon_id)

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
