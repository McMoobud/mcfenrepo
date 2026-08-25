import os

path = '/opt/mcfenlight/plugin.video.fenlight/resources/lib/caches/settings_cache.py'
with open(path) as f:
    content = f.read()

# Replace old Trakt client ID
content = content.replace(
    "c787278de2e4bba0a92125433e89e0d71d89a09a2f9c44dd69c2f13c8e8eef06",
    "d670d157485c272e4a9385da4a8b3d1ba1d248ee93a619309ebd7f9cf6a67351"
)

# Replace old Trakt client secret
content = content.replace(
    "72012ed0e523e642b62e3137207dc6208b6b5b0405f7d17d57d3b31567d6a59c",
    "7efa8413b83e997632598f39349444dc6b2d64cae668ff0bf1ca38986a4e8aa5"
)

with open(path, 'w') as f:
    f.write(content)

print('Trakt credentials updated in settings_cache.py')

# Verify
with open(path) as f:
    c = f.read()
assert 'd670d157485c272e4a9385da4a8b3d1ba1d248ee93a619309ebd7f9cf6a67351' in c
assert '7efa8413b83e997632598f39349444dc6b2d64cae668ff0bf1ca38986a4e8aa5' in c
print('Verified OK')
