# Google Maps di Halaman Checkout

Fitur ini mengganti input alamat manual di `/order/checkout` menjadi pemilihan lokasi interaktif dengan Google Maps.

## Fitur

- Cari alamat atau nama tempat melalui Google Places Autocomplete.
- Klik titik pada peta untuk memilih lokasi pengiriman.
- Geser pin untuk memperbaiki titik pengiriman.
- Tombol **Gunakan Lokasi Saya** untuk mengambil lokasi perangkat melalui browser Geolocation API.
- Reverse geocoding otomatis untuk mengisi alamat dari koordinat.
- Menyimpan alamat, latitude, longitude, Google Place ID, dan URL Google Maps ke tabel `orders`.
- Link Google Maps tampil di halaman sukses, riwayat pesanan, dan daftar pesanan admin.

## Konfigurasi `.env`

Tambahkan API key berikut:

```env
GOOGLE_MAPS_API_KEY=api-key-google-maps-anda
```

API yang perlu diaktifkan di Google Cloud Console:

- Maps JavaScript API
- Places API
- Geocoding API

Untuk development lokal, batasi API key pada HTTP referrer seperti:

```text
http://127.0.0.1:5000/*
http://localhost:5000/*
```

## Migrasi Database Lama

Jika database sudah dibuat sebelum fitur ini ditambahkan, jalankan:

```sql
SOURCE scripts/add_delivery_location_columns.sql;
```

Atau jalankan isi file SQL tersebut langsung di MySQL client/phpMyAdmin.

## Catatan Lokasi Perangkat

Browser akan meminta izin lokasi ke pengguna. Akses lokasi perangkat biasanya hanya berjalan pada HTTPS atau localhost. Jika izin ditolak, pengguna masih bisa mencari alamat, klik peta, atau mengisi alamat manual.
