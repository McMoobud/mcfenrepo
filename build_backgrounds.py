#!/usr/bin/env python3
"""Build the service.mcfenlight.backgrounds zip and sync repo metadata.

Packages the whole addon dir (including resources/), prunes old zips,
regenerates its index.html, then syncs the addon version in addons.xml
and regenerates addons.xml.md5. Leaves every other addon untouched.

Run on CT 110: python3 build_backgrounds.py
"""
import os
import re
import hashlib
import zipfile

REPO = '/mnt/files/Files/McFenRepo'
ADDON_ID = 'service.mcfenlight.backgrounds'


def version_from_addon_xml(addon_dir):
    text = open(os.path.join(addon_dir, 'addon.xml')).read()
    return re.search(r'id="%s"[^>]*\bversion="([^"]+)"' % re.escape(ADDON_ID), text).group(1)


def build_zip():
    addon_dir = os.path.join(REPO, ADDON_ID)
    version = version_from_addon_xml(addon_dir)
    target = os.path.join(addon_dir, '%s-%s.zip' % (ADDON_ID, version))
    if os.path.exists(target):
        os.remove(target)

    with zipfile.ZipFile(target, 'w', zipfile.ZIP_DEFLATED) as zf:
        for root, dirs, files in os.walk(addon_dir):
            dirs[:] = [d for d in dirs if d != '__pycache__']
            for f in files:
                if f.endswith('.zip') or f.endswith('.pyc') or f == 'index.html':
                    continue
                fp = os.path.join(root, f)
                arc = ADDON_ID + '/' + os.path.relpath(fp, addon_dir).replace(os.sep, '/')
                zf.write(fp, arc)
    print('Built %s (%d bytes)' % (os.path.basename(target), os.path.getsize(target)))
    with zipfile.ZipFile(target) as z:
        for i in z.infolist():
            print('  %s (%d)' % (i.filename, i.file_size))

    # prune any other backgrounds zips
    for fn in os.listdir(addon_dir):
        if fn.startswith(ADDON_ID + '-') and fn.endswith('.zip') and fn != os.path.basename(target):
            os.remove(os.path.join(addon_dir, fn))
            print('Pruned old %s' % fn)
    return version


def regen_dir_index():
    addon_dir = os.path.join(REPO, ADDON_ID)
    zips = [f for f in os.listdir(addon_dir) if f.endswith('.zip')]
    lines = ['<html><body>']
    lines += ['<a href="%s">%s</a>' % (z, z) for z in zips]
    lines += ['<a href="addon.xml">addon.xml</a>', '</body></html>', '']
    open(os.path.join(addon_dir, 'index.html'), 'w').write('\n'.join(lines))
    print('Regenerated %s/index.html' % ADDON_ID)


def sync_addons_xml(version):
    path = os.path.join(REPO, 'addons.xml')
    src_xml = open(os.path.join(REPO, ADDON_ID, 'addon.xml')).read()
    src_entry = re.search(r'<addon id="%s".*?</addon>' % re.escape(ADDON_ID),
                          src_xml, re.S).group(0)
    text = open(path).read()
    new_text, n = re.subn(r'<addon id="%s".*?</addon>' % re.escape(ADDON_ID),
                          src_entry.strip(), text, flags=re.S)
    if n:
        print('addons.xml: replaced %s entry (-> %s)' % (ADDON_ID, version))
    else:
        # insert before closing tag
        new_text = text.replace('</addons>', '    %s\n</addons>' % src_entry.strip())
        print('addons.xml: inserted %s entry (-> %s)' % (ADDON_ID, version))
    open(path, 'w').write(new_text)


def regen_md5():
    h = hashlib.md5(open(os.path.join(REPO, 'addons.xml'), 'rb').read()).hexdigest()
    open(os.path.join(REPO, 'addons.xml.md5'), 'w').write(h)
    print('Regenerated addons.xml.md5: %s' % h)


if __name__ == '__main__':
    v = build_zip()
    regen_dir_index()
    sync_addons_xml(v)
    regen_md5()
    print('--- done ---')
