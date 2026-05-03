# Aplikasi Pemesanan Makanan - Food Hall - Warung Nasi Teh Sarah

Proyek ini adalah aplikasi web sederhana untuk pemesanan makanan pada tempat makan **Food Hall - Warung Nasi Teh Sarah**. Aplikasi dibangun menggunakan **Flask** dengan struktur modular (routes, models, templates, static) dan mendukung alur dasar pengguna dari login sampai checkout.

## Fitur Utama

- Autentikasi pengguna: login, register, logout.
- Katalog menu dan detail menu.
- Keranjang belanja (cart).
- Checkout dan halaman sukses pesanan.
- Riwayat pesanan.
- Halaman admin untuk dashboard, kelola menu, kategori, dan pesanan.

## Teknologi

- Python
- Flask
- Flask-SQLAlchemy
- python-dotenv
- Pytest

## Struktur Proyek

```text
aplikasi-pemesanan-makanan/
+-- src/app/
|   +-- models/
|   +-- routes/
|   +-- templates/
|   \-- static/
+-- tests/
+-- run.py
+-- requirements.txt
\-- README.md
```

## Prasyarat

- Python 3.8 atau lebih baru
- `pip`

## Instalasi

1. Clone repository ini.
2. Masuk ke folder proyek.
3. Buat virtual environment.
4. Install dependensi.

Contoh perintah (Windows PowerShell):

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

## Konfigurasi Environment

Buat file `.env` di root proyek, lalu isi minimal seperti berikut:

```env
SECRET_KEY=dev-secret-key
FLASK_ENV=development
FLASK_DEBUG=1
DATABASE_URL=sqlite:///app.db
```

Catatan:
- Jika `DATABASE_URL` tidak diisi, aplikasi otomatis memakai SQLite lokal (`app.db`).

### Login Google OAuth 2.0

Tambahkan kredensial OAuth dari Google Cloud Console jika ingin mengaktifkan tombol **Sign in with Google**:

```env
GOOGLE_CLIENT_ID=client-id-anda.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=client-secret-anda
```

Daftarkan redirect URI berikut pada OAuth Client bertipe Web application:

```text
http://127.0.0.1:5000/auth/google/callback
```

## Menjalankan Aplikasi

```powershell
python run.py
```

Aplikasi akan berjalan di:

`http://127.0.0.1:5000`

## Menjalankan Pengujian

```powershell
pytest -q
```

## Daftar Kontributor

- Sindi Susanti - 001
- Fauzan Iffat Chairrullah - 004
- Fatya Lihawa Awaliyah - 006
- Firas Faiq Maulana - 015
