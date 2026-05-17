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
from app.infrastructure.database.migrations.migration_015_hop_dong_indexes import run as run_015
from app.infrastructure.database.migrations.migration_016_pk_categories import run as run_016
from app.infrastructure.database.migrations.migration_017_bh_ngay_ket_thuc_index import run as run_017
from app.infrastructure.database.migrations.migration_018_tg_indexes import run as run_018
from app.infrastructure.database.migrations.migration_019_kn_improvements import run as run_019
from app.infrastructure.database.migrations.migration_020_report_views import run as run_020
from app.infrastructure.database.migrations.migration_021_dashboard_indexes import run as run_021
from app.infrastructure.database.migrations.migration_022_nv_kpi_columns import run as run_022
from app.infrastructure.database.migrations.migration_023_sit_missing_columns import run as run_023
from app.infrastructure.database.migrations.migration_024_bao_hanh_external import run as run_024
from app.infrastructure.database.migrations.migration_025_bao_hiem import run as run_025
from app.infrastructure.database.migrations.migration_026_bao_hiem_table import run as run_026
from app.infrastructure.database.migrations.migration_027_dai_ly import run as run_027
from app.infrastructure.database.migrations.migration_028_cong_ty_bh import run as run_028
from app.infrastructure.database.migrations.migration_029_bao_hiem_extend import run as run_029
from app.infrastructure.database.migrations.migration_030_fix_ncc_score import run as run_030
from app.infrastructure.database.migrations.migration_031_bao_hiem_gia_tri import run as run_031
from app.infrastructure.database.migrations.migration_032_cuu_ho_trang_thai import run as run_032
from app.infrastructure.database.migrations.migration_033_bao_hiem_da_thanh_toan import run as run_033
from app.infrastructure.database.migrations.migration_034_khach_hang_trang_thai import run as run_034
from app.infrastructure.database.migrations.migration_035_hop_dong_da_thanh_toan import run as run_035
from app.infrastructure.database.migrations.migration_036_nhan_vien_dia_chi import run as run_036
from app.infrastructure.database.migrations.migration_037_nha_cung_cap_recreate import run as run_037


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
    (15, "015_hop_dong_indexes", run_015),
    (16, "016_pk_categories", run_016),
    (17, "017_bh_ngay_ket_thuc_index", run_017),
    (18, "018_tg_indexes", run_018),
    (19, "019_kn_improvements", run_019),
    (20, "020_report_views", run_020),
    (21, "021_dashboard_indexes", run_021),
    (22, "022_nv_kpi_columns", run_022),
    (23, "023_sit_missing_columns", run_023),
    (24, "024_bao_hanh_external", run_024),
    (25, "025_bao_hiem", run_025),
    (26, "026_bao_hiem_table", run_026),
    (27, "027_dai_ly", run_027),
    (28, "028_cong_ty_bh", run_028),
    (29, "029_bao_hiem_extend", run_029),
    (30, "030_fix_ncc_score", run_030),
    (31, "031_bao_hiem_gia_tri", run_031),
    (32, "032_cuu_ho_trang_thai", run_032),
    (33, "033_bao_hiem_da_thanh_toan", run_033),
    (34, "034_khach_hang_trang_thai", run_034),
    (35, "035_hop_dong_da_thanh_toan", run_035),
    (36, "036_nhan_vien_dia_chi", run_036),
    (37, "037_nha_cung_cap_recreate", run_037),
]