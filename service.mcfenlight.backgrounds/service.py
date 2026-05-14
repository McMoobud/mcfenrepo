# -*- coding: utf-8 -*-
import xbmc
import xbmcvfs
import xbmcaddon
import os
import shutil


def log(msg):
    xbmc.log('###McFenlightBG###: %s' % str(msg), xbmc.LOGINFO)


def install_backgrounds():
    addon = xbmcaddon.Addon('service.mcfenlight.backgrounds')
    addon_path = addon.getAddonInfo('path')

    splash_src = os.path.join(addon_path, 'splash.png')
    bg_src = os.path.join(addon_path, 'background.jpg')

    # Splash screen
    media_dir = xbmcvfs.translatePath('special://home/media/')
    splash_dest = os.path.join(media_dir, 'Splash.png')
    try:
        os.makedirs(media_dir, exist_ok=True)
        shutil.copy2(splash_src, splash_dest)
        log('Splash screen installed to %s' % splash_dest)
    except Exception as e:
        log('Failed to install splash: %s' % str(e))

    # Background — copy to persistent location and set skin setting
    bg_dir = xbmcvfs.translatePath('special://profile/addon_data/service.mcfenlight.backgrounds/')
    bg_dest = os.path.join(bg_dir, 'background.jpg')
    try:
        os.makedirs(bg_dir, exist_ok=True)
        shutil.copy2(bg_src, bg_dest)
        xbmc.executebuiltin('Skin.SetString(CustomBackgroundPath,%s)' % bg_dest)
        xbmc.executebuiltin('Skin.SetBool(UseCustomBackground)')
        log('Background set to %s' % bg_dest)
    except Exception as e:
        log('Failed to install background: %s' % str(e))


if __name__ == '__main__':
    monitor = xbmc.Monitor()
    monitor.waitForAbort(5)
    if not monitor.abortRequested():
        try:
            install_backgrounds()
        except Exception as e:
            log('FATAL: %s' % str(e))
