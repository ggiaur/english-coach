# Runtime lesson-state persistence setup

The app can persist lesson progress in Firestore. If Firestore is unavailable, it safely falls back to in-memory state, but that fallback does **not** survive a Cloud Run instance restart.

## One-time Google Cloud setup

Enable Firestore and create the default Standard / Native mode database if the project does not already have one:

```bash
gcloud services enable firestore.googleapis.com

gcloud firestore databases create \
  --database='(default)' \
  --location=us-central1 \
  --edition=standard \
  --type=firestore-native
```

If the default database already exists, do not run the create command again.

## Cloud Run service identity

The Cloud Run service identity must have permission to read and write Firestore. Grant the minimum role required by the app to the service account used by the `english-coach` Cloud Run service. A typical role for application read/write access is:

```text
roles/datastore.user
```

Use the actual service account attached to the Cloud Run service; do not assume a particular account name.

## Runtime configuration

`cloudbuild.yaml` sets:

```text
STATE_BACKEND=auto
```

Behavior:
- if `GCP_PROJECT_ID` is available and Firestore works, lesson state is persisted in Firestore;
- if Firestore cannot be used, the process logs a warning and falls back to in-memory state.

The collection defaults to:

```text
english_coach_sessions
```

Override it with `STATE_COLLECTION` if needed.

## What is persisted

For each browser/session ID the app stores:
- exact lesson phase,
- topic,
- practical situation,
- target chunks,
- core story text,
- understood chunks,
- active chunks,
- recurring errors,
- pronunciation issues,
- next priorities.

This is what allows the tutor to resume the lesson instead of asking the learner what comes next.
