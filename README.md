# Hamster (Inventory and Sales Management System — FastAPI Scaffold)

A clean-architecture oriented project scaffold for an inventory and sales management system.

## Tech Stack
- Python 3.13
- FastAPI
- SQLAlchemy
- PostgreSQL (via Docker Compose locally; any managed Postgres in the cloud)
- Alembic
- Pydantic
- Jinja2 templates

## Python Version Notice (Important)

This project is intentionally pinned to **Python 3.13**.

We tested this codebase on Python 3.14 and found compatibility problems with parts of the dependency/tooling stack used here (runtime and test ecosystem). To keep local development and CI stable, we standardized on 3.13.

Practical impact:
- Use Python **3.13.x** for local setup, tests, and CI jobs.
- Avoid Python 3.14 for this repository until dependencies are fully verified as compatible.
- The repository includes a `.python-version` file to reinforce this version choice.

Quick verification command:

```bash
python --version
```

Expected output should begin with `Python 3.13`.

## Database (PostgreSQL)

This project runs on PostgreSQL. Locally it's provisioned via Docker Compose; in the cloud, point `DATABASE_URL` at any managed Postgres instance (RDS, Supabase, Neon, Render, etc.) — no code changes required.

1. Copy the env file and adjust if needed:

   ```bash
   cp .env.example .env
   ```

2. Start Postgres:

   ```bash
   docker compose up -d
   ```

3. Apply migrations (schema is owned by Alembic, not `create_all`):

   ```bash
   source .venv/bin/activate && alembic upgrade head
   ```

4. Run the app as usual (see below). Demo data seeds automatically on first startup if the database is empty.

### Creating new migrations

After changing a model in `app/models/`, generate a migration and review it before applying:

```bash
alembic revision --autogenerate -m "describe the change"
alembic upgrade head
```

## Architecture Overview
This scaffold follows clean architecture principles by organizing responsibilities into layers:
- Routers: HTTP and REST endpoint definitions
- Schemas: API contracts and validation models
- Services: application use-case orchestration
- Models: persistence entities
- Database: engine and session management

Dependency direction is intended to be:
`routers -> services -> models/database`

## Project Structure

```text
app/
  core/
  database/
  models/
  routers/
  schemas/
  services/
  static/
  templates/
tests/
```

## Run Locally

1. Install Python 3.13.

   **macOS (Homebrew)**

   ```bash
   brew update
   brew install python@3.13
   ```

   **Ubuntu / Debian**

   ```bash
   sudo apt update
   sudo apt install -y software-properties-common
   sudo add-apt-repository -y ppa:deadsnakes/ppa
   sudo apt update
   sudo apt install -y python3.13 python3.13-venv python3.13-dev
   ```

   **Fedora**

   ```bash
   sudo dnf install -y python3.13
   ```

   **Windows (winget)**

   ```powershell
   winget install -e --id Python.Python.3.13
   ```

2. Create and activate a Python 3.13 virtual environment.

   **Windows**

   ```bash
   py -3.13 -m venv .venv
   .venv\Scripts\activate
   ```

   **macOS / Linux**

   ```bash
   python3.13 -m venv .venv
   source .venv/bin/activate
   ```

   Once activated, your terminal should display the virtual environment name (e.g., `(.venv)`), indicating that all dependencies will be installed in an isolated environment.

3. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

4. Run the application:

   ```bash
   uvicorn app.main:app --reload
   ```

   Or run it directly with Python:

   ```bash
   python -m app.main
   ```

## Quick Setup Scripts (Near One-Step)

The following scripts install common prerequisites, set up Python 3.13, create a virtual environment, and install project dependencies.

### macOS (bash)

```bash
#!/usr/bin/env bash
set -euo pipefail

if ! command -v brew >/dev/null 2>&1; then
  echo "Homebrew is required. Install it from https://brew.sh and rerun."
  exit 1
fi

brew update
brew install python@3.13 git

python3.13 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt

echo "Setup complete. Run: source .venv/bin/activate && uvicorn app.main:app --reload"
```

### Ubuntu / Debian (bash)

```bash
#!/usr/bin/env bash
set -euo pipefail

sudo apt update
sudo apt install -y software-properties-common git curl
sudo add-apt-repository -y ppa:deadsnakes/ppa
sudo apt update
sudo apt install -y python3.13 python3.13-venv python3.13-dev

python3.13 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt

echo "Setup complete. Run: source .venv/bin/activate && uvicorn app.main:app --reload"
```

### Windows (PowerShell)

```powershell
$ErrorActionPreference = "Stop"

winget install -e --id Python.Python.3.13

py -3.13 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt

Write-Host "Setup complete. Run: .\.venv\Scripts\Activate.ps1; uvicorn app.main:app --reload"
```

Tip: You can copy each block into files like `scripts/setup-macos.sh`, `scripts/setup-ubuntu.sh`, and `scripts/setup-windows.ps1` and run them directly.

## Testing Environment

This project uses `pytest` as the primary test runner with API, unit, and negative-case coverage.

### Installation

1. Activate the project virtual environment.

    **Windows**

    ```bash
    .venv\Scripts\activate
    ```

    **macOS / Linux**

    ```bash
    source .venv/bin/activate
    ```

2. Install all dependencies (including test tools):

    ```bash
    pip install -r requirements.txt
    ```

Test tooling included in the project:
- `pytest`
- `pytest-asyncio`
- `pytest-cov`
- `httpx`

### Running Tests

Run the entire test suite:

```bash
source .venv/bin/activate && pytest -q
```

Run only API integration tests:

```bash
source .venv/bin/activate && pytest tests/api -q
```

Run only unit service tests:

```bash
source .venv/bin/activate && pytest tests/unit/services -q
```

Run one specific test module:

```bash
source .venv/bin/activate && pytest tests/api/test_products_api.py -q
```

### Coverage

Coverage is configured through `pytest.ini` and `.coveragerc`.

Run tests with terminal coverage + HTML output:

```bash
source .venv/bin/activate && pytest --cov-report=term-missing --cov-report=html -q
```

Run with a minimum coverage threshold (example 85%):

```bash
source .venv/bin/activate && pytest --cov-report=term-missing --cov-report=html --cov-fail-under=85 -q
```

Coverage output locations:
- Terminal summary after test execution
- HTML report at `htmlcov/index.html`

### Test Folder Structure

```text
tests/
   conftest.py                     # shared fixtures: test DB, clients, overrides
   factories.py                    # reusable model and payload builders
   test_health.py                  # basic health endpoint test
   api/
      test_categories_api.py        # categories API integration tests
      test_products_api.py          # products API integration tests
      test_sales_api.py             # sales API integration tests
      test_negative_cases_api.py    # negative and edge-case API scenarios
   unit/
      services/
         test_category_service.py    # CategoryService unit tests
         test_product_service.py     # ProductService unit tests
         test_sale_service.py        # SaleService unit tests
```

### Troubleshooting

#### `pytest: command not found`

- Activate the virtual environment first:

   ```bash
   source .venv/bin/activate
   ```

- Reinstall dependencies:

   ```bash
   pip install -r requirements.txt
   ```

#### Tests fail due to stale environment packages

Reinstall from scratch in the active environment:

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

#### Python 3.14 is active by mistake

Symptoms can include dependency install failures, runtime import issues, or inconsistent test behavior.

Fix:

```bash
python --version
# if not 3.13, recreate venv with Python 3.13
rm -rf .venv
python3.13 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

#### SQLite / test isolation concerns

- Tests use a temporary SQLite database and dependency overrides in `tests/conftest.py`.
- If behavior looks inconsistent, run tests again from a clean process:

   ```bash
   source .venv/bin/activate && pytest -q
   ```

#### Coverage report not generated

- Ensure tests are run with `--cov-report=html`.
- Open `htmlcov/index.html` after execution.

#### Deprecation warnings from async fixtures

- The repository sets `asyncio_default_fixture_loop_scope = function` in `pytest.ini`.
- If warnings still appear, confirm you are running tests from this repository root and active `.venv`.
