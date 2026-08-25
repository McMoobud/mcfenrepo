import os, zipfile

base = '/mnt/files/Files/McFenRepo'
wizard_dir = os.path.join(base, 'script.mcfenlight.wizard')
zip_path = os.path.join(base, 'script.mcfenlight.wizard-1.0.0.zip')

with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zf:
    for fn in os.listdir(wizard_dir):
        fp = os.path.join(wizard_dir, fn)
        if os.path.isfile(fp):
            zf.write(fp, 'script.mcfenlight.wizard/' + fn)

print('Wizard zip:', os.path.getsize(zip_path), 'bytes')
with zipfile.ZipFile(zip_path) as z:
    for i in z.infolist():
        print(' ', i.filename, i.file_size)

# Update root index.html to include wizard zip
idx = '<html><body>\n'
idx += '<a href="repository.mcfenlight/">repository.mcfenlight/</a>\n'
idx += '<a href="plugin.video.mcfenlight/">plugin.video.mcfenlight/</a>\n'
idx += '<a href="script.mcfenlight.wizard/">script.mcfenlight.wizard/</a>\n'
idx += '<a href="script.mcfenlight.wizard-1.0.0.zip">script.mcfenlight.wizard-1.0.0.zip</a>\n'
idx += '<a href="addons.xml">addons.xml</a>\n'
idx += '<a href="addons.xml.md5">addons.xml.md5</a>\n'
idx += '</body></html>\n'
open(os.path.join(base, 'index.html'), 'w').write(idx)
print('Root index.html updated')
print('Done')
