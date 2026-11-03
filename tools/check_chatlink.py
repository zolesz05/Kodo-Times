"""Check the [Kodo Times] chat news lines: the name is a player link (left-click whispers), the banner keeps the plain name.

Runs the addon in Lua 5.1 with the stub WoW API of tools/check_volume.py.
Needs the lupa package (an embedded Lua 5.1):  uv run --with lupa python tools/check_chatlink.py
"""
from pathlib import Path
import ast
import sys

try:
    from lupa import lua51
except ImportError:
    sys.exit('FAIL: needs lupa (Lua 5.1 for Python). Run: uv run --with lupa python tools/check_chatlink.py')

root = Path(__file__).resolve().parents[1]
FILES = ['Theme.lua', 'Lines.lua', 'Pals.lua', 'Map.lua', 'Options.lua']

# the stub WoW API is shared with check_volume.py (importing it would run its checks)
STUBS = next(node.value.value for node in ast.parse((root / 'tools' / 'check_volume.py').read_text(encoding='utf-8')).body
             if isinstance(node, ast.Assign) and getattr(node.targets[0], 'id', None) == 'STUBS')

# Ambiguate as the client does it, with our realm "Home"; the banner's body text is recorded
EXTRA = r'''
function Ambiguate(name, mode)
    if mode == "short" then return (name:gsub("%-.*$", "")) end
    return (name:gsub("%-Home$", ""))
end
function UnitFactionGroup() return "Alliance", "Alliance" end
banners = {}
function RecordBanners()
    KodoTimesToast.text.SetText = function(self, s) banners[#banners + 1] = s end
    rawset(KodoTimesToast, "moving", false)
end
function ShowAll()   -- let every queued banner run its time
    for _ = 1, 50 do KodoTimesToast.__scripts.OnUpdate(KodoTimesToast, 100) end
end
'''

PALS = '|cffa88bff[Kodo Times]|r '
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
    g.RecordBanners()
    return lua, g, g.NS


def news(g):
    return [line[len(PALS):] for line in g.printed.values() if line.startswith(PALS)]


def banners(g):
    g.ShowAll()
    return list(g.banners.values())


def message(kind, msg_id, name, killer='', level='12', item=('', '', '')):
    return '~'.join(['1', kind, msg_id, level, 'Barrens', '', '', *item, 'MAGE', killer, '', name])


# /kodo test: every chat line links your own character, the banners are the same lines unlinked
_, g, ns = fresh({'chat': True})
g.SlashCmdList.KODOTIMES('test')
chat, shown = news(g), banners(g)
link = '|Hplayer:Tester|h[Tester]|h'
check(len(chat) == 9 and len(shown) == 9, f'/kodo test printed {len(chat)} news and showed {len(shown)} banners, expected 9 each')
for line, banner in zip(chat, shown):
    check('|Hplayer' not in banner, f'a banner has a player link: {banner!r}')
    check(line.replace(link, 'Tester') == banner, f'chat line {line!r} is not the banner {banner!r} with the name linked')
    check(line.count(link) == banner.count('Tester'), f'not every name is linked in {line!r}')
check(sum(line.count(link) for line in chat) >= 8, 'the /kodo test chat lines have almost no player links')
death = chat[1]
check(death.endswith('  |cffff8866Tettes: Defias Pillager (14)|r'), f'the death line lost its plain killer suffix: {death!r}')



# fixed lines from here on, so the exact texts can be checked
def fixed(saved=None):
    lua, g, ns = fresh(saved)
    lua.execute('NS.LINES_AT = nil; NS.LEGENDS = {}')
    for kind, line in [('levelup', 'DING! %n: %l'), ('death', 'RIP %n, %z'), ('epicloot', 'EPIC %n: %i')]:
        lua.execute(f'NS.LINES["{kind}"] = {{ "{line}" }}')
    return lua, g, ns


def receive(g, msg, sender):
    g.FireEvent('CHAT_MSG_ADDON', 'MOTEVEPAL', msg, 'WHISPER', sender)


# a pal from another realm with a two-part display name: the link whispers Name-Realm, shows the second part
_, g, ns = fixed({'chat': True})
receive(g, message('levelup', '11', 'Higgsbozon Lightchaser'), 'Higgsbozon-Other')
receive(g, message('death', '12', 'Higgsbozon Lightchaser', killer='Hogger'), 'Higgsbozon-Other')
receive(g, message('epicloot', '13', 'Higgsbozon Lightchaser', item=('2243', 'Hand of Edward the Odd', '4')), 'Higgsbozon-Other')
chat, shown = news(g), banners(g)
link = '|Hplayer:Higgsbozon-Other|h[Lightchaser]|h'
item = '|cffa335ee|Hitem:2243::::::::|h[Hand of Edward the Odd]|h|r'
check(chat == [f'DING! {link}: 12', f'RIP {link}, Barrens  |cffff8866Tettes: Hogger|r', f'EPIC {link}: {item}'],
      f'cross-realm chat lines: {chat!r}')
check(shown == ['DING! Lightchaser: 12', 'RIP Lightchaser, Barrens  |cffff8866Tettes: Hogger|r', f'EPIC Lightchaser: {item}'],
      f'cross-realm banners: {shown!r}')

# a pal from our realm: no realm in the whisper target
_, g, ns = fixed({'chat': True})
receive(g, message('levelup', '21', 'Miss Mcimbtyw'), 'Miss-Home')
check(news(g) == ['DING! |Hplayer:Miss|h[Mcimbtyw]|h: 12'], f'same-realm chat line: {news(g)!r}')
check(banners(g) == ['DING! Mcimbtyw: 12'], f'same-realm banner: {g.banners[1]!r}')

# a broken sender cannot break the link
_, g, ns = fixed({'chat': True})
receive(g, message('levelup', '31', 'Odd Name'), 'Od|d:-Other')
check(news(g) == ['DING! |Hplayer:Odd-Other|h[Name]|h: 12'], f'sanitised link: {news(g)!r}')

# chat off: no print, the banner as before
_, g, ns = fixed({'chat': True})
g.SlashCmdList.KODOTIMES('chat')
check(g.KodoTimesDB.chat is False, '/kodo chat did not switch chat output off')
receive(g, message('levelup', '41', 'Higgsbozon Lightchaser'), 'Higgsbozon-Other')
check(news(g) == [], f'chat off still printed {news(g)!r}')
check(banners(g) == ['DING! Lightchaser: 12'], f'chat off banner: {list(g.banners.values())!r}')

# your own news with /kodo self: whisper target is UnitName("player")
lua, g, ns = fixed({'chat': True, 'selfToast': True})
lua.execute('NS.Deliver = function() end')   # nothing to send to here
g.FireEvent('PLAYER_LEVEL_UP', 15)
check(news(g) == ['DING! |Hplayer:Tester|h[Tester]|h: 15'], f'own news chat line: {news(g)!r}')
check(banners(g) == ['DING! Tester: 15'], f'own news banner: {list(g.banners.values())!r}')

if failures:
    print('FAIL:')
    for failure in failures:
        print('  ' + failure)
    sys.exit(1)
print('PASS: [Kodo Times] chat lines link the name to the sender (realm kept cross-realm), banners and killer suffix unchanged')
