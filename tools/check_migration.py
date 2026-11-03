"""Check the rename to Kodo Times: both TOCs, and the one-time copy of the old saved variables.

Loads the addons in client order with the stub WoW API of tools/check_volume.py: the MotevePals bridge stub (its
saved variables already set), its ADDON_LOADED, then KodoTimes (OptionalDeps: MotevePals) and its ADDON_LOADED.
Needs the lupa package (an embedded Lua 5.1):  uv run --with lupa python tools/check_migration.py
"""
from pathlib import Path
import ast
import copy
import re
import sys

try:
    from lupa import lua51
except ImportError:
    sys.exit('FAIL: needs lupa (Lua 5.1 for Python). Run: uv run --with lupa python tools/check_migration.py')

root = Path(__file__).resolve().parents[1]
ADDON, STUB = root / 'KodoTimes', root / 'MotevePals'

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


# TOC fields: the renamed addon, and the stub that only declares the old saved variables
fields, addon_files = toc(ADDON)
for key, want in [('Title', '|cff7fd8ffKodo|r |cffa88bffTimes|r'), ('Version', '0.10.2'), ('Interface', '16001'),
                  ('SavedVariables', 'KodoTimesDB'), ('SavedVariablesPerCharacter', 'KodoTimesChar'),
                  ('OptionalDeps', 'MotevePals')]:
    check(fields.get(key) == want, f'KodoTimes.toc {key} is {fields.get(key)!r}, expected {want!r}')
check(addon_files == ['Theme.lua', 'Lines.lua', 'Pals.lua', 'Map.lua', 'Options.lua'], f'KodoTimes.toc lists {addon_files}')
check(not (ADDON / 'MotevePals.toc').exists(), 'KodoTimes/ still has the old TOC')
check(sorted(p.name for p in STUB.iterdir()) == ['MotevePals.lua', 'MotevePals.toc'],
      f'MotevePals/ holds {sorted(p.name for p in STUB.iterdir())}, expected only the stub TOC and its lua file')
check((STUB / 'MotevePals.lua').stat().st_size == 0, 'MotevePals/MotevePals.lua is not empty')
fields, stub_files = toc(STUB)
for key, want in [('Interface', '16001'), ('SavedVariables', 'MotevePalsDB'), ('SavedVariablesPerCharacter', 'MotevePalsChar'),
                  ('Version', '0.10.0')]:
    check(fields.get(key) == want, f'MotevePals.toc {key} is {fields.get(key)!r}, expected {want!r}')
check('Kodo' in fields.get('Title', '') and fields.get('Notes') and fields.get('Notes-huHU'),
      'the stub TOC does not say what it is (Title / Notes / Notes-huHU)')
check(stub_files == ['MotevePals.lua'], f'MotevePals.toc lists {stub_files}, expected only MotevePals.lua')


def fresh(old_db=None, old_char=None, new_db=None, new_char=None, old_addon=False):
    """A client start: saved variables in memory, the stub loaded, then KodoTimes; returns lua, globals, ns."""
    lua = lua51.LuaRuntime(unpack_returned_tuples=True)
    lua.execute(STUBS)
    lua.execute(EXTRA)
    g = lua.globals()
    for name, value in [('MotevePalsDB', old_db), ('MotevePalsChar', old_char), ('KodoTimesDB', new_db), ('KodoTimesChar', new_char)]:
        if value is not None:
            g[name] = to_lua(lua, value)
    if old_addon:   # the full 0.9.x addon still in the MotevePals folder: it defines this at file scope
        lua.execute('SLASH_MOTEVEPALS1 = "/mpal"; SlashCmdList.MOTEVEPALS = function() end')
    else:
        for name in stub_files:
            g.LoadAddonFile((STUB / name).read_text(encoding='utf-8'), 'MotevePals/' + name, 'MotevePals')
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

# upgrade: every old account and character value is in the new tables, the toast keeps its place, no welcome
lua, g, ns = fresh(copy.deepcopy(OLD_DB), copy.deepcopy(OLD_CHAR))
new_db, new_char = to_py(g.KodoTimesDB), to_py(g.KodoTimesChar)
for key, want in OLD_DB.items():
    check(new_db.get(key) == want, f'upgrade: KodoTimesDB.{key} is {new_db.get(key)!r}, expected {want!r}')
check(new_char == OLD_CHAR, f'upgrade: KodoTimesChar is {new_char}, expected {OLD_CHAR}')
check(ns.Volume() == 35, f'upgrade: ns.Volume() is {ns.Volume()}, expected 35')
check(list(g.KodoTimesToast.__point.values())[:1] == ['BOTTOMRIGHT'] and list(g.KodoTimesToast.__point.values())[2:] == ['BOTTOMRIGHT', -240, 180],
      f'upgrade: the toast is placed at {list(g.KodoTimesToast.__point.values())}')
check(new_db.get('guild') is True and new_db.get('time') == 6.5, 'upgrade: DEFAULTS were not filled in after the copy')
lua.execute('Spy("Welcome"); Spy("JoinCrew")')
login(g, 15)
check(list(g.calls.values()) == [], f'upgrade: after login {list(g.calls.values())} ran (welcomed, no crew on this character)')

# the old tables are only read: login (rewrites char.skills) and /kodo volume leave them as they were
g.SlashCmdList.KODOTIMES('volume 80')
lua.execute('if KodoTimesDB.knownPals then KodoTimesDB.knownPals.Miss.d = "changed"; KodoTimesDB.presetPrev.weed.grassDensity = "9" end')
check(g.KodoTimesDB.volume == 80, '/kodo volume 80 did not store 80 in KodoTimesDB')
check(to_py(g.MotevePalsDB) == OLD_DB, f'MotevePalsDB changed after migration: {to_py(g.MotevePalsDB)}')
check(to_py(g.MotevePalsChar) == OLD_CHAR, f'MotevePalsChar changed after migration: {to_py(g.MotevePalsChar)}')
check(lua.eval('KodoTimesDB ~= MotevePalsDB and KodoTimesChar ~= MotevePalsChar and KodoTimesChar.skills ~= MotevePalsChar.skills '
               'and KodoTimesDB.knownPals ~= MotevePalsDB.knownPals'), 'the new tables share a table with the old ones')

# an existing KodoTimesDB wins: nothing is taken from MotevePalsDB, which stays as it was
lua, g, ns = fresh(copy.deepcopy(OLD_DB), copy.deepcopy(OLD_CHAR), new_db={'volume': 60}, new_char={'welcomed': True})
new_db = to_py(g.KodoTimesDB)
check(new_db['volume'] == 60, f'existing KodoTimesDB: volume is {new_db["volume"]}, expected 60')
for key in ('welcomed', 'crew', 'knownPals', 'presetPrev'):
    check(key not in new_db, f'existing KodoTimesDB: {key} was taken from MotevePalsDB')
check(new_db['point'] == 'LEFT' and new_db['x'] == 18, 'existing KodoTimesDB: the old position overwrote it')
check(to_py(g.KodoTimesChar) == {'welcomed': True}, f'existing KodoTimesChar was overwritten: {to_py(g.KodoTimesChar)}')
check(to_py(g.MotevePalsDB) == OLD_DB and to_py(g.MotevePalsChar) == OLD_CHAR, 'the old tables changed')

# an alt logging in after the first character: KodoTimesDB exists, KodoTimesChar is still nil -> copied on its own
lua, g, ns = fresh(copy.deepcopy(OLD_DB), {'welcomed': True, 'noCrew': True}, new_db={'volume': 60, 'crew': 'MPhaverok', 'welcomed': True})
check(g.KodoTimesChar.welcomed is True and g.KodoTimesChar.noCrew is True, f'alt: KodoTimesChar is {to_py(g.KodoTimesChar)}')
check(g.KodoTimesDB.volume == 60 and g.KodoTimesDB.knownPals is None, 'alt: KodoTimesDB was overwritten by MotevePalsDB')
lua.execute('Spy("Welcome"); Spy("JoinCrew")')
login(g, 15)
check(list(g.calls.values()) == [], f'alt: after login {list(g.calls.values())} ran, expected neither the welcome nor a crew join')

# fresh install, no old saved variables: DEFAULTS, an empty character table, the welcome window after 6 s
lua, g, ns = fresh()
defaults = to_py(lua.eval('(function() local d = {} for k, v in pairs(KodoTimesDB) do d[k] = v end return d end)()'))
want = {'enabled': True, 'mapNames': False, 'quietRaidPvp': True, 'selfToast': False, 'chat': True, 'sound': True, 'volume': 100,
        'time': 6.5, 'share': True, 'map': True, 'guild': True, 'group': True, 'friends': True,
        'point': 'LEFT', 'relPoint': 'LEFT', 'x': 18, 'y': -46, 'scale': 0.8, 'posVersion': 2}
check(defaults == want, f'fresh install: KodoTimesDB is {defaults}')
check(to_py(g.KodoTimesChar) == {}, f'fresh install: KodoTimesChar is {to_py(g.KodoTimesChar)}')
check(g.MotevePalsDB is None and g.MotevePalsChar is None, 'fresh install: old saved variables were created')
login(g, 6.1)
check(g.KodoTimesWelcome is not None, 'fresh install: no welcome window 6 s after login')

# a saved scale is kept: an existing profile with the old 0.67 default stays at 0.67, only new installs get 0.8
for saved in (0.67, 1.5):
    lua, g, ns = fresh(new_db={'scale': saved, 'posVersion': 2})
    check(g.KodoTimesDB.scale == saved, f'saved scale {saved}: KodoTimesDB.scale is {g.KodoTimesDB.scale}')
    check(g.KodoTimesToast.__scale == saved, f'saved scale {saved}: the toast is drawn at {g.KodoTimesToast.__scale}')
lua, g, ns = fresh()
check(g.KodoTimesToast.__scale == 0.8, f'fresh install: the toast is drawn at {g.KodoTimesToast.__scale}, expected 0.8')

# prefix and slash commands: MOTEVEPAL is registered, sent and received; /kodo, /mpal and /pals are KODOTIMES
lua, g, ns = fresh(new_db={'chat': True})
check(list(g.registered.values()) == ['MOTEVEPAL'], f'registered prefixes {list(g.registered.values())}, expected MOTEVEPAL')
g.SlashCmdList.KODOTIMES('ping Tester2')
pings = [s for s in g.sent.values() if s.msg.startswith('PING~')]
check(len(pings) == 1 and pings[0].prefix == 'MOTEVEPAL' and pings[0].chan == 'WHISPER' and pings[0].target == 'Tester2',
      f'/kodo ping Tester2 sent {[(s.prefix, s.chan, s.target) for s in pings]}')
msg = '~'.join(['1', 'levelup', '77', '12', 'Barrens', '', '', '', '', '', 'MAGE', '', '', 'Miss Mcimbtyw'])
g.FireEvent('CHAT_MSG_ADDON', 'MOTEVEPAL', msg, 'WHISPER', 'Miss-Home')
check(any(line.startswith(PALS) and 'Mcimbtyw' in line for line in g.printed.values()), 'a MOTEVEPAL news message gave no chat line')
check((g.SLASH_KODOTIMES1, g.SLASH_KODOTIMES2, g.SLASH_KODOTIMES3) == ('/kodo', '/mpal', '/pals'),
      f'slash commands are {(g.SLASH_KODOTIMES1, g.SLASH_KODOTIMES2, g.SLASH_KODOTIMES3)}')
check(lua.eval('type(SlashCmdList.KODOTIMES)') == 'function', 'SlashCmdList.KODOTIMES is not a function')
check(g.SlashCmdList.MOTEVEPALS is None and g.SLASH_MOTEVEPALS1 is None, 'KodoTimes still defines the old slash command')

# the full old addon still running next to it: KodoTimes stays dormant, warns once, and never errors
lua, g, ns = fresh(copy.deepcopy(OLD_DB), copy.deepcopy(OLD_CHAR), old_addon=True)
check(g.KodoTimesDB is None and g.KodoTimesChar is None, 'dormant: KodoTimes created its saved variables')
check(len(g.registered) == 0, 'dormant: KodoTimes registered the prefix')
g.RecordBanners()
login(g, 10)
warnings = [line for line in g.printed.values() if 'KodoTimes.zip' in line]
check(len(warnings) == 1 and len(g.printed) == 1, f'dormant: after login printed {list(g.printed.values())}, expected one warning')
check(g.KodoTimesWelcome is None, 'dormant: the welcome window opened')
g.FireEvent('CHAT_MSG_ADDON', 'MOTEVEPAL', msg, 'WHISPER', 'Miss-Home')
g.ShowAll()
check(len(g.printed) == 1 and len(g.banners) == 0, 'dormant: a news message gave a chat line or a toast')
g.SlashCmdList.KODOTIMES('test')
g.ShowAll()
check(len(g.printed) == 2 and 'KodoTimes.zip' in g.printed[2] and len(g.banners) == 0, 'dormant: /kodo test did more than warn')
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
print('PASS: KodoTimes.toc and the MotevePals stub; old settings copied once (account and character apart), never written; '
      'fresh install gets DEFAULTS (toast at 0.8) and the welcome; a saved scale (0.67) stays; MOTEVEPAL prefix kept; /kodo /mpal /pals; dormant next to the old addon')
