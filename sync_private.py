import os, shutil

src = '/opt/mcfenlight/plugin.video.fenlight'
dst = '/mnt/files/Files/McFenLight'

# Sync all files from working copy to private repo, excluding .git
for root, dirs, files in os.walk(src):
    dirs[:] = [d for d in dirs if d != '.git' and d != '__pycache__']
    rel = os.path.relpath(root, src)
    dst_dir = os.path.join(dst, rel)
    os.makedirs(dst_dir, exist_ok=True)
    for fn in files:
        if fn.endswith('.pyc'):
            continue
        s = os.path.join(root, fn)
        d = os.path.join(dst_dir, fn)
        shutil.copy2(s, d)

print('Files synced from working copy to private repo')
