"""Check the rename to Kodo Times: no old visible or frame name is left, and the network names that must stay, stay.

The news toast's top line (the kicker) must carry the Kodo Times masthead, not the old one.

Scans every text file under KodoTimes/ and tools/. The only exceptions are this script and the older entries of the
KodoTimes/README.txt changelog (history stays as written). Standard library only:  python tools/check_rename.py
"""
from pathlib import Path
import re
import sys

root = Path(__file__).resolve().parents[1]
OLD = 'Moteve' + 'Pals'   # built from pieces, so this script never holds the names it bans
BANNED = ['Moteve' + ' Pals', 'MOTEVE' + ' PALS'] + [OLD + suffix for suffix in ('Toast', 'Options', 'Welcome', 'VolumeSlider', 'Tooltip')]
BANNED += ['AZEROTH' + ' BULVÁR']   # the pre-rename masthead of the news toast's top line
TEXT = {'.lua', '.toc', '.txt', '.py', '.md'}
HISTORY = re.compile(r'^(\d+\.\d+(?:\.\d+)?):')
failures = []

for folder in ('KodoTimes', 'tools'):
    for path in sorted((root / folder).rglob('*')):
        if not path.is_file() or path.suffix.lower() not in TEXT or path.resolve() == Path(__file__).resolve():
            continue
        rel = path.relative_to(root).as_posix()
        entry = None   # the changelog entry a README.txt line belongs to
        for number, line in enumerate(path.read_text(encoding='utf-8').splitlines(), 1):
            if rel == 'KodoTimes/README.txt':
                m = HISTORY.match(line)
                if m:
                    entry = m.group(1)
                elif not line.startswith(' '):
                    entry = None
                if entry and entry != '0.10.0':
                    continue
            for name in BANNED:
                if name in line:
                    failures.append(f'{rel}:{number} still has {name!r}: {line.strip()}')

# kept on purpose: 0.9.x and 0.10+ clients share the message prefix and the crew channel
pals = (root / 'KodoTimes' / 'Pals.lua').read_text(encoding='utf-8')
for kept in ('local PREFIX = "MOTEVEPAL"', 'local DEFAULT_CREW = "MPhaverok"', 'db.crew = "MP" .. '):
    if kept not in pals:
        failures.append(f'KodoTimes/Pals.lua lost {kept!r}')

# every news toast shares the one kicker, set once: it must read the Kodo Times masthead
kickers = re.findall(r'T\.kicker:SetText\((.*)\)', pals)
if kickers != ['"KODO TIMES  -  RENDKÍVÜLI KIADÁS"']:
    failures.append(f'KodoTimes/Pals.lua sets the toast kicker to {kickers}, expected one "KODO TIMES  -  RENDKÍVÜLI KIADÁS"')

if failures:
    print('FAIL:')
    for failure in failures:
        print('  ' + failure)
    sys.exit(1)
print('PASS: no old name left in KodoTimes/ or tools/ (changelog history aside); MOTEVEPAL prefix and MP crew channel kept; '
      'toast kicker reads KODO TIMES')
