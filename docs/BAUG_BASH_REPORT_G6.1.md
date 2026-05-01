# Bug Bash Report — G6.1 SIT Testing

**Date**: 2026-05-01  
**Phase**: System Integration Testing (SIT)  
**Group**: G6.1  
**Repository**: Car-Management  
**Branch**: `feature/sit-test-infrastructure`

---

## Summary

This report documents bugs found during G6.1 SIT testing workflow tests (WF-01 through WF-08) and previous test runs.

---

## Bug #1 — WF-05: `trang_thai` Validation Mismatch

| Field | Value |
|-------|-------|
| **Bug ID** | WF-05 |
| **Severity** | P2 |
| **Module** | Bảo dưỡng (BaoDuongService) |
| **Status** | ✅ Fixed |
| **Fixed In** | Commit `2f07b93` |
| **Affected Test** | Workflow test WF-05 |

### Description

The `trang_thai` validation in `BaoDuongService.update()` expected value `"hoan_thanh"` but the database schema uses `"da_hoan_thanh"`.

### Expected vs Actual

- **Expected**: `trang_thai` = `"hoan_thanh"` is valid
- **Actual**: Schema only accepts `"da_hoan_thanh"` — validation was rejecting valid database values

### Root Cause

Service-level validation used incorrect enum value.

### Fix

Changed `trang_thai` validation in `bao_duong_service.py` from `"hoan_thanh"` to `"da_hoan_thanh"` to match database schema.

---

## Bug #2 — WF-06: `KhieuNaiService.update()` Signature Mismatch

| Field | Value |
|-------|-------|
| **Bug ID** | WF-06 |
| **Severity** | P2 |
| **Module** | Khiếu nại (KhieuNaiService) |
| **Status** | ✅ Fixed |
| **Fixed In** | Commit `5fd671e` |
| **Affected Test** | Workflow test WF-06 |

### Description

`KhieuNaiService.update()` was called with 3 arguments in tests (`id`, `data`, `nv_id`) but the service method only accepted 2 arguments (`id`, `data`).

### Steps to Reproduce

1. Call `KhieuNaiService.update(id, data, nv_id)` with 3 args
2. Get TypeError: `update() missing 1 required positional argument`

### Expected vs Actual

- **Expected**: `update(id, data, nv_id)` — accepts `nv_id` for audit trail
- **Actual**: `update(id, data)` — missing `nv_id` parameter

### Fix

Added `nv_id` parameter to `KhieuNaiService.update()` method signature.

---

## Bug #3 — WF-07: `ChienDichMkService.update()` Signature Mismatch

| Field | Value |
|-------|-------|
| **Bug ID** | WF-07 |
| **Severity** | P2 |
| **Module** | Chiến dịch marketing (ChienDichMkService) |
| **Status** | ✅ Fixed |
| **Fixed In** | Commit `8197dde` |
| **Affected Test** | Workflow test WF-07 |

### Description

`ChienDichMkService.update()` was called with 3 arguments in tests (`id`, `data`, `nv_id`) but the service method only accepted 2 arguments (`id`, `data`).

### Steps to Reproduce

1. Call `ChienDichMkService.update(id, data, nv_id)` with 3 args
2. Get TypeError: `update() missing 1 required positional argument`

### Expected vs Actual

- **Expected**: `update(id, data, nv_id)` — accepts `nv_id` for audit trail
- **Actual**: `update(id, data)` — missing `nv_id` parameter

### Fix

Added `nv_id` parameter to `ChienDichMkService.update()` method signature.

---

## Bug #4 — CHECK Constraint: `phan_loai` Enum Value Error

| Field | Value |
|-------|-------|
| **Bug ID** | CHECK-01 |
| **Severity** | P2 |
| **Module** | Performance Test Fixtures |
| **Status** | ✅ Fixed |
| **Fixed In** | Commit `d412cd0` |
| **Affected Test** | Performance tests (perf test fixture) |

### Description

The performance test fixture used `phan_loai = 'Vip'` in INSERT statements, but the database CHECK constraint only allows `'Than_thiet'` (not `'Vip'`).

### Steps to Reproduce

1. Run perf tests with fixture data
2. Database INSERT fails — CHECK constraint violation

### Expected vs Actual

- **Expected**: `phan_loai = 'Than_thiet'` (valid enum value)
- **Actual**: Fixture used `phan_loai = 'Vip'` (invalid — not in CHECK constraint)

### Fix

Changed fixture data from `'Vip'` to `'Than_thiet'` in `tests/perf/conftest.py`.

---

## Bug #5 — SIT Bug Fixes (Multiple Issues)

| Field | Value |
|-------|-------|
| **Bug ID** | SIT-01 |
| **Severity** | P1 |
| **Module** | Multiple |
| **Status** | ✅ Fixed |
| **Fixed In** | Commit `ef27927` |
| **Affected Test** | Various SIT tests |

### Description

Multiple bugs in SIT tests were fixed in commit `ef27927` — "Fix loi bug trong cac test SIT - BO phien ban beta 2". This appears to be a batch fix for various issues discovered during beta 2 testing.

### Status

✅ Fixed — specific fixes include:
- Workflow test updates and `trang_thai` status path fixes
- Updated warranty status confirmation path
- Other SIT-specific bug fixes

---

## Metrics

| Metric | Count |
|--------|-------|
| Total Bugs Found | 5 |
| Fixed | 5 |
| Open | 0 |
| P1 | 1 |
| P2 | 4 |
| P3 | 0 |

---

## Files Changed (Fixed Bugs)

| Commit | Description |
|--------|-------------|
| `2f07b93` | Fix trang_thai validation cho bao duong service |
| `5fd671e` | Fix update signature cho KhieuNaiService |
| `8197dde` | Fix update signature cho ChienDichMkService |
| `d412cd0` | Fix CHECK constraint loi trong perf test fixture |
| `ef27927` | Fix loi bug trong cac test SIT - BO phien ban beta 2 |

---

*Report generated: 2026-05-01*
