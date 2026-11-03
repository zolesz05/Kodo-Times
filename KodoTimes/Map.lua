-- Kodo Times - where are the others? Everyone who runs the addon shares their position every few
-- seconds (hidden addon message), and the pals show up on the world map as class-coloured portraits
-- with their name. Works on the zone map and the continent map too (positions are projected).
--
-- Messages:  P~mapID~x~y~level~class~dead~zone   (x, y: 0..10000; mapID 0 = no position, e.g. in an instance)
--            H = "hello, do you run it?" (whispered to online friends at login)   h = "yes"
local _, ns = ...
local format, floor, abs = string.format, math.floor, math.abs
local secret = issecretvalue or function() return false end

local SEND_EVERY = 5        -- seconds between checks
local HEARTBEAT = 30        -- send even if not moved
local STALE, GONE = 90, 300 -- fade the pin after, remove after (seconds)

local pals = {}             -- name -> { map, x, y, level, class, dead, zone, t, lastGroup }
local diag = { sent = 0, lastSent = 0, lastPos = nil, recv = {} }   -- for /kodo diag
ns.PalPositions = pals

local function Now() return GetTime() end
local ClassColor = ns.ClassColor
local function Ago(sec)
    sec = floor(sec)
    if sec < 15 then return "épp most" end
    if sec < 60 then return sec .. " másodperce" end
    if sec < 3600 then return floor(sec / 60) .. " perce" end
    return floor(sec / 3600) .. " órája"
end
-- small coloured dot as inline texture (fonts may lack the bullet glyph)
local DOT = "|T" .. ns.TEX("circle") .. ":8:8:0:0:64:64:0:64:0:64:%d:%d:%d|t"
local function Dot(r, g, b) return format(DOT, r * 255, g * 255, b * 255) end
-- signal state: text, colour
local function Signal(age)
    if age < 15 then return "Élő jel", 0.35, 0.95, 0.45 end
    if age < STALE then return "Utolsó jel", 0.95, 0.80, 0.35 end
    return "A jel megszakadt", 0.6, 0.6, 0.6
end

---------------------------------------------------------------------------
-- Layer: NPC GUIDs look like Creature-0-<server>-<instance>-<zoneUID>-<npcID>-<spawn>;
-- the zoneUID differs between layers, so NPCs around us tell which layer we are on.
---------------------------------------------------------------------------
local myLayer = { id = nil, t = 0 }
local function LayerFromUnit(u)
    if not UnitExists(u) or UnitIsPlayer(u) then return nil end
    local ok, guid = pcall(UnitGUID, u)
    if not ok or not guid or secret(guid) then return nil end
    local kind, _, _, _, zoneUID = strsplit("-", guid)
    if (kind == "Creature" or kind == "Vehicle") and zoneUID and zoneUID ~= "0" then return zoneUID end
    return nil
end
local function ScanLayer()
    local units = { "target", "mouseover", "focus" }
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
        local ok, id = pcall(LayerFromUnit, u)
        if ok and id then myLayer.id, myLayer.t = id, GetTime(); return end
    end
end
-- the layer we are on (nil if no NPC seen in the last 10 minutes or we changed continent)
function ns.MyLayer()
    if myLayer.id and GetTime() - myLayer.t < 600 then return myLayer.id end
    return nil
end
local function LayerText(id, mine)
    if not id or id == "" then return "ismeretlen (nem látott még NPC-t)", 0.6, 0.6, 0.6 end
    if mine and id == mine then return "ugyanazon, mint te (" .. id .. ")", 0.35, 0.95, 0.45 end
    if mine then return "MÁS layer (" .. id .. "), te: " .. mine, 1, 0.6, 0.25 end
    return id .. "  (a sajátodat még nem tudom)", 0.9, 0.85, 0.6
end
ns.LayerText = LayerText

---------------------------------------------------------------------------
-- My position
---------------------------------------------------------------------------
local function MyPosition()
    if not (C_Map and C_Map.GetBestMapForUnit) then return 0, 0, 0 end
    local ok, map = pcall(C_Map.GetBestMapForUnit, "player")
    if not ok or not map or secret(map) then return 0, 0, 0 end
    local ok2, pos = pcall(C_Map.GetPlayerMapPosition, map, "player")
    if not ok2 or not pos then return map, 0, 0, true end   -- e.g. in an instance: zone only
    local x, y
    if pos.GetXY then x, y = pos:GetXY() else x, y = pos.x, pos.y end
    if not x or not y or secret(x) or secret(y) then return nil end   -- secret in combat: skip this round
    return map, x, y
end

local last = { map = -1, x = -1, y = -1, t = 0, dead = nil }
local function SendPosition(force)
    local db = ns.DB()
    if not db or not db.enabled or not db.share then return end
    local map, x, y, noPos = MyPosition()
    if map == nil then return end
    if noPos then map, x, y = 0, 0, 0 end
    local dead = UnitIsDeadOrGhost and UnitIsDeadOrGhost("player") and "1" or "0"
    if secret(dead) then dead = "0" end
    local now = Now()
    local moved = map ~= last.map or abs(x - last.x) > 0.0015 or abs(y - last.y) > 0.0015 or dead ~= last.dead
    if not force and not moved and now - last.t < HEARTBEAT then return end
    last.map, last.x, last.y, last.t, last.dead = map, x, y, now, dead
    local _, class = UnitClass("player")
    local zone = (GetRealZoneText and GetRealZoneText() or ""):gsub("[|~]", "")
    local full = (ns.MyName and ns.MyName() or UnitName("player") or ""):gsub("[|~]", "")
    diag.lastPos = format("map %d  %.1f, %.1f", map, x * 100, y * 100)
    local msg = format("P~%d~%d~%d~%d~%s~%s~%s~%s~%s~%s", map, floor(x * 10000 + 0.5), floor(y * 10000 + 0.5),
        UnitLevel("player") or 0, class or "", dead, zone, ns.TOKEN, full, ns.MyLayer() or "")
    ns.SendAll(msg, true)   -- guild, group, crew channel
    diag.sent = diag.sent + 1; diag.lastSent = now
    -- pals we only reach by whisper (friends not in the guild / group / crew), at most 8 per round
    local n = 0
    for name, p in pairs(pals) do
        if n >= 8 then break end
        if p.whisper and p.heard and now - p.heard < 600 and now - (p.lastGroup or 0) > 20 then
            ns.Whisper(msg, name); n = n + 1
        end
    end
end

-- ask the online friends whether they run the addon too
local asked = {}
local function Hello()
    local db = ns.DB()
    if not db or not db.enabled or not db.share or not db.friends then return end
    if not (C_FriendList and C_FriendList.GetNumFriends) then return end
    local me = UnitName("player")
    for i = 1, C_FriendList.GetNumFriends() do
        local f = C_FriendList.GetFriendInfoByIndex(i)
        if f and f.connected and f.name and f.name ~= me and not asked[f.name] then
            asked[f.name] = true
            ns.Whisper("H~" .. ns.TOKEN .. "~" .. (ns.MyName and ns.MyName() or ""), f.name)
        end
    end
end

-- every pal we currently reach by whisper (heard from in the last 10 minutes)
function ns.WhisperPals()
    local out, now = {}, Now()
    for name, p in pairs(pals) do
        if p.whisper and p.heard and now - p.heard < 600 then out[#out + 1] = name end
    end
    return out
end

-- the longer of the routing name and the name the sender reported (one of them can be cut)
local function Better(a, b)
    if not b or b == "" then return a end
    if not a or a == "" then return b end
    return (#b > #a) and b or a
end

-- remember pals across sessions, so we can whisper them at login even when channels don't deliver
local function Remember(name, display)
    local db = ns.DB()
    if not db or not name then return end
    db.knownPals = db.knownPals or {}
    db.knownPals[name] = { d = display, t = time and time() or 0 }
end

-- someone talked to us (ping/pong, news, hello): remember them; everyone we know gets our
-- position by whisper too (custom channels on this server don't always deliver addon messages)
function ns.NotePal(name, chan, display)
    if not name or ns.IsMe(name) then return end
    local pal = pals[name]
    local new = not pal
    pal = pal or {}
    pals[name] = pal
    pal.whisper = true
    pal.heard = Now()
    if chan ~= "WHISPER" then pal.lastGroup = Now() end
    pal.display = Better(pal.display or name, display)
    Remember(name, pal.display)
    if new then C_Timer.After(1, function() pcall(SendPosition, true) end) end
end

-- hide the "player not found" system line caused by our hidden hello whispers to offline pals
local quietUntil = {}
local origWhisper = ns.Whisper
ns.Whisper = function(msg, target)
    if target then quietUntil[target:lower()] = GetTime() + 3 end
    return origWhisper(msg, target)
end
if ChatFrame_AddMessageEventFilter and ERR_CHAT_PLAYER_NOT_FOUND_S then
    local pat = "^" .. ERR_CHAT_PLAYER_NOT_FOUND_S:gsub("([%(%)%.%%%+%-%*%?%[%]%^%$])", "%%%1"):gsub("%%%%s", "(.+)") .. "$"
    ChatFrame_AddMessageEventFilter("CHAT_MSG_SYSTEM", function(_, _, msg)
        if type(msg) ~= "string" or secret(msg) then return false end
        local who = msg:match(pat)
        if who and quietUntil[who:lower()] and quietUntil[who:lower()] > GetTime() then return true end
        return false
    end)
end

-- say hello by whisper to pals from earlier sessions and to the members of the crew channel
local helloed = {}
local function HelloKnown()
    local db = ns.DB()
    if not db or not db.enabled or not db.share then return end
    local hello = "H~" .. ns.TOKEN .. "~" .. (ns.MyName and ns.MyName() or "")
    local n = 0
    for name in pairs(db.knownPals or {}) do
        if n >= 20 then break end
        if not helloed[name] and not ns.IsMe(name) then helloed[name] = true; n = n + 1; ns.Whisper(hello, name) end
    end
    -- crew channel roster (if the client gives it)
    local id = db.crew and GetChannelName(db.crew) or 0
    if id and id > 0 then
        local count = 0
        if GetNumChannelMembers then local ok, c = pcall(GetNumChannelMembers, id); if ok and c then count = c end end
        for i = 1, math.min(count, 40) do
            local nm
            if C_ChatInfo and C_ChatInfo.GetChannelRosterInfo then
                local ok, a = pcall(C_ChatInfo.GetChannelRosterInfo, id, i); if ok then nm = a end
            end
            if not nm and GetChannelRosterInfo then
                local ok, a = pcall(GetChannelRosterInfo, id, i); if ok then nm = a end
            end
            if nm and not secret(nm) and not ns.IsMe(nm) and not helloed[nm] then
                helloed[nm] = true; ns.Whisper(hello, nm)
            end
        end
    end
end

---------------------------------------------------------------------------
-- Receiving (called from Pals.lua; return true = handled)
---------------------------------------------------------------------------
function ns.MapMessage(p, name, chan)
    local kind = p[1]
    if kind ~= "P" and kind ~= "H" and kind ~= "h" then return false end
    -- the name the sender reported (sender names can arrive cut); routing stays on the sender name
    local full = (kind == "P" and p[10]) or ((kind == "H" or kind == "h") and p[3]) or nil
    -- our own messages come back on channels: never show ourselves
    if not name or ns.IsMe(name) or (full and full ~= "" and ns.IsMe(full))
        or (p[2] and p[2] == ns.TOKEN) or (p[9] and p[9] == ns.TOKEN) then return true end
    ns.NotePal(name, chan, full)
    local pal = pals[name]
    if kind == "H" then
        ns.Whisper("h~" .. ns.TOKEN .. "~" .. (ns.MyName and ns.MyName() or ""), name)
        C_Timer.After(1, function() SendPosition(true) end)
    elseif kind == "h" then
        C_Timer.After(1, function() SendPosition(true) end)
    else
        pal.map = tonumber(p[2]) or 0
        pal.x = (tonumber(p[3]) or 0) / 10000
        pal.y = (tonumber(p[4]) or 0) / 10000
        pal.level = tonumber(p[5])
        pal.class = p[6] ~= "" and p[6] or pal.class
        pal.dead = p[7] == "1"
        pal.zone = p[8]
        pal.layer = p[11] ~= "" and p[11] or nil
        pal.t = Now()
        diag.recv[name] = { t = pal.t, chan = chan }
        if ns.RefreshMap then ns.RefreshMap() end
    end
    return true
end

---------------------------------------------------------------------------
-- World map pins
---------------------------------------------------------------------------
local function Canvas()
    local W = WorldMapFrame
    if not W then return nil end
    if W.ScrollContainer and W.ScrollContainer.Child then return W.ScrollContainer.Child, W.ScrollContainer end
    return WorldMapDetailFrame or WorldMapButton
end

-- position of a pal on the map that is shown (projects zone <-> continent)
local function Project(pal, shown)
    if not pal.map or pal.map == 0 then return nil end
    if pal.map == shown then return pal.x, pal.y end
    if not (C_Map.GetWorldPosFromMapPos and C_Map.GetMapPosFromWorldPos and CreateVector2D) then return nil end
    local ok, cont, wpos = pcall(C_Map.GetWorldPosFromMapPos, pal.map, CreateVector2D(pal.x, pal.y))
    if not ok or not cont or not wpos then return nil end
    local ok2, _, mpos = pcall(C_Map.GetMapPosFromWorldPos, cont, wpos, shown)
    if not ok2 or not mpos then return nil end
    local x, y = mpos:GetXY()
    if not x or x < 0 or x > 1 or y < 0 or y > 1 then return nil end
    return x, y
end

local pins = {}
local P = 15                         -- badge size (UI units, before the zoom correction)
local function NewPin(parent)
    local f = CreateFrame("Frame", nil, parent)
    f:SetSize(P, P)
    -- small round badge: dark outline, class-colour ring, class icon
    f.pulse = ns.Img(f, "circlering", "BACKGROUND", -2)
    f.pulse:SetPoint("CENTER")
    f.pulse:SetBlendMode("ADD")
    f.outline = ns.Circle(f, "BACKGROUND", 0)
    f.outline:SetPoint("CENTER"); f.outline:SetSize(P + 3, P + 3)
    f.outline:SetVertexColor(0, 0, 0, 0.85)
    f.ring = ns.Circle(f, "BORDER", 0)
    f.ring:SetPoint("CENTER"); f.ring:SetSize(P, P)
    f.icon = f:CreateTexture(nil, "ARTWORK", nil, 0)
    f.icon:SetPoint("CENTER")
    f.icon:SetSize(P - 3, P - 3)
    f.mask = f:CreateMaskTexture()
    f.mask:SetTexture("Interface\\CharacterFrame\\TempPortraitAlphaMask", "CLAMPTOBLACKADDITIVE", "CLAMPTOBLACKADDITIVE")
    f.mask:SetAllPoints(f.icon)
    f.icon:AddMaskTexture(f.mask)
    -- small name to the right, no plate
    f.name = f:CreateFontString(nil, "OVERLAY")
    ns.SetFontSafe(f.name, ns.FONT_BODY_BOLD, 9)
    f.name:SetPoint("LEFT", f, "RIGHT", 3, 0)
    f.name:SetShadowColor(0, 0, 0, 1); f.name:SetShadowOffset(1, -1)
    f:EnableMouse(true)
    f:SetScript("OnEnter", function(self)
        local p = pals[self.who]
        if not p then return end
        local r, g, b = ClassColor(p.class)
        ns.Tooltip:SetOwner(self, "ANCHOR_RIGHT")
        ns.Tooltip:AddLine(ns.Nick(p.display or self.who), r, g, b)
        local cls = p.class and LOCALIZED_CLASS_NAMES_MALE and LOCALIZED_CLASS_NAMES_MALE[p.class] or p.class or ""
        ns.Tooltip:AddLine(format("%s. szintű %s", tostring(p.level or "?"), cls), 0.92, 0.88, 0.80)
        local where = (p.zone and p.zone ~= "") and p.zone or "ismeretlen vidék"
        if p.x and p.x > 0 then where = format("%s  |cff8c8070%.1f, %.1f|r", where, p.x * 100, p.y * 100) end
        ns.Tooltip:AddLine(where, 1, 0.82, 0.45)
        local lt, lr, lg, lb = LayerText(p.layer, ns.MyLayer())
        ns.Tooltip:AddLine("Layer: " .. lt, lr, lg, lb)
        if p.dead then ns.Tooltip:AddLine("Elesett - szellemként bolyong", 1, 0.40, 0.35) end
        local age = Now() - (p.t or 0)
        local txt, sr, sg, sb = Signal(age)
        ns.Tooltip:AddLine(" ")
        ns.Tooltip:AddLine(Dot(sr, sg, sb) .. " " .. txt .. "  |cff8c8c8c-  " .. Ago(age) .. "|r", sr, sg, sb)
        ns.ShowTooltip()
    end)
    f:SetScript("OnLeave", function() ns.Tooltip:Hide() end)
    return f
end

local function Refresh()
    local db = ns.DB()
    local parent, scroll = Canvas()
    for _, pin in ipairs(pins) do pin:Hide() end
    if not db or not db.map or not parent or not WorldMapFrame:IsShown() then return end
    local shown = WorldMapFrame.GetMapID and WorldMapFrame:GetMapID()
    if not shown then return end
    local w, h = parent:GetWidth(), parent:GetHeight()
    if not w or w == 0 then return end
    -- keep the pins the same size on screen while zooming
    local s = 1
    if scroll and scroll.GetCanvasScale then s = 1 / (scroll:GetCanvasScale() or 1) end
    local now, i = Now(), 0
    for name, p in pairs(pals) do
        local age = now - (p.t or 0)
        if p.t and age > GONE then
            p.map = nil
        else
            local x, y = Project(p, shown)
            if x then
                i = i + 1
                local pin = pins[i] or NewPin(parent)
                pins[i] = pin
                pin:SetParent(parent)
                pin:SetFrameLevel(parent:GetFrameLevel() + 2000)
                pin:SetScale(s)
                pin:ClearAllPoints()
                pin:SetPoint("CENTER", parent, "TOPLEFT", x * w / s, -y * h / s)
                pin.who = name
                local r, g, b = ClassColor(p.class)
                -- plain class-coloured dot (the old class-icon sheet is not reliable on this client)
                pin.icon:SetTexture(ns.TEX("circle"))
                pin.icon:SetTexCoord(0, 1, 0, 1)
                pin.icon:SetDesaturated(false)
                if p.dead then pin.icon:SetVertexColor(0.35, 0.05, 0.04, 1)
                else pin.icon:SetVertexColor(r * 0.45, g * 0.45, b * 0.45, 1) end
                pin.ring:SetVertexColor(r, g, b, 1)
                if not db.mapNames then pin.name:SetText("")   -- default: name only in the tooltip
                elseif p.dead then pin.name:SetText("|TInterface\\TargetingFrame\\UI-RaidTargetingIcon_8:10:10|t" .. ns.Nick(p.display or name))
                else pin.name:SetText(ns.Nick(p.display or name)) end
                pin.name:SetTextColor(r, g, b)
                pin.live = age < 15 and not p.dead
                pin.pr, pin.pg, pin.pb = r, g, b
                if not pin.live then pin.pulse:Hide() end
                pin:SetAlpha(age > STALE and 0.5 or 1)
                pin:Show()
            end
        end
    end
end
ns.RefreshMap = function() if WorldMapFrame and WorldMapFrame:IsShown() then Refresh() end end

-- while the map is open: follow zooming / map changes
local watcher = CreateFrame("Frame")
local acc = 0
watcher:SetScript("OnUpdate", function(_, el)
    acc = acc + el
    if acc < 0.25 then return end
    acc = 0
    if WorldMapFrame and WorldMapFrame:IsShown() then pcall(Refresh) end
end)
-- soft "sonar" ring around the pals with a live signal
local pulser = CreateFrame("Frame")
pulser:SetScript("OnUpdate", function()
    if not (WorldMapFrame and WorldMapFrame:IsShown()) then return end
    local ph = (GetTime() % 2.4) / 2.4
    for _, pin in ipairs(pins) do
        if pin:IsShown() and pin.live then
            local sz = P * (1.1 + 1.2 * ph)
            pin.pulse:SetSize(sz, sz)
            pin.pulse:SetVertexColor(pin.pr, pin.pg, pin.pb, 0.55 * (1 - ph))
            pin.pulse:Show()
        end
    end
end)

---------------------------------------------------------------------------
-- Timers, events, slash
---------------------------------------------------------------------------
local ev = CreateFrame("Frame")
do
    local lf = CreateFrame("Frame")
    local acc, lastCont = 0, nil
    lf:SetScript("OnUpdate", function(_, el)
        acc = acc + el
        if acc < 2 then return end
        acc = 0
        -- a new continent means a new layer: forget the old one
        if C_Map and C_Map.GetBestMapForUnit then
            local ok, m = pcall(C_Map.GetBestMapForUnit, "player")
            local cont = ok and m and not secret(m) and C_Map.GetMapInfo and C_Map.GetMapInfo(m)
            while cont and cont.mapType and Enum and Enum.UIMapType and cont.mapType > Enum.UIMapType.Continent and cont.parentMapID do
                cont = C_Map.GetMapInfo(cont.parentMapID)
            end
            local cid = cont and cont.mapID
            if cid and lastCont and cid ~= lastCont then myLayer.id = nil end
            lastCont = cid or lastCont
        end
        pcall(ScanLayer)
    end)
end

-- joining a guild mid-session: hidden hello + position over GUILD right away (no /reload needed).
-- known: the login baseline is taken (events before it are ignored, so login / reload is never a join)
-- armed: a PLAYER_GUILD_UPDATE came since then (a guild that only finished loading is not a join)
-- pending: a re-check is scheduled (IsInGuild() can stay false for a moment after accepting)
local guildJoin = { known = false, inGuild = false, pending = false, armed = false }

local function OnGuildJoined()
    local db = ns.DB()
    if not db or not db.enabled then return end
    if not db.guild then
        ns.Print("beléptél egy guildbe, de a guildnek küldés ki van kapcsolva. Bekapcsolás: /kodo guild")
        return
    end
    ns.Print("beléptél egy guildbe: a hírek és a helyed mostantól a guilden át is mennek.")
    if db.share then
        ns.RawSend("H~" .. ns.TOKEN .. "~" .. (ns.MyName and ns.MyName() or ""), "GUILD")
        SendPosition(true)
    end
end

local function RequestGuildRoster()
    if C_GuildInfo and C_GuildInfo.GuildRoster then pcall(C_GuildInfo.GuildRoster)
    elseif GuildRoster then pcall(GuildRoster) end
end

local function CheckGuild(e)
    if not guildJoin.known then return end
    if e == "PLAYER_GUILD_UPDATE" then guildJoin.armed = true end
    if IsInGuild() then
        if not guildJoin.inGuild and guildJoin.armed then
            guildJoin.inGuild, guildJoin.armed = true, false
            OnGuildJoined()
        end
    elseif e == "PLAYER_GUILD_UPDATE" then
        -- maybe not up to date yet: ask for the roster and look again once
        RequestGuildRoster()
        if not guildJoin.pending then
            guildJoin.pending = true
            C_Timer.After(2, function()
                guildJoin.pending = false
                pcall(CheckGuild, "RECHECK")
            end)
        end
    else
        guildJoin.inGuild = false   -- confirmed out: a later join reacts again (nothing printed)
    end
end

for _, e in ipairs({ "PLAYER_LOGIN", "ZONE_CHANGED_NEW_AREA", "PLAYER_DEAD", "PLAYER_UNGHOST", "PLAYER_ALIVE",
                     "FRIENDLIST_UPDATE", "PLAYER_GUILD_UPDATE", "GUILD_ROSTER_UPDATE" }) do
    pcall(ev.RegisterEvent, ev, e)
end
ev:SetScript("OnEvent", function(_, e)
    if e == "PLAYER_LOGIN" then
        if C_FriendList and C_FriendList.ShowFriends then pcall(C_FriendList.ShowFriends) end
        C_Timer.After(8, function()
            guildJoin.inGuild = IsInGuild() and true or false
            guildJoin.known, guildJoin.armed = true, false
            pcall(Hello); pcall(HelloKnown); pcall(SendPosition, true)
        end)
        C_Timer.NewTicker(60, function() pcall(HelloKnown) end)
        C_Timer.NewTicker(SEND_EVERY, function() pcall(SendPosition) end)
    elseif e == "FRIENDLIST_UPDATE" then
        -- a friend came online: ask them too (only once per session)
        C_Timer.After(2, function() pcall(Hello) end)
    elseif e == "PLAYER_GUILD_UPDATE" or e == "GUILD_ROSTER_UPDATE" then
        pcall(CheckGuild, e)
    else
        C_Timer.After(1, function() pcall(SendPosition, true) end)
    end
end)

function ns.MapSlash(cmd, arg)
    local db = ns.DB()
    if cmd == "map" or cmd == "terkep" or cmd == "térkép" then
        db.map = not db.map
        ns.Print("haverok a térképen: " .. (db.map and "be" or "ki"))
        ns.RefreshMap()
        return true
    elseif cmd == "nevek" or cmd == "names" then
        db.mapNames = not db.mapNames
        ns.Print("nevek a térképen: " .. (db.mapNames and "be" or "ki (egér rá: tooltip)"))
        ns.RefreshMap()
        return true
    elseif cmd == "share" or cmd == "megoszt" then
        db.share = not db.share
        ns.Print("a helyed megosztása: " .. (db.share and "be" or "ki - a többiek nem látnak a térképen"))
        if db.share then SendPosition(true) end
        return true
    elseif cmd == "diag" then
        local now = Now()
        local mp = MyPosition and { MyPosition() } or {}
        ns.Print("|cffffcc00diagnosztika|r")
        print(format("   név: %s  ·  megosztás: %s  ·  térkép: %s  ·  be: %s", ns.MyName and ns.MyName() or "?",
            db.share and "be" or "KI", db.map and "be" or "KI", db.enabled and "be" or "KI"))
        local id = db.crew and GetChannelName(db.crew) or 0
        print(format("   crew: %s  ·  csatorna-szám: %s", tostring(db.crew), tostring(id)))
        print(format("   guild: %s  ·  csapat: %s", IsInGuild() and "igen" or "nem", IsInGroup() and "igen" or "nem"))
        print("   layer: " .. (ns.MyLayer() or "ismeretlen (targetelj / nézz meg egy NPC-t)"))
        print(format("   saját hely most: %s", mp[1] == nil and "TITKOS/nincs (harc?)" or format("map %s  %.1f, %.1f", tostring(mp[1]), (mp[2] or 0) * 100, (mp[3] or 0) * 100)))
        print(format("   elküldött helyek: %d db, utoljára %s", diag.sent, diag.lastSent > 0 and (floor(now - diag.lastSent) .. " mp-e") or "SOHA"))
        local any = false
        for n, r in pairs(diag.recv) do
            any = true
            print(format("   jött hely tőle: %s  via %s  (%d mp-e)", n, tostring(r.chan), floor(now - r.t)))
        end
        if not any then print("   jött hely: |cffff5544senkitől|r") end
        return true
    elseif cmd == "hol" or cmd == "where" then
        local now, any = Now(), false
        for name, p in pairs(pals) do
            if p.t and now - p.t < GONE then
                any = true
                local r, g, b = ClassColor(p.class)
                local where = p.zone ~= "" and p.zone or "?"
                if p.map and p.map > 0 and p.x > 0 then where = format("%s (%.1f, %.1f)", where, p.x * 100, p.y * 100) end
                local txt, sr, sg, sb = Signal(now - p.t)
                local lt, lr, lg, lb = LayerText(p.layer, ns.MyLayer())
                where = where .. format("  |cff%02x%02x%02xlayer: %s|r", lr * 255, lg * 255, lb * 255, lt)
                print(format("   %s |cff%02x%02x%02x%s|r  %s. szint  -  %s%s  |cff888888(%s: %s)|r", Dot(sr, sg, sb),
                    r * 255, g * 255, b * 255, ns.Nick(p.display or name), tostring(p.level or "?"), where,
                    p.dead and "  |cffff5544elesett|r" or "", txt:lower(), Ago(now - p.t)))
            end
        end
        if not any then ns.Print("most senkit nem látok - nincs fent haver az addonnal, vagy még nem jött üzenet.") end
        return true
    end
    return false
end
