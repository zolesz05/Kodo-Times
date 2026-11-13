"""Check the per-kind news switches (KodoTimesDB.show*): they filter only what shows up here, never what is sent.

Runs the addon in Lua 5.1 with the stub WoW API of tools/check_volume.py.
Needs the lupa package (an embedded Lua 5.1):  uv run --with lupa python tools/check_newsfilter.py
"""
from pathlib import Path
import ast
import sys

try:
    from lupa import lua51
except ImportError:
    sys.exit('FAIL: needs lupa (Lua 5.1 for Python). Run: uv run --with lupa python tools/check_newsfilter.py')

root = Path(__file__).resolve().parents[1]
FILES = ['Theme.lua', 'Lines.lua', 'Pals.lua', 'Map.lua', 'Options.lua']

# the stub WoW API is shared with check_volume.py (importing it would run its checks)
STUBS = next(node.value.value for node in ast.parse((root / 'tools' / 'check_volume.py').read_text(encoding='utf-8')).body
             if isinstance(node, ast.Assign) and getattr(node.targets[0], 'id', None) == 'STUBS')

# a guild to send to, a recorded SendAddonMessage, recorded font strings and check states, a counted toast Show
EXTRA = r'''
function Ambiguate(name, mode)
    if mode == "short" then return (name:gsub("%-.*$", "")) end
    return (name:gsub("%-Home$", ""))
end
function UnitFactionGroup() return "Alliance", "Alliance" end
function IsInGuild() return true end
function IsInRaid() return false end
RAID_CLASS_COLORS = { MAGE = { r = 0.25, g = 0.78, b = 0.92 }, PALADIN = { r = 0.96, g = 0.55, b = 0.73 } }
sent, fontStrings, banners, shows = {}, {}, {}, 0
C_ChatInfo = {
    RegisterAddonMessagePrefix = function() end,
    SendAddonMessage = function(prefix, msg, chan, target)
        sent[#sent + 1] = table.concat({ prefix, msg, chan, tostring(target) }, " | ")
        return true
    end,
}
local baseCreateFrame = CreateFrame
function CreateFrame(...)
    local f = baseCreateFrame(...)
    f.CreateFontString = function(self)
        local fs = baseCreateFrame("FontString")
        fontStrings[#fontStrings + 1] = fs
        return fs
    end
    f.SetChecked = function(self, v) self.__checked = v end
    return f
end
function RecordToast()
    KodoTimesToast.text.SetText = function(self, s) banners[#banners + 1] = s end
    KodoTimesToast.Show = function() shows = shows + 1 end
    rawset(KodoTimesToast, "moving", false)
end
function ShowAll()   -- let every queued banner run its time
    for _ = 1, 50 do KodoTimesToast.__scripts.OnUpdate(KodoTimesToast, 100) end
end
'''

PALS = '|cffa88bff[Kodo Times]|r '
SHOW_KEYS = ['showLevel', 'showDeath', 'showSkill', 'showCraftBlue', 'showCraftEpic', 'showEpicLoot']
KIND_KEY = {'levelup': 'showLevel', 'levelround': 'showLevel', 'level60': 'showLevel',
            'death': 'showDeath', 'deathlegend': 'showDeath', 'skill': 'showSkill',
            'craftblue': 'showCraftBlue', 'craftepic': 'showCraftEpic', 'epicloot': 'showEpicLoot'}
ALL_OFF = {k: False for k in SHOW_KEYS}

failures = []


def check(cond, what):
    if not cond:
        failures.append(what)


def fresh(saved=None):
    lua = lua51.LuaRuntime(unpack_returned_tuples=True)
    lua.execute(STUBS)
    lua.execute(EXTRA)
    g = lua.globals()
    if saved is not None:
        g.KodoTimesDB = lua.table_from(saved)
    for name in FILES:
        g.LoadAddonFile((root / 'KodoTimes' / name).read_text(encoding='utf-8'), name)
    g.FireEvent('ADDON_LOADED', 'KodoTimes')
    g.RecordToast()
    return lua, g, g.NS


def news(g):
    return [line for line in g.printed.values() if line.startswith(PALS)]


def shown(g):
    """(chat lines, sounds played, toast Show calls, banner texts) once every queued banner has run its time."""
    g.ShowAll()
    return len(news(g)), len(g.played), g.shows, len(g.banners)


def message(kind, msg_id, level='12', cls='MAGE', item=('', '', ''), skill=('', '')):
    return '~'.join(['1', kind, msg_id, level, 'Barrens', *skill, *item, cls, '', '', 'Miss Mcimbtyw'])


def receive(g, msg, sender='Miss-Home'):
    g.FireEvent('CHAT_MSG_ADDON', 'MOTEVEPAL', msg, 'GUILD', sender)


NOTHING = (0, 0, 0, 0)
ONE = (1, 1, 1, 1)

# saved values: a new profile and an old one without the keys get true, a saved false stays false
_, g, ns = fresh()
check(all(g.KodoTimesDB[k] is True for k in SHOW_KEYS), 'new profile: not every show* key is true')
_, g, ns = fresh({'sound': True, 'time': 8, 'chat': False})
check(all(g.KodoTimesDB[k] is True for k in SHOW_KEYS), 'old profile without show* keys: not every one is true')
for key in SHOW_KEYS:
    _, g, ns = fresh({key: False})
    check(g.KodoTimesDB[key] is False, f'a saved {key} = false did not stay false')
    check(all(g.KodoTimesDB[k] is True for k in SHOW_KEYS if k != key), f'a saved {key} = false changed another key')

# ns.WantsKind: every kind follows its own switch, an unknown kind is always wanted
for kind, key in KIND_KEY.items():
    _, g, ns = fresh()
    check(ns.WantsKind(kind) is True, f'WantsKind({kind!r}) is not true with every switch on')
    g.KodoTimesDB[key] = False
    check(ns.WantsKind(kind) is False, f'WantsKind({kind!r}) is not false with {key} off')
    others = [k for k, v in KIND_KEY.items() if v != key]
    check(all(ns.WantsKind(k) is True for k in others), f'{key} off also hid {[k for k in others if not ns.WantsKind(k)]}')
_, g, ns = fresh(ALL_OFF)
for kind in ['welcome', 'nosuchkind', None]:
    check(ns.WantsKind(kind) is True, f'WantsKind({kind!r}) is not true for an unknown kind')

# incoming news: every switch on shows each kind (chat line, sound, toast); its own switch off hides it all
SAMPLES = {
    'levelup': message('levelup', '101', level='15'),
    'levelround': message('levelround', '102', level='30'),
    'level60': message('level60', '103', level='60'),
    'death': message('death', '104'),
    'skill': message('skill', '105', skill=('Blacksmithing', '150')),
    'craftblue': message('craftblue', '106', item=('7960', 'Truesilver Champion', '3')),
    'craftepic': message('craftepic', '107', item=('12798', 'Annihilator', '4')),
    'epicloot': message('epicloot', '108', item=('2243', 'Hand of Edward the Odd', '4')),
}
for kind, msg in SAMPLES.items():
    _, g, ns = fresh()
    receive(g, msg)
    check(shown(g) == ONE, f'{kind} with every switch on: (chat, sound, toast, banner) is {shown(g)}, expected {ONE}')
    _, g, ns = fresh({KIND_KEY[kind]: False})
    receive(g, msg)
    check(shown(g) == NOTHING, f'{kind} with {KIND_KEY[kind]} off: (chat, sound, toast, banner) is {shown(g)}, expected nothing')
    check(g.NS.WhisperPals is not None and 'Miss' in list(g.KodoTimesDB.knownPals.keys()),
          f'{kind} with {KIND_KEY[kind]} off: the sender was not noted as a pal')

# the legend variant of a death (a PALADIN, the legend roll forced): shown with showDeath on, hidden with it off
for show in (True, False):
    lua, g, ns = fresh({'showDeath': show})
    lua.execute('math.random = function(a, b) return a or 0 end')
    receive(g, message('death', '201', cls='PALADIN'))
    got = shown(g)
    if show:
        check(got == ONE, f'legend death with showDeath on: {got}, expected {ONE}')
        check(lua.eval('NS.TITLES.deathlegend') == g.KodoTimesToast.title.__text,
              'the forced legend death did not show as deathlegend (the control case is broken)')
    else:
        check(got == NOTHING, f'legend death with showDeath off: {got}, expected nothing')

# only showDeath off: a levelup still brings its chat line, sound and toast
_, g, ns = fresh({'showDeath': False})
receive(g, SAMPLES['death'])
receive(g, SAMPLES['levelup'])
check(shown(g) == ONE, f'levelup with only showDeath off: {shown(g)}, expected {ONE}')
check(g.KodoTimesToast.title.__text == g.NS.TITLES.levelup, 'with only showDeath off the toast is not the levelup one')

# enabled = false: nothing shows, every show* key on
lua, g, ns = fresh({'enabled': False, 'selfToast': True})
receive(g, SAMPLES['levelup'])
receive(g, SAMPLES['death'])
g.FireEvent('PLAYER_DEAD')
g.FireEvent('PLAYER_LEVEL_UP', 20)
check(shown(g) == NOTHING, f'enabled = false still showed {shown(g)}')
check(len(g.sent) == 0, 'enabled = false still sent news')


# your own death with selfToast: no local line or sound with showDeath off, the very same addon message goes out
def own_death(show):
    lua, g, ns = fresh({'selfToast': True, 'showDeath': show})
    lua.execute('math.randomseed(4242)')
    g.now = 123.4
    g.FireEvent('PLAYER_DEAD')
    return list(g.sent.values()), shown(g)


sent_on, got_on = own_death(True)
sent_off, got_off = own_death(False)
check(got_on == ONE, f'own death with showDeath on: {got_on}, expected {ONE} (the control case is broken)')
check(got_off == NOTHING, f'own death with showDeath off: {got_off}, expected nothing')
check(len(sent_on) > 0 and all('~death~' in s for s in sent_on), f'own death sent {sent_on!r}')
check(sent_off == sent_on, f'own death with showDeath off sent {sent_off!r}, with it on {sent_on!r}')
# every switch off: your own news still go out
lua, g, ns = fresh(dict(ALL_OFF, selfToast=True))
g.FireEvent('PLAYER_LEVEL_UP', 20)
check(shown(g) == NOTHING, f'own levelround with showLevel off: {shown(g)}, expected nothing')
check(len(g.sent) > 0 and all('~levelround~' in s for s in g.sent.values()), 'own levelround with every switch off was not sent')

# /kodo test is never filtered
_, g, ns = fresh()
g.SlashCmdList.KODOTIMES('test')
unfiltered = shown(g)
_, g, ns = fresh(ALL_OFF)
g.SlashCmdList.KODOTIMES('test')
filtered = shown(g)
check(unfiltered[0] == 9 and unfiltered[3] == 9, f'/kodo test without filtering: {unfiltered}, expected 9 news')
check(filtered == unfiltered, f'/kodo test with every switch off: {filtered}, without filtering {unfiltered}')

# switched back on: what came while off never shows (not even when it arrives again), new news do
_, g, ns = fresh({'chat': True})
checks = {f.opt.key: f for f in g.frames.values() if f.__kind == 'CheckButton' and f.opt}
death = checks['showDeath']
death.GetChecked = lambda self: False
death.__scripts.OnClick(death)
receive(g, message('death', '301'))
check(shown(g) == NOTHING, f'death while off: {shown(g)}')
death.GetChecked = lambda self: True
death.__scripts.OnClick(death)
check(shown(g) == NOTHING, f'switching showDeath back on replayed {shown(g)}')
receive(g, message('death', '301'), 'Miss-Home')   # the same news again (another channel)
check(shown(g) == NOTHING, f'a news seen while off showed after switching back on: {shown(g)}')
receive(g, message('death', '302'))
check(shown(g) == ONE, f'a new death after switching back on: {shown(g)}, expected {ONE}')

# the options panel: header and six checkboxes in the right column, tooltips, writes and Refresh
_, g, ns = fresh()
fs = [f for f in g.fontStrings.values()]
heads = [f for f in fs if f.__text == 'Milyen híreket lássak']
check(len(heads) == 1, f'{len(heads)} "Milyen híreket lássak" headers, expected 1')
COL2 = 340
check(heads and heads[0].__point[2] == COL2, f'the header is at x {heads and heads[0].__point[2]}, expected the right column ({COL2})')
boxes = [f for f in g.frames.values() if f.__kind == 'CheckButton' and f.opt]
by_key = {f.opt.key: f for f in boxes}
LABELS = [('showLevel', 'Szintlépés'), ('showDeath', 'Halál'), ('showSkill', 'Szakma'),
          ('showCraftBlue', 'Kék craft'), ('showCraftEpic', 'Epic craft'), ('showEpicLoot', 'Epic loot')]
check([f.opt.key for f in boxes if f.opt.key in SHOW_KEYS] == SHOW_KEYS, 'the six checkboxes are missing or out of order')
head_y = heads[0].__point[3] if heads else 0
prev_y = head_y
for key, label in LABELS:
    cb = by_key.get(key)
    if cb is None:
        check(False, f'no checkbox for {key}')
        continue
    check(cb.opt.text == label, f'{key} is labelled {cb.opt.text!r}, expected {label!r}')
    check(cb.__point[2] == COL2 + 4, f'{key} is at x {cb.__point[2]}, not in the right column')
    check(cb.__point[3] < prev_y, f'{key} is not under the header / the row above it')
    prev_y = cb.__point[3]
    tip = cb.opt.tip
    check(isinstance(tip, str) and tip.strip() != '', f'{key} has no tooltip')
    check(isinstance(tip, str) and 'nálad' in tip and 'haverok' in tip and 'ugyanúgy megkapják' in tip,
          f'the {key} tooltip does not say it is only what shows up here: {tip!r}')
check('kerek' in by_key['showLevel'].opt.tip and '60' in by_key['showLevel'].opt.tip, 'the Szintlépés tooltip does not mention the round and the 60 level')
check('legendás' in by_key['showDeath'].opt.tip, 'the Halál tooltip does not mention the legend death')
# the tooltip shows the text when hovered
added = []
g.NS.Tooltip.AddLine = lambda self, text, *rest: added.append(text)
g.NS.Tooltip.SetOwner = lambda self, *rest: None
g.NS.ShowTooltip = lambda: None
for key in SHOW_KEYS:
    by_key[key].__scripts.OnEnter(by_key[key])
check(all(by_key[k].opt.tip in added for k in SHOW_KEYS), 'hovering a news switch did not show its tooltip')

# clicks write the key at once; Refresh shows the saved state
for key in SHOW_KEYS:
    cb = by_key[key]
    cb.GetChecked = lambda self: None
    cb.__scripts.OnClick(cb)
    check(g.KodoTimesDB[key] is False, f'unticking {key} stored {g.KodoTimesDB[key]!r}, expected false')
    cb.GetChecked = lambda self: 1
    cb.__scripts.OnClick(cb)
    check(g.KodoTimesDB[key] is True, f'ticking {key} stored {g.KodoTimesDB[key]!r}, expected true')
saved = {'showLevel': False, 'showDeath': True, 'showSkill': False, 'showCraftBlue': True, 'showCraftEpic': False, 'showEpicLoot': True}
for key, v in saved.items():
    g.KodoTimesDB[key] = v
g.KodoTimesOptions.__scripts.OnShow(g.KodoTimesOptions)
for key, v in saved.items():
    check(by_key[key].__checked is v, f'after Refresh the {key} box shows {by_key[key].__checked!r}, expected {v}')

# layout: the time row sits under the new block, the button rows stay above -540
last_y = by_key['showEpicLoot'].__point[3]
time_label = [f for f in fs if f.__text == 'Meddig maradjon kint egy hír']
check(len(time_label) == 1, 'no "Meddig maradjon kint egy hír" row')
time_y = time_label[0].__point[3] if time_label else 0
check(time_label and time_label[0].__point[2] == COL2, 'the time row left the right column')
check(time_y <= last_y - 26, f'the time row (y {time_y}) overlaps the last news switch (y {last_y}, 26 px high)')
buttons = {f.__text: f for f in g.frames.values() if f.__kind == 'Button' and f.__text}
for text in ['Minta-hírek (nálam)', 'Felugró ablak mozgatása', 'Kapcsolat-teszt (ping)', 'Ki hol van (chatbe)', 'Diagnosztika (chatbe)']:
    b = buttons.get(text)
    if b is None:
        check(False, f'no {text!r} button')
        continue
    y = b.__point[3]
    check(y >= -540, f'the {text!r} button is at y {y}, below -540')
    check(y <= time_y - 22, f'the {text!r} button (y {y}) overlaps the time row (y {time_y})')

if failures:
    print('FAIL:')
    for failure in failures:
        print('  ' + failure)
    sys.exit(1)
print('PASS: show* switches default on and keep a saved false; incoming and own news are hidden per kind (legend death and '
      'round / 60 levels too) while sending, /kodo test and duplicate filtering stay as they were; panel block, tooltips and layout')
