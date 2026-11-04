"""Check the KodoTimes install: the TOC, the one-folder ZIP, a fresh start, and the guard next to a 0.9.x install.

Loads KodoTimes with the stub WoW API of tools/check_volume.py and fires its ADDON_LOADED. The 0.9.x saved
variables (MotevePalsDB/MotevePalsChar) are no longer carried over: KodoTimes ignores them. A leftover full 0.9.x
addon (folder MotevePals) loads first (OptionalDeps: MotevePals) and keeps KodoTimes dormant.
Needs the lupa package (an embedded Lua 5.1):  uv run --with lupa python tools/check_install.py
"""
from pathlib import Path
import ast
import copy
import re
import sys
import zipfile

try:
    from lupa import lua51
except ImportError:
    sys.exit('FAIL: needs lupa (Lua 5.1 for Python). Run: uv run --with lupa python tools/check_install.py')

root = Path(__file__).resolve().parents[1]
ADDON = root / 'KodoTimes'
VERSION = '0.10.4'

# the stub WoW API is shared with check_volume.py (importing it would run its checks)
STUBS = next(node.value.value for node in ast.parse((root / 'tools' / 'check_volume.py').read_text(encoding='utf-8')).body
             if isinstance(node, ast.Assign) and getattr(node.targets[0], 'id', None) == 'STUBS')

# addon messages are recorded; the toast's body text and every frame's scale too
EXTRA = r'''
local createFrame = CreateFrame
function CreateFrame(...)
    local f = createFrame(...)
    f.SetScale = function(self, s) self.__scale = s end
    return f
end
registered, sent, banners, calls = {}, {}, {}, {}
C_ChatInfo = {
    RegisterAddonMessagePrefix = function(p) registered[#registered + 1] = p; return true end,
    SendAddonMessage = function(p, msg, chan, target) sent[#sent + 1] = { prefix = p, msg = msg, chan = chan, target = target }; return true end,
}
function Ambiguate(name) return (name:gsub("%-.*$", "")) end
function UnitFactionGroup() return "Horde", "Horde" end
function RecordBanners()
    KodoTimesToast.text.SetText = function(self, s) banners[#banners + 1] = s end
    rawset(KodoTimesToast, "moving", false)   -- the stub frame answers every unknown key with a function
end
function ShowAll() for _ = 1, 50 do KodoTimesToast.__scripts.OnUpdate(KodoTimesToast, 100) end end
function Spy(name)   -- record calls of NS[name] instead of running it
    NS[name] = function() calls[#calls + 1] = name end
end
'''

PALS = '|cffa88bff[Kodo Times]|r '
failures = []


def check(cond, what):
    if not cond:
        failures.append(what)


def toc(folder):
    """(## fields, file entries) of folder/<folder>.toc."""
    lines = (folder / f'{folder.name}.toc').read_text(encoding='utf-8').splitlines()
    fields = dict(m.groups() for m in (re.match(r'^## ([^:]+):\s*(.*?)\s*$', line) for line in lines) if m)
    files = [line.strip() for line in lines if line.strip() and not line.startswith('#')]
    return fields, files


def to_py(v):
    if hasattr(v, 'items') and not isinstance(v, (dict, str)):
        return {k: to_py(x) for k, x in v.items()}
    return v


def to_lua(lua, v):
    if isinstance(v, dict):
        return lua.table_from({k: to_lua(lua, x) for k, x in v.items()})
    return v


# TOC fields of the addon; OptionalDeps stays only so a leftover 0.9.x addon loads first (the duplicate guard)
fields, addon_files = toc(ADDON)
for key, want in [('Title', '|cff7fd8ffKodo|r |cffa88bffTimes|r'), ('Version', VERSION), ('Interface', '16001'),
                  ('SavedVariables', 'KodoTimesDB'), ('SavedVariablesPerCharacter', 'KodoTimesChar'),
                  ('OptionalDeps', 'MotevePals')]:
    check(fields.get(key) == want, f'KodoTimes.toc {key} is {fields.get(key)!r}, expected {want!r}')
check(addon_files == ['Theme.lua', 'Lines.lua', 'Pals.lua', 'Map.lua', 'Options.lua'], f'KodoTimes.toc lists {addon_files}')
check(not (ADDON / 'MotevePals.toc').exists(), 'KodoTimes/ still has the old TOC')
toc_text = (ADDON / 'KodoTimes.toc').read_text(encoding='utf-8')
check(re.search(r'^#[^#].*duplicate guard', toc_text, re.MULTILINE) is not None,
      'KodoTimes.toc has no comment saying OptionalDeps: MotevePals only orders loading for the duplicate guard')

# no bridge folder: the repository and the ZIP hold only KodoTimes/
check(not (root / 'MotevePals').exists(), 'the MotevePals/ bridge folder still exists')
pals = (ADDON / 'Pals.lua').read_text(encoding='utf-8')
for name in ('MotevePalsDB', 'MotevePalsChar', 'DeepCopy'):
    check(name not in pals, f'Pals.lua still references {name}')
with zipfile.ZipFile(root / 'downloads' / 'KodoTimes.zip') as archive:
    names = archive.namelist()
    outside = [n for n in names if not n.startswith('KodoTimes/')]
    check(names and not outside, f'downloads/KodoTimes.zip has entries outside KodoTimes/: {outside}')
    zip_toc = archive.read('KodoTimes/KodoTimes.toc').decode('utf-8') if 'KodoTimes/KodoTimes.toc' in names else ''
    zip_version = re.search(r'^## Version:\s*(\S+)', zip_toc, re.MULTILINE)
    check(zip_version and zip_version.group(1) == VERSION,
          f'downloads/KodoTimes.zip holds version {zip_version and zip_version.group(1)}, expected {VERSION} (run tools/package_addon.py)')


def fresh(old_db=None, old_char=None, new_db=None, new_char=None, old_addon=False):
    """A client start: saved variables in memory, the old addon first if asked, then KodoTimes; returns lua, globals, ns."""
    lua = lua51.LuaRuntime(unpack_returned_tuples=True)
    lua.execute(STUBS)
    lua.execute(EXTRA)
    g = lua.globals()
    for name, value in [('MotevePalsDB', old_db), ('MotevePalsChar', old_char), ('KodoTimesDB', new_db), ('KodoTimesChar', new_char)]:
        if value is not None:
            g[name] = to_lua(lua, value)
    if old_addon:   # a leftover full 0.9.x addon in the MotevePals folder loads first: it defines this at file scope
        lua.execute('SLASH_MOTEVEPALS1 = "/mpal"; SlashCmdList.MOTEVEPALS = function() end')
        g.FireEvent('ADDON_LOADED', 'MotevePals')
    for name in addon_files:
        g.LoadAddonFile((ADDON / name).read_text(encoding='utf-8'), name)
    g.FireEvent('ADDON_LOADED', 'KodoTimes')
    return lua, g, g.NS


def login(g, seconds):
    g.FireEvent('PLAYER_LOGIN')
    g.Advance(seconds)


OLD_DB = {'volume': 35, 'point': 'BOTTOMRIGHT', 'relPoint': 'BOTTOMRIGHT', 'x': -240, 'y': 180, 'scale': 0.9,
          'posVersion': 2, 'welcomed': True, 'crew': 'MPhaverok', 'chat': False,
          'knownPals': {'Miss': {'d': 'Miss Mcimbtyw', 't': 100}}, 'presetPrev': {'weed': {'grassDensity': '3'}}}
OLD_CHAR = {'welcomed': True, 'noCrew': True, 'skills': {'Blacksmithing': 150, 'Mining': 120}}
# what a new profile holds: DEFAULTS (toast scale 0.9) plus posVersion
FRESH_DB = {'enabled': True, 'mapNames': False, 'quietRaidPvp': True, 'selfToast': False, 'chat': True, 'sound': True, 'volume': 100,
            'time': 6.5, 'share': True, 'map': True, 'guild': True, 'group': True, 'friends': True,
            'point': 'LEFT', 'relPoint': 'LEFT', 'x': 18, 'y': -46, 'scale': 0.9, 'posVersion': 2}

# old 0.9.x saved variables still in memory, no KodoTimesDB: they are ignored, KodoTimes starts fresh
lua, g, ns = fresh(copy.deepcopy(OLD_DB), copy.deepcopy(OLD_CHAR))
new_db = to_py(lua.eval('(function() local d = {} for k, v in pairs(KodoTimesDB) do d[k] = v end return d end)()'))
for key in ('welcomed', 'crew', 'knownPals', 'presetPrev'):
    check(key not in new_db, f'old settings: KodoTimesDB.{key} was taken from MotevePalsDB')
check(new_db == FRESH_DB, f'old settings: KodoTimesDB is {new_db}, expected DEFAULTS {FRESH_DB}')
check(to_py(g.KodoTimesChar) == {}, f'old settings: KodoTimesChar is {to_py(g.KodoTimesChar)}, expected {{}}')
check(g.KodoTimesToast.__scale == 0.9, f'old settings: the toast is drawn at {g.KodoTimesToast.__scale}, expected 0.9')
check(ns.Volume() == 100, f'old settings: ns.Volume() is {ns.Volume()}, expected 100')
check(lua.eval('KodoTimesDB ~= MotevePalsDB and KodoTimesChar ~= MotevePalsChar'), 'old settings: the new tables are the old ones')
login(g, 6.1)
check(g.KodoTimesWelcome is not None, 'old settings: no welcome window 6 s after login')
g.SlashCmdList.KODOTIMES('volume 80')
check(g.KodoTimesDB.volume == 80, '/kodo volume 80 did not store 80 in KodoTimesDB')
check(to_py(g.MotevePalsDB) == OLD_DB, f'old settings: MotevePalsDB changed: {to_py(g.MotevePalsDB)}')
check(to_py(g.MotevePalsChar) == OLD_CHAR, f'old settings: MotevePalsChar changed: {to_py(g.MotevePalsChar)}')

# fresh install, no old saved variables: DEFAULTS, an empty character table, the welcome window after 6 s
lua, g, ns = fresh()
defaults = to_py(lua.eval('(function() local d = {} for k, v in pairs(KodoTimesDB) do d[k] = v end return d end)()'))
check(defaults == FRESH_DB, f'fresh install: KodoTimesDB is {defaults}')
check(to_py(g.KodoTimesChar) == {}, f'fresh install: KodoTimesChar is {to_py(g.KodoTimesChar)}')
check(g.MotevePalsDB is None and g.MotevePalsChar is None, 'fresh install: old saved variables were created')
login(g, 6.1)
check(g.KodoTimesWelcome is not None, 'fresh install: no welcome window 6 s after login')

# a saved scale is kept: an existing profile with the old 0.67 or 0.8 default keeps it, only new installs get 0.9
for saved in (0.67, 0.8, 1.5):
    lua, g, ns = fresh(new_db={'scale': saved, 'posVersion': 2})
    check(g.KodoTimesDB.scale == saved, f'saved scale {saved}: KodoTimesDB.scale is {g.KodoTimesDB.scale}')
    check(g.KodoTimesToast.__scale == saved, f'saved scale {saved}: the toast is drawn at {g.KodoTimesToast.__scale}')
lua, g, ns = fresh()
check(g.KodoTimesToast.__scale == 0.9, f'fresh install: the toast is drawn at {g.KodoTimesToast.__scale}, expected 0.9')

# prefix and slash commands: MOTEVEPAL is registered, sent and received; /kodo, /mpal and /pals are KODOTIMES
lua, g, ns = fresh(new_db={'chat': True})
check(list(g.registered.values()) == ['MOTEVEPAL'], f'registered prefixes {list(g.registered.values())}, expected MOTEVEPAL')
g.SlashCmdList.KODOTIMES('ping Tester2')
pings = [s for s in g.sent.values() if s.msg.startswith('PING~')]
check(len(pings) == 1 and pings[0].prefix == 'MOTEVEPAL' and pings[0].chan == 'WHISPER' and pings[0].target == 'Tester2',
      f'/kodo ping Tester2 sent {[(s.prefix, s.chan, s.target) for s in pings]}')
msg = '~'.join(['1', 'levelup', '77', '12', 'Barrens', '', '', '', '', '', 'MAGE', '', '', 'Miss Mcimbtyw'])
g.FireEvent('CHAT_MSG_ADDON', 'MOTEVEPAL', msg, 'WHISPER', 'Miss-Home')
check(any(line.startswith(PALS) and '[Miss]' in line for line in g.printed.values()), 'a MOTEVEPAL news message gave no chat line')
check((g.SLASH_KODOTIMES1, g.SLASH_KODOTIMES2, g.SLASH_KODOTIMES3) == ('/kodo', '/mpal', '/pals'),
      f'slash commands are {(g.SLASH_KODOTIMES1, g.SLASH_KODOTIMES2, g.SLASH_KODOTIMES3)}')
check(lua.eval('type(SlashCmdList.KODOTIMES)') == 'function', 'SlashCmdList.KODOTIMES is not a function')
check(g.SlashCmdList.MOTEVEPALS is None and g.SLASH_MOTEVEPALS1 is None, 'KodoTimes still defines the old slash command')

# a leftover full old addon still running next to it: KodoTimes stays dormant, warns once, and never errors.
# The warning says to delete the old MotevePals folder; unzipping over the old install no longer helps (no stub TOC).
def is_delete_warning(line):
    return 'Töröld a régi MotevePals mappát' in line and 'KodoTimes.zip' not in line and 'Csomagold' not in line


lua, g, ns = fresh(copy.deepcopy(OLD_DB), copy.deepcopy(OLD_CHAR), old_addon=True)
check(g.KodoTimesDB is None and g.KodoTimesChar is None, 'dormant: KodoTimes created its saved variables')
check(len(g.registered) == 0, 'dormant: KodoTimes registered the prefix')
g.RecordBanners()
login(g, 10)
warnings = [line for line in g.printed.values() if is_delete_warning(line)]
check(len(warnings) == 1 and len(g.printed) == 1, f'dormant: after login printed {list(g.printed.values())}, expected one warning '
      'telling the player to delete the MotevePals folder')
check(g.KodoTimesWelcome is None, 'dormant: the welcome window opened')
g.FireEvent('CHAT_MSG_ADDON', 'MOTEVEPAL', msg, 'WHISPER', 'Miss-Home')
g.ShowAll()
check(len(g.printed) == 1 and len(g.banners) == 0, 'dormant: a news message gave a chat line or a toast')
g.SlashCmdList.KODOTIMES('test')
g.ShowAll()
check(len(g.printed) == 2 and is_delete_warning(g.printed[2]) and len(g.banners) == 0, 'dormant: /kodo test did more than warn')
g.KodoTimesOptions.__scripts.OnShow(g.KodoTimesOptions)
g.KodoTimesOptions.__scripts.OnHide(g.KodoTimesOptions)
lua.execute('NS.ApplyPreset("weed", true)')
check(len(g.cvarWrites) == 0 and len(g.sent) == 0, 'dormant: a CVar was written or a message sent')
check(to_py(g.MotevePalsDB) == OLD_DB and to_py(g.MotevePalsChar) == OLD_CHAR, 'dormant: the old tables changed')

if failures:
    print('FAIL:')
    for failure in failures:
        print('  ' + failure)
    sys.exit(1)
print(f'PASS: KodoTimes.toc {VERSION} (OptionalDeps only for the guard); no MotevePals/ folder, the ZIP holds only KodoTimes/; '
      'old 0.9.x settings ignored and untouched (DEFAULTS, toast at 0.9, welcome); a saved scale (0.67/0.8/1.5) stays; '
      'MOTEVEPAL prefix kept; /kodo /mpal /pals; dormant next to the old addon with a delete-the-folder warning')
