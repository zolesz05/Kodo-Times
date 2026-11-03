-- Moteve Pals - the lines that pop up. Placeholders:
--   %n = name   %l = level   %z = zone   %s = skill   %r = skill rank   %i = item
--   %g = the legend of the dead player's class   %t = the legend's title (see ns.LEGENDS below)
-- Add your own freely: one line per entry, the addon picks one at random (never the same twice in a row).
-- ns.LINES_AT[kind][level] = lines that join ns.LINES[kind] only at that exact level (e.g. levelround at 40).
local _, ns = ...

ns.LINES = {
    levelup = {
        "%n szintet lépett (%l). A családja büszke lehet rá.",
        "%n most már %l-es. Ugyanolyan béna, csak több HP-val.",
        "DING! %n elérte a %l. szintet. Valaki adjon neki egy sört.",
        "Grat, %n! %l. szint, és még mindig lófasz dps-t nem tol.",
        "%n %l-es. Most már a szürke mobok is komolyan veszik. Kicsit.",
        "%n leveluppolt (%l). Valaki hívja fel a családját, mert ő nem fogja.",
        "%n elérte a %l. szintet. Szétszakítja a talenteket.",
        "Szintlépés: %n (%l). Ennyit seggen még nem ültek.",
        "%n %l-es lett. Úgyis megint meghal valami faszságban.",
        "%n %l. szint. Hogy mi változott? Semmi. De legalább villogott.",
        "%n szintet lépett. A tükörképe szerint még mindig ugyanaz a balfasz, csak %l-es.",
        "%l. szint, %n! A közvetítést a 'Csak még egy quest' alapítvány támogatta.",
        "Új szint! %n lelkének értéke továbbra is nulla.",
        "Gratulálunk! %n most már drágábban hal meg.",
        "%n, a démonod büszke rád. Hazudik.",
        "%n új képességeket oldott fel. Józan ész továbbra sem elérhető.",
        "LEVEL UP: %n felhasználói jogosultságai frissültek.",
        "%n egy szinttel közelebb került a munkanélküliséghez.",
        "%n anyja büszke lenne. Ha tudná, mivel tölti az idejét.",
        "%n már megint nem a való életben fejlődött.",
        "%n fejlődése megállíthatatlan. A társadalmi leépülése szintén.",
        "%n fejlődése már nem természetes folyamat. Ez szakmai segítséget igényel.",
        "%n újabb mérföldkövet ért el a digitális önpusztításban.",
        "%n karaktere fejlődik. A teste közben lassan feladja.",
        "%n: Egyre magasabb szintű probléma.",
        "%n: Új szint, változatlan szellemi kapacitás.",
        "%n: A karakter fejlődése meghaladta a gazdájáét.",
        "%n ismét magasabb szintre emelte a problémát.",
        "%n tapasztaltabb lett, de bölcsebbnek továbbra sem neveznénk.",
        "%n fejlődése olyan, mint a gazdaság: papíron lenyűgöző.",
        "%n ma is közelebb került ahhoz, aki lenni szeretne. De még messze van.",
    },
    levelround = {
        "%n elérte a %l. szintet! Ez már nem hobbi, ez kórkép.",
        "%n kerek %l-es. Kerek szám, kerek pocak, kerek élet.",
        "%n kerek %l. szinten. Valaki küldjön egy coppert a postaládájába.",
        "%l, %n! Ez annyi óra, hogy a napfény már bírósági végzést kért ellene.",
        "Kerek %l. szint, %n. Aludni ki fog?",
    },
    level60 = {
        "%n ELÉRTE A 60-AT! A napfény mostantól hivatalosan is ellenség.",
        "60! %n mostantól a raidek rabszolgája. Részvétem a családjának.",
        "%n 60-as lett. Most kezdődik az igazi szopás: A GEAR.",
        "MAX LEVEL! %n végre ráér... napi 10 órát farmolni.",
        "%n 60. Gratulálunk, a következő lépés: elmagyarázni a főnökének, miért volt betegszabin 4 hétig.",
        "%n 60-as lett, szagod hogy áll?",
        "%n elérte a 60-at, reméljük a fürdőszobát is.",
        "%n 60. W vitaminból nem szenvedsz hiányt, barátom.",
        "Gratulálunk, %n! Most kezdődik az igazi munkanélküliség.",
    },
    death = {
        "%n meghalt itt: %z. Egy billentyűzettel kevesebb.",
        "%n elhalálozott. Tartsunk egy perc néma röhögést.",
        "%n ismét a Spirit Healernél. Csak a szoki.",
        "%n: 'Laggolt a szerver!' – Egy faszt, %n.",
        "%n beadta a kulcsot (%z). WP a mobnak.",
        "%n meghalt. Szerinte taktikai visszavonulás volt. Dobott egy hasast.",
        "%n megint kimúlt. Lassan törzsvendég a temetőben, kap pecsételős kártyát.",
        "%n halott. Ha valaki talál egy agyat %z környékén, az az övé.",
        "%n meghalt. Futás a hulládért az egyetlen kardió az életében.",
        "%n megdögölt.",
        "%n sajnos befosott.",
        "%n szarba lépett.",
        "%n már nem lesz halottabb.",
        "%n rizzeli a Spirit Healert.",
        "%n: Geci, itt a Spirit Healer.",
        "%n tolt egy Attilát.",
        "%n-t elaltatták. Szép álmokat neki!",
        "%n neki gatya. Hívjátok a Fésűst.",
        "%n halott. Xd",
        "%n elhunyt. %z területén. Mi a fasznak ment oda?",
        "%n már a halakkal alszik.",
        "%n úgy be van baszva, mint macskát szarni.",
        "%n imádja a földet nyalogatni.",
        "%n nem élte túl, most már tényleg a föld alatt van a teljesítménye.",
        "%n újraélesztése sikertelen. Talán legközelebb kevesebb hülyeséggel próbálkozik.",
        "%n karaktere elhunyt. A szégyen azonban örök.",
        "%n javítási költsége meghaladja a karakter piaci értékét.",
        "Egy újabb mob büszkén mesélheti el, hogy legyőzött egy játékost. Az áldozat: %n.",
        "%n temetésére senki nem érkezett. Mindenki farmol.",
        "Critical failure: {%n}. Brain.dll not found.",
        "A mob nem volt erős. %n volt gyenge.",
        "A Spirit Healer már név szerint ismeri %n-t.",
        "%n ismét visszatért a szellemvilágba. Úgy tűnik, ott már törzsvendég.",
        "%n sikeresen tesztelte a mob sebzését. Saját magán.",
        "A helyi élővilág újabb áldozatot követelt: %n.",
        "%n ma is hozzájárult Azeroth hulladéktermeléséhez.",
    },
    skill = {
        "%n %s skillje elérte a %r-t. Végre ért valamihez.",
        "%n %s: %r. A szakmunkás-bizonyítvány postán érkezik.",
        "%n %s skillje %r. A sok kattintástól már a csuklója is sztrájkol.",
        "Gratula, %n! %s %r. Anyád mondhatja végre, hogy van szakmád.",
        "%n %s %r-on. Ennyi kattintásért máshol fizetést adnak.",
        "%n elérte a %r-t %s-ben. A hobbiból lassan függőség lett.",
        "%n: %s %r. Ennyi idő alatt valaki diplomát szerez.",
    },
    craftblue = {
        "%n összerakott egy kéket: %i. Remélem, nem ő fogja hordani.",
        "%n kék itemet csinált (%i). A szerencse még a vakokra is rámosolyog.",
        "%n alkotott: %i. Ma legalább valami hasznosat is csinált.",
        "%n kéket craftolt (%i). Valaki szóljon neki, hogy a gold elfogyott.",
        "%n kézműves foglalkozás: %i. Ügyes vagy, kisfiam!",
    },
    craftepic = {
        "EPIC CRAFT! %n legyártotta: %i. Mindenki térdre, de ne túl közel.",
        "EPIC!! %n: %i. Nem lehet bírni vele.",
        "%n epiket craftolt (%i). Valaki hívjon mentőt az egójához.",
        "%n: %i. Epic. Hivatalosan is menőbb nálad. Bocs.",
        "%n kikalapálta ezt: %i. A kovácsok istene most büszkén b@ssza a vasat.",
    },
    epicloot = {
        "%n epiket lootolt: %i. Az RNG-isten ma őt választotta, minket lesz@rt.",
        "%n kapott egy ilyet: %i. Irigység mód: bekapcsolva.",
        "EPIC drop! %n: %i. Mostantól csak napszemüvegben lehet ránézni.",
        "%n: %i. A többiek közben még mindig zöldekben flangálnak.",
        "%n epic lootja: %i. Szép. Utálunk.",
        "EPIC drop! %n: %i. Aura farming: ON.",
    },
}

-- extra lines of a single level: mixed into that kind's lines only at exactly that level
ns.LINES_AT = {
    levelround = {
        [10] = {
            "%n már nem teljesen kezdő. Csak majdnem.",
        },
        [20] = {
            "%n számára a játék most kezd igazán drága lenni.",
        },
        [30] = {
            "%n, félúton vagy. Legalábbis lélekben.",
        },
        [40] = {
            "Mount unlocked, %n. Pénztárca locked.",
        },
        [50] = {
            "%n már túl sok időt ölt bele ahhoz, hogy abbahagyja.",
        },
    },
}

-- Class legends: when someone dies, sometimes the legend of their class weighs in.
-- Add your own: CLASS = { name = "Name", title = "a ... istene/királya" }
-- (in game too: /mpal legend paladin SADISS a paladinok istene)
ns.LEGENDS = {
    PALADIN = { name = "SADISS", title = "a paladinok istene" },
    SHAMAN  = { name = "Chainsaw", title = "a shamanok királya" },
}

-- death lines with the class legend (used about every second death when the class has a legend)
ns.LINES.deathlegend = {
    "%g, %t büszke lenne rá!",
    "%n ismét a földön. %g, %t könnyes szemmel nézi... a röhögéstől.",
    "%n elhullott. %g, %t, már írja a könyvet: 'Hogyan ne csináld'.",
    "%g, %t ezt látta, és szégyenében classt váltott.",
    "%n meghalt. %g, %t kiadta a parancsot: mostantól csak a bankban állhatsz.",
    "%n bekapta. %g, %t szerint ez a szégyenfal első helyezettje.",
    "%g, %t üzeni %n-nek: 'Fiam, a földön fekvés nem tank-taktika.'",
    "%g, %t büszke lenne rád, %n. Ha nem halnál meg ilyen szánalmasan.",
}

-- small headline above the line
ns.TITLES = {
    levelup = "DING!", levelround = "DONG!", level60 = "LEGENDA SZÜLETETT",
    death = "RIP BALFASZ", deathlegend = "RIP BALFASZ", skill = "SZAKMAI SIKER",
    craftblue = "FRISS CRAFT", craftepic = "EPIKUS ALKOTÁS", epicloot = "EPIC LOOT",
}
