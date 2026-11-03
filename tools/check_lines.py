"""Check the pop-up lines in MotevePals/Lines.lua: UTF-8, lists, counts, texts and placeholders."""
from pathlib import Path
import re
import sys

root = Path(__file__).resolve().parents[1]
path = root / 'MotevePals' / 'Lines.lua'
try:
    text = path.read_bytes().decode('utf-8')
except UnicodeDecodeError as err:
    sys.exit(f'FAIL: {path.relative_to(root).as_posix()} is not valid UTF-8: {err}')

PLACEHOLDERS = set('nlzsrigt')
COUNTS = {
    'levelup': 20, 'levelround': 5, 'level60': 9, 'death': 36, 'skill': 7,
    'craftblue': 5, 'craftepic': 5, 'epicloot': 6, 'deathlegend': 8,
}
EXPECTED = {
    'levelup': [
        '%n szintet lépett (%l). A családja büszke lehet rá.',
        '%n %l-es lett. Úgyis megint meghal valami faszságban.',
        'Új szint, %n! A lelked értéke továbbra is nulla.',
        'Gratulálunk, %n! Most már drágábban halsz meg.',
        '%n, a démonod büszke rád. Hazudik.',
        '%n: új képességek feloldva. Józan ész továbbra sem elérhető.',
        'LEVEL UP: %n jogosultságai frissültek.',
        '%n egy szinttel közelebb a munkanélküliséghez.',
        '%n, anyád is büszke lenne. Ha tudná, mivel töltöd az időd.',
        '%n, már megint nem a való életben fejlődtél.',
    ],
    'levelround': [
        '%n kerek %l. szinten. Valaki küldjön egy coppert a postaládájába.',
    ],
    'level60': [
        '%n ELÉRTE A 60-AT! A napfény mostantól hivatalosan is ellenség.',
        '%n 60-as lett. Most kezdődik az igazi szopás: A GEAR.',
        'MAX LEVEL! %n végre ráér... napi 10 órát farmolni.',
        '%n 60-as lett, szagod hogy áll?',
        '%n elérte a 60-at, reméljük a fürdőszobát is.',
        '%n 60. W vitaminból nem szenvedsz hiányt, barátom.',
        'Gratulálunk, %n! Most kezdődik az igazi munkanélküliség.',
    ],
    'death': [
        '%n meghalt. Szerinte taktikai visszavonulás volt. Dobott egy hasast.',
        '%n megdögölt.',
        '%n sajnos befosott.',
        '%n szarba lépett.',
        '%n már nem lesz halottabb.',
        '%n rizzeli a Spirit Healert.',
        '%n: Geci, itt a Spirit Healer.',
        '%n tolt egy Attilát.',
        '%n-t elaltatták. Szép álmokat neki!',
        '%n neki gatya. Hívjátok a Fésűst.',
        '%n halott. Xd',
        '%n elhunyt. %z területén. Mi a fasznak ment oda?',
        '%n már a halakkal alszik.',
        '%n úgy be van baszva, mint macskát szarni.',
        '%n imádja a földet nyalogatni.',
        '%n nem élte túl, most már tényleg a föld alatt van a teljesítménye.',
        '%n újraélesztése sikertelen. Talán legközelebb kevesebb hülyeséggel próbálkozik.',
        '%n karaktere elhunyt. A szégyen azonban örök.',
        '%n javítási költsége meghaladja a karakter piaci értékét.',
        'Egy újabb mob büszkén mesélheti el, hogy legyőzött egy játékost. Az áldozat: %n.',
        '%n temetésére senki nem érkezett. Mindenki farmol.',
        'Critical failure: {%n}. Brain.dll not found.',
        'A mob nem volt erős. %n volt gyenge.',
        'A Spirit Healer már név szerint ismeri %n-t.',
        '%n ismét visszatért a szellemvilágba. Úgy tűnik, ott már törzsvendég.',
        '%n sikeresen tesztelte a mob sebzését. Saját magán.',
        'A helyi élővilág újabb áldozatot követelt: %n.',
        '%n ma is hozzájárult Azeroth hulladéktermeléséhez.',
    ],
    'skill': [
        '%n %s skillje elérte a %r-t. Végre ért valamihez.',
    ],
    'epicloot': [
        'EPIC drop! %n: %i. Aura farming: ON.',
    ],
}
LEVEL_LINES = {
    10: '%n, már nem vagy teljesen kezdő. Csak majdnem.',
    20: '%n, a játék most kezd igazán drága lenni.',
    30: '%n, félúton vagy. Legalábbis lélekben.',
    40: 'Mount unlocked, %n. Pénztárca locked.',
    50: '%n, már túl sok időt öltél bele ahhoz, hogy abbahagyd.',
}
REMOVED = [
    "%l. szint, %n! Most már nyugodtan mondhatod otthon, hogy 'csak még egy dungeon'.",
    '%n szintet lépett (%l). A családja büszke rá.',
    '%n %l-es lett. Ünnepeljük meg azzal, hogy megint meghal valami faszságban.',
    '%n kerek %l. szinten. Valaki tegyen egy tortát a postaládájába.',
    '%n ELÉRTE A 60-AT! A napfény mostantól hivatalosan ellenség.',
    '%n 60-as lett. Most kezdődik az igazi szopás: a gear.',
    'MAX LEVEL! %n végre ráér... napi 6 órát farmolni.',
    '%n meghalt. Szerinte taktikai visszavonulás volt. Hasra.',
    '%n %s skillje elérte a %r-t. Végre valamihez ért.',
    'EPIC drop! %n: %i. Aura farming on.',
]

failures = []
STRING = re.compile(r'"((?:[^"\\\n]|\\.)*)"')


def block(body, start):
    """The text between the '{' at body[start] and its matching '}'."""
    depth = 0
    for i in range(start, len(body)):
        if body[i] == '{':
            depth += 1
        elif body[i] == '}':
            depth -= 1
            if depth == 0:
                return body[start + 1:i]
    sys.exit('FAIL: unbalanced braces in Lines.lua')


def table(name):
    found = re.search(r'^' + re.escape(name) + r'\s*=\s*\{', text, re.MULTILINE)
    if not found:
        sys.exit(f'FAIL: {name} not found in Lines.lua')
    return block(text, found.end() - 1)


def lists(body):
    """Each `key = { "..." }` list directly inside body."""
    out = {}
    for found in re.finditer(r'^ {4}([A-Za-z_]\w*)\s*=\s*\{', body, re.MULTILINE):
        out[found.group(1)] = STRING.findall(block(body, found.end() - 1))
    return out


lines = lists(table('ns.LINES'))
for found in re.finditer(r'^ns\.LINES\.(\w+)\s*=', text, re.MULTILINE):
    if found.group(1) in lines:
        failures.append(f'ns.LINES.{found.group(1)} is set twice')
    lines[found.group(1)] = STRING.findall(table(f'ns.LINES.{found.group(1)}'))

if set(lines) != set(COUNTS):
    failures.append(f'ns.LINES keys are {sorted(lines)}, expected {sorted(COUNTS)}')
for kind, count in COUNTS.items():
    have = lines.get(kind, [])
    print(f'{kind}: {len(have)}')
    if len(have) != count:
        failures.append(f'{kind} has {len(have)} lines, expected {count}')
    if len(set(have)) != len(have):
        failures.append(f'{kind} has a line twice')
for kind, wanted in EXPECTED.items():
    for line in wanted:
        if line not in lines.get(kind, []):
            failures.append(f'{kind} is missing: {line}')
for line in REMOVED:
    if line in text:
        failures.append(f'removed line is still there: {line}')

at_body = table('ns.LINES_AT')
at = lists(at_body)
if set(at) != {'levelround'}:
    failures.append(f'ns.LINES_AT keys are {sorted(at)}, expected [\'levelround\']')
levels = {}
found = re.search(r'^ {4}levelround\s*=\s*\{', at_body, re.MULTILINE)
if found:
    body = block(at_body, found.end() - 1)
    for found in re.finditer(r'^ {8}\[(\d+)\]\s*=\s*\{', body, re.MULTILINE):
        levels[int(found.group(1))] = STRING.findall(block(body, found.end() - 1))
print('LINES_AT.levelround: ' + ', '.join(f'{lv}: {len(v)}' for lv, v in sorted(levels.items())))
if sorted(levels) != sorted(LEVEL_LINES):
    failures.append(f'LINES_AT.levelround levels are {sorted(levels)}, expected {sorted(LEVEL_LINES)}')
for level, line in LEVEL_LINES.items():
    if levels.get(level) != [line]:
        failures.append(f'LINES_AT.levelround[{level}] is {levels.get(level)}, expected [{line!r}]')

every = [line for kind in lines.values() for line in kind] + [line for v in levels.values() for line in v]
for line in every:
    for found in re.finditer(r'%(.?)', line):
        if found.group(1) not in PLACEHOLDERS:
            failures.append(f'unknown placeholder %{found.group(1)} in: {line}')

if failures:
    print('FAIL:')
    for failure in failures:
        print('  ' + failure)
    sys.exit(1)
print(f'PASS: {len(every)} lines, placeholders only %' + ' %'.join(sorted(PLACEHOLDERS)))
