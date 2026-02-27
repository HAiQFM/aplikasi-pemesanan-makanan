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
