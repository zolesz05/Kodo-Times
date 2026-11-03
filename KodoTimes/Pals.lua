-- Kodo Times - friends who all run this addon get funny pop-ups about each other:
-- level ups, deaths, profession milestones, blue / epic crafts and epic loot.
--
-- The news travels as hidden addon messages to the guild, the group, the online people on your
-- friends list, and (optional) a private "crew" channel - so it works between friends who are not
-- in the same guild or group. Only players who have the addon see anything.
local ADDON_NAME, ns = ...
local C = ns.C
local format, floor, random = string.format, math.floor, math.random

-- the addon-message prefix keeps the addon's old name on purpose: 0.9.x and 0.10+ clients
-- must keep hearing each other (news and map positions) while everyone updates
local PREFIX = "MOTEVEPAL"
local DEFAULTS = {
    enabled = true, mapNames = false, quietRaidPvp = true, selfToast = false, chat = true, sound = true, volume = 100, time = 6.5, share = true, map = true,
    guild = true, group = true, friends = true, crew = nil,
    point = "LEFT", relPoint = "LEFT", x = 18, y = -46, scale = 0.67,   -- left edge, above the chat
}
local db, char
local dormant   -- the full old addon (0.9.x, folder MotevePals) is running too: this copy stays silent

local function Print(msg) print("|cffa88bffKodo Times|r: " .. msg) end
local function WarnDuplicate()
    Print("|cffff5544a régi verzió (MotevePals mappa) is fut, ezért ez most nem csinál semmit.|r "
        .. "Csomagold ki a teljes KodoTimes.zip-et a régi fölé (felülírva), és indítsd újra a játékot.")
end
local secret = issecretvalue or function() return false end

---------------------------------------------------------------------------
-- Text
---------------------------------------------------------------------------
local lastLine = {}
-- the kind's lines, plus the extra lines of this exact level (ns.LINES_AT) when it has any
local function Pick(kind, level)
    local list = ns.LINES[kind]
    if not list or #list == 0 then return "" end
    local extra = ns.LINES_AT and ns.LINES_AT[kind]
    extra = extra and extra[tonumber(level)]
    if extra then
        local pool = {}
        for _, line in ipairs(list) do pool[#pool + 1] = line end
        for _, line in ipairs(extra) do pool[#pool + 1] = line end
        list = pool
    end
    local i = random(#list)
    -- remember the text, not the index: the pool differs from level to level
    if #list > 1 and list[i] == lastLine[kind] then i = (i % #list) + 1 end
    lastLine[kind] = list[i]
    return list[i]
end

local QUALITY = { [2] = "1eff00", [3] = "0070dd", [4] = "a335ee", [5] = "ff8000" }
local function ItemText(id, name, q)
    local col = QUALITY[tonumber(q) or 0] or "ffffff"
    if id and tonumber(id) then
        return format("|cff%s|Hitem:%d::::::::|h[%s]|h|r", col, tonumber(id), name or "?")
    end
    return format("|cff%s[%s]|r", col, name or "?")
end

-- characters here have two-part names ("Higgsbozon Lightchaser"): show the second part
local function Nick(name)
    if not name then return "?" end
    name = tostring(name):gsub("%-[^%s]*$", "")          -- drop "-Realm"
    local second = name:match("^%S+%s+(%S+)")
    return second or name
end
ns.Nick = Nick

-- our own full name: on this server UnitName("player") can return only the first part
-- ("Miss"), while the character frame / others see "Miss Mcimbtyw"
local function MyName()
    local n = UnitName("player") or "?"
    if not n:find(" ") and UnitPVPName then
        local ok, pv = pcall(UnitPVPName, "player")
        if ok and pv and not secret(pv) then
            local full = pv:match("^(" .. n:gsub("%p", "%%%0") .. "%s+%S+)")
            if full then return full end
        end
    end
    return n
end
ns.MyName = MyName

-- a chat player link in the class colour: left-click whispers target, right-click opens the usual menu
local function PlayerLink(target, label, class)
    target = target and tostring(target):gsub("[|:]", "") or ""
    if target == "" then return ns.ClassHex(class) .. label .. "|r" end
    return ns.ClassHex(class) .. format("|Hplayer:%s|h[%s]|h", target, label) .. "|r"
end

-- forChat: the name becomes a player link to f.sender (the banner keeps the plain name)
local function Fill(line, f, forChat)
    return (line:gsub("%%(%a)", function(k)
        if k == "n" then return forChat and PlayerLink(f.sender, Nick(f.name), f.class) or Nick(f.name)
        elseif k == "l" then return tostring(f.level or "?")
        elseif k == "z" then return f.zone or "?"
        elseif k == "s" then return f.skill or "?"
        elseif k == "r" then return tostring(f.rank or "?")
        elseif k == "i" then return ItemText(f.itemID, f.itemName, f.quality)
        elseif k == "g" then return f.legend and f.legend.name or "?"
        elseif k == "t" then return f.legend and f.legend.title or "?"
        end
        return "%" .. k
    end))
end

---------------------------------------------------------------------------
-- Toast: ornate WoW banner per news type (frame, faction flag, scenery and medallion are one
-- texture per type in Textures\toast_<type>.tga), with the player's class portrait or the item in
-- the ring on the left, kicker + headline + funny line in the middle, and the medallion on the right.
---------------------------------------------------------------------------
local TW = 520                       -- toast width in UI units
-- per type: texture, used height of the 1024x256 texture (0..1), headline/medallion colour, medallion text
local STYLE = {
    levelup     = { tex = "toast_levelup",    v = 0.7148,  c = { 1.00, 0.78, 0.25 }, med = "%l" },
    levelround  = { tex = "toast_levelround", v = 0.7109, c = { 1.00, 0.58, 0.22 }, med = "%l" },
    level60     = { tex = "toast_level60",    v = 0.6992, c = { 1.00, 0.70, 0.20 }, med = "60" },
    death       = { tex = "toast_death",      v = 0.7148,  c = { 1.00, 0.30, 0.25 }, med = "RIP" },
    deathlegend = { tex = "toast_death",      v = 0.7148,  c = { 1.00, 0.30, 0.25 }, med = "RIP" },
    skill       = { tex = "toast_skill",      v = 0.707,  c = { 0.55, 0.95, 0.35 }, med = "%r" },
    craftblue   = { gem = true, tex = "toast_craftblue",  v = 0.6953,  c = { 0.35, 0.65, 1.00 }, med = "KÉK" },
    craftepic   = { gem = true, tex = "toast_craftepic",  v = 0.6953, c = { 0.80, 0.45, 1.00 }, med = "EPIC" },
    epicloot    = { gem = true, tex = "toast_epicloot",   v = 0.6953,  c = { 0.80, 0.45, 1.00 }, med = "LOOT" },
}
-- banner texture path for the player's faction: Alliance characters get the Alliance-flag copy
-- (Textures\toast_<type>_alliance.tga, same layout), everyone else the Horde-flag original
local function BannerTex(name)
    return ns.TEX(UnitFactionGroup("player") == "Alliance" and name .. "_alliance" or name)
end
-- banner geometry (fractions of the width; from the 1024 px texture)
local PORT_X, PORT_S = 0.2079, 0.121   -- portrait ring centre / diameter
local MED_X = 0.8946                    -- medallion centre
-- icon in the ring per news type (crafts / loot show the item, skills the profession, death a skull)
local ICON = {
    levelup     = "Interface\\Icons\\Spell_Holy_PowerInfusion",
    levelround  = "Interface\\Icons\\INV_Misc_Gift_02",
    level60     = "Interface\\Icons\\INV_Misc_Head_Dragon_01",
    death       = "Interface\\Icons\\INV_Misc_Bone_HumanSkull_01",
    deathlegend = "Interface\\Icons\\INV_Misc_Bone_HumanSkull_01",
    skill       = "Interface\\Icons\\Trade_BlackSmithing",
    craftblue   = "Interface\\Icons\\Trade_BlackSmithing",
    craftepic   = "Interface\\Icons\\Trade_BlackSmithing",
    epicloot    = "Interface\\Icons\\INV_Misc_Bag_10",
}
-- profession icons (fallback when the spellbook has no texture for it)
local PROF_ICON = {
    ["Blacksmithing"] = "Trade_BlackSmithing", ["Alchemy"] = "Trade_Alchemy", ["Engineering"] = "Trade_Engineering",
    ["Tailoring"] = "Trade_Tailoring", ["Leatherworking"] = "Trade_LeatherWorking", ["Enchanting"] = "Trade_Engraving",
    ["Mining"] = "Trade_Mining", ["Herbalism"] = "Spell_Nature_NatureTouchGrow", ["Skinning"] = "INV_Misc_Pelt_Wolf_01",
    ["Cooking"] = "INV_Misc_Food_15", ["First Aid"] = "Spell_Holy_SealOfSacrifice", ["Fishing"] = "Trade_Fishing",
}
local function ProfIcon(name)
    if not name or name == "" then return nil end
    if GetSpellTexture then
        local ok, tex = pcall(GetSpellTexture, name)
        if ok and tex and not secret(tex) then return tex end
    end
    local f = PROF_ICON[name]
    return f and ("Interface\\Icons\\" .. f) or nil
end

-- WoW's own sounds per news type: { sound, delay }, ...  (SOUNDKIT name, numeric id as fallback)
local SK = SOUNDKIT or {}
local function K(name, id) return SK[name] or id end
local SOUND = {   -- one simple sound each
    welcome     = { { K("IG_QUEST_LIST_COMPLETE", 878), 0 } },
    levelup     = { { K("LEVELUP", 888), 0 } },
    levelround  = { { K("LEVELUP", 888), 0 } },
    level60     = { { K("LEVELUP", 888), 0 } },
    death       = { { SK.RAID_WARNING or SK.IG_QUEST_FAILED or 8959, 0 } },
    skill       = { { K("IG_QUEST_LIST_COMPLETE", 878), 0 } },
    craftblue   = { { K("IG_QUEST_LIST_COMPLETE", 878), 0 } },
    craftepic   = { { K("IG_QUEST_LIST_COMPLETE", 878), 0 } },
    epicloot    = { { K("IG_QUEST_LIST_COMPLETE", 878), 0 } },
}
SOUND.deathlegend = SOUND.death

-- CVar access that never errors (missing API or CVar = nil); Options.lua uses these too
function ns.GetCV(name)
    if C_CVar and C_CVar.GetCVar then local ok, v = pcall(C_CVar.GetCVar, name); if ok then return v end end
    if GetCVar then local ok, v = pcall(GetCVar, name); if ok then return v end end
end
function ns.SetCV(name, value)
    if C_CVar and C_CVar.SetCVar then return pcall(C_CVar.SetCVar, name, value) end
    if SetCVar then return pcall(SetCVar, name, value) end
end

-- the addon's own sound volume: a whole percent 0..100 (100 = as loud as the game plays it)
function ns.Volume()
    local n = tonumber(db and db.volume)
    if not n or n ~= n then return 100 end
    return math.max(0, math.min(100, floor(n + 0.5)))
end

-- PlaySound has no volume, so at 1-99% the sound plays on a little-used channel whose volume CVar is
-- set to volume/100 for a moment (= Master x volume), then put back. Master itself is never touched,
-- nor is Effects (SFX): it carries the game's loot, craft and skill-up sounds that play with our toasts.
local CHANNELS = {   -- least noticeable first; none of them usable = Master at full volume
    { name = "Dialog",   cvar = "Sound_DialogVolume",   enable = "Sound_EnableDialog" },
    { name = "Ambience", cvar = "Sound_AmbienceVolume", enable = "Sound_EnableAmbience" },
}
-- s the channel stays borrowed per sound id: the sound's length + 0.5 s, as the volume also changes
-- the channel's other sounds. Lengths measured from the client's Ogg files (FileDataID).
local HOLD = {
    [878]  = 8.9,   -- IG_QUEST_LIST_COMPLETE (567439): 8.35 s
    [888]  = 4.9,   -- LEVELUP (569593): 4.36 s
    [8959] = 1.8,   -- RAID_WARNING (567397): 1.29 s
    [847]  = 1.8,   -- IG_QUEST_FAILED (567459): 1.24 s
}
local HOLD_DEFAULT = 4   -- s, any other id
local borrowed, borrowOrig, borrowGen = nil, nil, 0   -- session only: the channel, the user's value, newest timer
local borrowUntil = 0   -- GetTime() when the longest sound on the borrowed channel has ended
local badChannel = {}   -- PlaySound errored on it: not tried again this session
local function RestoreChannel()
    if borrowed and borrowOrig ~= nil then ns.SetCV(borrowed.cvar, borrowOrig) end
    borrowed, borrowOrig, borrowUntil = nil, nil, 0
end
local function Usable(ch)
    return not badChannel[ch.name] and ns.GetCV(ch.cvar) ~= nil and tostring(ns.GetCV(ch.enable)) == "1"
end
local function TryChannel(ch, id, level)
    -- the user's value is saved once; overlapping plays reuse the channel and only push the restore later
    if not borrowed then borrowed, borrowOrig = ch, ns.GetCV(ch.cvar) end
    ns.SetCV(ch.cvar, level)
    local ok, willPlay = pcall(PlaySound, id, ch.name)
    if ok and willPlay ~= false then
        local hold = HOLD[id] or HOLD_DEFAULT
        if GetTime() + hold > borrowUntil then   -- a shorter sound inside a longer one keeps the longer timer
            borrowUntil = GetTime() + hold
            borrowGen = borrowGen + 1
            local gen = borrowGen
            C_Timer.After(hold, function() if gen == borrowGen then RestoreChannel() end end)
        end
        return true
    end
    if not ok then badChannel[ch.name] = true end
    RestoreChannel()
    return false
end
local function PlayOne(id)
    local v = ns.Volume()
    if v <= 0 then return end
    if v < 100 then
        local level = format("%.2f", v / 100)
        local tried = borrowed
        if borrowed and TryChannel(borrowed, id, level) then return end
        for _, ch in ipairs(CHANNELS) do
            if ch ~= tried and Usable(ch) and TryChannel(ch, id, level) then return end
        end
    end
    pcall(PlaySound, id, "Master")   -- 100%, or no channel to borrow: as loud as before
end

function ns.PlayKind(kind)
    local list = SOUND[kind]
    if not list or not PlaySound then return end
    for _, e in ipairs(list) do
        if e[2] > 0 then C_Timer.After(e[2], function() PlayOne(e[1]) end)
        else PlayOne(e[1]) end
    end
end

local T = CreateFrame("Frame", "KodoTimesToast", UIParent)
T:SetSize(TW, 76)
T:SetFrameStrata("HIGH")
T:SetMovable(true)
T:SetClampedToScreen(true)
T:Hide()

T.bg = T:CreateTexture(nil, "BACKGROUND")
T.bg:SetAllPoints()
T.shadow = ns.Slice(T, "shadow", 0.5, "BACKGROUND", -8):Fit(T, 26, 14)
T.shadow:SetColor({ 0, 0, 0 }, 0)   -- the banner texture has its own shadow

-- portrait (class icon or item) inside the left ring
T.portrait = T:CreateTexture(nil, "ARTWORK", nil, 1)
T.portrait:SetPoint("CENTER", T, "LEFT", TW * PORT_X, 0)
T.mask = T:CreateMaskTexture()
T.mask:SetTexture("Interface\\CharacterFrame\\TempPortraitAlphaMask", "CLAMPTOBLACKADDITIVE", "CLAMPTOBLACKADDITIVE")
T.mask:SetAllPoints(T.portrait)
T.portrait:AddMaskTexture(T.mask)

-- medallion text and a soft pulsing glow behind it
T.medGlow = ns.Img(T, "glow", "ARTWORK", 0)
T.medGlow:SetBlendMode("ADD")
T.medGlow:SetPoint("CENTER", T, "LEFT", TW * MED_X, 0)
T.medGlow:SetSize(58, 58)
T.med = T:CreateFontString(nil, "OVERLAY")
ns.SetFontSafe(T.med, ns.FONT_TITLE, 17)
T.med:SetPoint("CENTER", T, "LEFT", TW * MED_X, 0)
T.med:SetShadowColor(0, 0, 0, 1); T.med:SetShadowOffset(1, -1)

-- texts
local TEXT_L, TEXT_W = TW * 0.308, TW * 0.51
T.kicker = T:CreateFontString(nil, "OVERLAY")
ns.SetFontSafe(T.kicker, ns.FONT_BODY_BOLD, 8)
T.kicker:SetTextColor(0.80, 0.62, 0.38)
T.kicker:SetShadowColor(0, 0, 0, 1); T.kicker:SetShadowOffset(1, -1)
T.kicker:SetPoint("TOPLEFT", T, "TOPLEFT", TEXT_L, -14)
T.kicker:SetText("AZEROTH BULVÁR  -  RENDKÍVÜLI KIADÁS")
T.title = T:CreateFontString(nil, "OVERLAY")
ns.SetFontSafe(T.title, ns.FONT_TITLE, 19)
T.title:SetShadowColor(0, 0, 0, 1); T.title:SetShadowOffset(1, -1)
T.title:SetPoint("TOPLEFT", T.kicker, "BOTTOMLEFT", 0, -1)
T.text = T:CreateFontString(nil, "OVERLAY")
ns.SetFontSafe(T.text, ns.FONT_TITLE, 12)
T.text:SetTextColor(0.96, 0.93, 0.86)
T.text:SetShadowColor(0, 0, 0, 1); T.text:SetShadowOffset(1, -1)
T.text:SetJustifyH("LEFT"); T.text:SetJustifyV("TOP")
T.text:SetWordWrap(true)
T.text:SetWidth(TEXT_W)
T.text:SetPoint("TOPLEFT", T.title, "BOTTOMLEFT", 0, -1)

T:EnableMouse(false)
T:RegisterForDrag("LeftButton")
T:SetScript("OnDragStart", function(self) if self.moving then self:StartMoving() end end)
local function SavePos()
    local p, _, rp, x, y = T:GetPoint()
    db.point, db.relPoint, db.x, db.y = p, rp, x, y
end
T:SetScript("OnDragStop", function(self)
    self:StopMovingOrSizing()
    SavePos()
end)

local queue, showing, t0 = {}, false, 0
local SHOW, FADE = 6.5, 0.8

-- close: X in the corner (or left click) = this one, right click = this one and everything queued
local function Dismiss(all)
    if not showing or T.moving then return end
    if all then queue = {} end
    if t0 < SHOW then t0 = SHOW + FADE * 0.6 end   -- quick fade out
end
T.close = CreateFrame("Button", nil, T)
T.close:SetSize(18, 18)
T.close:SetPoint("TOPRIGHT", T, "TOPRIGHT", -TW * 0.035, -4)
T.close.x = T.close:CreateFontString(nil, "OVERLAY")
ns.SetFontSafe(T.close.x, ns.FONT_BODY_BOLD, 14)
T.close.x:SetPoint("CENTER")
T.close.x:SetText("×")
T.close.x:SetTextColor(0.85, 0.75, 0.6)
T.close.x:SetShadowColor(0, 0, 0, 1); T.close.x:SetShadowOffset(1, -1)
T.close:SetAlpha(0)
T.close:SetScript("OnEnter", function(self) self.x:SetTextColor(1, 0.35, 0.3) end)
T.close:SetScript("OnLeave", function(self) self.x:SetTextColor(0.85, 0.75, 0.6) end)
T.close:SetScript("OnClick", function() Dismiss(IsShiftKeyDown and IsShiftKeyDown()) end)
T:SetScript("OnMouseUp", function(self, btn)
    if self.moving then return end
    Dismiss(btn == "RightButton")
end)

-- size (move mode only): the whole banner is scaled, the layout above stays built for TW.
-- Grip in the corner or mouse wheel; the top-left corner stays where it is. Right click on the grip = 1.0
local function ClampScale(s) return math.min(2, math.max(0.5, tonumber(s) or 1)) end
local function SetToastScale(s)
    s = ClampScale(s)
    local l, t = T:GetLeft(), T:GetTop()
    local eff = T:GetEffectiveScale()
    T:SetScale(s)
    if l and t then
        local ne = T:GetEffectiveScale()
        T:ClearAllPoints()
        T:SetPoint("TOPLEFT", UIParent, "BOTTOMLEFT", l * eff / ne, t * eff / ne)
        -- clamped to the screen: keep where it is really drawn, so the saved place does not drift
        local cl, ct = T:GetLeft(), T:GetTop()
        if cl and ct then T:ClearAllPoints(); T:SetPoint("TOPLEFT", UIParent, "BOTTOMLEFT", cl, ct) end
    end
    local p, _, rp, x, y = T:GetPoint()
    db.scale, db.point, db.relPoint, db.x, db.y = s, p, rp, x, y
end
T.grip = CreateFrame("Button", nil, T)
T.grip:SetSize(16, 16)
T.grip:SetPoint("BOTTOMRIGHT", T, "BOTTOMRIGHT", -TW * 0.03, 6)
T.grip.tex = T.grip:CreateTexture(nil, "OVERLAY")
T.grip.tex:SetAllPoints()
local okTex, found = pcall(T.grip.tex.SetTexture, T.grip.tex, "Interface\\ChatFrame\\UI-ChatIM-SizeGrabber-Up")
if not (okTex and found) then   -- no size-grabber art on this client: a plain drawn corner
    T.grip.tex:Hide()
    for _, side in ipairs({ { 16, 3 }, { 3, 16 } }) do
        local bar = T.grip:CreateTexture(nil, "OVERLAY")
        bar:SetColorTexture(0.85, 0.75, 0.6, 0.9)
        bar:SetSize(side[1], side[2])
        bar:SetPoint("BOTTOMRIGHT")
    end
end
T.grip:Hide()
T.grip:EnableMouse(false)
local function StopGrip() T.grip:SetScript("OnUpdate", nil) end
T.grip:SetScript("OnMouseDown", function(self, btn)
    if btn ~= "LeftButton" or not GetCursorPosition or not T:GetLeft() then return end
    local leftPx = T:GetLeft() * T:GetEffectiveScale()
    local dx0, s0 = GetCursorPosition() - leftPx, T:GetScale()
    if dx0 <= 0 then return end
    self:SetScript("OnUpdate", function()
        SetToastScale(s0 * (GetCursorPosition() - leftPx) / dx0)
    end)
end)
T.grip:SetScript("OnMouseUp", function(_, btn)
    StopGrip()
    if btn == "RightButton" then SetToastScale(1) end
end)
T.grip:SetScript("OnHide", StopGrip)
pcall(T.SetScript, T, "OnMouseWheel", function(self, delta)
    if self.moving then SetToastScale(math.floor((self:GetScale() + delta * 0.05) * 20 + 0.5) / 20) end
end)
local glowC = { 1, 1, 1 }

local function Place(dy)
    T:ClearAllPoints()
    T:SetPoint(db.point, UIParent, db.relPoint, db.x, db.y + (dy or 0))
end

-- body text: starts at 12 and steps down so a long line still fits the banner
local function SetBodyText(text)
    ns.SetFontSafe(T.text, ns.FONT_TITLE, 12)
    T.text:SetText(text)
    if (T.text:GetStringHeight() or 0) > 30 then ns.SetFontSafe(T.text, ns.FONT_TITLE, 10.5) end
    if (T.text:GetStringHeight() or 0) > 40 then ns.SetFontSafe(T.text, ns.FONT_TITLE, 9.5) end
end

local function Next()
    local item = table.remove(queue, 1)
    if not item then showing = false; T:EnableMouse(false); T:Hide(); return end
    showing, t0 = true, 0
    local st = STYLE[item.kind] or STYLE.levelup
    local f = item.fields or {}
    -- banner
    T.bg:SetTexture(BannerTex(st.tex))
    T.bg:SetTexCoord(0, 1, 0, st.v)
    T:SetHeight(math.floor(TW * st.v / 4 + 0.5))   -- 1024 x 256 texture -> keep the aspect
    -- headline, line, medallion
    local c = st.c
    T.title:SetText(ns.TITLES[item.kind] or "")
    T.title:SetTextColor(c[1], c[2], c[3])
    SetBodyText(item.text)
    local med = st.med:gsub("%%l", tostring(f.level or "")):gsub("%%r", tostring(f.rank or ""))
    T.med:ClearAllPoints()
    if st.gem then   -- the gem sits in the upper half of the medallion, the word below it
        ns.SetFontSafe(T.med, ns.FONT_TITLE, 10)
        T.med:SetPoint("CENTER", T, "LEFT", TW * MED_X, -13)
    else
        ns.SetFontSafe(T.med, ns.FONT_TITLE, #med >= 4 and 13 or (#med == 3 and 17 or 22))
        T.med:SetPoint("CENTER", T, "LEFT", TW * MED_X, 0)
    end
    T.med:SetText(med)
    T.med:SetTextColor(c[1], c[2], c[3])
    glowC = c
    -- icon in the ring: own icon per news type; crafts / loot show the item, skills the profession
    local size = TW * PORT_S
    T.portrait:SetSize(size, size)
    local dead = item.kind == "death" or item.kind == "deathlegend"
    local isItem = item.kind == "craftblue" or item.kind == "craftepic" or item.kind == "epicloot"
    local tex = ICON[item.kind]
    if (isItem or item.kind == "skill") and item.icon then tex = item.icon end
    T.portrait:SetTexture(tex or "Interface\\Icons\\INV_Misc_QuestionMark")
    T.portrait:SetTexCoord(0.08, 0.92, 0.08, 0.92)
    T.portrait:SetDesaturated(false)
    if dead then T.portrait:SetVertexColor(1, 0.82, 0.78) else T.portrait:SetVertexColor(1, 1, 1) end
    SHOW = tonumber(db.time) or 6.5
    T:EnableMouse(true)
    T:SetAlpha(0)
    Place(24)
    T:Show()
    if db.sound then ns.PlayKind(item.kind) end
end

T:SetScript("OnUpdate", function(self, el)
    if not showing or self.moving then return end
    local over = self:IsMouseOver()
    self.close:SetAlpha(over and 1 or 0)
    -- while the mouse is on it, it stays (so you can read it in peace)
    if not (over and t0 > 0.35 and t0 < SHOW) then t0 = t0 + el end
    -- drops in from above with a small bounce
    if t0 < 0.35 then
        local p = t0 / 0.35
        self:SetAlpha(math.min(1, p * 1.6))
        Place(24 * (1 - p) * (1 - p) - 4 * math.sin(p * math.pi))
    elseif t0 < SHOW then
        self:SetAlpha(1)
        if t0 < 0.4 then Place(0) end
    elseif t0 < SHOW + FADE then
        self:SetAlpha(1 - (t0 - SHOW) / FADE)
    else
        Next()
        return
    end
    -- the medallion breathes
    local a = 0.35 + 0.25 * math.sin(t0 * 3.2)
    self.medGlow:SetVertexColor(glowC[1], glowC[2], glowC[3], a)
end)

local function Legend(class)
    if not class or class == "" then return nil end
    local own = db.legends and db.legends[class]
    return own or ns.LEGENDS[class]
end

local function Toast(kind, fields, icon)
    -- a death of a class with a legend: about every second time the legend comments
    if kind == "death" then
        local lg = Legend(fields.class)
        if lg and ns.LINES.deathlegend and math.random() < 0.55 then
            fields.legend = lg
            kind = "deathlegend"
        end
    end
    local line = Pick(kind, fields.level)
    local text, chatText = Fill(line, fields), Fill(line, fields, true)
    if (kind == "death" or kind == "deathlegend") and fields.killer and fields.killer ~= "" then
        local killer = "  |cffff8866Tettes: " .. fields.killer .. "|r"
        text, chatText = text .. killer, chatText .. killer
    end
    queue[#queue + 1] = { kind = kind, text = text, icon = icon, fields = fields }
    if db.chat then print("|cffa88bff[Kodo Times]|r " .. chatText) end
    if not showing then Next() end
end

---------------------------------------------------------------------------
-- First start: "Kezdődjön a kaland!" - join the friends' channel with one click
---------------------------------------------------------------------------
-- the crew channel keeps its "MP" name on purpose: 0.9.x players and stored db.crew values use it
local DEFAULT_CREW = "MPhaverok"
function ns.Welcome()
    if ns.welcomeFrame then ns.welcomeFrame:Show(); return end
    local st = STYLE.levelup
    local W = CreateFrame("Frame", "KodoTimesWelcome", UIParent)
    ns.welcomeFrame = W
    W:SetSize(TW, math.floor(TW * st.v / 4 + 0.5))
    W:SetPoint("TOP", UIParent, "TOP", 0, -180)
    W:SetFrameStrata("DIALOG")
    W:EnableMouse(true)
    W.bg = W:CreateTexture(nil, "BACKGROUND")
    W.bg:SetAllPoints()
    W.bg:SetTexture(BannerTex(st.tex)); W.bg:SetTexCoord(0, 1, 0, st.v)
    W.shadow = ns.Slice(W, "shadow", 0.5, "BACKGROUND", -8):Fit(W, 26, 14)
    W.shadow:SetColor({ 0, 0, 0 }, 0)
    W.icon = W:CreateTexture(nil, "ARTWORK", nil, 1)
    W.icon:SetPoint("CENTER", W, "LEFT", TW * PORT_X, 0)
    W.icon:SetSize(TW * PORT_S, TW * PORT_S)
    W.icon:SetTexture("Interface\\Icons\\INV_Misc_Map_01")
    W.icon:SetTexCoord(0.08, 0.92, 0.08, 0.92)
    local m = W:CreateMaskTexture()
    m:SetTexture("Interface\\CharacterFrame\\TempPortraitAlphaMask", "CLAMPTOBLACKADDITIVE", "CLAMPTOBLACKADDITIVE")
    m:SetAllPoints(W.icon); W.icon:AddMaskTexture(m)
    local k = W:CreateFontString(nil, "OVERLAY")
    ns.SetFontSafe(k, ns.FONT_BODY_BOLD, 8)
    k:SetTextColor(0.80, 0.62, 0.38); k:SetShadowColor(0, 0, 0, 1); k:SetShadowOffset(1, -1)
    k:SetPoint("TOPLEFT", W, "TOPLEFT", TW * 0.308, -14)
    k:SetText("DUDE, WHERE IS MY KODO?")
    local t = W:CreateFontString(nil, "OVERLAY")
    ns.SetFontSafe(t, ns.FONT_TITLE, 19)
    t:SetTextColor(1, 0.78, 0.25); t:SetShadowColor(0, 0, 0, 1); t:SetShadowOffset(1, -1)
    t:SetPoint("TOPLEFT", k, "BOTTOMLEFT", 0, -3)
    t:SetText("ÜDV A KODÓKERESŐK KÖZÖTT!")
    -- shrink the title into the text column (clear of the GO medallion); measured before any width is set
    local TextW = t.GetUnboundedStringWidth or t.GetStringWidth
    for _, size in ipairs({ 17, 16, 15 }) do
        if (TextW(t) or 0) <= TW * 0.51 then break end
        ns.SetFontSafe(t, ns.FONT_TITLE, size)
    end
    t:SetWidth(TW * 0.51); t:SetWordWrap(false)
    local x = W:CreateFontString(nil, "OVERLAY")
    ns.SetFontSafe(x, ns.FONT_TITLE, 11)
    x:SetTextColor(0.96, 0.93, 0.86); x:SetShadowColor(0, 0, 0, 1); x:SetShadowOffset(1, -1)
    x:SetJustifyH("LEFT"); x:SetJustifyV("TOP"); x:SetWidth(TW * 0.51); x:SetWordWrap(true)
    x:SetPoint("TOPLEFT", t, "BOTTOMLEFT", 0, -3)
    x:SetText("Nyomj egy Let's go-t, és szólunk, ha valaki végre megtalálta a kodót, vagy ha a többiekkel valami nagyon fontos történik.")
    if (x:GetStringHeight() or 0) > 30 then ns.SetFontSafe(x, ns.FONT_TITLE, 10) end
    if (x:GetStringHeight() or 0) > 38 then ns.SetFontSafe(x, ns.FONT_TITLE, 9) end
    local med = W:CreateFontString(nil, "OVERLAY")
    ns.SetFontSafe(med, ns.FONT_TITLE, 19)
    med:SetPoint("CENTER", W, "LEFT", TW * MED_X, 0)
    med:SetTextColor(1, 0.78, 0.25); med:SetShadowColor(0, 0, 0, 1); med:SetShadowOffset(1, -1)
    med:SetText("GO")
    local function Btn(label, xoff, fn)
        local b = CreateFrame("Button", nil, W, "UIPanelButtonTemplate")
        b:SetSize(130, 24)
        b:SetPoint("TOP", W, "BOTTOM", xoff, -4)
        b:SetText(label)
        b:SetScript("OnClick", fn)
        return b
    end
    Btn("Let's go!", -70, function()
        db.welcomed = true
        char.welcomed = true; char.noCrew = nil
        db.crew = db.crew or DEFAULT_CREW
        W:Hide()
        ns.JoinCrew(true)
        Print("a haverok csatornája: " .. db.crew .. ". Saját csapat neve kell? /kodo crew <név>")
    end)
    Btn("Kösz, nem", 70, function()
        char.welcomed = true; char.noCrew = true
        if db.crew and LeaveChannelByName then pcall(LeaveChannelByName, db.crew) end
        W:Hide()
        Print("oké. Ha meggondolod: /kodo crew haverok")
    end)
    if db.sound then ns.PlayKind("welcome") end
    W:Show()
end

---------------------------------------------------------------------------
-- Sending
---------------------------------------------------------------------------
local seen = {}
-- every session has a random token: messages that come back to us (channels echo) are recognised by it
ns.TOKEN = format("%06x", random(0x100000, 0xFFFFFF))
function ns.IsMe(name)
    if not name then return false end
    local function norm(x) return (tostring(x or ""):gsub("%-.*$", ""):gsub("%s", ""):lower()) end
    local a = norm(name)
    return a == norm(MyName()) or a == norm(UnitName("player"))
end
local function Clean(s) return (tostring(s or ""):gsub("[|~]", "")) end

-- noFriends: skip the friend-list whispers (Map.lua whispers only the pals who need it)
local RESULT = {}
if Enum and Enum.SendAddonMessageResult then for k, v in pairs(Enum.SendAddonMessageResult) do RESULT[v] = k end end
local DEBUG = false
local function RawSend(msg, chan, target)
    local send = C_ChatInfo and C_ChatInfo.SendAddonMessage or SendAddonMessage
    if not send then
        if DEBUG then Print("|cffff5544nincs SendAddonMessage ezen a kliensen!|r") end
        return
    end
    local ok, res = pcall(send, PREFIX, msg, chan, target)
    local good = ok and (res == nil or res == true or res == 0)
    if DEBUG and not msg:find("^P~") then
        local r = not ok and ("HIBA: " .. tostring(res)) or good and "ok" or tostring(RESULT[res] or res)
        Print(format("|cff888888küld -> %s%s: %s  [%s]|r", chan, target and (" " .. tostring(target)) or "", msg:sub(1, 40), r))
    end
    return good
end
ns.RawSend = RawSend

local function SendAll(msg, noFriends)
    local allGood = true
    local function S(chan, target) if not RawSend(msg, chan, target) then allGood = false end end
    if db.guild and IsInGuild() then S("GUILD") end
    if db.group then
        if IsInRaid() then S(IsInGroup(LE_PARTY_CATEGORY_INSTANCE) and "INSTANCE_CHAT" or "RAID")
        elseif IsInGroup() then S(IsInGroup(LE_PARTY_CATEGORY_INSTANCE) and "INSTANCE_CHAT" or "PARTY") end
    end
    if not noFriends and db.friends and C_FriendList and C_FriendList.GetNumFriends then
        local me = UnitName("player")
        local _, myClass = UnitClass("player")
        local n = 0
        for i = 1, C_FriendList.GetNumFriends() do
            local f = C_FriendList.GetFriendInfoByIndex(i)
            if f and f.connected and f.name and f.name ~= me and n < 40 then
                n = n + 1
                S("WHISPER", f.name)
            end
        end
    end
    if db.crew then
        local id = GetChannelName(db.crew)
        if id and id > 0 then S("CHANNEL", id)
        elseif DEBUG then Print("|cffff5544a crew csatornán nem vagy bent (" .. db.crew .. ")|r") end
    end
    return allGood
end

ns.SendAll = SendAll
function ns.Whisper(msg, target)
    if target then RawSend(msg, "WHISPER", target) end
end
ns.Print = Print
function ns.DB() return db end

-- join the crew channel; check a bit later whether it worked (and try the other join function)
function ns.JoinCrew(report)
    if not db.crew then return end
    local id = GetChannelName(db.crew)
    if id and id > 0 then if report then Print("crew csatornán bent vagy (" .. db.crew .. ")") end return end
    if JoinTemporaryChannel then pcall(JoinTemporaryChannel, db.crew) end
    C_Timer.After(2, function()
        local id2 = GetChannelName(db.crew)
        if (not id2 or id2 == 0) and JoinChannelByName then pcall(JoinChannelByName, db.crew) end
        C_Timer.After(2, function()
            local id3 = GetChannelName(db.crew)
            if id3 and id3 > 0 then
                for i = 1, (NUM_CHAT_WINDOWS or 10) do
                    local cf = _G["ChatFrame" .. i]
                    if cf then
                        if ChatFrame_RemoveChannel then pcall(ChatFrame_RemoveChannel, cf, db.crew) end
                        if cf.RemoveChannel then pcall(cf.RemoveChannel, cf, db.crew) end
                    end
                end
                if report then Print("|cff7fff7fbeléptél a crew csatornába (" .. db.crew .. ")|r") end
            else
                Print("|cffff5544nem sikerült belépni a crew csatornába (" .. db.crew .. ").|r Próbáld kézzel: /join " .. db.crew)
            end
        end)
    end)
end

-- kind ~ fields, separated by "~"
-- raid instance, battleground or arena: no news from there (unless /kodo raidhir)
local function InQuietPlace()
    if not db.quietRaidPvp or not IsInInstance then return false end
    local inside, kind = IsInInstance()
    return inside and (kind == "raid" or kind == "pvp" or kind == "arena") or false
end
ns.InQuietPlace = InQuietPlace

local function Announce(kind, f)
    if not db.enabled then return end
    if InQuietPlace() then return end
    local id = format("%d%04d", floor(GetTime() * 10) % 100000, random(9999))
    local _, classFile = UnitClass("player")
    f.class = classFile
    local parts = { "1", kind, id, Clean(f.level), Clean(f.zone), Clean(f.skill), Clean(f.rank),
        Clean(f.itemID), Clean(f.itemName), Clean(f.quality), Clean(classFile), Clean(f.killer), Clean(f.icon), Clean(MyName()) }
    seen[id] = true
    local msg = table.concat(parts, "~")
    ns.Deliver(msg)
    if db.selfToast then   -- by default your own news only go to the others
        f.name = MyName()
        f.sender = UnitName("player")
        f.class = classFile
        Toast(kind, f, f.icon)
    end
end

-- deliver a news message to everyone; in combat (deaths, most level ups) the client may refuse
-- addon messages, so those wait until combat ends, and failed sends are retried
local pending = {}
local function DeliverNow(msg)
    local good = SendAll(msg)
    -- the pals we found by whisper (ping / earlier sessions) get it by whisper too:
    -- custom channels on this server don't pass addon messages on
    if ns.WhisperPals then
        local friends = {}
        if db.friends and C_FriendList and C_FriendList.GetNumFriends then
            for i = 1, C_FriendList.GetNumFriends() do
                local fr = C_FriendList.GetFriendInfoByIndex(i)
                if fr and fr.connected and fr.name then friends[fr.name:lower()] = true end
            end
        end
        for _, name in ipairs(ns.WhisperPals()) do
            if not friends[name:lower()] then
                if not RawSend(msg, "WHISPER", name) then good = false end
            end
        end
    end
    return good
end
local function InCombat()
    return (InCombatLockdown and InCombatLockdown()) or (UnitAffectingCombat and UnitAffectingCombat("player"))
end
function ns.Deliver(msg, tries)
    tries = tries or 0
    if InCombat() then pending[#pending + 1] = msg; return end
    if not DeliverNow(msg) and tries < 3 then
        C_Timer.After(4, function() ns.Deliver(msg, tries + 1) end)
    end
end
function ns.FlushPending()
    if InCombat() then return end
    local list = pending
    pending = {}
    for i, msg in ipairs(list) do C_Timer.After(0.5 * i, function() ns.Deliver(msg) end) end
end
do
    local ticker = CreateFrame("Frame")
    ticker:RegisterEvent("PLAYER_REGEN_ENABLED")
    ticker:RegisterEvent("PLAYER_ALIVE")
    ticker:RegisterEvent("PLAYER_UNGHOST")
    ticker:SetScript("OnEvent", function() C_Timer.After(1, ns.FlushPending) end)
    -- safety net: try again every few seconds while something waits
    if C_Timer.NewTicker then C_Timer.NewTicker(5, function() if #pending > 0 then ns.FlushPending() end end) end
end

---------------------------------------------------------------------------
-- Receiving
---------------------------------------------------------------------------
local function Split(s)
    local t = {}
    for part in (s .. "~"):gmatch("(.-)~") do t[#t + 1] = part end
    return t
end

local function OnAddonMessage(prefix, msg, chan, sender)
    if prefix ~= PREFIX then return end
    if DEBUG then
        if secret(msg) or secret(sender) then Print("|cffff5544jött üzenet, de a kliens titkosította (secret)|r")
        else Print(format("|cff888888jött <- %s %s: %s|r", tostring(chan), tostring(sender), msg:sub(1, 40))) end
    end
    if not db.enabled or secret(msg) or secret(sender) then return end
    local p = Split(msg)
    if p[1] == "PING" or p[1] == "PONG" then
        local who = Ambiguate and Ambiguate(sender, "short") or sender
        if ns.IsMe(who) or p[2] == ns.TOKEN then return end
        local full = p[3] and p[3] ~= "" and p[3] or nil
        if ns.NotePal then ns.NotePal(who, chan, full) end
        if p[1] == "PING" then
            Print(format("|cff7fff7fPING jött tőle: %s (%s)|r - válaszolok", full or who, tostring(chan)))
            RawSend("PONG~" .. ns.TOKEN .. "~" .. MyName(), "WHISPER", sender)
        else
            Print(format("|cff7fff7fPONG: %s látja az üzeneteidet (%s). Működik!|r", full or who, tostring(chan)))
        end
        return
    end
    if ns.MapMessage and ns.MapMessage(p, Ambiguate and Ambiguate(sender, "short") or sender, chan) then return end
    if p[1] ~= "1" or not ns.LINES[p[2]] or p[2] == "deathlegend" then return end
    local id = p[3]
    if seen[id] then return end
    seen[id] = true
    local name = Ambiguate and Ambiguate(sender, "short") or sender
    if ns.IsMe(name) then return end
    if ns.NotePal then ns.NotePal(name, chan, p[14]) end
    if p[14] and p[14] ~= "" and #p[14] > #name then name = p[14] end   -- show the full name (sender names can be cut)
    -- whisper target: keeps "-Realm" only for players from another realm, like Blizzard's own links
    local f = { name = name, sender = Ambiguate and Ambiguate(sender, "none") or sender,
        level = p[4], zone = p[5], skill = p[6], rank = p[7],
        itemID = p[8] ~= "" and p[8] or nil, itemName = p[9], quality = p[10], class = p[11],
        killer = p[12] ~= "" and p[12] or nil }
    local icon = p[13] and p[13] ~= "" and (tonumber(p[13]) or p[13]) or nil
    if f.itemID and GetItemIcon then icon = GetItemIcon(tonumber(f.itemID)) or icon end
    if p[2] == "skill" and not icon then icon = ProfIcon(f.skill) end
    Toast(p[2], f, icon)
end

---------------------------------------------------------------------------
-- Detecting your own news
---------------------------------------------------------------------------
-- profession milestones: every 25 points from 50, and every new maximum (Journeyman, Expert...)
local PROF_HEADERS = {}
for _, h in ipairs({ TRADE_SKILLS or "Professions", SECONDARY_SKILLS or "Secondary Skills", "Professions", "Secondary Skills" }) do
    PROF_HEADERS[h] = true
end

local function ReadProfessions()
    local out = {}
    if not GetNumSkillLines then return out end
    local inProf = false
    for i = 1, GetNumSkillLines() do
        local name, isHeader, _, rank = GetSkillLineInfo(i)
        if isHeader then inProf = PROF_HEADERS[name] or false
        elseif inProf and name and rank then out[name] = rank end
    end
    return out
end

local function CheckSkills()
    local now = ReadProfessions()
    char.skills = char.skills or {}
    for name, rank in pairs(now) do
        local old = char.skills[name]
        if old and rank > old then
            -- the highest milestone crossed since last time
            local hit
            for m = 50, 375, 25 do if old < m and rank >= m then hit = m end end
            if hit then Announce("skill", { skill = name, rank = hit, icon = ProfIcon(name) }) end
        end
        char.skills[name] = rank
    end
end

local function Pattern(fmt)
    if not fmt then return nil end
    fmt = fmt:gsub("([%(%)%.%%%+%-%*%?%[%]%^%$])", "%%%1")
    fmt = fmt:gsub("%%%%s", "(.+)"):gsub("%%%%d", "(%%d+)")
    return "^" .. fmt
end
local CREATE = Pattern(LOOT_ITEM_CREATED_SELF or "You create: %s.")
local LOOT = Pattern(LOOT_ITEM_SELF or "You receive loot: %s.")
local LOOT_MULTI = Pattern(LOOT_ITEM_SELF_MULTIPLE or "You receive loot: %sx%d.")

local function ItemInfo(link)
    local id = tonumber(link:match("item:(%d+)"))
    local name = link:match("%[(.-)%]")
    local q
    if C_Item and C_Item.GetItemQualityByID then q = C_Item.GetItemQualityByID(link) end
    if not q and GetItemInfo then q = select(3, GetItemInfo(link)) end
    if not q then
        local hex = link:match("|cff(%x%x%x%x%x%x)")
        for k, v in pairs(QUALITY) do if hex and v == hex:lower() then q = k end end
    end
    return id, name, q
end

local function OnLoot(msg)
    if not msg or secret(msg) then return end
    local link = CREATE and msg:match(CREATE)
    local crafted = link ~= nil
    if not link then link = (LOOT_MULTI and msg:match(LOOT_MULTI)) or (LOOT and msg:match(LOOT)) end
    if not link or not link:find("item:") then return end
    local id, name, q = ItemInfo(link)
    if not q then return end
    local f = { itemID = id, itemName = name, quality = q, icon = id and GetItemIcon and GetItemIcon(id) }
    if crafted and q == 3 then Announce("craftblue", f)
    elseif crafted and q >= 4 then Announce("craftepic", f)
    elseif not crafted and q >= 4 then Announce("epicloot", f) end
end

---------------------------------------------------------------------------
-- Who killed us? No combat log here, so we watch which hostile units have us
-- as their target (target, focus, mouseover, nameplates) while we are in combat.
---------------------------------------------------------------------------
local lastKiller = nil   -- { text = "Name (lvl)", t = GetTime() }
local function KillerText(u)
    local ok, name = pcall(UnitName, u)
    if not ok or not name or secret(name) then return nil end
    local lv = UnitLevel and UnitLevel(u)
    if lv and secret(lv) then lv = nil end
    if lv and lv < 0 then return name .. " (??)" end
    return lv and lv > 0 and format("%s (%d)", name, lv) or name
end
local function IsMyAttacker(u)
    if not UnitExists(u) or not UnitCanAttack("player", u) then return false end
    local ok, me = pcall(UnitIsUnit, u .. "target", "player")
    return ok and me and not secret(me)
end
local function ScanAttacker()
    local units = { "target", "focus", "mouseover" }
    if C_NamePlate and C_NamePlate.GetNamePlates then
        local ok, plates = pcall(C_NamePlate.GetNamePlates)
        if ok and plates then
            for _, pl in ipairs(plates) do
                local tok = pl.namePlateUnitToken or (pl.UnitFrame and pl.UnitFrame.unit)
                if tok then units[#units + 1] = tok end
            end
        end
    end
    for _, u in ipairs(units) do
        local ok, hit = pcall(IsMyAttacker, u)
        if ok and hit then
            local txt = KillerText(u)
            if txt then lastKiller = { text = txt, t = GetTime() }; return end
        end
    end
end
local killWatch = CreateFrame("Frame")
local kAcc = 0
killWatch:SetScript("OnUpdate", function(_, el)
    kAcc = kAcc + el
    if kAcc < 0.3 then return end
    kAcc = 0
    if UnitAffectingCombat and UnitAffectingCombat("player") then pcall(ScanAttacker) end
end)
local function TakeKiller()
    pcall(ScanAttacker)
    local k = lastKiller
    lastKiller = nil
    if k and GetTime() - k.t < 8 then return k.text end
    return nil
end

---------------------------------------------------------------------------
-- Events
---------------------------------------------------------------------------
local function DeepCopy(v)
    if type(v) ~= "table" then return v end
    local t = {}
    for k, x in pairs(v) do t[DeepCopy(k)] = DeepCopy(x) end
    return t
end

local ev = CreateFrame("Frame")
for _, e in ipairs({ "ADDON_LOADED", "PLAYER_LOGIN", "PLAYER_LEVEL_UP", "PLAYER_DEAD", "SKILL_LINES_CHANGED",
                     "CHAT_MSG_LOOT", "CHAT_MSG_ADDON", "PLAYER_LOGOUT" }) do
    pcall(ev.RegisterEvent, ev, e)
end
ev:SetScript("OnEvent", function(_, e, a1, a2, a3, a4)
    if e == "PLAYER_LOGOUT" then RestoreChannel(); return end   -- logout and /reload: give back a borrowed channel
    if e == "ADDON_LOADED" then
        if a1 ~= ADDON_NAME then return end
        -- only the full old addon defines this (it loads first: OptionalDeps). Two copies would show every
        -- toast twice and answer twice on PREFIX, so this one stays dormant: db stays nil, nothing runs.
        if SlashCmdList.MOTEVEPALS then dormant = true; return end
        -- updating from 0.9.x: the MotevePals stub keeps loading the old saved variables, and each table is
        -- copied once, on its own (an alt logs in after the first character already made KodoTimesDB).
        -- Deep copies, and the old tables are never written: going back to 0.9.x still finds them as they were.
        if KodoTimesDB == nil and type(MotevePalsDB) == "table" then KodoTimesDB = DeepCopy(MotevePalsDB) end
        if KodoTimesChar == nil and type(MotevePalsChar) == "table" then KodoTimesChar = DeepCopy(MotevePalsChar) end
        KodoTimesDB = KodoTimesDB or {}
        KodoTimesChar = KodoTimesChar or {}
        for k, v in pairs(DEFAULTS) do if KodoTimesDB[k] == nil then KodoTimesDB[k] = v end end
        db, char = KodoTimesDB, KodoTimesChar
        -- before 0.9.30 the default was TOP/TOP/0/-120 at 1.0: a profile still holding it was never
        -- moved or resized, so it moves to the new default once. posVersion is not in DEFAULTS on purpose.
        -- (a profile from before 0.9.26 had no scale: the loop above just gave it DEFAULTS.scale)
        if (db.posVersion or 1) < 2 then
            if db.point == "TOP" and db.relPoint == "TOP" and math.abs(tonumber(db.x) or 0) < 0.5
                and math.abs((tonumber(db.y) or 0) + 120) < 0.5 and (db.scale == 1 or db.scale == DEFAULTS.scale) then
                for _, k in ipairs({ "point", "relPoint", "x", "y", "scale" }) do db[k] = DEFAULTS[k] end
            end
            db.posVersion = 2
        end
        db.scale = ClampScale(db.scale)
        T:SetScale(db.scale)
        T:ClearAllPoints()
        T:SetPoint(db.point, UIParent, db.relPoint, db.x, db.y)
        if C_ChatInfo and C_ChatInfo.RegisterAddonMessagePrefix then C_ChatInfo.RegisterAddonMessagePrefix(PREFIX)
        elseif RegisterAddonMessagePrefix then RegisterAddonMessagePrefix(PREFIX) end
        return
    end
    if dormant and e == "PLAYER_LOGIN" then C_Timer.After(8, WarnDuplicate) end
    if not db then return end
    if e == "PLAYER_LOGIN" then
        char.skills = ReadProfessions()
        -- welcome is per character: every new character gets the "Let's go" window once
        if db.crew and not char.noCrew then C_Timer.After(5, function() ns.JoinCrew(false) end) end
        if not char.welcomed then C_Timer.After(6, function() if ns.Welcome then ns.Welcome() end end) end
        C_Timer.After(12, function()
            if not char.welcomed or (db.crew and not char.noCrew) or IsInGuild() or IsInGroup() then return end
            local nf = 0
            if C_FriendList and C_FriendList.GetNumFriends then
                for i = 1, C_FriendList.GetNumFriends() do
                    local f = C_FriendList.GetFriendInfoByIndex(i)
                    if f and f.connected then nf = nf + 1 end
                end
            end
            if nf == 0 then
                Print("|cffffcc00nem éred el a haverokat|r (nincs guild, csapat, online barát vagy crew). Írjátok be mindketten: /kodo crew <közös név>")
            end
        end)
    elseif e == "PLAYER_LEVEL_UP" then
        local lv = tonumber(a1) or UnitLevel("player")
        -- csak 5 szintenként (5, 10 ... 55) és 60-nál megy hír; a többi szintnél semmi
        local kind = (lv >= 60 and "level60") or (lv % 10 == 0 and "levelround") or (lv % 5 == 0 and "levelup") or nil
        if kind then Announce(kind, { level = lv }) end
    elseif e == "PLAYER_DEAD" then
        Announce("death", { zone = GetRealZoneText and GetRealZoneText() or "", killer = TakeKiller() })
    elseif e == "SKILL_LINES_CHANGED" then
        pcall(CheckSkills)
    elseif e == "CHAT_MSG_LOOT" then
        pcall(OnLoot, a1)
    elseif e == "CHAT_MSG_ADDON" then
        pcall(OnAddonMessage, a1, a2, a3, a4)
    end
end)

---------------------------------------------------------------------------
-- Slash
---------------------------------------------------------------------------
local function OnOff(v) return v and "be" or "ki" end

-- move mode on / off (/kodo move, and off when the options panel is hidden)
function ns.SetMoveMode(on)
    if not on and not T.moving then return end   -- already off: leave a showing news toast alone
    T.close:SetAlpha(0)
    if on then
        queue = {}
        T.bg:SetTexture(BannerTex(STYLE.levelup.tex)); T.bg:SetTexCoord(0, 1, 0, STYLE.levelup.v)
        T:SetHeight(math.floor(TW * STYLE.levelup.v / 4 + 0.5))
        T.title:SetText("KODO TIMES"); T.title:SetTextColor(1, 0.78, 0.25)
        SetBodyText("Húzd a helyére, a sarkánál méretezd, majd /kodo move"); T.med:SetText("")
        T:SetAlpha(1); T:Show()
        T.grip:Show(); T.grip:EnableMouse(true)
        pcall(T.EnableMouseWheel, T, true)
        -- only once the toast is up, so a failed open never leaves the toggle stuck on
        T:EnableMouse(true); T.moving = true
    else
        T:EnableMouse(false); T.moving = false
        T:StopMovingOrSizing(); SavePos()   -- a drag cut short by hiding gets no OnDragStop
        T.grip:Hide(); T.grip:EnableMouse(false)
        pcall(T.EnableMouseWheel, T, false)
        T:Hide(); showing = false
    end
end

-- /kodo, and the old /mpal and /pals still work
SLASH_KODOTIMES1, SLASH_KODOTIMES2, SLASH_KODOTIMES3 = "/kodo", "/mpal", "/pals"
SlashCmdList.KODOTIMES = function(input)
    if not db then if dormant then WarnDuplicate() end return end
    local cmd, arg = (input or ""):match("^(%S*)%s*(.-)%s*$")
    cmd = cmd:lower()
    if cmd == "test" then
        local me, meSender = MyName(), UnitName("player")
        local _, myClass = UnitClass("player")
        Toast("levelup", { name = me, sender = meSender, class = myClass, level = (UnitLevel("player") or 1) + 1 })
        Toast("death", { name = me, sender = meSender, class = myClass, zone = GetRealZoneText and GetRealZoneText() or "Barrens", killer = "Defias Pillager (14)" })
        Toast("deathlegend", { name = me, sender = meSender, class = "PALADIN", zone = "Barrens", legend = ns.LEGENDS.PALADIN })
        Toast("levelround", { name = me, sender = meSender, class = myClass, level = 30 })
        Toast("level60", { name = me, sender = meSender, class = myClass, level = 60 })
        Toast("skill", { name = me, sender = meSender, class = myClass, skill = "Blacksmithing", rank = 150 }, ProfIcon("Blacksmithing"))
        Toast("craftblue", { name = me, sender = meSender, class = myClass, itemID = 7960, itemName = "Truesilver Champion", quality = 3 },
            GetItemIcon and GetItemIcon(7960))
        Toast("epicloot", { name = me, sender = meSender, class = myClass, itemID = 2243, itemName = "Hand of Edward the Odd", quality = 4 },
            GetItemIcon and GetItemIcon(2243))
        Toast("craftepic", { name = me, sender = meSender, class = myClass, itemID = 12798, itemName = "Annihilator", quality = 4 },
            GetItemIcon and GetItemIcon(12798))
    elseif cmd == "crew" then
        if arg == "" then
            if db.crew and LeaveChannelByName then pcall(LeaveChannelByName, db.crew) end
            db.crew = nil; Print("crew csatorna kikapcsolva.")
        else
            db.crew = "MP" .. (arg:lower():gsub("%s", "")); db.welcomed = true
            char.welcomed = true; char.noCrew = nil
            ns.JoinCrew(true)
            Print("crew: " .. db.crew .. "  - a barátaidnak ugyanezt kell beírniuk: /kodo crew " .. arg)
        end
    elseif cmd == "legend" or cmd == "legenda" then
        -- /kodo legend paladin SADISS a paladinok istene
        local class, name, title = arg:match("^(%S+)%s+(%S+)%s*(.*)$")
        local CLASSES = { warrior = "WARRIOR", paladin = "PALADIN", hunter = "HUNTER", rogue = "ROGUE", priest = "PRIEST",
            shaman = "SHAMAN", mage = "MAGE", warlock = "WARLOCK", druid = "DRUID" }
        class = class and CLASSES[class:lower()]
        db.legends = db.legends or {}
        if class and name then
            db.legends[class] = { name = name, title = (title ~= "" and title) or "a legenda" }
            Print(format("%s legendája: %s, %s", class, name, db.legends[class].title))
        else
            Print("használat: /kodo legend <class> <név> <cím>   pl. /kodo legend paladin SADISS a paladinok istene")
            for c, lg in pairs(ns.LEGENDS) do if not db.legends[c] then print(format("   %s: %s, %s", c, lg.name, lg.title)) end end
            for c, lg in pairs(db.legends) do print(format("   %s: %s, %s (saját)", c, lg.name, lg.title)) end
        end
    elseif cmd == "move" then
        ns.SetMoveMode(not T.moving)
    elseif cmd == "time" or cmd == "ido" or cmd == "idő" then
        local n = tonumber(arg)
        if n and n >= 1 and n <= 60 then db.time = n end
        Print(format("a hír %.1f mp-ig marad kint (+ elhalványulás). Állítás: /kodo time <1-60>", tonumber(db.time) or 6.5))
    elseif cmd == "volume" or cmd == "hangero" or cmd == "hangerő" then
        local n = tonumber(arg)
        if n and n == n then
            db.volume = math.max(0, math.min(100, floor(n + 0.5)))
            Print(format("hangerő: %d%%", ns.Volume()) .. (db.sound and "" or "  (a hang most ki van kapcsolva: /kodo sound)"))
            if db.sound then ns.PlayKind("welcome") end
        else
            Print(format("hangerő: %d%%  (az addon saját hangjai). Állítás: /kodo volume <0-100>", ns.Volume()))
        end
    elseif cmd == "raidhir" or cmd == "raid" then
        db.quietRaidPvp = not db.quietRaidPvp
        Print("raidben / BG-n / arénában: " .. (db.quietRaidPvp and "nem küld hírt" or "ott is küld hírt"))
    -- intentionally undocumented (no button, not in the help): only for testing on purpose
    elseif cmd == "kuld" or cmd == "küld" or cmd == "sendtest" then
        -- a test news to the others (they see a level up from you)
        Announce("levelup", { level = UnitLevel("player") or 1 })
        Print("teszt-hír elküldve a haveroknak (szintlépés). Nekik kell felugrania.")
    elseif cmd == "weed" then
        db.moreWeed = not db.moreWeed
        if ns.ApplyWeed then ns.ApplyWeed(db.moreWeed) end
    elseif cmd == "feny" or cmd == "fény" or cmd == "light" then
        db.goodLight = not db.goodLight
        if ns.ApplyPreset then ns.ApplyPreset("light", db.goodLight) end
    elseif cmd == "opciok" or cmd == "opciók" or cmd == "options" or cmd == "config" then
        if ns.OpenOptions then ns.OpenOptions() end
    elseif cmd == "welcome" then
        ns.Welcome()
    elseif cmd == "debug" then
        DEBUG = not DEBUG
        Print("debug: " .. OnOff(DEBUG) .. (DEBUG and "  - minden küldött és kapott Kodo Times-üzenetet kiír (a pozíciókat csak fogadáskor)" or ""))
    elseif cmd == "ping" then
        -- /kodo ping            -> to every path (guild, group, friends, crew)
        -- /kodo ping Név        -> direct whisper to one player
        local wasDebug = DEBUG; DEBUG = true
        if arg ~= "" then RawSend("PING~" .. ns.TOKEN .. "~" .. MyName(), "WHISPER", arg) else SendAll("PING~" .. ns.TOKEN .. "~" .. MyName()) end
        DEBUG = wasDebug
        local paths = {}
        if db.guild and IsInGuild() then paths[#paths + 1] = "guild" end
        if db.group and IsInGroup() then paths[#paths + 1] = "csapat" end
        local nf = 0
        if C_FriendList and C_FriendList.GetNumFriends then
            for i = 1, C_FriendList.GetNumFriends() do
                local f = C_FriendList.GetFriendInfoByIndex(i)
                if f and f.connected then nf = nf + 1 end
            end
        end
        if db.friends and nf > 0 then paths[#paths + 1] = nf .. " online barát" end
        if db.crew then
            local id = GetChannelName(db.crew)
            paths[#paths + 1] = "crew " .. db.crew .. ((id and id > 0) and "" or " |cffff5544(NEM vagy bent!)|r")
        end
        if arg == "" and #paths == 0 then
            Print("|cffff5544Nincs semmi, amin át elérnéd a többieket:|r nem vagy guildben, csapatban, nincs online barátod és nincs crew. "
                .. "Legegyszerűbb: mindketten írjátok be: /kodo crew haverok")
        else
            Print("PING elküldve: " .. (arg ~= "" and arg or table.concat(paths, ", ")) .. ". Ha a másiknál fut az addon, pár mp-en belül jön a PONG.")
        end
    elseif ns.MapSlash and ns.MapSlash(cmd, arg) then
        -- handled in Map.lua
    elseif cmd == "sound" then db.sound = not db.sound; Print("hang: " .. OnOff(db.sound))
    elseif cmd == "chat" then db.chat = not db.chat; Print("chatbe is kiírja: " .. OnOff(db.chat))
    elseif cmd == "self" then db.selfToast = not db.selfToast; Print("a saját híreid nálad is felugranak: " .. OnOff(db.selfToast))
    elseif cmd == "guild" then db.guild = not db.guild; Print("guildnek küldés: " .. OnOff(db.guild))
    elseif cmd == "friends" then db.friends = not db.friends; Print("barátlistának küldés: " .. OnOff(db.friends))
    elseif cmd == "group" then db.group = not db.group; Print("csapatnak küldés: " .. OnOff(db.group))
    elseif cmd == "off" or cmd == "on" then db.enabled = (cmd == "on"); Print("Kodo Times: " .. OnOff(db.enabled))
    else
        Print(format("be: %s  ·  guild: %s  ·  csapat: %s  ·  barátok: %s  ·  crew: %s  ·  hang: %s  ·  hangerő: %d%%",
            OnOff(db.enabled), OnOff(db.guild), OnOff(db.group), OnOff(db.friends),
            db.crew and ((char.noCrew and db.crew .. " (ezen a karakteren kihagyva)") or
                ((GetChannelName(db.crew) or 0) > 0 and db.crew .. " |cff7fff7f(bent vagy)|r" or db.crew .. " |cffff5544(NEM vagy bent)|r")) or "nincs",
            OnOff(db.sound), ns.Volume()))
        print("   /kodo test            minta-hírek")
        print("   /kodo crew <név>      közös rejtett csatorna a haveroknak (mind ugyanazt írjátok be)")
        print("   /kodo move            a felugró ablak mozgatása, a sarkánál / görgővel méretezés")
        print("   /kodo time <mp>       meddig maradjon kint (most: " .. (db.time or 6.5) .. " mp)")
        print("   /kodo volume <0-100>  az addon hangjainak hangereje (most: " .. ns.Volume() .. "%)")
        print("   bezárás: X a sarokban / bal klikk = ez,  jobb klikk = ez + a sorban állók")
        print("   /kodo legend <class> <név> <cím>   class-legenda halálhírekhez")
        print("   /kodo hol             ki hol van most")
        print("   /kodo self            a saját híreid nálad is felugorjanak (alap: ki)  ·  /kodo welcome")
        print("   /kodo weed            MORE WEED! ki/be (sűrűbb fű)")
        print("   /kodo feny            Jó fények ki/be (kontraszt 80, fényerő 49, gamma 1.2)")
        print("   /kodo opciok          beállítások (Beállítások > Kiegészítők > Kodo Times)")
        print("   /kodo ping [név]      kapcsolat-teszt (név nélkül minden csatornán)  ·  /kodo debug")
        print("   /kodo map | share     haverok a térképen ki/be  ·  a saját helyed megosztása ki/be")
        print("   /kodo nevek           nevek kiírva a térképen (alap: ki, csak egér rá)")
        print("   /kodo raidhir         raidben / BG-n is menjenek a hírek (alap: nem)")
        print("   /kodo sound | chat | self | guild | group | friends   ki/be")
        print("   /kodo on | off")
    end
end
