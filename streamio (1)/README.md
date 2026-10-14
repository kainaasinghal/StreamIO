# Streamio Streaming Platform Management System

This project keeps the existing React/Vite interface and adds a FastAPI backend backed by MySQL. The supplied normalized dataset is under the sibling `streamio_dataset/final_pkg` folder.

## Project layout

- `src/main.jsx`, `src/styles.css`: existing React shell, navigation, and visual system.
- `src/DatabasePages.jsx`, `src/api.js`, `src/database.css`: database-backed dashboard and management screens.
- `backend/app`: FastAPI configuration, SQLAlchemy models, validation schemas, and REST routes.
- `backend/.env`: local MySQL settings; fill in your own MySQL username and password.
- `backend/.env.example`: safe configuration template.
- `database/schema.sql`: non-destructive MySQL database/table creation script.
- `database/import_data.py`: repeatable, transactional CSV import script.
- `streamio_dataset/final_pkg/csv`: source data used by the importer.

## Database design

The schema contains nine normalized tables: `user`, `plan`, `category`, `content`, `subscription`, `payment`, `watchlist`, `watch_history`, and `review`. Users have subscriptions to plans; subscriptions own payments; content belongs to a category; watchlists, watch history, and reviews link users to content. The watchlist and review pairs have uniqueness constraints. Foreign keys and indexes support those relationships and the dashboard queries.

The supplied `streaming_platform_final.sql` begins with `DROP DATABASE IF EXISTS`. Do not run that file for setup because it deletes an existing database. Use `database/schema.sql`, which uses `CREATE DATABASE IF NOT EXISTS` and `CREATE TABLE IF NOT EXISTS` and does not drop data.

## Requirements

- Windows 10/11
- MySQL Server 8.x, with a MySQL account that can create/use `streaming_platform_db`
- Node.js LTS and npm
- Python 3.10 or newer
- MySQL Workbench (optional, for the GUI schema setup and verification)

## 1. Check MySQL Server

In PowerShell, from any directory:

```powershell
Get-Service MySQL80
Test-NetConnection 127.0.0.1 -Port 3306
```

If the service is stopped, open PowerShell as Administrator and run:

```powershell
Start-Service MySQL80
```

You can also start it from `services.msc`. A successful TCP check only proves that a server is listening; it does not verify your MySQL credentials.

## 2. Create the schema in MySQL Workbench

1. Open MySQL Workbench and connect to your local MySQL Server (usually `localhost`, port `3306`) using credentials you already configured.
2. Open `database/schema.sql` from this project with **File > Open SQL Script**.
3. Execute the script with the lightning-bolt button. It creates/selects `streaming_platform_db` and creates the nine tables without deleting existing data.
4. Refresh the **SCHEMAS** panel. Expand `streaming_platform_db > Tables` and confirm the nine table names above.

If Workbench reports access denied or cannot connect, resolve that account/service issue in MySQL first. This project does not set, reset, or assume a MySQL password.

## 3. Configure database credentials

The local `backend/.env` is excluded from Git. Open it and replace both placeholders with the username and password for your MySQL account. Do not paste credentials into source files or commit `.env`.

For a fresh checkout, from the project root:

```powershell
cd ".\streamio (1)\backend"
if (-not (Test-Path .env)) { Copy-Item .env.example .env }
notepad .env
```

`DB_HOST`, `DB_PORT`, and `DB_NAME` default to local MySQL on port `3306` and the schema created above. `FRONTEND_ORIGINS` defaults to the existing Vite origin on port `3000`.

## 4. Install backend dependencies and import the dataset

From the project root:

```powershell
cd ".\streamio (1)\backend"
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe ..\database\import_data.py
```

The importer reads the supplied sibling `streamio_dataset/final_pkg/csv` files in foreign-key order, commits them as one transaction, and prints both processed rows and database counts. It can be rerun without duplicating primary-key rows; duplicate rows already in the database are left unchanged. Set `STREAMIO_CSV_DIR` in the environment if you moved the dataset.

Expected source rows are: 12 users, 3 plans, 9 categories, 30 content records, 10 subscriptions, 12 payments, 15 watchlist entries, 12 watch-history entries, and 9 reviews. The test suite verifies the source CSV counts, but the database counts are only known after the importer completes successfully.

## 5. Start the backend

In the same `backend` directory, run:

```powershell
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Keep this terminal open. The database health endpoint is `http://127.0.0.1:8000/api/health`; interactive API docs are at `http://127.0.0.1:8000/docs`.

## 6. Install and start the frontend

Open a second PowerShell terminal and run:

```powershell
cd "C:\Users\frien\Downloads\rdbms project\streamio (1)"
npm install
npm run dev
```

Open `http://localhost:3000`. If Node.js/npm is not installed, install the current Node.js LTS release, reopen VS Code, and rerun the commands above. The client defaults to `http://127.0.0.1:8000/api`; to use a different API URL, create `streamio (1)/.env.local` with `VITE_API_URL=http://127.0.0.1:8000/api` and restart Vite.

## API routes

- `GET /api/health`: database connectivity check.
- `GET /api/dashboard`: actual member, catalog, subscription, payment, rating, category, and viewing aggregates.
- `GET /api/meta/options`: related-record choices for forms.
- `GET /api/{users|plans|categories|content|subscriptions|payments|watchlist|watch-history|reviews}`: search (`q`), filter, sort (`sort_by`, `descending`), and paginate (`page`, `page_size`) records.
- `GET`, `POST`, `PUT`, and `DELETE /api/{resource}/{id}`: read and mutate individual records. Writes use validated payloads and report missing records or relational conflicts with standard HTTP errors.

The Users, Content, Subscription, Payment History, Watch History, and Reviews screens use those endpoints. Dashboard cards and charts query database aggregates. Device types, passwords, session timestamps, and other fields absent from the supplied schema are not fabricated for display.

## Tests

From the project root, after creating the backend virtual environment and installing dependencies:

```powershell
$env:PYTHONPATH = "$PWD\streamio (1)\backend"
& ".\streamio (1)\.venv\Scripts\python.exe" -m unittest discover -s ".\streamio (1)\backend\tests" -v
```

The suite runs without database credentials and checks models, query compilation, OpenAPI routes, request validation, and dataset CSV counts. Database persistence, import counts, CRUD round trips, and frontend rendering require your MySQL credentials and Node/npm and must be verified after setup.

## Troubleshooting

- **MySQL connection refused:** check `Get-Service MySQL80` and `Test-NetConnection 127.0.0.1 -Port 3306`; start MySQL Server if stopped.
- **Access denied / API returns 503:** verify `DB_USER` and `DB_PASSWORD` in `backend/.env`, account permissions, host, port, and schema name. Restart Uvicorn after changing `.env`.
- **Unknown database/table:** run `database/schema.sql` in Workbench, then run the CSV importer.
- **Duplicate entry or foreign-key error during import:** confirm the schema is the one in this project and that no incompatible rows were manually inserted. The import rolls back the complete batch on an error.
- **Python package/import error:** activate/use the project `.venv` and rerun `python -m pip install -r requirements.txt` from `backend`.
- **`npm` is not recognized:** install Node.js LTS, reopen the terminal, then run `npm install`.
- **Vite port conflict:** Vite may select another port; add that exact origin (for example `http://localhost:3001`) to `FRONTEND_ORIGINS` in `backend/.env` and restart Uvicorn.
- **CORS error:** make sure the browser origin exactly matches one of the comma-separated `FRONTEND_ORIGINS` entries and restart the backend.
- **API URL error:** verify the backend is listening at port `8000`; set `VITE_API_URL` in the frontend `.env.local` only if using another address.