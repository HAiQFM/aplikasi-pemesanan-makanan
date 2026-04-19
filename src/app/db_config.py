"""
db_config.py — Konfigurasi & helper koneksi database MySQL.

File ini berisi:
  1. DatabaseConfig  — baca konfigurasi dari .env
  2. get_db_uri()    — buat URI SQLAlchemy
  3. test_connection() — tes koneksi MySQL via PyMySQL langsung
  4. Contoh kode PHP PDO di docstring (referensi untuk integrasi PHP)

KONEKSI XAMPP (default):
  Host     : localhost
  Port     : 3306
  User     : root
  Password : (kosong)
  Database : db_pemesanan_makanan
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field


# ── Konfigurasi koneksi ───────────────────────────────────────────────────────


@dataclass
class DatabaseConfig:
    """
    Baca konfigurasi database dari environment variables (.env).
    Fallback ke nilai default XAMPP jika variabel tidak ada.
    """

    host: str = field(default_factory=lambda: os.getenv("DB_HOST", "localhost"))
    port: int = field(default_factory=lambda: int(os.getenv("DB_PORT", "3306")))
    user: str = field(default_factory=lambda: os.getenv("DB_USER", "root"))
    password: str = field(default_factory=lambda: os.getenv("DB_PASSWORD", ""))
    database: str = field(
        default_factory=lambda: os.getenv("DB_NAME", "db_pemesanan_makanan")
    )

    def get_sqlalchemy_uri(self) -> str:
        """
        Buat URI untuk Flask-SQLAlchemy / PyMySQL.
        Format: mysql+pymysql://user:password@host:port/database?charset=utf8mb4
        """
        # Encode password jika mengandung karakter khusus
        from urllib.parse import quote_plus

        pw = quote_plus(self.password)
        return (
            f"mysql+pymysql://{self.user}:{pw}"
            f"@{self.host}:{self.port}/{self.database}"
            f"?charset=utf8mb4"
        )

    def __str__(self) -> str:
        return f"MySQL://{self.user}@{self.host}:{self.port}/{self.database}"


# Instance default (XAMPP)
db_config = DatabaseConfig()


def get_db_uri() -> str:
    """
    Kembalikan URI database dari DATABASE_URL (.env) atau build dari komponen.

    Prioritas:
      1. DATABASE_URL  — URI lengkap dari .env (dipakai app Flask utama)
      2. DB_HOST/USER/PASSWORD/NAME — komponen individual
    """
    env_url = os.getenv("DATABASE_URL", "").strip()
    if env_url:
        return env_url
    return db_config.get_sqlalchemy_uri()


# ── Tes koneksi langsung (tanpa Flask app context) ────────────────────────────


def test_connection() -> bool:
    """
    Tes koneksi MySQL menggunakan PyMySQL langsung.
    Berguna untuk health-check atau debugging sebelum menjalankan Flask.

    Contoh penggunaan:
        python -c "from app.db_config import test_connection; test_connection()"
    """
    try:
        import pymysql

        cfg = DatabaseConfig()
        conn = pymysql.connect(
            host=cfg.host,
            port=cfg.port,
            user=cfg.user,
            password=cfg.password,
            database=cfg.database,
            charset="utf8mb4",
            connect_timeout=5,
        )

        with conn.cursor() as cursor:
            cursor.execute("SELECT VERSION(), DATABASE()")
            version, dbname = cursor.fetchone()
            print(f"[OK] Terhubung ke MySQL {version}")
            print(f"     Database aktif : {dbname}")
            cursor.execute("SHOW TABLES")
            tables = [row[0] for row in cursor.fetchall()]
            print(
                f"     Tabel ditemukan: {', '.join(tables) if tables else '(belum ada tabel)'}"
            )

        conn.close()
        return True

    except Exception as exc:
        print(f"[ERROR] Koneksi gagal: {exc}")
        print("        Pastikan XAMPP MySQL sudah running di port 3306.")
        return False


# ── Referensi Kode PHP PDO ────────────────────────────────────────────────────
"""
==========================================================================
CONTOH KONEKSI PHP PDO (untuk referensi integrasi sisi PHP jika diperlukan)
==========================================================================

FILE: config/database.php
--------------------------------------------------------------------------

<?php
/**
 * Koneksi Database MySQL via PDO
 * - Menggunakan prepared statements untuk mencegah SQL Injection
 * - Charset utf8mb4 untuk support emoji dan karakter khusus
 * - Error mode EXCEPTION agar error mudah di-debug
 */

define('DB_HOST',     'localhost');
define('DB_PORT',     '3306');
define('DB_NAME',     'db_pemesanan_makanan');
define('DB_USER',     'root');
define('DB_PASS',     '');          // XAMPP default: password kosong
define('DB_CHARSET',  'utf8mb4');

function getConnection(): PDO {
    $dsn = sprintf(
        'mysql:host=%s;port=%s;dbname=%s;charset=%s',
        DB_HOST, DB_PORT, DB_NAME, DB_CHARSET
    );

    $options = [
        PDO::ATTR_ERRMODE            => PDO::ERRMODE_EXCEPTION,   // lempar exception saat error
        PDO::ATTR_DEFAULT_FETCH_MODE => PDO::FETCH_ASSOC,         // fetch sebagai array asosiatif
        PDO::ATTR_EMULATE_PREPARES   => false,                    // gunakan prepared statement asli
        PDO::MYSQL_ATTR_INIT_COMMAND => "SET NAMES utf8mb4",      // paksa charset
    ];

    try {
        return new PDO($dsn, DB_USER, DB_PASS, $options);
    } catch (PDOException $e) {
        // Jangan tampilkan pesan error ke user di production!
        error_log('DB Connection Error: ' . $e->getMessage());
        http_response_code(503);
        die('Layanan tidak tersedia sementara. Coba lagi nanti.');
    }
}

// Singleton pattern — gunakan satu koneksi per request
$pdo = getConnection();

--------------------------------------------------------------------------
CONTOH CRUD DENGAN PDO:
--------------------------------------------------------------------------

// ── CREATE (INSERT) ──────────────────────────────────────────────────────────
function createUser(PDO $pdo, string $name, string $email, string $password): int {
    // KEAMANAN: SELALU hash password sebelum disimpan
    $hash = password_hash($password, PASSWORD_BCRYPT, ['cost' => 12]);

    $stmt = $pdo->prepare(
        "INSERT INTO users (name, email, password_hash, role, is_active, created_at)
         VALUES (:name, :email, :password_hash, 'customer', 1, NOW())"
    );
    $stmt->execute([
        ':name'          => $name,
        ':email'         => strtolower(trim($email)),
        ':password_hash' => $hash,
    ]);
    return (int) $pdo->lastInsertId();
}

// ── READ (SELECT) ────────────────────────────────────────────────────────────
function getUserByEmail(PDO $pdo, string $email): array|false {
    $stmt = $pdo->prepare(
        "SELECT id, name, email, password_hash, role
         FROM users
         WHERE email = :email AND is_active = 1
         LIMIT 1"
    );
    $stmt->execute([':email' => strtolower(trim($email))]);
    return $stmt->fetch();   // array asosiatif atau false
}

// ── LOGIN (verifikasi password) ──────────────────────────────────────────────
function loginUser(PDO $pdo, string $email, string $password): array|false {
    $user = getUserByEmail($pdo, $email);
    if (!$user) return false;

    // KEAMANAN: password_verify() — JANGAN bandingkan hash secara manual
    if (!password_verify($password, $user['password_hash'])) return false;

    return $user;
}

// ── UPDATE ───────────────────────────────────────────────────────────────────
function updateOrderStatus(PDO $pdo, int $orderId, string $status): bool {
    $allowed = ['Menunggu Pembayaran','Sedang Dimasak','Dalam Perjalanan','Selesai','Dibatalkan'];
    if (!in_array($status, $allowed, true)) return false;  // whitelist validasi

    $stmt = $pdo->prepare(
        "UPDATE orders
         SET status = :status, updated_at = NOW()
         WHERE id = :id"
    );
    $stmt->execute([':status' => $status, ':id' => $orderId]);
    return $stmt->rowCount() > 0;
}

// ── DELETE ───────────────────────────────────────────────────────────────────
function deleteOrder(PDO $pdo, int $orderId): bool {
    // order_items akan terhapus otomatis via ON DELETE CASCADE
    $stmt = $pdo->prepare("DELETE FROM orders WHERE id = :id");
    $stmt->execute([':id' => $orderId]);
    return $stmt->rowCount() > 0;
}

// ── DAFTAR PESANAN (JOIN) ────────────────────────────────────────────────────
function listOrdersWithItems(PDO $pdo, ?string $customerEmail = null): array {
    $sql = "
        SELECT
            o.id,
            o.customer_name,
            o.customer_email,
            o.total_amount,
            o.status,
            o.payment_method,
            o.created_at,
            GROUP_CONCAT(
                CONCAT(oi.quantity, 'x ', oi.menu_name)
                ORDER BY oi.id
                SEPARATOR ', '
            ) AS item_summary
        FROM orders o
        LEFT JOIN order_items oi ON oi.order_id = o.id
    ";

    $params = [];
    if ($customerEmail !== null) {
        $sql .= " WHERE o.customer_email = :email";
        $params[':email'] = strtolower(trim($customerEmail));
    }

    $sql .= " GROUP BY o.id ORDER BY o.created_at DESC";
    $stmt = $pdo->prepare($sql);
    $stmt->execute($params);
    return $stmt->fetchAll();
}

--------------------------------------------------------------------------
KEAMANAN — CHECKLIST WAJIB:
--------------------------------------------------------------------------
  ✅ Gunakan PDO prepared statements — TIDAK pernah string concatenation
  ✅ Hash password dengan password_hash() + PASSWORD_BCRYPT (cost >= 12)
  ✅ Verifikasi password dengan password_verify() bukan ==
  ✅ Validasi & whitelist input sebelum query (misal: whitelist status)
  ✅ Jangan tampilkan error DB ke user — gunakan error_log()
  ✅ Set PDO::ATTR_EMULATE_PREPARES = false untuk prepared stmt asli
  ✅ Simpan kredensial DB di .env / config terpisah, JANGAN di kode

==========================================================================
"""
