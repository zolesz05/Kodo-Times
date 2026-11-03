"""Publish only the latest installable addon ZIP at a permanent download path: downloads/KodoTimes.zip.

The ZIP holds only the addon folder (KodoTimes/): installing means copying that one folder into Interface/AddOns.
"""
from pathlib import Path
import re
import zipfile

root = Path(__file__).resolve().parents[1]
FOLDERS = [root / 'KodoTimes']
downloads = root / 'downloads'
version = re.search(r'^## Version:\s*(\S+)', (root / 'KodoTimes' / 'KodoTimes.toc').read_text(encoding='utf-8'),
                    re.MULTILINE).group(1)
for folder in FOLDERS:
    toc = (folder / f'{folder.name}.toc').read_text(encoding='utf-8')
    for line in toc.splitlines():
        if line.strip() and not line.startswith('#'):
            assert (folder / line.strip()).is_file(), f'Missing TOC entry in {folder.name}.toc: {line}'

downloads.mkdir(exist_ok=True)
target = downloads / 'KodoTimes.zip'
pending = downloads / 'KodoTimes.zip.tmp'
files = [p for folder in FOLDERS for p in sorted(p for p in folder.rglob('*') if p.is_file())]
with zipfile.ZipFile(pending, 'w', zipfile.ZIP_DEFLATED) as archive:
    for path in files:
        archive.write(path, path.relative_to(root).as_posix())
with zipfile.ZipFile(pending) as archive:
    assert archive.testzip() is None
    assert archive.namelist() == [p.relative_to(root).as_posix() for p in files]
    for path in files:
        assert archive.read(path.relative_to(root).as_posix()) == path.read_bytes()
pending.replace(target)

# Old downloads in this exact directory are removed: versioned KodoTimes ZIPs and every ZIP of the old name.
for path in [*downloads.glob('KodoTimes-*.zip'), *downloads.glob('MotevePals*.zip')]:
    assert path.resolve().parent == downloads.resolve()
    if path.is_file():
        path.unlink()

DOWNLOAD_URL = 'https://github.com/zolesz05/Kodo-Times/raw/main/downloads/KodoTimes.zip'
readme = root / 'README.md'
text = readme.read_text(encoding='utf-8')
text = re.sub(r'\*\*Aktuális verzió: [^*]+\*\*', f'**Aktuális verzió: {version}**', text)
# absolute link: the relative downloads/...?raw=true form gives 404 on GitHub
text = re.sub(r'\]\([^)]*downloads/(?:MotevePals|KodoTimes)(?:-[0-9.]+)?\.zip(?:\?raw=true)?\)', '](' + DOWNLOAD_URL + ')', text)
readme.write_text(text, encoding='utf-8')
print(f'PASS: {version}; {len(files)} verified addon files in KodoTimes/ only; downloads/KodoTimes.zip is the only current addon download.')
