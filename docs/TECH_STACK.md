# TAI LIEU TECH STACK

**Phan mem quan ly dai ly xe hoi**

---

## 1. Tong quan

Tai lieu nay mo ta bo tech stack du kien cho ung dung desktop quan ly dai ly xe hoi. Tech stack tap trung vao tinh don gian, de trien khai va phu hop voi yeu cau da neu trong [README.md].

---

## 2. Bang tong hop

| Tang        | Cong nghe                       | Vai tro                                  |
| ----------- | ------------------------------- | ---------------------------------------- |
| Ngon ngu    | Python 3.x (khuyen nghi 3.10+)  | Xu ly nghiep vu, dieu phoi he thong      |
| UI          | PyQt6                           | Giao dien desktop, tuong tac nguoi dung  |
| Bieu do     | Qt Charts                       | Hien thi dashboard, thong ke, doanh thu  |
| CSDL        | SQLite                          | Luu tru du lieu noi bo, de trien khai    |
| Bao mat     | bcrypt (thu vien Python)        | Bam mat khau theo yeu cau bao mat        |
| Kiem thu    | pytest (khuyen nghi)            | Unit test cho cac ham nghiep vu          |
| Logging     | logging (Python built-in)       | Ghi log he thong, debug loi              |
| Phat hanh   | PyInstaller (tuy chon)          | Dong goi thanh file chay tren Windows    |

---

## 3. Chi tiet tung lop

### 3.1 Ngon ngu va runtime

- Python 3.x (khuyen nghi 3.10+).
- Su dung thu vien tieu chuan `sqlite3` de lam viec voi CSDL.

### 3.2 UI Desktop

- PyQt6 la thu vien giao dien chinh.
- Ho tro TableView, Form, Dialog, Sidebar, Tab view.
- Co the ket hop bieu do vao giao dien de tao dashboard.

### 3.3 Thu vien bieu do va dashboard



#### 3.3.1 Qt Charts

- Hieu nang cao, render nhanh.
- Phu hop bieu do realtime:
  - So xe ton kho
  - Luot giao dich trong ngay
  - Theo doi KPI nhan vien



### 3.3.2 Loai dashboard co the xay dung

- Tong doanh thu hom nay / thang nay
- Xe con ton kho
- Top nhan vien ban hang
- So hop dong moi
- Ty le don huy
- Khach hang tiem nang

### Hợp đồng 
- Jinja2 + WeasyPrint
- Làm template hợp đồng cực dễ
- UI đẹp như Word
- Tách file HTML riêng → rất chuyên nghiệp
### 3.4 Co so du lieu

- SQLite cho phep trien khai nhanh, khong can server rieng.
- Phu hop quy mo du lieu vua va nho.
- De backup va di chuyen du lieu.

### 3.5 Bao mat

- Bam mat khau bang `bcrypt`.
- Phan quyen theo vai tro:
  - Admin
  - Quan ly
  - Nhan vien ban hang
  - Ke toan

### 3.6 Kiem thu

- pytest duoc de xuat cho unit test.
- Kiem thu:
  - Tinh doanh thu
  - Tinh ton kho
  - Tao hop dong
  - Dang nhap

### 3.7 Logging

- Dung module `logging` cua Python.
- Luu log:
  - Dang nhap
  - Loi he thong
  - Tao / sua / xoa du lieu

### 3.8 Dong goi va phat hanh

- PyInstaller dong goi thanh file `.exe`.
- Co the cai dat truc tiep tai showroom.

---

## 4. Ghi chu pham vi

- Neu can dashboard dep hon co the nang cap them:
  - Qt Charts
  - Plotly + QWebEngineView
- Neu mo rong nhieu chi nhanh, nen chuyen sang PostgreSQL / MySQL.
- Tai lieu nay chi mo ta tech stack, khong bao gom chi tiet kien truc.

---
