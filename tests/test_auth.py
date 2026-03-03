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
