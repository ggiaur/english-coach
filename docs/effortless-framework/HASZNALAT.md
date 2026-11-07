# HASZNALAT.md — így használd (magyarul, röviden)

## Mi mire való

| Fájl | Mire |
|------|------|
| `WEEKLY_PLAN_W01.md` | mit csinálsz melyik nap |
| `MONTHLY_PLAN_M01.md` | szakaszok és kapuk (haladás tudás szerint) |
| `LESSONS_W01_IT.md` | a hétköznapi IT-leckék (L1–L5) teljes szövege |
| `LESSONS_W01_BIBLE_AND_SONGS.md` | péntek, szombat és az 5 dal |
| `LESSON_BIBLE_JOHN9_01.md` | a 2026-11-07-i szombat (János 9, 1–5) |
| `LISTENING_LINKS.md` | kattintható dal- és hanganyag-linkek |
| `ASSESSMENT_KIT.md`, `QUESTION_GYM.md` | heti és kétheti mérés, napi kérdéstorna |
| `PORTABLE_TUTOR_PROMPT.md`, `SESSION_SCRIPTS.md` | a tutor-modellnek (Claude, ChatGPT) |
| `TASK_LANGUAGE.md` | az egyszerű feladatnyelv (8 szó), egy utasítás egy fordulóban |
| Weboldal: `/progress` az appban | heti terv, kattintható dalok, pipák, SESSION RECORD vázlat |
| `STUDENT_STATE.md`, `PROGRESS_LOG.md`, `ITEM_TRACKER.md` | hol tartasz |

## Alkalom indítása (Claude, ChatGPT vagy bármely modell)

1. Első alkalom ChatGPT-vel: hozz létre egy Projectet, másold be a `PORTABLE_TUTOR_PROMPT.md` kódblokkját az utasításokba, és töltsd fel a fájlokat (lásd a fájl elején).
2. Mondd: `Start session. Track: IT. Lesson: L1.` vagy `Start session. Track: Bible. Lesson: John 9.`
3. Dalnál: `Start session. Track: Song. Song: S1.` Nyisd meg a linket a `LISTENING_LINKS.md`-ben.
4. Kérdéstorna mindig az elején van (5 perc).

## Minden alkalom végén: napi szabad beszéd

2–3 perc beszéd egy egyszerű témáról, **közben nincs javítás**. A végén visszajelzést kapsz: két jó mondat, egy–két javítás, hogyan mondhattad volna bővebben vagy profibban, és egy új szinonima vagy szókapcsolat (naponta egy). Részletek: `DAILY_SPEAKING.md`. A tutor megkérdezi, mikor tanultál (reggel, délután, este) és mennyire voltál friss (1–5). Kéthetente ebből készül a terhelés-visszamérés.

## Alkalom vége

1. Mondd: `End session.`
2. A modell kiad egy `SESSION RECORD` blokkot. Másold be a `PROGRESS_LOG.md` **tetejére**.
3. Ha Claude-dal dolgozol szöveges csevegésben, kérd: `Frissítsd a PROGRESS_LOG-ot és az ITEM_TRACKER-t.` Én megteszem.

## Mérés

- Csütörtökön heti ellenőrzés (5').
- Kéthetente szintfelmérés (10', 2026-11-19, 2026-12-03). A pontszám az `ASSESSMENT_KIT.md` szerint.

## Ha elakadsz egy tételben

Legfeljebb kétszer próbáljuk teljesen újra két külön napon. Harmadszor függőben marad, és 3–7 nap múlva más helyzetben visszajön. Nem ragadunk le.

## Mit nem tud a ChatGPT hangos módja

- Nem tud igazi csendet tartani. Ezért a „lassú kör” lassú beszéd, rövid mondatok, egyértelmű megállás. Ne kérj tőle `...`-t.
- Nem emlékszik az előző alkalomra, ha nem adod oda a `PROGRESS_LOG.md` utolsó 3 bejegyzését és az `ITEM_TRACKER.md`-t.
- Hajlamos magától kérdezni és válaszolni. Ilyenkor mondd: `Give me a task. Do not give the answer.`
- Hajlamos átfogalmazni a Biblia-szöveget. Mondd: `Use only the Bible wording in the lesson file.`
- Hajlamos dalszöveget idézni. Mondd: `Do not quote lyrics. Explain the meaning.`

## Tartós írási engedély a repóhoz

A `CLAUDE.md` rögzíti, hogy ennek a repónak az írását végleg engedélyezted. A tényleges hozzáférést a csatlakozás beállítása adja, azt Claude nem változtatja.

## Tanulóoldalak (`/learn`)

János 9 (szöveg, jelenetek, 5 szereplő), kifejezéskártyák, tankönyv. Minden mondat mellett lejátszó: ▶ természetes, 🐢 lassú, „4 sebesség” (lassú, lassú, közepes, természetes). A kártyán: kifejezés, teljes mondat, nyelvtani megjegyzés. Gyakorló mód: a mondat rejtve, először te mondod. Jézusról nincs kép. A telepítés a saját Dockerre: `DOCKER.md`.

## Haladási weboldal

Az app `/progress` oldala: napi lista pipákkal, kattintható dallinkek, SESSION RECORD vázlat. A pipák csak abban a böngészőben maradnak meg, ahol bepipáltad (nincs bejelentkezés, nincs szerveren tárolt adat). Ha több eszközön vagy bejelentkezéssel akarod, azt külön döntjük el.
