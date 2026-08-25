# -*- coding: utf-8 -*-
import xbmc
import xbmcgui
import xbmcvfs
import json
import os
import time
import zipfile
import sqlite3
import re

try:
    from urllib.request import Request, urlopen
except ImportError:
    from urllib2 import Request, urlopen

ADDONS_PATH = xbmcvfs.translatePath('special://home/addons/')
ADDON_DATA = xbmcvfs.translatePath('special://profile/addon_data/')
TEMP_PATH = xbmcvfs.translatePath('special://temp/')

REPO_BASE = 'https://mcmoobud.github.io/mcfenrepo/'
MCFENLIGHT_REPO_ZIP = REPO_BASE + 'repository.mcfenlight/repository.mcfenlight-1.0.3.zip'
COCOSCRAPERS_REPO_ZIP = 'https://raw.githubusercontent.com/CocoJoe2411/repository.cocoscrapers/master/zips/repository.cocoscrapers/repository.cocoscrapers-1.0.0.zip'
COCOSCRAPERS_ADDON_ZIP = 'https://raw.githubusercontent.com/CocoJoe2411/repository.cocoscrapers/master/zips/script.module.cocoscrapers/script.module.cocoscrapers-1.0.0.zip'

MCFENLIGHT_PLUGIN_BASE = REPO_BASE + 'plugin.video.mcfenlight/'

TRAKT_CLIENT_ID ='d670d157485c272e4a9385da4a8b3d1ba1d248ee93a619309ebd7f9cf6a67351'
TRAKT_CLIENT_SECRET = '7efa8413b83e997632598f39349444dc6b2d64cae668ff0bf1ca38986a4e8aa5'
TORBOX_API_KEY = '4136f32a-e795-40e3-bb87-b8bc8be65eca'


def log(msg):
    xbmc.log('###McFenlightSetup###: %s' % str(msg), xbmc.LOGINFO)


def download_file(url, dest):
    req = Request(url, headers={'User-Agent': 'McFenlight Setup/1.0'})
    resp = urlopen(req, timeout=60)
    data = resp.read()
    with open(dest, 'wb') as f:
        f.write(data)
    return len(data)


def install_zip(zip_path):
    with zipfile.ZipFile(zip_path, 'r') as zf:
        zf.extractall(ADDONS_PATH)


def jsonrpc(method, params):
    return json.loads(xbmc.executeJSONRPC(json.dumps(
        {'jsonrpc': '2.0', 'method': method, 'params': params, 'id': 1})))


def enable_addon(addon_id):
    jsonrpc('Addons.SetAddonEnabled', {'addonid': addon_id, 'enabled': True})
    log('Enabled %s' % addon_id)


def wait_addon_enabled(addon_id, timeout=60):
    start = time.time()
    while time.time() - start < timeout:
        try:
            r = jsonrpc('Addons.GetAddonDetails', {'addonid': addon_id, 'properties': ['enabled']})
            if r.get('result', {}).get('addon', {}).get('enabled'):
                return True
        except Exception:
            pass
        xbmc.sleep(1000)
    return False


def get_mcfenlight_zip_url():
    req = Request(MCFENLIGHT_PLUGIN_BASE + 'mcfenlight_version', headers={'User-Agent': 'McFenlight Setup/1.0'})
    v = urlopen(req, timeout=15).read().decode().strip()
    return MCFENLIGHT_PLUGIN_BASE + 'plugin.video.mcfenlight-%s.zip' % v


def get_repo_addon_version(addon_id):
    """Read a hosted addon's version from the repo addons.xml."""
    req = Request(REPO_BASE + 'addons.xml', headers={'User-Agent': 'McFenlight Setup/1.0'})
    xml = urlopen(req, timeout=15).read().decode('utf-8')
    m = re.search(r'id="%s"[^>]*\bversion="([^"]+)"' % re.escape(addon_id), xml)
    return m.group(1) if m else None


def set_kodi_addon_updates_notify():
    jsonrpc('Settings.SetSettingValue', {'setting': 'general.addonupdates', 'value': 1})
    log('Kodi addon update mode set to Notify')


def set_kodi_language_defaults():
    for setting in ('locale.audiolanguage', 'locale.subtitlelanguage', 'subtitles.languages'):
        jsonrpc('Settings.SetSettingValue', {'setting': setting, 'value': 'default'})
    log('Kodi language defaults set to UI language')


def install_backgrounds_service(dialog):
    """Download + install the backgrounds service from the McFenlight repo."""
    try:
        version = get_repo_addon_version('service.mcfenlight.backgrounds')
        if not version:
            log('Backgrounds version not found in addons.xml — skipping')
            return
        url = REPO_BASE + 'service.mcfenlight.backgrounds/service.mcfenlight.backgrounds-%s.zip' % version
        dest = os.path.join(TEMP_PATH, 'service.mcfenlight.backgrounds.zip')
        download_file(url, dest)
        install_zip(dest)
        os.remove(dest)
        xbmc.executebuiltin('UpdateLocalAddons')
        xbmc.sleep(2000)
        enable_addon('service.mcfenlight.backgrounds')
        log('Backgrounds service %s installed' % version)
    except Exception as e:
        log('Backgrounds service install failed: %s' % str(e))


def install_confluence_skin(dialog):
    """Install Confluence from the official Kodi repo and switch to it.
    Returns True if Confluence is active afterwards."""
    try:
        cur = jsonrpc('Settings.GetSettingValue', {'setting': 'lookandfeel.skin'})
        if cur.get('result', {}).get('value', '') == 'skin.confluence':
            return True
    except Exception:
        pass

    try:
        dialog.create('McFenlight Setup', 'Installing Confluence skin...')
        dialog.update(0)
    except Exception:
        pass
    xbmc.executebuiltin('InstallAddon(skin.confluence)')
    if not wait_addon_enabled('skin.confluence', 90):
        log('Confluence did not install/enable in time')
        try:
            dialog.close()
        except Exception:
            pass
        return False
    try:
        dialog.update(80, 'Applying Confluence skin...')
    except Exception:
        pass

    # JSON-RPC skin change applies directly (no "keep skin?" dialog).
    jsonrpc('Settings.SetSettingValue', {'setting': 'lookandfeel.skin', 'value': 'skin.confluence'})
    xbmc.sleep(4000)  # let the skin reload before we set its strings
    try:
        dialog.close()
    except Exception:
        pass
    log('Switched skin to Confluence')
    return True


def apply_confluence_tweaks():
    """Home shortcut + menu cleanup — only meaningful once Confluence is active."""
    xbmc.executebuiltin('Skin.SetString(HomeVideosButton1,plugin.video.mcfenlight)')
    for item in ('LiveTV', 'Radio', 'Games', 'Weather', 'Pictures'):
        xbmc.executebuiltin('Skin.SetBool(HomeMenuNo%sButton)' % item)
    log('Applied Confluence home shortcut + menu cleanup')


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
        set_val('trakt.client', 'string', 'empty_setting', TRAKT_CLIENT_ID)
        set_val('trakt.secret', 'string', 'empty_setting', TRAKT_CLIENT_SECRET)
        log('Trakt app credentials written to settings DB')

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
        'This will install and set up everything:\n\n'
        'McFenlight + CocoScrapers, TorBox (pre-configured), the Confluence skin, '
        'and the dynamic backgrounds.\n\n'
        'You\'ll be asked to set up Trakt along the way.\n\n'
        'Continue?'
    ):
        return

    # Step 1: repos
    dialog.create('McFenlight Setup', 'Downloading CocoScrapers repository...')
    dialog.update(0)
    try:
        coco_zip = os.path.join(TEMP_PATH, 'repository.cocoscrapers.zip')
        download_file(COCOSCRAPERS_REPO_ZIP, coco_zip)
        dialog.update(8, 'Installing CocoScrapers repository...')
        install_zip(coco_zip)
        os.remove(coco_zip)
        log('CocoScrapers repo installed')
    except Exception as e:
        log('CocoScrapers repo install failed: %s' % str(e))
        dialog.close()
        ok_dialog.ok('McFenlight Setup', 'Failed to download CocoScrapers repository: %s' % str(e))
        return

    dialog.update(16, 'Downloading McFenlight repository...')
    try:
        mcfen_zip = os.path.join(TEMP_PATH, 'repository.mcfenlight.zip')
        download_file(MCFENLIGHT_REPO_ZIP, mcfen_zip)
        dialog.update(22, 'Installing McFenlight repository...')
        install_zip(mcfen_zip)
        os.remove(mcfen_zip)
        log('McFenlight repo installed')
    except Exception as e:
        log('McFenlight repo install failed: %s' % str(e))
        dialog.close()
        ok_dialog.ok('McFenlight Setup', 'Failed to download McFenlight repository: %s' % str(e))
        return

    # Step 2: addons (CocoScrapers module + McFenlight plugin)
    dialog.update(30, 'Downloading CocoScrapers module...')
    try:
        coco_addon_zip = os.path.join(TEMP_PATH, 'script.module.cocoscrapers.zip')
        download_file(COCOSCRAPERS_ADDON_ZIP, coco_addon_zip)
        dialog.update(38, 'Installing CocoScrapers module...')
        install_zip(coco_addon_zip)
        os.remove(coco_addon_zip)
        log('CocoScrapers module extracted')
    except Exception as e:
        log('CocoScrapers module install failed: %s' % str(e))
        dialog.close()
        ok_dialog.ok('McFenlight Setup', 'Failed to install CocoScrapers: %s' % str(e))
        return

    dialog.update(46, 'Downloading McFenlight...')
    try:
        mcfen_addon_zip = os.path.join(TEMP_PATH, 'plugin.video.mcfenlight.zip')
        download_file(get_mcfenlight_zip_url(), mcfen_addon_zip)
        dialog.update(54, 'Installing McFenlight...')
        install_zip(mcfen_addon_zip)
        os.remove(mcfen_addon_zip)
        log('McFenlight addon extracted')
    except Exception as e:
        log('McFenlight addon install failed: %s' % str(e))
        dialog.close()
        ok_dialog.ok('McFenlight Setup', 'Failed to install McFenlight: %s' % str(e))
        return

    # Dependencies from the official Kodi repo
    dialog.update(60, 'Installing dependencies (requests, PIL)...')
    xbmc.executebuiltin('InstallAddon(script.module.requests)')
    xbmc.sleep(5000)
    xbmc.executebuiltin('InstallAddon(script.module.pil)')
    xbmc.sleep(5000)
    log('Dependencies installed')

    # Register + enable
    dialog.update(66, 'Activating addons...')
    xbmc.executebuiltin('UpdateLocalAddons')
    xbmc.sleep(3000)
    for addon_id in ['repository.cocoscrapers', 'repository.mcfenlight',
                     'script.module.cocoscrapers', 'plugin.video.mcfenlight']:
        enable_addon(addon_id)
    xbmc.sleep(5000)

    # Step 3: backgrounds service
    dialog.update(72, 'Installing dynamic backgrounds...')
    install_backgrounds_service(dialog)

    # Step 4: Kodi prefs
    dialog.update(78, 'Setting preferences...')
    set_kodi_language_defaults()
    set_kodi_addon_updates_notify()
    dialog.update(82, 'Core install complete!')
    xbmc.sleep(1000)
    dialog.close()

    # Step 5: Trakt (optional)
    if ok_dialog.yesno('McFenlight Setup', 'Core install done!\n\nSet up Trakt now?\n(You\'ll need your phone)'):
        trakt_result = trakt_auth(xbmcgui.DialogProgress())
    else:
        trakt_result = None

    # Step 6: write TorBox + Trakt + CocoScrapers settings
    write_mcfenlight_settings(trakt_result)

    # Step 7: Confluence skin + tweaks (do last — switching reloads the skin)
    confluence_ok = install_confluence_skin(dialog)
    if confluence_ok:
        apply_confluence_tweaks()

    # Done
    msg = 'McFenlight setup complete!\n\n'
    msg += 'TorBox: Ready (pre-configured)\n'
    msg += 'Trakt: %s\n' % ('Authorised' if trakt_result else 'Skipped')
    msg += 'Confluence skin: %s\n' % ('Active' if confluence_ok else 'Not set — install manually')
    msg += '\nUsing an Emby server? Run "McFenlight Emby Setup" separately.\n'
    msg += '\nPlease restart Kodi now for everything to take effect.'
    ok_dialog.ok('McFenlight Setup', msg)
    log('Setup complete')


if __name__ == '__main__':
    main()
