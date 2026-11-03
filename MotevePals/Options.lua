-- Moteve Pals - page in the game's Options > AddOns list, with every on/off switch.
local ADDON_NAME, ns = ...
local format = string.format

local OPTIONS = {
    { head = "Hírek" },
    { key = "enabled",      text = "Moteve Pals bekapcsolva",              tip = "Ha ki van kapcsolva, nem küld és nem mutat semmit." },
    { key = "selfToast",    text = "A saját híreim nálam is ugorjanak fel", tip = "Alapból csak a haverok látják, ami veled történik." },
    { key = "chat",         text = "Hírek a chatbe is",                     tip = "A felugró hír szövege a chatablakba is bekerül." },
    { key = "sound",        text = "Hang a felugró híreknél",               tip = "WoW-os hang: halálnál raid warning, szintlépésnél level up.\nAlatta a hangerő: csak az addon saját hangjaié.", below = 30 },
    { key = "quietRaidPvp", text = "Raidben, BG-n, arénában ne küldjön hírt", tip = "Dungeonban továbbra is megy." },
    { head = "Kinek menjen" },
    { key = "guild",        text = "Guild",                                 tip = "A guildtagok közül azok kapják, akiknél fut az addon." },
    { key = "group",        text = "Csapat / raid",                         tip = "A csapattagok közül azok kapják, akiknél fut az addon." },
    { key = "friends",      text = "Barátlista (suttogva)",                 tip = "Az online barátaid közül azok kapják, akiknél fut az addon." },
    { head = "Térkép", col = 2 },
    { key = "share",        text = "A helyem megosztása a haverokkal",      tip = "Ha kikapcsolod, a többiek nem látnak a térképen." },
    { key = "map",          text = "Haverok a világtérképen",               tip = "Kis class-színű pöttyök; egérrel rámutatva minden infó." },
    { key = "mapNames",     text = "Nevek kiírva a térképen",               tip = "Alapból csak egérrel rámutatva látszik a név.", refreshMap = true },
    { head = "Grafika" },
    { key = "moreWeed",     text = "MORE WEED!",
      tip = "Sűrűbb és messzebbre látszó fű és növényzet:\ngroundEffectDensity 256, groundEffectFade 370, groundEffectDist 500.\nKikapcsolva visszaáll az alapértékre.", preset = "weed" },
    { key = "goodLight",    text = "Jó fények",
      tip = "Kontraszt 80, fényerő 49, gamma 1.2.\nKikapcsolva visszaáll az alapértékre.", preset = "light" },
}

-- graphics presets: on = these CVars, off = the game's defaults
local PRESETS = {
    weed  = { key = "moreWeed",  on = "MORE WEED! bekapcsolva", off = "növényzet visszaállítva alapértékre",
              cvars = { groundEffectDensity = "256", groundEffectFade = "370", groundEffectDist = "500" } },
    light = { key = "goodLight", on = "Jó fények bekapcsolva", off = "fények visszaállítva alapértékre",
              cvars = { Contrast = "80", Brightness = "49", Gamma = "1.2" } },
}
local function GetDef(name)
    if C_CVar and C_CVar.GetCVarDefault then local ok, v = pcall(C_CVar.GetCVarDefault, name); if ok and v then return v end end
    if GetCVarDefault then local ok, v = pcall(GetCVarDefault, name); if ok and v then return v end end
    return nil
end
local GetCV, SetCV = ns.GetCV, ns.SetCV   -- from Pals.lua
-- remember the values from before the first switch-on (fallback when the client has no default lookup)
local function RememberPrev(id)
    local db = ns.DB()
    if not db then return end
    db.presetPrev = db.presetPrev or {}
    if db.presetPrev[id] then return end
    local t = {}
    for name in pairs(PRESETS[id].cvars) do t[name] = GetCV(name) end
    db.presetPrev[id] = t
end
function ns.ApplyPreset(id, on, quiet)
    local pr = PRESETS[id]
    if not pr then return end
    local db = ns.DB()
    if on then RememberPrev(id) end
    for name, v in pairs(pr.cvars) do
        if on then SetCV(name, v)
        else
            local def = GetDef(name) or (db and db.presetPrev and db.presetPrev[id] and db.presetPrev[id][name])
            if def then SetCV(name, def) end
        end
    end
    if not quiet and ns.Print then ns.Print(on and pr.on or pr.off) end
end
function ns.ApplyWeed(on, quiet) ns.ApplyPreset("weed", on, quiet) end

local panel = CreateFrame("Frame", "MotevePalsOptions")
panel.name = "Moteve Pals"
panel:Hide()

local title = panel:CreateFontString(nil, "ARTWORK", "GameFontNormalLarge")
ns.SetFontSafe(title, ns.FONT_BODY_BOLD, 18)
title:SetPoint("TOPLEFT", 16, -16)
title:SetText("Moteve Pals")
local sub = panel:CreateFontString(nil, "ARTWORK", "GameFontHighlightSmall")
ns.SetFontSafe(sub, ns.FONT_BODY, 12)
sub:SetPoint("TOPLEFT", title, "BOTTOMLEFT", 0, -6)
sub:SetText("Vicces hírek a haverokról, és ki hol van a térképen. Parancsok: /mpal")

local checks = {}
local volumeAnchor, UpdateVolumeState   -- the sound checkbox (the volume row hangs under it), set below
-- two columns so everything fits without scrolling
local COLX = { 16, 340 }
local colY = { -60, -60 }
local col = 1
local y = -60
for _, o in ipairs(OPTIONS) do
    if o.head then
        if o.col then col = o.col end
        y = colY[col]
        local h = panel:CreateFontString(nil, "ARTWORK", "GameFontNormal")
        ns.SetFontSafe(h, ns.FONT_BODY_BOLD, 13)
        h:SetPoint("TOPLEFT", COLX[col], y - 6)
        h:SetText(o.head)
        y = y - 26
        colY[col] = y
    else
        y = colY[col]
        local cb = CreateFrame("CheckButton", nil, panel, "UICheckButtonTemplate")
        cb:SetPoint("TOPLEFT", COLX[col] + 4, y)
        cb:SetSize(26, 26)
        local label = (type(rawget(cb, "Text")) == "table" and cb.Text) or (type(rawget(cb, "text")) == "table" and cb.text)
            or cb:CreateFontString(nil, "ARTWORK", "GameFontHighlight")
        label:ClearAllPoints()
        label:SetPoint("LEFT", cb, "RIGHT", 4, 0)
        label:SetFontObject("GameFontHighlight")
        ns.SetFontSafe(label, ns.FONT_BODY, 12)
        label:SetText(o.text)
        cb.opt = o
        cb:SetScript("OnClick", function(self)
            local db = ns.DB()
            if not db then return end
            db[self.opt.key] = self:GetChecked() and true or false
            if self.opt.preset then ns.ApplyPreset(self.opt.preset, db[self.opt.key]) end
            if self.opt.key == "sound" then UpdateVolumeState() end
            if self.opt.key == "map" or self.opt.refreshMap then
                if ns.RefreshMap then pcall(ns.RefreshMap) end
            end
        end)
        cb:SetScript("OnEnter", function(self)
            ns.Tooltip:SetOwner(self, "ANCHOR_RIGHT")
            ns.Tooltip:AddLine(self.opt.text, 1, 1, 1)
            ns.Tooltip:AddLine(self.opt.tip, 1, 0.82, 0, true)
            ns.ShowTooltip()
        end)
        cb:SetScript("OnLeave", function() ns.Tooltip:Hide() end)
        checks[#checks + 1] = cb
        y = y - 26
        if o.below then volumeAnchor = cb; y = y - o.below end   -- room for the row under it
        colY[col] = y
    end
end

-- how long a news stays on screen: - [ 6.5 mp ] +
y = colY[2]
local timeLabel = panel:CreateFontString(nil, "ARTWORK", "GameFontNormal")
ns.SetFontSafe(timeLabel, ns.FONT_BODY, 12)
timeLabel:SetPoint("TOPLEFT", COLX[2], y - 14)
timeLabel:SetText("Meddig maradjon kint egy hír")
local timeValue = panel:CreateFontString(nil, "ARTWORK", "GameFontHighlight")
ns.SetFontSafe(timeValue, ns.FONT_BODY, 12)
local function TimeBtn(txt, delta, anchorTo, x)
    local b = CreateFrame("Button", nil, panel, "UIPanelButtonTemplate")
    b:SetSize(26, 22)
    b:SetPoint("LEFT", anchorTo, "RIGHT", x, 0)
    b:SetText(txt)
    ns.SetFontSafe(b:GetFontString(), ns.FONT_BODY, 12)
    b:SetScript("OnClick", function()
        local db = ns.DB(); if not db then return end
        local t = (tonumber(db.time) or 6.5) + delta
        db.time = math.max(2, math.min(30, t))
        timeValue:SetText(format("%.1f mp", db.time))
    end)
    return b
end
local minus = TimeBtn("-", -0.5, timeLabel, 12)
timeValue:SetPoint("LEFT", minus, "RIGHT", 8, 0)
timeValue:SetWidth(56)
local plus = CreateFrame("Button", nil, panel, "UIPanelButtonTemplate")
plus:SetSize(26, 22)
plus:SetPoint("LEFT", timeValue, "RIGHT", 8, 0)
plus:SetText("+")
ns.SetFontSafe(plus:GetFontString(), ns.FONT_BODY, 12)
plus:SetScript("OnClick", function()
    local db = ns.DB(); if not db then return end
    db.time = math.min(30, (tonumber(db.time) or 6.5) + 0.5)
    timeValue:SetText(format("%.1f mp", db.time))
end)

-- the addon's own sound volume, under the sound checkbox: Hangerő [slider] 80%  (or - 80% + without the template)
local volWidgets, volSlider, refreshing, lastPreview = {}, nil, false, nil
local volLabel = panel:CreateFontString(nil, "ARTWORK", "GameFontHighlight")
ns.SetFontSafe(volLabel, ns.FONT_BODY, 12)
volLabel:SetPoint("TOPLEFT", volumeAnchor, "BOTTOMLEFT", 30, -8)
volLabel:SetText("Hangerő")
local volValue = panel:CreateFontString(nil, "ARTWORK", "GameFontHighlight")
ns.SetFontSafe(volValue, ns.FONT_BODY, 12)
local function SetVolume(v)
    local db = ns.DB(); if not db then return end
    db.volume = math.max(0, math.min(100, math.floor(v + 0.5)))
    volValue:SetText(ns.Volume() .. "%")
    -- a short sample, at most ~3 a second while dragging, only when sound is on
    if db.sound and ns.PlayKind and (not lastPreview or GetTime() - lastPreview >= 0.3) then
        lastPreview = GetTime()
        ns.PlayKind("welcome")
    end
end
local okSlider, slider = pcall(CreateFrame, "Slider", "MotevePalsVolumeSlider", panel, "OptionsSliderTemplate")
if okSlider and slider then
    volSlider = slider
    slider:SetWidth(150)
    slider:SetPoint("LEFT", volLabel, "RIGHT", 12, 0)
    slider:SetMinMaxValues(0, 100)
    slider:SetValueStep(5)
    if slider.SetObeyStepOnDrag then slider:SetObeyStepOnDrag(true) end
    for _, part in ipairs({ "Low", "High", "Text" }) do   -- the template's own texts: we have ours
        local fs = rawget(slider, part) or _G["MotevePalsVolumeSlider" .. part]
        if fs and fs.SetText then fs:SetText("") end
    end
    slider:SetScript("OnValueChanged", function(_, value)
        if refreshing then return end   -- Refresh setting it: no write, no sample
        local v = math.floor(value / 5 + 0.5) * 5
        if ns.Volume() ~= v then SetVolume(v) end
    end)
    volValue:SetPoint("LEFT", slider, "RIGHT", 10, 0)
    volWidgets = { volLabel, slider, volValue }
else
    local function VolBtn(txt, delta)
        local b = CreateFrame("Button", nil, panel, "UIPanelButtonTemplate")
        b:SetSize(26, 22)
        b:SetText(txt)
        ns.SetFontSafe(b:GetFontString(), ns.FONT_BODY, 12)
        b:SetScript("OnClick", function() SetVolume(ns.Volume() + delta) end)
        return b
    end
    local vMinus, vPlus = VolBtn("-", -10), VolBtn("+", 10)
    vMinus:SetPoint("LEFT", volLabel, "RIGHT", 12, 0)
    volValue:SetPoint("LEFT", vMinus, "RIGHT", 8, 0)
    volValue:SetWidth(40)
    vPlus:SetPoint("LEFT", volValue, "RIGHT", 8, 0)
    volWidgets = { volLabel, vMinus, volValue, vPlus }
end
volValue:SetText("100%")
-- dimmed and disabled while the sound is off
function UpdateVolumeState()
    local db = ns.DB()
    local on = db and db.sound and true or false
    for _, w in ipairs(volWidgets) do
        w:SetAlpha(on and 1 or 0.4)
        if w.Enable and w.Disable then if on then w:Enable() else w:Disable() end end
    end
end

y = math.min(colY[1], colY[2] - 44) - 14

-- handy buttons
local function Action(txt, cmd, x, yy)
    local b = CreateFrame("Button", nil, panel, "UIPanelButtonTemplate")
    b:SetSize(180, 24)
    b:SetPoint("TOPLEFT", x, yy)
    b:SetText(txt)
    ns.SetFontSafe(b:GetFontString(), ns.FONT_BODY, 12)
    b:SetScript("OnClick", function() if SlashCmdList.MOTEVEPALS then SlashCmdList.MOTEVEPALS(cmd) end end)
    return b
end
Action("Minta-hírek (nálam)", "test", 16, y)
Action("Felugró ablak mozgatása", "move", 206, y)
Action("Kapcsolat-teszt (ping)", "ping", 396, y)
y = y - 28
Action("Ki hol van (chatbe)", "hol", 16, y)
Action("Diagnosztika (chatbe)", "diag", 206, y)

local function Refresh()
    local db = ns.DB()
    if not db then return end
    for _, cb in ipairs(checks) do cb:SetChecked(db[cb.opt.key] and true or false) end
    timeValue:SetText(format("%.1f mp", tonumber(db.time) or 6.5))
    refreshing = true
    if volSlider then volSlider:SetValue(ns.Volume()) end
    refreshing = false
    volValue:SetText(ns.Volume() .. "%")
    UpdateVolumeState()
end
panel:SetScript("OnShow", Refresh)
panel:SetScript("OnHide", function() if ns.SetMoveMode then ns.SetMoveMode(false) end end)   -- closing the settings ends move mode
panel.refresh = Refresh   -- old options panel API

-- register in Options > AddOns (new Settings API, or the old Interface Options)
local function Register()
    if Settings and Settings.RegisterCanvasLayoutCategory and Settings.RegisterAddOnCategory then
        local ok, cat = pcall(Settings.RegisterCanvasLayoutCategory, panel, panel.name)
        if ok and cat then
            pcall(Settings.RegisterAddOnCategory, cat)
            ns.optionsCategory = cat
            return
        end
    end
    if InterfaceOptions_AddCategory then pcall(InterfaceOptions_AddCategory, panel) end
end
local reg = CreateFrame("Frame")
reg:RegisterEvent("PLAYER_LOGIN")
reg:SetScript("OnEvent", function()
    Register()
    local db = ns.DB()
    if db then   -- keep them on after restarts
        for id, pr in pairs(PRESETS) do if db[pr.key] then ns.ApplyPreset(id, true, true) end end
    end
end)

-- open it from chat: /mpal opciok
function ns.OpenOptions()
    if Settings and Settings.OpenToCategory and ns.optionsCategory then
        local id = ns.optionsCategory.GetID and ns.optionsCategory:GetID() or ns.optionsCategory.ID
        pcall(Settings.OpenToCategory, id)
    elseif InterfaceOptionsFrame_OpenToCategory then
        pcall(InterfaceOptionsFrame_OpenToCategory, panel)
        pcall(InterfaceOptionsFrame_OpenToCategory, panel)
    end
end
