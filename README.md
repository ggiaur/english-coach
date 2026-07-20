# English Coach — Cloud Run + Vertex AI Gemini

Személyes angol beszédcoach app, IT-fókuszú beszélgetésekkel. Backend: Flask + Vertex AI Gemini, Cloud Run-on futtatva, GitHub-ból automatikus deploy-jal (Cloud Build).

## Architektúra

```
GitHub repo (push) → Cloud Build trigger → Docker image build → Artifact Registry → Cloud Run deploy
                                                                                          ↓
                                                                          Flask app hívja a Vertex AI Gemini-t
```

---

## 1. GCP projekt létrehozása

1. Menj a [Google Cloud Console](https://console.cloud.google.com)-ra.
2. Fent, a projektválasztóban kattints **"New Project"**.
3. Adj neki nevet, pl. `english-coach`. Jegyezd fel a generált **Project ID**-t (ez lesz `YOUR_PROJECT_ID` a további lépésekben — nem feltétlenül egyezik a névvel).
4. Győződj meg róla, hogy van hozzá **billing account** rendelve (Cloud Run és Vertex AI billing nélkül nem működik, de van havi ingyenes kvóta, kis használatnál gyakorlatilag nem fog kerülni pénzbe).

## 2. Szükséges API-k bekapcsolása

A Cloud Console-ban, vagy ha van `gcloud` CLI-d telepítve lokálisan:

```bash
gcloud config set project YOUR_PROJECT_ID

gcloud services enable \
  run.googleapis.com \
  cloudbuild.googleapis.com \
  artifactregistry.googleapis.com \
  aiplatform.googleapis.com
```

Ha nincs `gcloud` CLI-d, ugyanezt megteheted a Console-ban: **APIs & Services → Enable APIs and Services**, és keresd meg egyenként: *Cloud Run API*, *Cloud Build API*, *Artifact Registry API*, *Vertex AI API*.

## 3. Artifact Registry repó létrehozása (ide kerülnek a Docker image-ek)

```bash
gcloud artifacts repositories create english-coach \
  --repository-format=docker \
  --location=us-central1 \
  --description="English coach app images"
```

## 4. Kód feltöltése GitHub-ra

Ezt a mappa tartalmát töltsd fel egy **privát** GitHub repóba:

```bash
cd english-coach
git init
git add .
git commit -m "Initial commit: English coach app"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/english-coach.git
git push -u origin main
```

(Ha még nincs GitHub-on létrehozva a repó: GitHub-on jobb felül **+ → New repository**, nevezd el `english-coach`-nak, állítsd **Private**-ra, ne inicializáld README-vel — utána jöhet a fenti push.)

## 5. Cloud Build trigger összekötése a GitHub repóval

1. Cloud Console → **Cloud Build → Triggers**.
2. **Connect Repository** → válaszd a GitHub-ot → jelentkezz be / engedélyezd a Google Cloud Build GitHub appot → válaszd ki az `english-coach` repót.
3. **Create Trigger**:
   - Event: *Push to a branch*
   - Branch: `^main$`
   - Configuration: *Cloud Build configuration file* → `cloudbuild.yaml`
4. Mentsd el.

Mostantól minden `git push` a `main` branch-re automatikusan build-eli és deployolja az appot Cloud Run-ra.

## 6. Jogosultságok

A Cloud Build szolgáltatásfióknak (`YOUR_PROJECT_NUMBER@cloudbuild.gserviceaccount.com`) szüksége van a Cloud Run Admin és a Service Account User szerepkörre:

```bash
PROJECT_NUMBER=$(gcloud projects describe YOUR_PROJECT_ID --format='value(projectNumber)')

gcloud projects add-iam-policy-binding YOUR_PROJECT_ID \
  --member="serviceAccount:${PROJECT_NUMBER}@cloudbuild.gserviceaccount.com" \
  --role="roles/run.admin"

gcloud projects add-iam-policy-binding YOUR_PROJECT_ID \
  --member="serviceAccount:${PROJECT_NUMBER}@cloudbuild.gserviceaccount.com" \
  --role="roles/iam.serviceAccountUser"

gcloud projects add-iam-policy-binding YOUR_PROJECT_ID \
  --member="serviceAccount:${PROJECT_NUMBER}@cloudbuild.gserviceaccount.com" \
  --role="roles/aiplatform.user"
```

## 7. Első push → automata deploy

```bash
git add .
git commit -m "trigger deploy"
git push
```

Nézd meg a **Cloud Build → History**-ban, hogy lefut-e a build. Ha zöld pipa, a **Cloud Run** oldalon meg fogod találni az `english-coach` szolgáltatást, és ott lesz egy publikus URL (pl. `https://english-coach-xxxxx-uc.a.run.app`).

## 8. Tesztelés és Web UI használata

### Webes Felület
Nyisd meg a Cloud Run szolgáltatás URL-jét a böngésződben (pl. `https://english-coach-xxxxx-uc.a.run.app`).
Az alkalmazás egy interaktív Web UI-t biztosít az alábbi funkciókkal:
- **Témaválasztó:** Gyorsindító témák (Daily Standup, DevOps, Cloud, Docker, Sysadmin, Enterprise AI, Állásinterjú).
- **Text-to-Speech (TTS):** A coach válaszainak hangos felolvasása angolul.
- **Beszédfelismerés (STT):** Mikrofon alapú beszédbevitel.
- **Munkamenet törlése:** Új beszélgetés indítása.

### API Tesztelés (`curl`)
```bash
curl -X POST https://YOUR_CLOUD_RUN_URL/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Hi! I would like to practice a daily standup conversation.", "session_id": "my-session-1"}'
```

## Lokális futtatás & Unit Tesztek

```bash
cd app
pip install -r requirements.txt
export GCP_PROJECT_ID=YOUR_PROJECT_ID
export GCP_LOCATION=us-central1
export MODEL_NAME=gemini-2.5-flash
gcloud auth application-default login   # lokális hitelesítéshez
python main.py
```

### Unit tesztek futtatása:
```bash
python3 -m unittest discover -s app -p "test_*.py"
```

Ezután a `http://localhost:8080` címen eléred a webes felületet, a `http://localhost:8080/chat` végponton pedig a REST API-t.

## Következő lépések (ha később bővítenéd)

- **Firestore**: a jelenlegi memóriában tárolt beszélgetés-history elveszik minden újraindításkor. Firestore-ral perzisztens lenne, session-ök között is megmaradna.
- **Autentikáció**: jelenleg `--allow-unauthenticated` van beállítva, tehát bárki elérheti az URL-t, ha megtalálja. Személyes projektként egyelőre elfogadható, de ha publikálod valahol az URL-t, érdemes lesz auth-ot rátenni.

