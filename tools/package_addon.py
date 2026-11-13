"""Build the installable addon ZIP: <out>/KodoTimes.zip (default dist/KodoTimes.zip).

The ZIP holds only the addon folder (KodoTimes/): installing means copying that one folder into Interface/AddOns.
Releases are built from main by .github/workflows/release.yml; nothing here touches README.md or the repository.
Standard library only:  python tools/package_addon.py [--out DIR]
"""
from pathlib import Path
import argparse
import re
import zipfile

root = Path(__file__).resolve().parents[1]
FOLDERS = [root / 'KodoTimes']
VERSION_RE = re.compile(r'^## Version:\s*(\S+)', re.MULTILINE)


def toc_version():
    """The ## Version of KodoTimes/KodoTimes.toc."""
    return VERSION_RE.search((root / 'KodoTimes' / 'KodoTimes.toc').read_text(encoding='utf-8')).group(1)


def build_zip(out_dir: Path) -> tuple[str, Path]:
    """Check the TOC entries, write out_dir/KodoTimes.zip, verify its content; returns (version, zip path)."""
    version = toc_version()
    for folder in FOLDERS:
        toc = (folder / f'{folder.name}.toc').read_text(encoding='utf-8')
        for line in toc.splitlines():
            if line.strip() and not line.startswith('#'):
                assert (folder / line.strip()).is_file(), f'Missing TOC entry in {folder.name}.toc: {line}'

    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    target = out_dir / 'KodoTimes.zip'
    pending = out_dir / 'KodoTimes.zip.tmp'
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
    return version, target


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Build the installable KodoTimes.zip.')
    parser.add_argument('--out', type=Path, default=root / 'dist', help='output folder (default: dist/)')
    args = parser.parse_args()
    version, target = build_zip(args.out)
    with zipfile.ZipFile(target) as archive:
        count = len(archive.namelist())
    print(f'PASS: {version}; {count} verified addon files in KodoTimes/ only; written to {target}')
