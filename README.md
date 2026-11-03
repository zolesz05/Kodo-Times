# Moteve Pals

**Moteve Pals** egy közösségi World of Warcraft addon a WoW Forever klienshez. Vicces, díszes felugró híreket mutat a haverok szintlépéseiről, halálairól, szakma-mérföldköveiről és értékes tárgyairól, valamint megjeleníti az addont használó társakat a világtérképen.

**Aktuális verzió: 0.9.35**

[Legfrissebb addon letöltése (ZIP)](downloads/MotevePals.zip?raw=true)

A `downloads` mappában csak a legfrissebb telepíthető `MotevePals.zip` szerepel. Frissítéskor ugyanaz a letöltési link használható.

## Telepítés és első indítás

1. Töltsd le és csomagold ki a fenti ZIP-et.
2. Másold a `MotevePals` mappát a játék `Interface/AddOns/` könyvtárába.
3. A karakterválasztón engedélyezd a **Moteve Pals** addont, majd lépj be.
4. A beállításokat a `/mpal opciok` paranccsal nyithatod meg. Egyedül a `/mpal test` paranccsal próbálhatod ki a felugró híreket.

```text
Interface/
└── AddOns/
    └── MotevePals/
        ├── MotevePals.toc
        ├── Pals.lua
        ├── Map.lua
        ├── Fonts/
        └── Textures/
```

A mappanevet tartsd meg: a `MotevePals.toc` közvetlenül a `MotevePals` mappában legyen. Ha egy új addon még nem jelenik meg a listában, indítsd újra a klienst. Meglévő addon frissítése után `/reload` használható, kivéve ha a frissítés új textúrafájlokat hoz (pl. 0.9.29): ilyenkor a klienst teljesen újra kell indítani, különben az új képek nem töltődnek be. A `WTF` könyvtárat tartsd meg, mert abban vannak a mentett beállítások.

## Milyen hírek jelennek meg?

| Esemény | Megjelenítés |
| --- | --- |
| Szintlépés | Csak 5 szintenként (5, 10, 15 … 55) és 60-nál; külön szövegek kerek szinteknél és 60-nál |
| Halál | Halálhír, zóna és az elérhető támadóadatok |
| Szakma-mérföldkő | Szakmapontok, szakmaikonnal; fegyverskillek nélkül |
| Kék / epic craft | Elkészített tárgy, tárgyikonnal |
| Epic loot | Megszerzett tárgy, tárgyikonnal |

A hírek véletlenszerű humoros szövegeket kapnak, és ugyanaz a sor nem ismétlődik közvetlenül egymás után. Halálnál kaszthoz kötött „legendák” beszólásai is megjelenhetnek. A szövegek a [Lines.lua](MotevePals/Lines.lua) fájlban bővíthetők; a kasztlegendák játékbeli paranccsal is beállíthatók.

## Felugró hírek kezelése

Az értesítések díszes fantasy keretet, hírtípusonként saját hátteret, bal oldali ikont és jobb oldali medált használnak. Alapból körülbelül **6,5 másodpercig** maradnak láthatók. Az egérmutatót rajtuk tartva nem tűnnek el.

- A felugró hír az **X** gombbal bezárható.
- Jobb kattintás vagy Shift + X a sorban várakozó híreket is eldobja.
- Alapból a képernyő bal szélén, a chat fölött jelenik meg, kisebb (0,67×) méretben.
- A `/mpal move` paranccsal mozgatható, és közben a jobb alsó sarkánál fogva vagy egérgörgővel arányosan átméretezhető (0,5–2×; jobb kattintás a sarokra = 1,0× méret); újra kiadva vagy a beállítások bezárásával befejezhető a mozgatás. A méret és a hely mentődik.
- A láthatósági idő **1–60 másodperc** között állítható, például `/mpal time 8`.
- A játék saját hangeffektjei, a chatbe kiírás és a saját hírek megjelenítése külön kapcsolhatók.
- Az addon saját hangjainak hangereje **0–100%** között állítható (a beállítópanelen vagy például `/mpal volume 50`); 0% néma, 100% az eddigi hangerő, a játék többi hangja nem változik.

## Haverok elérése

**Minden résztvevőnél fusson az addon**, aki híreket vagy helyzetadatokat szeretne küldeni és látni. Az addon guild-, csapat- és barátlistás kapcsolatokat, valamint a korábban megismert társaknak küldött addon-suttogásokat használ.

Az első indítás üdvözlőablaka segít csatlakozni a közös haveri csatornához. Saját közös csatorna a `/mpal crew <név>` paranccsal választható; mindenkinél ugyanazt a nevet kell megadni. Az egyéni csatornán a szerver nem feltétlenül továbbítja az addonüzeneteket, ezért a megismert társak közvetlen addon-suttogással is elérhetők.

Kapcsolatellenőrzéshez `/mpal ping <név>`, részletes állapothoz `/mpal diag` használható. Harc közben a hírek várakozhatnak, és harc után mennek ki. Raidben, battlegroundon és arénában a hírek küldése alapból ki van kapcsolva; a `/mpal raidhir` paranccsal állítható.

## Térképes helyzetjelzés

A térképes és beállítási tooltipek, valamint a beállítások feliratai magyar ékezeteket (ő/ű) is tartalmazó Barlow betűtípust használnak.

A világtérképen a társakat kis, kasztszínű pontok jelzik. Rámutatáskor név, szint, zóna, elérhető koordináták és a jel állapota látható. A nevek állandó megjelenítése külön kapcsolható.

- Mozgáskor körülbelül 5 másodpercenként, álló helyzetben ritkábban küld helyzetet.
- A régi jel halványul, majd körülbelül 5 perc után eltűnik.
- Instance-ben csak a zónaadat továbbítható.
- A layerjelzés a környező NPC-k azonosítóiból következtet; pontossága az elérhető adatoktól függ.
- A térképes jelölők és a saját hely megosztása egymástól függetlenül kapcsolhatók.

## Beállítások és parancsok

A beállítópanel a **Beállítások → Kiegészítők → Moteve Pals** oldalon vagy a `/mpal opciok` paranccsal érhető el. Két oszlopban tartalmazza a hír-, küldési, térképes és grafikai kapcsolókat.

| Parancs | Művelet |
| --- | --- |
| `/mpal` | Állapot és súgó |
| `/mpal opciok` | Beállítások |
| `/mpal test` | Helyi mintahírek |
| `/mpal move` | Felugró ablak mozgatása és méretezése (sarok / görgő) |
| `/mpal time 8` | Megjelenítési idő: 8 másodperc |
| `/mpal sound` | Hang kapcsolása |
| `/mpal volume 50` / `/mpal hangero 50` | Az addon hangjainak hangereje: 50% |
| `/mpal chat` | Chatbe kiírás kapcsolása |
| `/mpal self` | Saját hírek megjelenítésének kapcsolása |
| `/mpal guild` / `/mpal group` / `/mpal friends` | Küldés kapcsolása az adott kapcsolatok felé |
| `/mpal crew <név>` | Közös csatorna kiválasztása; név nélkül kikapcsolás |
| `/mpal ping <név>` | Kapcsolat ellenőrzése egy társsal |
| `/mpal diag` | Kapcsolati és helyzetdiagnosztika |
| `/mpal debug` | Küldési és fogadási hibakereső kiírás kapcsolása |
| `/mpal hol` | Ismert társak helyzetének listája |
| `/mpal map` | Térképjelölők kapcsolása |
| `/mpal share` | Saját hely megosztásának kapcsolása |
| `/mpal nevek` | Térképes nevek kapcsolása |
| `/mpal raidhir` | Hírek küldése raidben / PvP-területeken |
| `/mpal welcome` | Üdvözlőablak megnyitása |
| `/mpal legend` | Kasztlegendák listázása |
| `/mpal legend <class> <név> <cím>` | Kasztlegenda beállítása |
| `/mpal on` / `/mpal off` | Addon be- és kikapcsolása |

### Grafikai kapcsolók

A `/mpal weed` a sűrűbb, távolabb látszó növényzetet kapcsolja (`groundEffectDensity 256`, `groundEffectFade 370`, `groundEffectDist 500`). A `/mpal feny` a „Jó fények” profilt kapcsolja (`Contrast 80`, `Brightness 49`, `Gamma 1.2`). Kikapcsoláskor a kliens alapértékeit, illetve ha azok nem kérdezhetők le, a korábban eltárolt értékeket használja.

## Kompatibilitás és ellenőrzés

A célkliens **WoW Forever**, a TOC Interface-értéke **16001**. A mentések neve `MotevePalsDB` és karakterenként `MotevePalsChar`.

A csomag a fenti aktuális verzió forrásából készül. Feltöltés előtt a fájlok azonosságát, a Lua-szintaxist és a ZIP tartalmát ellenőriztük. Az élő játékbeli működést és a játékosok közötti üzenetküldést a feltöltéskor nem teszteltük újra. A kliens és a szerver korlátozásai befolyásolhatják az üzenetek és helyzetadatok kézbesítését.

## Hibajelentés és források

Hibát az [Issues oldalon](https://github.com/zolesz05/PalsAddon/issues) jelezhetsz. Add meg a kliens és az addon verzióját, a reprodukálás lépéseit és az érintett hír- vagy térképfunkciót. Kapcsolati hibánál a `/mpal diag` kimenete segíthet.

A teljes addon a [MotevePals](MotevePals/) mappában található. A [részletes leírás és változásnapló](MotevePals/README.txt) a korábbi változásokat is felsorolja. A Marcellus és Barlow betűtípusok SIL Open Font License fájljai a `MotevePals/Fonts/` mappában szerepelnek.

## Csomag frissítése

A repository gyökeréből:

```sh
python tools/package_addon.py
```

Az addon hangerő-kezelését (mentés, 0/100%, a kölcsönvett hangcsatorna visszaállítása, `/mpal volume`, beállítópanel) Lua 5.1-ben, a WoW API csonkjaival futtatva ellenőrzi:

```sh
uv run --with lupa python tools/check_volume.py
```

A csomagoló ellenőrzi a TOC bejegyzéseit és a ZIP tartalmát, lecseréli a `downloads/MotevePals.zip` fájlt, és eltávolítja a korábbi verziószámos addoncsomagokat ebből a mappából. A forrást, a ZIP-et és a README-t együtt kell feltölteni.
