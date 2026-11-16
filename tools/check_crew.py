"""Check that the crew channel is gone (0.10.7): nothing is sent to a CHANNEL, no channel is joined, a stored
db.crew moves to db.legacyCrew, and every character leaves the old channel once (char.crewGone).
And that the addon talks over the guild only (0.10.8): every send is GUILD (no WHISPER, PARTY, RAID or
INSTANCE_CHAT), and a character without a guild sends nothing at all - whispers to offline pals made the server print
"No player named '...' is currently playing." for each.

Runs the addon in Lua 5.1 with the stub WoW API of tools/check_volume.py, plus recorded addon messages, chat channels
and a friends list.
Needs the lupa package (an embedded Lua 5.1):  uv run --with lupa python tools/check_crew.py
"""
from pathlib import Path
import ast
import sys

try:
    from lupa import lua51
except ImportError:
    sys.exit('FAIL: needs lupa (Lua 5.1 for Python). Run: uv run --with lupa python tools/check_crew.py')

root = Path(__file__).resolve().parents[1]
FILES = ['Theme.lua', 'Lines.lua', 'Pals.lua', 'Map.lua', 'Options.lua']

# the stub WoW API is shared with check_volume.py (importing it would run its checks)
STUBS = next(node.value.value for node in ast.parse((root / 'tools' / 'check_volume.py').read_text(encoding='utf-8')).body
             if isinstance(node, ast.Assign) and getattr(node.targets[0], 'id', None) == 'STUBS')

# chat channels the character is in (name -> id), "stuck" ones that a leave does not remove, recorded sends,
# joins and leaves; a guild, a party and one online friend to send to (each can be switched off)
EXTRA = r'''
sent, joined, left, channels, stuck = {}, {}, {}, {}, {}
inGuild, inGroup = true, true
friends = { { name = "Buddy", connected = true } }
LE_PARTY_CATEGORY_INSTANCE = 2
function IsInGuild() return inGuild end
function IsInGroup(category) return inGroup and category == nil end
function IsInRaid() return false end
function UnitFactionGroup() return "Horde", "Horde" end
C_ChatInfo = {
    RegisterAddonMessagePrefix = function() end,
    SendAddonMessage = function(prefix, msg, chan, target)
        sent[#sent + 1] = { prefix = prefix, msg = msg, chan = chan, target = target }
        return true
    end,
}
C_FriendList = {
    ShowFriends = function() end,
    GetNumFriends = function() return #friends end,
    GetFriendInfoByIndex = function(i) return friends[i] end,
}
function GetChannelName(name) return channels[name] or 0 end
function LeaveChannelByName(name)
    left[#left + 1] = name
    if not stuck[name] then channels[name] = nil end
end
function JoinTemporaryChannel(name) joined[#joined + 1] = name end
function JoinChannelByName(name) joined[#joined + 1] = name end
'''

GONE = 'a crew csatorna megszűnt'
failures = []


def check(cond, what):
    if not cond:
        failures.append(what)


def fresh(saved=None, char=None, channels=None):
    lua = lua51.LuaRuntime(unpack_returned_tuples=True)
    lua.execute(STUBS)
    lua.execute(EXTRA)
    g = lua.globals()
    if saved is not None:
        g.KodoTimesDB = lua.table_from(saved)
    if char is not None:
        g.KodoTimesChar = lua.table_from(char)
    for name, cid in (channels or {}).items():
        g.channels[name] = cid
    for name in FILES:
        g.LoadAddonFile((root / 'KodoTimes' / name).read_text(encoding='utf-8'), name)
    g.FireEvent('ADDON_LOADED', 'KodoTimes')
    return lua, g, g.NS


def sends(g):
    return [(s.chan, s.target, s.msg) for s in g.sent.values()]


def lines(g):
    return list(g.printed.values())


def scalars(table):
    """The plain values of a saved-variables table, to hand to the next session (another Lua runtime)."""
    return {k: v for k, v in table.items() if isinstance(v, (str, bool, int, float))}


# sending: SendAll, a news Announce and a position send reach the guild only (not the party or the online friend),
# never a CHANNEL, even with an old db.crew set again after loading and the character still in that channel
_, g, ns = fresh({'crew': 'MPhaverok'}, {'welcomed': True, 'crewGone': True}, {'MPhaverok': 5})
g.KodoTimesDB.crew = 'MPhaverok'
ns.SendAll('X~test')
all_paths = sends(g)
check([(c, t) for c, t, _ in all_paths] == [('GUILD', None)],
      f'SendAll went to {[(c, t) for c, t, _ in all_paths]}, expected the guild only')
n = len(g.sent)
g.SlashCmdList.KODOTIMES('kuld')
news = sends(g)[n:]
check(any(c == 'GUILD' and '~levelup~' in m for c, _, m in news), f'the news Announce did not go to the guild: {news}')
check({c for c, _, _ in news} == {'GUILD'}, f'the news Announce went to {[c for c, _, _ in news]}')
n = len(g.sent)
g.FireEvent('ZONE_CHANGED_NEW_AREA')
g.Advance(1)
pos = sends(g)[n:]
check(any(c == 'GUILD' and m.startswith('P~') for c, _, m in pos), f'no position was sent to the guild: {pos}')
check({c for c, _, _ in pos} == {'GUILD'}, f'the position went to {[c for c, _, _ in pos]}')


# a whole session with the online friend, a party and a remembered pal (knownPals, now offline): the login hellos,
# a zone change, a test news, an incoming PING, hello and position from a pal, and /kodo ping with and without a name
OFFLINE = 'Linathel Silverwind'


def session(in_guild):
    _, g, ns = fresh({'knownPals': {OFFLINE: {'d': OFFLINE, 't': 100}}}, {'welcomed': True, 'crewGone': True})
    g.inGuild = in_guild
    g.FireEvent('PLAYER_LOGIN')
    g.Advance(10)
    g.FireEvent('FRIENDLIST_UPDATE')
    g.Advance(3)
    g.FireEvent('ZONE_CHANGED_NEW_AREA')
    g.Advance(2)
    g.SlashCmdList.KODOTIMES('kuld')
    g.FireEvent('CHAT_MSG_ADDON', 'MOTEVEPAL', 'PING~abcdef~Miss Mcimbtyw', 'WHISPER', 'Miss')
    g.FireEvent('CHAT_MSG_ADDON', 'MOTEVEPAL', 'H~abcdef~Miss Mcimbtyw', 'WHISPER', 'Miss')
    g.FireEvent('CHAT_MSG_ADDON', 'MOTEVEPAL', 'P~1413~5000~5000~20~MAGE~0~Barrens~abcdef~Miss Mcimbtyw~', 'GUILD', 'Miss')
    g.Advance(5)
    g.SlashCmdList.KODOTIMES('ping')
    g.SlashCmdList.KODOTIMES('ping ' + OFFLINE)
    g.Advance(30)
    return g, ns


# no guild: not a single addon message - no whisper (so no "No player named ..." line), no party, no guild
g, ns = session(False)
check(len(g.sent) == 0, f'without a guild the addon sent {[(c, t, m[:12]) for c, t, m in sends(g)]}')
ns.SendAll('X~test')
ns.RawSend('X~test', 'WHISPER', OFFLINE)
ns.RawSend('X~test', 'PARTY')
check(len(g.sent) == 0, f'without a guild SendAll / RawSend sent {sends(g)}')
check(ns.RawSend('X~test', 'WHISPER', OFFLINE) is True, 'a dropped send does not return true (ns.Deliver would retry)')
check(ns.Whisper is None and ns.WhisperPals is None, 'ns.Whisper / ns.WhisperPals still exist')

# in a guild: the same session sends over GUILD only, and something did go out (news, position, PONG, PINGs)
g, ns = session(True)
check(len(g.sent) > 0 and all(s.chan == 'GUILD' and s.target is None for s in g.sent.values()),
      f'in a guild something went elsewhere than GUILD: {sorted({(c, t) for c, t, _ in sends(g)}, key=str)}')
msgs = [m for _, _, m in sends(g)]
for start in ('1~levelup~', 'P~', 'PONG~', 'PING~'):
    check(any(m.startswith(start) for m in msgs), f'in a guild no {start} went to the guild: {msgs}')
check(any(m.startswith('PONG~') and m.endswith('~abcdef') for m in msgs), f'the PONG does not name the pinger: {msgs}')
check(any(m.startswith('PING~') and m.endswith('~' + OFFLINE) for m in msgs), f'/kodo ping <name> is not addressed: {msgs}')
# /kodo guild off: nothing goes out even in a guild
_, g, ns = fresh({'guild': False}, {'welcomed': True, 'crewGone': True})
g.FireEvent('PLAYER_LOGIN')
g.Advance(10)
g.SlashCmdList.KODOTIMES('kuld')
g.SlashCmdList.KODOTIMES('ping')
check(len(g.sent) == 0, f'with /kodo guild off the addon sent {sends(g)}')

# a guild PING or PONG meant for someone else: no answer, no line
_, g, ns = fresh(None, {'welcomed': True, 'crewGone': True})
n = len(g.printed)
g.FireEvent('CHAT_MSG_ADDON', 'MOTEVEPAL', 'PING~abcdef~Miss Mcimbtyw~Somebodyelse', 'GUILD', 'Miss')
g.FireEvent('CHAT_MSG_ADDON', 'MOTEVEPAL', 'PONG~abcdef~Miss Mcimbtyw~000000', 'GUILD', 'Miss')
check(not any(s.msg.startswith('PONG~') for s in g.sent.values()), 'a PING for another player was answered')
check(not any('PING' in line or 'PONG' in line for line in lines(g)[n:]), f'a PING / PONG for another player printed {lines(g)[n:]}')
g.FireEvent('CHAT_MSG_ADDON', 'MOTEVEPAL', 'PONG~abcdef~Miss Mcimbtyw~' + ns.TOKEN, 'GUILD', 'Miss')
check(any('PONG' in line for line in lines(g)[n:]), 'a PONG for us printed nothing')
check(all(c != 'CHANNEL' for c, _, _ in sends(g)), f'something was sent to a CHANNEL: {sends(g)}')
check(all(s.prefix == 'MOTEVEPAL' for s in g.sent.values()), 'a message left without the MOTEVEPAL prefix')
check(ns.JoinCrew is None, 'ns.JoinCrew still exists')

# moving off: a stored crew moves to legacyCrew once ADDON_LOADED ran, a custom one too; a new install has neither
for old in ('MPhaverok', 'MPkodo'):
    _, g, _ = fresh({'crew': old})
    check(g.KodoTimesDB.crew is None and g.KodoTimesDB.legacyCrew == old,
          f'crew {old!r} became crew {g.KodoTimesDB.crew!r}, legacyCrew {g.KodoTimesDB.legacyCrew!r}')
_, g, _ = fresh()
check(g.KodoTimesDB.crew is None and g.KodoTimesDB.legacyCrew is None, 'a new install got a crew or legacyCrew')

# first login of a character in MPhaverok: it leaves at 5 s, and is done only at the last try, with the channel gone
_, g, _ = fresh({'crew': 'MPhaverok', 'welcomed': True}, {'welcomed': True}, {'MPhaverok': 5})
g.FireEvent('PLAYER_LOGIN')
g.Advance(4.9)
check(len(g.left) == 0, 'the old channel was left before 5 s')
g.Advance(0.2)
check(list(g.left.values()) == ['MPhaverok'], f'at 5 s left {list(g.left.values())}, expected MPhaverok')
check(g.KodoTimesChar.crewGone is None, 'crewGone was set at the first try')
g.Advance(24.8)
check(g.KodoTimesChar.crewGone is None, 'crewGone was set before the last try (30 s)')
g.Advance(0.2)
check(g.KodoTimesChar.crewGone is True and g.GetChannelName('MPhaverok') == 0,
      'crewGone is not true at 30 s with the channel gone')
check(list(g.left.values()) == ['MPhaverok'], f'left {list(g.left.values())}, expected one leave')
check(len(g.joined) == 0, f'joined {list(g.joined.values())}')
first_db = scalars(g.KodoTimesDB)

# a second character of the same account: fresh KodoTimesChar, the shared DB (crew already moved) - leaves once too
_, g, _ = fresh(first_db, {}, {'MPhaverok': 3})
check(g.KodoTimesDB.legacyCrew == 'MPhaverok', 'the shared DB lost legacyCrew')
g.FireEvent('PLAYER_LOGIN')
g.Advance(60)
check(list(g.left.values()) == ['MPhaverok'], f'the second character left {list(g.left.values())}, expected MPhaverok once')
check(g.KodoTimesChar.crewGone is True, 'the second character did not get crewGone')

# a custom crew: both it and MPhaverok are left, each once
_, g, _ = fresh({'crew': 'MPkodo'}, {}, {'MPkodo': 4, 'MPhaverok': 5})
g.FireEvent('PLAYER_LOGIN')
g.Advance(60)
check(sorted(g.left.values()) == ['MPhaverok', 'MPkodo'], f'with a custom crew left {list(g.left.values())}')
check(g.KodoTimesChar.crewGone is True, 'with a custom crew crewGone was not set')

# a retry while the channel still reports joined: left again at 15 s, done at 30 s once it reports 0
_, g, _ = fresh({'legacyCrew': 'MPhaverok'}, {}, {'MPhaverok': 5})
g.stuck.MPhaverok = True
g.FireEvent('PLAYER_LOGIN')
g.Advance(10)
g.stuck.MPhaverok = None
g.Advance(50)
check(list(g.left.values()) == ['MPhaverok', 'MPhaverok'], f'the retry left {list(g.left.values())}, expected two leaves')
check(g.KodoTimesChar.crewGone is True, 'crewGone was not set after the retry worked')

# every try sees the channel joined: the flag stays unset, and the next login tries again
_, g, _ = fresh({'legacyCrew': 'MPhaverok'}, {}, {'MPhaverok': 5})
g.stuck.MPhaverok = True
g.FireEvent('PLAYER_LOGIN')
g.Advance(60)
check(len(g.left) == 3, f'a stuck channel was left {len(g.left)} times, expected 3 tries')
check(g.KodoTimesChar.crewGone is None, 'crewGone was set while the channel still reported joined')
_, g, _ = fresh({'legacyCrew': 'MPhaverok'}, scalars(g.KodoTimesChar), {'MPhaverok': 5})
g.FireEvent('PLAYER_LOGIN')
g.Advance(60)
check(list(g.left.values()) == ['MPhaverok'] and g.KodoTimesChar.crewGone is True, 'the next login did not try again')

# a character never in the channel: no leave, done at the last try
_, g, _ = fresh({'legacyCrew': 'MPhaverok'}, {})
g.FireEvent('PLAYER_LOGIN')
g.Advance(60)
check(len(g.left) == 0 and g.KodoTimesChar.crewGone is True, 'a character outside the channel left it or was not done')

# crewGone = true: no leave on later logins, even if the channel shows up
_, g, _ = fresh({'legacyCrew': 'MPhaverok'}, {'welcomed': True, 'crewGone': True}, {'MPhaverok': 5})
g.FireEvent('PLAYER_LOGIN')
g.Advance(60)
check(len(g.left) == 0, f'a crewGone character left {list(g.left.values())}')

# /kodo crew haverok: no crew, no join, only says that the channel is gone
_, g, _ = fresh(None, {'welcomed': True, 'crewGone': True})
g.SlashCmdList.KODOTIMES('crew haverok')
check(g.KodoTimesDB.crew is None, f'/kodo crew haverok set crew {g.KodoTimesDB.crew!r}')
check(len(g.joined) == 0, f'/kodo crew haverok joined {list(g.joined.values())}')
check(GONE in lines(g)[-1], f'/kodo crew haverok printed {lines(g)[-1]!r}')
g.SlashCmdList.KODOTIMES('crew')
check(GONE in lines(g)[-1] and g.KodoTimesDB.crew is None, f'/kodo crew printed {lines(g)[-1]!r}')

# /kodo ping: the guild only, no crew entry, even with db.crew set and the channel joined
_, g, _ = fresh(None, {'welcomed': True, 'crewGone': True}, {'MPhaverok': 5})
g.KodoTimesDB.crew = 'MPhaverok'
g.SlashCmdList.KODOTIMES('ping')
ping = [line for line in lines(g) if 'PING elküldve' in line]
check(len(ping) == 1 and 'PING elküldve: guild.' in ping[0], f'/kodo ping printed {ping}')
check(not any('crew' in line.lower() for line in lines(g)), f'/kodo ping mentions crew: {lines(g)}')
check(all(c != 'CHANNEL' for c, _, _ in sends(g)), '/kodo ping sent to a CHANNEL')
# no path at all: the hint names the guild and the group, not /kodo crew
_, g, _ = fresh(None, {'welcomed': True, 'crewGone': True})
g.inGuild, g.inGroup = False, False
g.friends[1].connected = False
g.SlashCmdList.KODOTIMES('ping')
check('Nincs semmi' in lines(g)[-1] and 'guild' in lines(g)[-1] and 'crew' not in lines(g)[-1],
      f'/kodo ping with no path printed {lines(g)[-1]!r}')

# the 12 s login hint, the status line, the help and /kodo diag: no crew
_, g, _ = fresh(None, {'welcomed': True, 'crewGone': True})
g.inGuild, g.inGroup = False, False
g.friends[1].connected = False
g.FireEvent('PLAYER_LOGIN')
g.Advance(13)
hint = [line for line in lines(g) if 'nem éred el a haverokat' in line]
check(len(hint) == 1 and 'crew' not in hint[0] and 'guild' in hint[0], f'the 12 s hint is {hint}')
for cmd in ('', 'diag'):
    n = len(g.printed)
    g.SlashCmdList.KODOTIMES(cmd)
    out = lines(g)[n:]
    check(out and not any('crew' in line.lower() for line in out), f'/kodo {cmd} mentions crew: {out}')
check(len(g.joined) == 0, f'joined {list(g.joined.values())}')

if failures:
    print('FAIL:')
    for failure in failures:
        print('  ' + failure)
    sys.exit(1)
print('PASS: guild only - without a guild nothing is sent, in one only GUILD (no WHISPER / PARTY); '
      'no CHANNEL sends or joins; crew moves to legacyCrew; every character leaves the old channel once '
      '(crewGone only once it reports 0); /kodo crew, ping, status, help, diag and the login hint have no crew')
