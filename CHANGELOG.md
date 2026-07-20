# English Coach — Projekt Fejlesztési Napló (Changelog & Roadmap)

Minden fejlesztési lépés, architekturális döntés, elvégzett tesztelés és jövőbeli feladat ebben a dokumentumban kerül rögzítésre.

---

## 📌 Jelenlegi Verzió: `v1.2.0` (2026-07-20)

### 🌟 Főbb Fejlesztések

#### 1. **Modell & Backend Továbbfejlesztések (`app/main.py`)**
- **Alapértelmezett Modell:** Frissítve a legújabb Vertex AI `gemini-2.5-flash` modellre a kiemelkedő válaszidő és intelligencia érdekében.
- **Session azonosítás:** Kérés JSON body (`session_id`) és HTTP fejlécek (`X-Session-ID`) támogatása (fallback Flask session cookie-ra).
- **Munkamenet Összegző Végpont (`/summary`):** Új API végpont, amely a prompt definíció alapján kéri le a munkamenet végén az összefoglalót (fejlődés, javított hibák, új szavak, házi feladat).
- **Előzmény-korlátozás (Context Window Pruning):** A memóriában tárolt előzmények automatikus szűkítése az utolsó 40 üzenetre (20 párbeszéd fordulóra) a megbízható és gyors hívásokért.
- **Robustus Hibakezelés:** `try-except` védőháló a Vertex AI API hívások köré, 500-as kódú strukturált hibaválaszzal.
- **CORS Fejlécek:** Cross-Origin Resource Sharing támogatás (`Access-Control-Allow-Origin: *`).

#### 2. **Interaktív Web UI (`app/static/`)**
- **Felület:** Modern dark glassmorphism felület `Outfit` és `Plus Jakarta Sans` betűtípusokkal, reszponzív elrendezéssel mobilra és desktopra.
- **Témaválasztó Modul:** Gyorsindító gombok az IT témákhoz (*Daily Standups, DevOps/CI-CD, Cloud AWS/Azure, Docker, Sysadmin, Enterprise AI, Állásinterjú*).
- **Hangfunkciók:**
  - **Text-to-Speech (TTS):** Web Speech API alapú hangos felolvasás.
  - **Beszédfelismerés (STT):** Mikrofon alapú beszéd-szöveg konverzió angol nyelven.
- **Értékelő Kártya:** Külön vizuális kiemelt smaragd kártya az összegzések megjelenítésére.

#### 3. **Tesztautomatizálás (`app/test_main.py`)**
- 8 dedikált unit teszteset a `unittest` és `unittest.mock` keretrendszerrel (modell teszt, `/health`, `session_id` kérések, hibaágak, maximális üzenethossz validáció, `/summary` sikeres és üres előzmény hibaágak).

---

## 📅 Fejlesztési Előzmények (History)

### `v1.1.0` (2026-07-20)
- Flask statikus mappa konfiguráció beállítása.
- Web UI frontend (HTML5/CSS3/JavaScript) elkészítése.
- Unit teszt lefedettség kiépítése.

### `v1.0.0` (2026-07-20)
- Kezdeti architektúra létrehozása (Flask + Vertex AI Gemini API).
- AI Coach System Prompt megírása ([app/coach_prompt.py](file:///srv/projects/english-coach/app/coach_prompt.py)).
- Dockerfile és GCP Cloud Build pipeline (`cloudbuild.yaml`) konfiguráció.

---

## 🔮 Jövőbeli Útiterv (Roadmap)

- [ ] **Firestore Adatbázis Integráció:** A memóriában tárolt `CONVERSATIONS` kiváltása tartós Google Cloud Firestore adatbázisra.
- [ ] **Autentikáció:** Firebase Auth / Google Sign-In bevezetése a személyes munkamenetek védelmére.
- [ ] **Mentett Szókincs (Flashcards / Anki):** Az órán megismert 3-5 új IT kifejezés automatikus mentése és külön felületen való kikérdezése.
- [ ] **Saját Dokumentáció Betöltés (RAG):** Lehetőség cég- vagy projektspecifikus dokumentumok feltöltésére az egyedi beszédgyakorláshoz.
