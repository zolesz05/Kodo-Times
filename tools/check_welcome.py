"""Check the first-start welcome window: the guild texts, that they fit the banner, and the untouched buttons, flags and sound.

Runs the addon in Lua 5.1 with the stub WoW API of tools/check_volume.py; the welcome window's FontStrings get a
simple glyph model (width = characters x size x glyph, greedy word wrap, line height = 1.2 x size).
Needs the lupa package (an embedded Lua 5.1):  uv run --with lupa python tools/check_welcome.py
"""
from pathlib import Path
import ast
import sys

try:
    from lupa import lua51
except ImportError:
    sys.exit('FAIL: needs lupa (Lua 5.1 for Python). Run: uv run --with lupa python tools/check_welcome.py')

root = Path(__file__).resolve().parents[1]
FILES = ['Theme.lua', 'Lines.lua', 'Pals.lua', 'Map.lua', 'Options.lua']

# the stub WoW API is shared with check_volume.py (importing it would run its checks)
STUBS = next(node.value.value for node in ast.parse((root / 'tools' / 'check_volume.py').read_text(encoding='utf-8')).body
             if isinstance(node, ast.Assign) and getattr(node.targets[0], 'id', None) == 'STUBS')

# the welcome frame's FontStrings and buttons are recorded; every FontString call goes into its log
EXTRA = r'''
glyph, unbounded = 0.6, true
welcomeFS, welcomeButtons, joined, left = {}, {}, {}, {}
local function Chars(s) return select(2, s:gsub("[^\128-\191]", "")) end
local function FontString()
    local fs = setmetatable({ text = "", log = {} }, { __index = function(_, key) if key:match("^%u") and not key:match("^Get") then return function() end end end })
    local function Log(s) fs.log[#fs.log + 1] = s end
    local function Natural(self) return Chars(self.text) * self.size * glyph end
    function fs:SetFont(path, size) self.font, self.size = path, size; Log("font " .. size) end
    function fs:GetFont() return self.font, self.size end
    function fs:SetText(s) self.text = s end
    function fs:SetWidth(w) self.width = w; Log("width") end
    function fs:SetWordWrap(on) self.wrap = on; Log("wrap") end
    function fs:SetPoint(...) self.point = { ... } end
    function fs:GetStringWidth()
        Log("measure")
        return self.width and math.min(Natural(self), self.width) or Natural(self)
    end
    if unbounded then function fs:GetUnboundedStringWidth() Log("measure"); return Natural(self) end end
    function fs:Lines()   -- greedy word wrap inside the set width
        if not self.width or self.wrap == false then return 1 end
        local lines, line = 1, 0
        for word in self.text:gmatch("%S+") do
            local w = Chars(word) * self.size * glyph
            if line > 0 and line + self.size * glyph + w > self.width then lines, line = lines + 1, w
            else line = line + (line > 0 and self.size * glyph or 0) + w end
        end
        return lines
    end
    function fs:GetStringHeight() return self:Lines() * self.size * 1.2 end
    return fs
end
local BaseCreateFrame = CreateFrame
function CreateFrame(kind, name, parent, ...)
    local f = BaseCreateFrame(kind, name, parent, ...)
    if name == "MotevePalsWelcome" then
        f.CreateFontString = function() local fs = FontString(); welcomeFS[#welcomeFS + 1] = fs; return fs end
    elseif kind == "Button" and parent and parent == rawget(_G, "MotevePalsWelcome") then
        welcomeButtons[#welcomeButtons + 1] = f
    end
    return f
end
function LeaveChannelByName(name) left[#left + 1] = name end
function UnitFactionGroup() return "Horde", "Horde" end
'''

TW, BANNER_H = 520, 93
COLUMN_L, COLUMN_W = TW * 0.308, TW * 0.51
PORTRAIT_R = TW * (0.2079 + 0.121 / 2)   # right edge of the portrait ring
MEDALLION_X = TW * 0.8946                  # centre of the GO medallion
KICKER = 'DUDE, WHERE IS MY KODO?'
TITLE = 'ÜDV A KODÓKERESŐK KÖZÖTT!'
TEXT = "Nyomj egy Let's go-t, és szólunk, ha valaki végre megtalálta a kodót, vagy ha a többiekkel valami nagyon fontos történik."
failures = []


def check(cond, what):
    if not cond:
        failures.append(what)


def fresh(saved=None, char=None, glyph=0.6, unbounded=True):
    lua = lua51.LuaRuntime(unpack_returned_tuples=True)
    lua.execute(STUBS)
    lua.execute(EXTRA)
    g = lua.globals()
    g.glyph, g.unbounded = glyph, unbounded
    if saved is not None:
        g.MotevePalsDB = lua.table_from(saved)
    if char is not None:
        g.MotevePalsChar = lua.table_from(char)
    for name in FILES:
        g.LoadAddonFile((root / 'MotevePals' / name).read_text(encoding='utf-8'), name)
    g.FireEvent('ADDON_LOADED', 'MotevePals')
    lua.execute('NS.JoinCrew = function(report) joined[#joined + 1] = report end')
    return lua, g, g.NS


def strings(g):
    k, t, x, med = list(g.welcomeFS.values())
    return k, t, x, med


def open_welcome(**kw):
    lua, g, ns = fresh(**kw)
    g.SlashCmdList.MOTEVEPALS('welcome')
    return lua, g, ns


def fit(t):
    """The title's last font size, and whether every measurement came before SetWidth and SetWordWrap."""
    log = list(t.log.values())
    sizes = [int(s.split()[1]) for s in log if s.startswith('font ')]
    measured_last = max((i for i, s in enumerate(log) if s == 'measure'), default=-1)
    clamped_first = min((i for i, s in enumerate(log) if s in ('width', 'wrap')), default=-1)
    return sizes, measured_last < clamped_first and 'width' in log and 'wrap' in log


# texts: /mpal welcome shows exactly the agreed lines, nothing of the old placeholder
_, g, ns = open_welcome()
k, t, x, med = strings(g)
check(k.text == KICKER, f'top line is {k.text!r}')
check(t.text == TITLE, f'title is {t.text!r}')
check(x.text == TEXT, f'description is {x.text!r}')
check(med.text == 'GO', f'medallion text is {med.text!r}')
for s in (k.text, t.text, x.text):
    for old in ('BULVÁR', 'FASZOS', 'fogyatékos'):
        check(old not in s, f'{old!r} is still in {s!r}')

# title fit: measured unbounded before any width is set, 19 -> 17 -> 16 -> 15, then clamped to the column, no wrap
for unbounded in (True, False):
    for glyph, want in [(0.45, 19), (0.6, 17), (0.63, 16), (0.68, 15), (1.0, 15)]:
        _, g, _ = open_welcome(glyph=glyph, unbounded=unbounded)
        _, t, _, _ = strings(g)
        sizes, ordered = fit(t)
        label = f'title (glyph {glyph}, GetUnboundedStringWidth {"present" if unbounded else "missing"})'
        check(sizes[-1] == want, f'{label} ends at size {sizes[-1]}, expected {want}')
        check(sizes == [19, 17, 16, 15][:len(sizes)], f'{label} stepped {sizes}')
        check(ordered, f'{label} was measured after SetWidth/SetWordWrap, or never clamped')
        check(t.width == COLUMN_W and t.wrap is False, f'{label} width {t.width}, wrap {t.wrap}')
        if glyph < 1.0:   # 1.0 is the wide case that stops at the 15 floor
            natural = len(TITLE) * t.size * glyph
            check(natural <= COLUMN_W, f'{label} is {natural:.0f} px wide at {t.size}, the column is {COLUMN_W:.0f}')

# description fit: 11, then 10 when taller than 30 px, then 9 when still taller than 38 px; never below 9
for glyph, want in [(0.3, [11]), (0.6, [11, 10]), (0.75, [11, 10, 9]), (1.5, [11, 10, 9])]:
    _, g, _ = open_welcome(glyph=glyph)
    _, _, x, _ = strings(g)
    sizes = [int(s.split()[1]) for s in x.log.values() if s.startswith('font ')]
    check(sizes == want, f'description (glyph {glyph}) sizes {sizes}, expected {want}')
    check(x.width == COLUMN_W and x.wrap is True, f'description (glyph {glyph}) width {x.width}, wrap {x.wrap}')

# the agreed texts under the default model stay inside the banner, between the portrait ring and the medallion
_, g, _ = open_welcome()
k, t, x, _ = strings(g)
bottom = 14 + k.GetStringHeight(k) + 3 + t.GetStringHeight(t) + 3 + x.GetStringHeight(x)
check(x.size == 10 and x.Lines(x) <= 3, f'description is {x.Lines(x)} lines at {x.size}, expected at most 3 at 10')
check(bottom <= BANNER_H, f'the description ends at {bottom:.1f} px, below the {BANNER_H} px banner')
check(k.GetStringWidth(k) <= COLUMN_W, f'the top line is {k.GetStringWidth(k):.0f} px wide')
check(k.point[4] == COLUMN_L and COLUMN_L > PORTRAIT_R, 'the text column starts over the portrait ring')
check(COLUMN_L + COLUMN_W < MEDALLION_X - 30, 'the text column runs into the GO medallion')

# buttons, flags, crew join and sound behave as before
_, g, ns = fresh()
g.FireEvent('PLAYER_LOGIN')
g.Advance(5.9)
check(len(g.welcomeFS) == 0, 'the welcome window opened before 6 s')
g.Advance(0.2)
check(len(g.welcomeFS) == 4, 'a new character did not get the welcome window 6 s after login')
check([p.id for p in g.played.values()] == [878], f'welcome sound plays {[p.id for p in g.played.values()]}')
buttons = list(g.welcomeButtons.values())
check([b['__text'] for b in buttons] == ["Let's go!", 'Kösz, nem'], f'buttons are {[b['__text'] for b in buttons]}')
buttons[0]['__scripts'].OnClick(buttons[0])
check(g.MotevePalsDB.welcomed is True and g.MotevePalsChar.welcomed is True and g.MotevePalsChar.noCrew is None,
      "Let's go! did not set welcomed / clear noCrew")
check(g.MotevePalsDB.crew == 'MPhaverok', f"Let's go! crew is {g.MotevePalsDB.crew!r}")
check(list(g.joined.values()) == [True], "Let's go! did not call ns.JoinCrew(true)")
check(list(g.printed.values())[-1].endswith('a haverok csatornája: MPhaverok. Saját csapat neve kell? /mpal crew <név>'),
      "Let's go! printed something else")

_, g, ns = fresh({'crew': 'MPkodo'})
g.SlashCmdList.MOTEVEPALS('welcome')
buttons = list(g.welcomeButtons.values())
buttons[1]['__scripts'].OnClick(buttons[1])
check(g.MotevePalsChar.welcomed is True and g.MotevePalsChar.noCrew is True, 'Kösz, nem did not set welcomed / noCrew')
check(g.MotevePalsDB.welcomed is None, 'Kösz, nem set db.welcomed')
check(list(g.left.values()) == ['MPkodo'] and len(g.joined) == 0, 'Kösz, nem did not just leave the crew channel')
check(list(g.printed.values())[-1].endswith('oké. Ha meggondolod: /mpal crew haverok'), 'Kösz, nem printed something else')

_, g, ns = fresh({'sound': False})
g.SlashCmdList.MOTEVEPALS('welcome')
check(len(g.played) == 0, 'the welcome sound played with sound off')

_, g, ns = fresh(char={'welcomed': True})
g.FireEvent('PLAYER_LOGIN')
g.Advance(15)
check(len(g.welcomeFS) == 0, 'a welcomed character got the window again')

if failures:
    print('FAIL:')
    for failure in failures:
        print('  ' + failure)
    sys.exit(1)
print('PASS: welcome window shows the "Dude where is my kodo" texts, fits the banner; buttons, flags and sound unchanged')
