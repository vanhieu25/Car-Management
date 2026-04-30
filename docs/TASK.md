# TASK BREAKDOWN — Phần mềm Quản lý Đại lý Xe hơi

> **Phiên bản:** 1.0 — Tài liệu task chi tiết để hoàn thành toàn bộ kế hoạch tại `PLAN.md`.
>
> **Cấu trúc:** 6 Phase (G1–G6) → 23 Sprint → ~480 task. Mỗi Sprint tuân thủ workflow chuẩn:
>
> ```text
> Requirements → Database → Backend → UI → Testing → Git Workflow
> ```

---

## MỤC LỤC

1. [Tổng quan dự án](#1-tổng-quan-dự-án)
2. [Quy ước & Ký hiệu](#2-quy-ước--ký-hiệu)
3. [Workflow chuẩn cho mỗi Sprint](#3-workflow-chuẩn-cho-mỗi-sprint)
4. [Phase G1 — Khởi tạo dự án](#4-phase-g1--khởi-tạo-dự-án)
5. [Phase G2 — Nền tảng hệ thống](#5-phase-g2--nền-tảng-hệ-thống)
6. [Phase G3 — Nghiệp vụ lõi](#6-phase-g3--nghiệp-vụ-lõi)
7. [Phase G4 — Module mở rộng](#7-phase-g4--module-mở-rộng)
8. [Phase G5 — Module bổ sung & Báo cáo](#8-phase-g5--module-bổ-sung--báo-cáo)
9. [Phase G6 — Hoàn thiện & Bàn giao](#9-phase-g6--hoàn-thiện--bàn-giao)
10. [Phụ lục A — Git Workflow chuẩn](#phụ-lục-a--git-workflow-chuẩn)
11. [Phụ lục B — Definition of Done (DoD)](#phụ-lục-b--definition-of-done-dod)
12. [Phụ lục C — Ma trận RACI](#phụ-lục-c--ma-trận-raci)

---

## 1. TỔNG QUAN DỰ ÁN

| Hạng mục | Giá trị |
| --- | --- |
| **Tổng số Phase** | 6 (G1 → G6) |
| **Tổng số Sprint** | 23 |
| **Số module nghiệp vụ** | 15 |
| **Số màn hình UI** | 42 (`S-XXX-NN`) |
| **Số bảng CSDL** | 25 |
| **Số Business Rule** | ~58 tổng thể + 124 module |
| **Số Use Case** | ~50 (`UC-XX-NN`) |
| **Số Workflow E2E** | 8 (`WF-01..08`) |
| **Số Báo cáo** | 7 (`RP-01..07`) |
| **Tech stack** | Python 3.10+, PyQt6, SQLite, bcrypt, Jinja2+WeasyPrint, openpyxl, pytest, PyInstaller |
| **Nhóm phát triển** | 3 thành viên (Trưởng nhóm + 2 thành viên) |

### Lộ trình cấp Phase

| Phase | Tên | Sprint | Module BRD | Sản phẩm chính |
| --- | --- | :---: | --- | --- |
| **G1** | Khởi tạo | 1 | — | Repo + skeleton + CI |
| **G2** | Nền tảng | 4 | NV (1 phần), SEC | Schema 25 bảng, Auth, Layout, Audit log |
| **G3** | Nghiệp vụ lõi | 5 | XE, KH, NV, KHO, HD | 5 module CRUD + HĐ wizard 4 bước + PDF |
| **G4** | Mở rộng | 5 | PK, KM, BH, NCC, TG | 5 module + WF-01..04 |
| **G5** | Bổ sung | 4 | HM, MK, KN, BC | 4 module + Dashboard + 7 báo cáo |
| **G6** | Hoàn thiện | 4 | Tất cả | SIT, hardening, đóng gói `.exe`, tài liệu |

---

## 2. QUY ƯỚC & KÝ HIỆU

### 2.1 Mã task

```text
T-<PHASE>.<SPRINT>.<STEP>.<NN>
   │         │         │     │
   │         │         │     └─ Số thứ tự task trong step (01..NN)
   │         │         └─────── Bước workflow (REQ/DB/BE/UI/TEST/GIT)
   │         └───────────────── Sprint số trong phase
   └─────────────────────────── Phase G1..G6

Ví dụ: T-G3.1.BE.03 = Phase G3, Sprint 1 (Module Xe), bước Backend, task số 3
```

### 2.2 Bước workflow (mã `STEP`)

| Mã | Tên | Mô tả |
| --- | --- | --- |
| **REQ** | Requirements | Đọc BRD, làm rõ nghiệp vụ, xác nhận AC, tạo task chi tiết |
| **DB** | Database | Migration, schema, index, trigger, seed |
| **BE** | Backend | Models, repository, service (business logic), validation |
| **UI** | UI (PyQt6) | Form, list, dialog, navigation, theme |
| **TEST** | Testing | Unit test, integration test, manual UAT theo AC |
| **GIT** | Git Workflow | Branching, commit, PR, code review, merge, tag |

### 2.3 Ký hiệu khác

| Ký hiệu | Ý nghĩa |
| --- | --- |
| `[ ]` / `[x]` | Trạng thái task: chưa làm / đã hoàn thành |
| `(2h)` / `(0.5d)` / `(1d)` | Estimate (giờ hoặc ngày) |
| `→ BR-XX-NN` | Tham chiếu Business Rule trong BRD |
| `→ UC-XX-NN` | Tham chiếu Use Case trong BRD |
| `→ S-XXX-NN` | Tham chiếu màn hình trong UI/UX Plan |
| `→ WF-NN` | Tham chiếu Workflow E2E |
| `→ AC-XX-NN` | Tham chiếu Acceptance Criteria |
| `[BLOCKER]` | Task chặn các task khác, ưu tiên cao nhất |
| `[OPT]` | Task tuỳ chọn / có thể hoãn |

### 2.4 Vai trò gán task (RACI)

| Mã | Tên | Phụ trách chính |
| --- | --- | --- |
| **TL** | Trưởng nhóm — Cao Văn Hiếu | Hợp đồng, hệ thống, bảo mật, kiến trúc, code review |
| **DEV-1** | Lê Minh Đạt | Khách hàng, kho, phụ kiện, báo cáo |
| **DEV-2** | Nguyễn Hữu Hải | Bảo hành, khuyến mãi, bảo mật (test), kiểm thử |

---

## 3. WORKFLOW CHUẨN CHO MỖI SPRINT

Mỗi Sprint **PHẢI** đi qua 6 bước theo đúng thứ tự. Không nhảy bước.

```text
┌────────────────────────────────────────────────────────────────────────┐
│  Sprint Workflow (lặp cho mỗi Sprint)                                  │
├────────────────────────────────────────────────────────────────────────┤
│                                                                        │
│   1. REQ   ──►  Đọc BRD §5.X, xác nhận UC, AC, validation rules       │
│       │                                                                │
│       ▼                                                                │
│   2. DB    ──►  Migration script, index, trigger, seed                 │
│       │                                                                │
│       ▼                                                                │
│   3. BE    ──►  Model + Repository + Service + Validator               │
│       │                                                                │
│       ▼                                                                │
│   4. UI    ──►  PyQt6 screen (List, Form, Dialog, Detail)              │
│       │                                                                │
│       ▼                                                                │
│   5. TEST  ──►  Unit test (≥80% LOC service) + Integration + UAT      │
│       │                                                                │
│       ▼                                                                │
│   6. GIT   ──►  PR review → merge `feature/*` → `dev` → tag sprint     │
│                                                                        │
└────────────────────────────────────────────────────────────────────────┘
```

**Quy tắc:**

- **REQ** không đạt → không sang DB.
- **DB** chưa migrate được → không code BE.
- **BE** chưa pass unit test → không build UI.
- **UI** chưa pass UAT → không gộp PR.
- **GIT** kết thúc Sprint với tag `vG<phase>.<sprint>` (vd `vG3.1`).

---

## 4. PHASE G1 — KHỞI TẠO DỰ ÁN

> **Thời gian:** 1 tuần (~5 ngày). **Mục tiêu:** sẵn sàng môi trường để bắt đầu code module nghiệp vụ ở G2.

### Sprint G1.1 — Project Setup & CI/CD

**Mục tiêu:** Repo Git, virtualenv, dependency, project skeleton, CI cơ bản.
**Phụ trách:** TL (lead), DEV-1, DEV-2.

#### REQ — Yêu cầu (0.5 ngày)

- [x] `T-G1.1.REQ.01` (1h) — Đọc và xác nhận `PLAN.md`, `BUSINESS_REQUIREMENTS.md`, `TECH_STACK.md` toàn bộ. **Output:** biên bản họp nội bộ.
- [x] `T-G1.1.REQ.02` (1h) — Quyết định cấu trúc thư mục dự án (Layered Architecture: `presentation / application / domain / infrastructure`).
- [x] `T-G1.1.REQ.03` (1h) — Chốt convention: PEP 8, Black formatter, isort, flake8, pre-commit hooks.
- [x] `T-G1.1.REQ.04` (1h) — Chốt Git workflow: GitFlow (`main` / `dev` / `feature/*` / `release/*` / `hotfix/*`).

#### DB — Cơ sở dữ liệu (N/A bước này)

- [x] `T-G1.1.DB.01` (0.5h) — Tạo thư mục `data/`, `data/backup/` với `.gitkeep`. Thêm `data/*.db` vào `.gitignore`.

#### BE — Backend skeleton (1 ngày)

- [x] `T-G1.1.BE.01` (1h) — Tạo cấu trúc thư mục:

  ```text
  car_management/
  ├── app/
  │   ├── presentation/        # PyQt6 windows, dialogs, widgets
  │   ├── application/         # Service, Use Case orchestrator
  │   ├── domain/              # Entity, Value Object, business rules
  │   ├── infrastructure/      # Repository, DB connection, PDF, Excel
  │   └── shared/              # Utility, helper, constants
  ├── data/                    # SQLite DB + backup
  ├── tests/                   # pytest
  ├── docs/                    # Tài liệu
  ├── design/                  # Design system
  ├── scripts/                 # Build, migration scripts
  ├── resources/               # Icon, logo, qss, jinja2 templates
  ├── main.py                  # Entry point
  ├── requirements.txt
  ├── requirements-dev.txt
  ├── pyproject.toml
  ├── .pre-commit-config.yaml
  ├── .gitignore
  └── README.md
  ```

- [x] `T-G1.1.BE.02` (0.5h) — `requirements.txt`: `PyQt6==6.6.*`, `bcrypt==4.*`, `Jinja2==3.*`, `WeasyPrint==60.*`, `openpyxl==3.*`.
- [x] `T-G1.1.BE.03` (0.5h) — `requirements-dev.txt`: `pytest`, `pytest-qt`, `pytest-cov`, `black`, `isort`, `flake8`, `mypy`, `pre-commit`.
- [x] `T-G1.1.BE.04` (1h) — `pyproject.toml`: cấu hình `black`, `isort`, `pytest`, `coverage`.
- [x] `T-G1.1.BE.05` (1h) — Cấu hình `logging` (file rotating + console) tại `app/shared/logger.py`.
- [x] `T-G1.1.BE.06` (0.5h) — Tạo `app/shared/constants.py`: trạng thái HĐ, vai trò, format ngày/tiền.
- [x] `T-G1.1.BE.07` (0.5h) — Tạo file `main.py` rỗng + entry point chạy `QApplication`.

#### UI — Giao diện cơ bản (0.5 ngày)

- [x] `T-G1.1.UI.01` (1h) — Tạo `app/presentation/themes/apple_light.qss` (style sheet base theo `design/DESIGN-apple.md`).
- [x] `T-G1.1.UI.02` (0.5h) — Cấu trúc thư mục `resources/icons/`, `resources/templates/` (Jinja2), `resources/qss/`.
- [x] `T-G1.1.UI.03` (0.5h) — Test render được 1 cửa sổ trắng tiêu đề "Car Management" 1280×720.

#### TEST — Test setup (0.5 ngày)

- [x] `T-G1.1.TEST.01` (1h) — Cấu hình `pytest.ini` + `conftest.py` (fixture chung: temp DB, app QtBot).
- [x] `T-G1.1.TEST.02` (1h) — Viết test mẫu `test_smoke.py` (assert True) — bảo đảm pipeline hoạt động.
- [x] `T-G1.1.TEST.03` (0.5h) — Cấu hình `coverage` báo cáo HTML tại `htmlcov/`.

#### GIT — Git workflow setup (1 ngày)

- [x] `T-G1.1.GIT.01` (1h) `[BLOCKER]` — Tạo repo GitHub `Car-Management`, push branch `main` initial.
- [x] `T-G1.1.GIT.02` (0.5h) — Tạo branch `dev` từ `main`, đặt làm default branch.
- [x] `T-G1.1.GIT.03` (0.5h) — Cấu hình Branch Protection: `main` & `dev` yêu cầu 1 reviewer + CI pass.
- [x] `T-G1.1.GIT.04` (1h) — Cài `pre-commit` hook: `black`, `isort`, `flake8`, `trailing-whitespace`, `end-of-file-fixer`.
- [x] `T-G1.1.GIT.05` (1.5h) — `.github/workflows/ci.yml`: chạy `pytest`, `coverage`, `flake8` trên mỗi PR (Python 3.10, 3.11).
- [x] `T-G1.1.GIT.06` (0.5h) — Thêm `CODEOWNERS` (TL review HĐ/SEC; mỗi DEV review module phụ trách).
- [x] `T-G1.1.GIT.07` (0.5h) — Templates: `PULL_REQUEST_TEMPLATE.md` (checklist DoD), `ISSUE_TEMPLATE/bug.md`, `ISSUE_TEMPLATE/feature.md`.
- [x] `T-G1.1.GIT.08` (0.5h) — Tag release `vG1.1`. Cập nhật `README.md`. Mở milestone `Phase G2`.

**Definition of Done (Sprint G1.1):**

- ✅ `pip install -r requirements.txt` chạy không lỗi.
- ✅ `pytest` chạy pass.
- ✅ `python main.py` mở cửa sổ trắng.
- ✅ Push commit lên `dev` → CI pass xanh.
- ✅ Tag `vG1.1` được tạo.

---

## 5. PHASE G2 — NỀN TẢNG HỆ THỐNG

> **Thời gian:** 3 tuần (~15 ngày). **Mục tiêu:** schema 25 bảng, đăng nhập, phân quyền, layout chính, audit log — tạo nền cho mọi module nghiệp vụ ở G3-G5.

### Sprint G2.1 — Database Schema & Migrations

**Mục tiêu:** Hiện thực hoá toàn bộ 25 bảng theo `DATABASE_PLAN.md`.
**Phụ trách:** TL (lead).

#### REQ (0.5 ngày)

- [x] `T-G2.1.REQ.01` (2h) — Đọc kỹ `DATABASE_PLAN.md` mục 4.3, 4.4, 4.5, 4.6 → liệt kê 25 bảng + cột + ràng buộc.
- [x] `T-G2.1.REQ.02` (1h) — Đọc `BUSINESS_REQUIREMENTS.md` Mục 4.4 (BR-FLOW) — xác nhận các state transition cần trigger.
- [x] `T-G2.1.REQ.03` (1h) — Quyết định **đặt trigger ở DB hay Application Service** (khuyến nghị: Application Service — TRG-01..08).

#### DB (3 ngày)

- [x] `T-G2.1.DB.01` (1h) — Tạo `app/infrastructure/database/connection.py`: factory connection, bật `PRAGMA foreign_keys = ON`, `PRAGMA journal_mode = WAL`.
- [x] `T-G2.1.DB.02` (1h) — Tạo cấu trúc migration `app/infrastructure/database/migrations/` + `migration_runner.py` (chạy file SQL theo thứ tự version).
- [x] `T-G2.1.DB.03` (2h) — Migration `001_create_users_roles.sql`: `vai_tro`, `nhan_vien` (BR-NV-* và BR-SEC-*).
- [x] `T-G2.1.DB.04` (2h) — Migration `002_create_xe_khach_hang.sql`: `xe`, `khach_hang` (BR-XE-*, BR-KH-*).
- [x] `T-G2.1.DB.05` (3h) — Migration `003_create_hop_dong.sql`: `hop_dong`, `hop_dong_phu_kien` (snapshot giá BR-HD-* và BR-PK-07).
- [x] `T-G2.1.DB.06` (2h) — Migration `004_create_phu_kien.sql`: `phu_kien`, `combo_phu_kien`, `combo_chi_tiet`.
- [x] `T-G2.1.DB.07` (2h) — Migration `005_create_khuyen_mai.sql`: `khuyen_mai`, `km_pham_vi`.
- [x] `T-G2.1.DB.08` (2h) — Migration `006_create_bao_hanh.sql`: `bao_hanh`, `bao_hanh_yeu_cau`.
- [x] `T-G2.1.DB.09` (1.5h) — Migration `007_create_hau_mai.sql`: `bao_duong`, `cuu_ho`.
- [x] `T-G2.1.DB.10` (2h) — Migration `008_create_ncc_kho.sql`: `nha_cung_cap`, `nhap_kho`, `don_dat_hang`.
- [x] `T-G2.1.DB.11` (2h) — Migration `009_create_tra_gop.sql`: `tra_gop`, `tra_gop_lich_su`.
- [x] `T-G2.1.DB.12` (1.5h) — Migration `010_create_marketing.sql`: `chien_dich_mk`, `lead`.
- [x] `T-G2.1.DB.13` (1h) — Migration `011_create_khieu_nai.sql`: `khieu_nai`.
- [x] `T-G2.1.DB.14` (1h) — Migration `012_create_audit_settings.sql`: `audit_log`, `system_settings`.
- [x] `T-G2.1.DB.15` (2h) — Migration `013_create_indexes.sql`: tất cả index hiệu năng (mục 4.6 DATABASE_PLAN).
- [x] `T-G2.1.DB.16` (3h) — Tạo seed data `app/infrastructure/database/seeds/dev_seed.py` theo Mục 4.7: 3 vai trò, 5 NV, 30 xe, 20 KH, 25 PK, 5 KM, 5 NCC, 15 HĐ.
- [x] `T-G2.1.DB.17` (1h) — Insert mặc định `system_settings`: `thoi_han_bh_default = 24`, `muc_toi_thieu_default = 2`, thông tin đại lý.
- [x] `T-G2.1.DB.18` (1h) — Script backup tự động `scripts/backup_db.py` (copy daily → `data/backup/YYYY-MM-DD.db`).

#### BE (2 ngày)

- [x] `T-G2.1.BE.01` (3h) — Tạo `app/domain/entities/` cho 25 entity (dataclass): `NhanVien`, `Xe`, `KhachHang`, `HopDong`, ...
- [x] `T-G2.1.BE.02` (3h) — Base `Repository` interface tại `app/infrastructure/repositories/base_repository.py` (CRUD chuẩn).
- [x] `T-G2.1.BE.03` (1h) — Helper `app/shared/db_utils.py`: `row_to_entity`, `entity_to_dict`, transaction context manager.

#### UI (N/A — chưa có UI ở sprint này)

#### TEST (1 ngày)

- [x] `T-G2.1.TEST.01` (2h) — Test migration: chạy 13 file → 25 bảng được tạo, FK & CHECK constraint hoạt động.
- [x] `T-G2.1.TEST.02` (2h) — Test seed: insert 100% record không lỗi.
- [x] `T-G2.1.TEST.03` (2h) — Test ràng buộc: insert vi phạm CHECK (vd `nam_san_xuat = 1980`) → SQLite raise `IntegrityError`.
- [x] `T-G2.1.TEST.04` (1h) — Test FK ON DELETE RESTRICT: xoá `xe` đang có `hop_dong` → fail.

#### GIT (0.5 ngày)

- [x] `T-G2.1.GIT.01` (0.5h) — Branch `feature/G2.1-database-schema`.
- [x] `T-G2.1.GIT.02` (0.5h) — Commit chuẩn Conventional Commits: `feat(db): create migration 001 users and roles`.
- [x] `T-G2.1.GIT.03` (1h) — PR vào `dev` + reviewer TL + DEV-2 (test) → merge.
- [x] `T-G2.1.GIT.04` (0.5h) — Tag `vG2.1`.

---

### Sprint G2.2 — Authentication & Authorization

**Mục tiêu:** Đăng nhập, đổi mật khẩu, phân quyền 3 actor (A-01/02/03).
**Phụ trách:** TL + DEV-2.
**BRD ref:** BR-SEC-* (Mục 4.7), UC-SEC-01..04, UC-NV-05.

#### REQ (0.5 ngày)

- [x] `T-G2.2.REQ.01` (1h) — Đọc BRD §4.7 (BR-SEC-01..09) + §5.15 (Bảo mật).
- [x] `T-G2.2.REQ.02` (1h) — Đọc UC-SEC-01..04 và AC-SEC-01..03 (Mục 9 BRD).
- [x] `T-G2.2.REQ.03` (1h) — Vẽ luồng `S-AUTH-01` (đăng nhập), `S-AUTH-02` (đổi mật khẩu).

#### DB (0.5 ngày)

- [x] `T-G2.2.DB.01` (1h) — Bổ sung trigger/check: `lan_dang_nhap_sai`, `khoa_den` (BR-SEC-05 — khoá 5 lần sai 15 phút). → Đã có trong migration_001, cần thêm cột `must_change_password` (BR-NV-08).
- [x] `T-G2.2.DB.02` (1h) — Seed admin gốc: `username=admin`, mật khẩu mặc định bcrypt-hashed (BR-NV-08).

#### BE (3 ngày)

- [x] `T-G2.2.BE.01` (2h) — `app/infrastructure/security/password_hasher.py`: bcrypt cost ≥ 12 (BR-SEC-04).
- [x] `T-G2.2.BE.02` (2h) — `app/infrastructure/repositories/nhan_vien_repository.py`: tìm theo username, cập nhật `lan_dang_nhap_sai`/`khoa_den`.
- [x] `T-G2.2.BE.03` (3h) `[BLOCKER]` — `app/application/services/auth_service.py`: `login(username, password)` → check khoá → so sánh hash → reset hoặc tăng counter (BR-SEC-05).
- [x] `T-G2.2.BE.04` (2h) — `change_password(user_id, old, new)` — kiểm tra old, validate độ mạnh ≥ 8 ký tự (BR-SEC-02), hash + lưu.
- [x] `T-G2.2.BE.05` (2h) — `app/application/services/permission_service.py`: load ma trận quyền theo role (BRD §3.4) → `has_permission(role, module, action)`.
- [x] `T-G2.2.BE.06` (2h) — `app/application/services/session.py`: lưu user hiện tại (singleton), idle timeout 30 phút (BR-TIME-07).
- [x] `T-G2.2.BE.07` (1h) — Decorator `@require_permission('module', 'action')` cho service methods.

#### UI (2 ngày)

- [x] `T-G2.2.UI.01` (3h) — `S-AUTH-01` Login window: logo + username + password + nút "Đăng nhập" (PrimaryButton pill); thông báo lỗi inline.
- [x] `T-G2.2.UI.02` (2h) — Hiển thị thông báo khoá: "Tài khoản bị khoá đến HH:mm" khi `khoa_den > now()`.
- [x] `T-G2.2.UI.03` (3h) — `S-AUTH-02` Change password dialog: 3 ô (cũ/mới/xác nhận) + indicator độ mạnh.
- [x] `T-G2.2.UI.04` (2h) — Force change password lần đầu khi flag `must_change_password = True` (BR-NV-08).

#### TEST (1.5 ngày)

- [x] `T-G2.2.TEST.01` (2h) — Unit test `auth_service.login`: success / sai password / bị khoá / hết khoá → AC-SEC-01.
- [x] `T-G2.2.TEST.02` (1h) — Unit test khoá sau 5 lần sai (AC-SEC-02).
- [x] `T-G2.2.TEST.03` (1h) — Unit test `change_password`: validate độ dài ≥ 8 (AC-SEC-03).
- [x] `T-G2.2.TEST.04` (2h) — Unit test `permission_service.has_permission` với ma trận quyền.
- [x] `T-G2.2.TEST.05` (2h) — Integration test `pytest-qt`: gõ login UI → service → DB → đóng dialog.
- [x] `T-G2.2.TEST.06` (1h) — Manual UAT: login admin, sales, kỹ thuật → đúng quyền.

#### GIT (0.5 ngày)

- [x] `T-G2.2.GIT.01` (0.5h) — Branch `feature/G2.2-authentication`.
- [x] `T-G2.2.GIT.02` (0.5h) — PR + review (TL bắt buộc — module SEC).
- [x] `T-G2.2.GIT.03` (0.5h) — Merge → tag `vG2.2`.

---

### Sprint G2.3 — Main Window, Sidebar & Navigation

**Mục tiêu:** Layout chính, sidebar điều hướng 15 module, theme Apple-style.
**Phụ trách:** TL + DEV-1 (UI).

#### REQ (0.5 ngày)

- [x] `T-G2.3.REQ.01` (1h) — Đọc `UI_UX_PLAN.md` mục 5.1 (triết lý) + 5.2 (cấu trúc layout).
- [x] `T-G2.3.REQ.02` (1h) — Đọc `design/DESIGN-apple.md` để chốt color, typography, spacing.
- [x] `T-G2.3.REQ.03` (0.5h) — Map sidebar theo phân quyền — A-01 thấy 15 mục, A-02 thấy 11, A-03 thấy 5.

#### DB (N/A)

- [x] `T-G2.3.DB.01` (0.5h) — Bảng `system_settings` đã có từ migration_012, chứa: ten_dai_ly, dia_chi, so_dien_thoai, email, thoi_han_bh_default, muc_toi_thieu_ton_kho.

#### BE (1 ngày)

- [x] `T-G2.3.BE.01` (1h) — Service `system_settings_service.py`: load config (logo, tên đại lý, version).
- [x] `T-G2.3.BE.02` (2h) — Navigation registry: dict `module_id → screen_class` để sidebar gọi động.
- [x] `T-G2.3.BE.03` (1h) — Filter sidebar items theo role hiện tại (`session.current_user.role`).

#### UI (3 ngày)

- [x] `T-G2.3.UI.01` (3h) — `MainWindow` với 4 area: top-bar (44px), sidebar (240px), content (stack), status-bar (28px).
- [x] `T-G2.3.UI.02` (2h) — `TopBar` widget: logo + tên đại lý + user dropdown (Hồ sơ / Đổi mật khẩu / Đăng xuất).
- [x] `T-G2.3.UI.03` (3h) — `Sidebar` widget: list 15 module + icon + highlight active item (nền `#f5f5f7`).
- [x] `T-G2.3.UI.04` (2h) — `StatusBar` widget: user · thời gian (cập nhật mỗi giây) · version · trạng thái DB.
- [x] `T-G2.3.UI.05` (3h) — `ContentArea` (`QStackedWidget`): chuyển màn hình theo signal sidebar.
- [ ] `T-G2.3.UI.06` (3h) — Component library cơ bản (Mục 5.7 UI/UX): `PrimaryButton`, `SecondaryButton`, `DangerButton`, `MoneyLabel`, `DateLabel`, `StatusBadge`, `KpiCard`, `SearchBar`, `FilterChip`, `ToastNotification`.
- [ ] `T-G2.3.UI.07` (2h) — Style sheet `apple_light.qss` đầy đủ: nút pill, font system, spacing, hover.
- [ ] `T-G2.3.UI.08` (1h) — Phím tắt: `Ctrl+1..9` chuyển module, `Ctrl+L` logout, `F1` help.
- [x] `T-G2.3.UI.09` (1h) — Empty/Loading/Error/Permission Denied states (Mục 5.8 UI/UX) — base widget tái sử dụng.

#### TEST (1 ngày)

- [x] `T-G2.3.TEST.01` (2h) — `pytest-qt` test: click sidebar → đúng screen được hiển thị.
- [x] `T-G2.3.TEST.02` (1h) — Test sidebar filter theo role (sales không thấy "Quản lý NV").
- [x] `T-G2.3.TEST.03` (1h) — Test top-bar dropdown user → mở `S-AUTH-02`.
- [x] `T-G2.3.TEST.04` (1h) — Manual UAT: 3 role login → sidebar tương ứng.

#### GIT (0.5 ngày)

- [x] `T-G2.3.GIT.01` (0.5h) — Branch `feature/G2.3-main-layout`.
- [x] `T-G2.3.GIT.02` (1h) — PR + screenshot UI → review TL + DEV-2.
- [x] `T-G2.3.GIT.03` (0.5h) — Merge → tag `vG2.3`.

---

### Sprint G2.4 — Audit Log & System Settings

**Mục tiêu:** Ghi log mọi hành động CRUD (BR-SEC-09), màn hình xem log (`S-SYS-01`), màn hình cài đặt (`S-CFG-01`).
**Phụ trách:** DEV-2 (lead) + TL review.
**BRD ref:** BR-SEC-09, UC-SEC-03.

#### REQ (0.25 ngày)

- [x] `T-G2.4.REQ.01` (1h) — Liệt kê các action cần log: `LOGIN`, `LOGOUT`, `CREATE_*`, `UPDATE_*`, `DELETE_*`, `CANCEL_HD`, `CHANGE_PASSWORD`.
- [x] `T-G2.4.REQ.02` (1h) — Format `noi_dung` JSON: `{ "before": {...}, "after": {...} }`.

#### DB (0.25 ngày)

- [x] `T-G2.4.DB.01` (0.5h) — Verify schema `audit_log` từ Sprint G2.1 đủ cột (id, nhan_vien_id, hanh_dong, bang_anh_huong, ban_ghi_id, noi_dung, thoi_gian).
- [x] `T-G2.4.DB.02` (0.5h) — Index `audit_log(thoi_gian, nhan_vien_id, hanh_dong)` đã có từ migration_012.

#### BE (1.5 ngày)

- [x] `T-G2.4.BE.01` (2h) — `audit_log_service.log(action, table, record_id, before, after)` — auto user từ session.
- [x] `T-G2.4.BE.02` (2h) — Decorator `@audit('CREATE_HD')` cho service methods → tự gọi log.
- [x] `T-G2.4.BE.03` (2h) — Tích hợp `audit_log_service` vào `auth_service` (LOGIN / LOGOUT) — chuẩn TRG-08.
- [x] `T-G2.4.BE.04` (1h) — Service `system_settings_service.update(key, value)` (chỉ A-01) — đã có trong system_settings_service.py.

#### UI (1 ngày)

- [ ] `T-G2.4.UI.01` (3h) — `S-SYS-01` Audit log viewer: bảng + filter (ngày từ-đến, user, action, table), phân trang 50 dòng.
- [ ] `T-G2.4.UI.02` (1h) — Click row → dialog hiển thị diff JSON (before vs after) format đẹp.
- [ ] `T-G2.4.UI.03` (1h) — Nút "Xuất Excel" log đã filter (openpyxl).
- [ ] `T-G2.4.UI.04` (3h) — `S-CFG-01` System settings: form sửa logo, tên đại lý, địa chỉ, `thoi_han_bh_default`, `muc_toi_thieu_default`, đường dẫn backup.

#### TEST (0.5 ngày)

- [ ] `T-G2.4.TEST.01` (1h) — Unit test decorator `@audit` ghi đúng record.
- [ ] `T-G2.4.TEST.02` (1h) — Test diff JSON khi UPDATE.
- [ ] `T-G2.4.TEST.03` (1h) — UAT: làm vài action → mở S-SYS-01 thấy log đúng thứ tự.

#### GIT (0.25 ngày)

- [ ] `T-G2.4.GIT.01` (0.5h) — Branch `feature/G2.4-audit-log`.
- [ ] `T-G2.4.GIT.02` (1h) — PR review TL.
- [ ] `T-G2.4.GIT.03` (0.5h) — Merge → tag `vG2.4` → **đóng milestone Phase G2**.

**Definition of Done — Phase G2:**

- ✅ Toàn bộ 25 bảng tạo OK.
- ✅ Login / Logout / Đổi mật khẩu chạy đủ 3 role.
- ✅ Sidebar hiển thị đúng quyền theo role.
- ✅ Audit log ghi nhận mọi action.
- ✅ `S-CFG-01` cập nhật được system_settings.
- ✅ Coverage ≥ 80% module SEC.
- ✅ Tag `vG2.4`.

---

## 6. PHASE G3 — NGHIỆP VỤ LÕI

> **Thời gian:** 5 tuần (~25 ngày). **Mục tiêu:** 5 module CRUD lõi + Hợp đồng wizard 4 bước + xuất PDF. Cuối phase phải hoàn thành **WF-02 (Bán xe chuẩn)** end-to-end.

### Sprint G3.1 — Module Xe (Vehicle Management)

**Phụ trách:** TL.
**BRD ref:** §5.1 (BR-XE-01..09), UC-XE-01..05, S-XE-01..03.

#### REQ (0.5 ngày)

- [ ] `T-G3.1.REQ.01` (1h) — Đọc BRD §5.1 + AC-XE-01..03.
- [ ] `T-G3.1.REQ.02` (0.5h) — Wireframe `S-XE-01`, `S-XE-02`, `S-XE-03` (sketch tay/Figma).
- [ ] `T-G3.1.REQ.03` (0.5h) — Liệt kê validation: BR-XE-09 (năm SX ≥ 1990), BR-XE-01 (mã xe unique không sửa).

#### DB (0.25 ngày)

- [ ] `T-G3.1.DB.01` (1h) — Verify schema `xe` từ G2.1 + bổ sung index nếu thiếu.
- [ ] `T-G3.1.DB.02` (0.5h) — Seed bổ sung 30 xe đa dạng (5 hãng × 3 dòng × 2 phiên bản) nếu chưa đủ.

#### BE (1.5 ngày)

- [ ] `T-G3.1.BE.01` (2h) — `XeRepository`: `find_by_id`, `find_all`, `search`, `create`, `update`, `delete`, `find_low_stock`.
- [ ] `T-G3.1.BE.02` (3h) — `XeService.create(data)` — validate BR-XE-01 (mã unique), BR-XE-09 (năm), BR-DATA-* (giá ≥ 0).
- [ ] `T-G3.1.BE.03` (2h) — `XeService.update(id, data)` — không cho sửa `ma_xe` (BR-XE-01).
- [ ] `T-G3.1.BE.04` (1h) — `XeService.delete(id)` — fail nếu có HĐ liên quan (BR-REF-01).
- [ ] `T-G3.1.BE.05` (1h) — `XeService.search(filter)` — query động theo hãng/dòng/năm/giá/trạng thái.
- [ ] `T-G3.1.BE.06` (1h) — `XeService.adjust_inventory(id, delta)` — dùng cho TRG-04, 05 (BR-XE-04, 05).
- [ ] `T-G3.1.BE.07` (1h) — Decorator `@audit('CRUD_XE')` + `@require_permission('xe', 'C/U/D')`.

#### UI (2 ngày)

- [ ] `T-G3.1.UI.01` (3h) — `S-XE-01` Vehicle List: SearchBar + 5 FilterChip + DataTable (cột: mã, hãng, dòng, năm, màu, giá, tồn kho, trạng thái).
- [ ] `T-G3.1.UI.02` (1h) — Highlight đỏ rows có `so_luong_ton ≤ muc_toi_thieu` (BR-XE-08).
- [ ] `T-G3.1.UI.03` (3h) — `S-XE-02` Vehicle Form (FormDialog): các input + validate inline, disable `ma_xe` khi sửa.
- [ ] `T-G3.1.UI.04` (3h) — `S-XE-03` Vehicle Detail: 4 tab (Thông tin, Lịch sử nhập, HĐ đã bán, KM áp dụng).
- [ ] `T-G3.1.UI.05` (1h) — Phân trang DataTable (mặc định 50 dòng/trang) + sort theo cột.
- [ ] `T-G3.1.UI.06` (1h) — Empty / Loading / Error state cho list.
- [ ] `T-G3.1.UI.07` (1h) — Confirm dialog xoá xe + nhập lý do (BR-UI-04).

#### TEST (1 ngày)

- [ ] `T-G3.1.TEST.01` (2h) — Unit test `XeService.create`: success / mã trùng / năm < 1990 / giá âm → AC-XE-01.
- [ ] `T-G3.1.TEST.02` (1h) — Unit test `XeService.update`: không sửa được `ma_xe`.
- [ ] `T-G3.1.TEST.03` (1h) — Unit test `XeService.delete`: bị chặn nếu có FK.
- [ ] `T-G3.1.TEST.04` (2h) — Unit test `XeService.search` với 6 filter combo.
- [ ] `T-G3.1.TEST.05` (1h) — Integration test `pytest-qt`: thêm xe mới qua UI → list refresh.
- [ ] `T-G3.1.TEST.06` (1h) — UAT: A-02 (sales) chỉ thấy nút "Xem", không thấy "Thêm/Sửa/Xoá".

#### GIT (0.5 ngày)

- [ ] `T-G3.1.GIT.01` (0.5h) — Branch `feature/G3.1-module-xe`.
- [ ] `T-G3.1.GIT.02` (1h) — PR + screenshot UI 3 màn hình → review TL + DEV-1.
- [ ] `T-G3.1.GIT.03` (0.5h) — Merge → tag `vG3.1`.

---

### Sprint G3.2 — Module Khách hàng (Customer Management)

**Phụ trách:** DEV-1.
**BRD ref:** §5.2 (BR-KH-01..06), UC-KH-01..03, S-KH-01..03.

#### REQ (0.5 ngày)

- [ ] `T-G3.2.REQ.01` (1h) — Đọc BRD §5.2 + AC-KH-01..02.
- [ ] `T-G3.2.REQ.02` (0.5h) — Liệt kê validation: BR-DATA-04 (email regex), BR-DATA-05 (SĐT VN 10-11 số), BR-KH-02 (SĐT unique).
- [ ] `T-G3.2.REQ.03` (1h) — Hiểu công thức phân loại KH (BR-CALC-03): `Thường < 500tr ≤ Thân thiết < 1.5 tỷ ≤ VIP`.

#### DB (0.25 ngày)

- [ ] `T-G3.2.DB.01` (0.5h) — Verify `khach_hang` schema + index `so_dien_thoai`, `email`, `phan_loai`.

#### BE (1.5 ngày)

- [ ] `T-G3.2.BE.01` (2h) — `KhachHangRepository` đầy đủ CRUD + `find_by_phone`, `find_by_birthday_window(±N days)`.
- [ ] `T-G3.2.BE.02` (3h) — `KhachHangService.create/update/delete` — validate email, SĐT VN, ngày sinh < today.
- [ ] `T-G3.2.BE.03` (2h) — `KhachHangService.update_classification(id)` — tự tính `phan_loai` (BR-CALC-03), gọi sau mỗi HĐ giao xe.
- [ ] `T-G3.2.BE.04` (1h) — `KhachHangService.search(filter)` — name/SĐT/email/phân loại.
- [ ] `T-G3.2.BE.05` (1h) — `KhachHangService.get_purchase_history(id)` — danh sách HĐ + BH + KN của KH.

#### UI (2 ngày)

- [ ] `T-G3.2.UI.01` (3h) — `S-KH-01` Customer List + filter phân loại + badge màu (Thường=xám, Thân thiết=xanh, VIP=vàng).
- [ ] `T-G3.2.UI.02` (3h) — `S-KH-02` Customer Form: validate inline; cảnh báo "SĐT đã tồn tại — KH: [tên]" (BR-KH-02).
- [ ] `T-G3.2.UI.03` (3h) — `S-KH-03` Customer Detail: 4 tab + KpiCard hiển thị `tong_gia_tri_mua`, `so_xe_da_mua`, `phan_loai`.
- [ ] `T-G3.2.UI.04` (1h) — Tooltip giải thích cách tính phân loại (BR-CALC-03).

#### TEST (1 ngày)

- [x] `T-G3.2.TEST.01` (2h) — Unit test validate email/SĐT (BR-DATA-04, 05).
- [x] `T-G3.2.TEST.02` (1h) — Unit test SĐT trùng → raise `DuplicatePhoneError`.
- [x] `T-G3.2.TEST.03` (2h) — Unit test `update_classification`: 4 case (499/500tr/1.5 tỷ/2 tỷ).
- [x] `T-G3.2.TEST.04` (1h) — Integration: thêm KH qua UI → list & detail đúng.
- [x] `T-G3.2.TEST.05` (1h) — UAT theo AC-KH-01, 02.

#### GIT (0.5 ngày)

- [ ] `T-G3.2.GIT.01` (0.5h) — Branch `feature/G3.2-module-khach-hang`.
- [ ] `T-G3.2.GIT.02` (1h) — PR review TL.
- [ ] `T-G3.2.GIT.03` (0.5h) — Merge → tag `vG3.2`.

---

### Sprint G3.3 — Module Nhân viên (Employee Management)

**Phụ trách:** DEV-2.
**BRD ref:** §5.3 (BR-NV-01..09), UC-NV-01..05, S-NV-01..03.

#### REQ (0.25 ngày)

- [x] `T-G3.3.REQ.01` (1h) — Đọc BRD §5.3 + AC-NV-*.
- [x] `T-G3.3.REQ.02` (0.5h) — Hiểu BR-NV-07 (không khoá admin gốc) + BR-NV-08 (mật khẩu random 12 ký tự, force change).
- [x] `T-G3.3.REQ.03` (0.5h) — KPI cá nhân (BR-CALC-05): số HĐ giao thành công, doanh thu, tỷ lệ chốt.

#### DB (0.25 ngày)

- [x] `T-G3.3.DB.01` (0.5h) — Verify cột `must_change_password` trong `nhan_vien`.
- [x] `T-G3.3.DB.02` (0.5h) — Bổ sung view/query KPI nhân viên theo tháng.

#### BE (1.5 ngày)

- [x] `T-G3.3.BE.01` (2h) — `NhanVienService.create(data)` — validate, sinh password random 12 ký tự, hash bcrypt, set `must_change_password=True`.
- [x] `T-G3.3.BE.02` (1h) — `NhanVienService.lock(id)` — không cho khoá admin gốc (`username == 'admin'`) — BR-NV-07.
- [x] `T-G3.3.BE.03` (1h) — `NhanVienService.unlock(id)`.
- [x] `T-G3.3.BE.04` (3h) — `NhanVienService.calc_kpi(nv_id, from_date, to_date)` — BR-CALC-05.
- [x] `T-G3.3.BE.05` (1h) — `NhanVienService.update_self(data)` — A-02/A-03 chỉ sửa được hồ sơ cá nhân (UC-NV-03).
- [x] `T-G3.3.BE.06` (1h) — Audit decorator + permission check.

#### UI (2 ngày)

- [x] `T-G3.3.UI.01` (3h) — `S-NV-01` Employee List (chỉ A-01): bảng đầy đủ + nút Thêm/Khoá/Mở khoá.
- [x] `T-G3.3.UI.02` (3h) — `S-NV-02` Employee Form: hiển thị mật khẩu sinh ngẫu nhiên 1 lần (copy to clipboard), cảnh báo "Hãy lưu lại mật khẩu này".
- [x] `T-G3.3.UI.03` (3h) — `S-NV-03` My Profile (A-02/A-03): hiển thị thông tin cá nhân + KPI tháng + đổi mật khẩu.
- [x] `T-G3.3.UI.04` (1h) — Confirm dialog khoá NV + ghi lý do.
- [x] `T-G3.3.UI.05` (1h) — Hiển thị KPI dạng KpiCard: số xe bán / doanh thu / tỷ lệ chốt.

#### TEST (1 ngày)

- [x] `T-G3.3.TEST.01` (2h) — Unit test sinh password 12 ký tự, đủ chữ số + chữ cái.
- [x] `T-G3.3.TEST.02` (1h) — Unit test BR-NV-07: lock admin gốc → fail.
- [x] `T-G3.3.TEST.03` (2h) — Unit test `calc_kpi` với data fixture (BR-CALC-05).
- [x] `T-G3.3.TEST.04` (1h) — Test phân quyền: A-02 truy cập S-NV-01 → permission denied.
- [x] `T-G3.3.TEST.05` (1h) — UAT theo AC-NV-*.

#### GIT (0.5 ngày)

- [ ] `T-G3.3.GIT.01` (0.5h) — Branch `feature/G3.3-module-nhan-vien`.
- [ ] `T-G3.3.GIT.02` (1h) — PR review TL (security-sensitive).
- [ ] `T-G3.3.GIT.03` (0.5h) — Merge → tag `vG3.3`.

---

### Sprint G3.4 — Module Kho (Inventory Management)

**Phụ trách:** DEV-1.
**BRD ref:** §5.5 (BR-KHO-01..08), UC-KHO-01..03, S-KHO-01..02.

#### REQ (0.25 ngày)

- [x] `T-G3.4.REQ.01` (1h) — Đọc BRD §5.5 + AC-KHO-01.
- [x] `T-G3.4.REQ.02` (0.5h) — Hiểu BR-KHO-02 (cảnh báo `≤ muc_toi_thieu`), BR-KHO-03 (auto giảm khi HĐ thanh toán), BR-KHO-06 (giá trị tồn).

#### DB (0.25 ngày)

- [x] `T-G3.4.DB.01` (0.5h) — Verify `nhap_kho` schema; thêm index `xe_id`, `ngay_nhap`.
- [x] `T-G3.4.DB.02` (0.5h) — Seed 10 record `nhap_kho` mẫu.

#### BE (1.5 ngày)

- [x] `T-G3.4.BE.01` (2h) — `NhapKhoRepository` + `NhapKhoService.create(data)` — tăng `xe.so_luong_ton` hoặc `phu_kien.ton_kho` (TRG-05).
- [x] `T-G3.4.BE.02` (2h) — `KhoService.get_inventory_overview()` — group theo dòng xe, hiển thị tồn kho + giá trị tồn (BR-KHO-06).
- [x] `T-G3.4.BE.03` (1h) — `KhoService.get_low_stock_items()` — list xe + PK có tồn ≤ ngưỡng (BR-KHO-02).
- [x] `T-G3.4.BE.04` (2h) — Trigger TRG-01 (giảm tồn khi HĐ thanh toán) — implement ở `HopDongService.set_paid()` (sẽ dùng ở G3.5).
- [x] `T-G3.4.BE.05` (1h) — Trigger TRG-04 (auto chuyển `xe.trang_thai = da_ban` khi tồn=0) — implement ở `XeService.adjust_inventory`.

#### UI (1.5 ngày)

- [x] `T-G3.4.UI.01` (3h) — `S-KHO-01` Inventory Overview: bảng group theo dòng xe + hightlight đỏ tồn ≤ ngưỡng + footer tổng giá trị.
- [x] `T-G3.4.UI.02` (3h) — `S-KHO-02` Stock-in Form: chọn NCC + xe/PK + số lượng + giá nhập + ngày → submit.
- [x] `T-G3.4.UI.03` (1h) — Bảng "Lịch sử nhập kho gần nhất" (10 record cuối) ở tab dưới `S-KHO-02`.
- [x] `T-G3.4.UI.04` (1h) — Toast notification "Đã nhập kho thành công, tồn mới = X" sau khi tạo.

#### TEST (1 ngày)

- [x] `T-G3.4.TEST.01` (2h) — Unit test `NhapKhoService.create` → tồn tăng đúng số lượng.
- [x] `T-G3.4.TEST.02` (1h) — Test `get_low_stock_items` với data 5 xe, 2 dưới ngưỡng.
- [x] `T-G3.4.TEST.03` (1h) — Test TRG-04: nhập 0 xe đã `da_ban` không đổi trạng thái; nhập 1 xe đã bán → `con_hang`.
- [x] `T-G3.4.TEST.04` (1h) — UAT theo AC-KHO-01.

#### GIT (0.25 ngày)

- [ ] `T-G3.4.GIT.01` (0.5h) — Branch `feature/G3.4-module-kho`.
- [ ] `T-G3.4.GIT.02` (1h) — PR review TL.
- [ ] `T-G3.4.GIT.03` (0.5h) — Merge → tag `vG3.4`.

---

### Sprint G3.5 — Module Hợp đồng (Contract — wizard 4 bước + PDF)

**Phụ trách:** TL (lead) + DEV-1 (UI) + DEV-2 (test).
**BRD ref:** §5.4 (BR-HD-01..10), UC-HD-01..04, S-HD-01..04, WF-02.
**Đây là sprint quan trọng nhất Phase G3.**

#### REQ (1 ngày)

- [x] `T-G3.5.REQ.01` (2h) — Đọc kỹ BRD §5.4 + AC-HD-01..03 + WF-02 (Mục 6 BRD).
- [x] `T-G3.5.REQ.02` (1h) — Hiểu BR-CALC-01 (tổng tiền HĐ = giá xe + PK − giảm KM), BR-CALC-02 (tính giảm KM 4 loại).
- [x] `T-G3.5.REQ.03` (1h) — Hiểu **snapshot price** BR-HD-* + BR-PK-07: lưu giá tại thời điểm tạo HĐ, không sync.
- [x] `T-G3.5.REQ.04` (1h) — Vẽ wizard 4 bước (B1: KH → B2: Xe+PK → B3: KM → B4: Xác nhận).
- [x] `T-G3.5.REQ.05` (1h) — Đặc tả PDF: header logo + đại lý, info KH, info xe, bảng giá, KM, điều khoản BH, chữ ký 2 bên.

#### DB (0.5 ngày)

- [x] `T-G3.5.DB.01` (0.5h) — Verify `hop_dong` (snapshot fields), `hop_dong_phu_kien` (snapshot `gia_ban`).
- [x] `T-G3.5.DB.02` (1h) — Procedure sinh `ma_hop_dong` định dạng `HD<YYYY>-<NNNN>` (sequential trong năm).
- [x] `T-G3.5.DB.03` (0.5h) — Index `hop_dong(ngay_tao, trang_thai, nhan_vien_id, khach_hang_id)`.

#### BE (4 ngày)

- [x] `T-G3.5.BE.01` (2h) — `HopDongRepository` đầy đủ + `next_ma_hop_dong()`.
- [x] `T-G3.5.BE.02` (3h) `[BLOCKER]` — `HopDongService.calculate_total(xe_id, pk_list, km_id)` — BR-CALC-01, 02; **trả về breakdown** (giá xe, tổng PK, tiền giảm, tổng).
- [x] `T-G3.5.BE.03` (3h) — `HopDongService.create(data)` — validate đủ 4 bước → snapshot giá → insert `hop_dong` + `hop_dong_phu_kien` trong transaction.
- [x] `T-G3.5.BE.04` (2h) — `HopDongService.update(id, data)` — chỉ cho `moi_tao` (BR-HD-09). HĐ `da_thanh_toan` chỉ A-01.
- [x] `T-G3.5.BE.05` (3h) `[BLOCKER]` — `HopDongService.set_paid(id)` — BR-HD-03: chuyển trạng thái + ghi `ngay_thanh_toan` + **giảm tồn kho (TRG-01)** + audit log.
- [x] `T-G3.5.BE.06` (3h) `[BLOCKER]` — `HopDongService.set_delivered(id)` — BR-HD-04: chuyển trạng thái + ghi `ngay_giao_xe` + **tự sinh `bao_hanh` (TRG-02)** + cập nhật KH (BR-CALC-03) + cập nhật KPI NV.
- [x] `T-G3.5.BE.07` (2h) — `HopDongService.cancel(id, reason)` — BR-HD-05 (chỉ A-01): hoàn tồn kho + xoá BH/TG liên quan + ghi `ly_do_huy` (TRG-03).
- [x] `T-G3.5.BE.08` (3h) — `HopDongService.search(filter)` — phân trang + filter trạng thái/ngày/KH/NV.
- [x] `T-G3.5.BE.09` (3h) `[BLOCKER]` — `PdfRenderer` wrapper Jinja2 + WeasyPrint: load template `contract.html` + CSS, render PDF.
- [x] `T-G3.5.BE.10` (2h) — Tạo template `resources/templates/contract.html` (Jinja2): full layout HĐ (header, KH, xe, bảng PK, KM, tổng, BH, chữ ký).
- [x] `T-G3.5.BE.11` (1h) — Tạo CSS `resources/templates/contract.css` (in A4, font system).
- [x] `T-G3.5.BE.12` (1h) — `HopDongService.export_pdf(id, output_path)` — render và lưu file.

#### UI (4 ngày)

- [ ] `T-G3.5.UI.01` (3h) — `S-HD-01` Contract List: bảng + filter trạng thái/ngày/KH/NV + badge trạng thái BR-FLOW.
- [ ] `T-G3.5.UI.02` (4h) `[BLOCKER]` — `S-HD-02` Wizard B1 — chọn/tạo KH (search hoặc tạo mới inline gọi `S-KH-02`).
- [ ] `T-G3.5.UI.03` (4h) — Wizard B2 — chọn xe + thêm PK (multi-select); hiển thị **giá đang được snapshot** với tooltip "Giá này sẽ cố định trên HĐ".
- [ ] `T-G3.5.UI.04` (3h) — Wizard B3 — chọn KM phù hợp (auto load KM còn hiệu lực + áp dụng được cho xe đã chọn — BR-KM-04).
- [ ] `T-G3.5.UI.05` (3h) — Wizard B4 — preview tổng tiền + breakdown (BR-CALC-01) + ghi chú + nút "Xác nhận lưu".
- [ ] `T-G3.5.UI.06` (2h) — Validation step-by-step: không cho Next nếu thiếu field bắt buộc.
- [ ] `T-G3.5.UI.07` (3h) — `S-HD-03` Contract Detail: thông tin đầy đủ + nút "Thanh toán", "Giao xe", "Hủy" (theo state machine BR-FLOW).
- [ ] `T-G3.5.UI.08` (1h) — Confirm dialog "Hủy HĐ" + bắt buộc nhập `ly_do_huy` ≥ 10 ký tự (BR-UI-04).
- [ ] `T-G3.5.UI.09` (3h) — `S-HD-04` PDF Preview: render PDF inline (QPdfView hoặc QWebEngineView) + nút "In" / "Xuất file".
- [ ] `T-G3.5.UI.10` (1h) — Lịch sử trạng thái HĐ (timeline): tạo → thanh toán → giao xe / hủy.

#### TEST (2 ngày)

- [ ] `T-G3.5.TEST.01` (3h) — Unit test `calculate_total` với 12 case (3 loại KM × 4 scenario).
- [ ] `T-G3.5.TEST.02` (2h) — Unit test `create` snapshot — giá HĐ không thay đổi sau khi sửa giá xe gốc.
- [ ] `T-G3.5.TEST.03` (2h) — Unit test state machine: chỉ cho transition hợp lệ (`moi_tao → da_thanh_toan → da_giao_xe`; `* → huy`).
- [ ] `T-G3.5.TEST.04` (2h) — Unit test `set_paid` → tồn xe giảm đúng.
- [ ] `T-G3.5.TEST.05` (2h) — Unit test `set_delivered` → BH được tạo đúng `thoi_han_bh` + KPI NV cập nhật.
- [ ] `T-G3.5.TEST.06` (2h) — Unit test `cancel` → tồn kho được hoàn + BH bị xoá.
- [ ] `T-G3.5.TEST.07` (2h) — Test PDF rendering với fixture HĐ → assert PDF có đủ KH, xe, tổng tiền (parse text bằng `pdfplumber`).
- [ ] `T-G3.5.TEST.08` (3h) — Integration test WF-02 đầy đủ qua UI: tạo KH → tạo HĐ wizard → thanh toán → giao xe → BH tự tạo.
- [ ] `T-G3.5.TEST.09` (2h) — UAT 3 role theo AC-HD-01, 02, 03.

#### GIT (1 ngày)

- [ ] `T-G3.5.GIT.01` (0.5h) — Branch `feature/G3.5-module-hop-dong`.
- [ ] `T-G3.5.GIT.02` (1h) — Commit nhỏ theo BE step (`feat(hd): calc total formula`, `feat(hd): pdf renderer`, ...).
- [ ] `T-G3.5.GIT.03` (2h) — PR + screenshot wizard + PDF mẫu → review TL bắt buộc.
- [ ] `T-G3.5.GIT.04` (0.5h) — Merge → tag `vG3.5` → **đóng milestone Phase G3** + demo cho stakeholders.

**Definition of Done — Phase G3:**

- ✅ 5 module CRUD chạy được CRUD đầy đủ với phân quyền.
- ✅ Hợp đồng wizard 4 bước hoạt động mượt.
- ✅ PDF render đúng template, in được.
- ✅ WF-02 (Bán xe chuẩn) end-to-end chạy thành công: tạo KH → HĐ → thanh toán → giao xe → BH tự sinh.
- ✅ Coverage ≥ 80% cho mỗi service.
- ✅ Tag `vG3.5`.

---

## 7. PHASE G4 — MODULE MỞ RỘNG

> **Thời gian:** 5 tuần (~25 ngày). **Mục tiêu:** 5 module phụ trợ HĐ + WF-01 (Nhập kho), WF-03 (Bán trả góp), WF-04 (Bảo hành).

### Sprint G4.1 — Module Phụ kiện & Combo

**Phụ trách:** DEV-1.
**BRD ref:** §5.6 (BR-PK-01..07), UC-PK-01..02, S-PK-01..03.

#### REQ (0.25 ngày)

- [ ] `T-G4.1.REQ.01` (1h) — Đọc BRD §5.6 + AC-PK-*.
- [ ] `T-G4.1.REQ.02` (0.5h) — Hiểu BR-CALC-07 (giá combo = `sum(gia_pk) × he_so_giam`).

#### DB (0.25 ngày)

- [ ] `T-G4.1.DB.01` (0.5h) — Verify `phu_kien`, `combo_phu_kien`, `combo_chi_tiet`.
- [ ] `T-G4.1.DB.02` (0.5h) — Seed 25 PK đa dạng + 5 combo mẫu.

#### BE (1.5 ngày)

- [ ] `T-G4.1.BE.01` (2h) — `PhuKienService` CRUD + validate (tên ≥ 3, giá ≥ 0, tồn ≥ 0 — BR-PK-05).
- [ ] `T-G4.1.BE.02` (2h) — `ComboService.create(name, items, he_so_giam)` — items ≥ 2 PK (BR-PK-04).
- [ ] `T-G4.1.BE.03` (2h) — `ComboService.calculate_price(combo_id)` — BR-CALC-07.
- [ ] `T-G4.1.BE.04` (1h) — `PhuKienService.adjust_inventory(pk_id, delta)` — dùng cho HĐ.
- [ ] `T-G4.1.BE.05` (1h) — Audit + permission decorator.

#### UI (2 ngày)

- [ ] `T-G4.1.UI.01` (3h) — `S-PK-01` Phụ kiện List: filter `phan_loai` (5 nhóm BR-PK-01) + cột tồn kho (highlight đỏ tồn ≤ 0 — BR-PK-05).
- [ ] `T-G4.1.UI.02` (2h) — `S-PK-02` Phụ kiện Form: tên, mô tả, phân loại, giá bán, tồn kho.
- [ ] `T-G4.1.UI.03` (4h) — `S-PK-03` Combo Manager: tạo combo dạng wizard (chọn PK + số lượng → set hệ số giảm → preview giá ưu đãi tự tính).
- [ ] `T-G4.1.UI.04` (1h) — Hiển thị "Giá thường: X — Giá combo: Y — Tiết kiệm: Z" trong card combo.

#### TEST (1 ngày)

- [ ] `T-G4.1.TEST.01` (2h) — Unit test `Combo.calculate_price` 5 case.
- [ ] `T-G4.1.TEST.02` (1h) — Test combo phải có ≥ 2 PK (BR-PK-04).
- [ ] `T-G4.1.TEST.03` (1h) — Test `adjust_inventory` không cho âm (BR-PK-05).
- [ ] `T-G4.1.TEST.04` (1h) — UAT theo AC-PK-*.

#### GIT (0.25 ngày)

- [ ] `T-G4.1.GIT.01` (0.5h) — Branch `feature/G4.1-module-phu-kien`.
- [ ] `T-G4.1.GIT.02` (1h) — PR review TL.
- [ ] `T-G4.1.GIT.03` (0.5h) — Merge → tag `vG4.1`.

---

### Sprint G4.2 — Module Khuyến mãi (Promotion)

**Phụ trách:** DEV-2.
**BRD ref:** §5.7 (BR-KM-01..09), UC-KM-01..05, S-KM-01..03.

#### REQ (0.5 ngày)

- [ ] `T-G4.2.REQ.01` (1h) — Đọc BRD §5.7 + AC-KM-*.
- [ ] `T-G4.2.REQ.02` (1h) — Hiểu 4 loại KM (BR-KM-03): `giam_tien_mat`, `tang_phu_kien`, `giam_lai_suat`, `combo`.
- [ ] `T-G4.2.REQ.03` (1h) — Hiểu BR-KM-04 (phạm vi áp dụng: hãng/dòng/xe cụ thể/xe tồn lâu) + BR-KM-08 (auto end khi `den_ngay < today`).

#### DB (0.5 ngày)

- [ ] `T-G4.2.DB.01` (0.5h) — Verify `khuyen_mai`, `km_pham_vi`.
- [ ] `T-G4.2.DB.02` (1h) — Seed 5 KM mỗi loại 1 chương trình.

#### BE (2 ngày)

- [ ] `T-G4.2.BE.01` (2h) — `KhuyenMaiService.create(data)` — validate `den_ngay > tu_ngay`, gia_tri > 0.
- [ ] `T-G4.2.BE.02` (2h) — `KhuyenMaiService.find_applicable(xe_id)` — BR-KM-04: lọc KM còn hiệu lực, trùng phạm vi (hãng/dòng/xe/tồn-lâu).
- [ ] `T-G4.2.BE.03` (2h) — `KhuyenMaiService.calculate_discount(km, gia_xe, ...)` — BR-CALC-02 cho 4 loại.
- [ ] `T-G4.2.BE.04` (1h) — `KhuyenMaiService.pause(id)` / `resume(id)` (BR-KM-07).
- [ ] `T-G4.2.BE.05` (2h) — Job daily TRG-06: chuyển KM `den_ngay < today` sang `ket_thuc`.
- [ ] `T-G4.2.BE.06` (3h) — `KhuyenMaiService.report_effectiveness(km_id)` — số HĐ áp dụng + doanh thu phát sinh + tổng giảm (BR-KM-09 — phục vụ RP-06).

#### UI (2 ngày)

- [ ] `T-G4.2.UI.01` (3h) — `S-KM-01` Promo List: badge trạng thái (BR-FLOW KM) + nút Pause/Resume.
- [ ] `T-G4.2.UI.02` (4h) — `S-KM-02` Promo Form: dropdown 4 loại + dynamic field (giá trị tiền/% theo loại) + multi-select phạm vi (hãng/dòng/xe/tồn-lâu).
- [ ] `T-G4.2.UI.03` (3h) — `S-KM-03` Effectiveness Report: KpiCard (số HĐ, doanh thu, tổng giảm) + biểu đồ cột so sánh KM.
- [ ] `T-G4.2.UI.04` (1h) — Filter by trạng thái + thời gian + loại KM trong list.

#### TEST (1 ngày)

- [ ] `T-G4.2.TEST.01` (2h) — Unit test `find_applicable` cho 5 case (xe có KM hãng / dòng / cụ thể / tồn-lâu / không match).
- [ ] `T-G4.2.TEST.02` (2h) — Unit test `calculate_discount` cho 4 loại KM × 2 kiểu (tiền/%).
- [ ] `T-G4.2.TEST.03` (1h) — Test daily job TRG-06: KM `den_ngay = yesterday` → `ket_thuc`.
- [ ] `T-G4.2.TEST.04` (1h) — Test `report_effectiveness` với data fixture.
- [ ] `T-G4.2.TEST.05` (1h) — UAT theo AC-KM-*.

#### GIT (0.25 ngày)

- [ ] `T-G4.2.GIT.01` (0.5h) — Branch `feature/G4.2-module-khuyen-mai`.
- [ ] `T-G4.2.GIT.02` (1h) — PR review TL.
- [ ] `T-G4.2.GIT.03` (0.5h) — Merge → tag `vG4.2`.

---

### Sprint G4.3 — Module Bảo hành (Warranty) — WF-04

**Phụ trách:** DEV-2.
**BRD ref:** §5.8 (BR-BH-01..10), UC-BH-01..05, S-BH-01..04, WF-04.

#### REQ (0.5 ngày)

- [ ] `T-G4.3.REQ.01` (1h) — Đọc BRD §5.8 + AC-BH-01, 02 + WF-04.
- [ ] `T-G4.3.REQ.02` (1h) — Hiểu BR-BH-01 (mỗi HĐ → 1 BH), BR-BH-02 (`ngay_ket_thuc = ngay_giao_xe + thoi_han_bh`).
- [ ] `T-G4.3.REQ.03` (0.5h) — Hiểu BR-BH-04 (miễn phí lỗi NSX, tính phí lỗi do KH).

#### DB (0.25 ngày)

- [ ] `T-G4.3.DB.01` (0.5h) — Verify `bao_hanh` (UNIQUE `hop_dong_id`), `bao_hanh_yeu_cau`.
- [ ] `T-G4.3.DB.02` (0.5h) — Index `bao_hanh.ngay_ket_thuc` (cảnh báo BR-BH-03 30 ngày).

#### BE (2 ngày)

- [ ] `T-G4.3.BE.01` (1h) — `BaoHanhRepository` + `find_expiring_in(days)`.
- [ ] `T-G4.3.BE.02` (2h) — `BaoHanhService.auto_create_from_hop_dong(hd_id)` — gọi từ TRG-02 (đã viết ở G3.5).
- [ ] `T-G4.3.BE.03` (3h) — `BaoHanhService.create_request(bh_id, data)` — validate ngày trong hạn BH, phân loại (miễn phí/tính phí — BR-BH-04), assign kỹ thuật.
- [ ] `T-G4.3.BE.04` (2h) — `BaoHanhService.update_request(req_id, status, ...)` — chuyển trạng thái yêu cầu (BR-BH-05).
- [ ] `T-G4.3.BE.05` (2h) — `BaoHanhService.find_expiring_in_30_days()` — BR-BH-03 (cho dashboard).
- [ ] `T-G4.3.BE.06` (3h) — Render phiếu BH PDF với Jinja2+WeasyPrint (BR-BH-07) — template `warranty.html`.

#### UI (2 ngày)

- [ ] `T-G4.3.UI.01` (3h) — `S-BH-01` Warranty List: filter trạng thái (còn HL/sắp hết/hết hạn) + highlight cảnh báo 30 ngày.
- [ ] `T-G4.3.UI.02` (2h) — `S-BH-02` Warranty Detail: thông tin xe, KH, thời hạn, phạm vi + danh sách yêu cầu.
- [ ] `T-G4.3.UI.03` (4h) — `S-BH-03` Create Request Form: ngày đến, nội dung sửa, phân loại (auto suggest theo lỗi), chi phí, KT phụ trách.
- [ ] `T-G4.3.UI.04` (3h) — `S-BH-04` Print Warranty Slip: preview PDF + nút in.

#### TEST (1 ngày)

- [ ] `T-G4.3.TEST.01` (2h) — Unit test `auto_create_from_hop_dong` → `ngay_ket_thuc` đúng công thức (BR-BH-02).
- [ ] `T-G4.3.TEST.02` (2h) — Unit test `create_request` reject nếu ngày > `ngay_ket_thuc`.
- [ ] `T-G4.3.TEST.03` (1h) — Test `find_expiring_in_30_days` với data 5 BH (3 trong window).
- [ ] `T-G4.3.TEST.04` (2h) — Integration WF-04: HĐ giao xe → BH tự sinh → tạo request → in phiếu.
- [ ] `T-G4.3.TEST.05` (1h) — UAT theo AC-BH-01, 02.

#### GIT (0.25 ngày)

- [ ] `T-G4.3.GIT.01` (0.5h) — Branch `feature/G4.3-module-bao-hanh`.
- [ ] `T-G4.3.GIT.02` (1h) — PR review TL.
- [ ] `T-G4.3.GIT.03` (0.5h) — Merge → tag `vG4.3`.

---

### Sprint G4.4 — Module Nhà cung cấp & Đơn đặt hàng — WF-01

**Phụ trách:** DEV-1.
**BRD ref:** §5.9 (BR-NCC-01..06), UC-NCC-01..03, S-NCC-01..03, WF-01.

#### REQ (0.5 ngày)

- [ ] `T-G4.4.REQ.01` (1h) — Đọc BRD §5.9 + AC-NCC-*.
- [ ] `T-G4.4.REQ.02` (1h) — Hiểu BR-NCC-02 (đánh giá 3 tiêu chí 1-5: chất lượng, giao hàng, giá), BR-NCC-03 (điểm TB), BR-NCC-05 (auto sinh `nhap_kho` khi đơn `da_nhan`).

#### DB (0.25 ngày)

- [ ] `T-G4.4.DB.01` (0.5h) — Verify `nha_cung_cap`, `don_dat_hang`, `nhap_kho`.
- [ ] `T-G4.4.DB.02` (0.5h) — Seed 5 NCC + 10 đơn mẫu.

#### BE (2 ngày)

- [ ] `T-G4.4.BE.01` (1h) — `NhaCungCapService` CRUD + validate.
- [ ] `T-G4.4.BE.02` (2h) — `NhaCungCapService.add_rating(ncc_id, ratings)` — lưu điểm 3 tiêu chí.
- [ ] `T-G4.4.BE.03` (1h) — `NhaCungCapService.calculate_avg_rating(ncc_id)` — BR-NCC-03.
- [ ] `T-G4.4.BE.04` (3h) — `DonDatHangService.create(ncc_id, items)` — tạo đơn `cho_xu_ly`.
- [ ] `T-G4.4.BE.05` (3h) — `DonDatHangService.set_received(don_id)` — BR-NCC-05: chuyển trạng thái + auto gọi `NhapKhoService.create()` cho mỗi item.
- [ ] `T-G4.4.BE.06` (1h) — Audit + permission.

#### UI (2 ngày)

- [ ] `T-G4.4.UI.01` (3h) — `S-NCC-01` Supplier List: bảng + cột điểm trung bình + nút "Đánh giá nhanh".
- [ ] `T-G4.4.UI.02` (3h) — `S-NCC-02` Supplier Detail: tab Thông tin · Lịch sử nhập · Đánh giá (form 3 sao).
- [ ] `T-G4.4.UI.03` (4h) — `S-NCC-03` Order Form: chọn NCC + thêm xe/PK + số lượng + giá nhập; bảng đơn hàng theo trạng thái.
- [ ] `T-G4.4.UI.04` (1h) — Nút "Đánh dấu đã nhận" → confirm → auto tạo nhập kho.

#### TEST (1 ngày)

- [ ] `T-G4.4.TEST.01` (2h) — Unit test `add_rating` + `calculate_avg_rating`.
- [ ] `T-G4.4.TEST.02` (2h) — Unit test `set_received` → tồn kho tăng đúng số lượng.
- [ ] `T-G4.4.TEST.03` (2h) — Integration WF-01: tạo NCC → đặt đơn → đánh dấu nhận → kiểm tra `nhap_kho` + tồn xe.
- [ ] `T-G4.4.TEST.04` (1h) — UAT theo AC-NCC-*.

#### GIT (0.25 ngày)

- [ ] `T-G4.4.GIT.01` (0.5h) — Branch `feature/G4.4-module-ncc`.
- [ ] `T-G4.4.GIT.02` (1h) — PR review TL.
- [ ] `T-G4.4.GIT.03` (0.5h) — Merge → tag `vG4.4`.

---

### Sprint G4.5 — Module Trả góp (Installment) — WF-03

**Phụ trách:** TL (lead) + DEV-2.
**BRD ref:** §5.11 (BR-TG-01..10), UC-TG-01..03, S-TG-01..03, WF-03.

#### REQ (0.5 ngày)

- [ ] `T-G4.5.REQ.01` (1h) — Đọc BRD §5.11 + AC-TG-* + WF-03.
- [ ] `T-G4.5.REQ.02` (1h) — Hiểu BR-CALC-04 (công thức niên kim): `M = P × r × (1+r)^n / ((1+r)^n − 1)` với `r = lai_suat_nam/12/100`, `n = so_ky`.
- [ ] `T-G4.5.REQ.03` (0.5h) — Hiểu BR-DATA-09 (lãi suất [0, 30]%), BR-TG-09 (chậm 5 ngày → `qua_han`).

#### DB (0.25 ngày)

- [ ] `T-G4.5.DB.01` (0.5h) — Verify `tra_gop`, `tra_gop_lich_su`.
- [ ] `T-G4.5.DB.02` (0.5h) — Index `tra_gop_lich_su.ngay_den_han`, `trang_thai`.

#### BE (2 ngày)

- [ ] `T-G4.5.BE.01` (1h) — `TraGopRepository` đầy đủ.
- [ ] `T-G4.5.BE.02` (3h) `[BLOCKER]` — `TraGopService.calculate_monthly_payment(P, r_year, n)` — BR-CALC-04.
- [ ] `T-G4.5.BE.03` (3h) — `TraGopService.create(hop_dong_id, ngan_hang, P, r_year, n)` — sinh hồ sơ + auto sinh `n` row `tra_gop_lich_su` với `ngay_den_han` mỗi tháng.
- [ ] `T-G4.5.BE.04` (2h) — `TraGopService.record_payment(ky_id)` — chuyển kỳ → `da_tra`.
- [ ] `T-G4.5.BE.05` (2h) — Job daily TRG-07: kỳ `chua_tra` & `ngay_den_han + 5d < today` → `qua_han` (BR-TG-09).
- [ ] `T-G4.5.BE.06` (1h) — `TraGopService.find_overdue()` cho dashboard.

#### UI (2 ngày)

- [ ] `T-G4.5.UI.01` (3h) — `S-TG-01` Installment List: filter ngân hàng + trạng thái; highlight đỏ hồ sơ có kỳ `qua_han`.
- [ ] `T-G4.5.UI.02` (4h) — `S-TG-02` Create Installment Form: chọn HĐ + nhập NH + P + lãi suất + số kỳ → preview `M` (auto tính BR-CALC-04) + lịch trả full.
- [ ] `T-G4.5.UI.03` (3h) — `S-TG-03` Track Progress: bảng kỳ trả + nút "Ghi nhận thanh toán" cho kỳ chưa trả.
- [ ] `T-G4.5.UI.04` (1h) — Cảnh báo "X kỳ quá hạn" tại header màn hình.

#### TEST (1 ngày)

- [ ] `T-G4.5.TEST.01` (3h) `[BLOCKER]` — Unit test `calculate_monthly_payment` với 5 case: P=500tr/r=10%/n=24, P=1tỷ/r=8%/n=36, edge case r=0, r=30, n=6, n=84.
- [ ] `T-G4.5.TEST.02` (2h) — Unit test `create` → `n` kỳ `tra_gop_lich_su` đúng số tiền + ngày.
- [ ] `T-G4.5.TEST.03` (1h) — Test job TRG-07: kỳ chậm 6 ngày → `qua_han`.
- [ ] `T-G4.5.TEST.04` (2h) — Integration WF-03: WF-02 + tạo trả góp → ghi nhận 3 kỳ.
- [ ] `T-G4.5.TEST.05` (1h) — UAT theo AC-TG-*.

#### GIT (0.25 ngày)

- [ ] `T-G4.5.GIT.01` (0.5h) — Branch `feature/G4.5-module-tra-gop`.
- [ ] `T-G4.5.GIT.02` (1.5h) — PR review TL bắt buộc (công thức tài chính).
- [ ] `T-G4.5.GIT.03` (0.5h) — Merge → tag `vG4.5` → **đóng milestone Phase G4**.

**Definition of Done — Phase G4:**

- ✅ 5 module mở rộng hoàn chỉnh.
- ✅ WF-01 (Nhập kho), WF-03 (Bán trả góp), WF-04 (Bảo hành) chạy E2E.
- ✅ PDF phiếu BH render đúng.
- ✅ Job daily TRG-06 (KM hết hạn), TRG-07 (TG quá hạn) chạy được.
- ✅ Coverage ≥ 80% tổng.
- ✅ Tag `vG4.5`.

---

## 8. PHASE G5 — MODULE BỔ SUNG & BÁO CÁO

> **Thời gian:** 4 tuần (~20 ngày). **Mục tiêu:** 4 module phụ + Dashboard tổng hợp + 7 báo cáo (RP-01..07) + WF-05, 06, 07.

### Sprint G5.1 — Module Hậu mãi (Bảo dưỡng & Cứu hộ) — WF-05

**Phụ trách:** DEV-2.
**BRD ref:** §5.10 (BR-HM-01..06), UC-HM-01..04, S-HM-01..04, WF-05.

#### REQ (0.5 ngày)

- [ ] `T-G5.1.REQ.01` (1h) — Đọc BRD §5.10 + AC-HM-*.
- [ ] `T-G5.1.REQ.02` (0.5h) — Hiểu BR-TIME-02 (nhắc 7 ngày trước lịch BD), BR-TIME-05 (sinh nhật KH ±7 ngày).
- [ ] `T-G5.1.REQ.03` (0.5h) — Phân biệt BD (định kỳ, có lịch) vs Cứu hộ (đột xuất, có vị trí).

#### DB (0.25 ngày)

- [ ] `T-G5.1.DB.01` (0.5h) — Verify `bao_duong`, `cuu_ho`.

#### BE (1.5 ngày)

- [ ] `T-G5.1.BE.01` (2h) — `BaoDuongService.create/update/delete` — chọn KH+xe, ngày, KM xe, nội dung, chi phí (BR-HM-06).
- [ ] `T-G5.1.BE.02` (2h) — `BaoDuongService.find_upcoming(days)` — BR-TIME-02: lịch BD trong N ngày tới.
- [ ] `T-G5.1.BE.03` (2h) — `CuuHoService.create/update` — KH, xe, vị trí, mô tả, chi phí, trạng thái (BR-HM-04, 05).
- [ ] `T-G5.1.BE.04` (2h) — `KhachHangService.find_birthday_window(days=7)` — phục vụ S-HM-04 (BR-TIME-05).

#### UI (2 ngày)

- [ ] `T-G5.1.UI.01` (4h) — `S-HM-01` Maintenance Schedule: Calendar view (`QCalendarWidget`) + List view, click ngày → xem lịch.
- [ ] `T-G5.1.UI.02` (3h) — `S-HM-02` Create Maintenance Form: chọn KH (search) → xe (auto load xe của KH) → ngày → KM xe → nội dung → chi phí.
- [ ] `T-G5.1.UI.03` (3h) — `S-HM-03` Rescue Request Form: thông tin KH/xe + ô nhập vị trí + mô tả + chi phí + trạng thái.
- [ ] `T-G5.1.UI.04` (3h) — `S-HM-04` Customer Care: list KH có sinh nhật ±7 ngày + nút "Gửi thiệp" (mock — chỉ ghi log).

#### TEST (0.5 ngày)

- [ ] `T-G5.1.TEST.01` (1h) — Unit test `find_upcoming(7)` — BR-TIME-02.
- [ ] `T-G5.1.TEST.02` (1h) — Unit test `find_birthday_window(7)` — BR-TIME-05.
- [ ] `T-G5.1.TEST.03` (1h) — Integration WF-05: Dashboard cảnh báo → mở S-HM-01 → tạo phiếu BD.
- [ ] `T-G5.1.TEST.04` (0.5h) — UAT theo AC-HM-*.

#### GIT (0.25 ngày)

- [ ] `T-G5.1.GIT.01` (0.5h) — Branch `feature/G5.1-module-hau-mai`.
- [ ] `T-G5.1.GIT.02` (1h) — PR review.
- [ ] `T-G5.1.GIT.03` (0.5h) — Merge → tag `vG5.1`.

---

### Sprint G5.2 — Module Marketing & Lead — WF-07

**Phụ trách:** DEV-1.
**BRD ref:** §5.12 (BR-MK-01..04), UC-MK-01..04, S-MK-01..03, WF-07.

#### REQ (0.5 ngày)

- [ ] `T-G5.2.REQ.01` (1h) — Đọc BRD §5.12 + AC-MK-*.
- [ ] `T-G5.2.REQ.02` (1h) — Hiểu BR-CALC-06 (tỷ lệ chuyển đổi = `lead_chuyen_doi / tong_lead × 100%`), BR-MK-02 (4 trạng thái lead), BR-MK-03 (chuyển lead → KH).

#### DB (0.25 ngày)

- [ ] `T-G5.2.DB.01` (0.5h) — Verify `chien_dich_mk`, `lead`.

#### BE (1.5 ngày)

- [ ] `T-G5.2.BE.01` (2h) — `ChienDichMkService.create/update` — validate ngân sách > 0, thời gian hợp lệ.
- [ ] `T-G5.2.BE.02` (2h) — `LeadService.create(campaign_id, ...)` — trạng thái default `moi`.
- [ ] `T-G5.2.BE.03` (2h) — `LeadService.update_status(id, status)` — 4 trạng thái BR-MK-02.
- [ ] `T-G5.2.BE.04` (3h) — `LeadService.convert_to_customer(lead_id)` — BR-MK-03: insert vào `khach_hang` + chuyển trạng thái `chuyen_doi`.
- [ ] `T-G5.2.BE.05` (2h) — `ChienDichMkService.calculate_conversion_rate(id)` — BR-CALC-06.

#### UI (1.5 ngày)

- [ ] `T-G5.2.UI.01` (3h) — `S-MK-01` Campaign List: bảng + cột ngân sách + tỷ lệ chuyển đổi.
- [ ] `T-G5.2.UI.02` (3h) — `S-MK-02` Create Campaign Form: tên, ngân sách, thời gian, kênh tiếp thị (dropdown), mục tiêu.
- [ ] `T-G5.2.UI.03` (4h) — `S-MK-03` Lead Manager: bảng lead + filter trạng thái + nút "Cập nhật trạng thái" + nút "Chuyển thành KH".

#### TEST (0.5 ngày)

- [ ] `T-G5.2.TEST.01` (1h) — Unit test `convert_to_customer` → KH được tạo + lead chuyển trạng thái.
- [ ] `T-G5.2.TEST.02` (1h) — Unit test `calculate_conversion_rate` (BR-CALC-06).
- [ ] `T-G5.2.TEST.03` (1h) — Integration WF-07: tạo chiến dịch → thêm lead → cham sóc → chuyển KH → tạo HĐ.
- [ ] `T-G5.2.TEST.04` (0.5h) — UAT theo AC-MK-*.

#### GIT (0.25 ngày)

- [ ] `T-G5.2.GIT.01` (0.5h) — Branch `feature/G5.2-module-marketing`.
- [ ] `T-G5.2.GIT.02` (1h) — PR review.
- [ ] `T-G5.2.GIT.03` (0.5h) — Merge → tag `vG5.2`.

---

### Sprint G5.3 — Module Khiếu nại — WF-06

**Phụ trách:** DEV-2.
**BRD ref:** §5.13 (BR-KN-01..05), UC-KN-01..04, S-KN-01..02, WF-06.

#### REQ (0.25 ngày)

- [ ] `T-G5.3.REQ.01` (1h) — Đọc BRD §5.13 + AC-KN-*.
- [ ] `T-G5.3.REQ.02` (0.5h) — Hiểu BR-KN-03 (KN cấp `cao` ưu tiên), BR-KN-04 (đánh giá hài lòng 1-5 trước khi đóng), BR-KN-05 (ghi lý do khi cập nhật trạng thái).

#### DB (0.25 ngày)

- [ ] `T-G5.3.DB.01` (0.5h) — Verify `khieu_nai`.

#### BE (1 ngày)

- [ ] `T-G5.3.BE.01` (2h) — `KhieuNaiService.create(data)` — KH/HĐ liên quan, mức độ, nội dung.
- [ ] `T-G5.3.BE.02` (2h) — `KhieuNaiService.assign(kn_id, nv_id)` — chỉ A-01 phân công.
- [ ] `T-G5.3.BE.03` (2h) — `KhieuNaiService.update_status(kn_id, status, ly_do)` — bắt buộc ghi `ly_do` nếu cập nhật (BR-KN-05).
- [ ] `T-G5.3.BE.04` (2h) — `KhieuNaiService.close(kn_id, satisfaction)` — BR-KN-04: bắt buộc đánh giá 1-5 trước khi đóng.

#### UI (1.5 ngày)

- [ ] `T-G5.3.UI.01` (3h) — `S-KN-01` Complaint List: filter mức độ + trạng thái; KN `cao` hiển thị ở đầu, badge đỏ.
- [ ] `T-G5.3.UI.02` (4h) — `S-KN-02` Detail & Process: tab Nội dung · Phân công (A-01) · Cập nhật trạng thái (textarea ly_do) · Đóng (5-sao satisfaction).
- [ ] `T-G5.3.UI.03` (1h) — Confirm dialog đóng KN nếu satisfaction chưa đánh giá → từ chối.

#### TEST (0.5 ngày)

- [ ] `T-G5.3.TEST.01` (1h) — Unit test `update_status` → reject nếu thiếu `ly_do` (BR-KN-05).
- [ ] `T-G5.3.TEST.02` (1h) — Unit test `close` → reject nếu chưa có satisfaction (BR-KN-04).
- [ ] `T-G5.3.TEST.03` (1h) — Integration WF-06: tạo KN → A-01 phân công → A-02 xử lý → đánh giá → đóng.
- [ ] `T-G5.3.TEST.04` (0.5h) — UAT theo AC-KN-*.

#### GIT (0.25 ngày)

- [ ] `T-G5.3.GIT.01` (0.5h) — Branch `feature/G5.3-module-khieu-nai`.
- [ ] `T-G5.3.GIT.02` (1h) — PR review.
- [ ] `T-G5.3.GIT.03` (0.5h) — Merge → tag `vG5.3`.

---

### Sprint G5.4 — Báo cáo (RP-01..07) & Dashboard tổng hợp

**Phụ trách:** DEV-1 (lead) + TL (Dashboard).
**BRD ref:** §5.14 (BR-BC-01..05), UC-BC-01..02, S-BC-01..04, S-DB-01, RP-01..07.

#### REQ (1 ngày)

- [ ] `T-G5.4.REQ.01` (2h) — Đọc BRD §5.14 + Mục 7 (Báo cáo & KPI) + AC-BC-*.
- [ ] `T-G5.4.REQ.02` (1h) — Liệt kê 7 báo cáo:
  - `RP-01` Doanh thu (`S-BC-01`)
  - `RP-02` Top 10 xe bán chạy (`S-BC-02`)
  - `RP-03` Hiệu suất NV (`S-BC-03`)
  - `RP-04` KH VIP (`S-BC-04`)
  - `RP-05` Chi phí BH (nhúng `S-BH-01`)
  - `RP-06` Hiệu quả KM (đã có ở `S-KM-03`)
  - `RP-07` Hiệu quả MK (đã có ở `S-MK-01`)
- [ ] `T-G5.4.REQ.03` (1h) — Đặc tả Dashboard `S-DB-01`: KPI tiles (doanh thu tháng, số HĐ, xe tồn, BH sắp hết, TG quá hạn, sinh nhật KH, KN cấp cao); biểu đồ doanh thu 12 tháng.

#### DB (0.5 ngày)

- [ ] `T-G5.4.DB.01` (1h) — Tạo các view SQL phục vụ báo cáo: `view_revenue_by_month`, `view_top_xe_sold`, `view_kpi_nv`, `view_vip_customers`.
- [ ] `T-G5.4.DB.02` (1h) — Verify index để query báo cáo nhanh < 3s với 10.000 record (C-PERF-04).

#### BE (3 ngày)

- [ ] `T-G5.4.BE.01` (3h) — `BaoCaoService.revenue(from_date, to_date, group_by, filters)` — RP-01: query động theo ngày/tháng/quý/năm + filter NV/dòng xe (BR-BC-01).
- [ ] `T-G5.4.BE.02` (2h) — `BaoCaoService.top_xe(from_date, to_date, top=10)` — RP-02 (BR-BC-02).
- [ ] `T-G5.4.BE.03` (2h) — `BaoCaoService.kpi_nv(month)` — RP-03: dùng `BR-CALC-05` cho từng NV.
- [ ] `T-G5.4.BE.04` (2h) — `BaoCaoService.vip_customers(top=N)` — RP-04 (BR-BC-03): sort `tong_gia_tri_mua` DESC.
- [ ] `T-G5.4.BE.05` (2h) — `BaoCaoService.warranty_cost(from, to)` — RP-05.
- [ ] `T-G5.4.BE.06` (3h) `[BLOCKER]` — `ExcelExporter` wrapper openpyxl: header bold + freeze pane + auto-fit width.
- [ ] `T-G5.4.BE.07` (1h) — `ExcelExporter.export_report(report_data, sheet_config, output_path)` — generic export.
- [ ] `T-G5.4.BE.08` (3h) — `DashboardService.get_summary(role, user_id)` — BR-BC-* tổng hợp KPI tile data.

#### UI (3 ngày)

- [ ] `T-G5.4.UI.01` (3h) — `S-BC-01` Revenue Report: filter (ngày/tháng/quý/năm + NV + dòng xe) + biểu đồ cột (`QChart`) + bảng + nút "Xuất Excel".
- [ ] `T-G5.4.UI.02` (2h) — `S-BC-02` Top 10 Xe: bảng + biểu đồ cột ngang + filter thời gian.
- [ ] `T-G5.4.UI.03` (3h) — `S-BC-03` Employee Performance: bảng KPI + biểu đồ so sánh + xuất Excel.
- [ ] `T-G5.4.UI.04` (2h) — `S-BC-04` VIP Customers: list + xuất Excel + nút "Gửi tin nhắn chăm sóc" (mock).
- [ ] `T-G5.4.UI.05` (4h) `[BLOCKER]` — `S-DB-01` Dashboard chính: 7 KpiCard ở grid + biểu đồ doanh thu 12 tháng (`QChart` line) + danh sách "Cảnh báo" (BH 30 ngày, TG quá hạn, sinh nhật KH).
- [ ] `T-G5.4.UI.06` (2h) — Lazy load Dashboard: hiển thị skeleton ngay, query async (`QThread`) → render khi xong.
- [ ] `T-G5.4.UI.07` (2h) — Click vào KPI tile → navigate đến màn hình chi tiết tương ứng.
- [ ] `T-G5.4.UI.08` (1h) — Auto refresh Dashboard mỗi 5 phút.

#### TEST (1 ngày)

- [ ] `T-G5.4.TEST.01` (2h) — Unit test 7 hàm báo cáo với data fixture lớn (1000 HĐ).
- [ ] `T-G5.4.TEST.02` (2h) — Test xuất Excel: file mở được, có header, có data.
- [ ] `T-G5.4.TEST.03` (1h) — Test performance: query báo cáo với 10.000 record < 3s (C-PERF-04).
- [ ] `T-G5.4.TEST.04` (1h) — Test Dashboard summary: số liệu khớp với từng query rời.
- [ ] `T-G5.4.TEST.05` (1h) — UAT theo AC-BC-*.

#### GIT (0.5 ngày)

- [ ] `T-G5.4.GIT.01` (0.5h) — Branch `feature/G5.4-bao-cao-dashboard`.
- [ ] `T-G5.4.GIT.02` (1h) — PR + screenshot Dashboard + Excel xuất → review TL.
- [ ] `T-G5.4.GIT.03` (0.5h) — Merge → tag `vG5.4` → **đóng milestone Phase G5**.

**Definition of Done — Phase G5:**

- ✅ 4 module bổ sung hoàn chỉnh.
- ✅ 7 báo cáo (RP-01..07) chạy + xuất Excel.
- ✅ Dashboard hiển thị đầy đủ KPI tile + biểu đồ.
- ✅ WF-05, 06, 07 chạy E2E.
- ✅ Tag `vG5.4`.

---

## 9. PHASE G6 — HOÀN THIỆN & BÀN GIAO

> **Thời gian:** 3 tuần (~15 ngày). **Mục tiêu:** kiểm thử toàn diện, hardening, đóng gói `.exe`, viết tài liệu, bàn giao.

### Sprint G6.1 — System Integration Testing (SIT) & Bug Fix

**Mục tiêu:** Test toàn bộ 8 workflow E2E + sửa hết bug nghiêm trọng.
**Phụ trách:** DEV-2 (test lead) + cả nhóm.

#### REQ (0.5 ngày)

- [ ] `T-G6.1.REQ.01` (2h) — Đọc lại BRD Mục 6 (8 workflow E2E) + Mục 9 (toàn bộ AC-XX-NN).
- [ ] `T-G6.1.REQ.02` (1h) — Lập test plan SIT: ma trận `Workflow × Role × Test case`.
- [ ] `T-G6.1.REQ.03` (1h) — Thiết lập "test environment" độc lập với "dev environment" (DB seed riêng, user mẫu).

#### DB (0.25 ngày)

- [ ] `T-G6.1.DB.01` (1h) — Seed test data lớn: 1000 KH, 5000 HĐ, 100 NCC, 200 BH (cho perf test).
- [ ] `T-G6.1.DB.02` (0.5h) — Backup DB sạch để rollback giữa các test run.

#### BE (1 ngày — thêm helper test)

- [ ] `T-G6.1.BE.01` (2h) — Helper `tests/integration/test_workflow.py`: chạy WF-01..08 tự động.
- [ ] `T-G6.1.BE.02` (2h) — Helper `tests/perf/` đo thời gian các query trọng yếu.

#### UI (N/A — chỉ test UI hiện có)

#### TEST (4 ngày) — Phần lớn thời gian Sprint

- [ ] `T-G6.1.TEST.01` (3h) `[BLOCKER]` — SIT WF-01: Nhập kho — 3 role, edge case (NCC thiếu, đơn 0 item).
- [ ] `T-G6.1.TEST.02` (4h) `[BLOCKER]` — SIT WF-02: Bán xe chuẩn — 3 role × 4 case (no KM, có KM tiền, có KM %, có combo PK).
- [ ] `T-G6.1.TEST.03` (3h) — SIT WF-03: Bán trả góp — 3 case lãi suất khác nhau.
- [ ] `T-G6.1.TEST.04` (3h) — SIT WF-04: Bảo hành — miễn phí + tính phí + ngoài hạn.
- [ ] `T-G6.1.TEST.05` (2h) — SIT WF-05: Bảo dưỡng định kỳ.
- [ ] `T-G6.1.TEST.06` (2h) — SIT WF-06: Khiếu nại — 3 mức độ.
- [ ] `T-G6.1.TEST.07` (2h) — SIT WF-07: Marketing → Lead → KH.
- [ ] `T-G6.1.TEST.08` (2h) — SIT WF-08: Hủy hợp đồng — verify hoàn tồn kho + xoá BH/TG.
- [ ] `T-G6.1.TEST.09` (2h) — Test phân quyền: 3 role × 42 màn hình → đúng quyền theo BRD §3.4.
- [ ] `T-G6.1.TEST.10` (2h) — Test edge case: nhập tiếng Việt có dấu, nhập số quá lớn (10^15), ký tự đặc biệt.
- [ ] `T-G6.1.TEST.11` (2h) — Test concurrent (50 user mô phỏng): C-PERF-03 — không lỗi DB lock.
- [ ] `T-G6.1.TEST.12` (2h) — Test recovery: kill app giữa transaction → restart → DB nhất quán.
- [ ] `T-G6.1.TEST.13` (4h) — Bug bash session 1 ngày toàn nhóm + log bug vào GitHub Issues.

#### GIT (1.5 ngày — fix bug)

- [ ] `T-G6.1.GIT.01` (0.5h) — Branch `release/v1.0` từ `dev`.
- [ ] `T-G6.1.GIT.02` (1d) — Sửa các bug critical/high (P0, P1) trên `release/v1.0` qua nhiều `hotfix/*` PR.
- [ ] `T-G6.1.GIT.03` (1h) — Re-test sau khi sửa bug (smoke test 3 WF chính).
- [ ] `T-G6.1.GIT.04` (0.5h) — Tag `vG6.1` (RC1 — Release Candidate 1).

---

### Sprint G6.2 — Performance & Security Hardening

**Mục tiêu:** Đáp ứng C-PERF-01..05 + C-SEC-01..05 + audit kỹ thuật.
**Phụ trách:** TL (lead).

#### REQ (0.5 ngày)

- [ ] `T-G6.2.REQ.01` (1h) — Đọc BRD Mục 8.3 (yêu cầu phi chức năng) — perf, sec, usability, portability.
- [ ] `T-G6.2.REQ.02` (1h) — Liệt kê các điểm cần tối ưu: query chậm, UI lag, log nhạy cảm.

#### DB (0.5 ngày)

- [ ] `T-G6.2.DB.01` (2h) — Profile các query chậm bằng `EXPLAIN QUERY PLAN`; thêm index nếu thiếu.
- [ ] `T-G6.2.DB.02` (1h) — Verify `PRAGMA journal_mode = WAL` đã bật → tăng concurrent read.
- [ ] `T-G6.2.DB.03` (1h) — Verify backup script chạy đúng cron task Windows.

#### BE (2 ngày)

- [ ] `T-G6.2.BE.01` (2h) — Cache `system_settings` trong memory (refresh 5 phút) — tránh query lặp.
- [ ] `T-G6.2.BE.02` (3h) — Threading: chuyển query nặng (báo cáo, dashboard) sang `QThread` (C-PERF-02).
- [ ] `T-G6.2.BE.03` (2h) — Pagination: mọi list > 100 record bắt buộc phân trang server-side.
- [ ] `T-G6.2.BE.04` (2h) — **Security audit:** verify bcrypt cost = 12 (BR-SEC-04), session timeout = 30 phút (BR-TIME-07).
- [ ] `T-G6.2.BE.05` (2h) — Loại bỏ log có chứa password/PII; mask SĐT/email trong log.
- [ ] `T-G6.2.BE.06` (1h) — Verify mọi service quan trọng có `@require_permission` đúng ma trận §3.4.
- [ ] `T-G6.2.BE.07` (2h) — SQL injection scan: review tất cả query — phải dùng parameterized.

#### UI (1 ngày)

- [ ] `T-G6.2.UI.01` (2h) — Test idle timeout: app không thao tác 30 phút → modal "Phiên hết hạn" → quay về login (BR-TIME-07).
- [ ] `T-G6.2.UI.02` (1h) — Loading spinner cho mọi action > 500ms.
- [ ] `T-G6.2.UI.03` (1h) — Hiển thị thông báo "Phiên DB mất kết nối" nếu DB bị lock/file mất.
- [ ] `T-G6.2.UI.04` (2h) — Validate input toàn UI: chặn ký tự `<>` trong text field (XSS phòng ngừa khi xuất Excel/PDF).

#### TEST (1.5 ngày)

- [ ] `T-G6.2.TEST.01` (2h) `[BLOCKER]` — Perf C-PERF-01: query xe < 2s với 10.000 record.
- [ ] `T-G6.2.TEST.02` (2h) — Perf C-PERF-02: tải dashboard < 3s.
- [ ] `T-G6.2.TEST.03` (1h) — Perf C-PERF-03: 50 user concurrent → không lỗi.
- [ ] `T-G6.2.TEST.04` (1h) — Perf C-PERF-04: báo cáo < 3s với 10.000 HĐ.
- [ ] `T-G6.2.TEST.05` (1h) — Perf C-PERF-05: phục hồi backup < 15 phút.
- [ ] `T-G6.2.TEST.06` (2h) — Sec C-SEC-01: brute force password → bị khoá sau 5 lần.
- [ ] `T-G6.2.TEST.07` (1h) — Sec C-SEC-02: SQL injection thử trên ô tìm kiếm → an toàn.
- [ ] `T-G6.2.TEST.08` (1h) — Sec C-SEC-03: audit log không chứa password.
- [ ] `T-G6.2.TEST.09` (1h) — Sec C-SEC-04: file backup mã hoá hoặc đường dẫn cấm public.

#### GIT (0.5 ngày)

- [ ] `T-G6.2.GIT.01` (0.5h) — Branch `release/v1.0` (tiếp tục từ G6.1).
- [ ] `T-G6.2.GIT.02` (1h) — PR review TL bắt buộc.
- [ ] `T-G6.2.GIT.03` (0.5h) — Merge → tag `vG6.2` (RC2).

---

### Sprint G6.3 — Packaging & Deployment (`.exe`)

**Mục tiêu:** Build file `.exe` chạy độc lập trên Windows + installer.
**Phụ trách:** TL.

#### REQ (0.25 ngày)

- [ ] `T-G6.3.REQ.01` (1h) — Đọc TECH_STACK.md §3.8 (PyInstaller).
- [ ] `T-G6.3.REQ.02` (0.5h) — Liệt kê resource phải bundle: icon, qss, jinja2 templates, weasyprint fonts.

#### DB (0.25 ngày)

- [ ] `T-G6.3.DB.01` (0.5h) — DB rỗng `data/car_management.db.template` để installer copy lần đầu.
- [ ] `T-G6.3.DB.02` (0.5h) — First-run wizard: tạo admin gốc + nhập tên đại lý.

#### BE (0.5 ngày)

- [ ] `T-G6.3.BE.01` (1h) — `app/bootstrap.py`: kiểm tra DB tồn tại, nếu không → chạy migration + seed admin.
- [ ] `T-G6.3.BE.02` (1h) — Đọc đường dẫn DB từ `%APPDATA%\CarManagement\data\` (không ở chỗ cài).

#### UI (0.5 ngày)

- [ ] `T-G6.3.UI.01` (2h) — First-run wizard 3 bước: chọn ngôn ngữ → cài đặt đại lý → tạo mật khẩu admin.
- [ ] `T-G6.3.UI.02` (1h) — Splash screen 2-3 giây khi khởi động.
- [ ] `T-G6.3.UI.03` (1h) — Icon app + favicon đa kích cỡ (16, 32, 48, 256).

#### TEST (1 ngày)

- [ ] `T-G6.3.TEST.01` (1h) — Build PyInstaller spec file + build thử.
- [ ] `T-G6.3.TEST.02` (2h) — Test `.exe` trên Windows 10/11 sạch (máy ảo) — không cần Python cài sẵn.
- [ ] `T-G6.3.TEST.03` (1h) — Test với user thường (không admin Windows) — quyền ghi vào `%APPDATA%`.
- [ ] `T-G6.3.TEST.04` (2h) — Test offline: app chạy không cần internet (BR-PORT-01).
- [ ] `T-G6.3.TEST.05` (2h) — Smoke test 3 WF chính trên `.exe` build.
- [ ] `T-G6.3.TEST.06` (1h) — Test installer Inno Setup / NSIS: cài → chạy → uninstall → DB không bị xoá nếu chọn keep.

#### GIT (0.5 ngày)

- [ ] `T-G6.3.GIT.01` (0.5h) — Branch `feature/G6.3-packaging`.
- [ ] `T-G6.3.GIT.02` (1h) — `scripts/build.ps1`: chạy PyInstaller + Inno Setup tự động.
- [ ] `T-G6.3.GIT.03` (0.5h) — Workflow `.github/workflows/release.yml`: tự build `.exe` khi tag `v*` được tạo, upload artifact.
- [ ] `T-G6.3.GIT.04` (0.5h) — Tag `vG6.3` (RC3).

---

### Sprint G6.4 — Documentation, UAT cuối & Release v1.0

**Mục tiêu:** Hoàn thiện tài liệu, UAT cuối với stakeholder, release `v1.0` chính thức.
**Phụ trách:** Cả nhóm.

#### REQ (0.5 ngày)

- [ ] `T-G6.4.REQ.01` (1h) — Lập checklist tài liệu cần giao.
- [ ] `T-G6.4.REQ.02` (1h) — Lên kịch bản UAT cuối với stakeholder (chủ đại lý / giảng viên).

#### DB (N/A)

#### BE (N/A)

#### UI (N/A)

#### TEST — Tài liệu & UAT (4 ngày)

- [ ] `T-G6.4.TEST.01` (3h) — Cập nhật `README.md`: hướng dẫn cài đặt, chạy, screenshots.
- [ ] `T-G6.4.TEST.02` (4h) — Viết `docs/USER_MANUAL.md`: hướng dẫn sử dụng cho 3 role (kèm screenshots).
- [ ] `T-G6.4.TEST.03` (2h) — Viết `docs/INSTALLATION_GUIDE.md`: cài đặt từng bước trên Windows.
- [ ] `T-G6.4.TEST.04` (2h) — Viết `docs/ADMIN_GUIDE.md`: backup/restore, system settings, troubleshoot.
- [ ] `T-G6.4.TEST.05` (3h) — Viết `docs/TEST_REPORT.md`: tổng hợp kết quả test G6.1, G6.2 + coverage report HTML.
- [ ] `T-G6.4.TEST.06` (2h) — Cập nhật `PLAN.md` đánh dấu các task đã hoàn thành; cập nhật `BUSINESS_REQUIREMENTS.md` "Phụ lục A. Lịch sử thay đổi" → v1.0.
- [ ] `T-G6.4.TEST.07` (4h) `[BLOCKER]` — UAT cuối với stakeholder: demo 8 workflow + xuất báo cáo + cài `.exe` trên máy stakeholder.
- [ ] `T-G6.4.TEST.08` (2h) — Ghi nhận feedback UAT, sửa nhanh các bug nhỏ (P2, P3).
- [ ] `T-G6.4.TEST.09` (1h) — Final regression test trên `.exe`.

#### GIT — Release (0.5 ngày)

- [ ] `T-G6.4.GIT.01` (0.5h) — Merge `release/v1.0` → `main` (PR review tất cả thành viên).
- [ ] `T-G6.4.GIT.02` (0.5h) — Tag `v1.0.0` chính thức trên `main`.
- [ ] `T-G6.4.GIT.03` (0.5h) — GitHub Release: changelog + upload `.exe` + installer.
- [ ] `T-G6.4.GIT.04` (0.5h) — Cập nhật README.md với badge build status, version, download link.
- [ ] `T-G6.4.GIT.05` (1h) — Bàn giao: copy `.exe` + `docs/` + DB template cho stakeholder.

**Definition of Done — Phase G6 (Project Done):**

- ✅ SIT pass cho 8 workflow E2E + 3 role.
- ✅ Đáp ứng C-PERF-01..05 (perf benchmark) + C-SEC-01..05 (security audit).
- ✅ `.exe` build chạy được trên Windows 10/11 sạch.
- ✅ Installer Inno Setup hoặc NSIS hoạt động.
- ✅ Tài liệu đầy đủ: README, USER_MANUAL, INSTALLATION_GUIDE, ADMIN_GUIDE, TEST_REPORT.
- ✅ UAT cuối được stakeholder ký nhận.
- ✅ Release `v1.0.0` trên GitHub.
- ✅ Coverage tổng ≥ 80%.

---

## PHỤ LỤC A — GIT WORKFLOW CHUẨN

> Áp dụng cho **mọi sprint**. Bước GIT trong workflow chuẩn của mỗi sprint dựa trên các quy tắc dưới đây.

### A.1 Mô hình GitFlow

```text
main (production)
 │
 ├── release/v1.0  ──────────────────────────────►  merge → tag v1.0.0
 │     ▲
 │     │ (cherry-pick / merge từ dev khi feature đủ ổn định)
 │
dev (integration)
 │
 ├── feature/G2.1-database-schema   ─► PR → dev
 ├── feature/G2.2-authentication    ─► PR → dev
 ├── feature/G3.1-module-xe         ─► PR → dev
 │     ...
 │
 ├── hotfix/HD-cancel-rollback      ─► PR → release/v1.0 + dev
 │
 └── chore/update-docs              ─► PR → dev
```

### A.2 Quy ước đặt tên branch

| Loại | Pattern | Ví dụ |
| --- | --- | --- |
| Feature | `feature/<sprint-id>-<short-desc>` | `feature/G3.5-module-hop-dong` |
| Hotfix | `hotfix/<issue-id>-<short-desc>` | `hotfix/123-hd-cancel-rollback` |
| Release | `release/v<major>.<minor>` | `release/v1.0` |
| Chore | `chore/<short-desc>` | `chore/update-readme` |
| Docs | `docs/<short-desc>` | `docs/user-manual` |

### A.3 Conventional Commits

```text
<type>(<scope>): <subject>

<body>

<footer>
```

| Type | Dùng cho |
| --- | --- |
| `feat` | Thêm tính năng mới |
| `fix` | Sửa bug |
| `docs` | Sửa tài liệu |
| `style` | Sửa format (không đổi logic) |
| `refactor` | Refactor code |
| `test` | Thêm/sửa test |
| `chore` | Việc không liên quan code (config, deps) |
| `perf` | Tối ưu hiệu năng |

**Ví dụ:**

```text
feat(hd): tính tổng tiền theo BR-CALC-01

- Snapshot giá xe và phụ kiện vào hop_dong
- Áp dụng giảm theo loại KM (4 loại)
- Trả về breakdown chi tiết

Refs: BR-CALC-01, BR-CALC-02
Closes #45
```

### A.4 Quy trình Pull Request

1. Push branch lên GitHub.
2. Mở PR vào `dev` (feature) hoặc `release/v1.0` (hotfix).
3. **Tiêu đề PR:** `[<sprint-id>] <ngắn gọn>` — vd `[G3.5] Module Hợp đồng + PDF`.
4. Điền `PULL_REQUEST_TEMPLATE.md` (checklist DoD).
5. Gán reviewer theo `CODEOWNERS`:
   - Module SEC, HD, kiến trúc → **TL bắt buộc review**.
   - Module BC, Dashboard → DEV-1 + TL.
   - Test, BH, KM → DEV-2.
6. Đợi CI pass (pytest + flake8 + coverage ≥ 80%).
7. Reviewer approve → merge bằng **Squash & Merge** (1 commit gọn cho `dev`).
8. Xoá branch sau khi merge.
9. Tag `vG<phase>.<sprint>` ở commit cuối của sprint.

### A.5 Hotfix Flow (sau khi đã release)

1. Tạo branch `hotfix/<issue>-<desc>` từ `main`.
2. Sửa bug + viết test regression.
3. PR vào `main` → review TL → merge → tag `v1.0.<patch>`.
4. **Cherry-pick** commit này về `dev` để tránh quên fix khi release sau.

### A.6 Cấm

- ❌ Không push trực tiếp lên `main` hoặc `release/*`.
- ❌ Không force-push lên branch người khác đang làm.
- ❌ Không merge khi CI fail.
- ❌ Không commit file `.db`, `.env`, log, build artifact.
- ❌ Không commit credentials, API key, password.

---

## PHỤ LỤC B — DEFINITION OF DONE (DoD)

### B.1 DoD cho mỗi Task

Một task được xem là **Done** khi:

- ✅ Code đã được viết và tự test ở local.
- ✅ Code đã được lint sạch (`flake8`, `black`, `isort` không lỗi).
- ✅ Có log/comment hợp lý cho điểm phức tạp.
- ✅ Push lên branch và CI pass.

### B.2 DoD cho mỗi Sprint

Một sprint được xem là **Done** khi:

- ✅ Tất cả task con đã `[x]`.
- ✅ Coverage ≥ 80% các service mới.
- ✅ PR đã được merge vào `dev`.
- ✅ Tag `vG<phase>.<sprint>` đã được tạo.
- ✅ UAT theo Acceptance Criteria của sprint pass.
- ✅ Không còn bug `P0` hoặc `P1` open.

### B.3 DoD cho mỗi Phase

- ✅ Tất cả Sprint trong phase đã `Done`.
- ✅ Demo nội bộ + biên bản nghiệm thu phase.
- ✅ Cập nhật `PLAN.md` mục lộ trình (đánh dấu phase đã xong).
- ✅ Milestone GitHub đã đóng.

### B.4 DoD cho v1.0

- ✅ Tất cả Phase G1-G6 đã `Done`.
- ✅ 8 Workflow chạy E2E ổn định.
- ✅ 7 Báo cáo (RP-01..07) chạy đúng.
- ✅ `.exe` build cài đặt + chạy được trên Windows 10/11 clean.
- ✅ UAT cuối stakeholder ký xác nhận.
- ✅ Tag `v1.0.0` trên `main`.

### B.5 Phân loại Bug Priority

| Priority | Định nghĩa | SLA xử lý |
| --- | --- | --- |
| **P0 (Critical)** | App crash, DB corrupt, security hole | Sửa ngay (≤ 1h) |
| **P1 (High)** | Workflow bị chặn, sai số liệu HĐ/báo cáo | Sửa trong 1 ngày |
| **P2 (Medium)** | Lỗi UI, format, edge case nhỏ | Sửa trong sprint |
| **P3 (Low)** | Cosmetic, gợi ý cải thiện | Backlog phase sau |

---

## PHỤ LỤC C — MA TRẬN RACI

> R = Responsible (làm), A = Accountable (chịu trách nhiệm), C = Consulted (tư vấn), I = Informed (được biết).

### C.1 RACI theo Sprint

| Sprint | TL | DEV-1 | DEV-2 |
| --- | :---: | :---: | :---: |
| **G1.1** Project setup | A, R | R | R |
| **G2.1** DB schema | A, R | C | R (test) |
| **G2.2** Authentication | A, R | C | R (test) |
| **G2.3** Main layout | A | R | C |
| **G2.4** Audit log | A, C | C | R |
| **G3.1** Module Xe | A, R | C | C |
| **G3.2** Module KH | A | R | C |
| **G3.3** Module NV | A | C | R |
| **G3.4** Module Kho | A | R | C |
| **G3.5** Module HĐ + PDF | A, R | R (UI) | R (test) |
| **G4.1** Phụ kiện | A | R | C |
| **G4.2** Khuyến mãi | A | C | R |
| **G4.3** Bảo hành | A | C | R |
| **G4.4** NCC + ĐĐH | A | R | C |
| **G4.5** Trả góp | A, R | C | R (test) |
| **G5.1** Hậu mãi | A | C | R |
| **G5.2** Marketing | A | R | C |
| **G5.3** Khiếu nại | A | C | R |
| **G5.4** Báo cáo + Dashboard | A, R | R | C |
| **G6.1** SIT | A, C | R | R |
| **G6.2** Perf + Sec | A, R | C | R |
| **G6.3** Packaging | A, R | C | C |
| **G6.4** Docs + Release | A | R | R |

### C.2 Tổng hợp khối lượng theo người

| Vai trò | Sprint A (Accountable) | Sprint R (Responsible chính) |
| --- | :---: | :---: |
| **TL — Cao Văn Hiếu** | 23 (toàn dự án) | G1.1, G2.1, G2.2, G3.1, G3.5, G4.5, G5.4, G6.2, G6.3 (9) |
| **DEV-1 — Lê Minh Đạt** | 0 | G3.2, G3.4, G4.1, G4.4, G5.2, G5.4 (6) |
| **DEV-2 — Nguyễn Hữu Hải** | 0 | G2.4, G3.3, G4.2, G4.3, G5.1, G5.3, G6.1 (7) |

### C.3 Quy tắc làm việc nhóm

- **Daily standup**: 9h sáng (15 phút) — nói nhanh hôm qua làm gì, hôm nay làm gì, blocker nào.
- **Sprint review**: cuối mỗi sprint — demo cho cả nhóm + log feedback.
- **Sprint retro**: cuối mỗi phase — bàn cải thiện.
- **Code review**: ≤ 24h sau khi PR mở; nếu không response, nhắc trực tiếp.
- **Pair programming**: bắt buộc cho task `[BLOCKER]` (TL + 1 DEV).

---

## TỔNG KẾT

| Hạng mục | Giá trị |
| --- | --- |
| **Tổng số Phase** | 6 |
| **Tổng số Sprint** | 23 |
| **Tổng số Task** | ~480 |
| **Tổng thời gian dự kiến** | ~16 tuần (~80 ngày làm việc) |
| **Tài liệu liên kết** | `PLAN.md`, `BUSINESS_REQUIREMENTS.md`, `DATABASE_PLAN.md`, `UI_UX_PLAN.md`, `STAKEHOLDERS.md`, `TECH_STACK.md` |

> 💡 **Cách dùng tài liệu này:**
>
> 1. Mở Sprint hiện tại đang làm.
> 2. Đi qua các bước **REQ → DB → BE → UI → TEST → GIT** theo thứ tự.
> 3. Đánh dấu `[x]` mỗi task khi hoàn thành.
> 4. Đối chiếu `BR-XX-NN`, `UC-XX-NN`, `S-XXX-NN` về BRD/UI Plan để chắc chắn không bỏ sót nghiệp vụ.
> 5. Tag Git theo đúng quy ước cuối mỗi Sprint.

**Phiên bản tài liệu:** 1.0
**Cập nhật lần cuối:** Phase G1 — chuẩn bị khởi tạo dự án.
