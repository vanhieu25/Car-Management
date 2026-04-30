# Phần mềm Quản lý Đại lý Xe hơi

**Car Dealership Management System** — Phần mềm desktop quản lý toàn diện hoạt động kinh doanh đại lý xe hơi.

## Giới thiệu

Phần mềm hỗ trợ quản lý:
- Xe và kho hàng
- Khách hàng và nhân viên
- Hợp đồng mua bán
- Bảo hành và bảo dưỡng
- Khuyến mãi và marketing
- Trả góp và báo cáo doanh thu

## Tech Stack

| Thành phần | Công nghệ |
|---|---|
| Ngôn ngữ | Python 3.10+ |
| Giao diện | PyQt6 |
| Cơ sở dữ liệu | SQLite |
| Bảo mật | bcrypt |
| PDF | Jinja2 + WeasyPrint |
| Excel | openpyxl |
| Testing | pytest |

## Cấu trúc dự án

```
car_management/
├── app/
│   ├── presentation/      # PyQt6 windows, dialogs, widgets
│   ├── application/       # Service, Use Case orchestrator
│   ├── domain/            # Entity, Value Object, business rules
│   ├── infrastructure/    # Repository, DB connection, PDF, Excel
│   └── shared/            # Utility, helper, constants
├── data/                  # SQLite DB + backup
├── tests/                 # pytest
├── docs/                  # Tài liệu
├── design/                # Design system
├── scripts/               # Build, migration scripts
├── resources/             # Icon, logo, qss, jinja2 templates
├── main.py                # Entry point
├── requirements.txt
├── requirements-dev.txt
└── pyproject.toml
```

## Cài đặt

### Yêu cầu

- Python 3.10 hoặc 3.11
- pip

### Các bước cài đặt

```bash
# Clone repository
git clone <repo-url>
cd Car-Management

# Tạo virtual environment (khuyến nghị)
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows

# Cài dependencies
pip install -r requirements.txt

# Cài dev dependencies (cho development)
pip install -r requirements-dev.txt

# Cài pre-commit hooks
pre-commit install
```

### Chạy ứng dụng

```bash
python main.py
```

### Chạy tests

```bash
pytest tests/ -v
```

### Code quality

```bash
# Format code
black app tests

# Sort imports
isort app tests

# Lint
flake8 app tests --max-line-length=88

# All checks
pre-commit run --all-files
```

## Quy ước

- Code style: Black + isort
- Commit message: Conventional Commits
- Branching: GitFlow
- Testing: ≥80% coverage

## Nhóm phát triển

| Thành viên | Vai trò |
|---|---|
| Cao Văn Hiếu | Trưởng nhóm |
| Lê Minh Đạt | Thành viên |
| Nguyễn Hữu Hải | Thành viên |

## License

MIT