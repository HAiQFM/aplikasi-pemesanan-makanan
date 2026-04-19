-- ============================================================
--  SETUP DATABASE — Aplikasi Pemesanan Makanan
--  Kompatibel dengan XAMPP MySQL 5.7+ / MariaDB 10.3+
--
--  CARA IMPORT DI phpMyAdmin:
--    1. Buka http://localhost/phpmyadmin
--    2. Klik tab "SQL" di menu atas
--    3. Copy-paste seluruh isi file ini
--    4. Klik tombol "Go" / "Jalankan"
--
--  ATAU import file langsung:
--    1. Klik "Import" di menu atas
--    2. Pilih file ini → klik "Go"
-- ============================================================

-- ──────────────────────────────────────────────────────────────
-- LANGKAH 1: Buat dan pilih database
-- ──────────────────────────────────────────────────────────────

CREATE DATABASE IF NOT EXISTS `db_pemesanan_makanan`
    CHARACTER SET utf8mb4          -- support emoji & karakter Asia
    COLLATE utf8mb4_unicode_ci;    -- sorting case-insensitive

USE `db_pemesanan_makanan`;

-- Matikan foreign key check sementara agar drop urutan tidak masalah
SET FOREIGN_KEY_CHECKS = 0;

-- ──────────────────────────────────────────────────────────────
-- LANGKAH 2: Hapus tabel lama (jika ada) untuk fresh install
-- ──────────────────────────────────────────────────────────────

DROP TABLE IF EXISTS `order_items`;
DROP TABLE IF EXISTS `orders`;
DROP TABLE IF EXISTS `carts`;
DROP TABLE IF EXISTS `menus`;
DROP TABLE IF EXISTS `categories`;
DROP TABLE IF EXISTS `users`;

SET FOREIGN_KEY_CHECKS = 1;

-- ============================================================
--  TABEL 1: users
--  Menyimpan akun pelanggan dan admin.
--  KEAMANAN: password WAJIB di-hash sebelum disimpan.
--            Aplikasi Python menggunakan werkzeug pbkdf2:sha256.
-- ============================================================

CREATE TABLE `users` (
    `id`            INT             NOT NULL AUTO_INCREMENT,
    `name`          VARCHAR(120)    NOT NULL                    COMMENT 'Nama lengkap pengguna',
    `email`         VARCHAR(255)    NOT NULL                    COMMENT 'Email unik untuk login',
    `password_hash` VARCHAR(255)    NOT NULL                    COMMENT 'Hash pbkdf2:sha256 — JANGAN simpan plaintext',
    `role`          VARCHAR(20)     NOT NULL DEFAULT 'customer' COMMENT 'customer | admin',
    `is_active`     TINYINT(1)      NOT NULL DEFAULT 1          COMMENT '1=aktif, 0=dinonaktifkan',
    `created_at`    DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP,

    PRIMARY KEY (`id`),
    UNIQUE  KEY `uq_users_email`    (`email`),
    INDEX   `ix_users_email`        (`email`),
    INDEX   `ix_users_role`         (`role`)
) ENGINE=InnoDB
  DEFAULT CHARSET=utf8mb4
  COLLATE=utf8mb4_unicode_ci
  COMMENT='Akun pengguna — pelanggan dan admin';


-- ============================================================
--  TABEL 2: categories
--  Kategori menu (misal: Paket Ayam, Minuman).
-- ============================================================

CREATE TABLE `categories` (
    `id`            INT             NOT NULL AUTO_INCREMENT,
    `name`          VARCHAR(120)    NOT NULL                    COMMENT 'Nama kategori (unik)',
    `description`   VARCHAR(255)        NULL                    COMMENT 'Deskripsi singkat kategori',
    `created_at`    DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP,

    PRIMARY KEY (`id`),
    UNIQUE  KEY `uq_categories_name` (`name`),
    INDEX   `ix_categories_name`     (`name`)
) ENGINE=InnoDB
  DEFAULT CHARSET=utf8mb4
  COLLATE=utf8mb4_unicode_ci
  COMMENT='Kategori item menu';


-- ============================================================
--  TABEL 3: menus
--  Data item menu yang dijual.
--  Relasi: menus.category_id → categories.id (RESTRICT)
--          Hapus kategori hanya jika tidak punya menu.
-- ============================================================

CREATE TABLE `menus` (
    `id`            INT             NOT NULL AUTO_INCREMENT,
    `category_id`   INT             NOT NULL                    COMMENT 'FK → categories.id',
    `name`          VARCHAR(120)    NOT NULL                    COMMENT 'Nama menu',
    `description`   TEXT                NULL                    COMMENT 'Deskripsi menu',
    `price`         DECIMAL(10,2)   NOT NULL DEFAULT 0.00       COMMENT 'Harga dalam rupiah',
    `image_url`     VARCHAR(255)        NULL                    COMMENT 'Nama file gambar di static/images/',
    `is_available`  TINYINT(1)      NOT NULL DEFAULT 1          COMMENT '1=tersedia, 0=habis',
    `created_at`    DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP,

    PRIMARY KEY (`id`),
    INDEX   `ix_menus_category_id`  (`category_id`),
    INDEX   `ix_menus_name`         (`name`),

    CONSTRAINT `fk_menus_category`
        FOREIGN KEY (`category_id`)
        REFERENCES `categories` (`id`)
        ON UPDATE CASCADE
        ON DELETE RESTRICT           -- tolak hapus kategori jika masih punya menu
) ENGINE=InnoDB
  DEFAULT CHARSET=utf8mb4
  COLLATE=utf8mb4_unicode_ci
  COMMENT='Item menu yang dijual';


-- ============================================================
--  TABEL 4: carts
--  Keranjang belanja per pengguna (server-side).
--  Relasi: carts.user_id → users.id (CASCADE DELETE)
--          carts.menu_id → menus.id (CASCADE DELETE)
-- ============================================================

CREATE TABLE `carts` (
    `id`            INT             NOT NULL AUTO_INCREMENT,
    `user_id`       INT             NOT NULL                    COMMENT 'FK → users.id',
    `menu_id`       INT             NOT NULL                    COMMENT 'FK → menus.id',
    `quantity`      INT             NOT NULL DEFAULT 1          COMMENT 'Jumlah item',
    `note`          VARCHAR(255)        NULL                    COMMENT 'Catatan khusus dari pelanggan',
    `created_at`    DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP,

    PRIMARY KEY (`id`),
    INDEX   `ix_carts_user_id`  (`user_id`),
    INDEX   `ix_carts_menu_id`  (`menu_id`),

    CONSTRAINT `fk_carts_user`
        FOREIGN KEY (`user_id`)
        REFERENCES `users` (`id`)
        ON UPDATE CASCADE
        ON DELETE CASCADE,           -- hapus cart jika user dihapus

    CONSTRAINT `fk_carts_menu`
        FOREIGN KEY (`menu_id`)
        REFERENCES `menus` (`id`)
        ON UPDATE CASCADE
        ON DELETE CASCADE            -- hapus cart item jika menu dihapus
) ENGINE=InnoDB
  DEFAULT CHARSET=utf8mb4
  COLLATE=utf8mb4_unicode_ci
  COMMENT='Keranjang belanja pengguna';


-- ============================================================
--  TABEL 5: orders
--  Setiap transaksi pesanan.
--  user_id NULL → pesanan tamu (guest) tanpa akun.
--  Data pelanggan didenormalisasi sebagai snapshot saat checkout.
-- ============================================================

CREATE TABLE `orders` (
    `id`                    INT             NOT NULL AUTO_INCREMENT,
    `user_id`               INT                 NULL                    COMMENT 'FK → users.id (NULL untuk tamu)',
    `customer_name`         VARCHAR(120)    NOT NULL DEFAULT ''         COMMENT 'Nama pelanggan saat checkout',
    `customer_email`        VARCHAR(255)    NOT NULL DEFAULT ''         COMMENT 'Email pelanggan / guest key',
    `address`               TEXT                NULL                    COMMENT 'Alamat pengiriman',
    `payment_method`        VARCHAR(50)         NULL                    COMMENT 'cash | transfer | ewallet',
    `payment_proof_path`    VARCHAR(255)        NULL                    COMMENT 'Path file bukti transfer/ewallet',
    `payment_verification`  VARCHAR(20)     NOT NULL DEFAULT 'pending'  COMMENT 'pending | verified',
    `total_amount`          DECIMAL(10,2)   NOT NULL DEFAULT 0.00       COMMENT 'Total harga pesanan',
    `status`                VARCHAR(50)     NOT NULL DEFAULT 'Menunggu Pembayaran'
                                                                        COMMENT 'Status: Menunggu Pembayaran | Sedang Dimasak | Dalam Perjalanan | Selesai | Dibatalkan',
    `created_at`            DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP,
    `updated_at`            DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP
                                                       ON UPDATE CURRENT_TIMESTAMP,

    PRIMARY KEY (`id`),
    INDEX   `ix_orders_user_id`         (`user_id`),
    INDEX   `ix_orders_customer_email`  (`customer_email`),
    INDEX   `ix_orders_status`          (`status`),

    CONSTRAINT `fk_orders_user`
        FOREIGN KEY (`user_id`)
        REFERENCES `users` (`id`)
        ON UPDATE CASCADE
        ON DELETE SET NULL           -- jika user dihapus, pesanan tetap ada (user_id → NULL)
) ENGINE=InnoDB
  DEFAULT CHARSET=utf8mb4
  COLLATE=utf8mb4_unicode_ci
  COMMENT='Transaksi pesanan';


-- ============================================================
--  TABEL 6: order_items
--  Detail item dalam setiap pesanan (one-to-many ke orders).
--  Data menu didenormalisasi: menu_name & unit_price adalah
--  snapshot saat checkout — tidak berubah walau admin edit harga.
-- ============================================================

CREATE TABLE `order_items` (
    `id`            INT             NOT NULL AUTO_INCREMENT,
    `order_id`      INT             NOT NULL                    COMMENT 'FK → orders.id',
    `menu_name`     VARCHAR(120)    NOT NULL                    COMMENT 'Nama menu saat checkout (snapshot)',
    `quantity`      INT             NOT NULL DEFAULT 1          COMMENT 'Jumlah item dipesan',
    `unit_price`    DECIMAL(10,2)   NOT NULL DEFAULT 0.00       COMMENT 'Harga satuan saat checkout (snapshot)',
    `details`       JSON                NULL                    COMMENT 'Pilihan tambahan: [{"label":"Sambal","value":"Sambal Matah"}]',

    PRIMARY KEY (`id`),
    INDEX   `ix_order_items_order_id` (`order_id`),

    CONSTRAINT `fk_order_items_order`
        FOREIGN KEY (`order_id`)
        REFERENCES `orders` (`id`)
        ON UPDATE CASCADE
        ON DELETE CASCADE            -- hapus items jika pesanan dihapus
) ENGINE=InnoDB
  DEFAULT CHARSET=utf8mb4
  COLLATE=utf8mb4_unicode_ci
  COMMENT='Detail item dalam setiap pesanan';


-- ============================================================
--  LANGKAH 3: INSERT Data Awal (Seed)
-- ============================================================

-- ── Kategori Menu ──────────────────────────────────────────

INSERT INTO `categories` (`name`, `description`) VALUES
    ('Paket Ayam', 'Paket nasi dengan lauk ayam pilihan'),
    ('Minuman',    'Minuman segar dan hangat');


-- ── Item Menu ──────────────────────────────────────────────

INSERT INTO `menus` (`category_id`, `name`, `description`, `price`, `image_url`, `is_available`) VALUES
    -- Paket Ayam (category_id = 1)
    (1, 'Nasi Ayam Geprek',  'Ayam geprek crispy dengan nasi hangat.',         13000.00, 'nasi ayam penyet.jfif', 1),
    (1, 'Nasi Ayam Bakar',   'Ayam bakar bumbu manis gurih dengan nasi.',     13000.00, 'nasi ayam bakar.jfif',  1),
    (1, 'Nasi Ayam Penyet',  'Ayam penyet empuk dengan lalapan segar.',       13000.00, 'nasi ayam penyet.jfif', 1),
    -- Minuman (category_id = 2)
    (2, 'Tea Jus',      'Teh manis dingin khas warung.',                3000.00,  NULL, 1),
    (2, 'Es Teh Manis', 'Teh dingin dengan gula sesuai selera.',        5000.00,  'es teh manis.jfif', 1),
    (2, 'Jus Mangga',   'Jus Mangga sehat, bisa request rasa.',        10000.00,  NULL, 1),
    (2, 'Jus Alpukat',  'Jus alpukat creamy ala warung.',              12000.00,  NULL, 1),
    (2, 'Jus Jambu',    'Jus jambu segar dengan rasa manis alami.',    10000.00,  'jus jambu.jfif', 1),
    (2, 'Jus Jeruk',    'Jus jeruk manis segar.',                       8000.00,  NULL, 1),
    (2, 'Kopi',         'Kopi hitam panas khas warung.',                5000.00,  NULL, 1),
    (2, 'Air Mineral',  'Air mineral dingin untuk pendamping menu.',    4000.00,  NULL, 1);


-- ── Akun Admin Default ─────────────────────────────────────
-- Password: Admin@Secure123 (hash werkzeug pbkdf2:sha256)
-- GANTI HASH INI dengan hasil generate_password_hash('password_anda')
-- dari Python: python -c "from werkzeug.security import generate_password_hash; print(generate_password_hash('Admin@Secure123'))"

INSERT INTO `users` (`name`, `email`, `password_hash`, `role`, `is_active`) VALUES
    (
        'Admin',
        'ffaiqm14@gmail.com',
        -- Hash untuk password: Admin@Secure123 (werkzeug scrypt)
        -- Untuk menghasilkan hash baru jalankan:
        -- python -c "from werkzeug.security import generate_password_hash; print(generate_password_hash('PASSWORD_ANDA'))"
        'scrypt:32768:8:1$j8MxBDPgYwnPgY43$857659c168fcbeb84f9af29488ef72f7ab78fefc15a5054e432ccada67a9d19467205824e7e8c3f88dd5c7b90b115a34a89ee496f460cee153eb60d2049a8e73',
        'admin',
        1
    );


-- ============================================================
--  LANGKAH 4: Verifikasi Struktur
-- ============================================================

-- Tampilkan semua tabel yang berhasil dibuat
SHOW TABLES;

-- Cek detail kolom tabel utama
DESCRIBE `users`;
DESCRIBE `menus`;
DESCRIBE `orders`;
DESCRIBE `order_items`;

-- Cek semua foreign key yang aktif
SELECT
    TABLE_NAME          AS `Tabel`,
    COLUMN_NAME         AS `Kolom`,
    CONSTRAINT_NAME     AS `Nama FK`,
    REFERENCED_TABLE_NAME  AS `Referensi Tabel`,
    REFERENCED_COLUMN_NAME AS `Referensi Kolom`
FROM
    INFORMATION_SCHEMA.KEY_COLUMN_USAGE
WHERE
    TABLE_SCHEMA = 'db_pemesanan_makanan'
    AND REFERENCED_TABLE_NAME IS NOT NULL
ORDER BY
    TABLE_NAME, COLUMN_NAME;
