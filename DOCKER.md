# DOCKER.md — telepítés a saját Docker-környezetben (magyarul)

Mit kapsz: a `web` konténer (az app, a `/learn` oldalak, a `/progress` oldal) és a `tts` konténer (Piper, ingyenes helyi felolvasó). A hang a te gépeden készül, a szöveg nem megy ki sehova. Az egész **jelszóval** védhető.

## Indítás

1. `cp .env.example .env`, majd írd be: `APP_PASSWORD` (hosszú jelszó) és `FLASK_SECRET_KEY` (véletlen szöveg). A felhasználónév alapból `bj`.
2. `docker compose up -d --build`. Az első építésnél a `tts` konténer letölti a hangot (kb. 60 MB), ehhez internet kell.
3. Próba: `http://127.0.0.1:8080/learn/` — böngészőablak kéri a felhasználónevet és jelszót.

## Reverse proxy

A `web` csak a gép saját címén (`127.0.0.1:8080`) hallgat. A proxy erre mutasson, és a **HTTPS-t a proxy intézze**, mert a jelszó különben titkosítás nélkül megy. Példák:

- Caddy: `english.pelda.hu { reverse_proxy 127.0.0.1:8080 }`
- Nginx: `location / { proxy_pass http://127.0.0.1:8080; proxy_set_header Host $host; proxy_set_header X-Forwarded-Proto $scheme; }`
- Traefik: címkékkel a `web` szolgáltatásra, 8080-as port.

## Mi működik Google nélkül

| Rész | Google kell? |
|------|--------------|
| `/learn` (János 9, kártyák, tankönyv) | nem |
| `/progress` (heti terv, dalok, pipák) | nem |
| Felolvasás (Piper) | nem |
| Chat-tutor a `/` oldalon (Gemini) | igen (`GCP_PROJECT_ID` és hitelesítés) |

A chat-tutor nélkül a többi teljes értékű. Ha később kell, a `.env`-ben add meg a projektet, és csatold fel a szolgáltatásfiók kulcsát (volume).

## Hang

- A lejátszó gombok a `/tts` útvonalat hívják, az a Piper konténerhez fordul.
- Ha a Piper nem elérhető, a böngésző saját hangja szól (rosszabb minőségű).
- Három sebesség: `slow`, `medium`, `natural`. A „4 sebesség” gomb sorban lejátssza: lassú, lassú, közepes, természetes.
- Más hang: `docker compose build --build-arg VOICE=en_GB-alan-medium tts`. A hangok listája: a Piper hangtárban (rhasspy/piper-voices).

## Jelszó

- `APP_PASSWORD` beállítva: minden oldal (az `/health` kivételével) HTTP Basic jelszót kér.
- Nincs beállítva: nincs védelem (így fut most a Cloud Run-os változat is). A nyilvános domainre mindig állítsd be.
- A haladás pipái a böngészőben vannak, a szerveren nem tárolódik semmi.

## Állapot

A `docker-compose.yml` szintaxisát ellenőriztem (`docker compose config`). Az image-ek építése és a Piper hang letöltése itt nem futott le (nincs elérhető Docker-szolgáltatás), ezért az első `docker compose up -d --build` az éles próba. A jelszó, a `/tts` proxy és az oldalak egységtesztekkel ellenőrzöttek.
