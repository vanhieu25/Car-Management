# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**Car Dealership Management System** — Desktop application for managing a car dealership's operations: vehicles, customers, contracts, warranty, maintenance, marketing, and reporting.

- **Stack**: Python 3.10+ | PyQt6 | SQLite | bcrypt | Jinja2 + WeasyPrint (PDF) | openpyxl (Excel) | pytest
- **Architecture**: Clean Architecture (presentation → application → domain → infrastructure)
- **Language**: Vietnamese UI and documentation

## Commands

```bash
# Run application
python main.py

# Run all tests
pytest tests/ -v

# Run a single test file
pytest tests/path/to/test_file.py -v

# Run a single test
pytest tests/path/to/test_file.py::TestClass::test_method -v

# Run tests matching a marker (see pytest.ini for markers)
pytest tests/ -m simple    # Fast SELECT query tests
pytest tests/ -m wf04 -v  # Workflow 04 warranty tests
pytest tests/ -m perf     # Performance benchmarks

# Format code
black app tests
isort app tests

# Lint
flake8 app tests --max-line-length=88

# Run pre-commit checks
pre-commit run --all-files

## Test Markers

Workflow integration tests:
- `wf01` – Nhập kho (Nhập xe mới)
- `wf02` – Bán xe chuẩn (Mua xe không trả góp)
- `wf03` – Bán trả góp
- `wf04` – Bảo hành
- `wf05` – Bảo dưỡng
- `wf06` – Khiếu nại
- `wf07` – Marketing → Lead → Khách hàng
- `wf08` – Hủy hợp đồng

Performance markers: `simple` (SELECT <50ms), `join_agg` (JOIN <200ms), `report` (<500ms), `perf` (benchmark)

## Architecture

```
app/
├── presentation/     # PyQt6 screens (app/presentation/screens/)
│   └── widgets/      # Reusable UI components
├── application/      # Services - business logic orchestration
│   └── services/     # One service per module (bao_hanh_service.py, etc.)
├── domain/
│   └── entities/    # Dataclasses: NhanVien, Xe, HopDong, BaoHanh, etc.
└── infrastructure/
    ├── database/
    │   ├── migrations/  # Sequential migrations (migration_001_*.py ...)
    │   └── seeds/      # dev_seed.py for sample data
    ├── repositories/   # Data access (base_repository.py + per-entity)
    ├── security/       # password_hasher.py (bcrypt)
    ├── exporters/      # Excel export wrappers
    └── pdf_renderer.py # Jinja2 + WeasyPrint PDF generation
```

**Key patterns:**
- **Entities** (`app/domain/entities/`): `@dataclass` classes with `to_dict()`, `from_row()` — BaseEntity provides id, created_at, updated_at, created_by
- **Repositories** (`app/infrastructure/repositories/`): `BaseRepository` provides standard CRUD; each entity has its own repo extending it
- **Services** (`app/application/services/`): Business logic, validation, cross-entity operations. Named `*_service.py`
- **Sessions**: `SessionManager` + `CurrentSession` in `session.py`; current user accessible via `CurrentSession` singleton

## Database

- **File**: `data/car_management.db` (SQLite)
- **Migrations**: Run automatically on startup via `MigrationRunner`. Migrations numbered sequentially (`migration_001_*.py` → `migration_030_*.py`). Add new migration as `migration_031_*.py` — each migration must have an `upgrade()` function
- **Seed**: `dev_seed.py` auto-runs if `nhan_vien` table is empty; default login: `admin` / `password123`
- **Connection**: `get_connection()` from `app.infrastructure.database.connection`; foreign_keys ON by default

## Business Rules Reference

Core business rules are documented in `docs/BUSINESS_REQUIREMENTS.md`. Key coding standards:
- `BR-CALC-*`: Financial formulas (contract total, customer classification, installment calculation) — must have unit tests
- `BR-SEC-*`: Security rules (bcrypt cost ≥12, password ≥8 chars, 5-fail lockout, 30-min session)
- `BR-FLOW-*`: State machines (contract: `moi_tao → da_thanh_toan → da_giao_xe / huy`)
- `BR-TIME-*`: Time rules (BH 30-day warning, BD 7-day reminder, 5-day late installment)

## UI Conventions

- Screens in `app/presentation/screens/` named `*_screen.py` (list) or `*_dialog.py` (modal form)
- Main window layout: `MainWindow` → `TopBar` + `Sidebar` + `ContentArea` + `StatusBar`
- Role-based access: `vai_tro.ma_vai_tro` = `A-01` (admin), `A-02` (sales), `A-03` (ky_thuat)
- Status badges use color coding per `StatusBadge` component

## PDF & Export

- Contract/warranty PDFs: `PdfRenderer` uses Jinja2 templates in `resources/templates/` + WeasyPrint
- Reports: `ExcelExporter` in `app/infrastructure/exporters/` uses openpyxl

## Shared Utilities

- `app/shared/constants.py`: Business constants (status values, role codes, etc.)
- `app/shared/logger.py`: Application logging
- `app/shared/db_utils.py`: Database utilities
