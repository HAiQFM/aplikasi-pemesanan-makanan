# Dokumentasi Aplikasi Pemesanan Makanan

## 1. Design

### 1.1 Gambaran Umum
Aplikasi ini dibangun dengan Flask menggunakan arsitektur modular:
- `routes/` untuk endpoint per fitur.
- `templates/` untuk tampilan HTML (server-side rendering).
- `static/` untuk aset CSS, JavaScript, gambar, dan upload bukti pembayaran.
- `services/` untuk logika penyimpanan order berbasis file JSON.
- `models/` untuk definisi model SQLAlchemy (siap untuk pengembangan database relasional).

### 1.2 Arsitektur Komponen
- Entry point: `run.py`
- App factory: `src/app/__init__.py` (`create_app`)
- Registrasi blueprint: `src/app/routes/__init__.py`
- Blueprint utama:
  - `main_bp` (`/`)
  - `auth_bp` (`/auth/*`)
  - `menu_bp` (`/menu/*`)
  - `cart_bp` (`/cart/*`)
  - `order_bp` (`/order/*`)
  - `admin_bp` (`/admin/*`)

### 1.3 Alur Data Order
1. User checkout dari halaman `/order/checkout`.
2. Backend memvalidasi form, metode pembayaran, dan file bukti (jika diperlukan).
3. Data order disimpan melalui `app.services.order_store.create_order`.
4. Data order persist ke file `src/instance/orders.json`.
5. Admin melakukan verifikasi pembayaran dan update status melalui endpoint admin.

### 1.4 Penyimpanan Data
- Saat ini order menggunakan file JSON (`orders.json`) di folder `instance`.
- Bukti pembayaran disimpan di `src/app/static/uploads/payment-proofs/`.
- Model SQLAlchemy (`User`, `Menu`, `Category`, `Cart`, `Order`) sudah tersedia tetapi belum menjadi sumber data utama untuk alur order aktif.

## 2. Development

### 2.1 Prasyarat
- Python 3.8+
- `pip`

### 2.2 Instalasi
```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### 2.3 Konfigurasi Environment
Buat file `.env` di root project:

```env
SECRET_KEY=dev-secret-key
FLASK_ENV=development
FLASK_DEBUG=1
DATABASE_URL=sqlite:///app.db
```

Opsional:
- `ORDER_STORE_FILE` untuk override lokasi file order JSON.

### 2.4 Menjalankan Aplikasi
```powershell
python run.py
```
Default URL: `http://127.0.0.1:5000`

### 2.5 Menjalankan Test
```powershell
pytest -q
```

### 2.6 Struktur Direktori Utama
```text
src/app/
  config.py
  routes/
  services/
  models/
  templates/
  static/
tests/
run.py
```

## 3. User Guide

### 3.1 Alur Pengguna (Customer)
1. Buka halaman utama (`/`).
2. Register di `/auth/register` lalu login di `/auth/login`.
3. Lihat menu di `/menu/`.
4. Tambah item ke cart (`/cart/add`).
5. Checkout di `/order/checkout`:
   - `cash`: tidak perlu upload bukti.
   - `transfer`/`ewallet`: wajib upload bukti (`png`, `jpg`, `jpeg`, `pdf`).
6. Lihat status pesanan di `/order/history`.
7. Lihat ringkasan sukses di `/order/success`.

### 3.2 Alur Admin
1. Login admin dari `/auth/login` menggunakan email admin yang ada di source code.
2. Akses dashboard di `/admin/`.
3. Kelola menu dan kategori:
   - `/admin/menus`
   - `/admin/menus/add`
   - `/admin/menus/<id>/edit`
   - `/admin/categories`
4. Kelola order di `/admin/orders`:
   - verifikasi pembayaran,
   - update status order,
   - hapus order.

### 3.3 Catatan Session & Akses
- Session menyimpan status login, email user, role (`customer`/`admin`).
- Semua endpoint `/admin/*` dilindungi oleh middleware `before_request` dan hanya bisa diakses role admin.

## 4. API Endpoint

Catatan: aplikasi ini mayoritas endpoint HTML (render template + redirect), bukan REST JSON murni.

### 4.1 Main
| Method | Path | Auth | Keterangan |
|---|---|---|---|
| GET | `/` | Tidak | Halaman utama + ringkasan status order user login |

### 4.2 Auth (`/auth`)
| Method | Path | Auth | Keterangan |
|---|---|---|---|
| GET, POST | `/auth/login` | Tidak | Login customer/admin |
| GET, POST | `/auth/register` | Tidak | Registrasi customer (disimpan di session) |
| POST | `/auth/logout` | Ya | Logout user |
| POST | `/auth/logout-admin` | Ya (admin) | Logout admin ke halaman utama |

### 4.3 Menu (`/menu`)
| Method | Path | Auth | Keterangan |
|---|---|---|---|
| GET | `/menu/` | Tidak | Halaman daftar menu |
| GET | `/menu/<menu_id>` | Tidak | Halaman detail menu |

### 4.4 Cart (`/cart`)
| Method | Path | Auth | Keterangan |
|---|---|---|---|
| GET | `/cart/` | Tidak | Lihat keranjang |
| POST | `/cart/add` | Tidak | Tambah item ke keranjang (flash + redirect) |
| POST | `/cart/remove/<item_id>` | Tidak | Hapus item dari keranjang |

### 4.5 Order (`/order`)
| Method | Path | Auth | Keterangan |
|---|---|---|---|
| GET, POST | `/order/checkout` | Tidak | Checkout order + validasi pembayaran |
| GET | `/order/history` | Opsional | Riwayat order berdasarkan customer key |
| POST | `/order/<order_id>/upload-proof` | Ya | Upload ulang bukti pembayaran |
| GET | `/order/success` | Tidak | Halaman sukses order |

### 4.6 Admin (`/admin`)
Semua endpoint berikut membutuhkan session role admin.

| Method | Path | Keterangan |
|---|---|---|
| GET | `/admin/` | Dashboard admin |
| GET | `/admin/menus` | Daftar menu |
| GET, POST | `/admin/menus/add` | Tambah menu |
| GET, POST | `/admin/menus/<menu_id>/edit` | Edit menu |
| POST | `/admin/menus/<menu_id>/delete` | Hapus menu |
| GET | `/admin/categories` | Halaman kategori |
| GET | `/admin/orders` | Daftar order |
| POST | `/admin/orders/<order_id>/verify-payment` | Verifikasi pembayaran transfer/e-wallet |
| POST | `/admin/orders/<order_id>/status` | Ubah status order |
| POST | `/admin/orders/<order_id>/delete` | Hapus order |

### 4.7 Format dan Validasi Penting
- Metode pembayaran valid: `cash`, `transfer`, `ewallet`.
- Format bukti pembayaran valid: `png`, `jpg`, `jpeg`, `pdf`.
- Status order yang didukung:
  - `Menunggu Pembayaran`
  - `Sedang Dimasak`
  - `Dalam Perjalanan`
  - `Selesai`
  - `Dibatalkan`
