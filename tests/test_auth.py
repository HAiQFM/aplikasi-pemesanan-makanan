import json
import tempfile
from datetime import date

from run import app


def get_client():
    app.config.update(TESTING=True, WTF_CSRF_ENABLED=False)
    return app.test_client()


def test_login_page_loads():
    client = get_client()
    response = client.get('/auth/login')
    assert response.status_code == 200


def test_register_page_loads():
    client = get_client()
    response = client.get('/auth/register')
    assert response.status_code == 200


def test_login_post_redirects_to_order_history():
    client = get_client()
    client.post('/auth/register', data={'name': 'User', 'email': 'user@mail.com', 'password': 'secret'})
    response = client.post('/auth/login', data={'email': 'user@mail.com', 'password': 'secret'})
    assert response.status_code == 302
    assert response.headers['Location'].endswith('/order/history')


def test_register_post_redirects_to_login():
    client = get_client()
    response = client.post('/auth/register', data={'name': 'User', 'email': 'user@mail.com', 'password': 'secret'})
    assert response.status_code == 302
    assert response.headers['Location'].endswith('/auth/login')


def test_logout_redirects_to_login():
    client = get_client()
    response = client.post('/auth/logout')
    assert response.status_code == 302
    assert response.headers['Location'].endswith('/auth/login')


def test_logout_clears_customer_session_but_preserves_registered_users():
    client = get_client()
    client.post('/auth/register', data={'name': 'User', 'email': 'user@mail.com', 'password': 'secret'})
    client.post('/auth/login', data={'email': 'user@mail.com', 'password': 'secret'})

    response = client.post('/auth/logout', follow_redirects=True)

    assert response.status_code == 200
    assert b'Anda telah logout.' in response.data
    assert b'Login' in response.data

    with client.session_transaction() as session_state:
      assert session_state.get('is_logged_in') is None
      assert session_state.get('user_email') is None
      assert session_state.get('user_name') is None
      assert session_state.get('user_role') is None
      assert session_state.get('users', {}).get('user@mail.com') == 'User'


def test_login_unregistered_email_shows_error():
    client = get_client()
    response = client.post('/auth/login', data={'email': 'unknown@mail.com', 'password': 'secret'})
    assert response.status_code == 200
    assert b'Email tidak terdaftar, mohon registrasi terlebih dahulu.' in response.data


def test_admin_login_redirects_to_admin_dashboard():
    client = get_client()
    response = client.post('/auth/login', data={'email': 'ffaiqm14@gmail.com', 'password': '123456'})
    assert response.status_code == 302
    assert response.headers['Location'].endswith('/admin/')


def test_admin_login_with_wrong_password_shows_error():
    client = get_client()
    response = client.post('/auth/login', data={'email': 'ffaiqm14@gmail.com', 'password': 'wrong'})
    assert response.status_code == 200
    assert b'Password admin salah.' in response.data


def test_non_admin_cannot_access_admin_pages():
    client = get_client()
    client.post('/auth/register', data={'name': 'User', 'email': 'user@mail.com', 'password': 'secret'})
    client.post('/auth/login', data={'email': 'user@mail.com', 'password': 'secret'})
    response = client.get('/admin/')
    assert response.status_code == 302
    assert response.headers['Location'].endswith('/auth/login')


def test_admin_logout_redirects_to_main_dashboard():
    client = get_client()
    client.post('/auth/login', data={'email': 'ffaiqm14@gmail.com', 'password': '123456'})
    response = client.post('/auth/logout-admin')
    assert response.status_code == 302
    assert response.headers['Location'].endswith('/')


def test_html_pages_disable_cache_after_logout():
    client = get_client()
    response = client.get('/auth/login')

    assert response.status_code == 200
    assert response.headers['Cache-Control'] == 'no-store, no-cache, must-revalidate, max-age=0'
    assert response.headers['Pragma'] == 'no-cache'
    assert response.headers['Expires'] == '0'


def test_admin_dashboard_shows_daily_sales_report():
    client = get_client()
    order_store = tempfile.NamedTemporaryFile(delete=False)
    order_store.close()
    today = date.today().isoformat()
    with open(order_store.name, 'w', encoding='utf-8') as handle:
        json.dump(
            [
                {
                    'id': 1,
                    'customer_name': 'Firas',
                    'customer_email': 'firas@mail.com',
                    'address': 'Jakarta',
                    'payment_method': 'cash',
                    'payment_proof_path': None,
                    'payment_verification': 'verified',
                    'total_amount': 25000,
                    'items': [
                        {'name': 'Nasi Goreng', 'qty': 2, 'price': 10000, 'details': []},
                        {'name': 'Es Teh Manis', 'qty': 1, 'price': 5000, 'details': []},
                    ],
                    'status': 'Selesai',
                    'created_at': f'{today}T10:00:00',
                    'updated_at': f'{today}T10:00:00',
                },
                {
                    'id': 2,
                    'customer_name': 'Sarah',
                    'customer_email': 'sarah@mail.com',
                    'address': 'Bandung',
                    'payment_method': 'transfer',
                    'payment_proof_path': None,
                    'payment_verification': 'pending',
                    'total_amount': 30000,
                    'items': [
                        {'name': 'Nasi Goreng', 'qty': 1, 'price': 10000, 'details': []},
                        {'name': 'Ayam Geprek', 'qty': 1, 'price': 20000, 'details': []},
                    ],
                    'status': 'Menunggu Pembayaran',
                    'created_at': f'{today}T12:00:00',
                    'updated_at': f'{today}T12:00:00',
                },
                {
                    'id': 3,
                    'customer_name': 'Budi',
                    'customer_email': 'budi@mail.com',
                    'address': 'Depok',
                    'payment_method': 'cash',
                    'payment_proof_path': None,
                    'payment_verification': 'verified',
                    'total_amount': 18000,
                    'items': [
                        {'name': 'Mie Goreng', 'qty': 1, 'price': 18000, 'details': []},
                    ],
                    'status': 'Dibatalkan',
                    'created_at': f'{today}T15:00:00',
                    'updated_at': f'{today}T15:00:00',
                },
            ],
            handle,
        )

    app.config.update(ORDER_STORE_FILE=order_store.name)
    client.post('/auth/login', data={'email': 'ffaiqm14@gmail.com', 'password': '123456'})
    response = client.get('/admin/')

    assert response.status_code == 200
    assert b'Laporan Penjualan Harian' in response.data
    assert b'Ringkasan Laporan Admin' in response.data
    assert b'Rp 55.000' in response.data
    assert b'>3<' in response.data
    assert b'Nasi Goreng' in response.data
    assert b'>3<' in response.data
    assert b'Firas' in response.data
