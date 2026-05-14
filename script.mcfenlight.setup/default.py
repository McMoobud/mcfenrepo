# -*- coding: utf-8 -*-
import xbmc
import xbmcgui
import xbmcvfs
import json
import os
import time
import zipfile
import sqlite3

try:
    from urllib.request import Request, urlopen
except ImportError:
    from urllib2 import Request, urlopen

ADDONS_PATH = xbmcvfs.translatePath('special://home/addons/')
ADDON_DATA = xbmcvfs.translatePath('special://profile/addon_data/')
TEMP_PATH = xbmcvfs.translatePath('special://temp/')

MCFENLIGHT_REPO_ZIP = 'https://mcmoobud.github.io/mcfenrepo/repository.mcfenlight/repository.mcfenlight-1.0.3.zip'
COCOSCRAPERS_REPO_ZIP = 'https://raw.githubusercontent.com/CocoJoe2411/repository.cocoscrapers/master/zips/repository.cocoscrapers/repository.cocoscrapers-1.0.0.zip'

MCFENLIGHT_ADDON_ZIP = 'https://mcmoobud.github.io/mcfenrepo/plugin.video.mcfenlight/plugin.video.mcfenlight-2.2.04.zip'
COCOSCRAPERS_ADDON_ZIP = 'https://raw.githubusercontent.com/CocoJoe2411/repository.cocoscrapers/master/zips/script.module.cocoscrapers/script.module.cocoscrapers-1.0.0.zip'

TRAKT_CLIENT_ID = 'd670d157485c272e4a9385da4a8b3d1ba1d248ee93a619309ebd7f9cf6a67351'
TRAKT_CLIENT_SECRET = '7efa8413b83e997632598f39349444dc6b2d64cae668ff0bf1ca38986a4e8aa5'
TORBOX_API_KEY = '4136f32a-e795-40e3-bb87-b8bc8be65eca'


def log(msg):
    xbmc.log('###McFenlightSetup###: %s' % str(msg), xbmc.LOGINFO)


def download_file(url, dest):
    req = Request(url, headers={'User-Agent': 'McFenlight Setup/1.0'})
    resp = urlopen(req, timeout=30)
    data = resp.read()
    with open(dest, 'wb') as f:
        f.write(data)
    return len(data)


def install_zip(zip_path):
    with zipfile.ZipFile(zip_path, 'r') as zf:
        zf.extractall(ADDONS_PATH)


def set_kodi_language_defaults():
    settings = [
        ('locale.audiolanguage', 'default'),
        ('locale.subtitlelanguage', 'default'),
        ('subtitles.languages', 'default'),
    ]
    for setting, value in settings:
        payload = json.dumps({
            'jsonrpc': '2.0',
            'method': 'Settings.SetSettingValue',
            'params': {'setting': setting, 'value': value},
            'id': 1
        })
        xbmc.executeJSONRPC(payload)
    log('Kodi language defaults set to UI language')


def trakt_auth(dialog):
    log('Starting Trakt auth')
    headers = {
        'Content-Type': 'application/json',
        'trakt-api-version': '2',
        'trakt-api-key': TRAKT_CLIENT_ID
    }
    data = json.dumps({'client_id': TRAKT_CLIENT_ID}).encode('utf-8')
    req = Request('https://api.trakt.tv/oauth/device/code', data=data, headers=headers)
    req.add_header('User-Agent', 'McFenlight for Kodi')
    try:
        resp = urlopen(req, timeout=10)
        device = json.loads(resp.read().decode('utf-8'))
    except Exception as e:
        log('Trakt device code error: %s' % str(e))
        xbmcgui.Dialog().ok('McFenlight Setup', 'Could not contact Trakt. Skipping — you can authorise later in McFenlight settings.')
        return None

    user_code = device['user_code']
    expires_in = device.get('expires_in', 600)
    interval = device.get('interval', 5)

    dialog.create(
        'McFenlight Setup — Trakt',
        'Go to [B]trakt.tv/activate[/B] on your phone\n\nEnter code: [B]%s[/B]\n\nWaiting for approval...' % user_code
    )

    token_data = json.dumps({
        'code': device['device_code'],
        'client_id': TRAKT_CLIENT_ID,
        'client_secret': TRAKT_CLIENT_SECRET
    }).encode('utf-8')

    start = time.time()
    while time.time() - start < expires_in:
        if dialog.iscanceled():
            log('Trakt auth cancelled by user')
            dialog.close()
            return None
        xbmc.sleep(interval * 1000)
        elapsed = int(time.time() - start)
        dialog.update(int(elapsed * 100 / expires_in))
        try:
            req = Request('https://api.trakt.tv/oauth/device/token', data=token_data, headers=headers)
            req.add_header('User-Agent', 'McFenlight for Kodi')
            resp = urlopen(req, timeout=10)
            result = json.loads(resp.read().decode('utf-8'))
            dialog.close()
            log('Trakt auth success')
            return result
        except Exception:
            pass

    dialog.close()
    xbmcgui.Dialog().ok('McFenlight Setup', 'Trakt authorisation timed out. You can authorise later in McFenlight settings.')
    return None


def write_mcfenlight_settings(trakt_result):
    db_dir = os.path.join(ADDON_DATA, 'plugin.video.mcfenlight', 'databases')
    db_path = os.path.join(db_dir, 'settings.db')

    for _ in range(60):
        if os.path.exists(db_path):
            break
        xbmc.sleep(500)
    else:
        log('Settings DB not found at %s — creating it' % db_path)
        os.makedirs(db_dir, exist_ok=True)

    conn = sqlite3.connect(db_path, timeout=20)
    conn.execute('PRAGMA synchronous = OFF')
    conn.execute('PRAGMA journal_mode = OFF')
    c = conn.cursor()
    c.execute('CREATE TABLE IF NOT EXISTS settings (setting_id text not null unique, setting_type text, setting_default text, setting_value text)')

    def set_val(sid, stype, default, value):
        c.execute('INSERT OR REPLACE INTO settings VALUES (?, ?, ?, ?)',
                  (sid, stype, default, value))

    if trakt_result:
        set_val('trakt.token', 'string', 'empty_setting', trakt_result.get('access_token', ''))
        set_val('trakt.refresh', 'string', 'empty_setting', trakt_result.get('refresh_token', ''))
        expires = str(time.time() + trakt_result.get('expires_in', 7776000))
        set_val('trakt.expires', 'string', '0', expires)
        set_val('trakt.user', 'string', 'empty_setting', 'true')
        log('Trakt tokens written to settings DB')

    set_val('tb.token', 'string', 'empty_setting', TORBOX_API_KEY)
    set_val('tb.enabled', 'boolean', 'false', 'true')
    set_val('provider.tb_cloud', 'boolean', 'false', 'true')
    log('TorBox enabled with baked API key')

    set_val('provider.external', 'boolean', 'false', 'true')
    set_val('external_scraper.module', 'string', 'empty_setting', 'script.module.cocoscrapers')
    set_val('external_scraper.name', 'string', 'empty_setting', 'cocoscrapers')
    log('CocoScrapers enabled as external scraper')

    conn.commit()

    verify = conn.execute(
        'SELECT setting_id, setting_value FROM settings WHERE setting_id IN (?, ?, ?, ?, ?)',
        ('tb.enabled', 'tb.token', 'provider.external', 'external_scraper.module', 'provider.tb_cloud')
    ).fetchall()
    log('Verified settings: %s' % str(verify))
    total = conn.execute('SELECT COUNT(*) FROM settings').fetchone()[0]
    log('Total settings in DB: %d' % total)
    conn.close()

    xbmc.executebuiltin('RunPlugin(plugin://plugin.video.mcfenlight/?mode=sync_settings&silent=true)')
    xbmc.sleep(3000)
    log('Triggered McFenlight sync_settings reload')


def main():
    dialog = xbmcgui.DialogProgress()
    ok_dialog = xbmcgui.Dialog()

    if not ok_dialog.yesno(
        'McFenlight Setup',
        'This will install McFenlight and everything it needs.\n\n'
        'TorBox is pre-configured — no debrid setup required.\n\n'
        'You\'ll be asked to authorise Trakt on your phone.\n\n'
        'Continue?'
    ):
        return

    # Step 1: Download and install repos
    dialog.create('McFenlight Setup', 'Downloading CocoScrapers repository...')
    dialog.update(0)
    try:
        coco_zip = os.path.join(TEMP_PATH, 'repository.cocoscrapers.zip')
        download_file(COCOSCRAPERS_REPO_ZIP, coco_zip)
        dialog.update(10, 'Installing CocoScrapers repository...')
        install_zip(coco_zip)
        os.remove(coco_zip)
        log('CocoScrapers repo installed')
    except Exception as e:
        log('CocoScrapers repo install failed: %s' % str(e))
        dialog.close()
        ok_dialog.ok('McFenlight Setup', 'Failed to download CocoScrapers repository: %s' % str(e))
        return

    dialog.update(20, 'Downloading McFenlight repository...')
    try:
        mcfen_zip = os.path.join(TEMP_PATH, 'repository.mcfenlight.zip')
        download_file(MCFENLIGHT_REPO_ZIP, mcfen_zip)
        dialog.update(30, 'Installing McFenlight repository...')
        install_zip(mcfen_zip)
        os.remove(mcfen_zip)
        log('McFenlight repo installed')
    except Exception as e:
        log('McFenlight repo install failed: %s' % str(e))
        dialog.close()
        ok_dialog.ok('McFenlight Setup', 'Failed to download McFenlight repository: %s' % str(e))
        return

    # Step 2: Download and install addons directly
    dialog.update(40, 'Downloading CocoScrapers module...')
    try:
        coco_addon_zip = os.path.join(TEMP_PATH, 'script.module.cocoscrapers.zip')
        download_file(COCOSCRAPERS_ADDON_ZIP, coco_addon_zip)
        dialog.update(50, 'Installing CocoScrapers module...')
        install_zip(coco_addon_zip)
        os.remove(coco_addon_zip)
        log('CocoScrapers module extracted')
    except Exception as e:
        log('CocoScrapers module install failed: %s' % str(e))
        dialog.close()
        ok_dialog.ok('McFenlight Setup', 'Failed to install CocoScrapers: %s' % str(e))
        return

    dialog.update(60, 'Downloading McFenlight...')
    try:
        mcfen_addon_zip = os.path.join(TEMP_PATH, 'plugin.video.mcfenlight.zip')
        download_file(MCFENLIGHT_ADDON_ZIP, mcfen_addon_zip)
        dialog.update(70, 'Installing McFenlight...')
        install_zip(mcfen_addon_zip)
        os.remove(mcfen_addon_zip)
        log('McFenlight addon extracted')
    except Exception as e:
        log('McFenlight addon install failed: %s' % str(e))
        dialog.close()
        ok_dialog.ok('McFenlight Setup', 'Failed to install McFenlight: %s' % str(e))
        return

    # Install dependencies from the official Kodi repo
    dialog.update(75, 'Installing dependencies (requests, PIL)...')
    xbmc.executebuiltin('InstallAddon(script.module.requests)')
    xbmc.sleep(5000)
    xbmc.executebuiltin('InstallAddon(script.module.pil)')
    xbmc.sleep(5000)
    log('Dependencies installed')

    # Register everything with Kodi and enable
    dialog.update(82, 'Activating addons...')
    xbmc.executebuiltin('UpdateLocalAddons')
    xbmc.sleep(3000)
    for addon_id in ['repository.cocoscrapers', 'repository.mcfenlight',
                     'script.module.cocoscrapers', 'plugin.video.mcfenlight']:
        xbmc.executeJSONRPC(json.dumps({
            'jsonrpc': '2.0', 'method': 'Addons.SetAddonEnabled',
            'params': {'addonid': addon_id, 'enabled': True}, 'id': 1
        }))
        log('Enabled %s' % addon_id)
    xbmc.sleep(5000)

    # Step 3: Set Kodi language defaults
    dialog.update(88, 'Setting language preferences...')
    set_kodi_language_defaults()

    dialog.update(92, 'Addon installation complete!')
    xbmc.sleep(1000)
    dialog.close()

    # Step 4: Trakt auth
    if ok_dialog.yesno('McFenlight Setup', 'Addons installed!\n\nWould you like to set up Trakt now?\n(You\'ll need your phone)'):
        trakt_result = trakt_auth(xbmcgui.DialogProgress())
    else:
        trakt_result = None

    # Step 5: Write TorBox key and Trakt tokens to McFenlight settings
    write_mcfenlight_settings(trakt_result)

    # Add McFenlight to Confluence skin home screen shortcut
    xbmc.executebuiltin('Skin.SetString(HomeVideosButton1,plugin.video.mcfenlight)')
    log('McFenlight added to home screen video shortcut 1')

    # Clean up home menu — hide unused items
    for item in ['LiveTV', 'Radio', 'Games', 'Weather', 'Pictures']:
        xbmc.executebuiltin('Skin.SetBool(HomeMenuNo%sButton)' % item)
    log('Hidden unused home menu items')

    # Done
    msg = 'McFenlight setup complete!\n\n'
    msg += 'TorBox: Ready (pre-configured)\n'
    msg += 'Trakt: %s\n' % ('Authorised' if trakt_result else 'Skipped — set up in McFenlight settings later')
    msg += '\nPlease restart Kodi now for everything to take effect.'
    ok_dialog.ok('McFenlight Setup', msg)

    log('Setup complete')


if __name__ == '__main__':
    main()
