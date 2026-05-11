# -*- coding: utf-8 -*-
import xbmc
import xbmcgui
import xbmcvfs
import xbmcaddon
import json
import os
import time
import zipfile
import sqlite3

try:
    from urllib.request import Request, urlopen
except ImportError:
    from urllib2 import Request, urlopen

ADDON = xbmcaddon.Addon()
ADDON_PATH = xbmcvfs.translatePath(ADDON.getAddonInfo('path'))
ADDONS_PATH = xbmcvfs.translatePath('special://home/addons/')
ADDON_DATA = xbmcvfs.translatePath('special://profile/addon_data/')
TEMP_PATH = xbmcvfs.translatePath('special://temp/')

MCFENLIGHT_REPO_ZIP = 'https://mcmoobud.github.io/mcfenrepo/repository.mcfenlight/repository.mcfenlight-1.0.3.zip'
COCOSCRAPERS_REPO_ZIP = 'https://raw.githubusercontent.com/CocoJoe2411/repository.cocoscrapers/master/zips/repository.cocoscrapers/repository.cocoscrapers-1.0.0.zip'
EMBY_REPO_ZIP = 'https://embydata.com/downloads/addons/xbmb3c/multi-repo/repositories/repository.emby.kodi/repository.emby.kodi-1.0.8.zip'

TRAKT_CLIENT_ID = 'd670d157485c272e4a9385da4a8b3d1ba1d248ee93a619309ebd7f9cf6a67351'
TRAKT_CLIENT_SECRET = '7efa8413b83e997632598f39349444dc6b2d64cae668ff0bf1ca38986a4e8aa5'


def log(msg):
    xbmc.log('###McFenlightWizard###: %s' % str(msg), xbmc.LOGINFO)


def download_file(url, dest):
    req = Request(url, headers={'User-Agent': 'McFenlight Wizard/1.0'})
    resp = urlopen(req, timeout=30)
    data = resp.read()
    with open(dest, 'wb') as f:
        f.write(data)
    return len(data)


def install_zip(zip_path):
    with zipfile.ZipFile(zip_path, 'r') as zf:
        zf.extractall(ADDONS_PATH)


def wait_for_addon(addon_id, timeout=30):
    start = time.time()
    while time.time() - start < timeout:
        if xbmc.getCondVisibility('System.HasAddon(%s)' % addon_id):
            return True
        xbmc.sleep(500)
    return False


def install_addon_from_repo(addon_id):
    xbmc.executebuiltin('InstallAddon(%s)' % addon_id)
    return wait_for_addon(addon_id, timeout=60)


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
        xbmcgui.Dialog().ok('McFenlight Wizard', 'Could not contact Trakt. Skipping — you can authorise later in McFenlight settings.')
        return None

    user_code = device['user_code']
    expires_in = device.get('expires_in', 600)
    interval = device.get('interval', 5)

    dialog.create(
        'McFenlight Wizard — Trakt',
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
    xbmcgui.Dialog().ok('McFenlight Wizard', 'Trakt authorisation timed out. You can authorise later in McFenlight settings.')
    return None


def realdebrid_auth(dialog):
    log('Starting Real-Debrid auth')
    try:
        req = Request('https://api.real-debrid.com/oauth/v2/device/code?client_id=X245A4XAIBGVM&new_credentials=yes',
                      headers={'User-Agent': 'McFenlight for Kodi'})
        resp = urlopen(req, timeout=10)
        device = json.loads(resp.read().decode('utf-8'))
    except Exception as e:
        log('RD device code error: %s' % str(e))
        xbmcgui.Dialog().ok('McFenlight Wizard', 'Could not contact Real-Debrid. Skipping — you can authorise later in McFenlight settings.')
        return None

    user_code = device['user_code']
    verification_url = device.get('verification_url', 'https://real-debrid.com/device')
    expires_in = device.get('expires_in', 600)
    interval = device.get('interval', 5)

    dialog.create(
        'McFenlight Wizard — Real-Debrid',
        'Go to [B]%s[/B] on your phone\n\nEnter code: [B]%s[/B]\n\nWaiting for approval...' % (verification_url, user_code)
    )

    start = time.time()
    while time.time() - start < expires_in:
        if dialog.iscanceled():
            log('RD auth cancelled by user')
            dialog.close()
            return None
        xbmc.sleep(interval * 1000)
        elapsed = int(time.time() - start)
        dialog.update(int(elapsed * 100 / expires_in))
        try:
            check_url = 'https://api.real-debrid.com/oauth/v2/device/credentials?client_id=X245A4XAIBGVM&code=%s' % device['device_code']
            req = Request(check_url, headers={'User-Agent': 'McFenlight for Kodi'})
            resp = urlopen(req, timeout=10)
            creds = json.loads(resp.read().decode('utf-8'))
            if creds.get('client_id'):
                token_data = 'client_id=%s&client_secret=%s&code=%s&grant_type=http://oauth.net/grant_type/device/1.0' % (
                    creds['client_id'], creds['client_secret'], device['device_code']
                )
                req2 = Request('https://api.real-debrid.com/oauth/v2/token',
                               data=token_data.encode('utf-8'),
                               headers={'Content-Type': 'application/x-www-form-urlencoded',
                                        'User-Agent': 'McFenlight for Kodi'})
                resp2 = urlopen(req2, timeout=10)
                token = json.loads(resp2.read().decode('utf-8'))
                dialog.close()
                log('RD auth success')
                return {
                    'client_id': creds['client_id'],
                    'client_secret': creds['client_secret'],
                    'token': token.get('access_token', ''),
                    'refresh': token.get('refresh_token', '')
                }
        except Exception:
            pass

    dialog.close()
    xbmcgui.Dialog().ok('McFenlight Wizard', 'Real-Debrid authorisation timed out. You can authorise later in McFenlight settings.')
    return None


def write_mcfenlight_settings(trakt_result, rd_result):
    db_dir = os.path.join(ADDON_DATA, 'plugin.video.mcfenlight', 'databases')
    os.makedirs(db_dir, exist_ok=True)
    db_path = os.path.join(db_dir, 'settings.db')

    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.execute('CREATE TABLE IF NOT EXISTS settings (setting_id TEXT PRIMARY KEY, setting_type TEXT, setting_default TEXT, setting_value TEXT)')

    def set_val(sid, stype, default, value):
        c.execute('INSERT OR REPLACE INTO settings (setting_id, setting_type, setting_default, setting_value) VALUES (?, ?, ?, ?)',
                  (sid, stype, default, value))

    if trakt_result:
        set_val('trakt.token', 'string', 'empty_setting', trakt_result.get('access_token', ''))
        set_val('trakt.refresh', 'string', 'empty_setting', trakt_result.get('refresh_token', ''))
        expires = str(time.time() + trakt_result.get('expires_in', 7776000))
        set_val('trakt.expires', 'string', '0', expires)
        set_val('trakt.user', 'string', 'empty_setting', 'true')
        log('Trakt tokens written to settings DB')

    if rd_result:
        set_val('rd.client_id', 'string', 'empty_setting', rd_result.get('client_id', ''))
        set_val('rd.secret', 'string', 'empty_setting', rd_result.get('client_secret', ''))
        set_val('rd.token', 'string', 'empty_setting', rd_result.get('token', ''))
        set_val('rd.refresh', 'string', 'empty_setting', rd_result.get('refresh', ''))
        set_val('rd.account_id', 'string', 'empty_setting', 'true')
        log('RD tokens written to settings DB')

    conn.commit()
    conn.close()


def main():
    dialog = xbmcgui.DialogProgress()
    ok_dialog = xbmcgui.Dialog()

    if not ok_dialog.yesno('McFenlight Wizard',
                           'This will install McFenlight and everything it needs.\n\n'
                           'You\'ll be asked to authorise Trakt and Real-Debrid on your phone.\n\n'
                           'Continue?'):
        return

    install_emby = ok_dialog.yesno('McFenlight Wizard',
                                   'Would you also like to install Emby for Kodi?\n\n'
                                   '(For streaming your own media library via Emby Server)')

    # Step 1: Download and install repos
    dialog.create('McFenlight Wizard', 'Downloading CocoScrapers repository...')
    dialog.update(0)
    try:
        coco_zip = os.path.join(TEMP_PATH, 'repository.cocoscrapers.zip')
        download_file(COCOSCRAPERS_REPO_ZIP, coco_zip)
        dialog.update(15, 'Installing CocoScrapers repository...')
        install_zip(coco_zip)
        os.remove(coco_zip)
        log('CocoScrapers repo installed')
    except Exception as e:
        log('CocoScrapers repo install failed: %s' % str(e))
        dialog.close()
        ok_dialog.ok('McFenlight Wizard', 'Failed to download CocoScrapers repository: %s' % str(e))
        return

    dialog.update(25, 'Downloading McFenlight repository...')
    try:
        mcfen_zip = os.path.join(TEMP_PATH, 'repository.mcfenlight.zip')
        download_file(MCFENLIGHT_REPO_ZIP, mcfen_zip)
        dialog.update(40, 'Installing McFenlight repository...')
        install_zip(mcfen_zip)
        os.remove(mcfen_zip)
        log('McFenlight repo installed')
    except Exception as e:
        log('McFenlight repo install failed: %s' % str(e))
        dialog.close()
        ok_dialog.ok('McFenlight Wizard', 'Failed to download McFenlight repository: %s' % str(e))
        return

    # Refresh addon list
    dialog.update(50, 'Refreshing addon list...')
    xbmc.executebuiltin('UpdateLocalAddons')
    xbmc.sleep(3000)

    # Step 2: Install addons from repos
    dialog.update(55, 'Installing CocoScrapers module...')
    xbmc.executebuiltin('InstallAddon(script.module.cocoscrapers)')
    xbmc.sleep(5000)

    dialog.update(60, 'Installing McFenlight...')
    xbmc.executebuiltin('InstallAddon(plugin.video.mcfenlight)')
    xbmc.sleep(5000)

    # Optional: Install Emby
    if install_emby:
        dialog.update(68, 'Downloading Emby repository...')
        try:
            emby_zip = os.path.join(TEMP_PATH, 'repository.emby.kodi.zip')
            download_file(EMBY_REPO_ZIP, emby_zip)
            dialog.update(72, 'Installing Emby repository...')
            install_zip(emby_zip)
            os.remove(emby_zip)
            xbmc.executebuiltin('UpdateLocalAddons')
            xbmc.sleep(3000)
            dialog.update(76, 'Installing Emby for Kodi...')
            xbmc.executebuiltin('InstallAddon(plugin.video.emby-next-gen)')
            xbmc.sleep(5000)
            xbmc.executebuiltin('InstallAddon(plugin.service.emby-next-gen)')
            xbmc.sleep(5000)
            log('Emby addons installed')
        except Exception as e:
            log('Emby install failed: %s' % str(e))
            ok_dialog.notification('McFenlight Wizard', 'Emby install failed — you can install it manually later')

    # Step 3: Set Kodi language defaults
    dialog.update(85, 'Setting language preferences...')
    set_kodi_language_defaults()

    dialog.update(90, 'Addon installation complete!')
    xbmc.sleep(1000)
    dialog.close()

    # Step 4: Trakt auth
    if ok_dialog.yesno('McFenlight Wizard', 'Addons installed!\n\nWould you like to set up Trakt now?\n(You\'ll need your phone)'):
        trakt_result = trakt_auth(xbmcgui.DialogProgress())
    else:
        trakt_result = None

    # Step 5: Real-Debrid auth
    if ok_dialog.yesno('McFenlight Wizard', 'Would you like to set up Real-Debrid now?\n(You\'ll need your phone)'):
        rd_result = realdebrid_auth(xbmcgui.DialogProgress())
    else:
        rd_result = None

    # Step 6: Write tokens to McFenlight settings
    if trakt_result or rd_result:
        write_mcfenlight_settings(trakt_result, rd_result)

    # Done
    msg = 'McFenlight setup complete!\n\n'
    msg += 'Trakt: %s\n' % ('Authorised' if trakt_result else 'Skipped — set up in McFenlight settings later')
    msg += 'Real-Debrid: %s\n' % ('Authorised' if rd_result else 'Skipped — set up in McFenlight settings later')
    if install_emby:
        msg += 'Emby: Installed — run it from Add-ons to connect to your server\n'
    msg += '\nPlease restart Kodi now for everything to take effect.'
    ok_dialog.ok('McFenlight Wizard', msg)

    log('Wizard complete')


if __name__ == '__main__':
    main()
