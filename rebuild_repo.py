#!/usr/bin/env python3
"""Prune deprecated addons, archive one-off tooling, rebuild repo metadata.

Survivors: repository.mcfenlight, plugin.video.mcfenlight,
           script.mcfenlight.setup, service.mcfenlight.backgrounds
Removed:   script.mcfenlight.wizard, script.mcfenlight.migrate,
           script.mcfenlight.emby
Archived helper scripts -> archive/

Run on CT 110: python3 rebuild_repo.py
"""
import os
import re
import shutil
import hashlib
import zipfile

REPO = '/mnt/files/Files/McFenRepo'

SURVIVORS = [
    'repository.mcfenlight',
    'plugin.video.mcfenlight',
    'script.mcfenlight.setup',
    'service.mcfenlight.backgrounds',
    'script.mcfenlight.emby',
]
REMOVE_DIRS = [
    'script.mcfenlight.wizard',
    'script.mcfenlight.migrate',
]
REMOVE_FILES = [
    'script.mcfenlight.wizard-1.0.0.zip',
]
ARCHIVE_SCRIPTS = [
    'build_all_wizards.py', 'build_wizard_zip.py',
    'fix_repo2.py', 'fix_repo3.py',
    'rebuild_plugin.py', 'update_trakt.py',
]


def version_of(addon_id):
    xml = open(os.path.join(REPO, addon_id, 'addon.xml')).read()
    return re.search(r'id="%s"[^>]*\bversion="([^"]+)"' % re.escape(addon_id), xml).group(1)


def build_zip(addon_id):
    addon_dir = os.path.join(REPO, addon_id)
    version = version_of(addon_id)
    target = os.path.join(addon_dir, '%s-%s.zip' % (addon_id, version))
    if os.path.exists(target):
        os.remove(target)
    with zipfile.ZipFile(target, 'w', zipfile.ZIP_DEFLATED) as zf:
        for root, dirs, files in os.walk(addon_dir):
            dirs[:] = [d for d in dirs if d != '__pycache__']
            for f in files:
                if f.endswith('.zip') or f.endswith('.pyc') or f == 'index.html':
                    continue
                fp = os.path.join(root, f)
                arc = addon_id + '/' + os.path.relpath(fp, addon_dir).replace(os.sep, '/')
                zf.write(fp, arc)
    # prune other zips of this addon
    for fn in os.listdir(addon_dir):
        if fn.startswith(addon_id + '-') and fn.endswith('.zip') and fn != os.path.basename(target):
            os.remove(os.path.join(addon_dir, fn))
    print('Built %s-%s.zip' % (addon_id, version))
    return version


def regen_dir_index(addon_id):
    addon_dir = os.path.join(REPO, addon_id)
    zips = [f for f in os.listdir(addon_dir) if f.endswith('.zip')]
    lines = ['<html><body>']
    lines += ['<a href="%s">%s</a>' % (z, z) for z in zips]
    lines += ['<a href="addon.xml">addon.xml</a>', '</body></html>', '']
    open(os.path.join(addon_dir, 'index.html'), 'w').write('\n'.join(lines))


def prune():
    for d in REMOVE_DIRS:
        p = os.path.join(REPO, d)
        if os.path.isdir(p):
            shutil.rmtree(p)
            print('Removed dir %s' % d)
    for f in REMOVE_FILES:
        p = os.path.join(REPO, f)
        if os.path.exists(p):
            os.remove(p)
            print('Removed file %s' % f)


def archive_scripts():
    arch = os.path.join(REPO, 'archive')
    os.makedirs(arch, exist_ok=True)
    for s in ARCHIVE_SCRIPTS:
        p = os.path.join(REPO, s)
        if os.path.exists(p):
            shutil.move(p, os.path.join(arch, s))
            print('Archived %s' % s)


def rebuild_addons_xml():
    blocks = []
    for addon_id in SURVIVORS:
        xml = open(os.path.join(REPO, addon_id, 'addon.xml')).read()
        m = re.search(r'<addon\s+id=.*?</addon>', xml, re.S)
        block = m.group(0)
        block = '\n'.join('    ' + line for line in block.splitlines())
        blocks.append(block)
    content = '<?xml version="1.0" encoding="UTF-8"?>\n<addons>\n' + '\n'.join(blocks) + '\n</addons>\n'
    open(os.path.join(REPO, 'addons.xml'), 'w').write(content)
    h = hashlib.md5(content.encode('utf-8')).hexdigest()
    open(os.path.join(REPO, 'addons.xml.md5'), 'w').write(h)
    print('Rebuilt addons.xml (%d addons), md5 %s' % (len(blocks), h))


def root_index():
    setup_v = version_of('script.mcfenlight.setup')
    plugin_v = version_of('plugin.video.mcfenlight')
    lines = [
        '<html><body>',
        '<a href="repository.mcfenlight/">repository.mcfenlight/</a>',
        '<a href="plugin.video.mcfenlight/">plugin.video.mcfenlight/ (%s)</a>' % plugin_v,
        '<a href="script.mcfenlight.setup/">script.mcfenlight.setup/</a>',
        '<a href="script.mcfenlight.setup/script.mcfenlight.setup-%s.zip">McFenlight Setup (%s)</a>' % (setup_v, setup_v),
        '<a href="service.mcfenlight.backgrounds/">service.mcfenlight.backgrounds/</a>',
        '<a href="script.mcfenlight.emby/">script.mcfenlight.emby/ (optional Emby installer)</a>',
        '<a href="addons.xml">addons.xml</a>',
        '<a href="addons.xml.md5">addons.xml.md5</a>',
        '</body></html>', '',
    ]
    open(os.path.join(REPO, 'index.html'), 'w').write('\n'.join(lines))
    print('Rebuilt root index.html')


if __name__ == '__main__':
    prune()
    archive_scripts()
    build_zip('script.mcfenlight.setup')
    regen_dir_index('script.mcfenlight.setup')
    rebuild_addons_xml()
    root_index()
    print('--- done ---')
