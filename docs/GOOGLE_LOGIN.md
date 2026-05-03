# Login dengan Google Identity Services

Dokumen ini menjelaskan implementasi Login with Google di aplikasi Flask ini.

## 1. Konfigurasi

Isi `.env` dengan OAuth 2.0 Web Client ID dari Google Cloud Console:

```env
GOOGLE_CLIENT_ID=client-id-anda.apps.googleusercontent.com
GOOGLE_ALLOWED_ORIGINS=http://127.0.0.1:5000,http://localhost:5000
```

Di Google Cloud Console, tambahkan Authorized JavaScript origins:

```text
http://127.0.0.1:5000
http://localhost:5000
```

Gunakan origin saja, tanpa path seperti `/auth/login`.

## 2. Frontend

Halaman `src/app/templates/auth/login.html` memuat SDK Google Identity Services:

```html
<script src="https://accounts.google.com/gsi/client" async defer></script>
```

Tombol Google hanya tampil jika `GOOGLE_CLIENT_ID` sudah diisi.

Saat user login, Google memanggil `handleGoogleCredential(response)`. Nilai pentingnya adalah:

```js
response.credential
```

Nilai tersebut adalah ID Token Google. Frontend mengirim token ini ke backend:

```js
fetch("/auth/google/credential", {
  method: "POST",
  headers: {
    "Content-Type": "application/json",
    "X-CSRF-Token": csrfToken
  },
  credentials: "same-origin",
  body: JSON.stringify({ credential: response.credential })
});
```

Jangan simpan ID Token di `localStorage`.

## 3. Backend Verification

Endpoint backend ada di:

```text
POST /auth/google/credential
```

File implementasi:

```text
src/app/routes/auth.py
```

Backend memverifikasi token memakai `google-auth`:

```python
payload = google_id_token.verify_oauth2_token(
    credential,
    google_requests.Request(),
    client_id,
)
```

Validasi yang dilakukan:

- signature token valid dari Google
- token belum expired
- `aud` sama dengan `GOOGLE_CLIENT_ID`
- `iss` adalah `accounts.google.com` atau `https://accounts.google.com`
- `email_verified` bernilai valid

Jika user belum ada, aplikasi membuat akun customer lokal memakai email Google.

## 4. Session Management

Setelah token valid, aplikasi mengisi session Flask yang sama dengan login biasa:

```python
session["is_logged_in"] = True
session["user_id"] = user.id
session["user_email"] = user.email
session["user_name"] = user.name
session["user_role"] = user.role
```

Cookie session dikonfigurasi di `src/app/config.py`:

```python
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = "Lax"
SESSION_COOKIE_SECURE = False
```

Untuk production HTTPS, set:

```env
SESSION_COOKIE_SECURE=1
```

## 5. Security Notes

- Backend selalu memverifikasi ID Token, frontend tidak dipercaya sebagai sumber identitas.
- Endpoint Google credential dilindungi CSRF token lewat header `X-CSRF-Token`.
- Origin request dicek melalui `GOOGLE_ALLOWED_ORIGINS`.
- ID Token hanya dipakai sekali untuk membuat session lokal.
- Session cookie `HttpOnly` agar tidak bisa dibaca JavaScript.
- Gunakan HTTPS di production.

## 6. Debugging

### Tombol Google tidak muncul

Pastikan `.env` memiliki:

```env
GOOGLE_CLIENT_ID=...
```

Restart server setelah mengubah `.env`.

### Origin mismatch

Tambahkan origin aplikasi ke Google Cloud Console.

Benar:

```text
http://127.0.0.1:5000
```

Salah:

```text
http://127.0.0.1:5000/auth/login
```

### Audience mismatch atau token tidak valid

Pastikan Client ID di frontend sama dengan backend:

```env
GOOGLE_CLIENT_ID=client-id-yang-sama.apps.googleusercontent.com
```

### CSRF error

Refresh halaman login agar session mendapat CSRF token baru, lalu coba login ulang.

### Cookie tidak tersimpan

Untuk local development, gunakan:

```env
SESSION_COOKIE_SECURE=0
```

Untuk production HTTPS, gunakan:

```env
SESSION_COOKIE_SECURE=1
```
