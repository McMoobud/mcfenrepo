import os, zipfile, hashlib, xml.etree.ElementTree as ET

base = '/mnt/files/Files/McFenRepo'
src = '/opt/mcfenlight/plugin.video.fenlight'
plugin_dir = os.path.join(base, 'plugin.video.mcfenlight')

# Rebuild plugin zip from source
zip_path = os.path.join(plugin_dir, 'plugin.video.mcfenlight-2.2.04.zip')
if os.path.exists(zip_path):
    os.remove(zip_path)

with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zf:
    for root, dirs, files in os.walk(src):
        dirs[:] = [d for d in dirs if d != '.git' and d != '__pycache__']
        for fn in files:
            if fn.endswith('.pyc'):
                continue
            fp = os.path.join(root, fn)
            arcname = os.path.join('plugin.video.mcfenlight', os.path.relpath(fp, src))
            zf.write(fp, arcname)

print(f'Plugin zip: {os.path.getsize(zip_path)} bytes')

# Rebuild addons.xml
repo_dir = os.path.join(base, 'repository.mcfenlight')

# Copy addon.xml from source to plugin dir in repo
import shutil
shutil.copy2(os.path.join(src, 'addon.xml'), os.path.join(plugin_dir, 'addon.xml'))

mcf = ET.parse(os.path.join(plugin_dir, 'addon.xml')).getroot()
repo = ET.parse(os.path.join(repo_dir, 'addon.xml')).getroot()
root = ET.Element('addons')
root.append(mcf)
root.append(repo)
ET.indent(root, space='    ')
c = '<?xml version="1.0" encoding="UTF-8"?>\n' + ET.tostring(root, encoding='unicode')
open(os.path.join(base, 'addons.xml'), 'w').write(c)
md5 = hashlib.md5(c.encode()).hexdigest()
open(os.path.join(base, 'addons.xml.md5'), 'w').write(md5)
print(f'addons.xml rebuilt, md5: {md5}')
print('Done')
