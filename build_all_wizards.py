#!/usr/bin/env python3
"""Build zip files for all McFenlight wizards, update addons.xml and index.html."""
import os
import zipfile
import hashlib
import xml.etree.ElementTree as ET

BASE = '/mnt/files/Files/McFenRepo'

WIZARDS = [
    ('script.mcfenlight.setup', '1.0.0'),
    ('script.mcfenlight.migrate', '1.0.0'),
    ('script.mcfenlight.emby', '1.0.0'),
]


def build_zip(addon_id, version):
    addon_dir = os.path.join(BASE, addon_id)
    zip_name = '%s-%s.zip' % (addon_id, version)
    zip_path = os.path.join(BASE, addon_id, zip_name)
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zf:
        for fn in os.listdir(addon_dir):
            fp = os.path.join(addon_dir, fn)
            if os.path.isfile(fp) and not fn.endswith('.zip'):
                zf.write(fp, '%s/%s' % (addon_id, fn))
    size = os.path.getsize(zip_path)
    print('Built %s (%d bytes)' % (zip_name, size))
    with zipfile.ZipFile(zip_path) as z:
        for i in z.infolist():
            print('  %s (%d)' % (i.filename, i.file_size))
    return zip_path


def update_addons_xml():
    addons_path = os.path.join(BASE, 'addons.xml')
    tree = ET.parse(addons_path)
    root = tree.getroot()

    existing_ids = {addon.get('id') for addon in root.findall('addon')}

    for addon_id, version in WIZARDS:
        if addon_id in existing_ids:
            print('Addon %s already in addons.xml, skipping' % addon_id)
            continue
        addon_xml_path = os.path.join(BASE, addon_id, 'addon.xml')
        addon_tree = ET.parse(addon_xml_path)
        addon_elem = addon_tree.getroot()
        root.append(addon_elem)
        print('Added %s to addons.xml' % addon_id)

    # Also update the old wizard name if not already done
    for addon in root.findall('addon'):
        if addon.get('id') == 'script.mcfenlight.wizard':
            if '(Deprecated)' not in addon.get('name', ''):
                addon.set('name', 'McFenlight Wizard (Deprecated)')
                print('Marked old wizard as deprecated in addons.xml')

    tree.write(addons_path, encoding='unicode', xml_declaration=True)

    # Read back and generate MD5
    with open(addons_path, 'r') as f:
        content = f.read()
    md5 = hashlib.md5(content.encode('utf-8')).hexdigest()
    with open(addons_path + '.md5', 'w') as f:
        f.write(md5)
    print('addons.xml.md5 updated: %s' % md5)


def update_index_html():
    idx = '<html><body>\n'
    idx += '<a href="repository.mcfenlight/">repository.mcfenlight/</a>\n'
    idx += '<a href="plugin.video.mcfenlight/">plugin.video.mcfenlight/</a>\n'
    idx += '<a href="script.mcfenlight.wizard/">script.mcfenlight.wizard/ (Deprecated)</a>\n'
    idx += '<a href="script.mcfenlight.wizard-1.0.0.zip">script.mcfenlight.wizard-1.0.0.zip (Deprecated)</a>\n'
    idx += '<a href="script.mcfenlight.setup/">script.mcfenlight.setup/</a>\n'
    idx += '<a href="script.mcfenlight.setup/script.mcfenlight.setup-1.0.0.zip">McFenlight Setup (New Users)</a>\n'
    idx += '<a href="script.mcfenlight.migrate/">script.mcfenlight.migrate/</a>\n'
    idx += '<a href="script.mcfenlight.migrate/script.mcfenlight.migrate-1.0.0.zip">McFenlight TorBox Migrator (Existing Users)</a>\n'
    idx += '<a href="script.mcfenlight.emby/">script.mcfenlight.emby/</a>\n'
    idx += '<a href="script.mcfenlight.emby/script.mcfenlight.emby-1.0.0.zip">McFenlight Emby Setup</a>\n'
    idx += '<a href="addons.xml">addons.xml</a>\n'
    idx += '<a href="addons.xml.md5">addons.xml.md5</a>\n'
    idx += '</body></html>\n'
    with open(os.path.join(BASE, 'index.html'), 'w') as f:
        f.write(idx)
    print('Root index.html updated')


if __name__ == '__main__':
    print('=== Building wizard zips ===')
    for addon_id, version in WIZARDS:
        build_zip(addon_id, version)

    print('\n=== Updating addons.xml ===')
    update_addons_xml()

    print('\n=== Updating index.html ===')
    update_index_html()

    print('\nDone!')
