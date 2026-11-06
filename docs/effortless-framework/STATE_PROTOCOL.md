# STATE_PROTOCOL.md — hogyan viszi át az állapotot egyik tutor a másikhoz

Cél: ugyanazt a tanulást tudja folytatni a Claude, a ChatGPT és az app. Az állapot **fájlban** van, nem a modell fejében.

## Fájlok

| Fájl | Mire való | Ki frissíti |
|------|-----------|-------------|
| `STUDENT_STATE.md` | szint, erősségek, hibaminták, preferenciák | foglaló frissítés kétheti mérés után, és ha új tartós megfigyelés van |
| `PROGRESS_LOG.md` | alkalmankénti rövid napló (SESSION RECORD blokkok) | minden alkalom végén beillesztve |
| `ITEM_TRACKER.md` | tételek állapota: új, hallott, aktív, függőben | minden hét végén összesítve a naplóból |

## SESSION RECORD formátum (a tutor ezt adja ki az alkalom végén)

```
SESSION RECORD
date: YYYY-MM-DD
track: IT | Bible | Song | Check | Placement
lesson: <fájl és azonosító, pl. LESSONS_W01_IT L2>
duration_min: <szám>
time_of_day: morning | afternoon | evening
freshness_1_5: <1 fáradt ... 5 friss, a tanuló mondja>
minutes_actual: <valódi idő, ha eltér a tervtől>
phase_reached: <pl. D active comprehension, step 3 who/what>
goal_met: yes | partly | no
new_items_taught: [<chunk>, ...]
understood_not_yet_said: [<chunk>, ...]
said_correctly_first_try_today: [<chunk>, ...]
said_correctly_after_repair: [<chunk>, ...]   # nem számít elsőre jónak
pending (3rd failure, return in 3-7 days): [<chunk>, ...]
errors_seen: [<hiba -> javítás>, ...]       # pl. "God try -> God tried"
pronunciation: [<szó vagy hang>, ...]       # pl. "faith/face"
scores: <ha volt mérés: pont/max és részek>
daily_speaking: {topic: <téma>, seconds: <szám>, good: [<2 mondat>], corrections: [<..>], expansion: <mondat>, enrichment: <tétel>}
next_priority: [<max 3 pont>]
return_dates: [{item: <chunk>, on: YYYY-MM-DD}, ...]
```

Szabályok:
- Csak azt írd be, ami az alkalmon **történt**. Nem találsz ki eredményt.
- `said_correctly_first_try_today` csak akkor kerül `ITEM_TRACKER`-ben **aktívra**, ha két különböző napon szerepel.
- Beszédfelismerési hibát (rossz átirat) ne vegyél fel kiejtéshibának egyetlen előfordulás alapján.

## Kezdeti állapot (2026-11-06)

A `PROGRESS_LOG.md` első bejegyzése a mai alkalmat rögzíti, az `ITEM_TRACKER.md` az ott elhangzott tételeket.

## Átadás egy új tutornak

1. Add át: `SYSTEM.md`, `STUDENT_STATE.md`, `SESSION_SCRIPTS.md`, `PROGRESS_LOG.md` utolsó 3 bejegyzése, `ITEM_TRACKER.md`, az aznapi lecke.
2. A tutor a napló utolsó bejegyzéséből folytatja a fázist (`phase_reached`), és a `return_dates` szerint hozza vissza a függő tételeket.
3. Ha ellentmondás van a napló és a `STUDENT_STATE.md` között, a **frissebb dátumú** számít.
