import os, zipfile, hashlib, xml.etree.ElementTree as ET

base = '/mnt/files/Files/McFenRepo'
repo_dir = os.path.join(base, 'repository.mcfenlight')

repo_xml = '<?xml version="1.0" encoding="UTF-8"?>\n'
repo_xml += '<addon id="repository.mcfenlight" name="McFenlight Repository" version="1.0.2" provider-name="McMoobud">\n'
repo_xml += '    <extension point="xbmc.addon.repository" name="McFenlight Repository">\n'
repo_xml += '        <info compressed="false">https://mcmoobud.github.io/mcfenrepo/addons.xml</info>\n'
repo_xml += '        <checksum>https://mcmoobud.github.io/mcfenrepo/addons.xml.md5</checksum>\n'
repo_xml += '        <datadir zipped="true">https://mcmoobud.github.io/mcfenrepo/</datadir>\n'
repo_xml += '    </extension>\n'
repo_xml += '    <extension point="xbmc.addon.metadata">\n'
repo_xml += '        <summary lang="en">McFenlight Repository</summary>\n'
repo_xml += '        <description lang="en">Install and update the McFenlight addon.</description>\n'
repo_xml += '        <platform>all</platform>\n'
repo_xml += '    </extension>\n'
repo_xml += '</addon>\n'

with open(os.path.join(repo_dir, 'addon.xml'), 'w') as f:
    f.write(repo_xml)

for fn in os.listdir(repo_dir):
    if fn.endswith('.zip'):
        os.remove(os.path.join(repo_dir, fn))

zp = os.path.join(repo_dir, 'repository.mcfenlight-1.0.2.zip')
with zipfile.ZipFile(zp, 'w', zipfile.ZIP_DEFLATED) as zf:
    for fn in ['addon.xml', 'icon.png']:
        fp = os.path.join(repo_dir, fn)
        if os.path.exists(fp):
            zf.write(fp, 'repository.mcfenlight/' + fn)

print('Zip:', os.path.getsize(zp), 'bytes')
with zipfile.ZipFile(zp) as z:
    for i in z.infolist():
        print(' ', i.filename)

mcf = ET.parse(os.path.join(base, 'plugin.video.mcfenlight', 'addon.xml')).getroot()
repo = ET.parse(os.path.join(repo_dir, 'addon.xml')).getroot()
root = ET.Element('addons')
root.append(mcf)
root.append(repo)
ET.indent(root, space='    ')
c = '<?xml version="1.0" encoding="UTF-8"?>\n' + ET.tostring(root, encoding='unicode')
open(os.path.join(base, 'addons.xml'), 'w').write(c)
md5 = hashlib.md5(c.encode()).hexdigest()
open(os.path.join(base, 'addons.xml.md5'), 'w').write(md5)
print('addons.xml rebuilt, md5:', md5)

idx = '<html><body>\n'
idx += '<a href="repository.mcfenlight-1.0.2.zip">repository.mcfenlight-1.0.2.zip</a>\n'
idx += '<a href="addon.xml">addon.xml</a>\n'
idx += '</body></html>\n'
open(os.path.join(repo_dir, 'index.html'), 'w').write(idx)
print('index.html updated')
