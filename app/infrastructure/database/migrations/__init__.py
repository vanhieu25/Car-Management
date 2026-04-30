"""Database migrations management."""

from app.infrastructure.database.migrations.migration_001_users_roles import run as run_001
from app.infrastructure.database.migrations.migration_002_xe_khach_hang import run as run_002
from app.infrastructure.database.migrations.migration_003_hop_dong import run as run_003
from app.infrastructure.database.migrations.migration_004_phu_kien import run as run_004
from app.infrastructure.database.migrations.migration_005_khuyen_mai import run as run_005
from app.infrastructure.database.migrations.migration_006_bao_hanh import run as run_006
from app.infrastructure.database.migrations.migration_007_hau_mai import run as run_007
from app.infrastructure.database.migrations.migration_008_ncc_kho import run as run_008
from app.infrastructure.database.migrations.migration_009_tra_gop import run as run_009
from app.infrastructure.database.migrations.migration_010_marketing import run as run_010
from app.infrastructure.database.migrations.migration_011_khieu_nai import run as run_011
from app.infrastructure.database.migrations.migration_012_audit_settings import run as run_012
from app.infrastructure.database.migrations.migration_013_indexes import run as run_013
from app.infrastructure.database.migrations.migration_014_password_change_flag import run as run_014


MIGRATIONS = [
    (1, "001_users_roles", run_001),
    (2, "002_xe_khach_hang", run_002),
    (3, "003_hop_dong", run_003),
    (4, "004_phu_kien", run_004),
    (5, "005_khuyen_mai", run_005),
    (6, "006_bao_hanh", run_006),
    (7, "007_hau_mai", run_007),
    (8, "008_ncc_kho", run_008),
    (9, "009_tra_gop", run_009),
    (10, "010_marketing", run_010),
    (11, "011_khieu_nai", run_011),
    (12, "012_audit_settings", run_012),
    (13, "013_indexes", run_013),
    (14, "014_password_change_flag", run_014),
]