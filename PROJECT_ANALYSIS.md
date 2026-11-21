# OceanIQ Project Analysis

## Overview

OceanIQ is a full-stack ocean-data dashboard for querying ARGO float telemetry in natural language. Its focus is Indian Ocean regions, including the Arabian Sea, Bay of Bengal, Laccadive Sea, and Equatorial Indian Ocean.

Users can ask questions such as “temperature trend in the Arabian Sea at 50 m.” The application extracts details from the request, queries stored ARGO measurements, and returns a textual summary, chart data, map points, source IDs, anomaly information, and optional forecasts.

## Main Features

- Natural-language ocean data queries.
- ARGO float, profile, and measurement browsing.
- Charts for time series and depth profiles.
- Map display of float locations.
- Statistical anomaly detection using z-scores.
- CSV export of stored measurements.
- User registration, login, profile editing, and saved queries.
- Background attempts to synchronize live ARGO data from GDAC/ERDDAP.
- Optional local conversational responses through Ollama.

## Technology Stack

| Layer | Actual technology in the codebase |
| --- | --- |
| Frontend | Next.js 14, React 18, Tailwind CSS |
| Visualizations | Plotly, Leaflet, React-Leaflet |
| Backend | FastAPI, Uvicorn, Python |
| Database access | SQLAlchemy async |
| Default database | SQLite (`oceaniq.db`) |
| Optional database container | PostgreSQL/PostGIS through Docker Compose |
| Live data retrieval | `argopy`, xarray, ERDDAP/GDAC |
| Local LLM option | Ollama with `llama3:latest` by default |
| Forecast interface | PyTorch LSTM |

## Architecture

```text
Browser / Next.js frontend
        |
        v
FastAPI API (`/api/v1`)
        |
        +-- Keyword intent classifier
        +-- Regex entity extractor
        +-- SQLAlchemy data query
        +-- Template response generator
        +-- Optional Ollama conversation fallback
        |
        v
SQLite by default / PostgreSQL-PostGIS if configured
        |
        v
ARGO floats -> profiles -> depth measurements
```

## Backend Data Model

The database is built around these tables:

- `argo_floats`: One record per ARGO float, identified by WMO ID.
- `argo_profiles`: Float cycles with date, coordinates, region, and data source.
- `argo_measurements`: Measurements at different pressures/depths: temperature, salinity, oxygen, and chlorophyll.
- `users`: Application users.
- `user_tokens`: Opaque authentication tokens with 30-day expiry.
- `user_saved_queries`: Saved queries for an authenticated user.
- `query_feedback`: User ratings and comments on query quality.

Relevant implementation files:

- `backend/app/main.py`: FastAPI startup, CORS, database-table initialization, router registration.
- `backend/app/api/routes.py`: Data query, profile, export, anomaly, and live-sync routes.
- `backend/app/api/auth_routes.py`: Registration, login, token validation, and user query routes.
- `backend/app/db/models.py`: SQLAlchemy database models.
- `backend/scripts/ingest_argo.py`: Synthetic demonstration-data generator.

## API Endpoints

| Method | Endpoint | Purpose |
| --- | --- | --- |
| POST | `/api/v1/query` | Natural-language ARGO data query |
| GET | `/api/v1/stats` | Dashboard statistics |
| GET | `/api/v1/live/status` | Live synchronization status |
| POST | `/api/v1/live/sync` | Trigger a live data sync |
| GET | `/api/v1/live/floats` | Latest float locations |
| GET | `/api/v1/floats` | All stored floats |
| GET | `/api/v1/floats/{wmo_id}` | One float and recent profiles |
| GET | `/api/v1/profiles` | Profile list with filters |
| GET | `/api/v1/profiles/{profile_id}` | Measurements for one profile |
| GET | `/api/v1/export/csv` | CSV measurement export |
| GET | `/api/v1/anomalies` | Z-score anomalies |
| POST | `/api/v1/feedback` | Store user feedback |
| POST | `/api/v1/auth/register` | Register an account |
| POST | `/api/v1/auth/login` | Log in |
| GET/PUT | `/api/v1/auth/me`, `/api/v1/auth/profile` | Read/update current profile |
| GET/POST/DELETE | `/api/v1/users/me/queries` | Manage saved queries |

## Query Processing Flow

1. The frontend sends the query to `POST /api/v1/query`.
2. The intent classifier selects one of `forecast`, `comparison`, `trend`, or `point_lookup` using keywords.
3. The entity extractor identifies a parameter, region, approximate dates, and depth range using aliases and regular expressions.
4. The SQL builder creates a SQLAlchemy query over ARGO profiles and measurements.
5. The backend calculates min, max, mean, map points, and optional z-score anomalies.
6. Template NLG returns a deterministic response for data queries.
7. Conversational requests can use Ollama if it is enabled and running locally.

## Data Sources

The application has three possible data modes:

1. **Synthetic seed data**: `ingest_argo.py` generates ocean-like values for five example floats. This is suitable for a demo, but is not real observational data.
2. **Cached local data**: The SQLite database in the project root stores profiles and measurements.
3. **Live ARGO data**: The scheduler tries to retrieve recent profiles using `argopy` from ERDDAP/GDAC. If retrieval fails or times out, the app falls back to cached data.

## Documentation vs. Current Implementation

The README describes a larger architecture than is currently implemented.

| Claimed/documented design | Current code behavior |
| --- | --- |
| PostgreSQL/PostGIS as primary runtime DB | SQLite is the default configuration |
| spaCy NER + TF-IDF/SVM classifier | Keyword matching and regex extraction |
| Gemini API fallback | Ollama local-model fallback |
| ChromaDB and sentence-transformer retrieval | Dependencies are listed but not used by the request path |
| Trained, benchmarked LSTM forecast | An LSTM object is created but no training process or model weights are included |
| Alembic migrations | No migration setup is present |
| React/Vite in technical document | The actual frontend is Next.js |

Therefore, the system is best described as a capable demo/prototype with a good architecture direction, rather than a complete production research platform.

## Strengths

- Clear domain model: floats, profiles, and measurements are correctly separated.
- Querying numeric data through SQLAlchemy is safer and more traceable than generating values with an LLM.
- The UI is feature-rich: charts, maps, export, profile explorer, account functions, and saved work.
- Authentication uses bcrypt password hashes and server-side stored tokens.
- Live ingestion gracefully handles unavailable ARGO services.
- The project supports both a simple SQLite demo setup and a future PostgreSQL/PostGIS deployment path.

## Important Issues to Address

### Data correctness and scientific reliability

1. **Date filters are not applied in SQL.** Dates are extracted from user input, but the SQL builder does not filter records by `start_date` or `end_date`.
2. **QC filtering is not implemented.** Responses claim QC=1/good data, but the database query does not filter parameter QC flags.
3. **QC confidence is hard-coded.** The confidence layer receives a `qc_pass_ratio` of `1.0` regardless of actual data.
4. **Forecasts are not scientifically validated.** The LSTM has no saved trained weights or training/evaluation code. RMSE and MAE values are hard-coded.
5. **Synthetic data can be inserted by a normal query.** If no records are found, the query endpoint seeds generated demo data. This should be a separate admin/setup action.
6. **Fallback UI data is fabricated.** When the backend cannot be reached, the frontend shows hard-coded values that could be mistaken for verified telemetry.

### Backend defects and performance

1. **Live-sync float lookup is likely incorrect.** It calls `session.get(ArgoFloat, p['wmo_id'])`, but the primary key is an integer `id`, not `wmo_id`. This can fail to find existing floats and lead to duplicate-key errors.
2. **Data source is not selected in the main query.** The query response can label results as cached even when their actual profile source is live.
3. **Float listing has an N+1 query pattern.** It runs a separate profile-count query for each float; this should be replaced by one grouped query.
4. **Broad exception fallbacks hide failures.** Some endpoints return plausible demo values after any error, making real production failures hard to detect.
5. **No automated test suite was found.** Critical behavior—query filtering, auth, CSV export, live sync, and database constraints—needs tests.

### Security and deployment

1. **CORS allows every origin while credentials are allowed.** Production should explicitly allow only trusted frontend domains.
2. **Users can choose arbitrary roles.** Registration and profile update accept role input, so authorization must be enforced server-side; users should not be able to assign themselves `admin`.
3. **Sensitive operational endpoints are public.** At minimum, live synchronization should be restricted to administrators.
4. **Password rules and rate limiting are absent.** Add minimum password strength, login throttling, and abuse protection.
5. **Tokens are stored in plaintext in the database.** Consider storing token hashes, cleaning expired tokens, and using secure cookie/session handling where appropriate.
6. **Frontend API URLs are hard-coded to localhost.** Use a `NEXT_PUBLIC_API_URL` environment variable for deployment.
7. **Fresh dependency installation may fail.** `bcrypt` and `email-validator` are used/imported but are not explicitly listed in `backend/requirements.txt`.

## Recommended Priorities

1. Make data provenance visible: clearly distinguish **live**, **cached**, **synthetic demo**, and **unavailable** data in every API/UI response.
2. Fix query correctness: implement date filters, region filters from UI controls, depth semantics, and QC filtering.
3. Fix live-sync upserts and add database constraints for unique `(wmo_id, cycle_number)` profiles.
4. Remove automatic seeding from the query endpoint; provide an explicit development-only seed command instead.
5. Replace the untrained LSTM output with either a trained/evaluated model or a clearly labeled baseline forecast.
6. Secure authorization, CORS, role changes, token handling, and sync endpoints.
7. Add automated API and database tests.
8. Introduce environment-specific configuration for frontend API URLs and database connections.
9. Choose and implement one coherent production architecture: SQLite demo mode or PostgreSQL/PostGIS deployment mode.

## Overall Assessment

OceanIQ has a strong project idea, a useful relational model, and a more complete implementation than a typical UI-only prototype. The best current parts are the FastAPI data explorer, profile/measurement structure, visual dashboard, CSV export, and user workspace features.

Before it is presented as a reliable oceanographic research platform, the project needs stronger scientific-data guarantees. In particular, it must correct filtering/QC behavior, make synthetic and fallback data explicit, repair live synchronization, and avoid claiming trained or benchmarked forecasting functionality that is not present in the repository.
