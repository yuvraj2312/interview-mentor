# Deployment Guide (Beta Hardening — Tier 1 & 2)

Scope: the minimum bar to run Interview Mentor outside your own machine, with
real people's real resume data, for a small private beta (a handful of
trusted users). This is explicitly **not** the full Phase 10 production
hardening pass (`docs/architecture.md` §11) — no load testing, no formal
privacy policy, no enterprise secrets management. Revisit this document when
you outgrow beta scale.

## 1. Required environment variables

Every variable below with **no default** will fail application startup if
unset — that's intentional (see `backend/app/core/config.py`'s `Settings`
class). Nothing silently falls back to a real, working-but-insecure value.

| Variable | Required? | Notes |
|---|---|---|
| `ENVIRONMENT` | Recommended | Set to `production`. Unlocks the CORS validation in §2. Defaults to `development`. |
| `DATABASE_URL` | **Required, no default** | `postgresql+psycopg2://user:pass@host:5432/dbname` |
| `ANTHROPIC_API_KEY` | **Required, no default** | From the Anthropic Console. See §6 for spend-limit guidance. |
| `ANTHROPIC_MODEL` | No (has default) | `claude-haiku-4-5` |
| `JWT_SECRET_KEY` | **Required, no default** | See §1a — generate a new one, never reuse the dev value. |
| `CORS_ORIGINS` | **Required in production** | See §2. JSON array string, e.g. `["https://app.yourdomain.com"]`. |
| `REDIS_URL` | No (has default) | Must point at a real Redis instance in production; also backs the rate limiter (§3). |
| `MINIO_ENDPOINT_URL` | No (has default) | Point at your real S3-compatible endpoint in production. |
| `MINIO_ACCESS_KEY` | **Required, no default** | Was `"minioadmin"` hardcoded as a fallback in code — fixed; must now be a real credential. |
| `MINIO_SECRET_KEY` | **Required, no default** | Same as above. |
| `MINIO_BUCKET_NAME` | No (has default) | `resumes` |
| `QDRANT_URL` | No (has default) | Point at your real Qdrant instance in production. |
| `SENTRY_DSN` | Optional | See §4. Fully inert (no `sentry_sdk.init()` call at all) if unset. |
| `RATE_LIMIT_LOGIN` / `RATE_LIMIT_SIGNUP` / `RATE_LIMIT_REFRESH` | No (has defaults) | See §3 for the reasoning behind the defaults. |
| `BACKUP_S3_BUCKET` | Required to run the backup script | See §5. Not read by the app itself. |
| `BACKUP_RETENTION_DAYS` | No (default `7`) | See §5. |

### 1a. Generating a production `JWT_SECRET_KEY`

Never reuse the value from your local `.env` — generate a fresh, unique
secret for production:

```bash
python -c "import secrets; print(secrets.token_hex(32))"
# or
openssl rand -hex 32
```

Treat this like any other credential: set it via your host's secret/env-var
manager, never commit it, and rotate it if it's ever exposed (e.g. pasted
into a chat log, a shared terminal, or a support ticket).

### 1b. Secrets audit — what was verified

- Grepped the full codebase (backend + frontend, including `.env.example`
  and committed config) for hardcoded API keys, DB passwords, and JWT
  secrets — none found. `database_url`, `anthropic_api_key`, and
  `jwt_secret_key` already had no code-level fallback.
- Found and fixed one real gap: `minio_access_key`/`minio_secret_key`
  defaulted to the well-known `"minioadmin"`/`"minioadmin"` credential pair
  in code. These are now required env vars with no fallback, matching the
  other secrets.
- Confirmed `backend/.env` is gitignored and has never been committed
  (`git ls-files` shows no tracked `.env`).
- Added `tests/test_config.py`, which directly asserts (via `pytest.raises`)
  that `Settings()` fails to construct without `jwt_secret_key`,
  `minio_access_key`, or `minio_secret_key`, so this can't silently regress.

## 2. CORS

`ENVIRONMENT=production` activates a startup-time validator
(`Settings._validate_production_cors`) that requires `CORS_ORIGINS` to be:

- Explicitly set (no default is used in production)
- Non-empty
- Free of any `localhost`/`127.0.0.1` origin
- Free of a wildcard (`"*"`)

Violating any of these raises a `ValidationError` at startup — the app
refuses to start with an insecure CORS config in production, rather than
starting up wide open. Set it to your exact deployed frontend origin only:

```
CORS_ORIGINS=["https://your-real-frontend-domain.com"]
```

In development, `ENVIRONMENT` defaults to `development` and none of the
above is enforced — `CORS_ORIGINS` falls back to a small hardcoded localhost
list (`5173`–`5175`, covering Vite's auto-increment on port conflicts) if
not set, same as before this change.

**Verified locally**, not just assumed safe because it's dev-only:
- `tests/test_config.py` covers all four production-validation cases
  (missing, empty, localhost, wildcard) plus the accept case.
- With the real local dev backend running (`--reload`, picking up these
  changes live) and the real Vite dev server auto-incrementing to `:5174`
  (because `:5173` was already in use — the exact port-drift scenario this
  fix targets), a real browser login from `:5174` completed a real CORS
  preflight (`OPTIONS /auth/login` → `200`) and a real `POST /auth/login`
  reached the backend (`401`, from a nonexistent test credential — not a
  CORS failure) with no CORS errors in the console.
- `curl`-driven preflight checks confirmed origins `:5173` and `:5174` (the
  ones actually in the dev `.env`) get a proper echoed
  `Access-Control-Allow-Origin`, while `:5175` and `:9999` are correctly
  rejected with `400` and no CORS headers.

## 3. Rate limiting on auth endpoints

`/auth/login`, `/auth/signup`, and `/auth/refresh` are rate-limited per
client IP via `slowapi`, backed by Redis (not in-memory) so the limits hold
correctly even if the app ever runs multiple worker processes.

| Endpoint | Default limit | Reasoning |
|---|---|---|
| `/auth/login` | 10/minute | Generous enough for several legitimate mistyped-password attempts in a burst, while still meaningfully throttling automated brute force (combined with bcrypt's cost factor already making each guess expensive). |
| `/auth/signup` | 5/minute | Legitimate signup is a one-time action per person; lower limit mainly targets automated account-creation spam. |
| `/auth/refresh` | 20/minute | Can fire automatically (token rotation) rather than from direct user action, so it's set higher to avoid false-positives from normal multi-tab/reconnect behavior, while still bounding a runaway refresh loop. |

Override via `RATE_LIMIT_LOGIN` / `RATE_LIMIT_SIGNUP` / `RATE_LIMIT_REFRESH`
(format: `"N/minute"`) if real beta usage shows these are wrong — don't
change them speculatively without evidence.

**Verified**:
- `tests/test_rate_limiting.py` fires repeated rapid requests against
  `/auth/login` and `/auth/signup` and asserts a `429` appears, while the
  first request in each burst still succeeds (confirming normal use isn't
  blocked).
- Confirmed live against the running dev backend: 15 rapid `POST
  /auth/login` attempts returned `401` for the first 10 and `429` for the
  remaining 5.
- Added an autouse fixture (`tests/conftest.py::_reset_rate_limiter`) that
  resets the limiter's Redis-backed state before every test, since without
  it the existing test suite's rapid-fire auth calls (many signup/login
  calls per test run, all from `TestClient`'s fixed IP) would start
  tripping the same limits and failing unrelated tests.

## 4. Error visibility

**Baseline (always on)**: `app/core/logging_config.py` configures
structured, single-line stdout logging (timestamp, level, logger name,
message) at app startup. Any PaaS host (Railway, Render, Fly, Heroku-style)
captures and retains stdout by default, so this alone is enough to inspect
logs after the fact there. It is **not** enough on a bare `docker run` or a
self-managed VM with no logging driver configured — if that's your
deployment target, either configure your container runtime's logging driver
to persist stdout, or add a rotating file handler.

Note this is on top of, not instead of, the LLM call tracing that already
persists every `LLMAdapter.generate()` call (prompt, response, latency,
tokens, cost) to the `llm_calls` table (`app/llm_adapter.py`) — that
requirement was already met before this pass.

**Sentry — recommendation: add it now.** For a beta you can't watch 24/7,
finding out "something broke for my friend at 11pm" via a searchable,
alertable error tracker beats grepping stdout after the fact. The
integration is small (~10 lines, see `app/main.py`) and the free tier (5k
errors/month) comfortably covers a handful of beta users. It's gated
entirely behind `SENTRY_DSN`:

```python
if settings.sentry_dsn:
    import sentry_sdk
    sentry_sdk.init(dsn=settings.sentry_dsn, environment=settings.environment, traces_sample_rate=0.0)
```

No DSN set → the `sentry_sdk` import and `init()` call never happen at all,
not just a disabled/no-op client.

To enable:
1. Create a free Sentry account and a project (platform: Python/FastAPI).
2. Copy the project's DSN.
3. Set `SENTRY_DSN=<your-dsn>` as an environment variable on your host —
   never hardcode it.

## 5. Database backups

`backend/scripts/backup_db.py` runs `pg_dump` (custom format, `-Fc`) against
`DATABASE_URL` and uploads the dump to an S3-compatible bucket, reusing the
app's existing MinIO/S3 credentials. It keeps only the last
`BACKUP_RETENTION_DAYS` days of backups (default 7), pruning older ones
after each successful run.

**Prefer your Postgres host's built-in backups if it has them** — Supabase,
Neon, Railway Postgres, Render Postgres, and RDS all offer automated daily
backups (some with point-in-time recovery) with zero maintenance. Check for
this first; if it's available, enable it and treat the script below as an
optional supplement, not the primary path.

**Otherwise, schedule the script**:

- Set `BACKUP_S3_BUCKET` (a separate bucket/prefix from your resumes
  bucket — don't mix backups into `MINIO_BUCKET_NAME`).
- Self-hosted VM: add a crontab entry, e.g. daily at 3am:
  ```
  0 3 * * * cd /path/to/backend && /path/to/venv/bin/python scripts/backup_db.py >> /var/log/interview-mentor-backup.log 2>&1
  ```
- Platform-native scheduled job (Railway Cron, Render Cron Jobs, etc.): point
  it at `python scripts/backup_db.py` with the same environment variables as
  the main app plus `BACKUP_S3_BUCKET`.
- Avoid exposing a backup-trigger HTTP endpoint — a scheduled job that runs
  the script directly against the database has less attack surface than an
  API route that would need its own auth.

This doesn't need to be sophisticated for beta scale, but losing real users'
data with zero recovery path is not acceptable even at beta scale — hence
it exists at all, not that it's elaborate.

## 6. Cost-cap relationship: app cap vs. Anthropic Console spend limit

These are two independent layers:

- **`interview_session_max_cost_usd`** (default `$2.00`,
  `backend/app/core/config.py`) is a **soft, per-session, in-app** cap,
  enforced in `app/services/interview_session_service.py` — it stops a
  single interview session from running away in cost (e.g. a stuck loop or
  pathological conversation), independent of how many sessions exist.
- **The Anthropic Console spend limit** is a **hard, account-wide,
  all-sessions, all-users** cap. It's your last line of defense against
  anything the per-session cap doesn't catch — a bug that bypasses the
  check, a leaked API key, or simply more concurrent sessions than expected.

They don't substitute for each other: the per-session cap bounds any single
session; the Console limit bounds your total exposure regardless of cause.

**Recommended Console monthly spend limit for beta**: **$25–$40**, with a
billing alert at **$10** for early warning.

Reasoning: for a handful of friends doing occasional sessions, even a
pessimistic estimate (every session hitting the full $2.00 cap, a handful of
users doing a few sessions per week) lands around $20–40/month — real
sessions will typically cost far less than the cap (the cap is a ceiling
against runaway behavior, not the expected cost). A $25–40 hard limit gives
headroom for legitimate use while still being a real backstop, and the $10
alert gives you a chance to investigate before you're anywhere near the hard
cutoff.

Configure both at <https://console.anthropic.com> (Console-level settings —
outside this codebase, no code change here).

## 7. Health check

`GET /health` (`backend/app/api/health.py`) checks the API itself, a
lightweight Postgres query (`SELECT 1`), and Redis (`PING`). No auth
required — point your host's uptime monitor or load balancer health check at
it. Returns `200` with `{"status": "ok", "database": "ok", "redis": "ok"}`
when everything is healthy, or `503` with the failing component(s) marked
`"error"` otherwise. A failed check is also logged (`app.api.health`
logger), so a 503 shows up in whatever's watching stdout (§4), not just in
whatever's polling the endpoint.

**Verified**: `backend/tests/test_health.py` covers the healthy case and a
simulated failure of each dependency independently. Confirmed live against
a real running instance too — stopping the Postgres/Redis containers
individually while the app was up produced the expected `503` and
per-component detail, and both recovered to `200` once the container was
back.

## 8. Resume upload size limit

Resume uploads are capped at **10MB** (`resume_max_upload_bytes`,
`backend/app/core/config.py`), matching the limit already shown in the
frontend's upload hint. Real resumes — even multi-page PDFs with an
embedded photo — are almost always a few MB at most; 10MB gives headroom
without being unbounded. Enforced both client-side (immediate rejection,
no network round-trip) and server-side (`413` with a clear message) —
never rely on the frontend check alone, since it's trivially bypassed.

One caveat worth knowing if you revisit this: the server-side check runs
*after* the file is fully received (FastAPI/Starlette buffer the entire
multipart body before your endpoint code runs at all, for any
`UploadFile`-typed parameter — there's no framework-level setting that
changes this). So it bounds what gets stored and processed, not the
receive-time memory/disk cost of a very large request body. This is
accepted as fine for beta scale (every upload endpoint already requires
login, so there's no anonymous DoS surface), not silently ignored — a true
pre-receipt cap would need hand-rolled ASGI middleware, which isn't
justified yet.

**Verified**: `backend/tests/test_resumes.py` asserts a `413` on an
oversized upload with no hang. Confirmed live too — a real 10MB+1 byte
upload via a running instance returned `413` with the expected message.

## 9. Environment separation discipline

Now that secrets and config are entirely environment-variable-driven (§1,
§2), the main remaining risk is a *process* one: mixing up which
environment you're actually pointed at.

**Checklist**:
- Keep local dev's `.env` and the beta deployment's environment variables
  **completely separate** — never copy a production value into your local
  `.env` "just to test something," even temporarily. If you must inspect
  production data, do it through the hosting platform's own console/CLI,
  not by pointing your local app at it.
- If you ever run a local dev instance and are also connected to the beta
  deployment's infrastructure (e.g. a DB admin tool) at the same time,
  label things clearly (terminal tab titles, browser profile/window) so
  it's never ambiguous which one you're looking at.
- Treat `ENVIRONMENT=production` as a real switch, not a formality — it's
  what unlocks the CORS (§2) and host (below) validation. Don't set it
  locally "to test the validators" without also setting real production
  values for everything it now requires, or startup will (correctly) fail.

**Two safeguards are built in, covering the two different failure
directions**:

1. **Local dev accidentally pointed at the production DB/Redis** — a
   validator can't catch this (a real production URL looks legitimate from
   a dev machine too). Instead, `backend/app/main.py` logs one line at
   every startup: `startup environment=<...> database=<host>/<dbname>
   redis=<host>` — deliberately never the credentials, just enough to
   glance at the log and confirm you're pointed where you think you are.
   **Verified**: confirmed live — the line appears on every boot, correctly
   showing `localhost` in dev.
2. **Production accidentally left pointed at a forgotten local DB/Redis** —
   `Settings._validate_production_hosts` (`backend/app/core/config.py`,
   alongside the existing CORS validator) rejects a `DATABASE_URL` or
   `REDIS_URL` containing `localhost`/`127.0.0.1` when
   `ENVIRONMENT=production`, failing startup loudly instead of silently
   running against the wrong database. **Verified**:
   `backend/tests/test_config.py` covers both the rejection and the
   accepts-real-values case.
