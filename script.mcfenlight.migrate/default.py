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
    if not os.path.exists(db_path):
        log('Settings DB not found at %s' % db_path)
        return False

    conn = sqlite3.connect(db_path, timeout=20)
    c = conn.cursor()

    def set_val(sid, stype, default, value):
        c.execute('INSERT OR REPLACE INTO settings VALUES (?, ?, ?, ?)',
                  (sid, stype, default, value))

    set_val('rd.enabled', 'boolean', 'false', 'false')
    set_val('provider.rd_cloud', 'boolean', 'false', 'false')

    set_val('tb.token', 'string', 'empty_setting', TORBOX_API_KEY)
    set_val('tb.enabled', 'boolean', 'false', 'true')
    set_val('provider.tb_cloud', 'boolean', 'false', 'true')

    conn.commit()

    verify = c.execute(
        'SELECT setting_id, setting_value FROM settings WHERE setting_id IN (?, ?, ?, ?, ?)',
        ('rd.enabled', 'tb.enabled', 'tb.token', 'provider.rd_cloud', 'provider.tb_cloud')
    ).fetchall()
    log('Verified settings: %s' % str(verify))
    conn.close()

    xbmc.executebuiltin('RunPlugin(plugin://plugin.video.mcfenlight/?mode=sync_settings&silent=true)')
    xbmc.sleep(3000)
    log('Triggered McFenlight sync_settings reload')
    return True


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
            'McFenlight settings database not found.\n\n'
            'Make sure McFenlight is installed and has been opened at least once before running this migrator.'
        )
        return

    log('Starting RD to TorBox migration')
    success = migrate_settings()

    if success:
        ok_dialog.ok(
            'McFenlight TorBox Migrator',
            'Migration complete!\n\n'
            'Real-Debrid: Disabled (credentials preserved)\n'
            'TorBox: Enabled and ready\n\n'
            'No restart required — changes are active now.'
        )
        log('Migration complete')
    else:
        ok_dialog.ok(
            'McFenlight TorBox Migrator',
            'Migration failed. Check the Kodi log for details.'
        )
        log('Migration failed')


if __name__ == '__main__':
    main()
