"""Check the addon's own sound volume (KodoTimesDB.volume) by running the addon in Lua 5.1 with a stub WoW API.

Needs the lupa package (an embedded Lua 5.1):  uv run --with lupa python tools/check_volume.py
"""
from pathlib import Path
import sys

try:
    from lupa import lua51
except ImportError:
    sys.exit('FAIL: needs lupa (Lua 5.1 for Python). Run: uv run --with lupa python tools/check_volume.py')

root = Path(__file__).resolve().parents[1]
FILES = ['Theme.lua', 'Lines.lua', 'Pals.lua', 'Map.lua', 'Options.lua']

# the bits of the WoW API the addon touches while loading, plus a clock, CVars and a PlaySound log
STUBS = r'''
now, timers, cvars, played, printed, frames = 0, {}, {}, {}, {}, {}
cvarWrites = {}
playFails = {}   -- channel -> "error" | "false"
local function Stub(name)
    return setmetatable({ __scripts = {}, __name = name }, { __index = function(t, k)
        if k == "SetScript" or k == "HookScript" then return function(self, n, f) self.__scripts[n] = f end end
        if k == "GetScript" then return function(self, n) return self.__scripts[n] end end
        if k:match("^Create") or k == "GetFontString" then return function() return Stub(k) end end
        if k:match("^Get") or k:match("^Is") then return function() return 1 end end
        return function() end
    end })
end
noSliderTemplate = false
function CreateFrame(kind, name, parent, template)
    if template == "OptionsSliderTemplate" and noSliderTemplate then error("unknown template") end
    local f = Stub(name or kind)
    f.__kind, f.__events, f.__alpha, f.__enabled = kind, {}, 1, true
    f.RegisterEvent = function(self, e) self.__events[e] = true end
    f.SetAlpha = function(self, a) self.__alpha = a end
    f.Enable = function(self) self.__enabled = true end
    f.Disable = function(self) self.__enabled = false end
    f.SetText = function(self, s) self.__text = s end
    f.SetPoint = function(self, ...) self.__point = { ... } end
    if kind == "Slider" then
        f.SetValue = function(self, v)
            if self.__value == v then return end
            self.__value = v
            local s = self.__scripts.OnValueChanged
            if s then s(self, v) end
        end
        f.GetValue = function(self) return self.__value end
    end
    frames[#frames + 1] = f
    if name then _G[name] = f end
    return f
end
UIParent = Stub("UIParent")
SlashCmdList = {}
C_Timer = { After = function(d, f) timers[#timers + 1] = { t = now + d, f = f } end, NewTicker = function() return Stub("ticker") end }
function Advance(dt)
    local target = now + dt
    while true do
        local best
        for i, tm in ipairs(timers) do if tm.t <= target and (not best or tm.t < timers[best].t) then best = i end end
        if not best then break end
        local tm = table.remove(timers, best)
        now = tm.t
        tm.f()
    end
    now = target
end
function GetTime() return now end
C_CVar = {
    GetCVar = function(n) return cvars[n] end,
    SetCVar = function(n, v) cvars[n] = tostring(v); cvarWrites[#cvarWrites + 1] = n end,
}
function PlaySound(id, channel)
    if playFails[channel] == "error" then error("bad channel") end
    if playFails[channel] == "false" then return false end
    local vol = { Dialog = "Sound_DialogVolume", Ambience = "Sound_AmbienceVolume", SFX = "Sound_SFXVolume" }
    played[#played + 1] = { id = id, channel = channel, level = vol[channel] and cvars[vol[channel]] }
    return true
end
function print(...) local t = {} for i = 1, select("#", ...) do t[i] = tostring(select(i, ...)) end printed[#printed + 1] = table.concat(t, " ") end
function UnitName() return "Tester" end
function UnitClass() return "Mage", "MAGE" end
function UnitLevel() return 10 end
function IsInGuild() return false end
function IsInGroup() return false end
function FireEvent(e, ...)
    for _, f in ipairs(frames) do
        if f.__events[e] and f.__scripts.OnEvent then f.__scripts.OnEvent(f, e, ...) end
    end
end
NS = {}
function LoadAddonFile(src, chunkname, addon)   -- addon defaults to "KodoTimes", the only one that gets NS
    addon = addon or "KodoTimes"
    local fn, err = loadstring(src, "@" .. chunkname)
    if not fn then error(err) end
    fn(addon, addon == "KodoTimes" and NS or {})
end
'''

failures = []


def check(cond, what):
    if not cond:
        failures.append(what)


def fresh(saved=None, slider=True, channels=None, soundkit=None):
    """A new client: the addon loaded, ADDON_LOADED fired with these saved variables, sound CVars and SOUNDKIT."""
    lua = lua51.LuaRuntime(unpack_returned_tuples=True)
    lua.execute(STUBS)
    g = lua.globals()
    if soundkit is not None:
        g.SOUNDKIT = lua.table_from(soundkit)
    g.noSliderTemplate = not slider
    cv = {
        'Sound_MasterVolume': '1.0',
        'Sound_DialogVolume': '0.7', 'Sound_EnableDialog': '1',
        'Sound_AmbienceVolume': '0.6', 'Sound_EnableAmbience': '1',
        'Sound_SFXVolume': '0.5', 'Sound_EnableSFX': '1',
    }
    cv.update(channels or {})
    for k, v in cv.items():
        if v is None:
            continue
        g.cvars[k] = v
    if saved is not None:
        g.KodoTimesDB = lua.table_from(saved)
    for name in FILES:
        g.LoadAddonFile((root / 'KodoTimes' / name).read_text(encoding='utf-8'), name)
    g.FireEvent('ADDON_LOADED', 'KodoTimes')
    return lua, g, g.NS


def plays(g):
    return [(p.channel, p.level) for p in g.played.values()]


# saved value: new profiles and old ones get 100, a stored value is kept
_, g, ns = fresh()
check(g.KodoTimesDB.volume == 100, f'new profile volume is {g.KodoTimesDB.volume}, expected 100')
_, g, ns = fresh({'sound': True, 'time': 8})
check(g.KodoTimesDB.volume == 100, 'an old profile without volume did not get 100')
_, g, ns = fresh({'volume': 35})
check(g.KodoTimesDB.volume == 35 and ns.Volume() == 35, 'a stored volume of 35 was not kept')

# ns.Volume: converts, rounds and clamps whatever is stored
for stored, want in [(None, 100), ('abc', 100), ('nan', 100), (250, 100), (-5, 0), (37.6, 38), ('40', 40), (0, 0)]:
    g.KodoTimesDB.volume = stored
    check(ns.Volume() == want, f'ns.Volume() with {stored!r} stored is {ns.Volume()}, expected {want}')

# 100%: today's path, Master, no CVar touched
_, g, ns = fresh()
ns.PlayKind('death')
ns.PlayKind('welcome')
check(plays(g) == [('Master', None), ('Master', None)], f'100% plays {plays(g)}, expected two plays on Master')
check(len(g.cvarWrites) == 0, '100% wrote a CVar')

# 0%: silent
_, g, ns = fresh({'volume': 0})
for kind in ['welcome', 'levelup', 'levelround', 'level60', 'death', 'deathlegend', 'skill', 'craftblue', 'craftepic', 'epicloot']:
    ns.PlayKind(kind)
check(plays(g) == [], f'0% still played {plays(g)}')

# 40%: Dialog borrowed at the absolute 0.40, put back after the hold, Master never written
_, g, ns = fresh({'volume': 40})
ns.PlayKind('levelup')
check(plays(g) == [('Dialog', '0.40')], f'40% plays {plays(g)}, expected Dialog at 0.40')
g.Advance(4.8)
check(g.cvars['Sound_DialogVolume'] == '0.40', 'Dialog was restored before the 4.9 s LEVELUP hold ended')
g.Advance(0.2)
check(g.cvars['Sound_DialogVolume'] == '0.7', f'Dialog is {g.cvars["Sound_DialogVolume"]} after the hold, expected 0.7')
check('Sound_MasterVolume' not in list(g.cvarWrites.values()), 'Sound_MasterVolume was written')
check(g.cvars['Sound_SFXVolume'] == '0.5' and g.cvars['Sound_AmbienceVolume'] == '0.6', 'another channel was changed')

# each sound holds the channel for its own length + 0.5 s; an id without a measured length keeps 4 s
for kind, hold in [('death', 1.8), ('levelup', 4.9), ('skill', 8.9), ('epicloot', 8.9), ('welcome', 8.9)]:
    _, g, ns = fresh({'volume': 40})
    ns.PlayKind(kind)
    g.Advance(hold - 0.1)
    check(g.cvars['Sound_DialogVolume'] == '0.40', f'{kind}: Dialog was restored before its {hold} s hold ended')
    g.Advance(0.2)
    check(g.cvars['Sound_DialogVolume'] == '0.7', f'{kind}: Dialog is {g.cvars["Sound_DialogVolume"]} after its {hold} s hold')
_, g, ns = fresh({'volume': 40}, soundkit={'RAID_WARNING': 12345})   # a client with another death sound id
ns.PlayKind('death')
check(g.played[len(g.played)].id == 12345, 'the reloaded addon did not play SOUNDKIT.RAID_WARNING')
g.Advance(3.9)
check(g.cvars['Sound_DialogVolume'] == '0.40', 'an unknown sound id was held less than 4 s')
g.Advance(0.2)
check(g.cvars['Sound_DialogVolume'] == '0.7', 'an unknown sound id was held more than 4 s')

# overlapping plays: one saved original, the channel is put back when the longest sound has ended
_, g, ns = fresh({'volume': 40})
ns.PlayKind('death')
g.Advance(0.5)
g.KodoTimesDB.volume = 60
ns.PlayKind('skill')
check(plays(g) == [('Dialog', '0.40'), ('Dialog', '0.60')], f'overlapping plays {plays(g)}')
g.Advance(2)
check(g.cvars['Sound_DialogVolume'] == '0.60', 'the first timer restored while the second play was still in its hold')
g.Advance(6.8)
check(g.cvars['Sound_DialogVolume'] == '0.60', 'the channel was restored before the second sound ended')
g.Advance(0.2)
check(g.cvars['Sound_DialogVolume'] == '0.7', f'after overlapping plays Dialog is {g.cvars["Sound_DialogVolume"]}, expected 0.7')

# a short sound inside a longer one does not restore early: LEVELUP's hold still decides
_, g, ns = fresh({'volume': 40})
ns.PlayKind('levelup')
g.Advance(0.5)
ns.PlayKind('death')
g.Advance(2)
check(g.cvars['Sound_DialogVolume'] == '0.40', 'a short sound restored the channel while LEVELUP was still playing')
g.Advance(2.3)
check(g.cvars['Sound_DialogVolume'] == '0.40', 'the channel was restored before LEVELUP\'s hold ended')
g.Advance(0.2)
check(g.cvars['Sound_DialogVolume'] == '0.7', f'after LEVELUP and a short sound Dialog is {g.cvars["Sound_DialogVolume"]}')

# logout / reload during the hold: restored at once, the later timer changes nothing
_, g, ns = fresh({'volume': 40})
ns.PlayKind('death')
g.FireEvent('PLAYER_LOGOUT')
check(g.cvars['Sound_DialogVolume'] == '0.7', 'PLAYER_LOGOUT did not restore the borrowed channel')
g.cvars['Sound_DialogVolume'] = '0.3'   # the user moves the slider afterwards
g.Advance(10)
check(g.cvars['Sound_DialogVolume'] == '0.3', 'a stale timer overwrote the channel after logout')

# a channel switched off by the user is skipped
_, g, ns = fresh({'volume': 50}, channels={'Sound_EnableDialog': '0'})
ns.PlayKind('death')
check(plays(g) == [('Ambience', '0.50')], f'with Dialog off plays {plays(g)}, expected Ambience')
_, g, ns = fresh({'volume': 50}, channels={'Sound_EnableDialog': '0', 'Sound_EnableAmbience': '0'})
ns.PlayKind('death')
check(plays(g) == [('Master', None)], f'with Dialog and Ambience off plays {plays(g)}, expected Master')
check(len(g.cvarWrites) == 0, 'with Dialog and Ambience off a CVar was written')
_, g, ns = fresh({'volume': 50}, channels={'Sound_DialogVolume': None})
ns.PlayKind('death')
check(plays(g) == [('Ambience', '0.50')], f'without a Dialog CVar plays {plays(g)}, expected Ambience')

# a channel PlaySound rejects is restored and not tried again this session
_, g, ns = fresh({'volume': 50})
g.playFails['Dialog'] = 'error'
ns.PlayKind('death')
check(plays(g) == [('Ambience', '0.50')], f'with Dialog erroring plays {plays(g)}, expected Ambience')
check(g.cvars['Sound_DialogVolume'] == '0.7', 'the failed Dialog channel was not restored')
g.Advance(5)
writes = len(g.cvarWrites)
g.playFails['Dialog'] = None
ns.PlayKind('death')
check(plays(g)[-1] == ('Ambience', '0.50'), 'an erroring channel was tried again')
check('Sound_DialogVolume' not in list(g.cvarWrites.values())[writes:], 'an erroring channel was written again')

# PlaySound returning false: next channel for this play
_, g, ns = fresh({'volume': 50})
g.playFails['Dialog'] = 'false'
ns.PlayKind('death')
check(plays(g) == [('Ambience', '0.50')], f'with Dialog returning false plays {plays(g)}, expected Ambience')

# no channel to borrow: Master, as loud as before
_, g, ns = fresh({'volume': 50}, channels={'Sound_EnableDialog': '0', 'Sound_EnableAmbience': '0', 'Sound_EnableSFX': '0'})
ns.PlayKind('death')
check(plays(g) == [('Master', None)], f'with every channel off plays {plays(g)}, expected Master')
check(len(g.cvarWrites) == 0, 'a CVar was written with no channel to borrow')

# SFX is never borrowed: it carries the game's own loot, craft and skill-up sounds, played with these toasts
SETUPS = {
    'all channels on': ({}, {}),
    'Dialog and Ambience off': ({'Sound_EnableDialog': '0', 'Sound_EnableAmbience': '0'}, {}),
    'Dialog and Ambience erroring': ({}, {'Dialog': 'error', 'Ambience': 'error'}),
    'Dialog and Ambience returning false': ({}, {'Dialog': 'false', 'Ambience': 'false'}),
}
for setup, (channels, fails) in SETUPS.items():
    for kind in ['epicloot', 'craftblue', 'craftepic', 'skill', 'welcome']:
        _, g, ns = fresh({'volume': 50}, channels=channels)
        for channel, how in fails.items():
            g.playFails[channel] = how
        ns.PlayKind(kind)
        sfx = []
        for _ in range(20):
            sfx.append(g.cvars['Sound_SFXVolume'])
            g.Advance(0.5)
        where = f'{kind} with {setup}'
        check('Sound_SFXVolume' not in list(g.cvarWrites.values()), f'{where}: Sound_SFXVolume was written')
        check(set(sfx) == {'0.5'}, f'{where}: Sound_SFXVolume went {sfx}')
        want = [('Dialog', '0.50')] if setup == 'all channels on' else [('Master', None)]
        check(plays(g) == want, f'{where} plays {plays(g)}, expected {want}')
        check(g.cvars['Sound_DialogVolume'] == '0.7' and g.cvars['Sound_AmbienceVolume'] == '0.6',
              f'{where}: Dialog or Ambience was not put back')

# /kodo volume | hangero | hangerő and the status line
_, g, ns = fresh()
g.SlashCmdList.KODOTIMES('volume 35')
check(g.KodoTimesDB.volume == 35, '/kodo volume 35 did not store 35')
check('hangerő: 35%' in g.printed[len(g.printed)], f'/kodo volume 35 printed {g.printed[len(g.printed)]!r}')
check(plays(g) == [('Dialog', '0.35')], f'/kodo volume 35 preview {plays(g)}')
g.SlashCmdList.KODOTIMES('hangero abc')
check(g.KodoTimesDB.volume == 35, '/kodo hangero abc changed the volume')
check('/kodo volume <0-100>' in g.printed[len(g.printed)], '/kodo hangero abc printed no usage')
g.SlashCmdList.KODOTIMES('VOLUME 250')
check(g.KodoTimesDB.volume == 100, f'/kodo volume 250 stored {g.KodoTimesDB.volume}, expected 100')
g.SlashCmdList.KODOTIMES('hangerő -3')
check(g.KodoTimesDB.volume == 0, f'/kodo hangerő -3 stored {g.KodoTimesDB.volume}, expected 0')
g.KodoTimesDB.volume = 70
first = len(g.printed)
g.SlashCmdList.KODOTIMES('')
out = [g.printed[i] for i in range(first + 1, len(g.printed) + 1)]
check('hangerő: 70%' in out[0], f'status line is {out[0]!r}')
check(any('/kodo volume <0-100>' in line and 'most: 70%' in line for line in out), 'the help has no /kodo volume line')
g.KodoTimesDB.sound = False
count = len(plays(g))
g.SlashCmdList.KODOTIMES('volume 20')
check(g.KodoTimesDB.volume == 20 and '/kodo sound' in g.printed[len(g.printed)], 'sound off: no hint to /kodo sound')
check(len(plays(g)) == count, 'sound off: /kodo volume still played a preview')


def find(g, pred):
    return [f for f in g.frames.values() if pred(f)]


# options panel: the row under the sound checkbox, no write on open, writes and samples on change
_, g, ns = fresh({'volume': 35})
checks = {f.opt.key: f for f in find(g, lambda f: f.__kind == 'CheckButton' and f.opt)}
sy, qy = checks['sound'].__point[3], checks['quietRaidPvp'].__point[3]
check(sy - qy == 56, f'quietRaidPvp sits {sy - qy} px under the sound checkbox, expected 26 + 30')
slider = g.KodoTimesVolumeSlider
check(slider is not None, 'no KodoTimesVolumeSlider')
g.KodoTimesOptions.__scripts.OnShow(g.KodoTimesOptions)
check(slider.__value == 35, f'the slider shows {slider.__value} after opening, expected 35')
check(g.KodoTimesDB.volume == 35 and plays(g) == [], 'opening the panel wrote the volume or played a sample')
slider.__scripts.OnValueChanged(slider, 52)
check(g.KodoTimesDB.volume == 50, f'the slider at 52 stored {g.KodoTimesDB.volume}, expected 50 (steps of 5)')
check(plays(g) == [('Dialog', '0.50')], f'the slider sample {plays(g)}')
slider.__scripts.OnValueChanged(slider, 70)
check(g.KodoTimesDB.volume == 70 and len(plays(g)) == 1, 'a second change within 0.3 s played another sample')
g.Advance(0.3)
slider.__scripts.OnValueChanged(slider, 80)
check(len(plays(g)) == 2, 'no sample 0.3 s later')
sound = checks['sound']
sound.GetChecked = lambda self: False
sound.__scripts.OnClick(sound)
check(slider.__alpha == 0.4 and not slider.__enabled, 'the slider is not dimmed and disabled with sound off')
sound.GetChecked = lambda self: True
sound.__scripts.OnClick(sound)
check(slider.__alpha == 1 and slider.__enabled, 'the slider is not enabled again with sound on')

# without OptionsSliderTemplate: - / + in steps of 10
_, g, ns = fresh({'volume': 35}, slider=False)
g.KodoTimesOptions.__scripts.OnShow(g.KodoTimesOptions)
minus = find(g, lambda f: f.__kind == 'Button' and f.__text == '-')[-1]
plus = find(g, lambda f: f.__kind == 'Button' and f.__text == '+')[-1]
plus.__scripts.OnClick(plus)
check(g.KodoTimesDB.volume == 45, f'+ made {g.KodoTimesDB.volume}, expected 45')
for _ in range(6):
    minus.__scripts.OnClick(minus)
check(g.KodoTimesDB.volume == 0, f'- six times made {g.KodoTimesDB.volume}, expected 0')

if failures:
    print('FAIL:')
    for failure in failures:
        print('  ' + failure)
    sys.exit(1)
print('PASS: volume saved and clamped; 0 silent, 100 on Master, 1-99 on Dialog or Ambience (never SFX) put back when '
      'the sound ends; slash and panel')
