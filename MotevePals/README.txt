Moteve Pals 0.9.35 - WoW Forever (Interface 16001)
Vicces felugró hírek a haverokról. Mindenkinek fel kell raknia, aki látni / küldeni akar.

TELEPÍTÉS
  A "MotevePals" mappát másold az Interface\AddOns mappába, majd /reload.
  Kipróbálás egyedül: /mpal test

HOGY NÉZ KI
  Díszes WoW-szalag hírtípusonként saját háttérrel (zászló, táj, medál): balra a szereplő
  class-portréja aranygyűrűben (halálnál vöröses-szürke; craftnál/lootnál az item ikonja),
  középen "AZEROTH BULVÁR - RENDKÍVÜLI KIADÁS", a színes címsor és a beszólás, jobbra a
  lüktető medál (szint, RIP, skillpont, KÉK, EPIC, LOOT). Felülről esik be, kb. 6,5 mp-ig látszik.
  A hátterek a Textures\toast_*.tga fájlok (a megadott terv alapján).

MIRŐL SZÓL
  - Szintlépés, csak 5 szintenként (5, 10, 15 ... 55) és 60-nál (kerek szintnél és 60-nál külön szövegek)
  - Halál (melyik zónában)
  - Szakma-mérföldkő: 50, 75, 100, 125 ... pontnál (csak szakmák, a fegyverskillek nem)
  - Kék vagy epic craft ("You create: ...")
  - Epic loot
  Minden eseményhez sok szöveg van, véletlenszerűen választ (kétszer egymás után nem ugyanazt).
  A szövegek a Lines.lua fájlban vannak: bátran írjátok át / bővítsétek.

CLASS-LEGENDÁK
  Halálnál nagyjából minden második alkalommal a halott classának "legendája" is beszól, pl.
  "SADISS, a paladinok istene büszke lenne rád." vagy "Chainsaw, a shamanok királya ...".
  Beállítva: Paladin = SADISS (a paladinok istene), Shaman = Chainsaw (a shamanok királya).
  Továbbiak a játékban:  /mpal legend warrior Grommash a warriorok atyja
  Lista:                 /mpal legend
  (Vagy a Lines.lua-ban a LEGENDS részben. Mindenkinél a saját beállítása számít.)

KIK KAPJÁK MEG
  A hír rejtett addon-üzenetként megy: a guildnek, a csapatnak / raidnek, és a barátlistádon lévő
  online játékosoknak. Ha a haverok se egy guildben, se egy csapatban nincsenek:
     /mpal crew valami     (mindenki ugyanazt a nevet írja be) -> közös rejtett csatorna.
  Csak az látja, akinek fent van az addon.

PARANCSOK (/mpal)
  /mpal                 állapot és súgó
  /mpal test            minta-hírek
  /mpal crew <név>      közös csatorna a haveroknak  (/mpal crew  üresen = kilépés)
  /mpal move            a felugró ablak mozgatása, a sarkánál (vagy görgővel) méretezés (újra /mpal move vagy a beállítások bezárása = kész)
  /mpal legend <class> <név> <cím>   class-legenda beállítása halálhírekhez
  /mpal sound           hang ki / be
  /mpal volume <0-100>  az addon saját hangjainak hangereje százalékban (alias: /mpal hangero)
  /mpal chat            a hírek a chatbe is ki / be
  /mpal self            a saját híreid is felugranak ki / be
  /mpal guild | group | friends   küldés ki / be az adott helyre
  /mpal on | off        az egész ki / be

TUDNIVALÓK
  - Dungeonban / raidben harc közben a játék korlátozhatja az addon-üzeneteket; ilyenkor a hír
    elmaradhat (pl. halálnál), harcon kívül minden megy.
  - Betűtípusok: Marcellus és Barlow (SIL Open Font License).

0.4.1: a felugró hír bezárható (X a jobb felső sarokban / bal klikk; jobb klikk vagy Shift+X a sorban állókat is eldobja),
       amíg rajta az egér, nem tűnik el, és /mpal time <mp> paranccsal állítható, meddig marad kint (alap: 6,5 mp).

0.5.0: haverok a térképen. Aki fut az addon, 5 mp-enként (csak ha mozdult, különben 30 mp-enként) elküldi a helyét
       a guildnek / csapatnak / crew csatornának, a csak barátlistás haveroknak suttogva.
       A világtérképen class-ikonos, class-színű jelölő + név; zóna- és kontinenstérképen is. Egér rá: szint, zóna, frissítés.
       Halott haver: szürke-vörös ikon (RIP). 90 mp után halvány, 5 perc után eltűnik. Instance-ben csak a zóna megy át.
       /mpal hol   - lista: ki hol van
       /mpal map   - jelölők ki/be      /mpal share - a saját helyed megosztása ki/be

0.5.1: kapcsolat-teszt. /mpal ping (minden csatornán) vagy /mpal ping <név> (közvetlenül neki) - a másik
       automatikusan válaszol (PONG), így azonnal kiderül, eljut-e az üzenet. /mpal debug: minden küldés/fogadás a chatbe.
       A crew csatornába lépést ellenőrzi és jelzi, ha nem sikerült. Belépéskor szól, ha semmin át nem éred el a többieket.

0.6.0: a saját híreid már csak a haverok kapják meg (nálad: /mpal self). Magadat nem látod a térképen.
       Új térképjelölő: arany jelölőtű class-színű kerettel, névtábla, élő jelnél "sonar" pulzálás.
       Tooltip: szint + class, zóna + koordináta, jel állapota (Élő jel / Utolsó jel / A jel megszakadt).
       Első indításkor "Kezdődjön a kaland!" ablak: egy kattintással beléptet a haverok csatornájába (MPhaverok),
       utána minden indításkor magától belép. Újra elővehető: /mpal welcome

0.7.0: új felugró design: sötét, egyszínű tábla típusonként színezett fém kerettel, bal oldalt portré-gyűrű,
       jobb oldalt iránytű-medál (craft/loot: drágakő + felirat). Nagyobb, jobban olvasható betűk, a szöveg
       mögött nincs tájkép, így nem vész bele a háttérbe.

0.7.1: a bannerek kerete, medálja és portré-gyűrűje most egy az egyben a minta-designból jön (díszes fém keret,
       sarok-tüskék, iránytű-medál, drágakő a craft/loot medálban), a szöveg továbbra is sötét, nyugodt háttéren.

0.8.0: design a második minta alapján: bal oldalt Horda-zászló rúddal, díszes keret, portré-gyűrű,
       iránytű-medál. A szöveg nagyobb sötét mezőn, hosszabb sornál automatikusan kisebb betűvel (3 sorig).

0.8.1: a visszajelzés alapján átírt szövegek (törlések, cserék, új sorok), új címek: DONG!, RIP BALFASZ, EPIC LOOT.
0.8.2: új első-indítás ablak: "ÜDV A FASZOS KLÁNBAN!", Let's go! / Kösz, nem gombok, szellősebb elrendezés.

0.9.0: voice-over. Minden felugró hírnél és az üdvözlő ablaknál a Sounds mappából szól egy hang:
       welcome, levelup, levelround, level60, death (a legendás halálnál is), skill, craftblue, craftepic, epicloot (.ogg).
       Saját felvételre bármikor cserélhető (ugyanazzal a névvel), de új/cserélt hangfájl után a játékot
       TELJESEN újra kell indítani (a /reload nem elég). Ki/be: /mpal voice  (a /mpal sound mindent néma).

0.9.1: kisebb térképjelölő: kis kerek class-ikon class-színű kerettel, mellette kis név (nincs tű és névtábla).
       /mpal nevek - a nevek ki/be a térképen (egér rá: tooltip).
0.9.2: a térképen alapból csak a pöttyök látszanak, név és minden infó egérrel rámutatva. /mpal nevek: nevek kiírva.
0.9.3: raidben, battlegroundon és arénában nem küld hírt (dungeonban igen). /mpal raidhir: ott is küldjön.
0.9.4: halálhírnél a bal oldali körben koponya van a class-ikon helyett.
0.9.5: a halálhír koponyája a játék saját koponya-ikonja (INV_Misc_Bone_HumanSkull_01), enyhén vöröses tónussal.
0.9.6: voice-over kivéve (Sounds mappa törölve), marad a sima játékhang (/mpal sound).
0.9.7: saját ikon minden hírtípusnak (class-ikon helyett), szakmánál a szakma ikonja, craft/lootnál az item.
       Halálnál a hír végén: "Tettes: <mob> (szint)" - az a mob, amelyik épp téged ütött/targetelt.
       Térkép: class-színű pötty (a régi class-ikon lap ezen a kliensen hibás képet adott).
0.9.8: saját hangeffekt minden hírtípushoz (Sounds mappa): fanfár, gong, szomorú harsona stb. Ki/be: /mpal sound.
       Új hangfájlok után a játékot teljesen újra kell indítani.
0.9.9: saját hangeffektek kivéve (Sounds mappa törölve), helyettük a WoW saját hangjai típusonként:
       halál = a régi raid warning, szintlépés = WoW level up, kerek/60 = level up + ready check / BG-dob,
       szakma/craft = quest complete, epic loot = érme + quest complete, üdvözlés = BG-dob.
0.9.10: egyszerűbb hangok: szinteknél WoW level up, minden másnál quest complete, halálnál marad a raid warning.
0.9.11: a kétrészes karakternevekből a második részt írja ki (hírek, térkép, /mpal hol).
0.9.12: a saját név a teljes kétrészes névből jön (a kliens UnitName-je csak az első részt adta: "Miss").
0.9.13: az üdvözlő ablak karakterenként jön fel (minden új karakternél egyszer); a csatornába csak az elfogadás után lép be.
0.9.14: a csatornába magától belép, ha a fiókon már egyszer elfogadtátok (új karakteren is), az üdvözlő ablak mellette feljön.
        Az üzenetekben a teljes név is utazik (a kliens a hosszú neveket levágva adja át), a suttogás ezzel megy.
        Akivel pingeltetek, annak suttogva is megy a pozíció. /mpal: kiírja, bent vagy-e a csatornában.
0.9.15: /mpal diag - kapcsolat-diagnosztika (csatorna, saját hely, elküldött/kapott helyek).
0.9.16: a szerver az egyéni csatornán nem továbbítja az addon-üzeneteket, ezért a hely suttogásban megy:
        akit egyszer megismert (barátlista, ping, bármilyen üzenet), azt megjegyzi, és belépéskor magától megkeresi.
0.9.17: a hírek is mennek suttogásban azoknak a haveroknak, akiket pinggel/korábbról ismer. /mpal kuld: teszt-hír a többieknek.
0.9.18: harc közben (halál, szintlépés kill után) a hírek várakoznak, és a harc vége után mennek ki; sikertelen küldést 3x újrapróbál.
0.9.19: layer-infó: a környező NPC-k azonosítójából felismeri, melyik layeren vagy, és elküldi a többieknek.
        Térképes tooltipben és /mpal hol-ban: "Layer: ugyanazon, mint te" / "MÁS layer". /mpal diag: a saját layered.
0.9.20: saját oldal a Beállítások > Kiegészítők listában, minden ki/be kapcsolóval, hír-idővel és gyors gombokkal. /mpal opciok
0.9.21: MORE WEED! (Beállítások > Grafika vagy /mpal weed): groundEffectDensity 256, groundEffectFade 370, groundEffectDist 500; kikapcsolva alapérték.
0.9.22: "Jó fények" kapcsoló (Beállítások > Grafika vagy /mpal feny): Contrast 80, Brightness 49, Gamma 1.2; kikapcsolva alapérték.
0.9.23: a beállítások oldal két oszlopos, nem lóg ki a gombok alá.

0.9.24: magyar ő/ű javítása a térképes és beállítási tooltipekben, valamint a beállítások feliratain; saját Barlow betűtípus, a játék többi tooltipjének módosítása nélkül.
0.9.25: guildbe lépés után azonnal átáll a guildre (/reload nélkül): rejtett hello és hely-küldés a guildnek, és egy helyi üzenet a chatben.
0.9.26: a felugró ablak mozgatáskor át is méretezhető: jobb alsó sarkánál húzva vagy egérgörgővel arányosan (0,5-2x),
        jobb klikk a sarokra = eredeti méret; a méret a hellyel együtt mentődik. A beállításokból kikerült a haveroknak
        teszt-hírt küldő gomb, a gombok rendezve.
0.9.27: a beállítások bezárásakor (vagy másik oldalra váltáskor) a felugró ablak mozgatása is befejeződik; a hely és a méret megmarad.
0.9.28: belépés után a „Felugró ablak mozgatása” (és a /mpal move) már az első kattintásra megmutatja a felugró ablakot, hiba nélkül.
0.9.29: Alliance karakternél Alliance-zászlós bannerek; új textúrafájlok után a játékot teljesen újra kell indítani.
0.9.30: a felugró hír alapból a képernyő bal szélén, a chat fölött jelenik meg, kisebb méretben (0,67x). Akinél még soha
        nem volt mozgatva vagy átméretezve, egyszer odakerül; az elhúzott vagy átméretezett hely és méret megmarad.
0.9.31: új és átírt beszólások (szintlépés, 60-as szint, halál, szakma, epic loot); a 10., 20., 30., 40. és 50. szint
        saját sort is kapott, ami csak azon a szinten jöhet ki. Az új sorokat csak az látja, akinél már a 0.9.31 fut.
0.9.32: szintlépés-hír (a haveroknak és a saját értesítő is) csak 5 szintenként (5, 10, 15 ... 55) és 60-nál megy ki;
        a többi szintnél nincs hír. A régebbi verziójú haverok szintlépései továbbra is minden szintnél megjelennek.
0.9.33: 12 új halál-beszólás.
0.9.34: hangerő az addon saját hangjainak (Beállítások > Hírek > Hangerő csúszka, vagy /mpal volume <0-100>), mentve.
        0% = néma, 100% = olyan hangos, mint eddig; a játék többi hangja és a Master hangerő nem változik.
        A WoW-os hangnak nincs hangerő-paramétere, ezért 1-99%-nál a hang egy ritkán használt csatornán szól
        (Párbeszéd, ha az ki van kapcsolva: Környezet, végül Effektek), aminek a hangerejét kb. 4 mp-re átállítja,
        utána (és kilépéskor / /reload-kor) visszaállítja. Ezalatt a csatorna többi hangja is ezen a hangerőn szól.
        Ha a játék közben összeomlik, a csatorna hangereje a hang beállításokban állítható vissza.
0.9.35: 1-99%-nál az addon már soha nem állítja az Effektek csatorna hangerejét: azon szólnak a játék saját zsákmány-,
        szakma- és tárgykészítés-hangjai, amelyek a hírrel egy időben indulnak, és eddig halkabban kezdődtek,
        a végükön pedig felhangosodtak. Ha a Párbeszéd és a Környezet csatorna sem használható, az addon hangja a
        Masteren szól, teljes hangerőn (mint 100%-nál). A kölcsönvett csatorna hangereje most pontosan addig marad
        átállítva, amíg az addon hangja szól (halál kb. 2 mp, szintlépés kb. 5 mp, a többi kb. 9 mp), nem fix 4 mp-ig.
