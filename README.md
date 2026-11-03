# Kodo Times

**Kodo Times** (korábbi nevén Moteve Pals) egy közösségi World of Warcraft addon a WoW Forever klienshez. Vicces, díszes felugró híreket mutat a haverok szintlépéseiről, halálairól, szakma-mérföldköveiről és értékes tárgyairól, valamint megjeleníti az addont használó társakat a világtérképen.

**Aktuális verzió: 0.10.0**

[Legfrissebb addon letöltése (ZIP)](downloads/KodoTimes.zip?raw=true)

A `downloads` mappában csak a legfrissebb telepíthető `KodoTimes.zip` szerepel. Frissítéskor ugyanaz a letöltési link használható. A 0.10.0-s átnevezéssel a link is új lett: a régi `downloads/MotevePals.zip` már nem létezik.

## Telepítés és első indítás

1. Töltsd le és csomagold ki a fenti ZIP-et.
2. Másold a ZIP-ben lévő **mindkét** mappát (`KodoTimes` és `MotevePals`) a játék `Interface/AddOns/` könyvtárába.
3. A karakterválasztón engedélyezd a **Kodo Times** addont (és hagyd bekapcsolva a „Kodo Times – régi beállítások” bejegyzést is), majd lépj be.
4. A beállításokat a `/kodo opciok` paranccsal nyithatod meg. Egyedül a `/kodo test` paranccsal próbálhatod ki a felugró híreket. A régi `/kodo` és `/pals` parancs is működik.

```text
Interface/
└── AddOns/
    ├── KodoTimes/
    │   ├── KodoTimes.toc
    │   ├── Pals.lua
    │   ├── Map.lua
    │   ├── Fonts/
    │   └── Textures/
    └── MotevePals/          (kis híd: a régi beállítások átviteléhez)
        ├── MotevePals.toc
        └── MotevePals.lua
```

A mappaneveket tartsd meg: a `KodoTimes.toc` közvetlenül a `KodoTimes` mappában legyen. Ha egy új addon még nem jelenik meg a listában, indítsd újra a klienst. Meglévő addon frissítése után `/reload` használható, kivéve ha a frissítés új textúrafájlokat hoz (pl. 0.9.29): ilyenkor a klienst teljesen újra kell indítani, különben az új képek nem töltődnek be. A `WTF` könyvtárat tartsd meg, mert abban vannak a mentett beállítások.

### Frissítés a Moteve Pals-ról (0.9.x → 0.10.0)

Az addon új neve **Kodo Times**, a mappája `KodoTimes`. A beállítások (hangerő, a felugró ablak helye és mérete, a kapcsolók, a crew, az „üdvözölve” jelzés) maguktól átjönnek, ha így frissítesz:

1. Csomagold ki a **teljes** `KodoTimes.zip`-et a régi telepítés fölé az `Interface/AddOns/` könyvtárba, felülírva a meglévő fájlokat. A régi `MotevePals` mappát **ne töröld előtte**.
2. Lépj ki teljesen a játékból, és indítsd újra a klienst (a `/reload` nem elég, mert új addonmappa jött).
3. Belépéskor minden karakter egyszer átmásolja a régi beállításait az új mentésbe (`KodoTimesDB`, karakterenként `KodoTimesChar`). A régi mentést az addon csak olvassa, nem írja.

A `MotevePals` mappában ezután csak egy kis híd marad („Kodo Times – régi beállítások”): semmit nem futtat, csak betölti a régi mentést, hogy az új addon átvehesse. A régi `Pals.lua` és a többi régi fájl a mappában maradhat, már nem töltődnek be. **Ajánlott megtartani.** Akkor törölhető, ha az első belépés után már minden karaktereddel beléptél egyszer a 0.10.0-val: ha korábban törlöd, a még be nem lépett karaktereknél újra feljön az üdvözlőablak, és a crewból kilépett alt karakterek újra belépnek.

Ha csak a `KodoTimes` mappát másolod be, és a régi, teljes addon is a helyén marad, a Kodo Times nem csinál semmit (különben minden hír kétszer jelenne meg), csak egy figyelmeztetést ír a chatbe: ilyenkor csomagold ki a teljes ZIP-et a régi fölé, és indítsd újra a klienst. A régi (0.9.x) és az új verziót használó haverok továbbra is látják egymás híreit és térképes helyét.

## Milyen hírek jelennek meg?

| Esemény | Megjelenítés |
| --- | --- |
| Szintlépés | Csak 5 szintenként (5, 10, 15 … 55) és 60-nál; külön szövegek kerek szinteknél és 60-nál |
| Halál | Halálhír, zóna és az elérhető támadóadatok |
| Szakma-mérföldkő | Szakmapontok, szakmaikonnal; fegyverskillek nélkül |
| Kék / epic craft | Elkészített tárgy, tárgyikonnal |
| Epic loot | Megszerzett tárgy, tárgyikonnal |

A hírek véletlenszerű humoros szövegeket kapnak, és ugyanaz a sor nem ismétlődik közvetlenül egymás után. Halálnál kaszthoz kötött „legendák” beszólásai is megjelenhetnek. A szövegek a [Lines.lua](KodoTimes/Lines.lua) fájlban bővíthetők; a kasztlegendák játékbeli paranccsal is beállíthatók.

## Felugró hírek kezelése

Az értesítések díszes fantasy keretet, hírtípusonként saját hátteret, bal oldali ikont és jobb oldali medált használnak. Alapból körülbelül **6,5 másodpercig** maradnak láthatók. Az egérmutatót rajtuk tartva nem tűnnek el.

- A felugró hír az **X** gombbal bezárható.
- Jobb kattintás vagy Shift + X a sorban várakozó híreket is eldobja.
- Alapból a képernyő bal szélén, a chat fölött jelenik meg, kisebb (0,67×) méretben.
- A `/kodo move` paranccsal mozgatható, és közben a jobb alsó sarkánál fogva vagy egérgörgővel arányosan átméretezhető (0,5–2×; jobb kattintás a sarokra = 1,0× méret); újra kiadva vagy a beállítások bezárásával befejezhető a mozgatás. A méret és a hely mentődik.
- A láthatósági idő **1–60 másodperc** között állítható, például `/kodo time 8`.
- A játék saját hangeffektjei, a chatbe kiírás és a saját hírek megjelenítése külön kapcsolhatók.
- A chatbe írt `[Kodo Times]` hírekben a karakter neve kattintható: bal kattintásra suttogást nyit neki, mint a játék saját névlinkjei.
- Az addon saját hangjainak hangereje **0–100%** között állítható (a beállítópanelen vagy például `/kodo volume 50`); 0% néma, 100% az eddigi hangerő, a játék többi hangja nem változik.

## Haverok elérése

**Minden résztvevőnél fusson az addon**, aki híreket vagy helyzetadatokat szeretne küldeni és látni. Az addon guild-, csapat- és barátlistás kapcsolatokat, valamint a korábban megismert társaknak küldött addon-suttogásokat használ.

Az első indítás üdvözlőablaka segít csatlakozni a közös haveri csatornához. Saját közös csatorna a `/kodo crew <név>` paranccsal választható; mindenkinél ugyanazt a nevet kell megadni. Az egyéni csatornán a szerver nem feltétlenül továbbítja az addonüzeneteket, ezért a megismert társak közvetlen addon-suttogással is elérhetők.

Kapcsolatellenőrzéshez `/kodo ping <név>`, részletes állapothoz `/kodo diag` használható. Harc közben a hírek várakozhatnak, és harc után mennek ki. Raidben, battlegroundon és arénában a hírek küldése alapból ki van kapcsolva; a `/kodo raidhir` paranccsal állítható.

## Térképes helyzetjelzés

A térképes és beállítási tooltipek, valamint a beállítások feliratai magyar ékezeteket (ő/ű) is tartalmazó Barlow betűtípust használnak.

A világtérképen a társakat kis, kasztszínű pontok jelzik. Rámutatáskor név, szint, zóna, elérhető koordináták és a jel állapota látható. A nevek állandó megjelenítése külön kapcsolható.

- Mozgáskor körülbelül 5 másodpercenként, álló helyzetben ritkábban küld helyzetet.
- A régi jel halványul, majd körülbelül 5 perc után eltűnik.
- Instance-ben csak a zónaadat továbbítható.
- A layerjelzés a környező NPC-k azonosítóiból következtet; pontossága az elérhető adatoktól függ.
- A térképes jelölők és a saját hely megosztása egymástól függetlenül kapcsolhatók.

## Beállítások és parancsok

A beállítópanel a **Beállítások → Kiegészítők → Kodo Times** oldalon vagy a `/kodo opciok` paranccsal érhető el. Két oszlopban tartalmazza a hír-, küldési, térképes és grafikai kapcsolókat.

| Parancs | Művelet |
| --- | --- |
| `/kodo` | Állapot és súgó (a régi `/mpal` és `/pals` is működik) |
| `/kodo opciok` | Beállítások |
| `/kodo test` | Helyi mintahírek |
| `/kodo move` | Felugró ablak mozgatása és méretezése (sarok / görgő) |
| `/kodo time 8` | Megjelenítési idő: 8 másodperc |
| `/kodo sound` | Hang kapcsolása |
| `/kodo volume 50` / `/kodo hangero 50` | Az addon hangjainak hangereje: 50% |
| `/kodo chat` | Chatbe kiírás kapcsolása (a névre kattintva suttogás) |
| `/kodo self` | Saját hírek megjelenítésének kapcsolása |
| `/kodo guild` / `/kodo group` / `/kodo friends` | Küldés kapcsolása az adott kapcsolatok felé |
| `/kodo crew <név>` | Közös csatorna kiválasztása; név nélkül kikapcsolás |
| `/kodo ping <név>` | Kapcsolat ellenőrzése egy társsal |
| `/kodo diag` | Kapcsolati és helyzetdiagnosztika |
| `/kodo debug` | Küldési és fogadási hibakereső kiírás kapcsolása |
| `/kodo hol` | Ismert társak helyzetének listája |
| `/kodo map` | Térképjelölők kapcsolása |
| `/kodo share` | Saját hely megosztásának kapcsolása |
| `/kodo nevek` | Térképes nevek kapcsolása |
| `/kodo raidhir` | Hírek küldése raidben / PvP-területeken |
| `/kodo welcome` | Üdvözlőablak megnyitása |
| `/kodo legend` | Kasztlegendák listázása |
| `/kodo legend <class> <név> <cím>` | Kasztlegenda beállítása |
| `/kodo on` / `/kodo off` | Addon be- és kikapcsolása |

### Grafikai kapcsolók

A `/kodo weed` a sűrűbb, távolabb látszó növényzetet kapcsolja (`groundEffectDensity 256`, `groundEffectFade 370`, `groundEffectDist 500`). A `/kodo feny` a „Jó fények” profilt kapcsolja (`Contrast 80`, `Brightness 49`, `Gamma 1.2`). Kikapcsoláskor a kliens alapértékeit, illetve ha azok nem kérdezhetők le, a korábban eltárolt értékeket használja.

## Kompatibilitás és ellenőrzés

A célkliens **WoW Forever**, a TOC Interface-értéke **16001**. A mentések neve `KodoTimesDB` és karakterenként `KodoTimesChar` (a 0.9.x-es `MotevePalsDB`/`MotevePalsChar` mentést a `MotevePals` híd tölti be, az addon egyszer átmásolja). A címek és a medálok a csomagban lévő Marcellus betűtípust használják, mert a játék Morpheus betűjéből hiányzik az Ő/Ű.

A csomag a fenti aktuális verzió forrásából készül. Feltöltés előtt a fájlok azonosságát, a Lua-szintaxist és a ZIP tartalmát ellenőriztük. Az élő játékbeli működést és a játékosok közötti üzenetküldést a feltöltéskor nem teszteltük újra. A kliens és a szerver korlátozásai befolyásolhatják az üzenetek és helyzetadatok kézbesítését.

## Hibajelentés és források

Hibát az [Issues oldalon](https://github.com/zolesz05/PalsAddon/issues) jelezhetsz. Add meg a kliens és az addon verzióját, a reprodukálás lépéseit és az érintett hír- vagy térképfunkciót. Kapcsolati hibánál a `/kodo diag` kimenete segíthet.

A teljes addon a [KodoTimes](KodoTimes/) mappában, a régi beállításokat átadó híd a [MotevePals](MotevePals/) mappában található. A [részletes leírás és változásnapló](KodoTimes/README.txt) a korábbi változásokat is felsorolja. A Marcellus és Barlow betűtípusok SIL Open Font License fájljai a `KodoTimes/Fonts/` mappában szerepelnek.

## Csomag frissítése

A repository gyökeréből:

```sh
python tools/package_addon.py
```

Az addon hangerő-kezelését (mentés, 0/100%, a kölcsönvett hangcsatorna visszaállítása, `/kodo volume`, beállítópanel) Lua 5.1-ben, a WoW API csonkjaival futtatva ellenőrzi:

```sh
uv run --with lupa python tools/check_volume.py
```

A chatbe írt hírek névlinkjét (suttogási cél, más realmről érkezőnél a realm is, a felugró szöveg változatlan) így ellenőrzi:

```sh
uv run --with lupa python tools/check_chatlink.py
```

Az első indításkor felugró üdvözlő ablak szövegeit, a cím és a leírás betűméretének kicsinyítését (hogy kiférjen a sávba) és a gombok változatlan működését így ellenőrzi:

```sh
uv run --with lupa python tools/check_welcome.py
```

Az átnevezés utáni egyszeri beállítás-átvitelt (régi mentés → új, a régi érintetlen marad, friss telepítésnél alapértékek és üdvözlőablak, régi addon mellett csendes mód), a megtartott `MOTEVEPAL` üzenetelőtagot és a `/kodo` parancsot így ellenőrzi:

```sh
uv run --with lupa python tools/check_migration.py
```

A betűtípusok ő/ű/Ő/Ű karaktereit (és hogy egy Lua-fájl se használja a Morpheust), illetve a régi nevek eltűnését így:

```sh
python tools/check_fonts.py
python tools/check_rename.py
```

A csomagoló ellenőrzi mindkét TOC bejegyzéseit és a ZIP tartalmát, a `KodoTimes` és a `MotevePals` mappát együtt a `downloads/KodoTimes.zip` fájlba teszi, és eltávolítja ebből a mappából a korábbi verziószámos és a régi nevű (`MotevePals*.zip`) addoncsomagokat. A forrást, a ZIP-et és a README-t együtt kell feltölteni.
