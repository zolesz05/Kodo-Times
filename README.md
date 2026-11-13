# Kodo Times

**Kodo Times** (korábbi nevén Moteve Pals) egy közösségi World of Warcraft addon a WoW Forever klienshez. Vicces, díszes felugró híreket mutat a haverok szintlépéseiről, halálairól, szakma-mérföldköveiről és értékes tárgyairól, valamint megjeleníti az addont használó társakat a világtérképen.

[![Legfrissebb kiadás](https://img.shields.io/github/v/release/zolesz05/Kodo-Times?label=Aktu%C3%A1lis%20verzi%C3%B3)](https://github.com/zolesz05/Kodo-Times/releases/latest)

[Legfrissebb addon letöltése (ZIP)](https://github.com/zolesz05/Kodo-Times/releases/latest/download/KodoTimes.zip)

A link mindig a legutóbbi kiadás `KodoTimes.zip` fájlját tölti le, így frissítéskor is ugyanaz használható. A korábbi verziók a [Releases oldalon](https://github.com/zolesz05/Kodo-Times/releases) érhetők el. A korábbi, a repositoryba feltöltött ZIP-re mutató letöltési link megszűnt, helyette ezt használd. A ZIP egyetlen mappát tartalmaz: `KodoTimes`.

## Telepítés és első indítás

1. Töltsd le és csomagold ki a fenti ZIP-et.
2. Másold a ZIP-ben lévő `KodoTimes` mappát a játék `Interface/AddOns/` könyvtárába.
3. A karakterválasztón engedélyezd a **Kodo Times** addont, majd lépj be.
4. A beállításokat a `/kodo opciok` paranccsal nyithatod meg. Egyedül a `/kodo test` paranccsal próbálhatod ki a felugró híreket. A régi `/mpal` és `/pals` parancs is működik.

```text
Interface/
└── AddOns/
    └── KodoTimes/
        ├── KodoTimes.toc
        ├── Pals.lua
        ├── Map.lua
        ├── Fonts/
        └── Textures/
```

A mappaneveket tartsd meg: a `KodoTimes.toc` közvetlenül a `KodoTimes` mappában legyen. Ha egy új addon még nem jelenik meg a listában, indítsd újra a klienst. Meglévő addon frissítése után `/reload` használható, kivéve ha a frissítés új textúrafájlokat hoz (pl. 0.9.29): ilyenkor a klienst teljesen újra kell indítani, különben az új képek nem töltődnek be. A `WTF` könyvtárat tartsd meg, mert abban vannak a mentett beállítások.

### Frissítés a Moteve Pals-ról (0.9.x)

Az addon új neve **Kodo Times**, a mappája `KodoTimes`. Frissítéskor:

1. Töröld a régi `MotevePals` mappát az `Interface/AddOns/` könyvtárból, és másold be helyette a `KodoTimes` mappát.
2. Lépj ki teljesen a játékból, és indítsd újra a klienst (a `/reload` nem elég, mert új addonmappa jött).

A régi (0.9.x) beállítások nem jönnek át: a Kodo Times alapértékekkel indul (hangerő, a felugró ablak helye és mérete, a kapcsolók és a crew újra beállítandó), és minden karakternél egyszer feljön az üdvözlőablak.

Ha a régi, teljes addon is a helyén marad, a Kodo Times nem csinál semmit (különben minden hír kétszer jelenne meg), csak egy figyelmeztetést ír a chatbe: ilyenkor töröld a régi `MotevePals` mappát, és indítsd újra a klienst. A régi (0.9.x) és az új verziót használó haverok továbbra is látják egymás híreit és térképes helyét.

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
- Alapból a képernyő bal szélén, a chat fölött jelenik meg, kisebb (0,9×) méretben.
- A `/kodo move` paranccsal mozgatható, és közben a jobb alsó sarkánál fogva vagy egérgörgővel arányosan átméretezhető (0,5–2×; jobb kattintás a sarokra = 1,0× méret); újra kiadva vagy a beállítások bezárásával befejezhető a mozgatás. A méret és a hely mentődik.
- A láthatósági idő **1–60 másodperc** között állítható, például `/kodo time 8`.
- A játék saját hangeffektjei, a chatbe kiírás és a saját hírek megjelenítése külön kapcsolhatók.
- A chatbe írt `[Kodo Times]` hírekben a karakter neve a kasztszínében jelenik meg (ismeretlen kasztnál világos homokszínben), és kattintható: bal kattintásra suttogást nyit neki, mint a játék saját névlinkjei.
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

A célkliens **WoW Forever**, a TOC Interface-értéke **16001**. A mentések neve `KodoTimesDB` és karakterenként `KodoTimesChar`; a 0.9.x-es `MotevePalsDB`/`MotevePalsChar` mentést a 0.10.3 óta nem olvassa. A TOC `OptionalDeps: MotevePals` sora csak a betöltési sorrendet állítja: így egy bent maradt régi, teljes addon előbb töltődik be, és a Kodo Times csendben marad mellette. A címek és a medálok a csomagban lévő Marcellus betűtípust használják, mert a játék Morpheus betűjéből hiányzik az Ő/Ű.

A csomag a fenti aktuális verzió forrásából készül. Feltöltés előtt a fájlok azonosságát, a Lua-szintaxist és a ZIP tartalmát ellenőriztük. Az élő játékbeli működést és a játékosok közötti üzenetküldést a feltöltéskor nem teszteltük újra. A kliens és a szerver korlátozásai befolyásolhatják az üzenetek és helyzetadatok kézbesítését.

## Hibajelentés és források

Hibát az [Issues oldalon](https://github.com/zolesz05/Kodo-Times/issues) jelezhetsz. Add meg a kliens és az addon verzióját, a reprodukálás lépéseit és az érintett hír- vagy térképfunkciót. Kapcsolati hibánál a `/kodo diag` kimenete segíthet.

A teljes addon a [KodoTimes](KodoTimes/) mappában található. A [részletes leírás és változásnapló](KodoTimes/README.txt) a korábbi változásokat is felsorolja. A Marcellus és Barlow betűtípusok SIL Open Font License fájljai a `KodoTimes/Fonts/` mappában szerepelnek.

## Csomag frissítése

A telepíthető ZIP-et a GitHub Actions építi a `main` ágból, kézzel nem kell újraépíteni vagy feltölteni:

1. Az addon (`KodoTimes/` mappa) minden változásánál emeld a verziót a `KodoTimes/KodoTimes.toc` `## Version` sorában és a `KodoTimes/README.txt` első sorában, és írj a változásnaplóba egy `<verzió>:` bejegyzést.
2. A pull requesten a `checks` workflow lefuttatja az összes `tools/check_*.py` szkriptet, és piros lesz, ha a `KodoTimes/` alatt változott valami, de a verzió nem emelkedett.
3. A merge után a `release` workflow létrehozza a `v<verzió>` kiadást a `KodoTimes.zip` fájllal, a változásnapló-bejegyzéssel mint kiadási jegyzettel. Ha a `v<verzió>` tag már létezik, nem csinál semmit.

A verzió fejlécét, a változásnapló-bejegyzést és a verzióemelést helyben így ellenőrzi (`--notes`: a kiadási jegyzet):

```sh
python tools/check_version.py --base origin/main
python tools/check_version.py --notes
```

A ZIP helyben is elkészíthető, a `dist/KodoTimes.zip` fájlba (ezt a git nem követi):

```sh
python tools/package_addon.py
```

Az addon hangerő-kezelését (mentés, 0/100%, a kölcsönvett hangcsatorna visszaállítása, `/kodo volume`, beállítópanel) Lua 5.1-ben, a WoW API csonkjaival futtatva ellenőrzi:

```sh
uv run --with lupa python tools/check_volume.py
```

A chatbe írt hírek névlinkjét (kasztszín, suttogási cél, más realmről érkezőnél a realm is, a felugró szöveg változatlan) így ellenőrzi:

```sh
uv run --with lupa python tools/check_chatlink.py
```

Az első indításkor felugró üdvözlő ablak szövegeit, a cím és a leírás betűméretének kicsinyítését (hogy kiférjen a sávba) és a gombok változatlan működését így ellenőrzi:

```sh
uv run --with lupa python tools/check_welcome.py
```

A telepítést (a TOC, a ZIP-ben csak a `KodoTimes` mappa, nincs `MotevePals` mappa, friss telepítésnél alapértékek és üdvözlőablak, a régi 0.9.x mentést figyelmen kívül hagyja és érintetlenül hagyja, a mentett méret megmarad, régi addon mellett csendes mód a mappa törlésére figyelmeztetve), a megtartott `MOTEVEPAL` üzenetelőtagot és a `/kodo` `/mpal` `/pals` parancsot így ellenőrzi:

```sh
uv run --with lupa python tools/check_install.py
```

A betűtípusok ő/ű/Ő/Ű karaktereit (és hogy egy Lua-fájl se használja a Morpheust), illetve a régi nevek eltűnését így:

```sh
python tools/check_fonts.py
python tools/check_rename.py
```

A csomagoló ellenőrzi a TOC bejegyzéseit és a ZIP tartalmát, és csak a `KodoTimes` mappát teszi a ZIP-be (alapból `dist/KodoTimes.zip`, a `--out` kapcsolóval máshová). A `check_install.py` ugyanígy, ideiglenes mappába építi és vizsgálja a ZIP-et.
