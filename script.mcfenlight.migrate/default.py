# -*- coding: utf-8 -*-
import xbmc
import xbmcgui
import xbmcvfs
import json
import os
import sqlite3

ADDON_DATA = xbmcvfs.translatePath('special://profile/addon_data/')
TORBOX_API_KEY = '4136f32a-e795-40e3-bb87-b8bc8be65eca'


def log(msg):
    xbmc.log('###McFenlightMigrate###: %s' % str(msg), xbmc.LOGINFO)


def get_settings_db_path():
    return os.path.join(ADDON_DATA, 'plugin.video.mcfenlight', 'databases', 'settings.db')


def migrate_settings():
    db_path = get_settings_db_path()
    log('DB path: %s' % db_path)
    log('DB exists: %s' % os.path.exists(db_path))

    if not os.path.exists(db_path):
        return False, 'Settings DB not found at %s' % db_path

    try:
        conn = sqlite3.connect(db_path, timeout=30)
        conn.execute('PRAGMA journal_mode=WAL')
        c = conn.cursor()

        before = c.execute(
            'SELECT setting_id, setting_value FROM settings WHERE setting_id IN (?, ?, ?, ?, ?)',
            ('rd.enabled', 'tb.enabled', 'tb.token', 'provider.rd_cloud', 'provider.tb_cloud')
        ).fetchall()
        log('Before migration: %s' % str(before))

        def set_val(sid, stype, default, value):
            c.execute('INSERT OR REPLACE INTO settings VALUES (?, ?, ?, ?)',
                      (sid, stype, default, value))

        set_val('rd.enabled', 'boolean', 'false', 'false')
        set_val('provider.rd_cloud', 'boolean', 'false', 'false')
        set_val('tb.token', 'string', 'empty_setting', TORBOX_API_KEY)
        set_val('tb.enabled', 'boolean', 'false', 'true')
        set_val('provider.tb_cloud', 'boolean', 'false', 'true')
        set_val('provider.external', 'boolean', 'false', 'true')
        set_val('external_scraper.module', 'string', 'empty_setting', 'script.module.cocoscrapers')
        set_val('external_scraper.name', 'string', 'empty_setting', 'cocoscrapers')

        conn.commit()

        after = c.execute(
            'SELECT setting_id, setting_value FROM settings WHERE setting_id IN (?, ?, ?, ?, ?)',
            ('rd.enabled', 'tb.enabled', 'tb.token', 'provider.rd_cloud', 'provider.tb_cloud')
        ).fetchall()
        log('After migration: %s' % str(after))

        conn.close()

        xbmc.executebuiltin('RunPlugin(plugin://plugin.video.mcfenlight/?mode=sync_settings&silent=true)')
        xbmc.sleep(3000)
        log('Triggered McFenlight sync_settings reload')

        return True, 'DB updated. Settings: %s' % str(dict(after))

    except Exception as e:
        log('Migration error: %s' % str(e))
        return False, 'Database error: %s' % str(e)


def main():
    ok_dialog = xbmcgui.Dialog()

    if not ok_dialog.yesno(
        'McFenlight TorBox Migrator',
        'This will switch your debrid provider from Real-Debrid to TorBox.\n\n'
        'Your Trakt account, watch history, and all other settings are preserved.\n\n'
        'Real-Debrid credentials are kept but disabled (can be re-enabled later).\n\n'
        'Continue?'
    ):
        return

    db_path = get_settings_db_path()
    if not os.path.exists(db_path):
        ok_dialog.ok(
            'McFenlight TorBox Migrator',
            'McFenlight settings database not found at:\n%s\n\n'
            'Make sure McFenlight is installed and has been opened at least once.' % db_path
        )
        return

    log('Starting RD to TorBox migration')
    success, detail = migrate_settings()

    if success:
        for item in ['LiveTV', 'Radio', 'Games', 'Weather', 'Pictures']:
            xbmc.executebuiltin('Skin.SetBool(HomeMenuNo%sButton)' % item)
        log('Hidden unused home menu items')

        ok_dialog.ok(
            'McFenlight TorBox Migrator',
            'Migration complete!\n\n'
            'Real-Debrid: Disabled\n'
            'TorBox: Enabled and ready\nCocoScrapers: Enabled\n\n'
            'Please restart Kodi for changes to take full effect.'
        )
        log('Migration complete: %s' % detail)
    else:
        ok_dialog.ok(
            'McFenlight TorBox Migrator',
            'Migration failed!\n\n%s' % detail
        )
        log('Migration failed: %s' % detail)


if __name__ == '__main__':
    main()
